@echo off
REM SEO 内容生成器 - Windows 一键启动脚本
REM 自动检测并安装所有依赖

chcp 65001 >nul
setlocal enabledelayedexpansion

echo ====================================================
echo     SEO 内容生成器 - 一键启动 (Windows)
echo ====================================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM ========== 步骤1：检测 Python ==========
echo [1/6] 检测 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X 未找到 Python
    echo.
    echo   请先安装 Python 3.8 或更高版本：
    echo   1. 访问 https://python.org/downloads/
    echo   2. 下载并安装 Python（勾选 "Add Python to PATH"）
    echo   3. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

python --version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo   √ Python 已安装: !PYTHON_VERSION!
echo.

REM ========== 步骤2：升级 pip ==========
echo [2/6] 检查 pip 是否需要升级...
python -m pip install --upgrade pip >nul 2>&1
echo   √ pip 已准备就绪
echo.

REM ========== 步骤3：安装 Python 依赖 ==========
echo [3/6] 安装 Python 依赖包...
echo   正在安装依赖，请稍候...

python -m pip install -e . --quiet --disable-pip-version-check
if errorlevel 1 (
    echo   X 依赖安装失败，尝试使用 verbose 模式重新安装...
    echo.
    python -m pip install -e .
    if errorlevel 1 (
        echo.
        echo   依赖安装失败，请检查网络连接或手动运行：
        echo   pip install -e .
        echo.
        pause
        exit /b 1
    )
)

echo   √ Python 依赖安装完成
echo.

REM ========== 步骤4：检查 Playwright ==========
echo [4/6] 检查 Playwright 安装...

python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo   → Playwright 未安装，正在安装...
    python -m pip install playwright --quiet
    echo   √ Playwright 安装完成
) else (
    echo   → Playwright 已安装
)

REM ========== 步骤5：安装 Chromium 浏览器 ==========
echo [5/6] 检查 Chromium 浏览器...

python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" >nul 2>&1
if errorlevel 1 (
    echo   → Chromium 未安装，正在安装...
    echo   这将下载约 150-200MB 的文件，请耐心等待...
    echo.

    python -m playwright install chromium --devel
    if errorlevel 1 (
        echo   X Chromium 安装失败
        echo   可能是网络问题，请尝试：
        echo   1. 检查网络连接
        echo   2. 使用国内镜像: set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
        echo   3. 或手动运行: playwright install chromium
        echo.
        pause
        exit /b 1
    )
    echo   √ Chromium 安装完成
) else (
    echo   → Chromium 已安装
)
echo.

REM ========== 步骤6：启动 GUI ==========
echo [6/6] 启动图形界面...
echo.
echo   ====================================================
echo   正在启动 SEO 内容生成器...
echo   ====================================================
echo.

REM 启动 GUI
python -m seo_gen.gui

REM 如果异常退出，暂停查看错误
if errorlevel 1 (
    echo.
    echo   程序异常退出，错误代码: %errorlevel%
    echo.
    pause
)
