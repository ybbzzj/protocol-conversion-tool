@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo 协议转换工具 - 一键打包（前端构建 + PyInstaller 打包）
echo ============================================================
echo.

REM ── 步骤 1/2：构建前端 ────────────────────────────────────────
echo [步骤 1/2] [%time%] 开始构建前端...
echo.

REM 检查 npm（注意：npm 是 .cmd，bat 内必须用 call，否则执行完即退出）
call npm --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ 错误：未检测到 npm，请先安装 Node.js 后重试
    pause
    exit /b 1
)

pushd "%~dp0public"

REM 依赖未安装则先安装，保证“自动打包”可从干净环境跑通
if not exist "node_modules" (
    echo ⚠️  未检测到 node_modules，正在执行 npm install ...
    call npm install
    if !errorlevel! neq 0 (
        echo ❌ npm install 失败，已中止
        popd
        pause
        exit /b 1
    )
    echo.
)

echo 正在执行 npm run build ...
call npm run build
if !errorlevel! neq 0 (
    echo ❌ 前端构建失败，已中止打包（避免把过期的前端资源打进 exe）
    popd
    pause
    exit /b 1
)
popd

echo.
echo ✅ [%time%] 前端构建完成，产物位于 public\dist
echo.

REM ── 步骤 2/2：执行 PyInstaller 打包 ───────────────────────────
echo [步骤 2/2] [%time%] 调用 build_exe.bat 执行后端打包...
echo.

call "%~dp0build_exe.bat"

endlocal
