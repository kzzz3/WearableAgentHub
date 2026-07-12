# 系统架构设计

## 1. 架构总览

WearableAgent Hub 采用 **前后端分离 + 多协议网关** 的架构。所有组件在 PC 本地单机运行。

```
┌─────────────────────────────────────────────────────────────────┐
│                        PC 本地环境                               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  眼镜模拟器   │  │  手表模拟器   │  │  Agent 管理面板      │  │
│  │  (HUD View)  │  │  (WatchFace) │  │  (Dashboard)         │  │
│  │  :5173       │  │  :5174       │  │  :5175               │  │
│  │  A2UI 渲染器  │  │  A2UI 渲染器  │  │  Agent 注册/监控     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └────────┬────────┘                      │              │
│                  │ WebSocket                     │              │
│                  ▼                               │              │
│  ┌───────────────────────────────────────────────┴───────────┐  │
│  │                  FastAPI Backend (:8000)                    │  │
│  │                                                            │  │
│  │  ┌─────────────┐  ┌───────────────┐  ┌─────────────────┐  │  │
│  │  │ AgentEngine  │  │ A2A Server    │  │ WebSocket Mgr   │  │  │
│  │  │ (LLM调用)    │  │ (JSON-RPC)    │  │ (连接管理)       │  │  │
│  │  └──────┬──────┘  └───────┬───────┘  └────────┬────────┘  │  │
│  │         │                 │                    │           │  │
│  │         ▼                 ▼                    │           │  │
│  │  ┌─────────────┐  ┌───────────────┐           │           │  │
│  │  │ A2UIGenerator│  │ AgentExecutor │           │           │  │
│  │  │ (JSON生成)   │  │ (任务执行)     │           │           │  │
│  │  └─────────────┘  └───────┬───────┘           │           │  │
│  │                           │                    │           │  │
│  │                           ▼                    │           │  │
│  │                  ┌─────────────────┐           │           │  │
│  │                  │ InMemoryTaskStore│           │           │  │
│  │                  │ (任务存储)       │           │           │  │
│  │                  └─────────────────┘           │           │  │
│  └──────────────────────────┬─────────────────────┘           │  │
│                             │                                 │  │
│                    ┌────────┴────────┐                        │  │
│                    │  A2A Client     │                        │  │
│                    │  (调用外部Agent)  │                        │  │
│                    └────────┬────────┘                        │  │
│                             │                                 │  │
└─────────────────────────────┼─────────────────────────────────┘
                              │ A2A JSON-RPC /a2a
                              ▼
              ┌───────────────────────────────┐
              │     外部 Agent 进程            │
              │  ┌──────────┐ ┌──────────┐    │
              │  │ 翻译Agent │ │ 导航Agent │    │
              │  │ :8001    │ │ :8003    │    │
              │  └──────────┘ └──────────┘    │
              │  ┌──────────┐                 │
              │  │ 支付Agent │                 │
              │  │ :8004    │                 │
              │  └──────────┘                 │
              └───────────────────────────────┘

              ┌───────────────────────────────┐
              │  x402 支付微服务 (:8002)       │
              │  TypeScript / Hono            │
              │  Mock 钱包 + 模拟支付流程      │
              └───────────────────────────────┘
```

---

## 2. 模块职责

### 2.1 核心后端 (packages/core)

**技术**: Python 3.13 + FastAPI + a2a-sdk v1.1.0

**职责**:
- 接收前端 WebSocket 消息，调度 AgentEngine 处理
- 调用 LLM（OpenAI 兼容接口）理解用户意图
- 检测 A2A 意图，通过 A2AClientWrapper 调用远程 Agent
- 检测支付意图，通过 X402Client 调用 x402 服务
- 生成 A2UI JSON 消息，通过 WebSocket 推送到前端
- 提供 A2A Server 端点（`/a2a` + `/.well-known/agent-card.json`）
- 提供语音 WebSocket 端点（`/voice/{session_id}`）

**关键文件**:
```
packages/core/src/
├── main.py                  # FastAPI 入口，lifespan 挂载所有路由
├── config.py                # pydantic-settings，加载 .env
├── engine/
│   └── agent_engine.py      # 意图检测 + LLM 调用 + A2A/x402 委派
├── a2a/
│   ├── executor.py          # WearableAgentExecutor(AgentExecutor)
│   ├── server_routes.py     # mount_a2a_routes(app, executor)
│   └── client_wrapper.py    # A2AClientWrapper（protobuf WhichOneof）
├── x402/
│   ├── client.py            # HTTP 客户端调用 x402-pay 服务
│   └── routes.py            # x402 FastAPI 路由
├── voice/
│   └── routes.py            # /voice/{session_id} WebSocket
├── a2ui/
│   └── generator.py         # A2UIGenerator
└── ws/
    └── manager.py           # WebSocket 连接管理器
```

### 2.2 A2UI 渲染器 (packages/a2ui-renderer)

**技术**: React + TypeScript

**职责**:
- 解析 A2UI JSON 消息，渲染为穿戴设备风格 UI 组件
- 提供 A2UIRenderer 主组件和子组件（HudCard, HudList, HudStatusBar, HudText）
- 供眼镜模拟器和手表模拟器共用

### 2.3 x402 支付服务 (packages/x402-pay)

**技术**: TypeScript + Hono

**职责**:
- 独立微服务运行在端口 8002
- 管理 Mock 钱包（user / translator / navigator）
- 提供 3 个付费服务（translate / premium-nav / health-analysis）
- 实现完整支付流程：request → verify → settle → pay-and-settle
- 记录支付历史

### 2.4 语音模块 (packages/voice)

**技术**: React Hook + WebSocket

**职责**:
- `useVoiceSession` Hook 管理语音 WebSocket 连接
- 处理语音转写和 Agent 回复
- 集成到眼镜模拟器的 VoiceButton

### 2.5 眼镜模拟器 (apps/glasses-sim)

**技术**: React 19 + Vite + Tailwind + Zustand

**职责**:
- 模拟 AI 眼镜 HUD 界面（400×600 风格）
- WebSocket 连接后端，发送文字/语音输入
- A2UIRenderer 渲染 HUD 组件
- MessageBubble 显示聊天历史
- VoiceButton 语音输入
- PaymentStatus 支付状态展示

**状态管理（Zustand）**：
```typescript
interface HudState {
  connected: boolean;           // WebSocket 连接状态
  messages: A2UIMessage[];      // A2UI 消息列表
  history: ChatEntry[];         // 聊天历史
  isProcessing: boolean;        // Agent 处理中标志
}
```

### 2.6 手表模拟器 (apps/watch-sim)

**技术**: React 19 + Vite + Tailwind

**职责**:
- 模拟 AI 手表表盘（280×280 圆形）
- WatchFace、TimeDisplay、HealthWidget、MiniInput、MiniMessage 组件
- WebSocket 连接后端

### 2.7 管理面板 (apps/dashboard)

**技术**: React 19 + Vite + Tailwind + recharts

**职责**:
- Overview：实时任务计数、Agent 状态概览
- Payments：支付记录和金额统计
- Agents：已注册 Agent 列表
- Logs：实时日志流

### 2.8 示例 Agent (examples/)

**技术**: Python + a2a-sdk

**职责**:
- translate-agent (8001)：字典翻译，A2A Executor
- nav-agent (8003)：位置搜索
- pay-agent (8004)：付费服务演示

---

## 3. 数据流

### 3.1 文字问答链路

```
用户在眼镜模拟器输入 "附近有什么咖啡店"
    ↓
ChatInput.onSend("附近有什么咖啡店")
    ↓
useWebSocket.sendMessage()
    ↓ WebSocket.send(text)
    ↓
FastAPI /ws/{session_id} 接收
    ↓
AgentEngine.process(text, session_id)
    ↓ OpenAI Chat API
    ↓ LLM 返回 JSON: {"type": "location_list", "title": "Nearby Cafes", ...}
    ↓
A2UIGenerator.generate(structured_data)
    ↓ 生成 A2UI 消息序列
    ↓
WebSocketManager.send_a2ui(session_id, messages)
    ↓
前端 A2UIRenderer 渲染
    ↓
HUD 上显示咖啡店列表卡片
```

### 3.2 A2A Agent 通信链路

```
用户在眼镜输入 "translate Hello World"
    ↓
AgentEngine.process() → _detect_a2a_intent() 正则匹配 "translate"
    ↓
A2AClientWrapper → A2ACardResolver 获取翻译 Agent 的 AgentCard
    ↓
client.send_message(SendMessageRequest) → A2A JSON-RPC POST /a2a
    ↓
翻译 Agent 的 A2A Server 接收
    ↓ AgentExecutor.execute(context, event_queue)
    ↓ TaskUpdater.start_work() → TaskUpdater.complete(artifact=翻译结果)
    ↓
返回 Task(status=COMPLETED, artifacts=[翻译结果])
    ↓
主 Agent 收到翻译结果
    ↓
A2UIGenerator → WebSocket → HUD 显示翻译结果
```

### 3.3 x402 付费链路

```
用户请求 "translate 你好世界 to English"
    ↓
AgentEngine → _detect_payment_intent() 检测支付意图
    ↓
X402Client.pay_and_settle() → POST http://localhost:8002/pay-and-settle
    ↓
x402 服务：Mock 钱包扣款 → 模拟结算 → 返回交易回执
    ↓
支付结果附加到回复
    ↓
PaymentStatus 组件显示支付金额和交易 ID
    ↓ MessageBubble 显示绿色支付成功标记
```

---

## 4. 通信协议设计

### 4.1 前端 ↔ 后端（WebSocket）

| 连接方式 | 用途 | 格式 |
|---------|------|------|
| WebSocket | A2UI 流式渲染 | JSON（A2UI 消息） |
| WebSocket | 聊天消息 | 纯文本 |
| HTTP REST | Agent 管理 | JSON |
| WebSocket | 语音交互 | JSON（transcript/reply/a2ui） |

### 4.2 后端 ↔ 外部 Agent（A2A）

| 端点 | 方法 | 协议 |
|------|------|------|
| `/.well-known/agent-card.json` | GET | HTTP |
| `/a2a` | POST | JSON-RPC 2.0 |

### 4.3 后端 ↔ x402 服务（HTTP）

| 端点 | 方法 | 说明 |
|------|------|------|
| `POST /pay` | POST | 发起支付 |
| `GET /payments/:id` | GET | 查询支付状态 |
| `GET /wallets` | GET | 查询钱包余额 |
| `POST /pay-and-settle` | POST | 一键支付结算 |
| `GET /services` | GET | 查询可用服务 |

---

## 5. 部署架构

**单机部署（开发/演示）**：

```
┌─ Python 进程 ──────────────────────┐
│  FastAPI (后端 :8000)                │
│  ├── WebSocket (/ws/{session_id})   │
│  ├── A2A Server (/a2a)              │
│  ├── Agent Card                     │
│  │   (/.well-known/agent-card.json) │
│  ├── Voice (/voice/{session_id})    │
│  └── REST API (/chat, /health)      │
└────────────────────────────────────┘

┌─ Python 进程 ──────────────────────┐
│  translate-agent (:8001)            │
│  nav-agent (:8003)                  │
│  pay-agent (:8004)                  │
└────────────────────────────────────┘

┌─ Node.js 进程 ─────────────────────┐
│  x402 Payment Service (:8002)       │
└────────────────────────────────────┘

┌─ Vite Dev Server ──────────────────┐
│  glasses-sim (:5173)                │
│  watch-sim (:5174)                  │
│  dashboard (:5175)                  │
└────────────────────────────────────┘
```

---

## 6. 安全考虑

| 维度 | 措施 |
|------|------|
| A2A 认证 | Agent Card 中声明 security_schemes |
| x402 安全 | 仅使用 Mock 模拟支付，无私钥风险 |
| 语音数据 | 音频流不持久化，仅在内存中处理 |
| CORS | 开发环境允许 localhost 跨域 |
| API Key | 通过 .env 文件配置，不进代码库 |