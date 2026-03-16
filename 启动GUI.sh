#!/bin/bash

# SEO 内容生成器 - GUI 启动脚本

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 启动 GUI (隐藏终端输出)
python3 -m seo_gen.gui 2>/dev/null &
