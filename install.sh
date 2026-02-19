#!/bin/bash

# install.sh - OpenTron Universal Unix Installer 🚥

echo -e "\033[0;36m🚥 OpenTron Installation Sequence Initiated...\033[0m"

# 1. Dependency Checks
if ! command -v python3 &> /dev/null; then
    echo -e "\033[0;31m❌ Python 3 not found. Please install it first.\033[0m"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "\033[0;31m❌ Git not found. Please install it first.\033[0m"
    exit 1
fi

# 2. Clone Repository
REPO_URL="https://github.com/opentron/agent.git" # Placeholder OR actual URL if known
TARGET_DIR="opentron-agent"

if [ ! -d "$TARGET_DIR" ]; then
    echo -e "\033[0;36m📂 Cloning the Grid into $TARGET_DIR...\033[0m"
    git clone "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR" || exit

# 3. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo -e "\033[0;36m📦 Creating Digital Environment (venv)...\033[0m"
    python3 -m venv venv
fi

# 4. Install Requirements
echo -e "\033[0;36m🦾 Installing Operative Tools (Requirements)...\033[0m"
./venv/bin/pip install -r requirements.txt

# 5. Boot Onboarding
echo -e "\033[0;36m🌌 Launching Onboarding Protocol...\033[0m"
./venv/bin/python onboard.py
