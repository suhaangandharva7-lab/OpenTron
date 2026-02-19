# setup_persistence.ps1 - OpenTron 24/7 Mode

$TaskName = "OpenTronAgent"
$BotScript = "OpenTron_telegram.py"
$WorkingDir = Get-Location
$VenvPython = Join-Path $WorkingDir "venv\Scripts\python.exe"
$ArgList = "OpenTron_telegram.py"

Write-Host "🦞 Setting up OpenTron persistence..."

$StartupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$BatchFile = Join-Path $WorkingDir "run_OpenTron.bat"
$ShortcutFile = Join-Path $StartupPath "OpenTron.lnk"

Write-Host "🦞 Setting up OpenTron Startup Folder persistence..."

# 1. Create a batch file to launch the bot
$BatchContent = @"
@echo off
cd /d "$WorkingDir"
:loop
"%VenvPython%" OpenTron_telegram.py
echo Bot crashed! Restarting in 10 seconds...
timeout /t 10
goto loop
"@
$BatchContent | Out-File -FilePath $BatchFile -Encoding ascii

# 2. Create a shortcut in the Startup folder using COM
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutFile)
$Shortcut.TargetPath = "cmd.exe"
$Shortcut.Arguments = "/c `"$BatchFile`""
$Shortcut.WorkingDirectory = $WorkingDir
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.Save()

Write-Host "✅ OpenTron is now set to run 24/7!"
Write-Host "A shortcut has been added to your Startup folder: $ShortcutFile"
Write-Host "It will launch minimized and restart itself if it crashes."
