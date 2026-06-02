@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo 协议转换工具 - PyInstaller 打包工具
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

REM 检查是否安装了 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  未检测到 PyInstaller，正在安装...
    python -m pip install pyinstaller==5.1
    if %errorlevel% neq 0 (
        echo ❌ PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo ✅ PyInstaller 已安装
python -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)"
echo.

REM 检查语义模型运行依赖。缺失时必须在打包前解决，否则 exe 会启动失败。
python -c "import onnxruntime, tokenizers; print('onnxruntime:', onnxruntime.__version__); print('tokenizers: ok')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  未检测到 onnxruntime/tokenizers，正在安装语义模型运行依赖...
    python -m pip install onnxruntime==1.14.1 tokenizers==0.13.3
    if %errorlevel% neq 0 (
        echo ❌ 语义模型运行依赖安装失败
        echo    请手动执行：
        echo    python -m pip install onnxruntime==1.14.1 tokenizers==0.13.3
        pause
        exit /b 1
    )
)

python -c "import onnxruntime, tokenizers; print('✅ onnxruntime:', onnxruntime.__version__); print('✅ tokenizers: ok')"
if %errorlevel% neq 0 (
    echo ❌ onnxruntime/tokenizers 仍不可用，停止打包
    pause
    exit /b 1
)
echo.

REM transformers 不再参与运行时打包；如果环境中安装了它，build.spec 会显式排除。
python -c "import importlib.util; print('ℹ️ transformers installed:', importlib.util.find_spec('transformers') is not None)"
echo.

REM 构建并校验前端资源，避免 index.html 引用不存在的 hash 文件导致白屏
set "HAS_NPM=0"
if exist "%~dp0public\package.json" (
    where npm >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️  未检测到 npm，无法自动构建前端
        where node >nul 2>&1
        if !errorlevel! equ 0 (
            if exist "%~dp0public\node_modules\vite\bin\vite.js" (
                echo 检测到 node 和本地 vite，使用 node 直接构建前端...
                set "HAS_NPM=1"
                pushd "%~dp0public"
                node node_modules\vite\bin\vite.js build
                if !errorlevel! neq 0 (
                    popd
                    echo ❌ 前端构建失败
                    pause
                    exit /b 1
                )
                popd
                echo ✅ 前端构建完成
                echo.
            )
        )
    ) else (
        set "HAS_NPM=1"
        echo ============================================================
        echo 构建前端资源...
        echo ============================================================
        pushd "%~dp0public"
        if not exist "node_modules" (
            echo 安装前端依赖...
            call npm install
            if !errorlevel! neq 0 (
                popd
                echo ❌ 前端依赖安装失败
                pause
                exit /b 1
            )
        )
        call npm run build
        if !errorlevel! neq 0 (
            popd
            echo ❌ 前端构建失败
            pause
            exit /b 1
        )
        popd
        echo ✅ 前端构建完成
        echo.
    )
)

if not exist "%~dp0public\dist\index.html" (
    echo ❌ 前端 dist 不存在：%~dp0public\dist\index.html
    pause
    exit /b 1
)

python "%~dp0verify_frontend_dist.py" "%~dp0public\dist"
if %errorlevel% neq 0 (
    echo ❌ 前端 dist 资源不完整
    if "!HAS_NPM!"=="0" (
        echo    当前机器未检测到 npm，无法自动修复 dist
        echo    请安装 Node.js 后重新运行 build_exe.bat，或在 public 目录执行 npm install && npm run build
    ) else (
        echo    请检查上方 npm run build 输出
    )
    pause
    exit /b 1
)
echo ✅ 前端资源校验通过
echo.

REM 检查模型文件
set "MODEL_DIRNAME=bge-small-zh-v1.5"
set "MODEL_SRC=%~dp0models\%MODEL_DIRNAME%"
if not exist "%MODEL_SRC%" (
    echo ⚠️  未检测到语义模型目录
    echo.
    echo 📥 请先下载模型：
    echo    python download_model.py
    echo.
    echo 💡 模型说明:
    echo    - 推荐模型：Xenova/bge-small-zh-v1.5
    echo    - 下载需要联网
    echo    - 如果无法下载，可手动从 HuggingFace 下载后放入 models 目录
    echo.
    set /p CONTINUE="是否继续打包？（模型将不可用）(y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo 取消打包
        pause
        exit /b 1
    )
    echo.
)

echo ============================================================
echo 开始打包...
echo ============================================================
echo.

REM 清理旧的构建文件
if exist "%~dp0build" (
    echo 清理旧的构建目录...
    rmdir /s /q "%~dp0build"
)

if exist "%~dp0dist" (
    echo 清理旧的发布目录...
    rmdir /s /q "%~dp0dist"
)

echo.
echo 执行 PyInstaller...
echo.

REM 使用 spec 文件进行打包
pyinstaller --clean "%~dp0build.spec"

if %errorlevel% equ 0 (
    echo.
    echo 正在复制语义模型到发布目录...
    set "MODEL_DST=%~dp0dist\协议转换工具\models\!MODEL_DIRNAME!"
    
    if exist "!MODEL_SRC!" (
        if not exist "%~dp0dist\协议转换工具\models" (
            mkdir "%~dp0dist\协议转换工具\models"
        )
        
        robocopy "!MODEL_SRC!" "!MODEL_DST!" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul
        set "ROBO_EXIT=!errorlevel!"
        
        if !ROBO_EXIT! GEQ 8 (
            echo ⚠️  模型复制失败（robocopy exit code: !ROBO_EXIT!）
            echo    请手动复制目录：
            echo    !MODEL_SRC!  ^>  !MODEL_DST!
        ) else (
            echo ✅ 语义模型复制完成：!MODEL_DST!
        )
    ) else (
        echo ⚠️  未找到模型目录，跳过自动复制：!MODEL_SRC!
    )

    echo.
    echo ============================================================
    echo ✅ 打包完成！
    echo ============================================================
    echo.
    echo 📦 发布位置：%~dp0dist\协议转换工具
    echo.
    echo 💡 使用说明:
    echo    1. 将整个 '协议转换工具' 文件夹复制到客户机器
    echo    2. 首次运行前，请确保 models 目录存在
    echo    3. 运行 '协议转换工具.exe'
    echo.
    echo ⚠️  注意事项:
    echo    - 模型文件较大（约 100MB），首次启动可能需要几秒钟
    echo    - models 目录必须与 exe 在同一层级
    echo    - 语义模型目录：models\bge-small-zh-v1.5
    echo.
    echo 📂 部署结构:
    echo    协议转换工具/
    echo    ├── 协议转换工具.exe
    echo    └── models/
    echo        └── bge-small-zh-v1.5/
    echo.
) else (
    echo.
    echo ============================================================
    echo ❌ 打包失败
    echo ============================================================
    echo.
    echo 可能的原因:
    echo   1. 依赖包缺失或不完整
    echo   2. 前端资源未正确构建
    echo   3. 模型文件损坏
    echo   4. 磁盘空间不足
    echo.
    echo 建议:
    echo   1. 检查上面的错误信息
    echo   2. 运行 install_offline.bat 确保所有依赖已安装
    echo   3. 重新运行此脚本
    echo.
)

pause
