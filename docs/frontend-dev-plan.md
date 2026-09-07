# Astra 前端开发计划文档

> **项目代号**：Astra  
> **文档版本**：v1.0  
> **创建日期**：2026-09-06  
> **作者**：Leona  
> **状态**：开发规划确认中  

---

## 1. 项目概述

本文档基于 `requirements.md` 第 2.1 节前端功能需求与第 7.1 节 Monorepo 结构，为 Astra 项目前端提供**逐文件、逐函数/组件级别**的开发计划。技术栈为 **React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Zustand + React Router + Axios + react-markdown + remark-gfm + rehype-katex + react-syntax-highlighter**。

### 1.1 响应式全端设计与断点规范 (Mobile & Desktop)

Astra 前端采用全端流体响应式架构，严格对标 DeepSeek Web 沉浸式交互：

1. **设备断点与布局形态**：
   - **移动端 (`< 768px / sm`)**：单栏极简对话流，侧边栏收起至由汉堡菜单触发的抽屉浮层（Drawer Sheet）；
   - **平板端 (`768px ~ 1023px / md`)**：弹性侧边栏，支持手势轻扫呼出；
   - **桌面端 (`≥ 1024px / lg`)**：经典三栏/两栏工作台，左侧固定 260px 侧边栏，支持快捷键 `Ctrl/Cmd + B` 丝滑折叠展开。
2. **移动端视口与软键盘保护**：
   - 全局高度基准采用现代 CSS `100dvh`，杜绝 iOS Safari / Android Chrome 动态地址栏缩放抖动；
   - 挂载 `useVirtualKeyboard` Hook 监听 `window.visualViewport` 变化，软键盘弹起时输入框无缝悬浮吸顶于键盘上沿，防止光标溢出可视区。
3. **内容组件小屏保护**：
   - 代码块与数学公式一律包裹 `overflow-x-auto` 独立横向滚动条，代码块右上角复制按钮与语言标签保持 `sticky` 粘性固定；
   - Agent & LLM 胶囊选择器小屏下采用隐藏滚动条的横向自由滑动容器，便于大拇指单手触达。

### 1.2 动态 HTML 交互沙箱设计 (Interactive Artifacts)

1. **安全沙箱隔离**：
   - 采用原生 `iframe` 结合 `sandbox="allow-scripts allow-modals"` 属性执行 LLM 生成的 HTML/JS/CSS，**严禁使用 `allow-same-origin`**，杜绝 XSS 攻击并彻底杜绝访问宿主域 Token、Cookies 或 LocalStorage；
2. **双态工作台组件 (`HtmlArtifactViewer.tsx`)**：
   - 自动识别 Markdown 渲染中的 `html` 独立代码块，升级为可交互式 Artifact 卡片；
   - 提供 `[代码 (Code)]` 与 `[预览 (Preview)]` 双选项卡自由切换；
   - 顶部工具栏集成“一键复制代码”、“重置刷新”、“全屏弹窗预览”与“导出单文件 HTML”功能；
   - 自动在沙箱文档头部注入 Tailwind CSS 运行时与重置样式，开箱呈现高颜值界面。

---

## 2. 目录结构总览

```
frontend/
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
├── index.html
├── Dockerfile
├── .env.development
├── .env.production
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── vite-env.d.ts
│   ├── config/
│   │   ├── env.ts
│   │   └── routes.ts
│   ├── types/
│   │   ├── index.ts
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   ├── conversation.ts
│   │   ├── message.ts
│   │   ├── agent.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── cn.ts
│   │   ├── format.ts
│   │   ├── storage.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── chat.ts
│   │   ├── conversations.ts
│   │   ├── messages.ts
│   │   ├── users.ts
│   │   └── sessions.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── chatStore.ts
│   │   ├── conversationStore.ts
│   │   ├── userStore.ts
│   │   └── settingsStore.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useChat.ts
│   │   ├── useConversations.ts
│   │   ├── useMessages.ts
│   │   ├── useTheme.ts
│   │   ├── useLocalStorage.ts
│   │   ├── useMediaQuery.ts
│   │   ├── useVirtualKeyboard.ts
│   │   └── useSSE.ts
│   ├── components/
│   │   ├── common/
│   │   │   ├── Loading.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   └── Toast.tsx
│   │   ├── layout/
│   │   │   ├── MainLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── MobileNavDrawer.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   └── chat/
│   │       ├── MarkdownRenderer.tsx
│   │       ├── HtmlArtifactViewer.tsx
│   │       ├── MessageList.tsx
│   │       ├── MessageItem.tsx
│   │       ├── ChatInput.tsx
│   │       ├── AgentSelector.tsx
│   │       ├── ModelSelector.tsx
│   │       ├── ConversationList.tsx
│   │       └── ConversationItem.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── SettingsPage.tsx
│   │   ├── ProfilePage.tsx
│   │   └── NotFoundPage.tsx
│   └── styles/
│       └── globals.css
```

---

## 3. 项目初始化与配置文件

### 3.1 `frontend/package.json`

**功能描述**：项目依赖与脚本配置。

**核心内容**：
```json
{
  "name": "astra-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "zustand": "^4.4.7",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0",
    "rehype-katex": "^7.0.0",
    "react-syntax-highlighter": "^15.5.0",
    "katex": "^0.16.9",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0",
    "class-variance-authority": "^0.7.0",
    "lucide-react": "^0.294.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-avatar": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@radix-ui/react-scroll-area": "^1.0.5",
    "@radix-ui/react-separator": "^1.0.3",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-label": "^2.0.2",
    "sonner": "^1.2.4",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@types/react-syntax-highlighter": "^15.5.11",
    "@types/node": "^20.10.4",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5"
  }
}
```

---

### 3.2 `frontend/vite.config.ts`

**功能描述**：Vite 构建配置，包括路径别名、代理、环境变量注入。

**核心函数/配置**：

```typescript
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: mode === 'development',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            markdown: ['react-markdown', 'remark-gfm', 'rehype-katex', 'react-syntax-highlighter'],
          },
        },
      },
    },
    define: {
      __APP_ENV__: JSON.stringify(env.VITE_APP_ENV),
    },
  };
});
```

**配置说明**：
- `resolve.alias`：配置 `@` 指向 `src` 目录
- `server.proxy`：开发环境代理 `/api` 到后端
- `build.rollupOptions.output.manualChunks`：代码分割优化
- `define`：注入全局环境变量

---

### 3.3 `frontend/tailwind.config.js`

**功能描述**：Tailwind CSS 配置，支持 shadcn/ui 主题系统。

**核心配置**：

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

---

### 3.4 `frontend/tsconfig.json`

**功能描述**：TypeScript 主配置。

**核心配置**：

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

### 3.5 `frontend/tsconfig.node.json`

**功能描述**：TypeScript Node 环境配置（用于 Vite 配置文件）。

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

---

### 3.6 `frontend/index.html`

**功能描述**：HTML 入口文件。

**核心内容**：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Astra - Modern LLM Chat Application" />
    <title>Astra</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

### 3.7 `frontend/.env.development`

**功能描述**：开发环境变量。

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=development
VITE_LOGTO_ENDPOINT=https://auth.jppwl.asia
VITE_LOGTO_APP_ID=dev-app-id
VITE_LOGTO_REDIRECT_URI=http://localhost:5173/callback
```

---

### 3.8 `frontend/.env.production`

**功能描述**：生产环境变量。

```bash
VITE_API_BASE_URL=https://api.astra.jppwl.asia
VITE_APP_ENV=production
VITE_LOGTO_ENDPOINT=https://auth.jppwl.asia
VITE_LOGTO_APP_ID=prod-app-id
VITE_LOGTO_REDIRECT_URI=https://astra.jppwl.asia/callback
```

---

### 3.9 `frontend/src/config/env.ts`

**功能描述**：环境变量类型安全封装。

**核心函数/常量**：

```typescript
interface EnvConfig {
  apiBaseUrl: string;
  appEnv: 'development' | 'staging' | 'production';
  logto: {
    endpoint: string;
    appId: string;
    redirectUri: string;
  };
}

function getEnvVar(key: string, defaultValue?: string): string {
  const value = import.meta.env[key] || defaultValue;
  if (value === undefined) {
    throw new Error(`Missing environment variable: ${key}`);
  }
  return value;
}

export const env: EnvConfig = {
  apiBaseUrl: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000'),
  appEnv: (getEnvVar('VITE_APP_ENV', 'development') as EnvConfig['appEnv']),
  logto: {
    endpoint: getEnvVar('VITE_LOGTO_ENDPOINT'),
    appId: getEnvVar('VITE_LOGTO_APP_ID'),
    redirectUri: getEnvVar('VITE_LOGTO_REDIRECT_URI'),
  },
};

export const isDev = env.appEnv === 'development';
export const isProd = env.appEnv === 'production';
```

**函数说明**：
- `getEnvVar(key: string, defaultValue?: string): string`：安全读取环境变量，缺失时抛出错误或返回默认值
- `env: EnvConfig`：全局环境配置对象，包含 API 地址、Logto 配置等
- `isDev / isProd`：环境判断快捷常量

---

### 3.10 `frontend/src/vite-env.d.ts`

**功能描述**：Vite 环境变量类型声明。

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_ENV: 'development' | 'staging' | 'production';
  readonly VITE_LOGTO_ENDPOINT: string;
  readonly VITE_LOGTO_APP_ID: string;
  readonly VITE_LOGTO_REDIRECT_URI: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

## 4. 类型定义（`src/types/*.ts`）

### 4.1 `frontend/src/types/index.ts`

**功能描述**：类型定义统一导出。

```typescript
export * from './auth';
export * from './user';
export * from './conversation';
export * from './message';
export * from './agent';
export * from './api';
```

---

### 4.2 `frontend/src/types/auth.ts`

**功能描述**：认证相关类型定义。

**核心类型**：

```typescript
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface LogtoCallbackRequest {
  code: string;
  state?: string;
}

export interface LogtoUserInfo {
  sub: string;
  username?: string;
  email?: string;
  avatar?: string;
}

export interface JwtPayload {
  sub: string;
  exp: number;
  iat: number;
  jti: string;
  type: 'access' | 'refresh';
}
```

---

### 4.3 `frontend/src/types/user.ts`

**功能描述**：用户相关类型定义。

```typescript
export interface UserProfile {
  id: string;
  username: string;
  email?: string;
  avatar_url?: string;
  preferences?: UserPreferences;
  default_model: string;
  default_agent: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: 'zh-CN' | 'en-US';
  font_size: 'small' | 'medium' | 'large';
  send_shortcut: 'enter' | 'ctrl_enter';
  enable_streaming: boolean;
  enable_sound: boolean;
}

export interface UserSession {
  id: string;
  user_id: string;
  device_info: string;
  ip_address: string;
  last_active_at: string;
  expires_at: string;
  created_at: string;
  is_current: boolean;
}

export interface UpdateProfileRequest {
  username?: string;
  avatar_url?: string;
  preferences?: Partial<UserPreferences>;
  default_model?: string;
  default_agent?: string;
}

export interface UsageStats {
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  this_month_tokens: number;
  favorite_model: string;
  favorite_agent: string;
}
```

---

### 4.4 `frontend/src/types/conversation.ts`

**功能描述**：会话相关类型定义。

```typescript
export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  model?: string;
  agent_preference?: AgentType;
  system_prompt?: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message_preview?: string;
}

export interface CreateConversationRequest {
  title?: string;
  model?: string;
  agent_preference?: AgentType;
  system_prompt?: string;
}

export interface UpdateConversationRequest {
  title?: string;
  model?: string;
  agent_preference?: AgentType;
  system_prompt?: string;
  is_archived?: boolean;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  total: number;
  page: number;
  page_size: number;
}

export type AgentType = 'auto' | 'code' | 'search' | 'analysis' | 'creative' | 'general';
```

---

### 4.5 `frontend/src/types/message.ts`

**功能描述**：消息相关类型定义。

```typescript
export interface Message {
  id: string;
  conversation_id: string;
  user_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  metadata?: MessageMetadata;
  tokens_used?: number;
  created_at: string;
}

export interface MessageMetadata {
  agent_name?: string;
  model?: string;
  tool_calls?: ToolCall[];
  citations?: Citation[];
  thinking?: string;
  error?: string;
}

export interface ToolCall {
  id: string;
  type: string;
  function: {
    name: string;
    arguments: string;
  };
}

export interface Citation {
  id: number;
  title: string;
  url: string;
  snippet: string;
}

export interface SendMessageRequest {
  conversation_id: string;
  content: string;
  agent_override?: AgentType;
  model_override?: string;
  stream?: boolean;
}

export interface MessageListResponse {
  messages: Message[];
  total: number;
  has_more: boolean;
}
```

---

### 4.6 `frontend/src/types/agent.ts`

**功能描述**：Agent 相关类型定义。

```typescript
export interface AgentInfo {
  id: string;
  name: string;
  display_name: string;
  description: string;
  icon: string;
  color: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description: string;
  max_tokens: number;
  supports_streaming: boolean;
  supports_vision: boolean;
}

export interface AgentTask {
  id: string;
  conversation_id: string;
  user_id: string;
  agent_name: string;
  input_text: string;
  output_text?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  execution_time_ms?: number;
  created_at: string;
}

export const AGENTS: AgentInfo[] = [
  { id: 'auto', name: 'auto', display_name: '自动路由', description: 'Main Agent 自动识别意图并分发', icon: 'Sparkles', color: 'text-purple-500' },
  { id: 'code', name: 'code_agent', display_name: '代码助手', description: '代码生成、审查、调试、解释', icon: 'Code', color: 'text-blue-500' },
  { id: 'search', name: 'search_agent', display_name: '搜索增强', description: '网络搜索、文档检索、实时信息', icon: 'Search', color: 'text-green-500' },
  { id: 'analysis', name: 'analysis_agent', display_name: '数据分析', description: '数据分析、图表生成、统计计算', icon: 'BarChart', color: 'text-orange-500' },
  { id: 'creative', name: 'creative_agent', display_name: '创意写作', description: '文案创作、头脑风暴、内容优化', icon: 'PenTool', color: 'text-pink-500' },
  { id: 'general', name: 'general_agent', display_name: '通用对话', description: '兜底通用对话', icon: 'MessageSquare', color: 'text-gray-500' },
];

export const MODELS: ModelInfo[] = [
  { id: 'deepseek-v4-flash', name: 'DeepSeek V4 Flash', provider: 'DeepSeek', description: '速度快，成本低', max_tokens: 8192, supports_streaming: true, supports_vision: false },
  { id: 'gemini-3.8-flash', name: 'Gemini 3.8 Flash', provider: 'Google', description: '多模态强，推理好', max_tokens: 8192, supports_streaming: true, supports_vision: true },
  { id: 'claude-sonnet-4-6', name: 'Claude Sonnet 4.6', provider: 'Anthropic', description: '长文本强，逻辑严谨', max_tokens: 200000, supports_streaming: true, supports_vision: true },
  { id: 'qwen-max', name: 'Qwen Max', provider: '阿里', description: '中文优化，知识丰富', max_tokens: 8192, supports_streaming: true, supports_vision: false },
];
```

---

### 4.7 `frontend/src/types/api.ts`

**功能描述**：API 通用类型定义。

```typescript
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

export interface ApiError {
  code: number;
  message: string;
  detail?: string;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginationResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface StreamChunk {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: StreamChoice[];
}

export interface StreamChoice {
  index: number;
  delta: {
    role?: string;
    content?: string;
  };
  finish_reason?: string;
}
```

---

## 5. 工具函数（`src/utils/*.ts`）

### 5.1 `frontend/src/utils/cn.ts`

**功能描述**：Tailwind CSS 类名合并工具（shadcn/ui 标准）。

```typescript
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**函数说明**：
- `cn(...inputs: ClassValue[]): string`：合并多个类名，自动处理 Tailwind 冲突

---

### 5.2 `frontend/src/utils/format.ts`

**功能描述**：格式化工具函数。

**核心函数**：

```typescript
import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { zhCN } from 'date-fns/locale';

export function formatDate(date: string | Date, formatStr: string = 'yyyy-MM-dd HH:mm:ss'): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, formatStr);
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true, locale: zhCN });
}

export function formatTokens(tokens: number): string {
  if (tokens >= 1000000) {
    return `${(tokens / 1000000).toFixed(1)}M`;
  }
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(1)}K`;
  }
  return tokens.toString();
}

export function truncateText(text: string, maxLength: number = 50): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

export function parseUserAgent(userAgent: string): { device: string; browser: string } {
  const isMobile = /Mobile|Android|iPhone/i.test(userAgent);
  const device = isMobile ? 'Mobile' : 'Desktop';

  let browser = 'Unknown';
  if (userAgent.includes('Chrome')) browser = 'Chrome';
  else if (userAgent.includes('Safari')) browser = 'Safari';
  else if (userAgent.includes('Firefox')) browser = 'Firefox';
  else if (userAgent.includes('Edge')) browser = 'Edge';

  return { device, browser };
}
```

**函数说明**：
- `formatDate(date, formatStr)`：格式化日期为指定格式字符串
- `formatRelativeTime(date)`：格式化为相对时间（如"3 小时前"）
- `formatTokens(tokens)`：格式化 token 数量为 K/M 单位
- `truncateText(text, maxLength)`：截断文本并添加省略号
- `generateId()`：生成随机 ID
- `parseUserAgent(userAgent)`：解析 User-Agent 字符串为设备和浏览器信息

---

### 5.3 `frontend/src/utils/storage.ts`

**功能描述**：本地存储封装（带类型安全和过期时间）。

**核心函数**：

```typescript
const PREFIX = 'astra_';

interface StorageItem<T> {
  value: T;
  expires_at?: number;
}

export function setItem<T>(key: string, value: T, ttlSeconds?: number): void {
  const item: StorageItem<T> = {
    value,
    expires_at: ttlSeconds ? Date.now() + ttlSeconds * 1000 : undefined,
  };
  localStorage.setItem(PREFIX + key, JSON.stringify(item));
}

export function getItem<T>(key: string): T | null {
  const raw = localStorage.getItem(PREFIX + key);
  if (!raw) return null;

  try {
    const item: StorageItem<T> = JSON.parse(raw);
    if (item.expires_at && Date.now() > item.expires_at) {
      localStorage.removeItem(PREFIX + key);
      return null;
    }
    return item.value;
  } catch {
    return null;
  }
}

export function removeItem(key: string): void {
  localStorage.removeItem(PREFIX + key);
}

export function clear(): void {
  Object.keys(localStorage)
    .filter(key => key.startsWith(PREFIX))
    .forEach(key => localStorage.removeItem(key));
}

export const STORAGE_KEYS = {
  JWT: 'jwt',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  THEME: 'theme',
  SELECTED_AGENT: 'selected_agent',
  SELECTED_MODEL: 'selected_model',
} as const;
```

**函数说明**：
- `setItem<T>(key, value, ttlSeconds?)`：存储数据到 localStorage，支持过期时间
- `getItem<T>(key)`：读取数据，自动检查过期并清理
- `removeItem(key)`：删除指定键
- `clear()`：清空所有带前缀的存储
- `STORAGE_KEYS`：预定义存储键名常量

---

### 5.4 `frontend/src/utils/validators.ts`

**功能描述**：表单验证工具函数。

```typescript
export function isValidEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

export function isValidUsername(username: string): boolean {
  return username.length >= 2 && username.length <= 64;
}

export function isValidPassword(password: string): boolean {
  return password.length >= 8;
}

export function validateRequired(value: string, fieldName: string): string | null {
  if (!value || value.trim() === '') {
    return `${fieldName}不能为空`;
  }
  return null;
}

export function validateMaxLength(value: string, maxLength: number, fieldName: string): string | null {
  if (value.length > maxLength) {
    return `${fieldName}不能超过${maxLength}个字符`;
  }
  return null;
}
```

---

### 5.5 `frontend/src/utils/constants.ts`

**功能描述**：全局常量定义。

```typescript
export const APP_NAME = 'Astra';
export const APP_VERSION = '0.1.0';

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    LOGTO_CALLBACK: '/api/v1/auth/logto/callback',
    LOGTO_LOGIN: '/api/v1/auth/logto/login',
  },
  USERS: {
    PROFILE: '/api/v1/users/me',
    UPDATE_PROFILE: '/api/v1/users/me',
    USAGE_STATS: '/api/v1/users/me/stats',
    SESSIONS: '/api/v1/users/me/sessions',
  },
  CONVERSATIONS: {
    LIST: '/api/v1/conversations',
    CREATE: '/api/v1/conversations',
    GET: (id: string) => `/api/v1/conversations/${id}`,
    UPDATE: (id: string) => `/api/v1/conversations/${id}`,
    DELETE: (id: string) => `/api/v1/conversations/${id}`,
    ARCHIVE: (id: string) => `/api/v1/conversations/${id}/archive`,
  },
  MESSAGES: {
    LIST: (conversationId: string) => `/api/v1/conversations/${conversationId}/messages`,
    CREATE: (conversationId: string) => `/api/v1/conversations/${conversationId}/messages`,
    DELETE: (id: string) => `/api/v1/messages/${id}`,
    REGENERATE: (id: string) => `/api/v1/messages/${id}/regenerate`,
  },
  CHAT: {
    COMPLETION: '/api/v1/chat/completions',
    STREAM: '/api/v1/chat/stream',
  },
  SESSIONS: {
    LIST: '/api/v1/sessions',
    REVOKE: (id: string) => `/api/v1/sessions/${id}/revoke`,
  },
} as const;

export const SSE_EVENTS = {
  MESSAGE: 'message',
  ERROR: 'error',
  DONE: 'done',
  HEARTBEAT: 'heartbeat',
} as const;

export const MAX_MESSAGE_LENGTH = 4000;
export const MAX_CONVERSATION_TITLE_LENGTH = 255;
export const DEFAULT_PAGE_SIZE = 20;
```

---
## 6. API 服务层（`src/services/*.ts`）

### 6.1 `frontend/src/services/api.ts`

**功能描述**：Axios 实例配置、请求/响应拦截器、JWT 自动刷新。

**核心代码**：

```typescript
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { env } from '@/config/env';
import { getItem, setItem, removeItem, STORAGE_KEYS } from '@/utils/storage';
import { RefreshTokenResponse } from '@/types';

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

export const api: AxiosInstance = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getItem<string>(STORAGE_KEYS.JWT);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getItem<string>(STORAGE_KEYS.REFRESH_TOKEN);
      if (!refreshToken) {
        removeItem(STORAGE_KEYS.JWT);
        removeItem(STORAGE_KEYS.USER);
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post<RefreshTokenResponse>(
          `${env.apiBaseUrl}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token: newRefreshToken } = response.data;
        setItem(STORAGE_KEYS.JWT, access_token);
        setItem(STORAGE_KEYS.REFRESH_TOKEN, newRefreshToken);

        processQueue(null, access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        removeItem(STORAGE_KEYS.JWT);
        removeItem(STORAGE_KEYS.REFRESH_TOKEN);
        removeItem(STORAGE_KEYS.USER);
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

**核心逻辑说明**：
- `api: AxiosInstance`：全局 Axios 实例，配置 baseURL 和超时
- 请求拦截器：自动从 localStorage 读取 JWT 并附加到 Authorization Header
- 响应拦截器：捕获 401 错误，自动使用 Refresh Token 刷新 Access Token
- `isRefreshing` 标志 + `failedQueue` 队列：防止并发请求时重复刷新 Token
- 刷新失败时清除本地凭证并跳转登录页
- **Cloudflare 同域 Zero Trust / 后端 Auth 开关适配**：
  - 当项目以后端 `APP_AUTH_MODE=cloudflare`（如部署在 `astra.jppwl.asia` 同域）部署时，Cloudflare Edge 自动注入 `CF-Access-Jwt-Assertion` 头，**前端无需在请求拦截器中手动携带 Bearer Token**，且在没有本地 JWT 时不强制重定向至 `/login`，直接复用 Cloudflare Access 提供的企业级单点登录；
  - 当后端 `APP_AUTH_ENABLED=false`（本地离线研发或内网测试）时，后端自动注入默认匿名用户身份，前端所有 API 调用免登录直接放行。

---

### 6.2 `frontend/src/services/auth.ts`

**功能描述**：认证相关 API 服务。

**核心函数**：

```typescript
import api from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import { LoginRequest, LoginResponse, LogtoCallbackRequest, UserProfile } from '@/types';

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, data);
  return response.data;
}

export async function logout(): Promise<void> {
  await api.post(API_ENDPOINTS.AUTH.LOGOUT);
}

export async function logtoLogin(): Promise<{ redirect_url: string }> {
  const response = await api.get<{ redirect_url: string }>(API_ENDPOINTS.AUTH.LOGTO_LOGIN);
  return response.data;
}

export async function logtoCallback(data: LogtoCallbackRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>(API_ENDPOINTS.AUTH.LOGTO_CALLBACK, data);
  return response.data;
}

export async function getCurrentUser(): Promise<UserProfile> {
  const response = await api.get<UserProfile>(API_ENDPOINTS.USERS.PROFILE);
  return response.data;
}
```

**函数说明**：
- `login(data)`：用户名密码登录
- `logout()`：退出登录，后端将 JWT 加入黑名单
- `logtoLogin()`：获取 Logto SSO 登录跳转 URL
- `logtoCallback(data)`：Logto 回调处理，用 code 换取 JWT
- `getCurrentUser()`：获取当前登录用户信息

---

### 6.3 `frontend/src/services/chat.ts`

**功能描述**：聊天相关 API 服务，包括 SSE 流式请求。

**核心函数**：

```typescript
import api from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import { SendMessageRequest, Message, StreamChunk } from '@/types';
import { getItem, STORAGE_KEYS } from '@/utils/storage';

export async function sendMessage(data: SendMessageRequest): Promise<Message> {
  const response = await api.post<Message>(API_ENDPOINTS.CHAT.COMPLETION, data);
  return response.data;
}

export function streamMessage(
  data: SendMessageRequest,
  callbacks: {
    onChunk: (chunk: StreamChunk) => void;
    onDone: () => void;
    onError: (error: Error) => void;
  }
): () => void {
  const token = getItem<string>(STORAGE_KEYS.JWT);
  const url = `${import.meta.env.VITE_API_BASE_URL}${API_ENDPOINTS.CHAT.STREAM}`;

  const controller = new AbortController();

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ ...data, stream: true }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          callbacks.onDone();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              callbacks.onDone();
              return;
            }
            try {
              const chunk: StreamChunk = JSON.parse(data);
              callbacks.onChunk(chunk);
            } catch (e) {
              console.error('Failed to parse SSE chunk:', e);
            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        callbacks.onError(error);
      }
    });

  return () => {
    controller.abort();
  };
}

export async function regenerateMessage(messageId: string): Promise<Message> {
  const response = await api.post<Message>(API_ENDPOINTS.MESSAGES.REGENERATE(messageId));
  return response.data;
}
```

**函数说明**：
- `sendMessage(data)`：发送非流式消息
- `streamMessage(data, callbacks)`：发送流式消息，使用 fetch + ReadableStream 处理 SSE
  - `onChunk`：收到流式数据块时回调
  - `onDone`：流式传输完成时回调
  - `onError`：发生错误时回调
  - 返回取消函数，用于中断流式传输
- `regenerateMessage(messageId)`：重新生成指定消息

---

### 6.4 `frontend/src/services/conversations.ts`

**功能描述**：会话管理 API 服务。

```typescript
import api from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import {
  Conversation,
  CreateConversationRequest,
  UpdateConversationRequest,
  ConversationListResponse,
  PaginationParams,
} from '@/types';

export async function getConversations(params?: PaginationParams): Promise<ConversationListResponse> {
  const response = await api.get<ConversationListResponse>(API_ENDPOINTS.CONVERSATIONS.LIST, { params });
  return response.data;
}

export async function getConversation(id: string): Promise<Conversation> {
  const response = await api.get<Conversation>(API_ENDPOINTS.CONVERSATIONS.GET(id));
  return response.data;
}

export async function createConversation(data: CreateConversationRequest): Promise<Conversation> {
  const response = await api.post<Conversation>(API_ENDPOINTS.CONVERSATIONS.CREATE, data);
  return response.data;
}

export async function updateConversation(id: string, data: UpdateConversationRequest): Promise<Conversation> {
  const response = await api.patch<Conversation>(API_ENDPOINTS.CONVERSATIONS.UPDATE(id), data);
  return response.data;
}

export async function deleteConversation(id: string): Promise<void> {
  await api.delete(API_ENDPOINTS.CONVERSATIONS.DELETE(id));
}

export async function archiveConversation(id: string, isArchived: boolean): Promise<Conversation> {
  const response = await api.post<Conversation>(API_ENDPOINTS.CONVERSATIONS.ARCHIVE(id), { is_archived: isArchived });
  return response.data;
}

export async function searchConversations(query: string): Promise<Conversation[]> {
  const response = await api.get<Conversation[]>(API_ENDPOINTS.CONVERSATIONS.LIST, {
    params: { search: query },
  });
  return response.data;
}
```

---

### 6.5 `frontend/src/services/messages.ts`

**功能描述**：消息管理 API 服务。

```typescript
import api from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import { Message, MessageListResponse, PaginationParams } from '@/types';

export async function getMessages(
  conversationId: string,
  params?: PaginationParams
): Promise<MessageListResponse> {
  const response = await api.get<MessageListResponse>(
    API_ENDPOINTS.MESSAGES.LIST(conversationId),
    { params }
  );
  return response.data;
}

export async function deleteMessage(id: string): Promise<void> {
  await api.delete(API_ENDPOINTS.MESSAGES.DELETE(id));
}

export async function editMessage(id: string, content: string): Promise<Message> {
  const response = await api.patch<Message>(API_ENDPOINTS.MESSAGES.DELETE(id), { content });
  return response.data;
}
```

---

### 6.6 `frontend/src/services/users.ts`

**功能描述**：用户相关 API 服务。

```typescript
import api from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import { UserProfile, UpdateProfileRequest, UsageStats, UserSession } from '@/types';

export async function getProfile(): Promise<UserProfile> {
  const response = await api.get<UserProfile>(API_ENDPOINTS.USERS.PROFILE);
  return response.data;
}

export async function updateProfile(data: UpdateProfileRequest): Promise<UserProfile> {
  const response = await api.patch<UserProfile>(API_ENDPOINTS.USERS.UPDATE_PROFILE, data);
  return response.data;
}

export async function getUsageStats(): Promise<UsageStats> {
  const response = await api.get<UsageStats>(API_ENDPOINTS.USERS.USAGE_STATS);
  return response.data;
}

export async function getSessions(): Promise<UserSession[]> {
  const response = await api.get<UserSession[]>(API_ENDPOINTS.USERS.SESSIONS);
  return response.data;
}

export async function revokeSession(sessionId: string): Promise<void> {
  await api.post(API_ENDPOINTS.SESSIONS.REVOKE(sessionId));
}
```

---

### 6.7 `frontend/src/services/sessions.ts`

**功能描述**：会话管理 API 服务（多设备登录管理）。

```typescript
import api from './api';
import { API_ENDPOINTS } from '@/utils/constants';
import { UserSession } from '@/types';

export async function getActiveSessions(): Promise<UserSession[]> {
  const response = await api.get<UserSession[]>(API_ENDPOINTS.SESSIONS.LIST);
  return response.data;
}

export async function revokeSession(sessionId: string): Promise<void> {
  await api.post(API_ENDPOINTS.SESSIONS.REVOKE(sessionId));
}

export async function revokeAllOtherSessions(): Promise<void> {
  await api.post(`${API_ENDPOINTS.SESSIONS.LIST}/revoke-all-others`);
}
```

---

## 7. Zustand 状态管理（`src/stores/*.ts`）

### 7.1 `frontend/src/stores/authStore.ts`

**功能描述**：认证状态管理。

**核心代码**：

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserProfile } from '@/types';
import { getItem, setItem, removeItem, STORAGE_KEYS } from '@/utils/storage';
import * as authService from '@/services/auth';

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  logtoCallback: (code: string) => Promise<void>;
  fetchUser: () => Promise<void>;
  setUser: (user: UserProfile | null) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.login({ username, password });
          setItem(STORAGE_KEYS.JWT, response.access_token);
          setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);
          setItem(STORAGE_KEYS.USER, response.user);
          set({ user: response.user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ error: error instanceof Error ? error.message : '登录失败', isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        try {
          await authService.logout();
        } finally {
          removeItem(STORAGE_KEYS.JWT);
          removeItem(STORAGE_KEYS.REFRESH_TOKEN);
          removeItem(STORAGE_KEYS.USER);
          set({ user: null, isAuthenticated: false });
        }
      },

      logtoCallback: async (code) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authService.logtoCallback({ code });
          setItem(STORAGE_KEYS.JWT, response.access_token);
          setItem(STORAGE_KEYS.REFRESH_TOKEN, response.refresh_token);
          setItem(STORAGE_KEYS.USER, response.user);
          set({ user: response.user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'SSO 登录失败', isLoading: false });
          throw error;
        }
      },

      fetchUser: async () => {
        const token = getItem<string>(STORAGE_KEYS.JWT);
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true });
        try {
          const user = await authService.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ isAuthenticated: false, user: null, isLoading: false });
        }
      },

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'astra-auth',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
```

**State 说明**：
- `user: UserProfile | null`：当前登录用户信息
- `isAuthenticated: boolean`：是否已认证
- `isLoading: boolean`：加载状态
- `error: string | null`：错误信息

**Actions 说明**：
- `login(username, password)`：用户名密码登录
- `logout()`：退出登录，清除本地凭证
- `logtoCallback(code)`：处理 Logto SSO 回调
- `fetchUser()`：获取当前用户信息（用于页面刷新后恢复状态）
- `setUser(user)`：手动设置用户
- `clearError()`：清除错误信息

---

### 7.2 `frontend/src/stores/chatStore.ts`

**功能描述**：聊天状态管理（当前会话、流式消息、输入状态）。

```typescript
import { create } from 'zustand';
import { Message, AgentType, StreamChunk } from '@/types';
import * as chatService from '@/services/chat';
import * as messageService from '@/services/messages';

interface ChatState {
  currentConversationId: string | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  selectedAgent: AgentType;
  selectedModel: string;
  inputValue: string;
  error: string | null;
  abortController: (() => void) | null;

  setCurrentConversation: (id: string | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  deleteMessage: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  sendStreamingMessage: (content: string) => Promise<void>;
  stopStreaming: () => void;
  setSelectedAgent: (agent: AgentType) => void;
  setSelectedModel: (model: string) => void;
  setInputValue: (value: string) => void;
  clearMessages: () => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  currentConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
  selectedAgent: 'auto',
  selectedModel: 'deepseek-v4-flash',
  inputValue: '',
  error: null,
  abortController: null,

  setCurrentConversation: (id) => set({ currentConversationId: id }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg)),
    })),

  deleteMessage: async (id) => {
    await messageService.deleteMessage(id);
    set((state) => ({ messages: state.messages.filter((msg) => msg.id !== id) }));
  },

  sendMessage: async (content) => {
    const { currentConversationId, selectedAgent, selectedModel } = get();
    if (!currentConversationId) return;

    set({ isLoading: true, error: null });
    try {
      const message = await chatService.sendMessage({
        conversation_id: currentConversationId,
        content,
        agent_override: selectedAgent !== 'auto' ? selectedAgent : undefined,
        model_override: selectedModel,
      });
      get().addMessage(message);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '发送失败' });
    } finally {
      set({ isLoading: false });
    }
  },

  sendStreamingMessage: async (content) => {
    const { currentConversationId, selectedAgent, selectedModel } = get();
    if (!currentConversationId) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversationId,
      user_id: '',
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    get().addMessage(userMessage);

    set({ isStreaming: true, streamingContent: '', error: null });

    const abort = chatService.streamMessage(
      {
        conversation_id: currentConversationId,
        content,
        agent_override: selectedAgent !== 'auto' ? selectedAgent : undefined,
        model_override: selectedModel,
        stream: true,
      },
      {
        onChunk: (chunk: StreamChunk) => {
          const delta = chunk.choices[0]?.delta?.content || '';
          set((state) => ({ streamingContent: state.streamingContent + delta }));
        },
        onDone: () => {
          const { streamingContent } = get();
          const assistantMessage: Message = {
            id: `temp-assistant-${Date.now()}`,
            conversation_id: currentConversationId,
            user_id: '',
            role: 'assistant',
            content: streamingContent,
            created_at: new Date().toISOString(),
          };
          get().addMessage(assistantMessage);
          set({ isStreaming: false, streamingContent: '', abortController: null });
        },
        onError: (error) => {
          set({ isStreaming: false, error: error.message, abortController: null });
        },
      }
    );

    set({ abortController: abort });
  },

  stopStreaming: () => {
    const { abortController } = get();
    if (abortController) {
      abortController();
      set({ isStreaming: false, abortController: null });
    }
  },

  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setInputValue: (value) => set({ inputValue: value }),
  clearMessages: () => set({ messages: [] }),
  clearError: () => set({ error: null }),
}));
```

---

### 7.3 `frontend/src/stores/conversationStore.ts`

**功能描述**：会话列表状态管理。

```typescript
import { create } from 'zustand';
import { Conversation, CreateConversationRequest, UpdateConversationRequest } from '@/types';
import * as conversationService from '@/services/conversations';

interface ConversationState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
  searchQuery: string;

  fetchConversations: () => Promise<void>;
  fetchConversation: (id: string) => Promise<void>;
  createConversation: (data: CreateConversationRequest) => Promise<Conversation>;
  updateConversation: (id: string, data: UpdateConversationRequest) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  archiveConversation: (id: string, isArchived: boolean) => Promise<void>;
  searchConversations: (query: string) => Promise<void>;
  setCurrentConversation: (conversation: Conversation | null) => void;
  setSearchQuery: (query: string) => void;
  clearError: () => void;
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  isLoading: false,
  error: null,
  searchQuery: '',

  fetchConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await conversationService.getConversations();
      set({ conversations: response.conversations, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取会话列表失败', isLoading: false });
    }
  },

  fetchConversation: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await conversationService.getConversation(id);
      set({ currentConversation: conversation, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取会话详情失败', isLoading: false });
    }
  },

  createConversation: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await conversationService.createConversation(data);
      set((state) => ({
        conversations: [conversation, ...state.conversations],
        currentConversation: conversation,
        isLoading: false,
      }));
      return conversation;
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '创建会话失败', isLoading: false });
      throw error;
    }
  },

  updateConversation: async (id, data) => {
    try {
      const updated = await conversationService.updateConversation(id, data);
      set((state) => ({
        conversations: state.conversations.map((c) => (c.id === id ? updated : c)),
        currentConversation: state.currentConversation?.id === id ? updated : state.currentConversation,
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '更新会话失败' });
      throw error;
    }
  },

  deleteConversation: async (id) => {
    try {
      await conversationService.deleteConversation(id);
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        currentConversation: state.currentConversation?.id === id ? null : state.currentConversation,
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '删除会话失败' });
      throw error;
    }
  },

  archiveConversation: async (id, isArchived) => {
    try {
      const updated = await conversationService.archiveConversation(id, isArchived);
      set((state) => ({
        conversations: state.conversations.map((c) => (c.id === id ? updated : c)),
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '归档会话失败' });
      throw error;
    }
  },

  searchConversations: async (query) => {
    set({ searchQuery: query, isLoading: true });
    try {
      const results = await conversationService.searchConversations(query);
      set({ conversations: results, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '搜索失败', isLoading: false });
    }
  },

  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  clearError: () => set({ error: null }),
}));
```

---

### 7.4 `frontend/src/stores/userStore.ts`

**功能描述**：用户资料与偏好设置状态管理。

```typescript
import { create } from 'zustand';
import { UserProfile, UpdateProfileRequest, UsageStats, UserSession } from '@/types';
import * as userService from '@/services/users';

interface UserState {
  profile: UserProfile | null;
  usageStats: UsageStats | null;
  sessions: UserSession[];
  isLoading: boolean;
  error: string | null;

  fetchProfile: () => Promise<void>;
  updateProfile: (data: UpdateProfileRequest) => Promise<void>;
  fetchUsageStats: () => Promise<void>;
  fetchSessions: () => Promise<void>;
  revokeSession: (sessionId: string) => Promise<void>;
  clearError: () => void;
}

export const useUserStore = create<UserState>((set, get) => ({
  profile: null,
  usageStats: null,
  sessions: [],
  isLoading: false,
  error: null,

  fetchProfile: async () => {
    set({ isLoading: true, error: null });
    try {
      const profile = await userService.getProfile();
      set({ profile, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取用户资料失败', isLoading: false });
    }
  },

  updateProfile: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const profile = await userService.updateProfile(data);
      set({ profile, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '更新用户资料失败', isLoading: false });
      throw error;
    }
  },

  fetchUsageStats: async () => {
    try {
      const usageStats = await userService.getUsageStats();
      set({ usageStats });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取用量统计失败' });
    }
  },

  fetchSessions: async () => {
    try {
      const sessions = await userService.getSessions();
      set({ sessions });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '获取会话列表失败' });
    }
  },

  revokeSession: async (sessionId) => {
    try {
      await userService.revokeSession(sessionId);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
      }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : '下线会话失败' });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));
```

---

### 7.5 `frontend/src/stores/settingsStore.ts`

**功能描述**：应用设置状态管理（主题、快捷键等）。

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { getItem, setItem, STORAGE_KEYS } from '@/utils/storage';

type Theme = 'light' | 'dark' | 'system';

interface SettingsState {
  theme: Theme;
  fontSize: 'small' | 'medium' | 'large';
  sendShortcut: 'enter' | 'ctrl_enter';
  enableStreaming: boolean;
  enableSound: boolean;

  setTheme: (theme: Theme) => void;
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
  setSendShortcut: (shortcut: 'enter' | 'ctrl_enter') => void;
  setEnableStreaming: (enable: boolean) => void;
  setEnableSound: (enable: boolean) => void;
  applyTheme: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      fontSize: 'medium',
      sendShortcut: 'enter',
      enableStreaming: true,
      enableSound: false,

      setTheme: (theme) => {
        set({ theme });
        get().applyTheme();
      },

      setFontSize: (fontSize) => set({ fontSize }),
      setSendShortcut: (sendShortcut) => set({ sendShortcut }),
      setEnableStreaming: (enableStreaming) => set({ enableStreaming }),
      setEnableSound: (enableSound) => set({ enableSound }),

      applyTheme: () => {
        const { theme } = get();
        const root = window.document.documentElement;
        root.classList.remove('light', 'dark');

        if (theme === 'system') {
          const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
          root.classList.add(systemTheme);
        } else {
          root.classList.add(theme);
        }
      },
    }),
    {
      name: 'astra-settings',
    }
  )
);
```

---
## 8. 自定义 Hooks（`src/hooks/*.ts`）

### 8.1 `frontend/src/hooks/useAuth.ts`

**功能描述**：认证相关 Hook，封装 authStore。

```typescript
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export function useAuth() {
  const { user, isAuthenticated, isLoading, error, login, logout, logtoCallback, fetchUser, clearError } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      fetchUser();
    }
  }, [isAuthenticated, isLoading, fetchUser]);

  const handleLogin = async (username: string, password: string) => {
    await login(username, password);
    navigate('/chat');
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleLogtoCallback = async (code: string) => {
    await logtoCallback(code);
    navigate('/chat');
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    logout: handleLogout,
    logtoCallback: handleLogtoCallback,
    clearError,
  };
}
```

**返回值说明**：
- `user`：当前用户
- `isAuthenticated`：是否已认证
- `isLoading`：加载状态
- `error`：错误信息
- `login(username, password)`：登录并跳转
- `logout()`：登出并跳转
- `logtoCallback(code)`：处理 SSO 回调并跳转
- `clearError()`：清除错误

---

### 8.2 `frontend/src/hooks/useChat.ts`

**功能描述**：聊天相关 Hook，封装 chatStore。

```typescript
import { useCallback, useEffect, useRef } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useConversationStore } from '@/stores/conversationStore';
import * as messageService from '@/services/messages';

export function useChat(conversationId?: string) {
  const {
    messages,
    isStreaming,
    streamingContent,
    selectedAgent,
    selectedModel,
    inputValue,
    error,
    setCurrentConversation,
    setMessages,
    sendMessage,
    sendStreamingMessage,
    stopStreaming,
    setSelectedAgent,
    setSelectedModel,
    setInputValue,
    clearMessages,
    clearError,
  } = useChatStore();

  const { currentConversation } = useConversationStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversationId) {
      setCurrentConversation(conversationId);
      loadMessages(conversationId);
    }
    return () => {
      clearMessages();
    };
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const loadMessages = async (id: string) => {
    try {
      const response = await messageService.getMessages(id);
      setMessages(response.messages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isStreaming) return;

    const content = inputValue.trim();
    setInputValue('');

    if (currentConversation?.id) {
      await sendStreamingMessage(content);
    }
  }, [inputValue, isStreaming, currentConversation, sendStreamingMessage, setInputValue]);

  const handleStop = useCallback(() => {
    stopStreaming();
  }, [stopStreaming]);

  return {
    messages,
    isStreaming,
    streamingContent,
    selectedAgent,
    selectedModel,
    inputValue,
    error,
    messagesEndRef,
    setInputValue,
    setSelectedAgent,
    setSelectedModel,
    handleSend,
    handleStop,
    clearError,
  };
}
```

---

### 8.3 `frontend/src/hooks/useConversations.ts`

**功能描述**：会话列表相关 Hook。

```typescript
import { useEffect } from 'react';
import { useConversationStore } from '@/stores/conversationStore';

export function useConversations() {
  const {
    conversations,
    currentConversation,
    isLoading,
    error,
    searchQuery,
    fetchConversations,
    createConversation,
    updateConversation,
    deleteConversation,
    archiveConversation,
    searchConversations,
    setCurrentConversation,
    setSearchQuery,
    clearError,
  } = useConversationStore();

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleCreate = async (title?: string) => {
    const conversation = await createConversation({ title: title || '新对话' });
    setCurrentConversation(conversation);
    return conversation;
  };

  const handleDelete = async (id: string) => {
    await deleteConversation(id);
  };

  const handleRename = async (id: string, title: string) => {
    await updateConversation(id, { title });
  };

  const handleArchive = async (id: string, isArchived: boolean) => {
    await archiveConversation(id, isArchived);
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      await searchConversations(query);
    } else {
      await fetchConversations();
    }
  };

  return {
    conversations,
    currentConversation,
    isLoading,
    error,
    searchQuery,
    handleCreate,
    handleDelete,
    handleRename,
    handleArchive,
    handleSearch,
    setCurrentConversation,
    clearError,
  };
}
```

---

### 8.4 `frontend/src/hooks/useMessages.ts`

**功能描述**：消息操作相关 Hook。

```typescript
import { useCallback } from 'react';
import { useChatStore } from '@/stores/chatStore';
import * as messageService from '@/services/messages';
import * as chatService from '@/services/chat';

export function useMessages() {
  const { messages, deleteMessage, updateMessage, addMessage } = useChatStore();

  const handleDelete = useCallback(async (id: string) => {
    await deleteMessage(id);
  }, [deleteMessage]);

  const handleEdit = useCallback(async (id: string, content: string) => {
    const updated = await messageService.editMessage(id, content);
    updateMessage(id, updated);
  }, [updateMessage]);

  const handleRegenerate = useCallback(async (id: string) => {
    const regenerated = await chatService.regenerateMessage(id);
    updateMessage(id, regenerated);
  }, [updateMessage]);

  const handleCopy = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
  }, []);

  return {
    messages,
    handleDelete,
    handleEdit,
    handleRegenerate,
    handleCopy,
  };
}
```

---

### 8.5 `frontend/src/hooks/useTheme.ts`

**功能描述**：主题切换 Hook。

```typescript
import { useEffect } from 'react';
import { useSettingsStore } from '@/stores/settingsStore';

export function useTheme() {
  const { theme, setTheme, applyTheme } = useSettingsStore();

  useEffect(() => {
    applyTheme();

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        applyTheme();
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, applyTheme]);

  return { theme, setTheme };
}
```

---

### 8.6 `frontend/src/hooks/useLocalStorage.ts`

**功能描述**：localStorage 同步 Hook。

```typescript
import { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue = (value: T) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue];
}
```

---

### 8.7 `frontend/src/hooks/useSSE.ts`

**功能描述**：SSE 流式连接 Hook（通用封装）。

```typescript
import { useEffect, useRef, useCallback } from 'react';

interface UseSSEOptions {
  onMessage: (data: string) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export function useSSE(url: string | null, options: UseSSEOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const { onMessage, onError, onOpen, onClose } = options;

  const connect = useCallback(() => {
    if (!url) return;

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      onOpen?.();
    };

    eventSource.onmessage = (event) => {
      onMessage(event.data);
    };

    eventSource.onerror = (error) => {
      onError?.(error);
      eventSource.close();
      onClose?.();
    };

    return eventSource;
  }, [url, onMessage, onError, onOpen, onClose]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      onClose?.();
    }
  }, [onClose]);

  useEffect(() => {
    if (url) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [url, connect, disconnect]);

  return { connect, disconnect };
}
```

---

## 9. 通用组件（`src/components/common/*.tsx`）

### 9.1 `frontend/src/components/common/Loading.tsx`

**功能描述**：加载状态组件。

```typescript
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export function Loading({ size = 'md', text, className }: LoadingProps) {
  const sizeMap = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className={cn('flex flex-col items-center justify-center gap-2', className)}>
      <Loader2 className={cn('animate-spin text-primary', sizeMap[size])} />
      {text && <p className="text-sm text-muted-foreground">{text}</p>}
    </div>
  );
}
```

**Props 说明**：
- `size`：加载图标大小
- `text`：加载提示文本
- `className`：自定义类名

---

### 9.2 `frontend/src/components/common/ErrorBoundary.tsx`

**功能描述**：错误边界组件，捕获子组件渲染错误。

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 p-4">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-lg font-semibold">出错了</h2>
          <p className="text-sm text-muted-foreground text-center max-w-md">
            {this.state.error?.message || '发生了未知错误'}
          </p>
          <Button onClick={this.handleReset}>重试</Button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

### 9.3 `frontend/src/components/common/EmptyState.tsx`

**功能描述**：空状态展示组件。

```typescript
import { LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/utils/cn';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 px-4', className)}>
      <div className="rounded-full bg-muted p-4 mb-4">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground text-center max-w-sm mb-4">{description}</p>
      )}
      {actionLabel && onAction && (
        <Button onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
```

---

### 9.4 `frontend/src/components/common/ConfirmDialog.tsx`

**功能描述**：确认对话框组件。

```typescript
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  variant?: 'default' | 'destructive';
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = '确认',
  cancelLabel = '取消',
  onConfirm,
  variant = 'default',
}: ConfirmDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && <AlertDialogDescription>{description}</AlertDialogDescription>}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{cancelLabel}</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className={variant === 'destructive' ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90' : ''}
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

---

### 9.5 `frontend/src/components/common/Toast.tsx`

**功能描述**：Toast 通知组件（基于 sonner）。

```typescript
import { Toaster } from 'sonner';

export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        classNames: {
          toast: 'group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg',
          description: 'group-[.toast]:text-muted-foreground',
          actionButton: 'group-[.toast]:bg-primary group-[.toast]:text-primary-foreground',
          cancelButton: 'group-[.toast]:bg-muted group-[.toast]:text-muted-foreground',
        },
      }}
    />
  );
}

export { toast } from 'sonner';
```

---

## 10. 布局组件（`src/components/layout/*.tsx`）

### 10.1 `frontend/src/components/layout/MainLayout.tsx`

**功能描述**：主布局组件，包含侧边栏和主内容区。

```typescript
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useTheme } from '@/hooks/useTheme';

export function MainLayout() {
  useTheme();

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

---

### 10.2 `frontend/src/components/layout/Sidebar.tsx`

**功能描述**：侧边栏组件，包含会话列表和导航。

```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, MessageSquare, Settings, User, LogOut, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { ConversationList } from '@/components/chat/ConversationList';
import { useAuth } from '@/hooks/useAuth';
import { useConversations } from '@/hooks/useConversations';
import { cn } from '@/utils/cn';

export function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { conversations, handleCreate, handleSearch, searchQuery } = useConversations();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const handleNewChat = async () => {
    const conversation = await handleCreate();
    navigate(`/chat/${conversation.id}`);
  };

  return (
    <div className={cn(
      'flex flex-col border-r bg-muted/40 transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-64'
    )}>
      <div className="p-4">
        <Button
          onClick={handleNewChat}
          className={cn('w-full justify-start gap-2', isCollapsed && 'justify-center px-2')}
        >
          <Plus className="h-4 w-4" />
          {!isCollapsed && '新对话'}
        </Button>
      </div>

      {!isCollapsed && (
        <div className="px-4 pb-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索会话..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>
      )}

      <ScrollArea className="flex-1 px-2">
        <ConversationList collapsed={isCollapsed} />
      </ScrollArea>

      <Separator />

      <div className="p-4 space-y-2">
        <Button
          variant="ghost"
          className={cn('w-full justify-start gap-2', isCollapsed && 'justify-center px-2')}
          onClick={() => navigate('/settings')}
        >
          <Settings className="h-4 w-4" />
          {!isCollapsed && '设置'}
        </Button>
        <Button
          variant="ghost"
          className={cn('w-full justify-start gap-2', isCollapsed && 'justify-center px-2')}
          onClick={() => navigate('/profile')}
        >
          <User className="h-4 w-4" />
          {!isCollapsed && (user?.username || '个人资料')}
        </Button>
        <Button
          variant="ghost"
          className={cn('w-full justify-start gap-2 text-destructive', isCollapsed && 'justify-center px-2')}
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          {!isCollapsed && '退出登录'}
        </Button>
      </div>
    </div>
  );
}
```

---

### 10.3 `frontend/src/components/layout/Header.tsx`

**功能描述**：顶部导航栏组件。

```typescript
import { useLocation } from 'react-router-dom';
import { Moon, Sun, Monitor } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useTheme } from '@/hooks/useTheme';
import { useConversationStore } from '@/stores/conversationStore';

export function Header() {
  const location = useLocation();
  const { theme, setTheme } = useTheme();
  const { currentConversation } = useConversationStore();

  const getTitle = () => {
    if (location.pathname.startsWith('/chat/') && currentConversation) {
      return currentConversation.title;
    }
    if (location.pathname === '/settings') return '设置';
    if (location.pathname === '/profile') return '个人资料';
    return 'Astra';
  };

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b bg-background">
      <h1 className="text-lg font-semibold">{getTitle()}</h1>

      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              {theme === 'light' && <Sun className="h-5 w-5" />}
              {theme === 'dark' && <Moon className="h-5 w-5" />}
              {theme === 'system' && <Monitor className="h-5 w-5" />}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setTheme('light')}>
              <Sun className="mr-2 h-4 w-4" /> 浅色
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('dark')}>
              <Moon className="mr-2 h-4 w-4" /> 深色
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('system')}>
              <Monitor className="mr-2 h-4 w-4" /> 跟随系统
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
```

---

### 10.4 `frontend/src/components/layout/ProtectedRoute.tsx`

**功能描述**：路由守卫组件，保护需要认证的页面。

```typescript
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { Loading } from '@/components/common/Loading';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loading size="lg" text="加载中..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

---

## 11. 聊天组件（`src/components/chat/*.tsx`）

### 11.1 `frontend/src/components/chat/MarkdownRenderer.tsx`

**功能描述**：Markdown 渲染组件，支持 GFM、LaTeX、代码高亮。

```typescript
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'katex/dist/katex.min.css';
import { cn } from '@/utils/cn';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn('prose prose-sm dark:prose-invert max-w-none', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={vscDarkPlus}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          table({ children }) {
            return (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="px-4 py-2 bg-muted font-medium text-left text-sm">{children}</th>
            );
          },
          td({ children }) {
            return (
              <td className="px-4 py-2 border-t text-sm">{children}</td>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
```

**Props 说明**：
- `content`：Markdown 文本内容
- `className`：自定义类名

**核心逻辑**：
- 使用 `react-markdown` 渲染 Markdown
- `remark-gfm` 支持 GFM 表格、删除线等
- `rehype-katex` 渲染 LaTeX 公式
- `react-syntax-highlighter` 提供代码块语法高亮
- 自定义 `table/th/td` 组件实现响应式表格样式

---

### 11.2 `frontend/src/components/chat/MessageList.tsx`

**功能描述**：消息列表组件，展示会话中的所有消息。

```typescript
import { useEffect, useRef } from 'react';
import { Message } from '@/types';
import { MessageItem } from './MessageItem';
import { Loading } from '@/components/common/Loading';
import { useChatStore } from '@/stores/chatStore';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const { streamingContent, isStreaming } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loading text="加载消息中..." />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-4 overflow-y-auto">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {isStreaming && streamingContent && (
        <MessageItem
          message={{
            id: 'streaming',
            conversation_id: '',
            user_id: '',
            role: 'assistant',
            content: streamingContent,
            created_at: new Date().toISOString(),
          }}
          isStreaming
        />
      )}

      <div ref={bottomRef} />
    </div>
  );
}
```

---

### 11.3 `frontend/src/components/chat/MessageItem.tsx`

**功能描述**：单条消息组件，支持用户/助手角色展示。

```typescript
import { useState } from 'react';
import { Message } from '@/types';
import { MarkdownRenderer } from './MarkdownRenderer';
import { Button } from '@/components/ui/button';
import { Copy, RefreshCw, Edit2, Trash2, Check } from 'lucide-react';
import { cn } from '@/utils/cn';
import { formatRelativeTime } from '@/utils/format';
import { useMessages } from '@/hooks/useMessages';
import { toast } from 'sonner';

interface MessageItemProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageItem({ message, isStreaming }: MessageItemProps) {
  const { handleCopy, handleRegenerate, handleDelete } = useMessages();
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [copied, setCopied] = useState(false);

  const isUser = message.role === 'user';

  const onCopy = async () => {
    await handleCopy(message.content);
    setCopied(true);
    toast.success('已复制到剪贴板');
    setTimeout(() => setCopied(false), 2000);
  };

  const onRegenerate = async () => {
    await handleRegenerate(message.id);
    toast.success('正在重新生成...');
  };

  const onDelete = async () => {
    await handleDelete(message.id);
    toast.success('消息已删除');
  };

  return (
    <div className={cn('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <div className={cn(
        'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
        isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
      )}>
        {isUser ? 'U' : 'AI'}
      </div>

      <div className={cn('flex-1 max-w-[80%]', isUser ? 'text-right' : 'text-left')}>
        <div className={cn(
          'inline-block rounded-lg px-4 py-2',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        )}>
          {isEditing ? (
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full min-h-[100px] bg-transparent resize-none focus:outline-none"
            />
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
          {isStreaming && (
            <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
          )}
        </div>

        <div className={cn(
          'flex items-center gap-2 mt-1 text-xs text-muted-foreground',
          isUser ? 'justify-end' : 'justify-start'
        )}>
          <span>{formatRelativeTime(message.created_at)}</span>

          {!isUser && !isStreaming && (
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onCopy}>
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onRegenerate}>
                <RefreshCw className="h-3 w-3" />
              </Button>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setIsEditing(true)}>
                <Edit2 className="h-3 w-3" />
              </Button>
              <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onDelete}>
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

### 11.4 `frontend/src/components/chat/ChatInput.tsx`

**功能描述**：聊天输入框组件，支持多行输入、快捷键发送。

```typescript
import { useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AgentSelector } from './AgentSelector';
import { ModelSelector } from './ModelSelector';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { MAX_MESSAGE_LENGTH } from '@/utils/constants';

interface ChatInputProps {
  onSend: () => void;
  onStop: () => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, onStop, disabled }: ChatInputProps) {
  const { inputValue, setInputValue, isStreaming } = useChatStore();
  const { sendShortcut } = useSettingsStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputValue]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (sendShortcut === 'enter' && !e.shiftKey) {
        e.preventDefault();
        onSend();
      } else if (sendShortcut === 'ctrl_enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        onSend();
      }
    }
  };

  const remainingChars = MAX_MESSAGE_LENGTH - inputValue.length;

  return (
    <div className="border-t bg-background p-4">
      <div className="flex items-center gap-2 mb-2">
        <AgentSelector />
        <ModelSelector />
      </div>

      <div className="relative">
        <Textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入消息..."
          disabled={disabled || isStreaming}
          className="min-h-[60px] max-h-[200px] resize-none pr-12"
          maxLength={MAX_MESSAGE_LENGTH}
        />

        <div className="absolute bottom-2 right-2 flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {remainingChars}
          </span>
          {isStreaming ? (
            <Button size="icon" variant="destructive" onClick={onStop}>
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button size="icon" onClick={onSend} disabled={!inputValue.trim() || disabled}>
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

### 11.5 `frontend/src/components/chat/AgentSelector.tsx`

**功能描述**：Agent 选择器组件。

```typescript
import { Check, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useChatStore } from '@/stores/chatStore';
import { AGENTS, AgentType } from '@/types';
import { cn } from '@/utils/cn';

export function AgentSelector() {
  const { selectedAgent, setSelectedAgent } = useChatStore();
  const currentAgent = AGENTS.find((a) => a.id === selectedAgent) || AGENTS[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <span className={cn('w-2 h-2 rounded-full', currentAgent.color.replace('text-', 'bg-'))} />
          {currentAgent.display_name}
          <ChevronDown className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {AGENTS.map((agent) => (
          <DropdownMenuItem
            key={agent.id}
            onClick={() => setSelectedAgent(agent.id as AgentType)}
            className="flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <span className={cn('w-2 h-2 rounded-full', agent.color.replace('text-', 'bg-'))} />
              <div>
                <div className="font-medium">{agent.display_name}</div>
                <div className="text-xs text-muted-foreground">{agent.description}</div>
              </div>
            </div>
            {selectedAgent === agent.id && <Check className="h-4 w-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

---

### 11.6 `frontend/src/components/chat/ModelSelector.tsx`

**功能描述**：LLM 模型选择器组件。

```typescript
import { Check, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useChatStore } from '@/stores/chatStore';
import { MODELS } from '@/types';

export function ModelSelector() {
  const { selectedModel, setSelectedModel } = useChatStore();
  const currentModel = MODELS.find((m) => m.id === selectedModel) || MODELS[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          {currentModel.name}
          <ChevronDown className="h-3 w-3" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        {MODELS.map((model) => (
          <DropdownMenuItem
            key={model.id}
            onClick={() => setSelectedModel(model.id)}
            className="flex items-center justify-between"
          >
            <div>
              <div className="font-medium">{model.name}</div>
              <div className="text-xs text-muted-foreground">
                {model.provider} · {model.description}
              </div>
            </div>
            {selectedModel === model.id && <Check className="h-4 w-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

---

### 11.7 `frontend/src/components/chat/ConversationList.tsx`

**功能描述**：会话列表组件。

```typescript
import { Conversation } from '@/types';
import { ConversationItem } from './ConversationItem';
import { useConversations } from '@/hooks/useConversations';
import { EmptyState } from '@/components/common/EmptyState';
import { MessageSquare } from 'lucide-react';

interface ConversationListProps {
  collapsed?: boolean;
}

export function ConversationList({ collapsed }: ConversationListProps) {
  const { conversations, isLoading } = useConversations();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
      </div>
    );
  }

  if (conversations.length === 0) {
    if (collapsed) return null;
    return (
      <EmptyState
        icon={MessageSquare}
        title="暂无会话"
        description="点击上方按钮开始新对话"
      />
    );
  }

  return (
    <div className="space-y-1 py-2">
      {conversations.map((conversation) => (
        <ConversationItem
          key={conversation.id}
          conversation={conversation}
          collapsed={collapsed}
        />
      ))}
    </div>
  );
}
```

---

### 11.8 `frontend/src/components/chat/ConversationItem.tsx`

**功能描述**：单个会话项组件。

```typescript
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { MoreHorizontal, Pencil, Trash2, Archive, ArchiveRestore } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Conversation } from '@/types';
import { useConversations } from '@/hooks/useConversations';
import { cn } from '@/utils/cn';
import { formatRelativeTime, truncateText } from '@/utils/format';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';

interface ConversationItemProps {
  conversation: Conversation;
  collapsed?: boolean;
}

export function ConversationItem({ conversation, collapsed }: ConversationItemProps) {
  const navigate = useNavigate();
  const { id: currentId } = useParams();
  const { handleRename, handleDelete, handleArchive, setCurrentConversation } = useConversations();
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(conversation.title);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const isActive = currentId === conversation.id;

  const handleClick = () => {
    setCurrentConversation(conversation);
    navigate(`/chat/${conversation.id}`);
  };

  const handleSaveRename = async () => {
    if (editTitle.trim() && editTitle !== conversation.title) {
      await handleRename(conversation.id, editTitle.trim());
    }
    setIsEditing(false);
  };

  const handleDeleteConfirm = async () => {
    await handleDelete(conversation.id);
    setShowDeleteDialog(false);
    if (isActive) {
      navigate('/chat');
    }
  };

  if (collapsed) {
    return (
      <div
        className={cn(
          'flex justify-center p-2 rounded-lg cursor-pointer hover:bg-accent',
          isActive && 'bg-accent'
        )}
        onClick={handleClick}
        title={conversation.title}
      >
        <MessageSquare className="h-5 w-5" />
      </div>
    );
  }

  return (
    <>
      <div
        className={cn(
          'group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer hover:bg-accent',
          isActive && 'bg-accent'
        )}
        onClick={handleClick}
      >
        {isEditing ? (
          <Input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onBlur={handleSaveRename}
            onKeyDown={(e) => e.key === 'Enter' && handleSaveRename()}
            autoFocus
            className="h-7 text-sm"
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{conversation.title}</div>
              <div className="text-xs text-muted-foreground">
                {formatRelativeTime(conversation.updated_at)}
              </div>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}>
                  <Pencil className="mr-2 h-4 w-4" /> 重命名
                </DropdownMenuItem>
                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleArchive(conversation.id, !conversation.is_archived); }}>
                  {conversation.is_archived ? (
                    <><ArchiveRestore className="mr-2 h-4 w-4" /> 取消归档</>
                  ) : (
                    <><Archive className="mr-2 h-4 w-4" /> 归档</>
                  )}
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={(e) => { e.stopPropagation(); setShowDeleteDialog(true); }}
                >
                  <Trash2 className="mr-2 h-4 w-4" /> 删除
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        )}
      </div>

      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="删除会话"
        description="确定要删除这个会话吗？此操作不可撤销。"
        confirmLabel="删除"
        variant="destructive"
        onConfirm={handleDeleteConfirm}
      />
    </>
  );
}
```

---
## 12. 页面组件（`src/pages/*.tsx`）

### 12.1 `frontend/src/pages/LoginPage.tsx`

**功能描述**：登录页面，支持用户名密码登录和 Logto SSO 登录。

```typescript
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/hooks/useAuth';
import { logtoLogin } from '@/services/auth';
import { toast } from 'sonner';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading, error, clearError } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/chat';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch {
      // error handled by store
    }
  };

  const handleLogtoLogin = async () => {
    try {
      const { redirect_url } = await logtoLogin();
      window.location.href = redirect_url;
    } catch (error) {
      toast.error('获取 SSO 登录链接失败');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-muted/40">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Astra</CardTitle>
          <CardDescription>登录您的账户</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入用户名"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
                required
              />
            </div>
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? '登录中...' : '登录'}
            </Button>
          </form>

          <div className="relative">
            <Separator />
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-xs text-muted-foreground">
              或
            </span>
          </div>

          <Button variant="outline" className="w-full" onClick={handleLogtoLogin}>
            使用 Logto SSO 登录
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### 12.2 `frontend/src/pages/ChatPage.tsx`

**功能描述**：聊天主页面。

```typescript
import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { useChat } from '@/hooks/useChat';
import { useConversations } from '@/hooks/useConversations';
import { EmptyState } from '@/components/common/EmptyState';
import { MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { conversations, handleCreate } = useConversations();
  const {
    messages,
    isStreaming,
    inputValue,
    setInputValue,
    handleSend,
    handleStop,
    messagesEndRef,
  } = useChat(id);

  const handleNewChat = async () => {
    const conversation = await handleCreate();
    navigate(`/chat/${conversation.id}`);
  };

  if (!id) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <EmptyState
          icon={MessageSquare}
          title="开始新对话"
          description="选择一个会话或创建新对话开始聊天"
          actionLabel="新对话"
          onAction={handleNewChat}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSend={handleSend} onStop={handleStop} />
    </div>
  );
}
```

---

### 12.3 `frontend/src/pages/SettingsPage.tsx`

**功能描述**：设置页面，包含主题、偏好设置、会话管理等。

```typescript
import { useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useSettingsStore } from '@/stores/settingsStore';
import { useUserStore } from '@/stores/userStore';
import { useAuthStore } from '@/stores/authStore';
import { formatRelativeTime, parseUserAgent } from '@/utils/format';
import { Monitor, Moon, Sun } from 'lucide-react';

export function SettingsPage() {
  const { theme, setTheme, fontSize, setFontSize, sendShortcut, setSendShortcut, enableStreaming, setEnableStreaming, enableSound, setEnableSound } = useSettingsStore();
  const { sessions, fetchSessions, revokeSession } = useUserStore();
  const { user } = useAuthStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return (
    <div className="container max-w-2xl py-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>外观</CardTitle>
          <CardDescription>自定义界面外观和显示效果</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>主题模式</Label>
            <RadioGroup value={theme} onValueChange={(v) => setTheme(v as typeof theme)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="light" id="light" />
                <Label htmlFor="light" className="flex items-center gap-2">
                  <Sun className="h-4 w-4" /> 浅色
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="dark" id="dark" />
                <Label htmlFor="dark" className="flex items-center gap-2">
                  <Moon className="h-4 w-4" /> 深色
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="system" id="system" />
                <Label htmlFor="system" className="flex items-center gap-2">
                  <Monitor className="h-4 w-4" /> 跟随系统
                </Label>
              </div>
            </RadioGroup>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label>字体大小</Label>
            <RadioGroup value={fontSize} onValueChange={(v) => setFontSize(v as typeof fontSize)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="small" id="small" />
                <Label htmlFor="small">小</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="medium" id="medium" />
                <Label htmlFor="medium">中</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="large" id="large" />
                <Label htmlFor="large">大</Label>
              </div>
            </RadioGroup>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>聊天偏好</CardTitle>
          <CardDescription>自定义聊天体验</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>发送快捷键</Label>
            <RadioGroup value={sendShortcut} onValueChange={(v) => setSendShortcut(v as typeof sendShortcut)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="enter" id="enter" />
                <Label htmlFor="enter">Enter 发送</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="ctrl_enter" id="ctrl_enter" />
                <Label htmlFor="ctrl_enter">Ctrl + Enter 发送</Label>
              </div>
            </RadioGroup>
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>流式输出</Label>
              <p className="text-sm text-muted-foreground">实时显示 AI 回复内容</p>
            </div>
            <Switch checked={enableStreaming} onCheckedChange={setEnableStreaming} />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>提示音</Label>
              <p className="text-sm text-muted-foreground">收到回复时播放提示音</p>
            </div>
            <Switch checked={enableSound} onCheckedChange={setEnableSound} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>登录设备管理</CardTitle>
          <CardDescription>查看和管理当前登录的设备</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sessions.map((session) => {
              const { device, browser } = parseUserAgent(session.device_info);
              return (
                <div key={session.id} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <div className="font-medium">
                      {device} · {browser}
                      {session.is_current && (
                        <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">当前设备</span>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {session.ip_address} · 最后活跃 {formatRelativeTime(session.last_active_at)}
                    </div>
                  </div>
                  {!session.is_current && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => revokeSession(session.id)}
                    >
                      下线
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### 12.4 `frontend/src/pages/ProfilePage.tsx`

**功能描述**：个人资料页面，展示用户信息、用量统计。

```typescript
import { useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useAuthStore } from '@/stores/authStore';
import { useUserStore } from '@/stores/userStore';
import { formatDate, formatTokens } from '@/utils/format';
import { MessageSquare, Zap, Bot, Calendar } from 'lucide-react';

export function ProfilePage() {
  const { user } = useAuthStore();
  const { usageStats, fetchUsageStats } = useUserStore();

  useEffect(() => {
    fetchUsageStats();
  }, [fetchUsageStats]);

  if (!user) return null;

  return (
    <div className="container max-w-2xl py-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>个人资料</CardTitle>
          <CardDescription>您的账户信息和偏好设置</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-4">
            <Avatar className="h-20 w-20">
              <AvatarImage src={user.avatar_url} />
              <AvatarFallback className="text-2xl">
                {user.username.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-2xl font-bold">{user.username}</h2>
              <p className="text-muted-foreground">{user.email || '未设置邮箱'}</p>
              <div className="flex gap-2 mt-2">
                <Badge variant="secondary">
                  默认模型: {user.default_model}
                </Badge>
                <Badge variant="secondary">
                  默认 Agent: {user.default_agent}
                </Badge>
              </div>
            </div>
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">注册时间:</span>
              <span>{formatDate(user.created_at, 'yyyy-MM-dd')}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>用量统计</CardTitle>
          <CardDescription>您的使用情况概览</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
              <MessageSquare className="h-6 w-6 mb-2 text-primary" />
              <span className="text-2xl font-bold">{usageStats?.total_conversations || 0}</span>
              <span className="text-xs text-muted-foreground">会话数</span>
            </div>
            <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
              <Zap className="h-6 w-6 mb-2 text-primary" />
              <span className="text-2xl font-bold">{formatTokens(usageStats?.total_tokens || 0)}</span>
              <span className="text-xs text-muted-foreground">总 Tokens</span>
            </div>
            <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
              <Bot className="h-6 w-6 mb-2 text-primary" />
              <span className="text-2xl font-bold">{usageStats?.total_messages || 0}</span>
              <span className="text-xs text-muted-foreground">消息数</span>
            </div>
            <div className="flex flex-col items-center p-4 bg-muted rounded-lg">
              <Zap className="h-6 w-6 mb-2 text-primary" />
              <span className="text-2xl font-bold">{formatTokens(usageStats?.this_month_tokens || 0)}</span>
              <span className="text-xs text-muted-foreground">本月 Tokens</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

### 12.5 `frontend/src/pages/NotFoundPage.tsx`

**功能描述**：404 页面。

```typescript
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FileQuestion } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <FileQuestion className="h-16 w-16 text-muted-foreground" />
      <h1 className="text-2xl font-bold">页面不存在</h1>
      <p className="text-muted-foreground">您访问的页面不存在或已被删除</p>
      <Button onClick={() => navigate('/chat')}>返回首页</Button>
    </div>
  );
}
```

---

## 13. 路由配置

### 13.1 `frontend/src/config/routes.ts`

**功能描述**：路由路径常量定义。

```typescript
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  CALLBACK: '/callback',
  CHAT: '/chat',
  CHAT_DETAIL: '/chat/:id',
  SETTINGS: '/settings',
  PROFILE: '/profile',
  NOT_FOUND: '*',
} as const;

export const PUBLIC_ROUTES = [ROUTES.LOGIN, ROUTES.CALLBACK];
```

---

### 13.2 `frontend/src/App.tsx`

**功能描述**：应用根组件，配置路由。

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { LoginPage } from '@/pages/LoginPage';
import { ChatPage } from '@/pages/ChatPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { ProfilePage } from '@/pages/ProfilePage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { ToastProvider } from '@/components/common/Toast';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { ROUTES } from '@/config/routes';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
          <Route path={ROUTES.CALLBACK} element={<LoginPage />} />
          <Route
            path={ROUTES.HOME}
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to={ROUTES.CHAT} replace />} />
            <Route path={ROUTES.CHAT} element={<ChatPage />} />
            <Route path={ROUTES.CHAT_DETAIL} element={<ChatPage />} />
            <Route path={ROUTES.SETTINGS} element={<SettingsPage />} />
            <Route path={ROUTES.PROFILE} element={<ProfilePage />} />
          </Route>
          <Route path={ROUTES.NOT_FOUND} element={<NotFoundPage />} />
        </Routes>
        <ToastProvider />
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
```

---

## 14. 入口文件

### 14.1 `frontend/src/main.tsx`

**功能描述**：应用入口文件。

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

### 14.2 `frontend/src/index.css`

**功能描述**：全局样式入口，包含 Tailwind 指令和 CSS 变量。

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

---

## 15. 附录

### 15.1 开发命令

```bash
# 安装依赖
cd frontend && npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

### 15.2 环境变量检查清单

| 变量 | 开发环境 | 生产环境 |
|------|----------|----------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | `https://api.astra.jppwl.asia` |
| `VITE_APP_ENV` | `development` | `production` |
| `VITE_LOGTO_ENDPOINT` | `https://auth.jppwl.asia` | `https://auth.jppwl.asia` |
| `VITE_LOGTO_APP_ID` | `dev-app-id` | `prod-app-id` |
| `VITE_LOGTO_REDIRECT_URI` | `http://localhost:5173/callback` | `https://astra.jppwl.asia/callback` |

---

> **文档维护**：本文档随项目演进持续更新，重大变更需版本号升级。  
> **反馈渠道**：直接在本文档下方留言，或联系 Leona。
