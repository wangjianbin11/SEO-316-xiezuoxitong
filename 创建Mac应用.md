# Mac 应用程序创建指南

## 方法一：使用 .command 文件（推荐，最简单）

1. 双击 `启动GUI-Mac.command` 文件即可启动
2. 终端会打开并运行程序
3. 关闭终端窗口会关闭程序

## 方法二：创建 Mac 应用程序（.app）

### 步骤 1：打开 Automator

1. 按 `Cmd + Space`，输入 "Automator"，打开应用
2. 选择 "应用程序" 作为文档类型
3. 点击 "选取"

### 步骤 2：添加运行 Shell 脚本操作

1. 在左侧搜索栏中搜索 "Shell"
2. 将 "运行 Shell 脚本" 拖到右侧工作区
3. 将以下脚本粘贴到脚本框中：

```bash
#!/bin/bash

# 获取应用程序所在目录
APP_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
cd "$APP_DIR"

# 设置 Python 路径
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONPATH="$APP_DIR/src:$PYTHONPATH"

# 检查虚拟环境
if [ -d "$APP_DIR/venv" ]; then
    source "$APP_DIR/venv/bin/activate"
fi

# 启动 GUI
python3 -m seo_gen.gui

# 如果出错，显示错误信息
if [ $? -ne 0 ]; then
    osascript -e 'display dialog "程序启动失败，请检查 Python 环境和依赖是否正确安装。" buttons {"OK"} with icon stop'
fi
```

### 步骤 3：保存为应用程序

1. 按 `Cmd + S` 保存
2. 选择 "应用程序" 作为文件格式
3. 命名为 "SEO 内容生成器"
4. 保存到 "应用程序" 文件夹或桌面

### 步骤 4：设置图标（可选）

1. 准备一个 `.icns` 格式的图标文件
2. 右键点击创建的应用 → "显示简介"
3. 将图标文件拖到左上角的图标上

## 方法三：使用 Platypus（更简单）

### 安装 Platypus

1. 从 https://sveinbjorn.org/platypus 下载 Platypus
2. 安装并打开 Platypus

### 创建应用

1. **App Name**: SEO 内容生成器
2. **Script Type**: Shell
3. **Script**:
```bash
#!/bin/bash
cd "$APP_PATH"
export PYTHONPATH="$APP_PATH/src:$PYTHONPATH"
python3 -m seo_gen.gui
```
4. **Options**:
   - ✅ Is droppable（允许拖放）
   - ✚ Remain running after execution
   - ✚ Send output to logfile

5. 点击 "Create" 创建应用程序

## 环境要求

### Python 版本
- Python 3.8 或更高版本
- 检查：`python3 --version`

### 安装依赖
```bash
# 方式1：使用 pip
pip3 install -e .

# 方式2：使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 配置 API 密钥
确保项目根目录有 `.env` 文件，包含：
```
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

## 常见问题

### Q: 双击 .command 文件提示"无法打开"？
A: 这是安全限制，解决方法：
1. 右键点击文件 → "打开"
2. 或在终端运行：`chmod +x 启动GUI-Mac.command`

### Q: 提示找不到模块？
A: 重新安装依赖：
```bash
pip3 install -e .
```

### Q: GUI 窗口无法显示？
A: 确保安装了图形界面依赖：
```bash
pip3 install customtkinter
```

### Q: 程序启动后立即退出？
A: 检查日志：
```bash
python3 -m seo_gen.gui
```
查看具体错误信息
