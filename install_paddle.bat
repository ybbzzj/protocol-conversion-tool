@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo 协议转换工具 - PaddlePaddle 依赖安装
echo ============================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Python 环境
    echo.
    echo 请先安装 Python 3.8
    pause
    exit /b 1
)

echo ✅ 检测到 Python 环境
python --version
echo.

REM 检查是否已安装 paddlepaddle
python -c "import paddle; print('✅ PaddlePaddle 版本:', paddle.__version__)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PaddlePaddle 已安装
) else (
    echo ⚠️  未检测到 PaddlePaddle
    echo.
    echo 📥 正在安装 PaddlePaddle...
    echo.
    
    REM 使用清华镜像源安装
    python -m pip install paddlepaddle==2.6.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    if %errorlevel% neq 0 (
        echo.
        echo ❌ PaddlePaddle 安装失败
        echo.
        echo 请尝试手动安装:
        echo   python -m pip install paddlepaddle==2.6.2
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ PaddlePaddle 安装完成
)

echo.

REM 检查是否已安装 paddlenlp
python -c "import paddlenlp; print('✅ PaddleNLP 版本:', paddlenlp.__version__)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PaddleNLP 已安装
) else (
    echo ⚠️  未检测到 PaddleNLP
    echo.
    echo 📥 正在安装 PaddleNLP...
    echo.
    
    REM 使用清华镜像源安装
    python -m pip install paddlenlp==2.6.1 -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    if %errorlevel% neq 0 (
        echo.
        echo ❌ PaddleNLP 安装失败
        echo.
        echo 请尝试手动安装:
        echo   python -m pip install paddlenlp==2.6.1
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ PaddleNLP 安装完成
)

echo.
echo ============================================================
echo ✅ 所有依赖安装完成！
echo ============================================================
echo.
echo 💡 现在可以运行：协议转换工具.exe
echo.
pause
