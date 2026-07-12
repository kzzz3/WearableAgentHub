# 需求规格说明书

## 1. 项目概述

### 1.1 项目名称

WearableAgent Hub（穿戴设备 AI Agent 模拟中枢）

### 1.2 项目目标

在 PC 环境中完整模拟穿戴设备（AI 眼镜、AI 手表）的 AI Agent 交互场景，跑通以下三条核心链路：

1. **语音 → Agent → A2UI 渲染**: 用户语音输入 → LLM 理解意图 → 调用 Agent/工具 → A2UI 渲染为 HUD/表盘 UI
2. **Agent → Agent → x402 结算**: Agent 间通过 A2A 协议通信，付费服务通过 x402 自动结算
3. **多 Agent 协作**: 多个穿戴设备 Agent 协同工作，共享上下文

### 1.3 目标用户

- AI Agent 开发者（学习 A2A/A2UI/x402 协议）
- 穿戴设备 AI 产品经理（原型验证）
- 协议研究者（端到端 Demo）

### 1.4 项目范围

**包含**:
- PC 端穿戴设备 UI 模拟器（眼镜 HUD + 手表表盘）
- A2A v1.0 协议完整实现（Server + Client）
- A2UI v0.9.1 渲染器（穿戴设备风格）
- x402 支付结算（测试网）
- 语音实时交互（OpenAI Realtime API）
- MCP 工具集成
- 示例 Agent（翻译、导航、支付）

**不包含**:
- 真实穿戴设备硬件集成
- 生产环境部署方案
- 移动端适配
- 主网支付

---

## 2. 功能需求

### 2.1 用户故事

#### 2.1.1 语音交互

| ID | 用户故事 | 优先级 |
|----|---------|-------|
| US-01 | 作为用户，我可以通过麦克风用自然语言向 AI 眼镜提问 | P0 |
| US-02 | 作为用户，我可以在眼镜 HUD 上看到 Agent 的回复 | P0 |
| US-03 | 作为用户，我可以听到 Agent 的语音回复（TTS） | P1 |
| US-04 | 作为用户，我可以打断 Agent 的回复并继续提问 | P2 |

#### 2.1.2 A2A Agent 通信

| ID | 用户故事 | 优先级 |
|----|---------|-------|
| US-05 | 作为开发者，我可以通过 A2A 协议注册和发现 Agent | P0 |
| US-06 | 作为开发者，我可以让一个 Agent 调用另一个 Agent 的服务 | P0 |
| US-07 | 作为开发者，我可以查看 Agent 间通信的实时日志 | P1 |
| US-08 | 作为开发者，我可以监控 Task 的生命周期状态 | P1 |
| US-09 | 作为开发者，我可以使用 SSE 流式接收 Agent 响应 | P0 |

#### 2.1.3 A2UI 界面渲染

| ID | 用户故事 | 优先级 |
|----|---------|-------|
| US-10 | 作为用户，我可以在眼镜模拟器上看到 HUD 风格的信息卡片 | P0 |
| US-11 | 作为用户，我可以在手表模拟器上看到表盘风格的数据面板 | P0 |
| US-12 | 作为用户，我可以点击 UI 上的按钮触发 Agent 操作 | P1 |
| US-13 | 作为开发者，我可以自定义 A2UI 组件目录 | P2 |
| US-14 | 作为用户，我可以实时看到 UI 的渐进式渲染效果 | P1 |

#### 2.1.4 x402 支付结算

| ID | 用户故事 | 优先级 |
|----|---------|-------|
| US-15 | 作为用户，当我调用付费 Agent 服务时，系统自动处理支付 | P0 |
| US-16 | 作为用户，我可以在 Dashboard 上查看支付历史 | P1 |
| US-17 | 作为开发者，我可以为我的 Agent 设置服务价格 | P1 |
| US-18 | 作为用户，支付过程对我不透明（自动签名确认） | P0 |

#### 2.1.5 多 Agent 协作

| ID | 用户故事 | 优先级 |
|----|---------|-------|
| US-19 | 作为用户，我可以同时使用眼镜 Agent 和手表 Agent | P1 |
| US-20 | 作为用户，多个 Agent 的结果可以合并显示在一个 HUD 上 | P2 |

#### 2.1.6 Agent 管理面板

| ID | 用户故事 | 优先级 |
|----|---------|-------|
| US-21 | 作为开发者，我可以在 Dashboard 上查看所有已注册 Agent | P0 |
| US-22 | 作为开发者，我可以在 Dashboard 上查看 A2A 通信日志 | P1 |
| US-23 | 作为开发者，我可以在 Dashboard 上查看 x402 支付记录 | P1 |
| US-24 | 作为开发者，我可以在 Dashboard 上手动发送 A2A 消息测试 | P2 |

### 2.2 功能模块详细需求

#### 2.2.1 眼镜模拟器 (glasses-sim)

**外观**:
- 模拟 Google Glass / Meta Orion 风格的 HUD 界面
- 半透明背景，信息浮层效果
- 分区布局：主视图区（中央）、状态栏（顶部）、通知区（底部）

**功能**:
- HUD 信息卡片渲染（A2UI Surface）
- 语音输入指示器（录音状态）
- Agent 回复动画（渐入渐出）
- 支持文本、列表、图片、地图片段等组件

**交互**:
- 点击麦克风图标开始语音输入
- 点击卡片展开详情
- 滑动查看历史记录

#### 2.2.2 手表模拟器 (watch-sim)

**外观**:
- 模拟 Apple Watch / Pixel Watch 风格的圆形/方形表盘
- 表盘主界面 + 应用列表 + 通知面板

**功能**:
- 表盘数据面板（时间、天气、健康数据）
- Glance Widget（速览小部件）
- 通知推送（来自其他 Agent 的消息）

**交互**:
- 点击表盘切换面板
- 旋转表冠（模拟）滚动列表
- 长按进入编辑模式

#### 2.2.3 Agent 管理面板 (dashboard)

**功能**:
- Agent 列表（名称、状态、端点、技能）
- A2A 通信日志（实时流）
- x402 支付记录（交易哈希、金额、状态）
- Agent Card 编辑器（JSON 编辑）
- 手动 A2A 消息发送器（测试工具）
- MCP 工具列表

#### 2.2.4 语音交互模块

**功能**:
- 麦克风音频采集（Web Audio API）
- 音频流式传输（WebSocket）
- OpenAI Realtime API 集成
- 语音活动检测（VAD）
- 打断检测（barge-in）
- TTS 音频播放

**约束**:
- 需要 OpenAI API Key
- 语音延迟目标：< 500ms（端到端）
- 支持中英文

#### 2.2.5 A2A 协议模块

**功能**:
- A2A v1.0 Server 实现（JSON-RPC 2.0 over HTTP）
- Agent Card 发布（/.well-known/agent.json）
- Task 生命周期管理（submitted → working → input-required → completed / failed / canceled）
- 消息处理（message/send + message/stream）
- SSE 流式响应
- Artifact 管理

**接口**:

`
POST /a2a                    # JSON-RPC 端点
GET  /a2a/stream             # SSE 流式端点
GET  /.well-known/agent.json # Agent Card
GET  /a2a/tasks/{id}         # 查询 Task 状态
POST /a2a/tasks/{id}/cancel  # 取消 Task
`

#### 2.2.6 A2UI 渲染模块

**功能**:
- A2UI v0.9.1 协议解析器
- Surface 管理器（创建/更新/删除）
- 组件注册表（基础组件 + 穿戴设备专用组件）
- 数据模型绑定（DataModel path 引用）
- 流式渲染（逐条处理 JSON 消息）
- 主题系统（眼镜深色 / 手表深色）

**支持的 A2UI 消息类型**:
- createSurface — 创建 UI 区域
- updateComponents — 更新组件树
- updateDataModel — 更新数据
- deleteSurface — 删除 UI 区域

**穿戴设备组件目录**:

| 组件名 | 说明 | 适用设备 |
|--------|------|---------|
| HudCard | HUD 信息卡片 | 眼镜 |
| WatchFace | 表盘面板 | 手表 |
| MiniMap | 迷你地图 | 眼镜 |
| GlanceWidget | 速览小部件 | 手表 |
| VoiceWaveform | 语音波形 | 通用 |
| StatusBar | 状态栏 | 通用 |
| Notification | 通知条 | 通用 |
| Text | 文本 | 通用 |
| Image | 图片 | 通用 |
| Button | 按钮 | 通用 |
| List | 列表 | 通用 |

#### 2.2.7 x402 支付模块

**功能**:
- x402 支付流程管理（payment-required → payment-submitted → payment-completed）
- 测试网钱包管理（Base Sepolia）
- ERC-20 USDC 支付
- A2A 扩展集成
- 支付记录查询

**约束**:
- 仅支持 Base Sepolia 测试网
- 仅支持 USDC 代币
- 钱包私钥通过环境变量配置，不进代码库

---

## 3. 非功能需求

### 3.1 性能

| 指标 | 目标 |
|------|------|
| 语音端到端延迟 | < 500ms |
| A2UI 渲染首屏时间 | < 200ms |
| A2A 消息往返时间（本地） | < 100ms |
| WebSocket 消息推送延迟 | < 50ms |
| 页面加载时间 | < 2s |

### 3.2 可用性

- 眼镜模拟器和手表模拟器可同时运行
- Dashboard 实时刷新，无需手动刷新
- 语音输入有明确的视觉反馈
- 错误信息清晰可读

### 3.3 可扩展性

- 组件目录可扩展（注册新组件）
- MCP 工具可热插拔
- 新 Agent 可通过配置文件注册
- 主题可自定义

### 3.4 兼容性

- 浏览器: Chrome 120+, Edge 120+
- 操作系统: Windows 10+, macOS 13+
- Node.js: 20+
- Python: 3.11+

---

## 4. 接口需求

### 4.1 外部 API

| API | 用途 | 认证方式 |
|-----|------|---------|
| OpenAI Realtime API | 语音 STT + LLM + TTS | API Key |
| OpenAI Chat API | LLM 推理（备用） | API Key |
| Base Sepolia RPC | x402 链上交互 | 公共端点 |

### 4.2 内部接口

| 接口 | 协议 | 端口 |
|------|------|------|
| 前端 ↔ 后端 | WebSocket | 8000 |
| 后端 ↔ 外部 Agent | A2A JSON-RPC | 各 Agent 端口 |
| 后端 ↔ x402 服务 | HTTP | 8001 |
| 后端 ↔ MCP Server | stdio/SSE | 各 MCP 端口 |

---

## 5. 数据需求

### 5.1 数据存储

| 数据 | 存储方式 | 说明 |
|------|---------|------|
| Agent 注册信息 | SQLite | Agent Card 持久化 |
| Task 记录 | SQLite | A2A Task 状态和历史 |
| 支付记录 | SQLite | x402 交易记录 |
| 会话上下文 | 内存 (Redis-like) | 短期会话状态 |
| Agent Card | JSON 文件 | 静态配置 |

### 5.2 数据模型

`
Agent:
  id: UUID
  name: string
  url: string
  card: JSON (Agent Card)
  status: enum [online, offline, busy]
  created_at: datetime

Task:
  id: UUID
  agent_id: FK(Agent)
  status: enum [submitted, working, input-required, completed, failed, canceled]
  messages: JSON[]
  artifacts: JSON[]
  created_at: datetime
  updated_at: datetime

Payment:
  id: UUID
  task_id: FK(Task)
  amount: string
  currency: string (USDC)
  network: string (base-sepolia)
  tx_hash: string
  status: enum [pending, confirmed, failed]
  created_at: datetime
`

---

## 6. MVP 范围定义

### Phase 1: 最短链路（2 周）

**目标**: 跑通 "语音提问 → Agent 回复 → HUD 显示"

- [x] 项目脚手架（monorepo 初始化）
- [ ] FastAPI 后端骨架
- [ ] 眼镜模拟器基础 UI（纯 Web）
- [ ] A2UI 渲染器最小实现（Text + Card 组件）
- [ ] WebSocket 连接（后端 → 前端）
- [ ] OpenAI Chat API 集成（先不用 Realtime）
- [ ] 文字输入 → LLM → A2UI JSON → HUD 显示

### Phase 2: A2A 协议（1 周）

**目标**: 跑通 Agent 间 A2A 通信

- [ ] A2A Server 实现（JSON-RPC 2.0）
- [ ] Agent Card 发布
- [ ] 示例翻译 Agent
- [ ] Agent 间 message/send 调用
- [ ] Dashboard Agent 列表

### Phase 3: x402 支付（1 周）

**目标**: 跑通付费 Agent 服务

- [ ] x402 支付流程
- [ ] 测试网钱包配置
- [ ] 付费翻译 Agent 示例
- [ ] Dashboard 支付记录

### Phase 4: 语音 + 体验优化（1 周）

**目标**: 完整语音交互体验

- [ ] OpenAI Realtime API 集成
- [ ] 手表模拟器
- [ ] 多 Agent 协作示例
- [ ] 主题系统
- [ ] 文档完善

---

## 7. 验收标准

### 7.1 功能验收

| 场景 | 验收标准 |
|------|---------|
| 语音提问 | 输入语音后 2 秒内在 HUD 上看到回复 |
| A2A 通信 | 两个 Agent 成功交换消息并返回结果 |
| x402 支付 | 付费调用自动完成支付并返回服务结果 |
| A2UI 渲染 | HUD 卡片正确显示文本、列表、图片 |
| 多 Agent | 眼镜和手表 Agent 同时运行，结果合并显示 |

### 7.2 技术验收

| 检查项 | 标准 |
|--------|------|
| A2A 兼容性 | 通过官方 A2A 测试工具验证 |
| A2UI 兼容性 | 正确解析 v0.9.1 所有消息类型 |
| 代码质量 | Python: ruff pass, TypeScript: eslint pass |
| 测试覆盖 | 核心模块 > 70% |
