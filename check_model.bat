@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo 协议转换工具 - 模型部署检查
echo ============================================================
echo.

REM 检查 models 目录
if not exist "%~dp0models" (
    echo ❌ 错误：未找到 models 目录
    echo.
    echo 📥 请运行以下命令下载模型:
    echo    python download_model.py
    echo.
    pause
    exit /b 1
)

REM 检查 ONNX 模型目录（兼容新旧目录名）
set "model_dir=%~dp0models\bge-small-zh-v1.5"
if not exist "%model_dir%" (
    if exist "%~dp0models\bge-small-zh-v1.5-onnx" (
        set "model_dir=%~dp0models\bge-small-zh-v1.5-onnx"
    )
)
if not exist "%model_dir%" (
    echo ❌ 错误：未找到 ONNX 语义模型目录
    echo.
    echo 📥 请运行以下命令下载模型:
    echo    python download_model.py
    echo.
    pause
    exit /b 1
)

REM 检查关键文件
set "onnx_file=%model_dir%\onnx\model.onnx"
if not exist "%onnx_file%" (
    set "onnx_file=%model_dir%\onnx\model_int8.onnx"
)
if not exist "%onnx_file%" (
    set "onnx_file=%model_dir%\onnx\model_quantized.onnx"
)

if not exist "%model_dir%\config.json" (
    echo ❌ 错误：缺少 config.json
    goto :incomplete
)

if not exist "%model_dir%\tokenizer.json" (
    echo ❌ 错误：缺少 tokenizer.json
    goto :incomplete
)

if not exist "%model_dir%\vocab.txt" (
    echo ❌ 错误：缺少 vocab.txt
    goto :incomplete
)

if not exist "%onnx_file%" (
    echo ❌ 错误：缺少 onnx/model.onnx 或 onnx/model_int8.onnx
    goto :incomplete
)

echo ✅ 模型文件检查完成！
echo.
echo 📦 模型位置：%model_dir%
echo.

REM 检查文件大小
for %%A in ("%onnx_file%") do (
    set "size=%%~zA"
    set /a size_mb=%%~zA/1024/1024
    echo 📊 ONNX 大小：!size_mb! MB
)

echo.
echo ✅ 模型文件完整，可以正常使用！
echo.
goto :end

:incomplete
echo.
echo ⚠️  模型文件不完整，请重新下载
echo.
echo 📥 请运行：python download_model.py
echo.
pause
exit /b 1

:end
pause
