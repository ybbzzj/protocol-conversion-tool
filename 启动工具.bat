@echo off

:: Get the directory of this script
set "CURRENT_DIR=%~dp0"

:: Define absolute paths
set "PYTHON_EXE=%CURRENT_DIR%venv\Scripts\python.exe"
set "APP_SCRIPT=%CURRENT_DIR%backend\app.py"

:: Set PYTHONPATH to allow imports from the root directory
set "PYTHONPATH=%CURRENT_DIR%"

echo Starting the application...
echo Please open your browser and go to: http://localhost:5001
echo (Do not close this window)
echo --------------------------------------------------------

:: Execute the application
"%PYTHON_EXE%" "%APP_SCRIPT%"

pause
