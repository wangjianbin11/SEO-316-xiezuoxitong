#!/bin/bash
# SEO 内容生成器 - Mac 一键启动脚本
# 双击此文件即可启动

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 清屏
clear

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    SEO 内容生成器 - Mac 启动器${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查 Python 3.11
PYTHON_CMD=""
if command -v /opt/homebrew/bin/python3.11 &> /dev/null; then
    PYTHON_CMD="/opt/homebrew/bin/python3.11"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}错误: 未找到 Python 3${NC}"
    echo -e "${YELLOW}请先安装 Python 3.11:${NC}"
    echo "  1. 使用 Homebrew: brew install python@3.11"
    echo "  2. 或从 https://python.org 下载安装"
    echo ""
    read -p "按 Enter 键退出..."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python 版本: $PYTHON_VERSION (使用: $PYTHON_CMD)${NC}"

# 检查虚拟环境
VENV_DIR="$SCRIPT_DIR/venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✓ 检测到虚拟环境，正在激活...${NC}"
    source "$VENV_DIR/bin/activate"
else
    echo -e "${YELLOW}未检测到虚拟环境${NC}"
    echo -e "${YELLOW}提示: 推荐使用虚拟环境来隔离依赖${NC}"
    echo ""
fi

# 检查 .env 文件
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo -e "${YELLOW}未找到 .env 文件，正在从 .env.example 复制...${NC}"
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo -e "${YELLOW}请编辑 .env 文件填入您的 API 密钥${NC}"
        echo ""
        read -p "按 Enter 键继续，或 Ctrl+C 退出..."
    fi
fi

# 设置 PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# 检查依赖
echo -e "${BLUE}正在检查依赖...${NC}"
if ! $PYTHON_CMD -c "import customtkinter" 2>/dev/null; then
    echo -e "${YELLOW}未安装依赖，正在安装...${NC}"
    $PYTHON_CMD -m pip install -e "$SCRIPT_DIR" --quiet
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 依赖安装完成${NC}"
    else
        echo -e "${RED}依赖安装失败，请手动运行: $PYTHON_CMD -m pip install -e .${NC}"
        read -p "按 Enter 键退出..."
        exit 1
    fi
else
    echo -e "${GREEN}✓ 依赖已安装${NC}"
fi

echo ""
echo -e "${GREEN}正在启动 GUI...${NC}"
echo -e "${YELLOW}提示: 关闭此终端窗口将关闭应用程序${NC}"
echo ""
echo -e "${BLUE}================================================${NC}"
echo ""

# 启动 GUI
$PYTHON_CMD -m seo_gen.gui

# 如果程序异常退出，暂停以显示错误信息
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}程序异常退出${NC}"
    read -p "按 Enter 键退出..."
fi
