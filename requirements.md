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
- **Kong 网关层 Zero-Trust SSO (Logto + GitHub OAuth + OAuth2-Proxy Forward-Auth)**

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
| P0 | **Kong 网关 SSO 登录** | 复用集群统一 Kong Lua `oauth2-forward-auth`，未登录自动重定向 Logto + GitHub OAuth，共享 `.jppwl.asia` 单点登录 |
| P0 | **多用户界面隔离** | 用户只能看到自己的会话、消息、记忆 |
| P0 | **Session 管理** | 多设备登录管理、会话过期、强制下线 |
| P0 | **响应式全端适配** | 自动适配 Mobile (iOS/Android 触控抽屉 Drawer、dvh 视口与虚拟键盘防遮挡) 与 Desktop (PC 宽屏三栏、侧边栏快捷键折叠) |
| P1 | 会话管理 | 新建、重命名、删除、归档、搜索（仅限当前用户） |
| P1 | 消息操作 | 复制、重新生成、编辑、删除（仅限当前用户消息） |
| P1 | 主题切换 | 深色/浅色模式，跟随系统（用户级偏好存储） |
| P1 | **用户资料页** | 头像、昵称、Logto 绑定信息、用量统计 |
| P1 | **Agent 选择器** | 手动指定 Sub-Agent 或自动路由 |
| P1 | **LLM 模型选择器** | 切换底层模型（DeepSeek / Gemini / Claude 等） |
| P1 | **动态 HTML 交互沙箱 (Artifacts)** | 支持 HTML/JS/CSS 实时渲染预览与双态切换 (代码/预览)、Sandboxed iFrame 零信任安全隔离、全屏与导出 |
| P1 | **多功能导航与扩展入口** | 侧边栏/主导航常驻功能中枢入口，预留 RAG 知识库信息浏览、切片检索、Agent 广场及未来微应用扩展 |
| P2 | 代码块增强 | 行号、复制按钮、语言标识 |
| P2 | 导出功能 | Markdown / PDF / PNG 导出（仅限当前用户会话） |

### 2.2 后端功能

| 优先级 | 功能 | 描述 |
|--------|------|------|
| P0 | Main Agent | 用户 Query 接收、意图识别、任务分发、结果聚合 |
| P0 | Sub-Agent 集群 | 代码、搜索、分析、创作等专业化子代理 |
| P0 | 记忆能力 | 短期记忆（会话上下文）+ 长期记忆（用户画像/历史） |
| P0 | **Kong 网关 SSO 集成** | 接收 Kong `X-Auth-Request-*` 注入头，自动提取/同步 GitHub 用户、绑定设备会话 |
| P0 | **多用户数据隔离** | 用户表、会话表、消息表、记忆表全量 `user_id` 行级隔离 |
| P0 | **多用户缓存隔离** | Redis Key 前缀 `user:{user_id}:*`，Agent 状态独立 |
| P0 | **Session 管理** | JWT 黑名单、多设备会话追踪、强制下线 |
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

### 2.4 Agent 与 LLM 选择器

**智能体动态注册与发现机制 (LangGraph 状态机单源驱动，严禁 Hardcode)：**

智能体列表**严禁在前端代码中静态硬编码**，必须由后端的 LangGraph 编排引擎统一作为唯一信任源（SSOT）动态下发：

1. **后端注册中心发现端点 (`GET /astra/api/chat/agents`)**：
   - 后端基于 `src/agents/graph.py` 中的真实智能体编排注册表（`AGENT_REGISTRY`）统一定义并下发支持的 Sub-Agent 清单（包含 `id`, `name`, `description`, `icon`, `is_default`）；
   - 支持动态路由默认项 `auto`（由 Main Agent 自适应意图分类），以及专精子代理（`code_assistant` 代码助手、`deep_reasoner` 深度思考、`direct_chat` 直接对话等）。

2. **前端响应式消费与动态呈现**：
   - 前端 Store (`chatStore.ts`) 异步触发 `fetchAgents()`，在组件挂载时动态拉取注册智能体列表；
   - `AgentSelector.tsx` 浮层菜单完全基于接口下发数据动态渲染，图标与描述与后端 LangGraph 严格对齐；
   - 后续在后端扩充搜索、分析等新智能体时，前端零改动即可自动生效。

**LLM 模型动态发现机制 (全动态网关同步，严禁 Hardcode)：**

模型列表**严禁在前端代码中静态硬编码**，必须通过私有网关实时自动发现与动态装配：

1. **后端统一发现中继 (`GET /astra/api/chat/models`)**：
   - 后端 `LiteLLMClient` 使用 Virtual Key 调用私有网关接口 `GET {LITELLM_BASE_URL}/models`，杜绝密钥泄漏至浏览器；
   - 引入 Redis L1 缓存机制（缓存键 `cache:litellm:models`，TTL 300s），防止高并发穿透网关；
   - 自动解析模型名称前缀，智能映射提供商徽章（如 `gemini-*` ➔ Google，`kimi-*` ➔ Moonshot，`gpt-*` ➔ OpenAI，`claude-*` ➔ Anthropic）；
   - 根据应用配置 `APP_DEFAULT_MODEL` 自动注入 `is_default` 标记。

2. **前端响应式消费与动态呈现**：
   - 前端 Store (`chatStore.ts`) 异步触发 `fetchModels()`；
   - 模型选择胶囊实时基于网关在线清单动态渲染，自动适配 LiteLLM 挂载的实际模型（如 `gemini-3.8-flash`, `gemini-3.7-flash`, `kimi-k3`, `gpt-5.6-luna-a6` 等）；
   - 当运维在 LiteLLM 侧热上线或下架模型时，前端零改动、零构建，自动实时同步。

**选择器 UI 与全链路双向数据绑定设计：**

1. **四层数据双向绑定机制 (Four-Layer Two-Way Binding)**：
   - **会话级回显与绑定**：用户在侧边栏切换不同历史会话时，选择器自动从当前选中会话实体读取 `conversation.model` 与 `conversation.agent_preference` 进行动态回显；
   - **即时修改与持久化同步**：用户在当前会话中主动切换模型或智能体时，前端状态立刻响应，并自动调用 `PUT /conversations/{id}` 将最新选择实时持久化到后端 MySQL，刷新页面不丢失；
   - **全局偏好自动继承**：当点击“+ 新对话”开启全新空白对话时，选择器自动从用户个人资料 (`user.default_model`, `user.default_agent`) 中继承默认值，无需反复挑选；
   - **动态占位符联动与发送透传**：输入框占位提示语实时根据选择器动态联动：`向 [所选Agent] 提问，基于 [所选Model]... (Shift+Enter 换行)`；发送消息时，值自动组装进 `SendMessageRequest` 的 `model_override` 与 `agent_override` 字段中。

2. **高颜值悬浮浮层菜单交互 (Custom Popover Dropdown)**：
   - **摒弃系统原生 Select**：彻底废弃浏览器原生白框 `<select>`，改用具有 DeepSeek 质感的半透明微毛玻璃卡片（Popover）；
   - **信息多维呈现**：每个选项不仅展示名称，还清晰展示品牌彩色图标、提供商徽标标签（如 Google / Moonshot / OpenAI）与适用场景说明；
   - **当前选中态**：当前选中项以柔和主色高亮并附带右侧对勾（`Check`）图标，支持点击外部区域自动平滑收起。

**后端处理逻辑：**
```json
// 请求体示例
{
  "content": "帮我写个 Python 脚本",
  "conversation_id": "uuid",
  "agent_override": "code_assistant",      // 可选，强制指定 Agent
  "model_override": "gemini-3.8-flash",    // 可选，强制指定模型 (动态匹配网关)
  "stream": true
}
```

---

### 2.5 Session 管理设计

**Session 生命周期：**

| 阶段 | 说明 | 存储 |
|------|------|------|
| **创建** | Logto 认证成功后签发 JWT + Refresh Token | Redis + MySQL |
| **活跃** | 每次请求刷新 `last_active_at`，滑动过期 | Redis |
| **过期** | JWT 2 小时过期，Refresh Token 7 天过期 | 自动失效 |
| **注销** | 用户主动退出，加入 JWT 黑名单 | Redis 黑名单 |
| **强制下线** | 管理员或用户远程注销其他设备 | Redis 黑名单 |

**多设备会话管理：**

用户可在设置页查看当前所有活跃会话：

| 设备 | 浏览器 | IP | 最后活跃 | 操作 |
|------|--------|-----|----------|------|
| MacBook Pro | Chrome 128 | 113.108.x.x | 2 分钟前 | 当前设备 |
| iPhone 15 | Safari | 113.108.x.x | 3 小时前 | [下线] |
| Windows PC | Edge 128 | 61.144.x.x | 昨天 | [下线] |

**JWT 黑名单机制（Redis）：**
```
# Key: jwt:blacklist:{jti}
# Value: 1
# TTL: JWT 剩余有效期

# 检查是否黑名单
async def is_token_blacklisted(jti: str) -> bool:
    return await redis.exists(f"jwt:blacklist:{jti}")
```

**强制下线实现：**
```python
@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    user: User = Depends(get_current_user)
):
    # 1. 查询该会话的 JWT jti
    session = await get_session(session_id)
    if session.user_id != user.id:
        raise Forbidden()
    
    # 2. 加入黑名单
    await redis.setex(
        f"jwt:blacklist:{session.jti}",
        session.jwt_ttl_remaining,
        1
    )
    
    # 3. 删除会话记录
    await delete_session(session_id)
    
    return {"status": "revoked"}
```

---

### 2.6 多用户界面隔离设计

**核心原则**：用户登录后，界面仅展示当前用户的数据，无任何跨用户内容泄露。

| 界面模块 | 隔离实现 |
|----------|----------|
| **侧边栏会话列表** | 仅查询 `conversations WHERE user_id = current_user_id`，按 `updated_at` 倒序 |
| **对话窗口** | 加载 `messages WHERE conversation_id = ? AND user_id = current_user_id` |
| **用户头像/昵称** | 从 Logto 同步，本地 `users` 表存储，仅显示当前用户 |
| **记忆面板** | 展示 `long_term_memories WHERE user_id = current_user_id`，支持分类筛选 |
| **设置/偏好** | 读取 `users.preferences` JSON 字段，仅当前用户可修改 |
| **用量统计** | 展示 `agent_tasks` 聚合数据，仅当前用户可见 |
| **分享/导出** | 生成链接带 `user_id` 签名，过期时间 24h，仅创建者可撤销 |

**前端路由守卫：**
```typescript
// 所有受保护路由必须携带有效 JWT
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" />;
  return children;
};

// API 请求自动附加 Authorization Header
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('astra_jwt');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

**后端强制过滤：**
```python
# 所有数据库查询自动附加 user_id 条件
@router.get("/conversations")
async def list_conversations(
    user: User = Depends(get_current_user),  # JWT 解析
    db: Session = Depends(get_db)
):
    return db.query(Conversation).filter(
        Conversation.user_id == user.id  # 强制隔离
    ).order_by(Conversation.updated_at.desc()).all()
```

---

### 2.7 响应式全端适配与移动端体验设计 (Responsive Design & Mobile Optimization)

**核心设计目标**：确保 Astra 在桌面大屏（PC / Mac）、平板（iPad）及智能手机（iOS / Android）各种屏幕比例与输入方式下，均具备媲美原生 App 的极致流畅交互。

#### 1. 响应式断点与视口基准

| 设备级别 | 断点宽度 | 布局特征 | 交互重点 |
|---------|---------|---------|---------|
| **Mobile (移动端)** | `< 768px` (`sm`) | 单栏沉浸流，侧边栏收起至抽屉 | 手势滑动、单手大拇指热区、软键盘防抖 |
| **Tablet (平板端)** | `768px ~ 1023px` (`md`) | 窄边栏或悬浮可收起侧边栏 | 触摸与鼠标混合输入适配 |
| **Desktop (桌面端)** | `≥ 1024px` (`lg`/`xl`) | 经典三栏/两栏常驻工作台 | `Ctrl/Cmd + B` 快捷键折叠、多列宽幅排版 |

#### 2. 核心适配机制

* **侧边栏双态分流 (Desktop Sidebar vs Mobile Sheet Drawer)**：
  - **桌面端 (Desktop)**：固定在页面左侧（默认宽 260px），支持通过顶部图标或快捷键平滑收起展开；折叠后中央对话流平滑扩展至居中最大宽度（`max-w-3xl` / `max-w-4xl`）。
  - **移动端 (Mobile)**：侧边栏默认完全隐藏，顶部 Header 显示汉堡菜单图标；点击时以 **Sheet 抽屉** 形式从左侧滑出并叠加毛玻璃遮罩（Backdrop Blur），选中会话或点击遮罩边缘自动回弹收起。
* **移动端视口与软键盘防遮挡 (Dynamic Viewport Height & Keyboard Safe Area)**：
  - 采用现代 CSS 视口单位 `100dvh`（Dynamic Viewport Height），解决移动端 Safari/Chrome 浏览器顶部地址栏与底部工具栏展开/收起导致的滚动跳跃问题。
  - 结合 `window.visualViewport` API 动态计算移动端虚拟键盘弹出高度，确保底部输入坞（Chat Dock）始终紧密贴合在软键盘正上方，避免光标被遮挡或输入框被顶出可视区。
* **胶囊选择器 (Agent & Model) 小屏自适应**：
  - 桌面端：在输入框工具栏上方水平并列排列【智能体选择器】与【模型选择器】；
  - 移动端：启用隐藏滚动条的横向自由滑动容器（`flex overflow-x-auto no-scrollbar`），或在极小屏收敛为紧凑微型胶囊按钮，保证单手大拇指轻松点选。
* **Markdown、科学公式与代码块排版保护**：
  - **代码块**：手机端严禁挤压自动换行（破换缩进），统一包裹 `overflow-x-auto` 独立横向滚动，并在右上角使用 `sticky` 粘性固定一键复制按钮与语言标签。
  - **KaTeX 公式与 GFM 表格**：行间长公式与宽表格自动注入外层响应式容器，支持手势横向平滑拖动查看，严禁撑破主页面视口宽度。

---

### 2.8 动态 HTML 与交互沙箱体验设计 (Interactive HTML Artifacts)

**核心定位**：对标 Claude Artifacts 与 ChatGPT Canvas，当模型输出完整可执行的 HTML/JS/CSS（如游戏、交互数据图表、落地页原型、可视化小工具）时，前端自动将普通的 Markdown 代码块升格为可即时交互、操作的微应用卡片。

#### 1. 零信任安全隔离架构 (Zero-Trust iFrame Sandbox)

动态执行未知 LLM 代码必须死守金融级安全红线，严防 XSS 攻击与敏感凭证被窃：

```html
<iframe
  srcdoc={sanitizedHtml}
  sandbox="allow-scripts allow-modals"
  csp="default-src 'self' 'unsafe-inline' https: data:;"
  className="w-full h-full border-0 rounded-lg"
/>
```

- **安全边界铁律**：
  1. **严禁包含 `allow-same-origin`**：沙箱内部被浏览器强制置于无权限的 `null` 匿名源，沙箱内部 JS 绝对无法访问宿主页面的 `window.parent`、`document.cookie`、`localStorage`（JWT 凭证永不泄露）；
  2. **网络凭证隔离**：沙箱内任何 `fetch` / `XMLHttpRequest` 调用均无法附带主应用的 Authorization 头或 Cookie，阻断对受保护 API 的非法跨站调用；
  3. **交互放行**：保留 `allow-scripts` 允许运行 Canvas、DOM 事件与计算逻辑，保留 `allow-modals` 支持必要的 `alert` 调试。

#### 2. 双态工作台交互 (Code vs Preview)

- **标签页无缝切换**：
  - `[📄 源码 (Code)]`：带语法高亮、行号及语言标记的代码视图，支持编辑与一键复制；
  - `[▶️ 实时预览 (Preview)]`：零延迟实时挂载执行沙箱，所见即所得。
- **工具栏实用工具**：
  - **重置/刷新 (Reload)**：一键重新渲染沙箱 DOM，重置小游戏或动画的初始状态；
  - **全屏聚焦 (Fullscreen Modal)**：点击放大至全屏模态框，提供沉浸式体验；
  - **导出单文件 (Export)**：支持将当前 HTML/CSS/JS 源码一键下载为 `.html` 文件。
- **现代样式自动增强 (Smart Runtime Injections)**：
  - 在组装 `srcDoc` 时自动在 `<head>` 中轻量注入 Tailwind CSS Play CDN 及常用基础样式重置，确保模型生成的现代 UI 界面无需繁复配置即可开箱美观呈现。

---

### 2.9 流式打字机视觉输出与平滑缓冲体验设计 (Smooth Streaming Typewriter Design)

**核心设计目标**：杜绝网络高并发或 Token 极速涌入时的“视觉抽搐跳字”与“组件频繁重绘掉帧”，提供如丝般匀速顺滑、带有极客呼吸感的沉浸式打字机视觉呈现。

#### 1. 动态平滑缓冲插值引擎 (RAF Smooth Buffer Engine)

* **痛点问题**：
  当 LLM 高速吐字（如 `gemini-3.8-flash` 达 50~80 tokens/s）或网络传输由于 TCP 拥塞产生数据块堆积时，若来一个 chunk 就触发一次 `setState`，会导致 React 一秒内执行数十次全量虚拟 DOM 比对与 Markdown 解析，引起浏览器卡顿、风扇狂转且文字大段跳跃。
* **缓冲队列与自适应步长算法**：
  - 前端维持一个先进先出（FIFO）的字符待消费队列；
  - 核心渲染循环由浏览器的 `requestAnimationFrame`（16.6ms 刷新率）驱动；
  - **自适应出字步长（Dynamic Catch-up Step）**：
    - 队列积压字符 `< 20` 时：每次 RAF 帧输出 1~2 个字符，维持从容优雅的打字节奏；
    - 队列积压字符 `> 50` 时：动态提升步长至 3~6 个字符/帧，迅速平滑追赶进度，杜绝流式已结束界面还在漫长打字的迟滞感。
  - **性能收益**：单轮重度长文本流式输出期间，页面渲染帧率始终坚挺在 60 FPS，CPU 占用率控制在 5% 以内。

#### 2. 视觉动效与打字光标 (Blinking Pulse Cursor)

* **呼吸打字光标**：在流式生成中，最新文字末尾附带带有呼吸微弱发光动效的打字指示光标（`inline-block w-2 h-4 bg-primary animate-pulse`）；
* **自然淡出**：收到后端 `[DONE]` 结束标记或由于中止而定格时，光标平滑淡出，不留多余排版空隙。

#### 3. 智能视口跟随与用户脱钩滚动 (Smart Auto-Scroll & Scroll Detach)

* **吸底自动跟随**：当用户停留在对话流最底部时，随打字机流式生成，视口平滑向下自动滚动，保证最新一句话始终映入眼帘；
* **用户主动干预脱钩机制 (Scroll Detach)**：
  - 一旦检测到用户主动向上滚动滑轮或触摸向上翻阅历史消息，系统立即解除“强制自动吸底”，绝对不会粗暴将用户的视线拉回底部；
  - 界面右下角浮现优雅的悬浮轻提示按钮：`[ ↓ 回到最新内容 ]`，并附带未读更新呼吸点；
  - 用户点击按钮或重新手动滑至最底部时，自动恢复吸底跟随状态。

#### 4. 可中断流与前端快速截断 (Instant Stop Feedback)

* 在流式输出期间，输入框右下角发送按钮自动切换为带旋转指示器的红色 `[ ■ 停止生成 ]` 按钮；
* 点击停止时：
  1. 前端立即触发本地 `AbortController.abort()` 瞬间断开 SSE 长连接；
  2. 异步向后端 `POST /chat/stop` 触发分布式中止信号；
  3. 清空未消费的字符缓冲队列，打字光标立即定格，保全已收到的内容，整个流程零卡顿、无延时。

---

### 2.10 多功能模块导航与 RAG 知识库扩展设计 (Extensible Navigation & RAG Hub)

**核心设计目标**：超越单一的 Chat 界面，将 Astra 打造为可无限横向扩展的模块化 AI 工作台。界面预留清晰、直观的功能导航入口，第一期无缝承接已在后端建好表结构的 **RAG 向量知识库浏览与检索**，并为后续插件、微应用提供即插即用的路由与组件槽位。

#### 1. 侧边栏多模块功能中枢 (App Switcher & Navigation Rail)

* **模块化主入口分布**：
  侧边栏采用分组架构，顶部为核心功能切换，底部为历史对话与系统设置：
  1. 💬 **对话工作台 (Chat - `/`)**：核心多轮对话、流式推理与 Artifacts 预览；
  2. 📚 **RAG 知识库工坊 (Knowledge Base - `/knowledge`)**：
     - **文档资产浏览**：以卡片/列表形式展示当前用户上传的知识库文档（文件类型、文档名、切片数量、向量化状态、上传时间）；
     - **切片与向量探查器 (Chunk Inspector)**：点击文档即可展开抽屉/模态框，查看文档被分割出的每一个分片内容（Chunk Text）及其对应的 Embedding 维度信息；
     - **相似度检索实验室 (Retrieval Playground)**：提供快速提问测试框，输入任意 Query，实时展示基于 OCI MySQL HeatWave 向量检索召回的 Top-K 切片及其相似度得分（Score）；
  3. 🧩 **智能体广场 (Agent Hub - `/agents`)**：预留浏览、调试与自定义 Sub-Agent 提示词的微应用入口；
  4. ⚙️ **设置与设备管理 (Settings - `/settings`)**：多设备会话管理 (Sessions)、实时 Token 用量仪表盘、模型偏好设置。

#### 2. 对话流内的 RAG 知识库即时挂载 (In-Chat Context Attachment)

* 在主聊天界面的底部输入工具栏中，除了【Agent 选择器】与【Model 选择器】，预留第三个胶囊组件：**【知识库挂载徽章 (Knowledge Pinning)】**；
* 用户可在提问前快速勾选某个知识库，提问时携带 `knowledge_id`，触发后端的向量语义召回作为上下文注入 Prompt，实现真正的即点即查、知行合一。

#### 3. 插件化架构扩展性保障 (Code Cleanliness & Extensibility)

* **路由配置表驱动 (`routes.ts`)**：导航条目完全由静态配置数组生成，未来接入“数据分析看板”、“代码执行器”等新功能时，只需在配置文件注册页面组件与 Icon，侧边栏、快捷键与权限守卫自动就绪，遵循开闭原则（OCP）。

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
┌─────────────────────────┐       ┌─────────────────────────────────┐
│       Logto IdP         │       │   Kong Gateway (Forward-Auth)   │
│    sodaxw.logto.app     │◄─────►│      gw.jppwl.asia              │
│   Logto + GitHub 登录    │       │  · 前端: /astra/                 │
└─────────────────────────┘       │  · 后端: /astra/api              │
                                  │  · OAuth2-Proxy: /oauth2/*      │
                                  └─────────────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────────────┐
                                    │      Astra Backend      │
                                    │   (FastAPI + LangGraph) │
                                    │   /astra/api            │
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
| **UI 组件库** | shadcn/ui / Tailwind | latest | 高质量组件 |
| **样式方案** | Tailwind CSS | 3.x | 原子化 CSS |
| **Markdown 渲染** | react-markdown + remark-math + rehype-katex | latest | 完整 GFM + LaTeX |
| **代码高亮** | PrismJS | latest | 语法高亮 |
| **构建工具** | Vite | 6.x | 极速冷启动 |
| **后端框架** | FastAPI | 0.100+ | 异步高性能 |
| **Agent 框架** | LangGraph / LangChain | latest | 多 Agent 编排 |
| **LLM 接入** | LiteLLM (OpenAI 兼容) | - | 私有网关 |
| **数据库** | OCI MySQL HeatWave | 26.7.0-cloud | 关系 + 向量一体化 |
| **缓存** | Redis (K3s) | 7.2-alpine | 热点数据加速 |
| **ORM** | SQLAlchemy + asyncmy | 2.0+ | 异步 MySQL ORM |
| **认证** | Kong Forward-Auth + OAuth2-Proxy | latest | Logto + GitHub SSO，单点登录，安全注入身份头 |
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
    preferences JSON,           -- 用户偏好设置（默认模型、默认 Agent、主题等）
    default_model VARCHAR(64) DEFAULT 'deepseek-v4-flash',  -- 用户默认 LLM
    default_agent VARCHAR(64) DEFAULT 'auto',               -- 用户默认 Agent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户会话表（多设备登录追踪）
CREATE TABLE user_sessions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    jti VARCHAR(255) NOT NULL,              -- JWT ID，用于黑名单
    device_info VARCHAR(255),               -- 设备信息（User-Agent 解析）
    ip_address VARCHAR(45),                 -- 登录 IP
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,          -- JWT 过期时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_active (user_id, last_active_at DESC),
    INDEX idx_jti (jti)
);

-- 会话表
CREATE TABLE conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    title VARCHAR(255) DEFAULT '新对话',
    model VARCHAR(64),          -- 当前会话选择的 LLM 模型
    agent_preference VARCHAR(64), -- 当前会话选择的 Agent（auto/code/search/analysis/creative/general）
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
| **认证层** | Kong Forward-Auth (`oauth2-forward-auth`) + FastAPI `Depends(get_current_user)` | 自动校验 `_oauth2_proxy` Cookie，从注入的 `X-Auth-Request-*` 提取 `user_id` 与身份 |
| **API 路由** | 请求自动绑定网关注入身份 | 全接口依托依赖注入强隔离 |
| **数据库** | `user_id` 外键 + 行级隔离 | 所有表带 `user_id`，查询强制过滤 |
| **Redis** | Key 前缀 `user:{user_id}:*` | 短期记忆、会话缓存隔离 |
| **向量检索** | Metadata 过滤 | `user_id` 作为 metadata 强制过滤 |
| **Agent 上下文** | 每个请求独立 `AgentState` | 不共享全局状态，防止串话 |

### 6.2 Kong 网关层 Zero-Trust SSO 集成方案

系统完全复用集群既有的 **Kong Gateway + OAuth2-Proxy + Logto (GitHub OAuth)** 生产级单点登录架构，与 `LiteLLM UI`、`DbGate` 共享 `.jppwl.asia` 根域凭据，实现零信任与无感登录：

**认证流转全时序：**
```
浏览器访问 https://gw.jppwl.asia/astra/
    ↓
Kong Gateway (Lua 插件 oauth2-forward-auth 拦截)
    ↓
向内部 http://oauth2-proxy.default.svc:4180/oauth2/auth 发送鉴权探针
    ├─► [未认证 (401)] 页面导航: Kong 下发 302 重定向至 /oauth2/start?rd=/astra/
    │                   ↓
    │               Logto OIDC (https://sodaxw.logto.app/oidc)
    │                   ↓
    │               GitHub OAuth 授权
    │                   ↓
    │               /oauth2/callback 换票并写入 .jppwl.asia 根域 _oauth2_proxy Cookie
    │                   ↓
    │               自动跳回 /astra/ 页面完成无感登录
    │
    └─► [已认证 (202)] Kong 自动向下游 Pod 注入 X-Auth-Request-* 身份请求头：
                        · X-Auth-Request-User: Logto sub 唯一身份锚点
                        · X-Auth-Request-Email: 用户关联邮箱
                        · X-Auth-Request-Preferred-Username: GitHub 用户名
                        ↓
                    FastAPI 从注入头无感获取当前用户，完成 MySQL 用户表同步与行级隔离
```

**方案核心收益：**
- **前端零 Token 存储**：无需在 localStorage 存储敏感 JWT，彻底免疫 XSS 窃取令牌攻击；
- **跨微服务全站单点通用**：登录 LiteLLM UI 或 DbGate 后，打开 Astra 立即处于已登录态；
- **优雅登出**：前端或用户访问 `/oauth2/sign_out?rd=/astra/` 即可一键清除全站 `.jppwl.asia` Cookie 并安全登出。

**用户同步策略：**
- 首次访问时，后端自动通过 `UserRepository.get_or_create_by_sso` 在 MySQL 中创建或关联记录；
- `logto_id` 与 `username` 自动映射并持久化，保障会话与聊天记录与当前真实用户严格行级绑定。

### 6.3 安全红线

- 任何数据库查询、向量检索、Redis 操作，**必须**携带 `user_id` 条件
- 禁止任何跨用户的聚合查询（除非管理员权限）
- JWT 过期时间不宜过长（建议 2 小时），支持 Refresh Token 轮换
- 所有外部请求必须经 Cloudflare HTTPS，禁止裸 IP 访问
- **前端禁止渲染非当前用户的数据**，即使 API 返回异常也必须过滤
- **分享链接必须签名 + 过期**，防止未授权访问

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

### 7.2 节点部署规划

| 组件 | 部署节点 | 节点位置 | 架构 | 说明 |
|------|----------|----------|------|------|
| **Frontend** | `free-arm-vm` | OCI 新加坡 | ARM64 | 静态文件托管，Cloudflare CDN 回源 |
| **Backend** | `nuc` | 本地家宽 | AMD64 | FastAPI 服务，低延迟访问 MySQL |
| **Redis** | `oppo-termux` | 本地家宽 | ARM64 | OPPO 手机 Termux，边缘缓存节点 |
| **MySQL** | `rin-heatwave` | OCI 新加坡 | x86_64 | OCI HeatWave 托管，无需部署 |

**节点选择理由：**

- **Frontend → OCI free ARM VM**：静态资源托管，OCI 新加坡国际出口优质，Cloudflare CDN 回源延迟低；ARM64 架构与 OCI free tier 匹配，零成本。
- **Backend → NUC**：本地家宽 NUC 性能强劲（AMD64），直连 OCI MySQL 新加坡延迟稳定（~50ms），且便于本地调试。
- **Redis → OPPO Termux**：OPPO 手机 ARM64 架构，Termux 环境轻量运行 Redis，作为边缘缓存节点；家宽内网直连 Backend（NUC），延迟 <1ms；利用闲置设备，零额外成本。

**网络拓扑：**

```
用户浏览器
    ↓ HTTPS
Cloudflare Edge CDN (gw.jppwl.asia)
    ↓ 回源至 Kong Ingress
Kong Gateway (路径分流)
    ├── /astra/    → Frontend (Nginx SPA)
    └── /astra/api → Backend (FastAPI)
    ↓ 缓存读写
Backend → Tailscale Redis (100.105.130.0:6379, <5ms)
    ↓ 持久化
Backend → OCI MySQL HeatWave (161.118.240.218:3306, <50ms)
```

**K8s Node Selector 配置：**

```yaml
# Frontend Deployment
nodeSelector:
  kubernetes.io/hostname: free-arm-vm
  kubernetes.io/arch: arm64

# Backend Deployment
nodeSelector:
  kubernetes.io/hostname: nuc
  kubernetes.io/arch: amd64

# Redis 不走 K8s，独立部署在 OPPO Termux
# 通过 Tailscale 或家宽内网直连
```

**OPPO Termux Redis 配置要点：**

```bash
# OPPO 手机 Termux 安装 Redis
pkg install redis

# 启动 Redis（绑定 Tailscale IP 或家宽内网 IP）
redis-server --bind 100.x.x.x --port 6379 --requirepass <YOUR_REDIS_PASSWORD>

# 或配置持久化
redis-server --appendonly yes --appendfsync everysec
```

**Backend 连接 Redis 配置：**

```python
# 优先连接 OPPO Termux Redis（家宽内网）
REDIS_URL = "redis://:<YOUR_REDIS_PASSWORD>@100.x.x.x:6379/0"  # Tailscale IP

# 降级策略：OPPO Redis 不可用 → 直连 MySQL（容忍穿透）
```

---

### 7.3 ArgoCD Application

**Frontend Application（部署到 OCI free ARM VM）：**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: astra-frontend
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/nvd11/astra
    targetRevision: main
    path: k8s/frontend
  destination:
    server: https://kubernetes.default.svc
    namespace: astra
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

**Backend Application（部署到 NUC）：**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: astra-backend
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/nvd11/astra
    targetRevision: main
    path: k8s/backend
  destination:
    server: https://kubernetes.default.svc
    namespace: astra
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

**K8s Manifest 目录结构：**

```
k8s/
├── frontend/
│   ├── deployment.yaml      # nodeSelector: free-arm-vm, arm64
│   ├── service.yaml         # ClusterIP
│   └── httproute.yaml       # Kong: gw.jppwl.asia/astra/ → frontend:80
├── backend/
│   ├── deployment.yaml      # nodeSelector: free-arm-vm, arm64
│   ├── service.yaml         # ClusterIP
│   ├── httproute.yaml       # Kong: gw.jppwl.asia/astra/api → backend:8000
│   ├── secret.yaml          # DATABASE_URL, REDIS_URL, LITELLM_API_KEY
│   └── configmap.yaml       # LITELLM_BASE_URL, ENVIRONMENT, LOGTO_ENDPOINT
└── argocd/
    ├── astra-frontend-app.yaml # ArgoCD Application for frontend (generic-web-service-v2)
    └── astra-backend-app.yaml  # ArgoCD Application for backend (generic-web-service-v2)
```

### 7.4 环境变量

| 变量 | 说明 | 存储 |
|------|------|------|
| `DATABASE_URL` | OCI MySQL 连接串 | K8s Secret |
| `REDIS_URL` | Redis 连接串 | K8s Secret |
| `LITELLM_API_KEY` | LiteLLM 网关密钥 | K8s Secret |
| `LITELLM_BASE_URL` | LiteLLM 网关地址 (`https://gw.jppwl.asia/litellm/v1`) | K8s ConfigMap |
| `JWT_SECRET` | （可选开发回退）：标准 OIDC/Cloudflare 模式直接基于 JWKS 公钥验签，无需此密钥 | K8s Secret（仅自签模式） |
| `LOGTO_ENDPOINT` | Logto SSO 端点（`https://auth.jppwl.asia`） | K8s ConfigMap |
| `LOGTO_APP_ID` | Logto 应用 ID | K8s Secret |
| `LOGTO_APP_SECRET` | Logto 应用密钥 | K8s Secret |
| `LOGTO_REDIRECT_URI` | 回调地址（`https://gw.jppwl.asia/astra/callback`） | K8s ConfigMap |
| `ENVIRONMENT` | 环境标识（dev/staging/prod） | K8s ConfigMap |

### 7.5 Cloudflare DNS 与生产网关配置

统一接入生产网关 `gw.jppwl.asia`（Proxied）：

| 域名与路径 | 目标服务 | 说明 |
|----------|---------|------|
| `https://gw.jppwl.asia/astra/` | `astra-frontend:80` | 前端 SPA UI 入口（带 Nginx 历史路由保护） |
| `https://gw.jppwl.asia/astra/api` | `astra-backend:8000` | 后端 API 入口（带 strip-path 转发至 FastAPI 根路径） |
| `https://gw.jppwl.asia/litellm/v1` | `litellm-svc:4000` | 私有 LLM 网关接口 |

**Kong HTTPRoute 配置要点：**
- `gw.jppwl.asia/astra/` → 前端 Service（静态文件）
- `gw.jppwl.asia/astra/api` → 后端 Service（FastAPI）
- CORS 严格配置（允许 `https://gw.jppwl.asia` 及本地调试端口 `3000`/`5173`）

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
