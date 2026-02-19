@echo off
cd /d "C:\Users\shash\OpenTron-agent"
:loop
"%VenvPython%" OpenTron_telegram.py
echo Bot crashed! Restarting in 10 seconds...
timeout /t 10
goto loop
