@echo off
setlocal
cd /d "%~dp0"
title CCS v6.0.1 - Windows
if not exist ".venv\Scripts\python.exe" (
  echo Execute INSTALL_WINDOWS.bat primeiro.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -u windows_launcher.py
pause
