@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" backup_now.py
pause
