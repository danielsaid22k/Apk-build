@echo off
setlocal
cd /d "%~dp0"
title CCS v6.0.1 - Migrar dados antigos

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado.
  echo Execute INSTALL_WINDOWS.bat primeiro.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -u migrate_previous_data.py
set "EXIT_CODE=%ERRORLEVEL%"
echo.
pause
exit /b %EXIT_CODE%
