@echo off
echo ===================================================
echo   STARTING JARVIS VISUAL SYSTEM
echo ===================================================
echo.
echo [1/3] Launching JARVIS Core + API (Port 8000)...
start "JARVIS Unified Core" /min cmd /k "python jarvis_core/core/unified_server.py"

echo [2/3] Launching Web Interface (Port 5173)...
cd web_interface
start "JARVIS Web Interface" /min cmd /k "npm run dev"

echo [3/3] Opening Browser...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo JARVIS Visualizer is running.
echo API: ws://localhost:8000/ws
echo GUI: http://localhost:5173
echo.
echo Close the popup windows to stop the servers.
pause
