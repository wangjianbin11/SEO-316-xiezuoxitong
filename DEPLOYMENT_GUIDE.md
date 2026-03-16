# SEO Content Generator 部署指南

> 适合小白的完整安装和使用指南 | Windows & Mac 通用

---

## 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [配置 API 密钥](#配置-api-密钥)
4. [运行程序](#运行程序)
5. [常见问题](#常见问题)

---

## 系统要求

### Windows
- Windows 10 或更高版本
- 至少 4GB RAM
- 500MB 可用磁盘空间

### Mac
- macOS 11 (Big Sur) 或更高版本
- 至少 4GB RAM
- 500MB 可用磁盘空间

---

## 安装步骤

### 方案一：使用 Claude Code（推荐 - 最简单）

如果你当前电脑安装了 Claude Code，可以直接复制以下文件到新电脑：

**需要复制的文件和文件夹：**
```
seo-content-generator/
├── src/                 # 源代码
├── config/              # 配置文件
│   └── knowledge/       # 知识库文件（重要！）
├── pyproject.toml       # 依赖配置
├── .env                 # 环境配置（包含密钥）
└── outputs/             # 输出目录（可选）
```

**复制后，在新电脑上打开终端：**

```bash
# 进入项目目录
cd seo-content-generator

# 安装依赖
pip install -e .

# 运行程序
seo-gen generate-advanced "你的关键词"
```

---

### 方案二：手动安装（无需 Claude Code）

### Windows 安装

#### 步骤 1: 安装 Python

1. 访问 https://www.python.org/downloads/
2. 下载 **Python 3.11** 或 **3.12** Windows installer
3. 运行安装程序，**务必勾选 "Add Python to PATH"**
4. 安装完成后，重启电脑

#### 步骤 2: 验证 Python 安装

打开 **命令提示符** (Win+R 输入 `cmd` 回车):

```bash
python --version
```

应该显示类似 `Python 3.11.x` 或 `Python 3.12.x`

#### 步骤 3: 安装项目

1. 将项目文件夹复制到你的电脑（例如 `C:\Users\你的用户名\seo-content-generator`）
2. 在项目文件夹中，按住 **Shift + 右键**，选择"在此处打开命令窗口"或"在此处打开 PowerShell"
3. 运行以下命令：

```bash
# 安装依赖
pip install -e .

# 验证安装
seo-gen --help
```

---

### Mac 安装

#### 步骤 1: 安装 Homebrew（包管理器）

打开 **终端** (在 Launchpad 或 Spotlight 中搜索"终端")，运行：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 步骤 2: 安装 Python

```bash
brew install python@3.11
```

#### 步骤 3: 验证 Python 安装

```bash
python3 --version
```

#### 步骤 4: 安装项目

1. 将项目文件夹复制到你的用户目录
2. 打开终端，进入项目目录：

```bash
cd ~/seo-content-generator

# 安装依赖
pip3 install -e .

# 验证安装
seo-gen --help
```

---

## 配置 API 密钥

### 必需的 API 服务

#### 1. OpenRouter API（用于 AI 文章生成）

**注册地址**: https://openrouter.ai/

1. 注册账号并登录
2. 点击 "Keys" 创建新 API Key
3. 复制 API Key

**费用**: 按使用量计费，约 $0.01-0.05/篇文章

#### 2. Google Custom Search API（用于 SERP 分析）

**注册地址**: https://console.cloud.google.com/

1. 创建新项目
2. 启用 "Custom Search API"
3. 创建凭据 → API Key
4. 设置可编程搜索引擎 (https://programmablesearchengine.google.com/)
   - 创建搜索引擎
   - 获取 Search Engine ID

**免费额度**: 每天 100 次免费查询

#### 3. WordPress 凭证（用于自动发布）

在你的 WordPress 网站后台：

1. 进入 `用户` → `个人资料`
2. 滚动到"应用程序密码"
3. 创建新密码（命名如"SEO生成器"）
4. 复制生成的密码（格式如：abcd 1234 efgh 5678）

---

### 配置 .env 文件

1. 复制 `.env.template` 为 `.env`
2. 用文本编辑器打开 `.env`
3. 填写你的 API 密钥：

```env
# OpenRouter API
OPENAI_API_KEY=sk-or-v1-你的密钥

# Google Search API
GOOGLE_SEARCH_API_KEY=AIzaSy你的密钥
GOOGLE_SEARCH_ENGINE_ID=你的搜索引擎ID

# WordPress
WORDPRESS_SITE_URL=https://你的网站.com/
WORDPRESS_USERNAME=你的用户名
WORDPRESS_APP_PASSWORD=abcd 1234 efgh 5678
```

---

## 运行程序

### 基本命令

```bash
# 查看帮助
seo-gen --help

# 标准工作流（单阶段）
seo-gen generate "关键词" --slug url-slug

# 高级工作流（两阶段 - 推荐）
seo-gen generate-advanced "关键词"

# 只生成文章，不发布到 WordPress
seo-gen generate-advanced "关键词" --skip-wordpress

# 不生成图片
seo-gen generate-advanced "关键词" --skip-images
```

### 使用示例

```bash
# 生成关于 "dropshipping automation" 的文章
seo-gen generate-advanced "dropshipping automation"

# 生成关于 "shopify optimization" 的文章
seo-gen generate-advanced "shopify optimization tips"
```

---

### GUI 图形界面（推荐 - 更简单！）

#### 启动方式

**Windows:**
- 双击 `启动GUI.bat`

**Mac:**
```bash
chmod +x 启动GUI.sh
./启动GUI.sh
```

或在终端中运行：
```bash
python -m seo_gen.gui
```

#### GUI 功能

1. **单个生成** - 输入关键词，一键生成
2. **批量生成** - 多个关键词自动排队处理
3. **历史记录** - 查看所有生成记录和详细报告
4. **可视化进度** - 实时显示当前步骤
5. **质量报告** - 完整的 E-E-A-T 详细分析

#### GUI 界面预览

```
┌─────────────────────────────────────────┐
│     SEO 内容生成器 v1.0               │
├─────────────────────────────────────────┤
│                                         │
│  关键词: [输入框]                       │
│  □ 生成图片   □ 发布WordPress           │
│  [开始生成文章]                        │
│                                         │
│  进度: [████░░░░] 60%                 │
│                                         │
│  ● 正在分析 SERP...                    │
│  ● 正在生成标题...                     │
│  ● 正在撰写内容...                     │
│                                         │
│  📊 质量检测报告                        │
│  总体评分: 88/100                       │
│  E-E-A-T 详细分析...                    │
└─────────────────────────────────────────┘
```

#### GUI 使用技巧

- **单个生成**: 在"单个生成"标签输入关键词，点击"开始生成文章"
- **批量生成**: 在"批量生成"标签每行输入一个关键词，点击"批量生成文章"
- **查看历史**: 在"历史记录"标签双击任意记录查看详细报告
- **停止生成**: 直接关闭窗口即可停止

---

## 常见问题

### Q1: "不是内部或外部命令" 错误

**原因**: Python 未正确安装或未添加到 PATH

**解决**:
1. 重新安装 Python，确保勾选 "Add Python to PATH"
2. 重启电脑
3. 使用 `python -m seo_gen.main` 代替 `seo-gen`

### Q2: "No module named 'xxx'" 错误

**解决**: 重新安装依赖

```bash
# Windows
pip install -e .

# Mac
pip3 install -e .
```

### Q3: API 密钥无效

**解决**:
1. 检查 `.env` 文件中的密钥是否正确
2. 确保没有多余的空格或引号
3. 验证密钥是否在对应平台有效

### Q4: WordPress 发布失败（401 Unauthorized）

**解决**:
1. 检查 WordPress 应用密码是否正确
2. 确保用户名正确
3. 确保网站 URL 以 `/` 结尾

### Q5: 图片生成失败

**解决**:
1. 确保有足够的 OpenRouter 额度
2. 使用 `--skip-images` 跳过图片生成

### Q6: 不需要 Claude Code 吗？

**是的，不需要！**

这个项目是独立的 Python 程序，只需要：
- Python 环境
- .env 配置文件
- API 密钥

**Claude Code 只是一个方便的开发工具**，不是必需的。

### Q7: GUI 启动失败 - "No module named 'customtkinter'"

**解决**:
```bash
pip install customtkinter
```

### Q8: GUI 界面显示异常

**解决**:
- 确保使用 Python 3.11 或更高版本
- Windows: 重新安装 Python，勾选 "Add to PATH"
- 更新 CustomTkinter: `pip install --upgrade customtkinter`

### Q9: GUI 进度条不更新

**原因**: 生成过程在后台线程运行

**解决**: 等待生成完成，结果会自动显示

---

## 快速参考卡

### Windows 命令

| 操作 | 命令 |
|------|------|
| 安装项目 | `pip install -e .` |
| 启动 GUI | 双击 `启动GUI.bat` |
| 生成文章 | `seo-gen generate-advanced "关键词"` |
| 跳过图片 | `seo-gen generate-advanced "关键词" --skip-images` |
| 跳过 WordPress | `seo-gen generate-advanced "关键词" --skip-wordpress` |

### Mac 命令

| 操作 | 命令 |
|------|------|
| 安装项目 | `pip3 install -e .` |
| 启动 GUI | `python3 -m seo_gen.gui` |
| 生成文章 | `seo-gen generate-advanced "关键词"` |
| 跳过图片 | `seo-gen generate-advanced "关键词" --skip-images` |
| 跳过 WordPress | `seo-gen generate-advanced "关键词" --skip-wordpress` |

---

## 技术支持

如遇到问题：
1. 检查本文档的"常见问题"部分
2. 确认所有 API 密钥正确配置
3. 查看日志输出中的错误信息

**ASG Dropshipping**: https://asgdropshipping.com/
