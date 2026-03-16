# ============================================
# SEO Content Generator - Dockerfile
# ============================================

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml ./
COPY src/ ./src/

# 安装 Python 依赖
RUN pip install -e .

# 创建输出目录
RUN mkdir -p /app/outputs

# 暴露端口（如果需要 web 界面）
# EXPOSE 8000

# 默认命令
CMD ["seo-gen", "--help"]
