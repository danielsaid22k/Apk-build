@echo off
setlocal
cd /d "%~dp0"
title CCS v6.0.1 - Instalacao

echo ================================================
echo  Crypto Certified Switch v6.0.1 - Windows
echo ================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo Python nao foi encontrado.
  where winget >nul 2>nul
  if errorlevel 1 (
    echo Instale Python 3.12 ou superior em:
    echo https://www.python.org/downloads/windows/
    echo Marque a opcao "Add Python to PATH".
    pause
    exit /b 1
  )
  echo Instalando Python pelo winget...
  winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  py -3 -m venv .venv
)

echo Atualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

if exist requirements.txt (
  echo Instalando dependencias...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

if not exist ".env" copy /Y ".env.example" ".env" >nul

for %%D in (data logs backups tools proposals\pending proposals\submitted proposals\completed proposals\rejected proposals\failed) do (
  if not exist "%%D" mkdir "%%D"
)

echo Instalando Cloudflared...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_cloudflared.ps1"
if errorlevel 1 (
  echo Falha ao instalar o cloudflared.
  pause
  exit /b 1
)

echo.
echo Instalacao concluida.
echo Proximos passos:
echo   1. CONFIGURE_TELEGRAM.bat
echo   2. CONFIGURE_WALLETS.bat
echo   3. TEST_WINDOWS.bat
echo   4. START_WINDOWS.bat
echo.
pause
