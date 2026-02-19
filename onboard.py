import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

# Custom Tron Theme
tron_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "neon": "bold blue",
    "grid": "dim white"
})

def initialize_directories():
    """Ensure basic folder structure exists."""
    dirs = ["workspace", "skills", "skills/browser", "skills/desktop"]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)

console = Console(theme=tron_theme)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    clear()
    header_text = Text(r"""
   ____                     _____                      
  / __ \____  ___  ____    |_   _| __ ___  _ __  
 / / / / __ \/ _ \/ __ \     | || '__/ _ \| '_ \ 
/ /_/ / /_/ /  __/ / / /     | || | | (_) | | | |
\____/ .___/\___/_/ /_/      |_||_|  \___/|_| |_|
    /_/                                          
    """, style="neon")
    console.print(header_text)
    console.print(Panel("[grid]Digital Frontier Synchronization Protocol [v1.0][/grid]", style="info"))

def stage_safety_consent():
    show_header()
    console.print("\n[bold yellow]⚠️ CORE SAFETY PROTOCOL[/bold yellow]")
    console.print("""
OpenTron is an autonomous digital operative with 'Unlimited Hands'.
By proceeding, you acknowledge that:
1. OpenTron can execute shell commands and manage files.
2. OpenTron can control your mouse and keyboard (with approval).
3. You are responsible for the agent's actions on your machine.
    """)
    if not Confirm.ask("Do you accept the terms of the Grid?"):
        console.print("[error]Synchronization aborted. End of line.[/error]")
        sys.exit()

def stage_env_config():
    show_header()
    console.print("\n[info]Phase 1: Neural Link Configuration[/info]")
    
    gemini_key = Prompt.ask("Enter your [neon]Gemini API Key[/neon] (Google AI Studio)")
    tg_token = Prompt.ask("Enter your [neon]Telegram Bot Token[/neon] (@BotFather)", default="")

    with open(".env", "w") as f:
        f.write(f"GEMINI_API_KEY={gemini_key}\n")
        f.write(f"TELEGRAM_BOT_TOKEN={tg_token}\n")
    
    console.print("[success]Neural link established.[/success]")
    time.sleep(1)

def stage_api_config():
    show_header()
    console.print("\n[info]Phase 1b: API Service Gateway[/info]")
    
    if Confirm.ask("Enable the OpenTron REST API Service?"):
        from uuid import uuid4
        default_key = f"tron-{str(uuid4())[:8]}"
        api_key = Prompt.ask("Set your [neon]OpenTron API Key[/neon]", default=default_key)
        
        with open(".env", "a") as f:
            f.write(f"OPENTRON_API_KEY={api_key}\n")
        
        console.print(f"[success]API Gateway configured. Key: {api_key}[/success]")
    else:
        console.print("[info]API Gateway remains offline.[/info]")
    time.sleep(1)

def stage_identity_synthesis():
    show_header()
    console.print("\n[info]Phase 2: Identity Synthesis[/info]")
    
    user_name = Prompt.ask("What is your name, User?", default="Suhaan")
    agent_name = Prompt.ask("What shall this agent be called?", default="OpenTron")
    vibe = Prompt.ask("Define the agent's 'Soul' vibe (e.g. Logical, Sarcastic, Proactive)", default="Logical & Proactive")

    # Update USER.md
    with open("USER.md", "w") as f:
        f.write(f"# USER PROFILE: {user_name}\n\n- Name: {user_name}\n- Access: Root/Admin\n- Role: Architect of the Grid\n")

    # Update IDENTITY.md
    with open("IDENTITY.md", "w") as f:
        f.write(f"# IDENTITY: {agent_name} 🚥\n\nI am **{agent_name}**, an autonomous digital operative. I serve {user_name}.\n\n## Core Directives\n- Autonomy: I act independently.\n- Precision: I execute bit-perfect cycles.\n")

    # Update SOUL.md personality
    with open("SOUL.md", "a") as f:
        f.write(f"\n## User Synthesis\n- Vibe: {vibe}\n- Synchronized on: {time.strftime('%Y-%m-%d')}\n")

    console.print(f"[success]Identity synthesized. Welcome, {user_name}. Welcome, {agent_name}.[/success]")
    time.sleep(1)

def stage_platform_selection():
    show_header()
    console.print("\n[info]Phase 3: Platform Selection[/info]")
    choice = Prompt.ask("Where shall we operate?", choices=["Telegram", "CLI", "Both"], default="Telegram")
    
    console.print(f"[info]Configuring {choice} interface...[/info]")
    time.sleep(1)
    return choice

def stage_first_directive():
    show_header()
    console.print("\n[info]Phase 4: The First Directive[/info]")
    console.print("[grid]What is OpenTron's first objective in the Grid?[/grid]")
    task = Prompt.ask("Enter First Directive", default="Analyze my local system and summarize my capabilities.")
    
    schedule_path = "workspace/SCHEDULE.md"
    with open(schedule_path, "w") as f:
        f.write(f"# First Directive\n- [ ] {task}\n")
    
    console.print("[success]Directive encoded into the memory stream.[/success]")
    time.sleep(1)

def finalize_onboarding(platform):
    show_header()
    console.print("\n[bold green]SYNCHRONIZATION COMPLETE[/bold green]")
    console.print(f"OpenTron is ready to serve in [neon]{platform}[/neon] mode.")
    
    if Confirm.ask("Would you like to wake OpenTron now?"):
        if platform == "Telegram" or platform == "Both":
            console.print("[info]Booting Telegram Interface...[/info]")
            os.system(f"{sys.executable} opentron_telegram.py")
        else:
            console.print("[info]Booting CLI Interface...[/info]")
            os.system(f"{sys.executable} opentron_cli.py")

def main():
    try:
        initialize_directories()
        stage_safety_consent()
        stage_env_config()
        stage_api_config()
        stage_identity_synthesis()
        platform = stage_platform_selection()
        stage_first_directive()
        finalize_onboarding(platform)
    except KeyboardInterrupt:
        console.print("\n[error]Onboarding interrupted.[/error]")
        sys.exit()

if __name__ == "__main__":
    main()
