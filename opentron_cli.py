import os
import sys
import subprocess
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
import apprise
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv
import google.generativeai as genai
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pyautogui
import mss
import psutil
from PIL import Image

# --- Configuration ---
load_dotenv()

# Setup Logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("rich")
console = Console()

# Constants
WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")
POLICY_FILE = os.path.join(WORKSPACE_DIR, "POLICY.md")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

# --- Tool Functions ---

def run_shell_command(command: str) -> str:
    """Executes a shell command in the local workspace."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=WORKSPACE_DIR
        )
        output = result.stdout
        if result.stderr:
            output += f"\nError Output:\n{result.stderr}"
        return output.strip() or "Command executed with no output."
    except Exception as e:
        return f"Error executing command: {str(e)}"

def read_file(file_path: str) -> str:
    """Reads a file from the workspace."""
    try:
        safe_path = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
        if not safe_path.startswith(WORKSPACE_DIR):
            return "Error: Access denied. File must be within the workspace directory."
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(file_path: str, content: str) -> str:
    """Writes content to a file in the workspace."""
    try:
        safe_path = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
        if not safe_path.startswith(WORKSPACE_DIR):
            return "Error: Access denied. File must be within the workspace directory."
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def send_notification(service_url: str, title: str, body: str) -> str:
    """Sends a notification via Apprise (Discord, Telegram, etc.)."""
    try:
        apobj = apprise.Apprise()
        apobj.add(service_url)
        success = apobj.notify(body=body, title=title)
        return "Notification sent successfully." if success else "Failed to send notification."
    except Exception as e: return f"Error: {str(e)}"
async def browse_url(url: str) -> str:
    """Browse a URL and return a semantic text snapshot."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            for script in soup(["script", "style"]): script.decompose()
            text = soup.get_text(separator=" ", strip=True)
            await browser.close()
            return f"--- SNAPSHOT OF {url} ---\n{text[:5000]}..."
    except Exception as e: return f"Error browsing {url}: {str(e)}"

def run_global_shell(command: str) -> str:
    """Execute a shell command ANYWHERE on the system. HIGH RISK."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return (result.stdout + (f"\nError:\n{result.stderr}" if result.stderr else "")).strip() or "Success"
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
    """Capture the current screen."""
    try:
        with mss.mss() as sct:
            filename = os.path.join(WORKSPACE_DIR, "current_screen.png")
            sct.shot(output=filename)
            return f"Screenshot saved to workspace/current_screen.png"
    except Exception as e: return f"Error: {str(e)}"

def desktop_interaction(action: str, params: dict) -> str:
    """Interact with the desktop GUI."""
    try:
        if action == "move": pyautogui.moveTo(params.get("x", 0), params.get("y", 0))
        elif action == "click": pyautogui.click(button=params.get("button", "left"))
        elif action == "type": pyautogui.write(params.get("text", ""), interval=params.get("interval", 0.1))
        elif action == "press": pyautogui.press(params.get("key", "enter"))
        return f"Successfully performed {action}"
    except Exception as e: return f"Error: {str(e)}"

def get_system_info() -> str:
    """Get CPU, Memory, and Disk info."""
    try:
        return f"CPU: {psutil.cpu_percent()}%, RAM: {psutil.virtual_memory().percent}%, Disk: {psutil.disk_usage('/').percent}%"
    except Exception as e: return f"Error: {str(e)}"

# --- Prompt Management ---

class PromptManager:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.components = ["IDENTITY.md", "SOUL.md", "AGENTS.md", "KNOWLEDGE.md", "USER.md", "TOOLS.md"]

    def assemble_prompt(self) -> str:
        prompt_parts = []
        for component in self.components:
            path = os.path.join(self.root_dir, component)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f: prompt_parts.append(f.read())
        
        skills_dir = os.path.join(self.root_dir, "skills")
        if os.path.exists(skills_dir):
            for skill_name in os.listdir(skills_dir):
                skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
                if os.path.exists(skill_path):
                    with open(skill_path, 'r', encoding='utf-8') as f:
                        prompt_parts.append(f"\n## SKILL: {skill_name.upper()}\n{f.read()}")
        return "\n\n".join(prompt_parts)

# Define the tools for Gemini (Synchronized with Telegram)
tools = [
    run_shell_command, read_file, write_file, browse_url,
    run_global_shell, read_global_file, write_global_file,
    get_screenshot, desktop_interaction, get_system_info
]

# --- Agent Logic ---

class OpenTronGemini:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            console.print("[bold red]Error: GEMINI_API_KEY not found.[/bold red]")
            sys.exit(1)
        
        genai.configure(api_key=self.api_key)
        
        # Load System Prompt from grid
        prompt_manager = PromptManager(os.getcwd())
        system_instruction = prompt_manager.assemble_prompt()

        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=tools,
            system_instruction=system_instruction
        )
        self.chat_session = self.model.start_chat(enable_automatic_function_calling=False)
        self.review_policy = self.load_policy()

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
        console.print(f"[bold cyan]Policy updated to: {policy}[/bold cyan]")

    async def chat(self, user_input: str):
        # Handle Policy Commands
        cmd = user_input.lower().strip()
        if cmd == "/high":
            self.save_policy("HIGH")
            console.print("[info]OpenTron is now in HIGH oversight mode (Co-pilot).[/info]")
            return
        if cmd == "/medium":
            self.save_policy("MEDIUM")
            console.print("[info]OpenTron is now in MEDIUM oversight mode (Assistant).[/info]")
            return
        if cmd == "/none":
            self.save_policy("NONE")
            console.print("[warning]OpenTron is now in NONE oversight mode (Full Autonomy).[/warning]")
            return
        if cmd == "/policy":
            console.print(f"[info]Current Policy: {self.review_policy}[/info]")
            return

        response = self.chat_session.send_message(user_input)
        
        while True:
            if response.text and not response.candidates[0].content.parts[0].function_call:
                console.print(Panel(Markdown(response.text), title="OpenTron", border_style="green"))
                break
            
            for part in response.candidates[0].content.parts:
                if fn := part.function_call:
                    func_name = fn.name
                    args = dict(fn.args)
                    
                    console.print(Panel(f"[bold yellow]Tool Request:[/bold yellow] {func_name}\n[dim]{json.dumps(args, indent=2)}[/dim]", border_style="yellow"))
                    
                    # Policy Gatekeeper
                    high_risk = ["run_global_shell", "read_global_file", "write_global_file", "desktop_interaction", "run_shell_command", "write_file"]
                    
                    if self.review_policy == "HIGH":
                        approval_tools = [func_name]
                    elif self.review_policy == "NONE":
                        approval_tools = []
                    else: # MEDIUM
                        approval_tools = high_risk
                    
                    if func_name in approval_tools:
                        if not Confirm.ask("[bold red]Allow this action?[/bold red]"):
                            response = self.chat_session.send_message(
                                genai.protos.Content(parts=[genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(name=func_name, response={"result": "User denied action."})
                                )])
                            )
                            continue

                    result = await self.execute_local_tool(func_name, args)
                    console.print(f"[blue]Result:[/blue] {str(result)[:500]}...")
                    
                    response = self.chat_session.send_message(
                        genai.protos.Content(parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(name=func_name, response={"result": result})
                        )])
                    )

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
        return "Unknown tool."

# --- Main CLI ---

def main():
    console.print(Panel("[bold green]OpenTron Digital Frontier CLI[/bold green]\nIntegrated Grid | System Tools | Autonomous", border_style="blue"))
    agent = OpenTronGemini()
    
    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            if user_input.lower() in ["exit", "quit"]: break
            asyncio.run(agent.chat(user_input))
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
