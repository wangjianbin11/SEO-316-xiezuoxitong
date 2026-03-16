# Mac 快速启动指南

## 一键启动（推荐）

### 最简单的方式

1. 找到 `启动GUI-Mac.command` 文件
2. 双击该文件
3. 等待程序启动

### 首次运行提示

如果双击后提示"无法打开"，因为来自身份不明的开发者：

**方法 1：右键打开**
1. 右键点击 `启动GUI-Mac.command`
2. 选择"打开"
3. 点击"打开"确认

**方法 2：终端授权**
```bash
chmod +x 启动GUI-Mac.command
```

## 创建桌面快捷方式

### 创建桌面别名

```bash
# 在终端运行
ln -s ~/path/to/seo-content-generator/启动GUI-Mac.command ~/Desktop/SEO内容生成器
```

### 创建真正的应用程序

详见 [创建Mac应用.md](创建Mac应用.md)

## 环境要求

### 1. 检查 Python

打开终端，运行：
```bash
python3 --version
```

需要 Python 3.8 或更高版本。

### 2. 安装 Python（如未安装）

**使用 Homebrew（推荐）**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3
```

**或从官网下载**
访问 https://python.org/downloads/ 下载安装

### 3. 安装依赖

首次运行会自动安装依赖，或手动安装：
```bash
pip3 install -e .
```

## 配置 API 密钥

### 创建 .env 文件

1. 找到项目目录中的 `.env.example` 文件
2. 复制并重命名为 `.env`
3. 编辑 `.env` 文件，填入您的 API 密钥

### 必需配置

```bash
# OpenAI API 配置
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini

# WordPress 配置
WORDPRESS_SITE_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=your_app_password
```

### 可选配置

```bash
# Google SERP API
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

## 常见问题

### Q: 双击后终端闪退？
A: 打开"终端.app"，手动运行：
```bash
cd /path/to/seo-content-generator
./启动GUI-Mac.command
```
查看错误信息

### Q: 提示找不到模块？
A: 重新安装依赖：
```bash
pip3 install -e .
```

### Q: GUI 窗口不显示？
A: 安装图形界面依赖：
```bash
pip3 install customtkinter
```

### Q: 虚拟环境问题？
A: 创建虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Q: 如何在后台运行？
A: 使用 nohup：
```bash
nohup ./启动GUI-Mac.command > /dev/null 2>&1 &
```

## 高级配置

### 使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -e .

# 启动 GUI
python3 -m seo_gen.gui
```

### 配置自动启动

1. 打开"系统偏好设置" → "用户与群组"
2. 选择您的用户 → "登录项"
3. 点击"+"号，添加 `启动GUI-Mac.command`

### 设置图标（.command 文件）

1. 准备一个 .icns 格式的图标
2. 选中 `启动GUI-Mac.command`
3. 按 `Cmd + I` 打开简介
4. 将图标拖到文件图标上

## 卸载

```bash
# 删除虚拟环境
rm -rf venv

# 删除配置文件
rm .env

# 删除应用（如创建了 .app）
rm -rf /Applications/SEO\ 内容生成器.app
```

## 技术支持

遇到问题？
- 查看 [创建Mac应用.md](创建Mac应用.md) 了解更多创建应用的选项
- 查看 [README.md](README.md) 了解完整使用说明
- 提交 Issue 到项目仓库
