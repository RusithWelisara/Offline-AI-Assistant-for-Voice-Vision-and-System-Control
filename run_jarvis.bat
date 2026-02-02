@echo off
setlocal

:: Set the project root directory
set "PROJECT_ROOT=%~dp0jarvis_core"

:: Ensure you are in the directory where this script is located
cd /d "%~dp0"

:: Add the current directory to PYTHONPATH so jarvis_core can be imported
set "PYTHONPATH=%~dp0;%PYTHONPATH%"

echo Starting JARVIS...
:: python "%PROJECT_ROOT%\main.py"
python "D:\AI Assistant\Voice Assistant (Gemini API)\main.py"

if errorlevel 1 (
    echo JARVIS exited with error or was stopped.
    pause
)
