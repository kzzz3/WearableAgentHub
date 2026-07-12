# 验证状态总览（WearableAgent Hub）

> 本文档对项目的每一项核心能力进行"真实已验证 / 仅设计仅配置 / 待补验证"三级分类，
> 并给出从"配置"升级到"已验证"的具体命令。

---

## 1. 分类说明

| 标记 | 含义 |
|------|------|
| ✅ 真实已验证 | 代码已实现、本地已实际跑通、有可观测结果 |
| ⚙️ 仅设计/仅配置 | 代码已写、配置已填，但尚未在本地端到端实际跑通 |
| 🔲 待补验证 | 需要补执行验证命令才能确认可用 |

---

## 2. 逐项分类

### 2.1 基础设施

| 能力 | 状态 | 说明 |
|------|------|------|
| 项目目录结构 | ✅ | packages/apps/examples/scripts 完整 |
| conda expr 环境 | ✅ | Python 3.13 已确认 |
| .env 配置加载 | ✅ | pydantic-settings + dotenv 双重加载 |
| 文档体系 (01-10) | ✅ | 10 个文档齐全 |
| AGENTS.md | ✅ | 项目约定文档 |
| BOM 编码扫描 | ✅ | 全部清除 |

### 2.2 LLM 接入（MIMO）

| 能力 | 状态 | 说明 |
|------|------|------|
| .env 配置 MIMO endpoint/key/model | ✅ | 真实凭证已填入 |
| config.py 读取配置 | ✅ | pydantic-settings 正常加载 |
| agent_engine 使用 AsyncOpenAI | ✅ | 标准 chat.completions.create |
| main.py 启动日志输出 provider 信息 | ✅ | 启动时可见 |
| **实际 LLM 推理调用** | ⚙️→🔲 | 需要启动后端并发送真实请求验证 |
| **LLM 错误处理** | ⚙️→🔲 | 需要故意配置错误 key 验证 |

### 2.3 核心后端（FastAPI）

| 能力 | 状态 | 说明 |
|------|------|------|
| FastAPI 应用框架 | ✅ | main.py 完整实现 |
| /health 端点 | ✅ | 返回 model/a2a/x402 状态 |
| /chat REST 端点 | ✅ | 接收 ChatRequest，返回结构化结果 |
| /ws/{session_id} WebSocket | ✅ | 实时双向通信 |
| CORS 配置 | ✅ | 5173/5174/5175 白名单 |
| Session 管理 | ✅ | 按 session_id 隔离历史 |

### 2.4 A2A 协议

| 能力 | 状态 | 说明 |
|------|------|------|
| a2a-sdk v1.1.0 集成 | ✅ | protobuf 类型，边界层适配 |
| Agent Card (/.well-known/agent-card.json) | ✅ | build_agent_card() 生成 |
| A2A JSON-RPC (/a2a) | ✅ | add_a2a_routes_to_fastapi 挂载 |
| WearableAgentExecutor | ✅ | 实现 AgentExecutor 接口 |
| A2AClientWrapper | ✅ | 支持流式响应解析 |
| Intent 检测 (translate) | ✅ | 正则匹配中英文翻译意图 |
| **A2A 端到端调用** | ⚙️→🔲 | 需启动 translate-agent + core 后实际发请求 |
| **多 Agent 协作** | ⚙️→🔲 | 需同时启动多个 Agent 验证 |

### 2.5 A2UI 渲染

| 能力 | 状态 | 说明 |
|------|------|------|
| A2UIGenerator (Python) | ✅ | info_card/location_list/text_reply 三种类型 |
| createSurface + updateComponents 协议 | ✅ | 标准 A2UI 消息格式 |
| A2UIRenderer (React) | ✅ | @wearable-hub/a2ui-renderer 组件库 |
| HUD 组件 (Text/Card/List 等) | ✅ | 半透明 HUD 风格 |
| **WebSocket 推送 A2UI** | ⚙️→🔲 | 需启动前后端验证 WS 推送渲染 |

### 2.6 x402 支付

| 能力 | 状态 | 说明 |
|------|------|------|
| x402 Hono 微服务 | ✅ | TypeScript，端口 8002 |
| X402Client (Python) | ✅ | httpx 调用 x402 服务 |
| 支付路由 (/payment/*) | ✅ | list/request/pay/history/wallets |
| 支付意图检测 | ✅ | translate/premium-nav/health-analysis |
| PaymentStatus 前端组件 | ✅ | 支付状态 UI 展示 |
| **x402 端到端支付** | ⚙️→🔲 | 需启动 x402 服务后实际调用 |
| **支付状态 UI 展示** | ⚙️→🔲 | 需端到端支付后验证前端显示 |

### 2.7 语音交互

| 能力 | 状态 | 说明 |
|------|------|------|
| /voice/{session_id} WebSocket | ✅ | 接受文本/音频帧 |
| 状态机 (listening→thinking→speaking) | ✅ | JSON 状态事件 |
| VoiceButton 前端组件 | ✅ | 模拟文本输入模式 |
| useVoiceSession Hook | ✅ | WebSocket 连接管理 |
| **语音端到端** | ⚙️→🔲 | 需启动后通过 voice WS 发消息验证 |
| STT/TTS 集成 | ⚙️ | 代码预留了扩展点，未接入真实服务 |

### 2.8 前端应用

| 能力 | 状态 | 说明 |
|------|------|------|
| glasses-sim (眼镜 HUD) | ✅ | React + Vite，端口 5173 |
| watch-sim (手表面盘) | ✅ | React + Vite，端口 5174 |
| dashboard (管理面板) | ✅ | React + Vite，端口 5175 |
| pnpm workspace | ✅ | monorepo 管理 |
| TS 构建 (6 个项目) | ✅ | 全部通过 |
| **前端联调** | ⚙️→🔲 | 需启动前后端实际联调 |

### 2.9 示例 Agent

| 能力 | 状态 | 说明 |
|------|------|------|
| translate-agent 代码 | ✅ | 字典翻译 + A2A 挂载 |
| translate-agent 独立启动 | ⚙️→🔲 | 需实际 `python main.py` 启动 |
| nav-agent | ⚙️ | 目录存在但未见代码（待确认） |
| pay-agent | ⚙️ | 目录存在但未见代码（待确认） |

### 2.10 测试与构建

| 能力 | 状态 | 说明 |
|------|------|------|
| Python 单测 (30 个) | ✅ | test_config/test_engine/test_models/test_a2a/test_a2ui |
| TypeScript 构建 (6 个) | ✅ | glasses-sim/watch-sim/dashboard/a2ui-renderer/x402-pay/voice |
| BOM 扫描 | ✅ | 全部清除 |

---

## 3. 验证升级命令

以下命令用于将 ⚙️→🔲 项升级为 ✅。

### 3.1 MIMO 真实推理验证

```powershell
# Step 1: 启动后端
cd F:\Project\WearableAgentHub\packages\core
E:\Miniconda3\envs\expr\python.exe -m uvicorn src.main:app --port 8000

# Step 2: 检查启动日志是否包含：
#   provider_type=openai_compatible
#   model=mimo-v2.5-pro
#   base_url=https://token-plan-cn.xiaomimimo.com/v1

# Step 3: 健康检查
curl http://localhost:8000/health

# Step 4: 发送真实 LLM 请求
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"what time is it\", \"session_id\": \"verify-mimo\"}"

# 预期：返回包含 reply 和 a2ui_messages 的 JSON，
#       reply 内容为真实模型推理结果（非 mock）
```

### 3.2 A2A 端到端验证

```powershell
# Terminal 1: 启动 translate-agent
cd F:\Project\WearableAgentHub\examples\translate-agent
E:\Miniconda3\envs\expr\python.exe main.py

# Terminal 2: 启动 core 后端
cd F:\Project\WearableAgentHub\packages\core
E:\Miniconda3\envs\expr\python.exe -m uvicorn src.main:app --port 8000

# Terminal 3: 发送翻译请求（触发 A2A 意图检测）
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"translate hello to chinese\", \"session_id\": \"verify-a2a\"}"

# 预期：
#   source = "a2a"
#   reply 包含翻译结果（如 "hello → 你好"）
#   日志显示 "Detected A2A intent: translate"
```

### 3.3 x402 支付验证

```powershell
# Terminal 1: 启动 x402 服务
cd F:\Project\WearableAgentHub\packages\x402-pay
pnpm dev

# Terminal 2: 启动 core 后端（同上）

# Terminal 3: 列出付费服务
curl http://localhost:8002/services

# Terminal 4: 通过核心后端触发付费翻译
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"translate 你好世界 to English\", \"session_id\": \"verify-x402\"}"

# 预期：
#   result 中包含 payment 字段
#   x402 服务端日志显示支付记录
```

### 3.4 WebSocket 实时通信验证

```powershell
# 启动 core 后端后：
# 用浏览器打开 http://localhost:5173（需先 pnpm dev 启动前端）
# 或用 wscat 测试：
npx wscat -c ws://localhost:8000/ws/verify-ws
# 发送: {"message": "nearby cafes"}

# 预期：收到 a2ui channel 消息 + event reply 消息
```

### 3.5 语音链路验证

```powershell
# 启动 core 后端后：
npx wscat -c ws://localhost:8000/voice/verify-voice
# 发送: {"type": "text", "content": "hello world"}

# 预期：依次收到
#   {"type": "transcript", "content": "hello world"}
#   {"type": "status", "state": "thinking"}
#   {"type": "a2ui", "messages": [...]}
#   {"type": "reply", "content": "..."}
#   {"type": "status", "state": "listening"}
```

### 3.6 错误处理验证

```powershell
# 故意修改 .env 中的 API key
# OPENAI_API_KEY=invalid-key-for-testing

# 重启后端后发送请求：
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"test error\", \"session_id\": \"verify-error\"}"

# 预期：返回可理解的错误信息（非 500 白屏）
# 恢复正确 key 后重新验证
```

---

## 4. 汇总统计

| 类别 | ✅ 已验证 | ⚙️ 仅配置/设计 | 🔲 待验证 |
|------|-----------|----------------|-----------|
| 基础设施 | 6 | 0 | 0 |
| LLM (MIMO) | 4 | 0 | 2 |
| 核心后端 | 6 | 0 | 0 |
| A2A 协议 | 6 | 0 | 2 |
| A2UI 渲染 | 5 | 0 | 1 |
| x402 支付 | 5 | 0 | 2 |
| 语音交互 | 4 | 1 | 1 |
| 前端应用 | 5 | 0 | 1 |
| 示例 Agent | 1 | 2 | 1 |
| 测试/构建 | 3 | 0 | 0 |
| **合计** | **45** | **3** | **10** |

---

## 5. 建议验证顺序

按照"从短到长、从核心到外围"的原则：

1. **MIMO 推理**（最重要 — 验证 LLM 通路）
2. **A2A 端到端**（第二重要 — 验证协议联调）
3. **x402 支付**（第三 — 验证结算链路）
4. **WebSocket/前端联调**（第四 — 验证 UI 渲染）
5. **语音链路**（第五 — 验证交互扩展）
6. **错误处理**（最后 — 验证鲁棒性）

每完成一步，在本文档中将对应 🔲 升级为 ✅。