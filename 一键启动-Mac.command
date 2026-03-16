#!/bin/bash
# SEO 内容生成器 - Mac 一键启动脚本（支持 Apple Silicon）
# 自动检测并安装所有依赖

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 清屏
clear

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}    SEO 内容生成器 - 一键启动 (macOS)${NC}"
echo -e "${BLUE}    支持 Intel & Apple Silicon (M1/M2/M3)${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# 检测 Mac 架构
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    MACHINE_TYPE="Apple Silicon (M1/M2/M3)"
else
    MACHINE_TYPE="Intel Mac"
fi
echo -e "${CYAN}检测到机器类型: $MACHINE_TYPE${NC}"
echo ""

# ========== 步骤1：检测 Python ==========
echo -e "${YELLOW}[1/7] 检测 Python 环境...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "  ${RED}X${NC} 未找到 Python 3"
    echo ""
    echo "请先安装 Python 3.8 或更高版本："
    echo ""
    echo "方式1 - 使用 Homebrew（推荐，支持 M 芯片）:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    echo "方式2 - 从官网下载:"
    echo "  https://www.python.org/downloads/"
    echo "  选择 macOS 64-bit installers"
    echo ""
    read -p "按 Enter 键退出..."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "  ${GREEN}√${NC} Python 已安装: $PYTHON_VERSION"

# 检查 Python 版本
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "  ${RED}X${NC} Python 版本过低（需要 3.8+），当前版本: $PYTHON_VERSION"
    echo ""
    read -p "按 Enter 键退出..."
    exit 1
fi

# 检查 Python 架构是否匹配系统
PYTHON_ARCH=$(python3 -c 'import platform; print(platform.machine())')
echo -e "  → Python 架构: $PYTHON_ARCH"

if [ "$ARCH" = "arm64" ] && [ "$PYTHON_ARCH" != "arm64" ]; then
    echo -e "  ${YELLOW}⚠️${NC}  警告: Python 不是 arm64 版本，可能在 M 芯片上运行较慢"
fi

echo ""

# ========== 步骤2：检测 pip ==========
echo -e "${YELLOW}[2/7] 检测 pip...${NC}"

if ! python3 -m pip --version &> /dev/null; then
    echo "  → pip 未安装，正在安装..."
    curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py --user
    export PATH="$HOME/.local/bin:$PATH"
fi

# 升级 pip
echo "  → 升级 pip 到最新版本..."
python3 -m pip install --upgrade pip --quiet --disable-pip-version-check 2>/dev/null
echo -e "  ${GREEN}√${NC} pip 已准备就绪"
echo ""

# ========== 步骤3：检查/创建虚拟环境 ==========
echo -e "${YELLOW}[3/7] 检查虚拟环境...${NC}"

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "  → 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"

    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"

    # 升级 pip
    pip install --upgrade pip setuptools wheel --quiet --disable-pip-version-check

    # Apple Silicon 特殊处理：确保使用正确版本的依赖
    if [ "$ARCH" = "arm64" ]; then
        echo "  → Apple Silicon: 优化依赖配置..."
        # 设置环境变量优先使用 arm64 包
        echo "export PYTHONPATH=\"$PWD/src:$PYTHONPATH\"" >> "$VENV_DIR/bin/activate"
    fi

    echo -e "  ${GREEN}√${NC} 虚拟环境创建完成"
else
    echo "  → 虚拟环境已存在"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"
echo ""

# ========== 步骤4：安装 Python 依赖 ==========
echo -e "${YELLOW}[4/7] 安装 Python 依赖包...${NC}"
echo "  → 正在安装依赖，请稍候..."

# 设置编译环境变量（Apple Silicon 优化）
if [ "$ARCH" = "arm64" ]; then
    # 确保 ROSW 无法使用 x86_64 包
    export PYTHONPATH="$PWD/src:$PYTHONPATH"
fi

# 先安装基础依赖
echo "    → 安装基础依赖 (requests, beautifulsoup4)..."
pip install requests beautifulsoup4 --quiet --disable-pip-version-check

# 安装项目依赖
if ! pip install -e . --quiet --disable-pip-version-check; then
    echo -e "  ${RED}X${NC} 依赖安装失败，尝试详细模式..."
    echo ""
    pip install -e .
    if [ $? -ne 0 ]; then
        echo ""
        echo "依赖安装失败，可能的原因："
        echo "  1. 某些包不支持 Apple Silicon（arm64）"
        echo "  2. 需要安装 Xcode Command Line Tools"
        echo ""
        echo "解决方案:"
        echo "  xcode-select --install"
        echo ""
        read -p "按 Enter 键退出..."
        exit 1
    fi
fi

echo -e "  ${GREEN}√${NC} Python 依赖安装完成"
echo ""

# ========== 步骤5：检查 Playwright ==========
echo -e "${YELLOW}[5/7] 检查 Playwright...${NC}"

if ! python3 -c "import playwright" 2>/dev/null; then
    echo "  → Playwright 未安装，正在安装..."
    pip install playwright --quiet --disable-pip-version-check
    echo -e "  ${GREEN}√${NC} Playwright 安装完成"
else
    echo "  → Playwright 已安装"
fi
echo ""

# ========== 步骤6：安装 Chromium 浏览器 ==========
echo -e "${YELLOW}[6/7] 检查 Chromium 浏览器...${NC}"

# 测试 Chromium 是否可用
if ! python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" 2>/dev/null; then
    echo "  → Chromium 未安装，正在安装..."
    echo ""
    echo -e "${YELLOW}这将下载约 150-200MB 的文件，请耐心等待...${NC}"
    echo ""

    # Apple Silicon 优化：使用系统架构
    export PLAYWRIGHT_BROWSERS_PATH="$VENV_DIR/bin/msplaywright"

    # 安装 Chromium
    if ! playwright install chromium --with-deps; then
        echo -e "  ${RED}X${NC} Chromium 安装失败"
        echo ""
        echo "可能的解决方案："
        echo "  1. 检查网络连接"
        echo "  2. 尝试使用国内镜像:"
        echo "     export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/"
        echo "     playwright install chromium"
        echo ""
        echo "  3. Apple Silicon 特殊问题:"
        echo "     export PLAYWRIGHT_BROWSERS_PATH=0"
        echo "     playwright install chromium --force"
        echo ""
        read -p "按 Enter 键退出..."
        exit 1
    fi

    echo -e "  ${GREEN}√${NC} Chromium 安装完成"
else
    echo "  → Chromium 已安装"
fi
echo ""

# ========== 步骤7：启动 GUI ==========
echo -e "${YELLOW}[7/7] 启动图形界面...${NC}"
echo ""
echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}    正在启动 SEO 内容生成器...${NC}"
echo -e "${GREEN}===================================================${NC}"
echo ""

# 启动 GUI
python3 -m seo_gen.gui

# 如果异常退出，暂停查看错误
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}程序异常退出${NC}"
    echo ""
    read -p "按 Enter 键退出..."
fi
