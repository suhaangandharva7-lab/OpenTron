# install.ps1 - OpenTron Installer 🚥

$RepoUrl = "https://github.com/opentron/agent.git"
$TargetDir = "opentron-agent"

Write-Host "🚥 OpenTron Installation Sequence Initiated..." -ForegroundColor Cyan

# 1. Dependency Check
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python 3.10+ not found. Please install it first." -ForegroundColor Red
    exit
}

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git not found. Please install it first." -ForegroundColor Red
    exit
}

# 2. Clone Repository
if (!(Test-Path $TargetDir)) {
    Write-Host "📂 Cloning the Grid into $TargetDir..." -ForegroundColor Cyan
    git clone $RepoUrl $TargetDir
}

Set-Location $TargetDir

# 3. Create Virtual Environment
if (!(Test-Path "venv")) {
    Write-Host "📦 Creating Digital Environment (venv)..." -ForegroundColor Cyan
    python -m venv venv
}

# 4. Install Hands (Requirements)
Write-Host "🦾 Installing Operative Tools (Requirements)..." -ForegroundColor Cyan
.\venv\Scripts\pip install -r requirements.txt

# 5. Boot Onboarding
Write-Host "🌌 Launching Onboarding Protocol..." -ForegroundColor Cyan
.\venv\Scripts\python.exe onboard.py
