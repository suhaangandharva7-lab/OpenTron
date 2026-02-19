@echo off
echo 🚥 Booting OpenTron API Grid...
set PORT=8000
python -m uvicorn opentron_api:app --host 0.0.0.0 --port %PORT% --reload
pause
