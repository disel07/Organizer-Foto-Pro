@echo off
cd /d "%~dp0"
title Organizer Foto Pro Launcher

echo ========================================
echo   Organizer Foto Pro - Avvio
echo ========================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRORE] Python non trovato!
    echo Per favore installa Python da python.org
    pause
    exit /b
)

REM Check/Create Venv
if not exist "app\venv" (
    echo [CONFIG] Creazione ambiente virtuale...
    python -m venv app\venv
    
    echo [INSTALL] Installazione librerie...
    app\venv\Scripts\pip install -r app\photo_organizer\requirements.txt
)

REM Launch
echo [START] Avvio programma...
cd app
start /B venv\Scripts\pythonw photo_organizer\main.py

REM Exit launcher immediately
exit
