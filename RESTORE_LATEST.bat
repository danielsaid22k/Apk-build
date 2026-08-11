@echo off
setlocal
cd /d "%~dp0"
echo ATENCAO: pare o programa antes de restaurar.
pause
".venv\Scripts\python.exe" restore_latest.py
pause
