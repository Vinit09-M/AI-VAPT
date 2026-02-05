@echo off
echo [*] Starting Auto_VAPT System...
echo [*] Launching Backend Server (Port 8000)...
start "Auto_VAPT Backend" cmd /k "python -m uvicorn src.api:app --reload"

echo [*] Launching Frontend Dashboard (Port 5173)...
cd frontend
start "Auto_VAPT Frontend" cmd /k "npm run dev"

echo [SUCCESS] System is booting up. Check the new windows.
pause
