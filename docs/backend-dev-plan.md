# Astra 后端开发计划文档

> **项目代号**：Astra  
> **文档版本**：v2.0 (Follow python-template-v2 Architecture)  
> **创建日期**：2026-09-06  
> **作者**：Cindy  
> **架构基线**：[python-template-v2](https://github.com/nvd11/python-template-v2)  
> **需求规范**：[requirements.md](../requirements.md)  
> **状态**：开发规划确认就绪

---

## 1. 架构基线与核心设计原则

本项目后端开发计划完全遵循主人 GitHub 上的 **`python-template-v2`** 现代化架构标准构建，彻底摒弃旧式目录组织，核心规范如下：

1. **项目布局（`src/` 模式）**：
   - 采用标准 `src/` 扁平模块分层，包含 `configs`、`models`、`routers`、`services`、`engine`、`agents`、`memory`、`middleware` 和 `utils`。
   - 禁止混入遗留项目非标准目录（如 `app/`、`core/`、`api/v1/`），全面统一至 `src/`。
2. **极速依赖与原生 `uv` 工程化体系**：
   - 依赖管理与项目运行完全统一采用 **Astral `uv`** 工具链（弃用所有传统 `pip`、`virtualenv` 与 `requirements.txt`）。
   - 项目基于 `uv init` / `pyproject.toml` 标准管理，采用 `uv.lock` 锁定跨平台可重现的二进制级确定性依赖。
   - 开发与运行全部通过 `uv run` 与 `uv sync` 进行托管：
     - 本地运行：`uv run python -m src.server`
     - 依赖同步：`uv sync --extra dev`
     - 单元测试：`uv run pytest`
     - 代码格式化与检查：`uv run ruff check .` / `uv run black .`
   - 构建后端采用 `hatchling`，分设生产依赖 `[project].dependencies` 与开发依赖 `[project.optional-dependencies].dev`。
   - 容器化镜像构建采用官方多阶段 `ghcr.io/astral-sh/uv:latest` 镜像直接拷贝二进制，零 `pip` 介入，秒级冷启动。
3. **分层配置管理（YAML + 环境变量）**：
   - 配置系统统一置于 `src/configs/`。
   - 基于 `pydantic-settings` 的 `BaseSettings`，指定环境变量前缀 `APP_`。
   - 双层加载机制：加载当前环境对应的 YAML 配置文件（`config_local.yaml` / `config_dev.yaml` / `config_prod.yaml`），再由系统环境变量进行强覆盖。
   - 提供 `@lru_cache` 装饰的 `get_settings()` 单例函数，配合 FastAPI 的 `Annotated[Settings, Depends(get_settings)]` 实现高效依赖注入。
4. **统一日志基础设施（Loguru）**：
   - 位于 `src/configs/log_config.py`，全面取代标准库 logging。
   - `local` / `dev` 环境：彩色控制台输出，高精度排障跟踪。
   - `prod` 环境：标准 JSON 结构化日志，原生适配 GCP Cloud Logging 字段（`severity`, `timestamp`, `logging.googleapis.com/sourceLocation` 等）。
5. **统一泛型响应协议（`BaseResponse[T]`）**：
   - 位于 `src/models/responses.py`，强制采用统一泛型结构：
     ```python
     class BaseResponse(BaseModel, Generic[T]):
         code: int = Field(default=0, description="业务状态码, 0 表示成功")
         message: str = Field(default="success", description="响应消息")
         data: T | None = Field(default=None, description="业务数据载荷")
         timestamp: datetime = Field(default_factory=datetime.utcnow)
     ```
6. **服务层（Service Pattern）与依赖注入**：
   - Router 负责入参校验、鉴权注入与 HTTP 响应包装，核心逻辑委托给 `src/services/`。
   - Service 类接收配置与存储引擎实例，返回业务 Dataclass 或 Pydantic 实体。
7. **生命周期与入口（`create_app` & `server.py`）**：
   - `src/main.py` 提供应用工厂 `create_app()`，采用 `@asynccontextmanager` 的 `lifespan(app: FastAPI)` 管理 MySQL 连接池与 Redis 连接的启停。
   - `src/server.py` 为统一启动入口，支持 `python -m src.server` 启动，兼容 Uvicorn 运行时。
8. **安全红线与多用户数据隔离**：
   - 任何涉及用户会话、消息、记忆、配置的数据库检索，必须强校验 `user_id`。
   - Redis 缓存使用 `user:{user_id}:*` 命名空间，防止跨用户数据污染。

---

## 2. 完整目录结构总览

```
backend/
├── pyproject.toml              # 统一项目配置 (uv / black / isort / mypy / pytest / ruff)
├── Dockerfile                  # 多阶段构建 Dockerfile (基于 uv, 非 root appuser 运行)
├── .dockerignore
├── .env-template               # 环境变量模板
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用工厂 (create_app, lifespan, 全局异常处理)
│   ├── server.py               # 服务启动主入口
│   │
│   ├── configs/                # 配置与日志基础设施
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings 加载器 (YAML + ENV 双层加载)
│   │   ├── config_local.yaml   # 本地开发配置 (单 worker, debug 模式, 本地 proxy 支持)
│   │   ├── config_dev.yaml     # 联调开发配置
│   │   ├── config_prod.yaml    # 生产部署配置 (4 workers, JSON 日志)
│   │   ├── log_config.py       # Loguru 结构化日志配置 (GCP Cloud Logging 兼容)
│   │   └── proxy.py            # 本地代理配置管理
│   │
│   ├── models/                 # Pydantic 数据契约 (DTO / 请求与响应)
│   │   ├── __init__.py
│   │   ├── requests.py         # 统一请求模型 (Auth, Chat, Conv, Message, User, Session)
│   │   └── responses.py        # 统一泛型响应模型 BaseResponse[T] 及各业务返回体
│   │
│   ├── routers/                # API 路由模块
│   │   ├── __init__.py         # api_router 统一聚合入口
│   │   ├── health.py           # K8s 探针 (/health, /ready, /live)
│   │   ├── auth.py             # 认证登录、Logto SSO 回调与 Token 刷新
│   │   ├── chat.py             # 核心流式对话 (/chat/completions SSE, /chat/stop)
│   │   ├── conversations.py    # 会话 CRUD、归档与历史查询
│   │   ├── messages.py         # 消息查看、编辑、重新生成与删除
│   │   ├── users.py            # 用户资料、偏好与用量统计
│   │   └── sessions.py         # 多设备 Session 追踪与远程下线/JWT 黑名单
│   │
│   ├── services/               # 领域业务服务层
│   │   ├── __init__.py
│   │   ├── auth_service.py     # 登录认证与 Logto OIDC 微信扫码对接
│   │   ├── chat_service.py     # 对话编排、SSE 打字机组装与 Agent 驱动
│   │   ├── conversation_service.py # 会话元数据与生命周期
│   │   ├── message_service.py  # 消息持久化与状态更新
│   │   ├── user_service.py     # 用户信息与用量配额计算
│   │   └── session_service.py  # 多端 Session 维护与 Redis 黑名单撤销
│   │
│   ├── engine/                 # 存储引擎与底层客户端
│   │   ├── __init__.py
│   │   ├── orm_models.py       # 数据库物理表 ORM 声明 (SQLAlchemy 2.0 Declarative)
│   │   ├── mysql_client.py     # MySQL 异步连接池与事务管理器 (asyncmy)
│   │   ├── redis_client.py     # Redis 异步客户端与连接池
│   │   ├── litellm_client.py   # 私有 LiteLLM 网关异步客户端 (OpenAI 协议兼容)
│   │   └── vector_store.py     # OCI MySQL HeatWave 原生 VECTOR 向量检索实现
│   │
│   ├── agents/                 # 多智能体集群 (LangGraph / LangChain)
│   │   ├── __init__.py
│   │   ├── base.py             # BaseAgent 抽象基类
│   │   ├── state.py            # AgentState 数据状态类
│   │   ├── router.py           # 意图识别与 Sub-Agent 动态路由器
│   │   ├── main_agent.py       # MainAgent 中央编排与聚合
│   │   ├── code_agent.py       # CodeAgent 代码助手
│   │   ├── search_agent.py     # SearchAgent 联网检索增强
│   │   ├── analysis_agent.py   # AnalysisAgent 数据统计分析
│   │   ├── creative_agent.py   # CreativeAgent 创意写作助手
│   │   └── general_agent.py    # GeneralAgent 通用问答兜底
│   │
│   ├── memory/                 # 短期/长期记忆系统
│   │   ├── __init__.py
│   │   ├── short_term.py       # Redis 会话上下文缓存 (滑动窗口)
│   │   ├── long_term.py        # MySQL HeatWave 向量检索长期记忆
│   │   └── manager.py          # 综合记忆拼装与注入管理器
│   │
│   ├── middleware/             # HTTP 中间件与请求处理
│   │   ├── __init__.py
│   │   ├── auth_middleware.py  # JWT 解析依赖与黑名单熔断拦截
│   │   ├── logging_middleware.py # 请求链路跟踪与耗时度量
│   │   └── cors_middleware.py  # 严格 CORS 跨域策略
│   │
│   └── utils/                  # 工具类与辅助函数
│       ├── __init__.py
│       ├── validators.py       # 关键词、参数范围与安全字符校验
│       ├── helpers.py          # UUID、时间戳与通用数据结构转换
│       └── formatters.py       # SSE 协议流式组帧与 Markdown 处理
│
└── test/                       # 自动化测试套件
    ├── __init__.py
    ├── conftest.py             # pytest 全局 fixtures (TestClient, Mock 存储)
    ├── test_routers/           # API 端点集成测试
    ├── test_services/          # 业务逻辑单元测试
    ├── test_agents/            # Agent 意图识别与流程测试
    └── test_engine/            # 数据库与缓存底层测试
```

---

## 3. 项目初始化与配置模块 (`backend/pyproject.toml`, Dockerfile, `src/configs/`)

### 3.1 `backend/pyproject.toml`
- **文件路径**：`backend/pyproject.toml`
- **功能描述**：项目统一配置清单，采用 `hatchling` 构建系统，统一收敛依赖、代码风格、类型检查与测试配置。
- **核心段落说明**：
  1. `[project]`：
     - `name = "astra-backend"`
     - `version = "1.0.0"`
     - `requires-python = ">=3.12"`
  2. `[project.dependencies]`（生产依赖）：
     - `fastapi>=0.110.0,<1.0.0`
     - `uvicorn[standard]>=0.29.0,<1.0.0`
     - `pydantic>=2.7.0,<3.0.0`
     - `pydantic-settings>=2.2.0,<3.0.0`
     - `loguru>=0.7.2,<1.0.0`
     - `python-dotenv>=1.0.1`
     - `PyYAML>=6.0.1`
     - `sqlalchemy[asyncio]>=2.0.30`
     - `asyncmy>=0.2.9`
     - `redis>=5.0.4`
     - `httpx>=0.27.0`
     - `python-jose[cryptography]>=3.3.0`
     - `passlib[bcrypt]>=1.7.4`
     - `langchain>=0.2.0`
     - `langgraph>=0.0.60`
     - `litellm>=1.35.0`
  3. `[project.optional-dependencies].dev`（开发测试依赖）：
     - `pytest>=8.1.0`
     - `pytest-asyncio>=0.23.0`
     - `pytest-cov>=5.0.0`
     - `black>=24.3.0`
     - `isort>=5.13.0`
     - `flake8>=6.1.0`
     - `mypy>=1.9.0`
     - `ruff>=0.3.4`
  4. 质量工具配置：
     - `[tool.black]`：`line-length = 88`, `target-version = ['py312']`
     - `[tool.isort]`：`profile = "black"`, `src_paths = ["src", "test"]`
     - `[tool.mypy]`：`python_version = "3.12"`, `strict = true`, `ignore_missing_imports = true`
     - `[tool.pytest.ini_options]`：`testpaths = ["test"]`, `addopts = ["-v", "--cov=src", "--cov-report=html"]`
     - `[tool.ruff]`：规则与 `python-template-v2` 对齐。

---

### 3.2 `backend/Dockerfile`
- **文件路径**：`backend/Dockerfile`
- **功能描述**：采用现代官方 `uv` 多阶段极速镜像构建，零 `pip` 介入，编译与运行环境严格解耦，以非 root 用户安全运行。
- **Dockerfile 规范设计**：
  ```dockerfile
  # 第一阶段：使用官方 uv 二进制提取
  FROM ghcr.io/astral-sh/uv:0.6.0 AS uv_bin

  # 第二阶段：生产运行镜像
  FROM python:3.12-slim-bookworm

  # 注入 uv 二进制工具
  COPY --from=uv_bin /uv /uvx /bin/

  # 环境变量设置
  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1 \
      UV_COMPILE_BYTECODE=1 \
      UV_LINK_MODE=copy

  WORKDIR /app

  # 先拷贝项目依赖清单，充分利用 Docker 层缓存
  COPY pyproject.toml uv.lock* ./

  # 使用 uv 极速冻结同步生产依赖 (无 pip、无多余依赖构建工具)
  RUN uv sync --frozen --no-dev --no-install-project

  # 拷贝源代码与必要配置
  COPY src/ ./src/

  # 执行最终项目安装
  RUN uv sync --frozen --no-dev

  # 安全加固：创建并切换非 root 用户 appuser
  RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
  USER appuser

  # 将 uv 创建的虚拟环境路径加入 PATH
  ENV PATH="/app/.venv/bin:$PATH"

  EXPOSE 8000

  # 健康探针
  HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
      CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

  # 启动指令 (通过 uv 托管执行)
  CMD ["uv", "run", "python", "-m", "src.server"]
  ```

---

### 3.3 `backend/.env-template`
- **文件路径**：`backend/.env-template`
- **功能描述**：后端环境变量配置模板。开发者首次克隆代码后，执行 `cp .env-template .env` 即可获得开箱即用的配置底稿。真实 `.env` 必须加入 `.gitignore`，严禁提交敏感凭据。
- **模板完整内容规范**：
  ```bash
  # ============================================================
  # Astra Backend 环境变量配置模板
  # 复制本文件为 .env：cp .env-template .env
  # ============================================================

  # ========== 基础服务环境 ==========
  APP_NAME=Astra
  APP_VERSION=1.0.0
  APP_ENVIRONMENT=local           # local | dev | prod
  APP_DEBUG=true                  # 生产环境强制 false
  APP_HOST=0.0.0.0
  APP_PORT=8000
  APP_WORKERS=1
  APP_LOG_LEVEL=DEBUG             # DEBUG | INFO | WARNING | ERROR

  # ========== 数据库连接 (OCI MySQL HeatWave) ==========
  # 本地开发可直连测试库或跳板机代理
  APP_DATABASE_URL=mysql+asyncmy://astra_user:<YOUR_DB_PASSWORD>@127.0.0.1:3306/astra

  # ========== 缓存服务 (Redis / OPPO 边缘节点) ==========
  # 本地开发可指向 localhost:6379 或通过内网 Tailscale 访问
  APP_REDIS_URL=redis://:<YOUR_REDIS_PASSWORD>@127.0.0.1:6379/0

  # ========== 私有 LiteLLM 网关 ==========
  APP_LITELLM_BASE_URL=https://litellm.jppwl.asia
  APP_LITELLM_API_KEY=sk-hsbc-litellm-secret-key
  APP_DEFAULT_MODEL=deepseek-v4-flash

  # ========== JWT 认证与会话安全 (开发自签回退；生产 OIDC 优先拉取 JWKS 公钥验签) ==========
  APP_JWT_SECRET=change-this-to-a-super-secret-random-key-in-production
  APP_JWT_ALGORITHM=HS256
  APP_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
  APP_JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

  # ========== 认证开关与多模式部署 (支持 Cloudflare 同域 Zero Trust) ==========
  # 是否启用认证: true=启用校验, false=完全跳过认证 (开发/单机/内部测试)
  APP_AUTH_ENABLED=true
  # 认证模式: logto | cloudflare | none
  # - logto: 使用 Logto SSO 微信扫码，基于 Logto JWKS 公钥端点验签，后端无需保存签名私钥
  # - cloudflare: 使用 Cloudflare Access 同域认证 (自动从 CF-Access-Jwt-Assertion 证书公钥验签)
  # - none: 无认证 (等同于 auth_enabled=false，直接注入 anonymous 用户)
  APP_AUTH_MODE=logto
  # Cloudflare Access 配置 (仅 auth_mode=cloudflare 时生效)
  APP_CLOUDFLARE_TEAM_NAME=your-team-name
  APP_CLOUDFLARE_AUDIENCE=your-audience-tag

  # ========== Logto SSO 统一认证 (微信扫码) ==========
  APP_LOGTO_ENDPOINT=https://auth.jppwl.asia
  APP_LOGTO_APP_ID=your-logto-app-id
  APP_LOGTO_APP_SECRET=your-logto-app-secret
  APP_LOGTO_REDIRECT_URI=https://gw.jppwl.asia/astra/callback

  # ========== 本地开发代理 (仅 local 环境可选) ==========
  # HTTP_PROXY=http://10.0.1.223:7890
  # HTTPS_PROXY=http://10.0.1.223:7890
  ```

---

### 3.4 `src/configs/config.py`
- **文件路径**：`src/configs/config.py`
- **功能描述**：应用核心配置单例加载器，实现 YAML 配置文件加载 + 环境变量高优先级覆盖，导出全局单例 `get_settings()`。
- **核心类与函数列表**：

| 类/函数 | 签名 | 说明 |
|---|---|---|
| `Settings` | `class Settings(BaseSettings)` | 配置数据模型，继承 `BaseSettings`，定义 `env_prefix = "APP_"` |
| `Settings.from_yaml` | `@classmethod def from_yaml(cls, yaml_config: dict[str, Any]) -> Settings` | 从已加载的 YAML 字典构造 Settings 实例 |
| `Settings.validate_log_level` | `@field_validator("log_level") @classmethod def validate_log_level(cls, v: str) -> str` | 校验日志级别合法性（`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`） |
| `_setup_project_path` | `def _setup_project_path() -> Path` | 获取工程根目录并动态添加至 `sys.path` |
| `_load_yaml_config` | `def _load_yaml_config(env: str) -> dict[str, Any]` | 按环境（`local`/`dev`/`prod`）读取 `config_{env}.yaml` |
| `get_settings` | `@lru_cache def get_settings() -> Settings` | 全局单例获取器，提供缓存 |

- **Settings 字段详单**：
  - **基础信息**：`app_name: str = "Astra"`, `app_version: str = "1.0.0"`, `app_environment: str = "dev"`, `debug: bool = False`
  - **网络监听**：`host: str = "0.0.0.0"`, `port: int = 8000`, `workers: int = 1`, `root_path: str = ""`
  - **数据库连接**：`database_url: str`（OCI MySQL HeatWave 异步连接串，形如 `mysql+asyncmy://user:pass@host:3306/astra`）
  - **缓存连接**：`redis_url: str`（OPPO 边缘节点 Redis，形如 `redis://:<YOUR_REDIS_PASSWORD>@10.0.1.17:6379/0`）
  - **LLM 私有网关**：`litellm_base_url: str`, `litellm_api_key: str`, `default_model: str = "deepseek-v4-flash"`
  - **认证系统（可插拔多模式 / JWT / Logto / Cloudflare Access）**：
    - `auth_enabled: bool = True`（全局认证开关：若为 `False` 则完全跳过 JWT/Logto 校验并自动注入只读 Mock 匿名用户，专用于本地单元测试、离线开发或单租户内网部署）
    - `auth_mode: str = "logto"`（认证运行模式：`logto` | `cloudflare` | `none`）
    - `cloudflare_team_name: str = ""`（Cloudflare Access 团队名称）
    - `cloudflare_audience: str = ""`（Cloudflare Access Application AUD 标签）
    - `jwt_secret: str`, `jwt_algorithm: str = "HS256"`
    - `jwt_access_token_expire_minutes: int = 120`
    - `jwt_refresh_token_expire_days: int = 7`
    - `logto_endpoint: str = "https://auth.jppwl.asia"`
    - `logto_app_id: str`, `logto_app_secret: str`, `logto_redirect_uri: str = "https://gw.jppwl.asia/astra/callback"`
  - **日志级别**：`log_level: str = "INFO"`

---

### 3.5 `src/configs/config_local.yaml`, `config_dev.yaml`, `config_prod.yaml`
- **文件路径**：`src/configs/config_{env}.yaml`
- **功能描述**：多环境预设参数文件。
- **配置内容设计**：
  - `config_local.yaml`：`server.workers: 1`, `server.debug: true`, `logging.level: "DEBUG"`, 预留 `proxy` 节点（`http: "http://10.0.1.223:7890"`）。
  - `config_dev.yaml`：`server.workers: 1`, `server.debug: true`, `server.root_path: ""`, `logging.level: "DEBUG"`。
  - `config_prod.yaml`：`server.workers: 4`, `server.debug: false`, `logging.level: "INFO"`。

---

### 3.6 `src/configs/log_config.py`
- **文件路径**：`src/configs/log_config.py`
- **功能描述**：Loguru 结构化日志配置模块，确保生产环境输出标准的 GCP Cloud Logging JSON 格式。
- **核心类与函数列表**：

| 类/函数 | 签名 | 说明 |
|---|---|---|
| `setup_logging` | `def setup_logging(app_env: str = "local") -> None` | 初始化 Loguru 日志输出格式与输出管道 |
| `gcp_formatter` | `def gcp_formatter(record: Record) -> str` | 将日志记录转换为包含 `severity`, `message`, `timestamp`, `sourceLocation` 的 JSON 字符串 |
| `get_logger` | `def get_logger(name: str)` | 获取绑定指定命名空间的 Logger 实例 |

---

### 3.7 `src/configs/proxy.py`
- **文件路径**：`src/configs/proxy.py`
- **功能描述**：本地环境代理切换工具函数。
- **核心函数**：
  - `def apply_proxy(http_proxy: str | None = None, https_proxy: str | None = None) -> None`：写入环境变量 `HTTP_PROXY` 与 `HTTPS_PROXY`。
  - `def clear_proxy() -> None`：清理环境变量中的代理设置。

---

## 4. 数据传输模型层 (`src/models/`)

采用 Pydantic v2 模型，统一使用泛型 `BaseResponse[T]` 包装返回结果。

### 4.1 `src/models/responses.py`
- **文件路径**：`src/models/responses.py`
- **功能描述**：系统级统一响应格式与各类业务数据出参。
- **核心模型列表**：

| 模型名称 | 核心字段 | 说明 |
|---|---|---|
| `BaseResponse[T]` | `code: int = 0`, `message: str = "success"`, `data: T \| None = None`, `timestamp: datetime` | 系统级统一通用响应外壳 |
| `PaginatedData[T]` | `items: list[T]`, `total: int`, `page: int`, `page_size: int`, `has_more: bool` | 通用分页数据包装器 |
| `HealthResponseData` | `status: str`, `service: str`, `version: str`, `mysql_ok: bool`, `redis_ok: bool`, `uptime_seconds: float \| None` | 探针健康状态明细 |
| `TokenResponseData` | `access_token: str`, `refresh_token: str`, `token_type: str = "Bearer"`, `expires_in: int`, `user: UserInfoData` | 登录成功后签发的令牌与用户数据 |
| `UserInfoData` | `id: str`, `username: str`, `email: str \| None`, `avatar_url: str \| None`, `preferences: dict[str, Any]`, `default_model: str`, `default_agent: str`, `created_at: datetime` | 用户核心资料实体 |
| `ConversationData` | `id: str`, `title: str`, `model: str`, `agent_preference: str`, `system_prompt: str \| None`, `is_archived: bool`, `created_at: datetime`, `updated_at: datetime`, `message_count: int \| None` | 单个会话元数据 |
| `MessageData` | `id: str`, `conversation_id: str`, `role: str`, `content: str`, `metadata: dict[str, Any] \| None`, `tokens_used: int \| None`, `created_at: datetime` | 消息明细实体 |
| `UserSessionItem` | `id: str`, `device_info: str`, `ip_address: str`, `last_active_at: datetime`, `expires_at: datetime`, `is_current: bool` | 活跃设备会话条目 |
| `UsageStatsData` | `total_messages: int`, `total_tokens: int`, `total_conversations: int`, `today_messages: int`, `today_tokens: int` | 用户用量统计 |
| `ChatStreamChunkData` | `id: str`, `delta: str`, `finish_reason: str \| None`, `model: str`, `agent: str` | SSE 流式输出单帧数据载荷 |

---

### 4.2 `src/models/requests.py`
- **文件路径**：`src/models/requests.py`
- **功能描述**：统一客户端请求入参校验模型。
- **核心模型列表**：

| 模型名称 | 核心字段 | 说明与校验规则 |
|---|---|---|
| `LoginRequest` | `username: str`, `password: str` | 基础账密登录 |
| `RefreshTokenRequest` | `refresh_token: str` | 刷新 Access Token |
| `LogtoCallbackRequest` | `code: str`, `state: str` | Logto SSO 微信登录授权码兑换 |
| `CreateConversationRequest` | `title: str \| None = "新对话"`, `model: str \| None = None`, `agent_preference: str = "auto"`, `system_prompt: str \| None = None` | 创建会话，标题超 255 字符自动截断 |
| `UpdateConversationRequest` | `title: str \| None = None`, `model: str \| None = None`, `agent_preference: str \| None = None`, `system_prompt: str \| None = None`, `is_archived: bool \| None = None` | 修改会话配置 |
| `SendMessageRequest` | `conversation_id: str`, `content: str`, `agent_override: str \| None = None`, `model_override: str \| None = None`, `stream: bool = True` | 发送对话消息，正文限制 1~10000 字符 |
| `EditMessageRequest` | `content: str` | 编辑已有消息正文 |
| `UpdateProfileRequest` | `avatar_url: str \| None = None`, `preferences: dict[str, Any] \| None = None` | 修改个人资料 |
| `UpdatePreferenceRequest` | `default_model: str \| None = None`, `default_agent: str \| None = None` | 修改默认模型与默认 Agent |
| `StopChatRequest` | `conversation_id: str` | 手动中断正在进行的流式推理 |

---

## 5. 存储引擎与外部协议层 (`src/engine/`)

### 5.1 `src/engine/orm_models.py`
- **文件路径**：`src/engine/orm_models.py`
- **功能描述**：严格映射 `requirements.md` 第 4.1 节建表语句的 SQLAlchemy 2.0 声明式 ORM 模型。
- **核心类列表**：

| ORM 类名 | 物理表名 | 核心字段及类型映射 |
|---|---|---|
| `User` | `users` | `id (VARCHAR(36), PK)`, `username (VARCHAR(64), Unique)`, `email (VARCHAR(255))`, `avatar_url (VARCHAR(500))`, `preferences (JSON)`, `default_model (VARCHAR(64))`, `default_agent (VARCHAR(64))`, `logto_id (VARCHAR(64), Unique)`, `created_at`, `updated_at` |
| `UserSession` | `user_sessions` | `id (VARCHAR(36), PK)`, `user_id (VARCHAR(36), FK, Index)`, `refresh_token (TEXT)`, `device_info (VARCHAR(255))`, `ip_address (VARCHAR(45))`, `last_active_at`, `expires_at`, `created_at` |
| `Conversation` | `conversations` | `id (VARCHAR(36), PK)`, `user_id (VARCHAR(36), FK, Index)`, `session_id (VARCHAR(36), FK, Index, Nullable)`, `title (VARCHAR(255))`, `model (VARCHAR(64))`, `agent_preference (VARCHAR(64))`, `system_prompt (TEXT)`, `is_archived (BOOLEAN)`, `created_at`, `updated_at` |
| `Message` | `messages` | `id (VARCHAR(36), PK)`, `conversation_id (VARCHAR(36), FK, Index)`, `user_id (VARCHAR(36), FK, Index)`, `session_id (VARCHAR(36), FK, Index, Nullable)`, `role (VARCHAR(20))`, `content (TEXT)`, `metadata (JSON)`, `tokens_used (INT)`, `is_deleted (BOOLEAN)`, `created_at`, `updated_at` |
| `KnowledgeDocument` | `knowledge_documents` | `id (VARCHAR(36), PK)`, `user_id (VARCHAR(36), FK, Index)`, `title (VARCHAR(255))`, `file_type (VARCHAR(32))`, `chunk_count (INT)`, `created_at` |
| `DocumentChunk` | `document_chunks` | `id (VARCHAR(36), PK)`, `document_id (VARCHAR(36), FK, Index)`, `user_id (VARCHAR(36), FK, Index)`, `chunk_index (INT)`, `content (TEXT)`, `embedding (JSON / VECTOR(1536))`, `metadata (JSON)`, `created_at` |

---

### 5.2 `src/engine/mysql_client.py`
- **文件路径**：`src/engine/mysql_client.py`
- **功能描述**：基于 `SQLAlchemy 2.0` + `asyncmy` 的 MySQL HeatWave 异步连接池与事务管理器。
- **核心类与函数列表**：

| 类/函数 | 签名 | 说明 |
|---|---|---|
| `MySQLClient` | `class MySQLClient` | 数据库引擎包装器 |
| `MySQLClient.__init__` | `def __init__(self, database_url: str) -> None` | 创建 `AsyncEngine`，配置连接池参数：`pool_size=20`, `max_overflow=10`, `pool_recycle=3600`, `pool_pre_ping=True` |
| `MySQLClient.check_connection` | `async def check_connection(self) -> bool` | 执行 `SELECT 1` 验证数据库活性 |
| `MySQLClient.session_scope` | `@asynccontextmanager async def session_scope(self) -> AsyncIterator[AsyncSession]` | 事务上下文，自动 commit，遇异常回滚 |
| `MySQLClient.close` | `async def close(self) -> None` | 优雅断开连接池 |
| `get_db_session` | `async def get_db_session() -> AsyncIterator[AsyncSession]` | FastAPI 依赖注入，提供单个请求专用的 `AsyncSession` |

---

### 5.3 `src/engine/redis_client.py`
- **文件路径**：`src/engine/redis_client.py`
- **功能描述**：异步 Redis 客户端，维护连接池，操作会话上下文、偏好设置缓存与黑名单。
- **核心类与函数列表**：

| 类/函数 | 签名 | 说明 |
|---|---|---|
| `RedisClient` | `class RedisClient` | Redis 异步包装类 |
| `RedisClient.__init__` | `def __init__(self, redis_url: str) -> None` | 基于 `redis.asyncio.from_url` 建立连接池 |
| `RedisClient.get` | `async def get(self, key: str) -> str | None` | 读取字符串缓存 |
| `RedisClient.setex` | `async def setex(self, key: str, seconds: int, value: str) -> bool` | 写入带 TTL 的字符串缓存 |
| `RedisClient.delete` | `async def delete(self, *keys: str) -> int` | 删除单个或多个 Key |
| `RedisClient.exists` | `async def exists(self, key: str) -> bool` | 检查 Key 是否存在（用于黑名单判断） |
| `RedisClient.rpush` | `async def rpush(self, key: str, *values: str) -> int` | 写入列表末尾（存储会话消息） |
| `RedisClient.lrange` | `async def lrange(self, key: str, start: int, end: int) -> list[str]` | 读取列表区间 |
| `RedisClient.ping` | `async def ping(self) -> bool` | 探针探活 |
| `RedisClient.close` | `async def close(self) -> None` | 断开连接 |
| `get_redis_client` | `def get_redis_client() -> RedisClient` | FastAPI 依赖注入单例工厂 |

---

### 5.4 `src/engine/litellm_client.py`
- **文件路径**：`src/engine/litellm_client.py`
- **功能描述**：异步对接主人私有 LiteLLM 网关（兼容 OpenAI 协议），提供流式生成与向量计算。
- **核心类与函数列表**：

| 类/函数 | 签名 | 说明 |
|---|---|---|
| `LiteLLMClient` | `class LiteLLMClient` | 网关交互类 |
| `LiteLLMClient.__init__` | `def __init__(self, base_url: str, api_key: str, default_model: str) -> None` | 初始化 HTTPX 异步客户端 |
| `LiteLLMClient.acompletion` | `async def acompletion(self, model: str, messages: list[dict[str, Any]], temperature: float = 0.7, max_tokens: int | None = None) -> dict[str, Any]` | 非流式文本推理 |
| `LiteLLMClient.astream_completion` | `async def astream_completion(self, model: str, messages: list[dict[str, Any]], temperature: float = 0.7) -> AsyncIterator[str]` | 异步逐字输出 Delta 字符流 |
| `LiteLLMClient.aembedding` | `async def aembedding(self, text: str, model: str = "text-embedding-3-small") -> list[float]` | 生成 1536 维浮点向量 |

---

### 5.5 `src/engine/vector_store.py`
- **文件路径**：`src/engine/vector_store.py`
- **功能描述**：利用 OCI MySQL HeatWave 26.7 原生 `VECTOR` 类型与内置相似度算法进行长期记忆的语义检索与写入。
- **核心类与函数列表**：

| 类/函数 | 签名 | 说明 |
|---|---|---|
| `HeatWaveVectorStore` | `class HeatWaveVectorStore` | 原生向量存取管理器 |
| `HeatWaveVectorStore.add_memory` | `async def add_memory(self, session: AsyncSession, user_id: str, content: str, memory_type: str, importance: float = 0.5, source_conv_id: str | None = None) -> str` | 调用嵌入模型生成向量，通过原生 SQL 写入 `long_term_memories` |
| `HeatWaveVectorStore.search_memories` | `async def search_memories(self, session: AsyncSession, user_id: str, query: str, top_k: int = 3, threshold: float = 0.65) -> list[dict[str, Any]]` | 生成查询向量，执行带有 `WHERE user_id = :uid` 强隔离的 `DISTANCE(embedding, :vec, 'COSINE')` 查询 |

---

## 6. 业务服务层设计 (`src/services/`)

Service 层承载纯粹的领域逻辑，屏蔽底层 ORM 细节，与 Router 保持松耦合。

### 6.1 `src/services/auth_service.py`
- **文件路径**：`src/services/auth_service.py`
- **功能描述**：负责常规密码登录校验、Logto OIDC 微信扫码凭据兑换、JWT 令牌签发及用户信息同步。
- **核心函数列表**：

| 函数名 | 签名 | 逻辑说明 |
|---|---|---|
| `login` | `async def login(self, req: LoginRequest) -> TokenResponseData` | 查询 `users` 表验证哈希密码；签发 Access Token 与 Refresh Token，并在 `user_sessions` 创建活跃记录 |
| `handle_logto_callback` | `async def handle_logto_callback(self, code: str, state: str) -> TokenResponseData` | 携带 code 请求 Logto SSO 获取 ID Token 与 Access Token；提取 openid，若用户不存在则自动同步创建本地记录并签发 JWT |
| `refresh_token` | `async def refresh_token(self, refresh_token: str) -> TokenResponseData` | 解析 Refresh Token；校验其有效性及是否被黑名单拦截；重新签发新 Access Token |
| `get_current_user_profile` | `async def get_current_user_profile(self, user_id: str) -> UserInfoData` | 获取当前登录用户画像实体 |

---

### 6.2 `src/services/chat_service.py`
- **文件路径**：`src/services/chat_service.py`
- **功能描述**：核心对话编排服务，整合短期记忆、长期向量记忆、Sub-Agent 路由与 LiteLLM 流式输出。
- **核心函数列表**：

| 函数名 | 签名 | 逻辑说明 |
|---|---|---|
| `stream_chat` | `async def stream_chat(self, user_id: str, req: SendMessageRequest) -> AsyncIterator[str]` | 1. 验证会话归属；<br>2. 保存用户消息至数据库；<br>3. 提取短期与长期记忆装配上下文；<br>4. 经由 `AgentRouter` 调度 Sub-Agent 生成回复；<br>5. 产出 SSE 格式数据流（`data: {...}

`）；<br>6. 推理结束将 Assistant 消息异步持久化至数据库，并刷新 Redis 缓存 |
| `stop_chat` | `async def stop_chat(self, user_id: str, req: StopChatRequest) -> None` | 在 Redis 写入会话停止标识（Key: `chat:stop:{conv_id}`，TTL 60s），流生成器检测到后主动熔断退出 |

---

### 6.3 `src/services/conversation_service.py`
- **文件路径**：`src/services/conversation_service.py`
- **功能描述**：会话生命周期管理，严格确保行级 `user_id` 物理隔离。
- **核心函数列表**：

| 函数名 | 签名 | 逻辑说明 |
|---|---|---|
| `list_conversations` | `async def list_conversations(self, user_id: str, page: int, page_size: int, search: str | None, is_archived: bool) -> PaginatedData[ConversationData]` | 强制附加 `WHERE user_id = :uid`，支持标题模糊搜索与按更新时间倒序 |
| `create_conversation` | `async def create_conversation(self, user_id: str, req: CreateConversationRequest) -> ConversationData` | 初始化新会话，落库并返回元数据 |
| `get_conversation` | `async def get_conversation(self, user_id: str, conv_id: str) -> ConversationData` | 获取单个会话详情，跨用户访问抛出 404/403 |
| `update_conversation` | `async def update_conversation(self, user_id: str, conv_id: str, req: UpdateConversationRequest) -> ConversationData` | 更新会话标题、模型或归档标志 |
| `delete_conversation` | `async def delete_conversation(self, user_id: str, conv_id: str) -> None` | 级联物理/逻辑删除会话、消息及相关 Redis 上下文 |
| `archive_conversation` | `async def archive_conversation(self, user_id: str, conv_id: str, archived: bool) -> ConversationData` | 快捷归档/取消归档会话 |

---

### 6.4 `src/services/message_service.py`
- **文件路径**：`src/services/message_service.py`
- **功能描述**：历史消息存取、撤销、编辑与重新生成。
- **核心函数列表**：

| 函数名 | 签名 | 逻辑说明 |
|---|---|---|
| `list_messages` | `async def list_messages(self, user_id: str, conv_id: str, page: int, page_size: int, before: datetime | None) -> PaginatedData[MessageData]` | 获取会话历史记录（带游标/分页支持） |
| `delete_message` | `async def delete_message(self, user_id: str, message_id: str) -> None` | 仅允许删除属于自己的消息，并同步清理 Redis 短期上下文 |
| `edit_message` | `async def edit_message(self, user_id: str, message_id: str, req: EditMessageRequest) -> MessageData` | 修改消息内容 |
| `regenerate_message` | `async def regenerate_message(self, user_id: str, message_id: str) -> AsyncIterator[str]` | 回溯至指定助手消息的上文，重新触发大模型推理并以 SSE 流式回传 |

---

### 6.5 `src/services/session_service.py`
- **文件路径**：`src/services/session_service.py`
- **功能描述**：多端登录管理，维护 Redis 黑名单以实现远程注销。
- **核心函数列表**：

| 函数名 | 签名 | 逻辑说明 |
|---|---|---|
| `list_active_sessions` | `async def list_active_sessions(self, user_id: str, current_jti: str) -> list[UserSessionItem]` | 查询数据库活跃 Session，对比 `current_jti` 标注当前使用设备 |
| `revoke_session` | `async def revoke_session(self, user_id: str, session_id: str) -> None` | 获取目标 Session 的 `jti`，写入 Redis `jwt:blacklist:{jti}`，TTL 设为剩余生存时间；并在数据库删除该条会话 |
| `is_jti_blacklisted` | `async def is_jti_blacklisted(self, jti: str) -> bool` | 快速校验指定 Token 是否已被吊销 |

---

### 6.6 `src/services/user_service.py`
- **文件路径**：`src/services/user_service.py`
- **功能描述**：个人设置、偏好持久化及用量汇总。
- **核心函数列表**：

| 函数名 | 签名 | 逻辑说明 |
|---|---|---|
| `update_profile` | `async def update_profile(self, user_id: str, req: UpdateProfileRequest) -> UserInfoData` | 更新头像与个性化偏好 JSON |
| `update_preferences` | `async def update_preferences(self, user_id: str, req: UpdatePreferenceRequest) -> UserInfoData` | 更新用户全局默认模型与默认 Agent |
| `get_user_usage` | `async def get_user_usage(self, user_id: str) -> UsageStatsData` | 聚合计算用户在当前计费周期的累计消息数与 Token 开销 |

---

## 7. Agent 智能体系统 (`src/agents/`)

### 7.1 `src/agents/state.py`
- **文件路径**：`src/agents/state.py`
- **功能描述**：定义智能体运行时的状态载荷。
- **核心状态定义**：
  ```python
  from typing import Annotated, Any, TypedDict
  from langchain_core.messages import BaseMessage
  import operator

  class AgentState(TypedDict):
      user_id: str
      conversation_id: str
      query: str
      messages: Annotated[list[BaseMessage], operator.add]
      selected_agent: str
      target_model: str
      memory_context: str
      intermediate_steps: list[dict[str, Any]]
      final_output: str
  ```

---

### 7.2 `src/agents/base.py`
- **文件路径**：`src/agents/base.py`
- **功能描述**：所有 Agent 的通用抽象基类。
- **核心抽象方法**：
  - `class BaseAgent(ABC)`：
    - `name: str`：智能体标识。
    - `description: str`：智能体职责说明。
    - `@abstractmethod async def run(self, state: AgentState) -> dict[str, Any]`：同步执行模式。
    - `@abstractmethod async def astream(self, state: AgentState) -> AsyncIterator[str]`：异步流式生成模式。

---

### 7.3 `src/agents/router.py`
- **文件路径**：`src/agents/router.py`
- **功能描述**：意图识别与 Sub-Agent 派发路由。
- **核心类与方法**：
  - `class AgentRouter`：
    - `async def route(self, query: str, override: str | None = None) -> str`：
      - 若用户在输入中携带 `@code`、`@search` 等指令或前端明确指定 `override`，则强制直通对应 Sub-Agent。
      - 否则使用轻量意图分类提示词调用网关，智能判定属于 `code`、`search`、`analysis`、`creative` 还是兜底 `general`。

---

### 7.4 各具体 Sub-Agent 详细实现

| 文件路径 | 智能体类名 | 职责定位 | 核心提示词与编排逻辑 |
|---|---|---|---|
| `src/agents/main_agent.py` | `MainAgent(BaseAgent)` | 意图解析、任务协调、记忆融合与最终回答汇总 | 解析用户 Query，协调 `AgentRouter` 分发给专业 Agent，聚合多步骤执行结果输出 |
| `src/agents/code_agent.py` | `CodeAgent(BaseAgent)` | 编程、调试、重构与代码审查 | 注入严密的代码规范提示词，强化 Markdown 语法高亮与行号输出，支持 Python / TS / Shell |
| `src/agents/search_agent.py` | `SearchAgent(BaseAgent)` | 联网搜索、文档检索与事实核查 | 触发外网搜索引擎或知识库检索，提取可信参考来源（Citations）并整合入上下文 |
| `src/agents/analysis_agent.py` | `AnalysisAgent(BaseAgent)` | 数据分析、统计计算与表格产出 | 专注结构化数据处理，强制产出 GFM 斑马纹 Markdown 表格与 LaTeX 统计公式 |
| `src/agents/creative_agent.py` | `CreativeAgent(BaseAgent)` | 创意写作、头脑风暴与文案优化 | 微调大模型采样温度（Temperature 0.8~0.9），擅长丰富文采与多角度思维发散 |
| `src/agents/general_agent.py` | `GeneralAgent(BaseAgent)` | 日常问答、通用闲聊与未分类兜底 | 标准轻量通用提示词，低延迟响应日常对话需求 |

---

## 8. 记忆与缓存系统 (`src/memory/`)

严格遵循 requirements.md 第 5 节缓存设计与第 4.2 节向量能力规范。

### 8.1 `src/memory/short_term.py`
- **文件路径**：`src/memory/short_term.py`
- **功能描述**：基于 Redis 的 L1 会话多轮上下文加速缓存（Cache-Aside 模式）。优先从内存读取最近 20 轮上下文（耗时由 18ms 降至 0.8ms），未命中穿透至 MySQL 回填，发生消息编辑/软删除时主动失效缓存保证一致性。
- **Key 规范**：`conv:{conversation_id}:context`（Redis String 序列化 JSON 结构，TTL 1800 秒，会话活跃自动滑动续期）。
- **核心函数**：
  - `async def get_context(self, conversation_id: str) -> list[dict[str, str]] | None`：从 Redis 读取多轮问答列表，未命中或异常返回 None（Fail-Open 兜底）。
  - `async def set_context(self, conversation_id: str, messages: list[dict[str, str]], ttl: int = 1800) -> bool`：写入/回填最近多轮上下文并刷新 TTL。
  - `async def append_message(self, conversation_id: str, role: str, content: str, max_messages: int = 20, ttl: int = 1800) -> None`：在缓存中追加新一轮问答并保持 20 条滑动窗口大小。
  - `async def clear(self, conversation_id: str) -> bool`：主动失效清除该会话的缓存（在编辑消息、删除消息或删除会话时调用）。

---

### 8.2 `src/memory/long_term.py`
- **文件路径**：`src/memory/long_term.py`
- **功能描述**：基于 OCI MySQL HeatWave 原生向量索引的用户画像与长期记忆。
- **核心函数**：
  - `async def search_memories(self, user_id: str, query: str, top_k: int = 3) -> list[str]`：
    - 读取 Redis 缓存 `memory:{user_id}:ltm:{hash}`，命中直接返回；
    - 未命中则通过 HeatWave 检索并回填 Redis（TTL 10 分钟）。
  - `async def record_fact(self, user_id: str, fact: str, conv_id: str | None = None) -> None`：将重要特征/事实沉淀入向量库。

---

### 8.3 `src/memory/manager.py`
- **文件路径**：`src/memory/manager.py`
- **功能描述**：综合记忆管理器，负责合并短期上下文与长期记忆，生成最终注入 System Prompt 的上下文字符串。
- **核心函数**：
  - `async def assemble_context(self, user_id: str, conversation_id: str, current_query: str) -> str`：并行拉取短期消息列表与关联长期事实，统一拼接为大模型提示词上下文。

---

## 9. API 路由实现 (`src/routers/`)

路由统一接收请求，通过依赖注入解析当前用户，并由 `BaseResponse[T]` 包装出参。

### 9.1 `src/routers/health.py`
- **文件路径**：`src/routers/health.py`
- **端点**：
  - `GET /health` -> `BaseResponse[HealthResponseData]`（Kubernetes Pod 健康探针）
  - `GET /ready` -> `BaseResponse[HealthResponseData]`（就绪探针，验证 MySQL 与 Redis 活性）
  - `GET /live` -> `BaseResponse[HealthResponseData]`（存活探针）

### 9.2 `src/routers/auth.py`
- **文件路径**：`src/routers/auth.py`
- **端点**：
  - `POST /auth/login` -> `BaseResponse[TokenResponseData]`（账号密码登录）
  - `POST /auth/refresh` -> `BaseResponse[TokenResponseData]`（Refresh Token 换发）
  - `POST /auth/logto/callback` -> `BaseResponse[TokenResponseData]`（Logto SSO 回调验票与自动注册）
  - `POST /auth/logout` -> `BaseResponse[None]`（注销当前设备 Session）
  - `GET /auth/me` -> `BaseResponse[UserInfoData]`（获取当前鉴权用户信息）

### 9.3 `src/routers/chat.py`
- **文件路径**：`src/routers/chat.py`
- **端点**：
  - `POST /chat/completions` -> 返回 `StreamingResponse(media_type="text/event-stream")`（核心 SSE 流式对话，实时打字机推流）
  - `POST /chat/stop` -> `BaseResponse[dict]`（手动中止当前正在运行的流式推理）

### 9.4 `src/routers/conversations.py`
- **文件路径**：`src/routers/conversations.py`
- **端点**：
  - `GET /conversations` -> `BaseResponse[PaginatedData[ConversationData]]`（分页查询用户会话列表，强制 user_id 行级隔离）
  - `POST /conversations` -> `BaseResponse[ConversationData]`（新建会话）
  - `GET /conversations/{id}` -> `BaseResponse[ConversationData]`（获取指定会话详情）
  - `PUT /conversations/{id}` -> `BaseResponse[ConversationData]`（重命名标题/修改绑定模型）
  - `DELETE /conversations/{id}` -> `BaseResponse[None]`（删除会话，级联清理消息与缓存）
  - `POST /conversations/{id}/archive` -> `BaseResponse[ConversationData]`（归档会话）
  - `POST /conversations/{id}/unarchive` -> `BaseResponse[ConversationData]`（取消归档）

### 9.5 `src/routers/messages.py`
- **文件路径**：`src/routers/messages.py`
- **端点**：
  - `GET /messages` -> `BaseResponse[PaginatedData[MessageData]]`（根据 conversation_id 分页拉取历史消息）
  - `DELETE /messages/{id}` -> `BaseResponse[None]`（删除单条消息）
  - `PUT /messages/{id}` -> `BaseResponse[MessageData]`（编辑已发送消息）
  - `POST /messages/{id}/regenerate` -> 返回 `StreamingResponse(media_type="text/event-stream")`（重新生成 AI 回复）

### 9.6 `src/routers/users.py`
- **文件路径**：`src/routers/users.py`
- **端点**：
  - `GET /users/profile` -> `BaseResponse[UserInfoData]`（获取个人主页信息）
  - `PUT /users/profile` -> `BaseResponse[UserInfoData]`（修改头像与基础资料）
  - `PUT /users/preferences` -> `BaseResponse[UserInfoData]`（修改用户全局默认模型与 Agent）
  - `GET /users/usage` -> `BaseResponse[UsageStatsData]`（查看当前用户的消息总数与 Token 用量统计）

### 9.7 `src/routers/sessions.py`
- **文件路径**：`src/routers/sessions.py`
- **端点**：
  - `GET /sessions` -> `BaseResponse[list[UserSessionItem]]`（查看用户当前所有在线设备列表）
  - `POST /sessions/{id}/revoke` -> `BaseResponse[None]`（远程踢出指定设备会话，写入 Redis 黑名单）

### 9.8 `src/routers/__init__.py`
- **文件路径**：`src/routers/__init__.py`
- **功能描述**：将上述所有 Router 统一集中挂载到 `api_router` 根树上。

---

## 10. 中间件与通用工具 (`src/middleware/`, `src/utils/`)

### 10.1 `src/middleware/auth_middleware.py`
- **文件路径**：`src/middleware/auth_middleware.py`
- **功能描述**：FastAPI `Depends(get_current_user)` 鉴权依赖注入。
- **核心逻辑**：
  1. 从 HTTP Header 提取 `Authorization: Bearer <token>`。
  2. 使用 `jwt_secret` 解码，提取 `sub` (`user_id`) 与 `jti`。
  3. 查询 Redis 黑名单：`await session_service.is_jti_blacklisted(jti)`，若已拉黑抛出 401。
  4. 返回上下文 `CurrentUser` 实体供业务接口使用。

### 10.2 `src/middleware/logging_middleware.py` & `cors_middleware.py`
- **`logging_middleware.py`**：计算请求耗时，记录请求 URL、方法、状态码至 Loguru，并注入 `X-Request-ID`。
- **`cors_middleware.py`**：仅允许前端来源 `https://gw.jppwl.asia` 与本地调试源 (`http://localhost:5173`, `http://localhost:3000`)。

### 10.3 `src/utils/validators.py`, `helpers.py`, `formatters.py`
- **`validators.py`**：提供 `validate_uuid`、`validate_message_length` 等校验函数。
- **`helpers.py`**：封装 `generate_uuid()`、`utcnow()` 与密码哈希验证。
- **`formatters.py`**：提供 `format_sse_event(data: dict) -> str` 组装 SSE 数据帧。

---

## 11. 应用工厂与启动入口 (`src/main.py`, `src/server.py`)

### 11.1 `src/main.py`
- **文件路径**：`src/main.py`
- **功能描述**：FastAPI 应用工厂模块，生命周期编排与全局统一异常捕获。
- **核心代码结构**：
  ```python
  from contextlib import asynccontextmanager
  from fastapi import FastAPI, Request
  from fastapi.middleware.cors import CORSMiddleware
  from fastapi.responses import JSONResponse
  from loguru import logger

  from src.configs.config import APP_ENV, get_settings
  from src.engine.mysql_client import MySQLClient
  from src.engine.redis_client import RedisClient
  from src.routers import api_router


  @asynccontextmanager
  async def lifespan(app: FastAPI):
      settings = get_settings()
      logger.info(f"Starting {settings.app_name} v{settings.app_version}")
      logger.info(f"Environment: {APP_ENV}")

      # 初始化存储与外部连接池
      app.state.mysql_client = MySQLClient(settings.database_url)
      app.state.redis_client = RedisClient(settings.redis_url)
      await app.state.mysql_client.check_connection()
      await app.state.redis_client.ping()

      yield

      # 优雅释放资源
      logger.info("Shutting down storage connections...")
      await app.state.mysql_client.close()
      await app.state.redis_client.close()
      logger.info("Application shutdown complete.")


  def create_app() -> FastAPI:
      settings = get_settings()

      app = FastAPI(
          title=settings.app_name,
          version=settings.app_version,
          docs_url="/docs" if settings.debug else None,
          redoc_url="/redoc" if settings.debug else None,
          openapi_url="/openapi.json" if settings.debug else None,
          root_path=settings.root_path,
          lifespan=lifespan,
      )

      # 挂载 CORS 中间件
      app.add_middleware(
          CORSMiddleware,
          allow_origins=settings.cors_origins,
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )

      # 挂载统一路由树
      app.include_router(api_router)

      # 全局异常捕获兜底
      @app.exception_handler(Exception)
      async def global_exception_handler(request: Request, exc: Exception):
          logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
          return JSONResponse(
              status_code=500,
              content={
                  "code": 500,
                  "message": "Internal server error",
                  "data": None,
              },
          )

      return app


  app = create_app()
  ```

---

### 11.2 `src/server.py`
- **文件路径**：`src/server.py`
- **功能描述**：服务启动主入口，解析配置并启动 Uvicorn。
- **核心代码结构**：
  ```python
  import sys
  from pathlib import Path
  import uvicorn
  from loguru import logger

  project_root = Path(__file__).parent.parent
  sys.path.insert(0, str(project_root))

  from src.configs.config import APP_ENV, get_settings
  from src.main import app


  def main() -> None:
      settings = get_settings()
      logger.info(f"Starting {settings.app_name} server on {settings.host}:{settings.port} [{APP_ENV}]...")

      uvicorn.run(
          "src.server:app",
          host=settings.host,
          port=settings.port,
          workers=settings.workers,
          log_level=settings.log_level.lower(),
          reload=settings.debug,
      )


  if __name__ == "__main__":
      main()
  ```

---

## 12. 测试套件规范 (`test/`)

遵循 pytest + pytest-asyncio 测试标准：

1. **`test/conftest.py`**：
   - 注入测试环境变量，提供 SQLite 内存数据库与内存 Redis Mock。
   - 提供 `async_client` fixture，自动携带模拟有效用户的 Bearer Token。
2. **测试模块覆盖要求**：
   - `test/test_routers/test_health.py`：验证 `/health` 与探针状态码返回。
   - `test/test_routers/test_auth.py`：测试密码登录、错误拦截及 JWT 刷新。
   - `test/test_routers/test_conversations.py`：**重点测试多租户数据隔离**（确保用户 A 无法读取或操作用户 B 的会话）。
   - `test/test_services/test_chat_service.py`：测试流式 SSE 组帧与手动中止逻辑。
   - `test/test_agents/test_router.py`：测试 `@` 指令与意图分类路由器的命中准确率。

---

## 13. 开发里程碑与执行步骤

| 阶段 | 交付物 | 关键验证指标 | 状态 |
|---|---|---|---|
| **Phase 1: 基础脚手架与存储引擎** | `pyproject.toml`, `uv.lock`, `src/configs/`, `src/engine/`, `src/routers/health.py` | `uv run python -m src.server` 启动成功，`/health`, `/ready`, `/live` 三重探针健全，90 个测试全绿 | ✅ 已完成 |
| **Phase 2: 鉴权开关与会话管理** | `src/utils/jwt.py`, `src/services/auth.py`, `src/services/logto_service.py`, `src/routers/auth.py`, `src/routers/sessions.py` | 支持 `AUTH_ENABLED` 与 Cloudflare 同域多模式；JWT 签发/刷新、会话踢出正常，159 个测试全绿 | ✅ 已完成 |
| **Phase 3: 会话与消息管理** | `src/models/conversation.py`, `src/routers/conversations.py` | 严格基于 `user_id` 强行级隔离；会话 CRUD、消息编辑软删除 API 全通，190 个测试全绿 | ✅ 已完成 |
| **Phase 4: Agent 与流式对话** | `src/engine/litellm_client.py`, `src/agents/`, `src/routers/chat.py` | LiteLLM 网关对接，LangGraph 动态意图路由，`/chat/stream` SSE 输出与 `/chat/stop` 中止，208 个测试全绿 | ✅ 已完成 |
| **Phase 5: 高级扩展与企业级治理** | `src/routers/users.py`, `src/middleware/`, `src/engine/vector_store.py`, `src/models/knowledge.py` | 用户画像、用量统计、RequestID/Timing/RateLimit 中间件、OCI MySQL HeatWave 向量检索，226 个测试全绿 (93.66% 覆盖率) | ✅ 已完成 |

---

## 14. `uv` 原生工具链与本地开发运维规范

本项目后端强制使用 Astral `uv` 全家桶进行日常开发、包管理、格式化与测试，严禁直接使用 `pip`、`pipenv` 或手动激活裸虚拟环境：

### 14.1 核心命令速查表

| 开发操作 | `uv` 规范命令 | 传统命令对比（已废除） | 说明 |
|---|---|---|---|
| **创建虚拟环境** | `uv venv` | `python -m venv .venv` | 自动匹配 pyproject 的 Python 版本要求 |
| **同步完整依赖** | `uv sync --extra dev` | `pip install -r requirements.txt` | 包含开发/代码质量/测试依赖，秒级全量更新 |
| **仅同步生产依赖** | `uv sync --no-dev` | `pip install ...` | 生产镜像与极简部署环境使用 |
| **锁定依赖版本** | `uv lock` | `pip freeze > ...` | 生成/更新平台无关的高精度 `uv.lock` |
| **新增生产依赖** | `uv add fastapi litellm` | `pip install x && vim pyproject` | 自动解析版本、安装并写入 `pyproject.toml` |
| **新增开发依赖** | `uv add --dev pytest-mock` | `pip install ...` | 自动归类写入 `[project.optional-dependencies].dev` |
| **移除依赖** | `uv remove <pkg>` | `pip uninstall <pkg>` | 自动卸载并自 `pyproject.toml` 清除 |
| **本地启动后端** | `uv run python -m src.server` | `python src/server.py` | 自动加载 `.venv` 环境，免去手动 `source` |
| **执行单元测试** | `uv run pytest` | `pytest` | 自动在隔离沙盒内运行，带覆盖率检测 |
| **代码格式化** | `uv run black . && uv run isort .` | `black .` | 确保提交前代码风格统一 |
| **静态分析与 Lint** | `uv run ruff check .` | `flake8 .` | 极速 Rust 代码检查与自动修复 (`--fix`) |
| **静态类型检查** | `uv run mypy src/` | `mypy src/` | 严格模式类型验证 |

### 14.2 本地开发者工作流（从 0 到 1 启动后端）

```bash
cd backend/

# 1. 复制环境变量模板
cp .env-template .env
# (编辑 .env 填入 MySQL、Redis 及 LiteLLM API 地址与密钥)

# 2. 一键秒级安装与同步依赖 (创建 .venv 并锁定)
uv sync --extra dev

# 3. 运行本地开发服务器 (支持热重载)
uv run python -m src.server

# 4. 提交代码前的代码质量检查
uv run isort src test && uv run black src test
uv run ruff check src test
uv run mypy src
uv run pytest
```

---

## 15. 技术架构演进与关键实现细节 (Architecture Evolution & Technical Details)

在实际工程构建与落地过程中，结合主人的技术演进诉求（如 Cloudflare 同域部署、开发模式快速调试、严格数据合规等），系统在架构上进行了如下针对性增强与细化：

### 15.1 认证架构解耦与 Cloudflare 同域 / OIDC JWKS 公钥验签设计 (`src/services/auth.py`)

在标准企业级 OIDC / SSO 架构中，**后端作为资源服务器 (Resource Server)，根本不需要也不应该持有任何签发 Token 的对称私密密钥（如所谓的 `JWT_SECRET`）**。

#### 1. 核心安全机制解耦（告别后端保存对称密钥）
- **Logto 签发与校验机制**：
  - 用户微信扫码登录后，Token 是由 Logto 统一身份认证中心（IdP）使用其自身的非对称私钥（RS256）签发的；
  - Astra 后端只需拉取 Logto 的公开证书集合 **JWKS (JSON Web Key Set)**（端点：`https://auth.jppwl.asia/oidc/jwks`），即可在内存中利用**公钥**无状态验签，零网络开销且从根本上杜绝私钥泄漏风险；
- **Cloudflare Access 签发与校验机制**：
  - 在 Cloudflare 同域模式下，Edge 注入的 `CF-Access-Jwt-Assertion` 头直接通过 Cloudflare 的官方公共证书端点 (`https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`) 校验，同样无需后端存储任何加解密密钥；
- **自签 `JWT_SECRET` 的定位**：
  - 仅作为本地无网络断网调试、开发环境快捷账密登录 (`/auth/login`) 或纯 Mock 模式的兜底回退，**严禁也不需要在生产 OCI Vault 中为此分配机密配额**。

#### 2. OCI Vault 生产机密注入极简清单
彻底剔除 `JWT_SECRET` 伪机密后，生产环境部署需注入 **OCI Vault (Secrets in Vault)** 的真正核心密码仅需 **3 项基础设施机密**（Cloudflare 同域模式）或最多 **4 项**（Logto 模式）：

| 序号 | 变量名称 | 建议 OCI Vault Secret 名称 | 类别 | 说明 |
| :---: | :--- | :--- | :---: | :--- |
| **1** | `APP_DATABASE_URL` (或 `APP_DB_PASSWORD`) | `astra-mysql-heatwave-url` | **纯密码/连接串** | OCI MySQL HeatWave 专属业务用户 (`astra_user`) 高强密码连接串 |
| **2** | `APP_REDIS_URL` (或 `APP_REDIS_PASSWORD`) | `astra-redis-url` | **纯密码/连接串** | Redis 边缘实例鉴权访问连接串 |
| **3** | `APP_LITELLM_API_KEY` | `astra-litellm-api-key` | **网关特权密钥** | 私有 LiteLLM 网关 (`https://litellm.jppwl.asia`) 专属分配给 Astra 应用的 **Virtual Key** (`sk-hsbc-...`)，用于计量与隔离 |
| **4** | `APP_LOGTO_APP_SECRET` *(仅 Logto 独立模式需)* | `astra-logto-app-secret` | **第三方通信密钥** | 仅在使用后端 Code 换 Token 的机密客户端时需要；若采用 Cloudflare 同域模式则**无需此项** |

> 📌 **其余所有参数**（如 `APP_ENVIRONMENT=prod`、`APP_AUTH_MODE=cloudflare`、`APP_LITELLM_BASE_URL`、`APP_CLOUDFLARE_AUDIENCE`、`APP_DB_USER=astra_user` 等）均为公开配置或应用标识，直接统一存放在 **K8s ConfigMap** 或标准环境变量即可，极大地节约了 OCI Vault 资源并简化了运维开销。

#### 3. 认证开关与多模式环境变量配置
```bash
# 是否开启认证: true = 强校验; false = 完全跳过认证（单机调试、自动化测试）
APP_AUTH_ENABLED=true

# 认证模式: logto | cloudflare | none
# - logto: 标准 Logto OIDC 微信扫码，直接通过 JWKS 公钥端点验签，后端无需保存签名密钥
# - cloudflare: Cloudflare Zero Trust 同域认证，自动解析 CF-Access-Jwt-Assertion 公钥验签
# - none: 完全免认证（等同于 auth_enabled=false，直接注入 anonymous 用户）
APP_AUTH_MODE=cloudflare

# Cloudflare Access 配置 (仅 auth_mode=cloudflare 时生效)
APP_CLOUDFLARE_TEAM_NAME=your-team-name
APP_CLOUDFLARE_AUDIENCE=your-audience-tag
```

#### 4. 三种模式行为矩阵
| 认证模式 | `auth_enabled` | `auth_mode` | 凭据来源与验签方式 | 适用场景 | 前端行为 |
|---|---|---|---|---|---|
| **Cloudflare 同域模式（推荐）** | `true` | `cloudflare` | HTTP `CF-Access-Jwt-Assertion`，通过 CF 公开证书验签 | Cloudflare Access 保护的前后端同域反代 (`gw.jppwl.asia/astra/` 与 `/astra/api`) | **前端无需保存或传输任何 Bearer Token**，Cloudflare Edge 自动注入 Assertion 头，后端自动提取用户身份，杜绝 XSS 盗取 Token |
| **Logto SSO 独立模式** | `true` | `logto` | HTTP `Authorization: Bearer <JWT>`，通过 Logto JWKS 公钥验签 | 经典跨域部署、独立域名部署 | 前端在 LocalStorage 存储 JWT并在请求头附加 Bearer 令牌，支持 Refresh Token 刷新 |
| **调试 / 离线模式** | `false` | 任意 / `none` | 无需凭据，直接放行 | 本地极速开发、离线 CI/CD 单元测试 | 所有受保护路由自动注入默认 `anonymous` 匿名用户，`/sessions` 接口优雅返回空列表，免去反复登录 |

#### 5. 依赖注入透明分发 (`get_current_user`)
无论在何种模式下，FastAPI 路由只需声明 `current_user: Annotated[User, Depends(get_current_user)]`，依赖注入函数会在底层自动根据配置路由至对应的解析器：
```python
async def get_current_user(request: Request, settings: Settings) -> User:
    if not settings.auth_enabled:
        return User(id="anonymous", username="anonymous", ...)
    if settings.auth_mode == "cloudflare":
        return await _get_user_from_cloudflare(request, settings)
    return await _get_user_from_jwt(request, settings)
```

---

### 15.2 会话追踪与多设备远程下线 (`src/models/user.py`, `src/routers/sessions.py`)

- **设备会话追踪 (`user_sessions`)**：每次登录成功自动在 MySQL 记录客户端 IP、设备类型与会话过期时间；
- **远程注销与踢出**：
  - `DELETE /sessions/{session_id}`：用户在任一客户端可主动踢出其他异常设备；
  - `DELETE /sessions`：一键踢出当前设备以外的所有历史登录。

---

### 15.3 严格多租户行级数据隔离与全链路设备审计链 (`src/models/conversation.py`)

系统在 ORM 仓储层与路由层实现了端到端的强行级隔离（Row-Level Security）与金融级设备溯源追溯体系：

#### 1. 强租户行级隔离 (Row-Level Security)
- **所有 SQL 范围收敛**：`ConversationRepository` 与 `MessageRepository` 的所有 `select`、`update`、`delete` 操作，必须强制追加 `where(Model.user_id == current_user.id)`；
- **防枚举探测**：当用户尝试访问、修改或删除不属于自己的 `conversation_id` 或 `message_id` 时，统一返回 `404 Not Found`，绝不返回 `403`，彻底杜绝数据 ID 枚举漏洞。

#### 2. 金融级设备审计与全链路追溯 (`session_id` 关联)
针对金融内控合规（如 SOC2 / 金融业数据出境安全审计）中“不仅要追查责任人 (`user_id`)，还要精确溯源到具体物理设备 (`device_info`) 与登录 IP (`ip_address`)”的硬性要求：
- **跨表关联外键**：在 `conversations` 与 `messages` 表中显式引入 `session_id VARCHAR(36) NULL` 外键与索引，指向 `user_sessions(id)`；
- **解耦保护策略 (`ON DELETE SET NULL`)**：当用户的登录设备会话自然过期或被管理员踢出删除时，历史对话和问答数据绝对不受影响，关联键平滑置空（`NULL`），兼顾审计追溯与会话清理的解耦；
- **全链路四表联查审计 SQL 范式**：
  ```sql
  SELECT 
      u.username,
      s.device_info,
      s.ip_address,
      c.title AS conversation_title,
      m.role,
      m.content,
      m.created_at
  FROM messages m
  JOIN user_sessions s ON m.session_id = s.id
  JOIN users u ON m.user_id = u.id
  JOIN conversations c ON m.conversation_id = c.id
  WHERE m.user_id = :uid
  ORDER BY m.created_at DESC
  LIMIT 50;
  ```
  由于各关键字段均建有单列覆盖索引，该四表联查耗时稳定在 `< 5ms` 以内。

---

### 15.4 LiteLLM 接入与 LangGraph 动态智能体编排 (`src/engine/litellm_client.py`, `src/agents/`)

- **网关统一接入**：通过 `LiteLLMClient` 对接私有网关（`https://litellm.jppwl.asia`），自动规范化模型前缀，**显式禁用 Telemetry 遥测以满足金融安全审计规范**；
- **意图自动路由 (`resolve_agent_intent`)**：
  - 用户指定智能体偏好为 `auto` 时，系统自动根据 Query 关键词分流：
    - 编程/函数/bug -> `code_assistant`；
    - 深度思考/公式推导 -> `deep_reasoner`；
    - 常见闲聊 -> `direct_chat`；
- **可中断的流式打字机输出 (`astream_chat`)**：
  - 流生成器与 Redis 信号联动（`chat:stop:{conv_id}`），当用户在前端点击“停止推理”时，毫秒级终止下一 Token 的生成并安全断开流连接；
  - 流式推流完毕后，采用**独立且受控的数据库事务 session** 将 Assistant 完整回复持久化入库，杜绝请求生命周期结束引发的会话泄漏。

---

### 15.5 企业级中间件治理体系 (`src/middleware/`)

FastAPI 采用标准洋葱模型装配三个核心中间件：
1. **`RequestIDMiddleware` (最外层)**：从入站请求中提取或生成全局唯一 UUID，并使用 `logger.contextualize(request_id=...)` 将其注入当前异步协程的日志上下文，响应头自动追加 `X-Request-ID`；
2. **`TimingMiddleware`**：纳秒级高精度度量请求往返耗时，响应头附加 `X-Process-Time`（毫秒），并自动对 `/live` 探针降噪；
3. **`RateLimitMiddleware`**：基于 Redis 滑动窗口计数器（默认 120 RPM），超出限额直接返回 `429 Too Many Requests` 与 `Retry-After`，同时设计了 **Fail-Open（故障自愈放行）** 机制。

---

### 15.6 OCI MySQL HeatWave 原生向量检索与降级容灾 (`src/engine/vector_store.py`)

- **HeatWave 原生加速**：充分利用 MySQL 8.4+ HeatWave 原生 `VECTOR(1536)` 列类型与 `DISTANCE(embedding, string_to_vector(:vec), 'COSINE')` 向量距离函数；
- **跨环境平滑降级**：在非 HeatWave 生产环境（如开发者本地调试、CI/CD 单元测试）中，系统自动捕获异常并降级至纯 Python 高精度余弦相似度计算，保证任何机器上一键运行测试。

---
*Cindy 已将全部关键技术细节、认证开关机制与各阶段演进方案完整沉淀至开发规划文档！* 💋
