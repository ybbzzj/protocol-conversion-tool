@echo off
chcp 65001 >nul

echo ============================================================
echo 创建 PaddlePaddle libs 目录（解决 DLL 路径问题）
echo ============================================================
echo.

REM 获取 exe 所在目录（去掉末尾的反斜杠）
set "EXE_DIR=%~dp0"
set "EXE_DIR=%EXE_DIR:~0,-1%"

echo 📁 EXE 目录：%EXE_DIR%
echo.

REM 创建 paddle base 目录结构
if not exist "%EXE_DIR%paddle\base" (
    echo 创建目录：%EXE_DIR%paddle\base
    mkdir "%EXE_DIR%paddle\base"
)

REM 创建 libs 目录
if not exist "%EXE_DIR%paddle\libs" (
    echo 创建目录：%EXE_DIR%paddle\libs
    mkdir "%EXE_DIR%paddle\libs"
)

echo ✅ libs 目录已创建
echo.

REM 使用 py -3.8 检查 PaddlePaddle
echo 🐍 检查 Python 3.8 环境...
py -3.8 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未找到 Python 3.8
    pause
    exit /b 1
)

echo ✅ 使用 Python 3.8
echo.

REM 检查是否已安装 PaddlePaddle
echo 🔍 检查 PaddlePaddle...
py -3.8 -c "import paddle; print('PaddlePaddle 版本:', paddle.__version__)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PaddlePaddle 已安装
) else (
    echo.
    echo ⚠️  未检测到 PaddlePaddle
    echo.
    echo 💡 可能的原因:
    echo   1. install_offline.bat 没有成功执行
    echo   2. Python 环境路径不正确
    echo.
    echo 📥 请先确保已运行：install_offline.bat
    echo.
    echo 或者手动安装:
    echo   py -3.8 -m pip install paddlepaddle==2.6.2 paddlenlp==2.6.1
    echo.
    pause
    exit /b 1
)

echo.
echo 📦 正在复制 DLL 文件...
echo.

REM 使用 Python 脚本复制 DLL 文件
py -3.8 "%~dp0copy_paddle_dlls.py" "%EXE_DIR%"

echo.
echo ============================================================
echo ✅ libs 目录和 DLL 文件准备完成！
echo ============================================================
echo.
echo 💡 现在可以运行：协议转换工具.exe
echo.
pause
