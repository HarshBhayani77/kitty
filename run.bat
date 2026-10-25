@echo off
:: Windows launch script for Kitty AI
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

set VENV_DIR=KittyAI\.venv

:: Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo === Creating Virtual Environment ===
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
    python -m ensurepip --default-pip --upgrade
    python -m pip install --upgrade pip
    python -m pip install -r KittyAI\requirements.txt
) else (
    call "%VENV_DIR%\Scripts\activate.bat"
)

:: Launch Kitty AI
echo === Starting Kitty AI Companion ===
python KittyAI\main.py
pause
