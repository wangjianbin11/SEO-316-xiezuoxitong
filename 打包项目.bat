@echo off
chcp 65001 >nul
echo ============================================
echo SEO Content Generator - 项目打包工具
echo ============================================
echo.

REM 获取当前日期时间
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do (
    set datetime=%%a
    goto :found_time
)
:found_time

REM 创建打包目录
set PACK_DIR=seo-content-generator-package
if exist "%PACK_DIR%" rmdir /s /q "%PACK_DIR%"
mkdir "%PACK_DIR%"

echo [1/5] 创建打包目录...
echo.

REM 复制必需文件
echo [2/5] 复制项目文件...
xcopy /E /I /Y src "%PACK_DIR%\src\" >nul
xcopy /E /I /Y config "%PACK_DIR%\config\" >nul
copy /Y pyproject.toml "%PACK_DIR%\" >nul
copy /Y .env.example "%PACK_DIR%\" >nul
copy /Y 快速启动.bat "%PACK_DIR%\" >nul
copy /Y 快速启动.sh "%PACK_DIR%\" >nul
copy /Y 启动GUI.bat "%PACK_DIR%\" >nul
copy /Y 启动GUI.sh "%PACK_DIR%\" >nul
copy /Y 使用指南.md "%PACK_DIR%\" >nul
copy /Y GUI使用说明.md "%PACK_DIR%\" >nul
copy /Y DEPLOYMENT_GUIDE.md "%PACK_DIR%\" >nul
copy /Y 打包清单.md "%PACK_DIR%\" >nul
echo.

REM 询问是否包含 .env
echo [3/5] 检查敏感文件...
echo.
set /p include_env="是否包含 .env 文件（包含密钥）？(y/n) [默认: n]: "
if /i "%include_env%"=="y" (
    copy /Y .env "%PACK_DIR%\" >nul
    echo [注意] .env 文件已包含（请勿分享给他人！）
) else (
    echo .env 文件未包含（更安全）
)
echo.

REM 创建 README
echo [4/5] 创建说明文件...
echo SEO Content Generator - 项目打包 >> "%PACK_DIR%\读取我.md"
echo. >> "%PACK_DIR%\读取我.md"
echo 打包时间: %datetime% >> "%PACK_DIR%\读取我.md"
echo. >> "%PACK_DIR%\读取我.md"
echo 首次使用？请查看: 使用指南.md >> "%PACK_DIR%\读取我.md"
echo. >> "%PACK_DIR%\读取我.md"
echo 详细文档: DEPLOYMENT_GUIDE.md >> "%PACK_DIR%\读取我.md"
echo. >> "%PACK_DIR%\读取我.md"
echo 文件清单: 打包清单.md >> "%PACK_DIR%\读取我.md"
echo.

REM 压缩
echo [5/5] 压缩项目...
echo.
set ZIP_FILE=seo-content-generator-%datetime:~0,10%.zip

echo 正在压缩到: %ZIP_FILE%
echo.
powershell -Command "Compress-Archive -Path '%PACK_DIR%' -DestinationPath '%ZIP_FILE%' -Force"

echo.
echo ============================================
echo 打包完成！
echo ============================================
echo.
echo 打包文件: %ZIP_FILE%
echo.
echo 下一步:
echo   1. 将 %ZIP_FILE% 复制到 U 盘或云盘
echo   2. 在新电脑上解压
echo   3. 查看"使用指南.md"开始使用
echo.
echo ============================================

REM 询问是否打开目录
set /p open_dir="是否打开打包目录？(y/n) [默认: n]: "
if /i "%open_dir%"=="y" (
    explorer "%PACK_DIR%"
)

pause
