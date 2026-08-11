@echo off
setlocal
cd /d "%~dp0"
title CCS v6.0.1 - Testes
if not exist ".venv\Scripts\python.exe" (
  echo Execute INSTALL_WINDOWS.bat primeiro.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m compileall -q .
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto :error
".venv\Scripts\python.exe" health_check.py
if errorlevel 1 goto :error
".venv\Scripts\python.exe" telegram_test.py
if errorlevel 1 goto :error
echo.
echo Todos os testes foram concluidos.
pause
exit /b 0
:error
echo.
echo Algum teste falhou. Leia a mensagem acima.
pause
exit /b 1
