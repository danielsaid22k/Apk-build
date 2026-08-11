@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute INSTALL_WINDOWS.bat primeiro.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" configure_telegram.py
pause
