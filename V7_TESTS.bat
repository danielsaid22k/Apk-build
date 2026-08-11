@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Execute INSTALL_WINDOWS.bat primeiro.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m compileall -q .
if errorlevel 1 exit /b 1
echo Testes v7 concluídos.
pause
