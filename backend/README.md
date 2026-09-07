# Astra Backend

Astra 是基于 FastAPI + uv + LangGraph + LiteLLM + OCI MySQL HeatWave 构建的企业级类 DeepSeek AI 对话应用后端。

## 技术栈架构

- **核心框架**：FastAPI 0.110+、Uvicorn、Pydantic v2、Pydantic-Settings
- **包管理器与工具链**：Astral `uv`、Hatchling、Black、isort、Ruff、MyPy (Strict)
- **数据库与 ORM**：SQLAlchemy 2.0 (Async) + `asyncmy` 驱动，直连 OCI MySQL HeatWave (支持原生 `VECTOR(1536)`)
- **高速缓存与会话**：Redis (支持滑动窗口限流、可中断推理信号)
- **智能体编排**：LangGraph `StateGraph` (支持意图自动路由、动态提示词装配)
- **AI 统一推理网关**：LiteLLM Proxy 客户端 (支持 SSE 实时打字机流式输出)
- **认证与会话**：Logto SSO、Cloudflare Zero Trust 同域反代兼容、JWT 双令牌、多设备远程管理与行级数据隔离

## 快速上手

### 1. 安装环境与依赖

```bash
# 安装 Python 3.12 虚拟环境并同步全量开发依赖
uv sync --extra dev
```

### 2. 配置环境变量

```bash
cp .env-template .env
# 编辑 .env 文件配置数据库与网关密钥
```

### 3. 本地启动服务

```bash
uv run python -m src.server
```

服务运行于 `http://0.0.0.0:8000`。
健康检查探针：
- `GET /health`：Kubernetes 综合探针
- `GET /ready`：就绪探针
- `GET /live`：存活探针

### 4. 执行测试套件与代码质检

```bash
# 运行全部 226 个单元与集成测试并统计覆盖率
uv run pytest

# 静态类型检查 (Strict 模式)
uv run mypy src

# 代码规范与坏味道检查
uv run ruff check src test

# 代码格式化
uv run isort src test && uv run black src test
```

## GitOps & CI/CD 自动化流水线

- **Backend CI (`.github/workflows/ci.yaml`)**：自动运行 Black、isort、Ruff、MyPy Strict 静态代码分析与 226 个单元测试门禁；
- **Backend CD (`.github/workflows/build-and-push-image.yaml`)**：自动编译 `linux/amd64` + `linux/arm64` 双架构容器镜像并推送至 GHCR，计算唯一不可变 SHA256 Digest 并自动向 `my-argocd-manifests` 发起 GitOps 事件派发，触发 ArgoCD 生产部署。
