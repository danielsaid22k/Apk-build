@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" telegram_test.py
pause
