# 技术栈详细说明

## 1. 总览

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端 | Python + FastAPI | 3.13 (conda `expr`) / 0.135+ | Agent 引擎 + A2A Server |
| 前端 | React + TypeScript + Vite | 18.x / 5.x / 6.x | 穿戴设备 UI 模拟器 |
| 语音 | OpenAI Realtime API | 2024-12-17 | 实时语音交互 |
| A2A | A2A v1.0 + a2a-sdk | 1.0.0 / 0.2.x | Agent 间通信 |
| A2UI | A2UI v0.9.1 | 0.9.1 | 声明式 UI 流式渲染 |
| x402 | @x402/core + a2a-x402 | 0.1.x | HTTP 原生支付结算 |
| MCP | @modelcontextprotocol/sdk | latest | 工具服务集成 |
| 数据库 | SQLite + aiosqlite | 3.x | 开发环境持久化 |
| Monorepo | pnpm workspaces | 9.x | 前端多包管理 |
| Python 环境 | conda `expr` | — | Python 依赖与虚拟环境 |

---

## 2. Python 环境

### 2.1 conda `expr` 环境

本项目 Python 端统一使用 conda 的 `expr` 环境，不使用 `uv` 或系统 Python。

**环境信息**:
- **环境名**: `expr`
- **Python 版本**: 3.13.12
- **激活方式**: `conda activate expr`

**已安装的核心依赖**（无需重复安装）:

| 包名 | 版本 | 用途 |
|------|------|------|
| `fastapi` | 0.135.3 | Web 框架 |
| `uvicorn` | 0.43.0 | ASGI 服务器 |
| `openai` | 2.28.0 | LLM + Realtime API |
| `pydantic` | 2.12.5 | 数据验证 |
| `pydantic-settings` | 2.14.2 | 配置管理 |
| `httpx` | 0.28.1 | 异步 HTTP 客户端 |
| `aiohttp` | 3.13.5 | 异步 HTTP（辅助） |
| `websockets` | 16.0 | WebSocket 支持 |
| `alembic` | 1.18.4 | 数据库迁移 |
| `ruff` | 0.15.21 | 代码格式化 + lint |
| `mypy` | 2.2.0 | 类型检查 |
| `pytest` | 9.1.1 | 测试框架 |
| `pytest-asyncio` | 1.4.0 | 异步测试 |
| `pytest-cov` | 7.1.0 | 覆盖率 |

**仍需安装的依赖**:

```bash
conda activate expr
pip install a2a-sdk aiosqlite python-dotenv
```

### 2.2 所有 Python 命令的统一前缀

```bash
# 运行后端
conda run -n expr uvicorn src.main:app --reload --port 8000

# 运行测试
conda run -n expr pytest

# 类型检查
conda run -n expr mypy src/

# 代码格式化
conda run -n expr ruff format src/

# 代码检查
conda run -n expr ruff check src/
```

---

## 3. 后端技术栈

### 3.1 Python 3.13

**选择理由**:
- A2A 官方 Python SDK (`a2a-sdk`) 是最成熟的 A2A 实现
- 用户本地已有 conda `expr` 环境（Python 3.13），依赖齐全
- Python 3.13 提供 `TaskGroup`、`ExceptionGroup` 等结构化并发原语
- FastAPI + Pydantic v2 生态与 A2A 的 JSON-RPC 数据模型天然契合

**关键特性使用**:
- `asyncio.TaskGroup` — 并行派发多 Agent 请求
- `typing.Annotated` — FastAPI 依赖注入类型标注
- `dataclasses` / `pydantic.BaseModel` — A2A 数据模型定义

### 3.2 FastAPI 0.135+

**选择理由**:
- 原生支持 WebSocket（前端 ↔ 后端实时通信）
- 原生支持 SSE（A2A streaming 响应）
- 自动 OpenAPI 文档生成（调试友好）
- `Depends()` 系统适合注入 LLM Client、Agent Registry 等单例

**路由规划**:

| 路由前缀 | 用途 | 协议 |
|---------|------|------|
| `/a2a` | A2A JSON-RPC 2.0 端点 | HTTP POST + SSE |
| `/.well-known/agent.json` | Agent Card 发现 | HTTP GET |
| `/ws` | 前端 WebSocket 连接 | WebSocket |
| `/voice` | 语音流式接口 | WebSocket |
| `/agents` | Agent 管理 REST API | HTTP |
| `/tasks` | Task 查询 API | HTTP |
| `/health` | 健康检查 | HTTP GET |

### 3.3 a2a-sdk (PyPI)

**包名**: `a2a-sdk`
**版本**: `>=0.2.0,<1.0`
**用途**: A2A v1.0 协议的官方 Python 实现

**提供的核心能力**:
- `A2AServer` — 快速搭建 A2A 兼容服务端
- `A2AClient` — 调用其他 A2A Agent
- `AgentCard` — Agent Card 数据模型
- `Task` / `TaskState` — Task 生命周期管理
- `Message` / `Part` — 消息和内容片段模型
- JSON-RPC 2.0 请求/响应序列化
- SSE 流式传输支持

**使用方式**:

```python
from a2a.server import A2AServer, AgentCard
from a2a.types import Task, Message, TextPart

# 定义 Agent Card
card = AgentCard(
    name="WearableHub Agent",
    description="穿戴设备 AI Agent",
    url="http://localhost:8000/a2a",
    version="0.1.0",
    capabilities={"streaming": True},
    skills=[...],
)

# 创建 Server
server = A2AServer(agent_card=card, task_handler=my_handler)
```

**注意事项**:
- SDK 仍在快速迭代，需锁定版本号
- 部分高级特性（Push Notifications）可能未完整实现
- 需关注 `CHANGELOG.md` 中的 breaking changes

### 3.4 OpenAI Python SDK

**包名**: `openai`
**版本**: `2.28.0`（已安装）
**用途**: LLM 推理 + Realtime API 语音

**使用场景**:
- `openai.OpenAI().chat.completions.create()` — 非实时 LLM 推理（MVP 阶段）
- `openai.AsyncOpenAI().beta.realtime.connect()` — Realtime API 语音会话（Phase 4）
- Function Calling — 意图解析 + 工具调用

### 3.5 其他 Python 依赖

| 包名 | 版本 | 状态 | 用途 |
|------|------|------|------|
| `uvicorn[standard]` | 0.43.0 | ✅ 已安装 | ASGI 服务器 |
| `pydantic` | 2.12.5 | ✅ 已安装 | 数据验证和序列化 |
| `pydantic-settings` | 2.14.2 | ✅ 已安装 | 配置管理 |
| `websockets` | 16.0 | ✅ 已安装 | WebSocket 支持 |
| `httpx` | 0.28.1 | ✅ 已安装 | 异步 HTTP 客户端 |
| `aiosqlite` | — | ❌ 需安装 | 异步 SQLite |
| `python-dotenv` | — | ❌ 需安装 | 环境变量管理 |
| `a2a-sdk` | — | ❌ 需安装 | A2A 协议 SDK |
| `ruff` | 0.15.21 | ✅ 已安装 | 代码格式化 + lint |
| `mypy` | 2.2.0 | ✅ 已安装 | 类型检查 |
| `pytest` | 9.1.1 | ✅ 已安装 | 测试框架 |
| `pytest-asyncio` | 1.4.0 | ✅ 已安装 | 异步测试支持 |
| `alembic` | 1.18.4 | ✅ 已安装 | 数据库迁移 |

---

## 4. 前端技术栈

### 4.1 React 18

**选择理由**:
- A2UI 官方提供 React 渲染器参考实现
- `Suspense` + `useDeferredValue` 适合流式 UI 更新
- 生态成熟，组件库丰富

**关键特性使用**:
- `useSyncExternalStore` — 订阅 A2UI 数据模型变更
- `useTransition` — A2UI 渐进式渲染不阻塞交互
- `ErrorBoundary` — 渲染错误隔离

### 4.2 TypeScript 5.x (strict mode)

**配置要点**:
- `strict: true` — 全部严格检查
- `noUncheckedIndexedAccess` — 数组/对象索引安全
- `verbatimModuleSyntax` — ESM 导入导出一致性
- 路径别名: `@wearable/core`, `@wearable/a2ui-renderer`, `@wearable/voice`

### 4.3 Vite 6

**选择理由**:
- 原生 ESM 开发服务器，HMR 亚秒级
- 多页面应用支持（glasses-sim、watch-sim、dashboard 并行开发）
- 插件生态成熟（`@vitejs/plugin-react`）

**配置要点**:
- 开发服务器代理: `/api` → FastAPI, `/ws` → WebSocket
- 构建产物: 各 app 独立输出到 `dist/`
- 环境变量: `VITE_*` 前缀

### 4.4 状态管理: Zustand

**选择理由**:
- 极简 API，无 Provider 包裹
- 天然支持 `useSyncExternalStore`（与 A2UI 数据模型对接方便）
- 中间件支持（`devtools`, `persist`）
- 包体积极小（~1KB）

**Store 规划**:

| Store | 职责 |
|-------|------|
| `useAgentStore` | Agent 连接状态、当前活跃 Agent |
| `useA2UIStore` | A2UI Surface/组件树/数据模型 |
| `useVoiceStore` | 语音录制状态、音频波形数据 |
| `usePaymentStore` | 支付状态、交易记录 |

### 4.5 样式方案: Tailwind CSS + CSS Modules

- **Tailwind CSS 3.x** — 快速原型开发，HUD/表盘的半透明、模糊效果
- **CSS Modules** — 组件级样式隔离（A2UI 渲染器组件）
- **CSS Variables** — 主题系统（暗色 HUD、亮色表盘）

### 4.6 其他前端依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| `react-router` | 6.x | Dashboard 页面路由 |
| `@tanstack/react-query` | 5.x | REST API 数据获取 + 缓存 |
| `framer-motion` | 11.x | HUD 动画（渐入渐出、卡片翻转） |
| `lucide-react` | latest | 图标库 |
| `recharts` | 2.x | Dashboard 图表（Agent 通信统计） |
| `zod` | 3.x | A2UI JSON Schema 运行时验证 |
| `vitest` | 2.x | 单元测试（dev） |
| `playwright` | 1.x | E2E 测试（dev） |
| `eslint` | 9.x | 代码规范（dev） |
| `prettier` | 3.x | 代码格式化（dev） |

---

## 5. 协议技术栈

### 5.1 A2A v1.0

**规范**: [a2aproject/A2A](https://github.com/a2aproject/A2A) (24.7k⭐)
**版本锁定**: v1.0.0
**协议基础**: JSON-RPC 2.0

**核心概念**:
- **Agent Card** — Agent 自描述元数据（名称、能力、技能、端点）
- **Task** — 有状态的任务单元（生命周期: submitted → working → input-required → completed / failed / canceled）
- **Message** — 任务内的消息（role: user/agent, parts: text/file/data）
- **Part** — 消息内容片段（TextPart, FilePart, DataPart）
- **Artifact** — Agent 产出物（文件、数据等）

**本项目使用的方法**:
| 方法 | 用途 |
|------|------|
| `message/send` | 同步发送消息（等待结果） |
| `message/stream` | SSE 流式发送消息 |
| `tasks/get` | 查询 Task 状态 |
| `tasks/cancel` | 取消 Task |

**SDK**: `a2a-sdk` (Python, PyPI)

### 5.2 A2UI v0.9.1

**规范**: [a2ui-project/a2ui](https://github.com/a2ui-project/a2ui)
**版本锁定**: v0.9.1
**协议性质**: 声明式 JSON 流式 UI 协议

**四种消息类型**:
| 消息类型 | 作用 | 触发时机 |
|---------|------|---------|
| `createSurface` | 创建 UI 区域（Surface） | Agent 开始输出 |
| `updateComponents` | 更新组件树 | Agent 输出内容 |
| `updateDataModel` | 更新数据绑定 | 数据变更 |
| `deleteSurface` | 销毁 UI 区域 | 会话结束 / 超时 |

**Surface 呈现模式**:
- `card` — 信息卡片（眼镜 HUD 主要模式）
- `panel` — 面板（手表数据面板）
- `overlay` — 浮层（通知、弹窗）
- `fullscreen` — 全屏（地图、图片查看）

**穿戴设备自定义组件**:

| 组件 | A2UI 类型 | 属性 | 适用 |
|------|----------|------|------|
| HudCard | `container` | title, subtitle, icon | 眼镜 |
| WatchFace | `container` | layout, widgets | 手表 |
| MiniMap | `map` | center, zoom, markers | 眼镜 |
| GlanceWidget | `container` | metric, value, unit | 手表 |
| VoiceWaveform | `canvas` | audioData, color | 通用 |
| StatusBar | `container` | battery, signal, time | 通用 |

**SDK**:
- Agent 端: Python `a2ui-agent-sdk`（生成 A2UI JSON）
- 渲染端: 自研 React 渲染器（参考官方 `a2ui-react`）

### 5.3 x402

**规范**: [x402-foundation/x402](https://github.com/x402-foundation/x402) (6.3k⭐)
**版本锁定**: v0.1+
**协议性质**: HTTP 原生支付协议

**支付流程**:
```
Client → GET /api/resource → Server (402 Payment Required)
Client → POST /api/resource + Payment Header → Server (200 OK + Data)
```

**A2A 扩展**: [google-agentic-commerce/a2a-x402](https://github.com/google-agentic-commerce/a2a-x402) (536⭐)
- 在 A2A Task 中嵌入 x402 支付需求
- `payment-required` 状态表示需要支付
- 自动签名 + 提交支付

**SDK**:
| 语言 | 包名 | 用途 |
|------|------|------|
| TypeScript | `@x402/core` | 核心支付逻辑 |
| TypeScript | `a2a-x402` | A2A 扩展 |
| Python | `x402-python` | Python 客户端（辅助） |

**网络配置**:
- 测试网: Base Sepolia
- 代币: USDC (ERC-20)
- RPC: `https://sepolia.base.org`
- 水龙头: [Base Sepolia Faucet](https://www.alchemy.com/faucets/base-sepolia)

### 5.4 MCP (Model Context Protocol)

**规范**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
**用途**: 连接外部工具服务（地图、翻译、天气等）

**传输方式**:
- `stdio` — 本地 MCP Server（子进程）
- `SSE` — 远程 MCP Server（HTTP）

**集成方式**:
- 后端作为 MCP Client，通过 `@modelcontextprotocol/sdk` (Node.js) 或 Python MCP SDK 连接
- 将 MCP 工具注册为 Agent 的 Function Calling 工具
- x402 支付也可以作为 MCP 工具暴露

**本项目 MCP 工具规划**:
| 工具名 | 说明 | 来源 |
|--------|------|------|
| `maps_search` | 地点搜索 | 外部 MCP Server |
| `weather_current` | 当前天气 | 外部 MCP Server |
| `translate_text` | 文本翻译 | 示例 MCP Server |
| `health_data` | 健康数据查询 | 模拟 MCP Server |

---

## 6. 基础设施

### 6.1 包管理

| 环境 | 工具 | 说明 |
|------|------|------|
| TypeScript | pnpm 9.x workspaces | Monorepo 多包管理 |
| Python | conda `expr` 环境 | 统一 Python 环境管理 |
| 根目录 | pnpm-workspace.yaml | 声明 TS 包的工作区范围 |
| Python 根 | pyproject.toml (各包独立) | 每个 Python 包独立 pyproject.toml |

**Monorepo 结构**:
```
wearable-agent-hub/
├── package.json              # root: devDependencies (eslint, prettier)
├── pnpm-workspace.yaml       # packages/*, apps/*
├── packages/
│   ├── core/                 # Python (conda expr)
│   ├── a2a-server/           # Python (conda expr)
│   ├── a2ui-renderer/        # TS: package.json (pnpm)
│   ├── x402-pay/             # TS: package.json (pnpm)
│   └── voice/                # TS: package.json (pnpm)
├── apps/
│   ├── glasses-sim/          # TS: package.json (pnpm)
│   ├── watch-sim/            # TS: package.json (pnpm)
│   └── dashboard/            # TS: package.json (pnpm)
└── examples/
    ├── translate-agent/      # Python (conda expr)
    ├── nav-agent/            # Python (conda expr)
    └── pay-agent/            # Python (conda expr)
```

### 6.2 数据库

**选择**: SQLite（开发阶段）
- 零配置，单文件数据库
- `aiosqlite` 提供异步支持
- 足够支撑开发和演示场景

**迁移工具**: `alembic`（已安装，如需要）

**升级路径**: 生产环境可切换为 PostgreSQL（仅需修改连接字符串）

### 6.3 跨语言通信

**Python ↔ TypeScript 桥接方案**:

| 场景 | 方案 | 说明 |
|------|------|------|
| 后端调用 x402 支付 | HTTP REST | Python → x402 TS 服务 (:8001) |
| 前端调用后端 | WebSocket + REST | React → FastAPI (:8000) |
| Agent 间通信 | A2A JSON-RPC | 标准协议，语言无关 |

**x402 TypeScript 微服务**:
- 独立进程，监听 `:8001`
- 暴露 REST API: `POST /pay`, `GET /payments/:id`, `GET /wallet/balance`
- Python 后端通过 `httpx` 调用

### 6.4 开发工具

| 工具 | 用途 | 配置文件 |
|------|------|---------|
| ESLint 9.x | TS 代码规范 | `eslint.config.js` |
| Prettier 3.x | 代码格式化 | `.prettierrc` |
| ruff | Python lint + format | `ruff.toml` |
| mypy | Python 类型检查 | `mypy.ini` |
| husky | Git hooks | `.husky/` |
| lint-staged | 提交时检查 | `lint-staged.config.js` |
| commitlint | 提交信息规范 | `commitlint.config.js` |

---

## 7. 版本兼容性矩阵

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Node.js | 20.0 | 22.x LTS | ESM + WebSocket 原生支持 |
| pnpm | 9.0 | 9.x | workspace 协议支持 |
| Python | 3.13 | 3.13 (conda expr) | 用户指定环境 |
| Chrome | 120 | latest | WebAudio API + WebSocket |
| 浏览器 | — | Chrome/Edge | 不支持 Firefox（WebAudio 限制） |

---

## 8. 依赖安全与风险

### 8.1 已知风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| `a2a-sdk` API 不稳定 | 代码返工 | 锁定版本，写适配层隔离变化 |
| A2UI 规范仍在演进 | 渲染器适配 | 自研渲染器，仅实现需要的子集 |
| x402 测试网水龙头限流 | 测试受阻 | 实现 mock 支付模式 |
| OpenAI API 限流 | 语音体验下降 | 实现退避重试 + Chat API 降级 |
| pnpm + conda 混合工具链 | 环境管理复杂 | 文档化各包的启动/构建命令 |

### 8.2 许可证

| 依赖 | 许可证 | 兼容性 |
|------|--------|--------|
| a2a-sdk | Apache 2.0 | ✅ |
| A2UI | Apache 2.0 | ✅ |
| x402 | MIT | ✅ |
| React | MIT | ✅ |
| FastAPI | MIT | ✅ |
| OpenAI SDK | Apache 2.0 | ✅ |