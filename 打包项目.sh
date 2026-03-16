#!/bin/bash

echo "============================================"
echo "SEO Content Generator - 项目打包工具"
echo "============================================"
echo ""

# 获取当前日期
DATETIME=$(date +"%Y%m%d")
PACK_DIR="seo-content-generator-package-$DATETIME"

# 创建打包目录
echo "[1/5] 创建打包目录..."
rm -rf "$PACK_DIR"
mkdir -p "$PACK_DIR"
echo ""

# 复制必需文件
echo "[2/5] 复制项目文件..."
cp -r src "$PACK_DIR/"
cp -r config "$PACK_DIR/"
cp pyproject.toml "$PACK_DIR/"
cp .env.example "$PACK_DIR/"
cp 快速启动.bat "$PACK_DIR/"
cp 快速启动.sh "$PACK_DIR/"
cp 启动GUI.bat "$PACK_DIR/"
cp 启动GUI.sh "$PACK_DIR/"
cp 使用指南.md "$PACK_DIR/"
cp GUI使用说明.md "$PACK_DIR/"
cp DEPLOYMENT_GUIDE.md "$PACK_DIR/"
cp 打包清单.md "$PACK_DIR/"
echo ""

# 询问是否包含 .env
echo "[3/5] 检查敏感文件..."
echo ""
read -p "是否包含 .env 文件（包含密钥）？(y/n) [默认: n]: " include_env

if [[ "$include_env" == "y" || "$include_env" == "Y" ]]; then
    cp .env "$PACK_DIR/"
    echo "[注意] .env 文件已包含（请勿分享给他人！）"
else
    echo ".env 文件未包含（更安全）"
fi
echo ""

# 创建 README
echo "[4/5] 创建说明文件..."
cat > "$PACK_DIR/读取我.md" <<EOF
# SEO Content Generator - 项目打包

打包时间: $DATETIME

## 首次使用？
请查看: **使用指南.md**

## 详细文档
- 使用指南.md - 快速上手
- DEPLOYMENT_GUIDE.md - 完整部署指南
- 打包清单.md - 文件说明

## 重要提示
⚠️ 如果包含 .env 文件，请勿分享给他人！
EOF
echo ""

# 压缩
echo "[5/5] 压缩项目..."
echo ""
ZIP_FILE="seo-content-generator-$DATETIME.zip"

echo "正在压缩到: $ZIP_FILE"
echo ""
zip -qr "$ZIP_FILE" "$PACK_DIR"

echo ""
echo "============================================"
echo "打包完成！"
echo "============================================"
echo ""
echo "打包文件: $ZIP_FILE"
echo ""
echo "下一步:"
echo "  1. 将 $ZIP_FILE 复制到 U 盘或云盘"
echo "  2. 在新电脑上解压"
echo "  3. 查看'使用指南.md'开始使用"
echo ""
echo "============================================"

# 询问是否打开 Finder
read -p "是否在 Finder 中显示？(y/n) [默认: n]: " open_finder

if [[ "$open_finder" == "y" || "$open_finder" == "Y" ]]; then
    open -R "$ZIP_FILE"
fi

echo ""
