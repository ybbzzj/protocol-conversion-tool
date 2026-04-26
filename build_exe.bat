@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================================
echo Protocol Conversion Tool - PyInstaller Build
echo Python 3.8 + Windows 7
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto :NO_PYTHON
echo Python detected:
python --version
echo.

python -c "import PyInstaller" >nul 2>&1
if not errorlevel 1 goto :PYI_READY
echo PyInstaller not found. Installing pyinstaller==5.1 ...
python -m pip install pyinstaller==5.1
if errorlevel 1 goto :PYI_FAIL
:PYI_READY
echo PyInstaller ready.
python -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)"
echo.

python -c "import torch, transformers, regex" >nul 2>&1
if not errorlevel 1 goto :DEP_OK
echo Semantic dependencies not complete.
echo Please run install_paddle.bat first.
set /p CONTINUE="Continue build anyway? y/N: "
if /i not "%CONTINUE%"=="y" goto :CANCELLED
echo.
:DEP_OK

if exist "%ROOT%\public\dist\index.html" goto :FRONT_OK
echo Frontend build not found. Suggested commands:
echo    cd public
echo    npm install
echo    npm run build
echo.
set /p CONTINUE="Continue build without frontend dist? y/N: "
if /i not "%CONTINUE%"=="y" goto :CANCELLED
echo.
:FRONT_OK

if exist "%ROOT%\models\bge-small-zh-v1.5" goto :MODEL_OK
echo BGE model folder not found.
echo Please download model first: python download_model.py
echo.
set /p CONTINUE="Continue build without model? y/N: "
if /i not "%CONTINUE%"=="y" goto :CANCELLED
echo.
:MODEL_OK

echo ============================================================
echo Start building...
echo ============================================================
echo.

if exist "%ROOT%\build" rmdir /s /q "%ROOT%\build"
if exist "%ROOT%\dist" rmdir /s /q "%ROOT%\dist"

echo Running PyInstaller...
pyinstaller --clean "%ROOT%\build.spec"
if errorlevel 1 goto :BUILD_FAIL

echo Build completed successfully.

set "APP_DIR="
for /d %%D in ("%ROOT%\dist\*") do (
    set "APP_DIR=%%~fD"
    goto :APP_DIR_FOUND
)
:APP_DIR_FOUND

if not defined APP_DIR (
    echo WARNING: Cannot locate built app folder in dist.
    goto :DONE
)

if not exist "%ROOT%\models\bge-small-zh-v1.5" (
    echo WARNING: Source model folder not found. Skip model copy.
    goto :SHOW_OUTPUT
)

if not exist "%APP_DIR%\models" mkdir "%APP_DIR%\models"
xcopy "%ROOT%\models\bge-small-zh-v1.5" "%APP_DIR%\models\bge-small-zh-v1.5\" /E /I /Y >nul
if errorlevel 1 (
    echo WARNING: Model copy failed. Please copy models folder manually.
) else (
    echo Model copy completed.
)

:SHOW_OUTPUT
echo Output folder: %ROOT%\dist
if defined APP_DIR echo App folder: %APP_DIR%
goto :DONE

:NO_PYTHON
echo ERROR: Python not found. Please install Python 3.8 first.
goto :DONE

:PYI_FAIL
echo ERROR: PyInstaller install failed.
goto :DONE

:BUILD_FAIL
echo ============================================================
echo Build failed.
echo ============================================================
goto :DONE

:CANCELLED
echo Build cancelled.

:DONE
echo.
pause
exit /b 0
