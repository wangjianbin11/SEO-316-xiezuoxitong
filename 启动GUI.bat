@echo off
REM SEO 内容生成器 - GUI 启动脚本 (隐藏控制台窗口)

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 使用 pythonw 启动，不显示控制台窗口
pythonw -m seo_gen.gui

REM 如果 pythonw 不可用，尝试使用 python
if errorlevel 1 (
    python -m seo_gen.gui
)
