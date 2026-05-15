@echo off
setlocal enabledelayedexpansion

:: Set console to UTF-8 to prevent garbled characters, though we avoid them now.
chcp 65001 >nul

echo ==========================================
echo    Protocol Tool - EXE Builder
echo ==========================================

:: 1. Check for virtual environment
set "VENV_PATH=%~dp0venv"
if not exist "!VENV_PATH!\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run 'start_tool.bat' first.
    pause
    exit /b
)

:: 2. Install PyInstaller
echo [1/2] Installing PyInstaller...
"!VENV_PATH!\Scripts\python.exe" -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 3. Run the build process
echo [2/2] Building EXE, this may take a while...
"!VENV_PATH!\Scripts\pyinstaller.exe" build.spec

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Build failed. Please check the logs above for details.
) else (
    echo.
    echo [SUCCESS] Build complete!
    echo The application is in the 'dist\协议转换工具' folder.
)

pause
