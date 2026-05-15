@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo 离线依赖包安装工具
echo Python 3.8 + Windows 7 专用版本
echo ============================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Python，请先安装 Python 3.8
    pause
    exit /b 1
)

echo ✅ 检测到 Python 环境
python --version
echo.

REM 设置下载目录
set DOWNLOAD_DIR=%~dp0offline_packages

REM 检查下载目录是否存在
if not exist "%DOWNLOAD_DIR%" (
    echo ❌ 错误：找不到离线包目录：%DOWNLOAD_DIR%
    echo 请先使用 download_offline_packages.py 下载依赖包
    pause
    exit /b 1
)

echo 📦 找到离线包目录：%DOWNLOAD_DIR%
echo.

REM 检查 requirements.txt
set REQUIREMENTS_FILE=%~dp0requirements.txt
if not exist "%REQUIREMENTS_FILE%" (
    set REQUIREMENTS_FILE=%~dp0backend\requirements.txt
)

if not exist "%REQUIREMENTS_FILE%" (
    echo ❌ 错误：找不到 requirements.txt 文件
    pause
    exit /b 1
)

echo 📋 使用 requirements 文件：%REQUIREMENTS_FILE%
echo.

echo ============================================================
echo 开始安装离线依赖包...
echo ============================================================
echo.

REM 执行安装
python -m pip install --no-index --find-links="%DOWNLOAD_DIR%" -r "%REQUIREMENTS_FILE%"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo ✅ 所有依赖包安装完成！
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo ❌ 安装过程中出现错误
    echo 可能的原因:
    echo   1. 离线包不完整
    echo   2. Python 版本不匹配（需要 Python 3.8）
    echo   3. 系统架构不匹配（需要 Windows 64 位）
    echo ============================================================
)

echo.
pause
