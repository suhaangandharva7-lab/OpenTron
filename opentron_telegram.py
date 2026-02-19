import os
import json
import asyncio
import subprocess
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pyautogui
import mss
import psutil
from PIL import Image

# --- Configuration ---
load_dotenv()

# Setup Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")
POLICY_FILE = os.path.join(WORKSPACE_DIR, "POLICY.md")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# --- Tool Functions ---

def run_shell_command(command: str) -> str:
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=WORKSPACE_DIR)
        output = result.stdout
        if result.stderr:
            output += f"\nError:\n{result.stderr}"
        return output.strip() or "Success (no output)"
    except Exception as e: return f"Error: {str(e)}"

CORE_FILES = ["IDENTITY.md", "SOUL.md", "USER.md", "AGENTS.md", "TOOLS.md", "KNOWLEDGE.md"]

def read_file(file_path: str) -> str:
    try:
        if file_path in CORE_FILES:
            path = os.path.abspath(os.path.join(os.getcwd(), file_path))
        else:
            path = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
            if not path.startswith(WORKSPACE_DIR): return "Error: Path outside workspace."
        
        with open(path, 'r', encoding='utf-8') as f: return f.read()
    except Exception as e: return f"Error: {str(e)}"

def write_file(file_path: str, content: str) -> str:
    try:
        if file_path in CORE_FILES:
            path = os.path.abspath(os.path.join(os.getcwd(), file_path))
        else:
            path = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
            if not path.startswith(WORKSPACE_DIR): return "Error: Path outside workspace."
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e: return f"Error: {str(e)}"

async def browse_url(url: str) -> str:
    """Browse a URL and return a semantic text snapshot."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            
            # Clean up with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            for script in soup(["script", "style"]): script.decompose()
            text = soup.get_text(separator=" ", strip=True)
            
            await browser.close()
            # Return a truncated snapshot for token efficiency
            return f"--- SNAPSHOT OF {url} ---\n{text[:5000]}..."
    except Exception as e:
        return f"Error browsing {url}: {str(e)}"

def run_global_shell(command: str) -> str:
    """Execute a shell command ANYWHERE on the system. HIGH RISK."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout
        if result.stderr:
            output += f"\nError:\n{result.stderr}"
        return output.strip() or "Success (no output)"
    except Exception as e: return f"Error: {str(e)}"

def read_global_file(file_path: str) -> str:
    """Read any file on the system. HIGH RISK."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return f.read()
    except Exception as e: return f"Error: {str(e)}"

def write_global_file(file_path: str, content: str) -> str:
    """Write any file on the system. HIGH RISK."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f: f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e: return f"Error: {str(e)}"

async def get_screenshot() -> str:
    """Capture the current screen and save it to the workspace."""
    try:
        with mss.mss() as sct:
            filename = os.path.join(WORKSPACE_DIR, "current_screen.png")
            sct.shot(output=filename)
            return f"Screenshot saved to workspace/current_screen.png"
    except Exception as e: return f"Error capturing screen: {str(e)}"

def desktop_interaction(action: str, params: dict) -> str:
    """Interact with the desktop GUI.
    Actions: move (x, y), click (button), type (text, interval), press (key)
    """
    try:
        if action == "move":
            pyautogui.moveTo(params.get("x", 0), params.get("y", 0))
        elif action == "click":
            pyautogui.click(button=params.get("button", "left"))
        elif action == "type":
            pyautogui.write(params.get("text", ""), interval=params.get("interval", 0.1))
        elif action == "press":
            pyautogui.press(params.get("key", "enter"))
        else:
            return f"Unknown action: {action}"
        return f"Successfully performed {action}"
    except Exception as e: return f"Error in desktop interaction: {str(e)}"

def get_system_info() -> str:
    """Get CPU, Memory, and Disk info."""
    try:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return f"CPU: {cpu}%, RAM: {mem}%, Disk: {disk}%"
    except Exception as e: return f"Error getting sys info: {str(e)}"

async def send_telegram_photo(file_path: str, caption: str = "") -> str:
    """Send a photo back to the user on Telegram. CAPTION IS OPTIONAL."""
    try:
        # This will be handled by the bot instance which has access to the telegram app
        return f"RESERVED_TOOL_CALL:SEND_PHOTO:{file_path}:{caption}"
    except Exception as e: return f"Error: {str(e)}"

# --- Prompt Management ---

class PromptManager:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.components = ["IDENTITY.md", "SOUL.md", "AGENTS.md", "KNOWLEDGE.md", "USER.md", "TOOLS.md"]

    def assemble_prompt(self) -> str:
        prompt_parts = []
        # Core prompt pieces at root
        for component in self.components:
            path = os.path.join(self.root_dir, component)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    prompt_parts.append(f.read())
        
        # Skill-based prompts
        skills_dir = os.path.join(self.root_dir, "skills")
        if os.path.exists(skills_dir):
            for skill_name in os.listdir(skills_dir):
                skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
                if os.path.exists(skill_path):
                    with open(skill_path, 'r', encoding='utf-8') as f:
                        prompt_parts.append(f"\n## SKILL: {skill_name.upper()}\n{f.read()}")

        return "\n\n".join(prompt_parts)

# --- Agent State ---

class OpenTronBot:
    def __init__(self, api_key: str, bot_token: str):
        genai.configure(api_key=api_key)
        self.bot_token = bot_token
        self.prompt_manager = PromptManager(os.getcwd())
        self.app = None # Set later
        
        # Initial instruction assembly
        system_instruction = self.prompt_manager.assemble_prompt()
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            tools=[
                run_shell_command, read_file, write_file, browse_url,
                run_global_shell, read_global_file, write_global_file,
                get_screenshot, desktop_interaction, get_system_info,
                send_telegram_photo
            ],
            system_instruction=system_instruction
        )
        self.sessions: Dict[int, Any] = {}
        self.pending_actions: Dict[str, asyncio.Event] = {}
        self.action_results: Dict[str, Any] = {}
        self.is_running = True
        self.last_chat_id = None
        self.review_policy = self.load_policy()
        
        # We'll run check_dependencies in the background heartbeat or just log it here synchronously
        logger.info(f"Initializing OpenTron Core... [Policy: {self.review_policy}]")

    def load_policy(self) -> str:
        if os.path.exists(POLICY_FILE):
            with open(POLICY_FILE, 'r') as f:
                p = f.read().strip().upper()
                if p in ["HIGH", "MEDIUM", "NONE"]: return p
        return "MEDIUM"

    def save_policy(self, policy: str):
        self.review_policy = policy
        with open(POLICY_FILE, 'w') as f:
            f.write(policy)
        logger.info(f"Policy updated to: {policy}")

    async def check_dependencies(self):
        """Verify that all required tools are installed for a new user."""
        logger.info("Checking system dependencies...")
        missing = []
        try: import playwright
        except ImportError: missing.append("playwright")
        try: import pyautogui
        except ImportError: missing.append("pyautogui")
        try: import mss
        except ImportError: missing.append("mss")
        try: import psutil
        except ImportError: missing.append("psutil")
        
        if missing:
            logger.warning(f"⚠️ Missing optional dependencies: {', '.join(missing)}. Some skills may be limited.")
            logger.warning("Run 'pip install -r requirements.txt' to fix.")
        else:
            logger.info("✅ All core dependencies present.")

    def get_chat_session(self, chat_id: int):
        if chat_id not in self.sessions:
            # Always refresh prompt when starting a new session
            new_instruction = self.prompt_manager.assemble_prompt()
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                tools=[
                    run_shell_command, read_file, write_file, browse_url,
                    run_global_shell, read_global_file, write_global_file,
                    get_screenshot, desktop_interaction, get_system_info,
                    send_telegram_photo
                ],
                system_instruction=new_instruction
            )
            self.sessions[chat_id] = self.model.start_chat(enable_automatic_function_calling=False)
        return self.sessions[chat_id]

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat_id = update.effective_chat.id
            self.last_chat_id = chat_id
            user_text = update.message.text
            if not user_text: return
            
            logger.info(f"Received message from {chat_id}: {user_text}")
            session = self.get_chat_session(chat_id)
            
            response = session.send_message(user_text)
            await self.process_response(update, context, response)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(f"🛑 Error: {str(e)}")

    async def process_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, response):
        try:
            chat_id = update.effective_chat.id
            session = self.get_chat_session(chat_id)

            while True:
                # Handle Text Response (Gemini 2.0/3.0 can have text and tools in parts)
                has_text = False
                try:
                    if response.text:
                        await update.message.reply_text(response.text)
                        has_text = True
                except ValueError:
                    # This happens if the response was blocked or only has function calls
                    pass

                # Handle Tool Calls
                tool_calls = []
                for part in response.candidates[0].content.parts:
                    if fn := part.function_call:
                        tool_calls.append(fn)

                if not tool_calls:
                    break

                for fn in tool_calls:
                    func_name = fn.name
                    args = dict(fn.args)
                    
                    # Approval Logic
                    high_risk_tools = ["run_global_shell", "read_global_file", "write_global_file", "desktop_interaction"]
                    
                    # Define which tools require approval based on policy
                    if self.review_policy == "HIGH":
                        # In HIGH, practically everything needs a check
                        approval_tools = [func_name] 
                    elif self.review_policy == "NONE":
                        # In NONE, nothing needs approval
                        approval_tools = []
                    else: # MEDIUM (Default)
                        approval_tools = ["run_shell_command", "write_file"] + high_risk_tools
                    
                    if func_name in approval_tools:
                        action_id = f"{chat_id}_{id(fn)}"
                        self.pending_actions[action_id] = asyncio.Event()
                        
                        is_high_risk = func_name in high_risk_tools
                        header = "⚠️ *HIGH RISK TOOL REQUEST*" if is_high_risk else "🤖 *Tool Request*"
                        
                        keyboard = [
                            [InlineKeyboardButton("Approve ✅", callback_data=f"approve_{action_id}"),
                             InlineKeyboardButton("Deny ❌", callback_data=f"deny_{action_id}")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            f"{header}: `{func_name}`\nArgs: `{json.dumps(args)}`",
                            reply_markup=reply_markup, parse_mode='Markdown'
                        )
                        
                        # Wait for button click
                        await self.pending_actions[action_id].wait()
                        result = self.action_results.pop(action_id)
                        del self.pending_actions[action_id]
                        
                        if result == "Denied":
                            tool_response = "User denied action."
                        else:
                            tool_response = await self.execute_local_tool(func_name, args)
                            
                            # Special handling for send_photo reserved call
                            if isinstance(tool_response, str) and tool_response.startswith("RESERVED_TOOL_CALL:SEND_PHOTO:"):
                                _, _, photo_path, caption = tool_response.split(":", 3)
                                path = os.path.abspath(os.path.join(os.getcwd(), photo_path)) if not os.path.isabs(photo_path) else photo_path
                                if os.path.exists(path):
                                    await update.message.reply_photo(photo=open(path, 'rb'), caption=caption or "📸 OpenTron Delivery")
                                    tool_response = f"Successfully sent photo: {photo_path}"
                                else:
                                    tool_response = f"Error: Photo path not found: {photo_path}"
                    else:
                        tool_response = await self.execute_local_tool(func_name, args)

                    # Send result back
                    response = session.send_message(
                        genai.protos.Content(parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(name=func_name, response={"result": tool_response})
                        )])
                    )
                    
                    # If it was a screenshot, send it to the user
                    if func_name == "get_screenshot" and "Error" not in tool_response:
                        img_path = os.path.join(WORKSPACE_DIR, "current_screen.png")
                        if os.path.exists(img_path):
                            await update.message.reply_photo(photo=open(img_path, 'rb'), caption="🚥 OpenTron Visual Input")
        except Exception as e:
            logger.error(f"Error in process_response: {e}")
            await update.message.reply_text(f"🛑 Error processing: {str(e)}")

    async def execute_local_tool(self, name, args):
        if name == "run_shell_command": return run_shell_command(**args)
        if name == "read_file": return read_file(**args)
        if name == "write_file": return write_file(**args)
        if name == "browse_url": return await browse_url(**args)
        if name == "run_global_shell": return run_global_shell(**args)
        if name == "read_global_file": return read_global_file(**args)
        if name == "write_global_file": return write_global_file(**args)
        if name == "get_screenshot": return await get_screenshot()
        if name == "desktop_interaction": return desktop_interaction(**args)
        if name == "get_system_info": return get_system_info()
        if name == "send_telegram_photo": return await send_telegram_photo(**args)
        return "Unknown tool."

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        action_type, action_id = data.split("_", 1)
        
        if action_id in self.pending_actions:
            self.action_results[action_id] = "Approved" if action_type == "approve" else "Denied"
            self.pending_actions[action_id].set()
            await query.edit_message_text(text=f"Action {action_type}ed.")

    async def heartbeat(self, context: ContextTypes.DEFAULT_TYPE):
        """Proactive background loop inspired by OpenClaw."""
        logger.info("OpenTron Heartbeat active.")
        while self.is_running:
            try:
                # Check for scheduled tasks in SCHEDULE.md
                schedule_path = os.path.join(WORKSPACE_DIR, "SCHEDULE.md")
                if os.path.exists(schedule_path):
                    with open(schedule_path, 'r', encoding='utf-8') as f:
                        schedule = f.read().strip()
                    
                    if schedule and self.last_chat_id:
                        logger.info(f"Heartbeat: Processing proactive tasks for {self.last_chat_id}")
                        session = self.get_chat_session(self.last_chat_id)
                        
                        # Trigger a "proactive thought"
                        prompt = f"SYSTEM: Checking SCHEDULE.md. Current tasks:\n{schedule}\nPerform any necessary actions and notify the user."
                        response = session.send_message(prompt)
                        
                        # Use bot instance to send message
                        await context.bot.send_message(
                            chat_id=self.last_chat_id, 
                            text=f"🤖 **Proactive Update**:\n{response.text}",
                            parse_mode='Markdown'
                        )
                
                await asyncio.sleep(600)  # 10 minute heartbeat
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(60)

# --- Start Bot ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🚥 **OpenTron Online**\n\n"
        "I am an autonomous digital operative, inspired by the digital frontier. I am now fully synchronized with The Grid.\n\n"
        "**System State:**\n"
        "- Owner: Suhaan\n"
        "- Protocol: Proactive & Independent\n\n"
        "How shall we alter the digital landscape today?"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 OpenTron de-rezzing. End of line.")
    os._exit(0) # Immediate kill

if __name__ == "__main__":
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not tg_token:
        print("Error: TELEGRAM_BOT_TOKEN missing in .env")
        exit(1)

    bot = OpenTronBot(gemini_key, tg_token)
    app = ApplicationBuilder().token(tg_token).build()

    print("OpenTron (Tron Edition) is starting...")
    
    # Command Handlers for Policy
    async def set_policy_high(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot.save_policy("HIGH")
        await update.message.reply_text("⚖️ **Policy: HIGH**\nI am now a Co-pilot. I will ask for approval before *any* action.", parse_mode='Markdown')

    async def set_policy_medium(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot.save_policy("MEDIUM")
        await update.message.reply_text("⚖️ **Policy: MEDIUM**\nStandard protocol. High-risk and workspace mutations require approval.", parse_mode='Markdown')

    async def set_policy_none(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot.save_policy("NONE")
        await update.message.reply_text("⚠️ **Policy: NONE**\nFull Autonomy. I will execute all commands without waiting for approval. Use with caution.", parse_mode='Markdown')

    async def show_policy(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"📊 **Current Review Policy**: `{bot.review_policy}`", parse_mode='Markdown')

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("high", set_policy_high))
    app.add_handler(CommandHandler("medium", set_policy_medium))
    app.add_handler(CommandHandler("none", set_policy_none))
    app.add_handler(CommandHandler("policy", show_policy))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.button_callback))
    
    # Add Heartbeat Job
    if app.job_queue:
        app.job_queue.run_once(bot.heartbeat, when=0)

    print("OpenTron (Tron Edition) is starting...")
    app.run_polling()
