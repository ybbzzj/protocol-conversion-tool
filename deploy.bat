@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo 协议转换工具 - 一键部署脚本
echo Python 3.8 + Windows 7 专用版本
echo ============================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Python
    echo.
    echo 请先安装 Python 3.8.8:
    echo https://www.python.org/downloads/release/python-388/
    echo.
    echo 安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ 检测到 Python 环境
python --version
echo.

REM 检查 Python 版本是否为 3.8
python -c "import sys; sys.exit(0 if sys.version_info.major == 3 and sys.version_info.minor == 8 else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  警告：当前 Python 版本不是 3.8
    echo Windows 7 最高支持 Python 3.8
    echo.
    set /p CONTINUE="是否继续？(可能导致兼容性问题) (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo 取消部署
        pause
        exit /b 1
    )
    echo.
)

echo ============================================================
echo 步骤 1/5: 安装项目依赖
echo ============================================================
echo.

REM 先升级 pip（解决编码问题）
echo 正在升级 pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ⚠️  pip 升级失败，继续尝试安装依赖...
    echo.
)

echo.
echo 开始安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装完成
echo.

REM 修复 paddlenlp 中的 scipy 导入问题
echo ============================================================
echo 步骤 1.5/5: 修复 PaddleNLP scipy 导入问题
echo ============================================================
echo.
python patch_paddlenlp.py
python patch_paddlenlp_datasets.py
echo.

echo ============================================================
echo 步骤 2/5: 下载语义模型
echo ============================================================
echo.

python download_model.py
if %errorlevel% neq 0 (
    echo ⚠️  模型下载失败，但可以选择继续
    echo.
    set /p CONTINUE="是否继续后续步骤？(模型可以在之后单独下载) (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo 取消部署
        pause
        exit /b 1
    )
    echo.
)

echo.

echo ============================================================
echo 步骤 3/5: 构建前端
echo ============================================================
echo.

REM 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  未检测到 Node.js
    echo.
    echo 前端构建需要 Node.js v14+
    echo 下载地址：https://nodejs.org/en/download/releases/
    echo.
    set /p CONTINUE="是否跳过前端构建继续？(打包会缺少前端资源) (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo 取消部署
        pause
        exit /b 1
    )
    echo.
    goto BUILD_FRONT_END
)

echo ✅ 检测到 Node.js 环境
node --version
echo.

cd public
call npm install
if %errorlevel% neq 0 (
    echo ❌ 前端依赖安装失败
    cd ..
    pause
    exit /b 1
)

call npm run build
if %errorlevel% neq 0 (
    echo ❌ 前端构建失败
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ✅ 前端构建完成
echo.

:BUILD_FRONT_END

echo ============================================================
echo 步骤 4/5: 运行兼容性检查（可选）
echo ============================================================
echo.

set /p RUN_CHECK="是否运行 Python 3.8 兼容性检查？(推荐) (y/N): "
if /i "!RUN_CHECK!"=="y" (
    python check_python38_compat.py
    echo.
)

echo ============================================================
echo 步骤 5/5: 打包成 EXE
echo ============================================================
echo.

set /p BUILD_EXE="是否立即打包成 EXE? (y/N): "
if /i "!BUILD_EXE!"=="y" (
    call build_exe.bat
) else (
    echo.
    echo 💡 提示：可以稍后手动运行 build_exe.bat 进行打包
    echo.
)

echo.
echo ============================================================
echo 🎉 部署完成！
echo ============================================================
echo.
echo 下一步操作:
echo.
echo 方式 A: 使用 EXE（推荐）
echo   1. 运行 build_exe.bat 打包（如果刚才选择了否）
echo   2. 将 dist\协议转换工具 文件夹复制到目标机器
echo   3. 运行 协议转换工具.exe
echo.
echo 方式 B: 使用 Python 环境
echo   1. 确保所有依赖已安装
echo   2. 运行 python main.py
echo   3. 访问 http://localhost:5001
echo.
echo 方式 C: 离线部署到其他机器
echo   1. 运行 python download_offline_packages.py
echo   2. 将生成的 offline_packages 文件夹复制到目标机器
echo   3. 在目标机器运行 install_offline.bat
echo.
echo 详细文档:
echo   - QUICK_START.md - 快速参考
echo   - DEPLOYMENT_GUIDE.md - 详细指南
echo   - README_PYTHON38_WINDOWS7.md - 完整说明
echo.

pause
