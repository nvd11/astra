# Chat App 需求文档

> **项目代号**：Astra  
> **文档版本**：v1.1  
> **创建日期**：2026-09-06  
> **更新日期**：2026-09-06  
> **作者**：Rin（远坂凛）  
> **状态**：需求确认中

---

## 1. 项目概述

### 1.1 项目背景

开发一款类似 DeepSeek Web 的现代 LLM 对话应用，支持完整的 Markdown 渲染、LaTeX 公式、多轮对话、流式输出。采用前后端分离架构，后端基于 FastAPI + LangChain，对接私有 LiteLLM 网关，通过 ArgoCD 部署至 K3s 集群。

### 1.2 核心目标

- 提供流畅的 LLM 对话体验，支持 Markdown / 表格 / LaTeX 完整渲染
- 实现 Main Agent + Sub-Agent 多智能体架构，具备记忆能力
- 多用户数据完全隔离，支持私有化部署
- 利用 OCI MySQL HeatWave 原生向量能力，简化架构
- Redis 缓存加速，容忍穿透，最终一致性
- **Cloudflare 域名 + Edge SSL 全站 HTTPS**
- **Logto SSO 统一认证，微信扫码登录**

---

## 2. 功能需求

### 2.1 前端功能

| 优先级 | 功能 | 描述 |
|--------|------|------|
| P0 | Markdown 完整渲染 | 标题、列表、代码块（语法高亮）、引用、分割线、链接、图片 |
| P0 | GFM 表格支持 | 边框、对齐、斑马纹，响应式适配 |
| P0 | LaTeX 公式渲染 | KaTeX 引擎，行内 `$...$` 与独立 `$$...$$` |
| P0 | 流式输出 | SSE/WebSocket 打字机效果，支持中断 |
| P0 | 多轮对话 | 上下文管理，历史消息加载 |
| P0 | **Logto SSO 登录** | 微信扫码 / OIDC 认证，自动跳转 |
| P1 | 会话管理 | 新建、重命名、删除、归档、搜索 |
| P1 | 消息操作 | 复制、重新生成、编辑、删除 |
| P1 | 主题切换 | 深色/浅色模式，跟随系统 |
| P2 | 代码块增强 | 行号、复制按钮、语言标识 |
| P2 | 导出功能 | Markdown / PDF / PNG 导出 |

### 2.2 后端功能

| 优先级 | 功能 | 描述 |
|--------|------|------|
| P0 | Main Agent | 用户 Query 接收、意图识别、任务分发、结果聚合 |
| P0 | Sub-Agent 集群 | 代码、搜索、分析、创作等专业化子代理 |
| P0 | 记忆能力 | 短期记忆（会话上下文）+ 长期记忆（用户画像/历史） |
| P0 | **Logto SSO 集成** | OIDC 认证、JWT 签发、用户同步 |
| P0 | 多用户隔离 | JWT 认证，数据行级隔离，记忆独立 |
| P0 | LiteLLM 对接 | OpenAI 兼容格式，多模型切换 |
| P1 | 流式响应 | SSE 推送，支持中断与重连 |
| P1 | 会话持久化 | MySQL 存储，支持历史回看 |
| P2 | 文件上传 | 图片/文档解析，多模态输入 |
| P2 | 插件系统 | Function Calling / MCP 工具调用 |

### 2.3 Sub-Agent 分工

| Agent 名称 | 职责 | 触发方式 |
|------------|------|----------|
| `main_agent` | 意图识别、任务分发、结果聚合、上下文维护 | 默认入口 |
| `code_agent` | 代码生成、审查、调试、解释 | 自动路由 / `@code` |
| `search_agent` | 网络搜索、文档检索、实时信息 | 自动路由 / `@search` |
| `analysis_agent` | 数据分析、图表生成、统计计算 | 自动路由 / `@analysis` |
| `creative_agent` | 文案创作、头脑风暴、内容优化 | 自动路由 / `@creative` |
| `general_agent` | 兜底通用对话，无法分类时的默认处理 | 自动路由 |

---

## 3. 技术架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Edge CDN                       │
│              *.jppwl.asia · 免费 Universal SSL 终结          │
│              HTTP/2 & HTTP/3 (QUIC) · WebSocket 支持         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Kong Gateway (K3s)                         │
│              路径路由 / Forward-Auth / 限流                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│      Logto SSO          │       │      Astra Frontend     │
│   auth.jppwl.asia       │◄─────►│   (React + Vite)        │
│   微信扫码 / OIDC        │       │   astra.jppwl.asia      │
└─────────────────────────┘       └─────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────────────┐
                                    │      Astra Backend      │
                                    │   (FastAPI + LangGraph) │
                                    │   api.jppwl.asia        │
                                    └─────────────────────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                        ┌─────────┐     ┌─────────┐     ┌─────────┐
                        │ LiteLLM │     │  Redis  │     │  MySQL  │
                        │  网关   │     │  缓存   │     │HeatWave │
                        └─────────┘     └─────────┘     └─────────┘
```

### 3.2 技术选型

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **前端框架** | React + TypeScript | 18+ | 组件化开发 |
| **UI 组件库** | shadcn/ui / Ant Design | latest | 高质量组件 |
| **样式方案** | Tailwind CSS | 3.x | 原子化 CSS |
| **Markdown 渲染** | react-markdown + remark-gfm + rehype-katex | latest | 完整 GFM + LaTeX |
| **代码高亮** | highlight.js / prism | latest | 语法高亮 |
| **构建工具** | Vite | 5.x | 极速冷启动 |
| **后端框架** | FastAPI | 0.100+ | 异步高性能 |
| **Agent 框架** | LangGraph / LangChain | latest | 多 Agent 编排 |
| **LLM 接入** | LiteLLM (OpenAI 兼容) | - | 私有网关 |
| **数据库** | OCI MySQL HeatWave | 26.7.0-cloud | 关系 + 向量一体化 |
| **缓存** | Redis (K3s) | 7.2-alpine | 热点数据加速 |
| **ORM** | SQLAlchemy + asyncpg | 2.0+ | 异步 ORM |
| **认证** | Logto SSO (OIDC) | latest | 微信扫码 / 统一认证 |
| **部署** | ArgoCD + K3s | - | GitOps 持续交付 |
| **CDN/SSL** | Cloudflare | - | Edge SSL + 全球加速 |

---

## 4. 数据库设计

### 4.1 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    avatar_url TEXT,
    preferences JSON,           -- 用户偏好设置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 会话表
CREATE TABLE conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    title VARCHAR(255) DEFAULT '新对话',
    model VARCHAR(64),          -- 使用的模型
    system_prompt TEXT,         -- 自定义系统提示词
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_updated (user_id, updated_at DESC)
);

-- 消息表
CREATE TABLE messages (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    conversation_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,  -- 冗余，便于查询隔离
    role ENUM('user', 'assistant', 'system', 'tool') NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,              -- 工具调用、引用来源等
    tokens_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_conversation_created (conversation_id, created_at)
);

-- 长期记忆表（利用 MySQL 26.x VECTOR 类型）
CREATE TABLE long_term_memories (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    content TEXT NOT NULL,      -- 记忆内容
    embedding VECTOR(1536),     -- 向量嵌入（HeatWave 原生支持）
    memory_type ENUM('fact', 'preference', 'summary', 'instruction') DEFAULT 'fact',
    importance_score FLOAT DEFAULT 0.5,
    source_conversation_id CHAR(36),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_type (user_id, memory_type),
    INDEX idx_user_importance (user_id, importance_score DESC)
);

-- Agent 任务记录表
CREATE TABLE agent_tasks (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    conversation_id CHAR(36),
    user_id CHAR(36) NOT NULL,
    agent_name VARCHAR(64),
    input_text TEXT,
    output_text TEXT,
    status ENUM('pending', 'running', 'completed', 'failed'),
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 4.2 向量能力说明

OCI MySQL HeatWave 26.7.0-cloud 原生支持：
- `VECTOR` 数据类型：存储向量嵌入
- HNSW 向量索引：`rapid_auto_vector_index_enabled: ON`
- 内置 Embedding 模型：`all_minilm_l12_v2` / `minilm`
- 向量存储过程：`vector_store_load`, `ML_VECTOR_STORE_DISCOVERY`, `ML_RETRIEVE_VECTOR_TABLES`

**架构优势**：无需额外部署 Chroma/Qdrant，关系数据与向量数据统一存储。

---

## 5. 缓存设计

### 5.1 缓存策略

| 数据类型 | 策略 | TTL | 说明 |
|----------|------|-----|------|
| 用户会话上下文 | 写穿 + 读穿 | 30 分钟 | 当前对话完整消息历史 |
| 用户偏好设置 | 写穿 | 1 小时 | 模型选择、主题、语言 |
| 长期记忆检索结果 | 读穿 | 10 分钟 | 相同查询的语义检索结果 |
| 会话列表 | 读穿 | 5 分钟 | 用户对话列表（侧边栏） |
| 热点消息 | 只读缓存 | 1 小时 | 被频繁引用的历史消息 |
| Token 用量统计 | 写后失效 | 实时 | 用户配额计数 |

### 5.2 Redis Key 规范

```
# 用户相关
user:{user_id}:profile          # 用户资料
user:{user_id}:preferences      # 用户偏好
user:{user_id}:quota            # 配额计数

# 会话相关
conv:{conv_id}:messages         # 会话消息列表（List）
conv:{conv_id}:context          # 当前上下文（Hash）
user:{user_id}:conversations    # 用户会话列表（ZSet，按时间排序）

# 记忆相关
memory:{user_id}:ltm:{hash}     # 长期记忆检索缓存
memory:{user_id}:summary        # 用户画像摘要

# 系统相关
model:config:{model_name}       # 模型配置
system:prompt:{prompt_id}       # 系统提示词模板
```

### 5.3 最终一致性策略

**方案 A：容忍缓存穿透，直接打 MySQL**

```
正常流程：
请求 → Redis（命中）→ 返回
请求 → Redis（未命中）→ MySQL → 写 Redis → 返回

Redis 故障流程：
请求 → Redis（连接失败/超时）→ 降级标记 → MySQL → 直接返回（不写缓存）
```

**延迟双删（写操作）：**
1. 更新 MySQL
2. 删除 Redis 缓存（第一次）
3. 休眠 500ms（或异步延迟）
4. 再次删除 Redis 缓存（第二次）

**防护机制：**
- 穿透：缓存空值（`null` 占位，TTL 60s）
- 击穿：热点 Key 互斥重建（`SETNX` 分布式锁）
- 雪崩：TTL 加随机抖动（基础 TTL + random(0, 300s)）

---

## 6. 多用户隔离

### 6.1 隔离层级

| 层级 | 方案 | 说明 |
|------|------|------|
| **边缘层** | Cloudflare Edge SSL + CDN | 全站 HTTPS，DDoS 防护，全球加速 |
| **认证层** | Logto SSO (OIDC) + FastAPI `Depends(get_current_user)` | 微信扫码 / OIDC 认证，JWT 解析提取 `user_id` |
| **API 路由** | 路径参数或请求头携带 `user_id` | `/api/v1/users/{user_id}/chat` |
| **数据库** | `user_id` 外键 + 行级隔离 | 所有表带 `user_id`，查询强制过滤 |
| **Redis** | Key 前缀 `user:{user_id}:*` | 短期记忆、会话缓存隔离 |
| **向量检索** | Metadata 过滤 | `user_id` 作为 metadata 强制过滤 |
| **Agent 上下文** | 每个请求独立 `AgentState` | 不共享全局状态，防止串话 |

### 6.2 Logto SSO 集成方案

**认证流程：**
```
用户访问 astra.jppwl.asia
    ↓
未认证 → 重定向至 auth.jppwl.asia (Logto)
    ↓
微信扫码 / 账号密码登录
    ↓
Logto 回调 astra.jppwl.asia/callback 携带 code
    ↓
后端换取 ID Token + Access Token
    ↓
创建/同步本地用户，签发 JWT
    ↓
后续请求携带 JWT 访问 API
```

**Logto 配置要点：**
- **Endpoint**: `https://auth.jppwl.asia`
- **App ID**: 从 Logto Console 获取
- **App Secret**: 存储于 K8s Secret
- **Redirect URI**: `https://astra.jppwl.asia/callback`
- **Scopes**: `openid profile email`

**用户同步策略：**
- 首次登录自动创建本地用户记录
- `logto_user_id` 映射到本地 `users.id`
- 用户头像、昵称定期从 Logto 同步

### 6.3 安全红线

- 任何数据库查询、向量检索、Redis 操作，**必须**携带 `user_id` 条件
- 禁止任何跨用户的聚合查询（除非管理员权限）
- JWT 过期时间不宜过长（建议 2 小时），支持 Refresh Token 轮换
- 所有外部请求必须经 Cloudflare HTTPS，禁止裸 IP 访问

---

## 7. 部署架构

### 7.1 Monorepo 结构

```
astra/
├── frontend/              # React 前端 (Vite + React 18 + TS)
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── agents/        # Agent 定义
│   │   ├── api/           # API 路由
│   │   ├── core/          # 核心配置 (Logto / JWT / CORS)
│   │   ├── models/        # 数据模型
│   │   └── services/      # 业务逻辑
│   ├── requirements.txt
│   └── Dockerfile
├── k8s/                   # K8s  manifests
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── redis-deployment.yaml
│   ├── ingress.yaml       # Kong HTTPRoute + Cloudflare
│   └── argocd-application.yaml
├── docker-compose.yml     # 本地开发
└── README.md
```

### 7.2 ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: chat-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/nvd11/chat-app.git
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: chat-app
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 7.3 环境变量

| 变量 | 说明 | 存储 |
|------|------|------|
| `DATABASE_URL` | OCI MySQL 连接串 | K8s Secret |
| `REDIS_URL` | Redis 连接串 | K8s Secret |
| `LITELLM_API_KEY` | LiteLLM 网关密钥 | K8s Secret |
| `LITELLM_BASE_URL` | LiteLLM 网关地址 | K8s ConfigMap |
| `JWT_SECRET` | JWT 签名密钥 | K8s Secret |
| `LOGTO_ENDPOINT` | Logto SSO 端点（`https://auth.jppwl.asia`） | K8s ConfigMap |
| `LOGTO_APP_ID` | Logto 应用 ID | K8s Secret |
| `LOGTO_APP_SECRET` | Logto 应用密钥 | K8s Secret |
| `LOGTO_REDIRECT_URI` | 回调地址（`https://astra.jppwl.asia/callback`） | K8s ConfigMap |
| `ENVIRONMENT` | 环境标识（dev/staging/prod） | K8s ConfigMap |

### 7.4 Cloudflare DNS 配置

需在 Cloudflare 控制台（或 API）为 `jppwl.asia` 添加以下记录：

| 记录类型 | 名称 | 目标 | 代理状态 | 用途 |
|----------|------|------|----------|------|
| `A` | `astra` | `43.139.214.231`（腾讯云 K3s） | 🟢 Proxied | 前端入口 |
| `A` | `api.astra` | `43.139.214.231`（腾讯云 K3s） | 🟢 Proxied | 后端 API |

**Cloudflare 特性自动生效：**
- 免费 Universal SSL（ECC/RSA 双证书）
- HTTP/2 & HTTP/3 (QUIC)
- WebSocket 支持
- DDoS 防护 + WAF 基础规则

**Kong HTTPRoute 配置要点：**
- `astra.jppwl.asia` → 前端 Service（静态文件）
- `api.astra.jppwl.asia` → 后端 Service（FastAPI）
- 或单域名路径分流：`/api/*` → 后端，其余 → 前端

---

## 8. 非功能需求

### 8.1 性能指标

| 指标 | 目标值 |
|------|--------|
| 首 token 延迟 | < 500ms |
| 流式输出帧率 | > 20 tokens/s |
| 页面加载时间 | < 2s |
| 缓存命中率 | > 90% |
| 并发支持 | 100+ 用户同时在线 |

### 8.2 可用性

- 目标可用性：99.9%
- 故障恢复时间（RTO）：< 15 分钟
- 数据丢失容忍（RPO）：< 5 分钟

### 8.3 安全

- 全链路 HTTPS/TLS（Cloudflare Edge SSL 终结）
- Logto SSO OIDC 标准认证流程
- JWT 短期有效（2 小时）+ Refresh Token 轮换
- SQL 注入防护（ORM 参数化查询）
- XSS 防护（前端输入过滤 + React 自动转义）
- CORS 严格配置（仅允许 `astra.jppwl.asia`）
- 敏感配置全量 K8s Secret 管理，禁止硬编码

---

## 9. 里程碑规划

| 阶段 | 目标 | 交付物 |
|------|------|--------|
| **M1** | 基础对话功能 | 前端 Markdown 渲染 + 后端 FastAPI + LiteLLM 对接 |
| **M2** | 多用户隔离 + SSO | Logto 认证 + JWT + 数据隔离 + 会话管理 |
| **M3** | Agent 架构 | Main Agent + Sub-Agent + 记忆能力 |
| **M4** | 缓存优化 | Redis 接入 + 最终一致性策略 |
| **M5** | 生产部署 | Cloudflare DNS + ArgoCD + K3s + 监控告警 |

---

## 10. 风险与依赖

| 风险/依赖 | 影响 | 缓解措施 |
|-----------|------|----------|
| LiteLLM 网关稳定性 | 核心功能不可用 | 多模型降级策略，本地缓存常用响应 |
| OCI MySQL 连接数限制 | 高并发时连接耗尽 | 连接池管理，读写分离，SQL 优化 |
| Redis 单点故障 | 缓存失效，性能下降 | 容忍穿透设计，直接打 MySQL |
| K3s 集群资源不足 | 服务不可用 | 资源 requests/limits 合理配置，HPA 自动扩缩容 |

---

## 11. 附录

### 11.1 参考文档

- [OCI MySQL HeatWave 向量功能](https://docs.oracle.com/en-us/iaas/mysql-database/doc/heatwave-vector-store.html)
- [LangGraph 多 Agent 编排](https://langchain-ai.github.io/langgraph/)
- [FastAPI 最佳实践](https://fastapi.tiangolo.com/tutorial/)
- [react-markdown 插件生态](https://github.com/remarkjs/react-markdown)

### 11.2 术语表

| 术语 | 说明 |
|------|------|
| **Main Agent** | 主智能体，负责意图识别、任务分发、结果聚合 |
| **Sub-Agent** | 子智能体，专业化处理特定领域任务 |
| **HeatWave** | OCI MySQL 的内存分析引擎，支持向量存储与检索 |
| **Cache-Aside** | 旁路缓存模式，应用层控制缓存读写 |
| **最终一致性** | 允许短暂不一致，异步同步达到一致状态 |

---

> **文档维护**：本需求文档随项目演进持续更新，重大变更需版本号升级。  
> **反馈渠道**：直接在本文档下方留言，或联系 Rin。
