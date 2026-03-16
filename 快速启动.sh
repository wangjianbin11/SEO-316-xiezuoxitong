#!/bin/bash

echo "============================================"
echo "SEO Content Generator - 快速启动"
echo "============================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3"
    echo "请安装 Python 3.11 或更高版本"
    echo "Mac: brew install python@3.11"
    echo "或访问: https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] Python3 已安装: $(python3 --version)"
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "[提示] 未找到 .env 文件"
    echo "正在从 .env.example 创建 .env..."
    cp .env.example .env
    echo ""
    echo "[重要] 请编辑 .env 文件，填写你的 API 密钥"
    echo "所需 API:"
    echo "  1. OpenRouter: https://openrouter.ai/"
    echo "  2. Google Search: https://console.cloud.google.com/"
    echo "  3. WordPress: 在你的网站后台生成应用密码"
    echo ""

    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a TextEdit .env
    else
        nano .env
    fi

    echo ""
    echo "配置完成后，重新运行此脚本"
    exit 0
fi

echo "[OK] 配置文件已找到"
echo ""

# 检查依赖是否安装
if ! python3 -c "import seo_gen" 2>/dev/null; then
    echo "[提示] 依赖未安装，正在安装..."
    pip3 install -e .
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "[OK] 依赖已安装"
echo ""
echo "============================================"
echo "使用示例:"
echo "============================================"
echo ""
echo "标准生成:"
echo "  seo-gen generate \"关键词\" --slug url-slug"
echo ""
echo "高级工作流 (推荐):"
echo "  seo-gen generate-advanced \"关键词\""
echo ""
echo "只生成文章，不发布:"
echo "  seo-gen generate-advanced \"关键词\" --skip-wordpress"
echo ""
echo "不生成图片:"
echo "  seo-gen generate-advanced \"关键词\" --skip-images"
echo ""
echo "============================================"

# 询问是否启动生成
echo ""
read -p "请输入要生成文章的关键词 (直接回车跳过): " keyword

if [ -n "$keyword" ]; then
    echo ""
    echo "正在生成文章: $keyword"
    echo ""
    seo-gen generate-advanced "$keyword"
else
    echo ""
    echo "已跳过自动生成，你可以手动运行命令"
    echo "输入 'seo-gen --help' 查看帮助"
fi

echo ""
