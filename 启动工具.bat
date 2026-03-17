@echo off
setlocal enabledelayedexpansion

:: Set encoding to UTF-8
chcp 65001 >nul

echo ==========================================
echo    Protocol Tool - Quick Start
echo ==========================================

:: 1. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b
)

:: 2. Check Virtual Environment
set "VENV_PATH=%~dp0venv"
if exist "!VENV_PATH!\Scripts\python.exe" (
    echo [1/2] Virtual environment found. Checking dependencies...
    
    "!VENV_PATH!\Scripts\python.exe" -c "import flask_cors" >nul 2>nul
    if !errorlevel! neq 0 (
        echo [INFO] Missing dependencies. Installing...
        "!VENV_PATH!\Scripts\python.exe" -m pip install -r "%~dp0backend\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
    )
) else (
    echo [1/2] Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b
    )
    echo Installing dependencies...
    "!VENV_PATH!\Scripts\python.exe" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
    "!VENV_PATH!\Scripts\python.exe" -m pip install -r "%~dp0backend\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
)

:: 3. Start Service
echo [2/2] Starting service...
echo ------------------------------------------
echo Please visit: http://localhost:5001
echo ------------------------------------------

:: Kill any existing process on port 5001 to avoid conflicts
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5001') do (
    taskkill /f /pid %%a >nul 2>&1
)

set "PYTHONPATH=%~dp0"
"!VENV_PATH!\Scripts\python.exe" "%~dp0backend\app.py"

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Program crashed. Please check the logs above.
)

pause
