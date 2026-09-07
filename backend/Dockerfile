# syntax=docker/dockerfile:1

# ========================================================
# 阶段一：提取官方 uv 二进制工具
# ========================================================
FROM ghcr.io/astral-sh/uv:0.6.5 AS uv_bin

# ========================================================
# 阶段二：生产运行环境 (Debian Bookworm Slim)
# ========================================================
FROM python:3.12-slim-bookworm

# 注入 uv 二进制
COPY --from=uv_bin /uv /uvx /bin/

# 环境变量配置
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 优先拷贝依赖定义文件与说明文档以最大化利用 Docker 构建层缓存
COPY pyproject.toml uv.lock* README.md ./

# 极速预安装生产依赖 (无开发依赖，无裸项目构建)
RUN uv sync --frozen --no-dev --no-install-project

# 拷贝源代码
COPY src/ ./src/

# 执行项目最终安装
RUN uv sync --frozen --no-dev

# 安全加固：创建并切换至非 root 用户运行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 将虚拟环境加入 PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# 容器原生健康检查 (调用 /live 存活探针)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/live')" || exit 1

# 启动应用服务器
CMD ["python", "-m", "src.server"]
