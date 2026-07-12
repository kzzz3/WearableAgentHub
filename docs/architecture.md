# 系统架构设计

## 1. 架构总览

WearableAgent Hub 采用 **前后端分离 + 多协议网关** 的架构模式。后端作为 Agent 服务中枢，负责协议转换和 Agent 编排；前端模拟穿戴设备的 HUD 交互界面。

`
┌─────────────────────────────────────────────────────────────────┐
│                        PC 本地环境                               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  眼镜模拟器   │  │  手表模拟器   │  │  Agent 管理面板      │  │
│  │  (HUD View)  │  │  (WatchFace) │  │  (Dashboard)         │  │
│  │              │  │              │  │                      │  │
│  │  A2UI 渲染器  │  │  A2UI 渲染器  │  │  Agent 注册/监控     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └────────┬────────┘                      │              │
│                  │ WebSocket / SSE               │              │
│                  ▼                               │              │
│  ┌───────────────────────────────────────────────┴───────────┐  │
│  │                    API Gateway (FastAPI)                    │  │
│  │                                                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ 语音服务  │  │ A2A 路由  │  │ x402 网关 │  │ MCP 桥接 │  │  │
│  │  │ /voice   │  │ /a2a     │  │ /pay     │  │ /mcp     │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │  │
│  │       │              │             │             │         │  │
│  └───────┼──────────────┼─────────────┼─────────────┼─────────┘  │
│          │              │             │             │            │
│          ▼              ▼             ▼             ▼            │
│  ┌──────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ OpenAI       │ │ Agent     │ │ x402     │ │ MCP Server   │  │
│  │ Realtime API │ │ Registry  │ │ Payment  │ │ Connections  │  │
│  │              │ │ (A2A)     │ │ Engine   │ │              │  │
│  └──────────────┘ └─────┬─────┘ └──────────┘ └──────────────┘  │
│                         │                                       │
│                         ▼ A2A JSON-RPC / SSE                   │
│              ┌─────────────────────┐                            │
│              │  外部 Agent 服务     │                            │
│              │  (翻译/导航/支付...)  │                            │
│              └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
`

## 2. 核心模块详解

### 2.1 Agent 核心引擎 (packages/core)

**职责**: Agent 生命周期管理、消息路由、协议适配

`
core/
├── engine/
│   ├── agent_registry.py    # Agent 注册与发现
│   ├── task_manager.py      # A2A Task 生命周期管理
│   ├── message_router.py    # 消息路由与分发
│   └── context_store.py     # 会话上下文存储
├── protocols/
│   ├── a2a_adapter.py       # A2A 协议适配层
│   ├── a2ui_bridge.py       # A2UI JSON 生成桥接
│   └── x402_gateway.py      # x402 支付网关
├── llm/
│   ├── openai_client.py     # OpenAI API 封装
│   └── prompt_templates.py  # 提示词模板
├── mcp/
│   ├── mcp_client.py        # MCP 客户端
│   └── tool_registry.py     # MCP 工具注册
└── main.py                  # FastAPI 入口
`

**核心流程**:

`python
# 伪代码：语音输入 → Agent 处理 → A2UI 输出
async def handle_voice_input(audio_stream):
    # 1. 语音转文字
    text = await speech_to_text(audio_stream)

    # 2. LLM 理解意图，决定是否需要调用其他 Agent
    intent = await llm.parse_intent(text)

    if intent.needs_agent_call:
        # 3a. 通过 A2A 协议调用远程 Agent
        task = await a2a_client.send_task(
            agent_card=intent.target_agent,
            message=intent.message
        )
        result = await a2a_client.wait_for_result(task.id)
    elif intent.needs_tool:
        # 3b. 通过 MCP 调用工具
        result = await mcp_client.call_tool(intent.tool, intent.params)
    else:
        # 3c. 直接 LLM 回复
        result = await llm.chat(intent.message)

    # 4. 生成 A2UI JSON
    a2ui_messages = await a2ui_bridge.generate_ui(result)

    # 5. 推送到前端渲染
    await ws_manager.broadcast(a2ui_messages)
`

### 2.2 A2A 协议服务端 (packages/a2a-server)

**职责**: 实现 A2A v1.0 协议规范，暴露标准 Agent Card 端点

`
a2a-server/
├── agent_cards/
│   ├── glasses_agent.json     # 眼镜 Agent Card
│   ├── watch_agent.json       # 手表 Agent Card
│   └── hub_agent.json         # 中枢 Agent Card
├── handlers/
│   ├── message_handler.py     # message/send 处理
│   ├── stream_handler.py      # message/stream 处理
│   └── task_handler.py        # task 生命周期处理
├── models/
│   ├── task.py                # Task 数据模型
│   ├── message.py             # Message 数据模型
│   └── artifact.py            # Artifact 数据模型
└── server.py                  # A2A JSON-RPC 服务
`

**A2A 协议关键实现点**:

| A2A 概念 | 实现方式 | 说明 |
|----------|---------|------|
| Agent Card | JSON 文件 + /.well-known/agent.json | 描述 Agent 能力、端点、认证方式 |
| Task | 内存 + SQLite 持久化 | 支持 submitted → working → completed 状态机 |
| Message | JSON-RPC 2.0 | message/send 和 message/stream |
| Part | TextPart / FilePart / DataPart | 支持文本、文件引用、结构化数据 |
| Streaming | SSE (Server-Sent Events) | 实时推送 Task 状态更新 |

**Agent Card 示例**:

`json
{
  "name": "WearableHub Glasses Agent",
  "description": "AI 眼镜模拟器，提供视觉识别和 HUD 显示",
  "url": "http://localhost:8000/a2a",
  "version": "0.1.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "skills": [
    {
      "id": "visual_recognition",
      "name": "视觉识别",
      "description": "识别图像中的物体、文字、人脸"
    },
    {
      "id": "hud_display",
      "name": "HUD 显示",
      "description": "在虚拟 HUD 上渲染信息卡片"
    }
  ],
  "defaultInputModes": ["text", "file"],
  "defaultOutputModes": ["text", "a2ui"]
}
`

### 2.3 A2UI 穿戴端渲染器 (packages/a2ui-renderer)

**职责**: 将 A2UI v0.9.1 JSON 消息渲染为穿戴设备风格的 UI 组件

`
a2ui-renderer/
├── core/
│   ├── surface_manager.ts     # Surface 生命周期管理
│   ├── component_registry.ts  # 组件注册表
│   ├── data_model.ts          # 数据模型绑定
│   └── stream_parser.ts       # JSON 流解析器
├── components/
│   ├── wearable/              # 穿戴设备专用组件
│   │   ├── HudCard.tsx        # HUD 信息卡片
│   │   ├── WatchFace.tsx      # 表盘面板
│   │   ├── MiniMap.tsx        # 迷你地图
│   │   ├── VoiceWaveform.tsx  # 语音波形
│   │   └── GlanceWidget.tsx   # 速览小部件
│   ├── base/                  # A2UI 基础组件
│   │   ├── Card.tsx
│   │   ├── Text.tsx
│   │   ├── Button.tsx
│   │   ├── List.tsx
│   │   └── Image.tsx
│   └── layout/
│       ├── Stack.tsx
│       └── Grid.tsx
├── themes/
│   ├── glasses-dark.ts        # 眼镜深色主题
│   ├── watch-dark.ts          # 手表深色主题
│   └── common.ts              # 共享设计 token
└── hooks/
    ├── useA2UIStream.ts       # A2UI 流连接 Hook
    ├── useSurface.ts          # Surface 管理 Hook
    └── useDataBinding.ts      # 数据绑定 Hook
`

**A2UI 消息处理流程**:

`
Server → createSurface → updateComponents → updateDataModel → deleteSurface
                                         ↓
                                    SurfaceManager
                                         ↓
                                    ComponentRegistry
                                         ↓
                                    React 渲染树
                                         ↓
                                    穿戴设备 UI
`

**渲染器关键设计**:

1. **Surface 管理**: 每个 HUD 区域对应一个 A2UI Surface（主视图、侧边栏、通知栏）
2. **组件目录**: 预注册穿戴设备风格组件（HUD Card、Watch Face、Glance Widget）
3. **数据绑定**: 支持 A2UI 的 dataModel 路径引用，实现动态数据更新
4. **流式渲染**: 解析 JSON 流，逐条处理 createSurface / updateComponents / updateDataModel 消息
5. **主题系统**: 针对不同穿戴设备（眼镜/手表）提供差异化主题

### 2.4 x402 支付模块 (packages/x402-pay)

**职责**: 实现 Agent 间的 x402 支付结算

`
x402-pay/
├── core/
│   ├── payment_flow.ts        # 支付流程编排
│   ├── wallet_manager.ts      # 钱包管理（测试网）
│   └── settlement.ts          # 链上结算
├── middleware/
│   ├── a2a_payment_middleware.ts  # A2A 支付中间件
│   └── price_calculator.ts       # 动态定价
├── models/
│   ├── payment_request.ts     # 支付请求模型
│   └── payment_receipt.ts     # 支付凭证模型
└── utils/
    └── x402_utils.ts          # x402 工具函数
`

**x402 支付流程**:

`
Client Agent                    Merchant Agent
     │                               │
     │─── message/send ─────────────→│
     │                               │ (计算价格)
     │←── payment-required ──────────│
     │                               │
     │ (签名支付)                     │
     │─── payment-submitted ────────→│
     │                               │ (验证 + 链上结算)
     │←── payment-completed ─────────│
     │                               │
     │←── 返回结果 + Artifact ───────│
`

**技术选型**: 使用 @x402/core (TypeScript) 处理支付协议，2a-x402 处理 A2A 扩展。Python 后端通过子进程或 HTTP 调用 TypeScript 支付服务。

### 2.5 语音交互模块 (packages/voice)

**职责**: 实时语音输入/输出，对接 OpenAI Realtime API

`
voice/
├── client/
│   ├── realtime_client.ts     # WebSocket 客户端
│   ├── audio_processor.ts     # 音频采集/播放
│   └── vad.ts                 # 语音活动检测
├── server/
│   ├── voice_service.py       # 语音服务端
│   └── audio_proxy.py         # 音频代理
└── types/
    └── voice_events.ts        # 事件类型定义
`

**语音链路**:

`
麦克风 → Web Audio API → WebSocket → OpenAI Realtime API
                                        ↓
                                   STT + LLM + TTS
                                        ↓
                                   WebSocket → 扬声器
                                        ↓
                                   文字/意图 → Agent 引擎
`

## 3. 数据流架构

### 3.1 最短链路（MVP）

`
用户语音 "附近有什么咖啡店"
    ↓
[语音模块] STT → 文字
    ↓
[Agent 引擎] LLM 意图解析 → 需要调用地图 Agent
    ↓
[A2A 适配] message/send → 外部地图 Agent
    ↓
[A2A 适配] 接收结果（咖啡店列表）
    ↓
[A2UI 桥接] 生成 A2UI JSON
    ↓
[WebSocket] 推送到前端
    ↓
[A2UI 渲染器] 渲染 HUD 卡片
    ↓
用户看到眼镜 HUD 上显示咖啡店列表
`

### 3.2 付费链路

`
用户 "帮我翻译这段话"
    ↓
[Agent 引擎] 需要调用翻译 Agent
    ↓
[A2A 适配] message/send → 翻译 Agent
    ↓
[翻译 Agent] 返回 payment-required（x402）
    ↓
[x402 模块] 签名支付 → payment-submitted
    ↓
[翻译 Agent] 验证支付 → 返回翻译结果
    ↓
[x402 模块] 记录交易
    ↓
[A2UI 桥接] 生成翻译结果 UI
    ↓
前端显示翻译结果 + 支付确认
`

### 3.3 多 Agent 协作链路

`
用户 "帮我识别这个物体并查一下健康数据"
    ↓
[Agent 引擎] 并行派发：
    ├─ [眼镜 Agent] 视觉识别 → A2A
    └─ [手表 Agent] 健康数据 → A2A
    ↓
[Agent 引擎] 合并结果
    ↓
[A2UI 桥接] 生成组合 UI（识别结果 + 健康面板）
    ↓
前端渲染组合 HUD
`

## 4. 通信协议设计

### 4.1 前端 ↔ 后端

| 连接方式 | 用途 | 协议 |
|---------|------|------|
| WebSocket | A2UI 流式渲染 | JSON 流（A2UI 消息） |
| WebSocket | 语音实时传输 | 二进制音频帧 |
| HTTP REST | Agent 管理 API | JSON |

**WebSocket 消息格式**:

`	ypescript
// A2UI 消息通道
interface WSMessage {
  channel: 'a2ui' | 'voice' | 'agent';
  type: string;  // createSurface | updateComponents | updateDataModel | deleteSurface
  payload: any;
}

// 示例
{
  "channel": "a2ui",
  "type": "createSurface",
  "payload": {
    "surfaceId": "hud-main",
    "presentation": { "mode": "card" }
  }
}
`

### 4.2 后端 ↔ 外部 Agent

| 协议 | 端点 | 说明 |
|------|------|------|
| A2A JSON-RPC | /a2a | 标准 A2A 端点 |
| A2A SSE | /a2a/stream | 流式消息 |
| Agent Card | /.well-known/agent.json | Agent 发现 |

### 4.3 后端 ↔ MCP Server

| 协议 | 说明 |
|------|------|
| stdio | 本地 MCP Server |
| SSE | 远程 MCP Server |

## 5. 部署架构

`
单机部署（开发/演示）：

┌─ Node.js 进程 ─────────────────────┐
│  Vite Dev Server (前端)              │
│  ├── glasses-sim (:5173)            │
│  ├── watch-sim (:5174)              │
│  └── dashboard (:5175)              │
└────────────────────────────────────┘

┌─ Python 进程 ──────────────────────┐
│  FastAPI (后端 :8000)                │
│  ├── A2A Server (/a2a)              │
│  ├── Voice Service (/voice)         │
│  ├── WebSocket (/ws)                │
│  └── MCP Client                     │
└────────────────────────────────────┘

┌─ Node.js 进程 ─────────────────────┐
│  x402 Payment Service (:8001)       │
└────────────────────────────────────┘

┌─ 外部 Agent 进程 ──────────────────┐
│  examples/translate-agent (:8010)   │
│  examples/nav-agent (:8011)         │
│  examples/pay-agent (:8012)         │
└────────────────────────────────────┘
`

## 6. 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 后端语言 | Python | A2A 官方 SDK 只有 Python 版本最成熟 |
| 前端框架 | React | A2UI 官方有 React 渲染器可参考 |
| 构建工具 | Vite | 开发体验好，HMR 快 |
| Monorepo | pnpm workspaces | 轻量，TS 原生支持好 |
| 状态管理 | Zustand | 轻量，适合穿戴设备 UI 的简单状态 |
| 样式方案 | Tailwind CSS + CSS Modules | 快速开发 + 组件隔离 |
| 数据库 | SQLite (开发) | 轻量，单文件，无需额外服务 |
| 语音方案 | OpenAI Realtime API | 一体化 STT+LLM+TTS，延迟低 |
| x402 实现 | TypeScript 子进程 | 官方 TS SDK 最完善 |
| 测试网 | Base Sepolia | x402 官方示例使用的网络 |

## 7. 安全考虑

- **A2A 认证**: 使用 API Key 或 OAuth 2.0（Agent Card 中声明）
- **x402 安全**: 仅使用测试网，钱包私钥不进代码库
- **语音数据**: 音频流不持久化，仅在内存中处理
- **MCP 工具**: 白名单机制，限制可调用的工具范围
- **CORS**: 开发环境允许 localhost 跨域
