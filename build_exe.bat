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

REM 检查前端是否构建
if not exist "%~dp0public\dist\index.html" (
    echo ⚠️  前端未构建，请先执行以下命令:
    echo    cd public
    echo    npm install
    echo    npm run build
    echo.
    set /p CONTINUE="是否继续打包？(前端资源可能不完整) (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo 取消打包
        pause
        exit /b 1
    )
    echo.
)

REM 检查模型文件（只校验 onnx 文件是否存在，不再判断大小）
set "MODEL_ONNX=%~dp0models\bge-small-zh-v1.5-onnx\onnx\model.onnx"
set "MODEL_OK=1"
if not exist "!MODEL_ONNX!" set "MODEL_OK=0"
if "!MODEL_OK!"=="0" (
    echo ⚠️  语义模型缺失：未找到 model.onnx
    echo     路径: !MODEL_ONNX!
    echo.
    echo 💡 常见原因与处理:
    echo    - 若用 git 拉取代码: 模型由 Git LFS 托管，请先安装 git-lfs 再拉取:
    echo        git lfs install ^&^& git lfs pull
    echo    - 若需重新下载: python download_model.py ^(需联网^)
    echo.
    set /p CONTINUE="是否继续打包？（模型将不可用）(y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo 取消打包
        pause
        exit /b 1
    )
    echo.
) else (
    echo ✅ 已检测到语义模型 model.onnx
    echo.
)

echo ============================================================
echo 开始打包...
echo ============================================================
echo.

REM 清理旧的构建文件
echo [1/3] [%time%] 清理旧的构建产物...
if exist "%~dp0build" (
    echo    - 删除 build 目录...
    rmdir /s /q "%~dp0build"
)

if exist "%~dp0dist" (
    echo    - 删除 dist 目录...
    rmdir /s /q "%~dp0dist"
)
echo    清理完成
echo.

echo [2/3] [%time%] 执行 PyInstaller（耗时较长，请耐心等待）...
echo.

REM 使用 spec 文件进行打包
pyinstaller --clean "%~dp0build.spec"

if %errorlevel% equ 0 (
    echo.
    echo [3/3] [%time%] PyInstaller 完成，正在准备发布目录...
    set "MODEL_SRC=%~dp0models\bge-small-zh-v1.5-onnx"
    set "MODEL_DST=%~dp0dist\协议转换工具\models\bge-small-zh-v1.5-onnx"
    
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

    REM 确保识别结果目录存在于发布包（exe 每次识别文档都会在此重新生成结果）
    set "RECOG_DST=%~dp0dist\协议转换工具\table_recognition_results"
    if not exist "!RECOG_DST!" (
        mkdir "!RECOG_DST!"
        echo ✅ 已创建识别结果目录：!RECOG_DST!
    ) else (
        echo ✅ 识别结果目录已就绪：!RECOG_DST!
    )

    echo.
    echo ============================================================
    echo ✅ [%time%] 打包完成！
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
    echo    - 语义模型目录：models\bge-small-zh-v1.5-onnx
    echo.
    echo 📂 部署结构:
    echo    协议转换工具/
    echo    ├── 协议转换工具.exe
    echo    ├── table_recognition_results/   ← 每次识别文档自动生成的结果
    echo    │   ├── 1_classification_log.json
    echo    │   ├── 2_raw_tables.json
    echo    │   ├── 3_linked_tables.json
    echo    │   ├── 4_processed_tables.json
    echo    │   └── latest_recognition.json
    echo    └── models/
    echo        └── bge-small-zh-v1.5-onnx/
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
