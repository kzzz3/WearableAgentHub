# 08 演示指南（Demo Guide）

> 本文档提供 WearableAgent Hub 的 5 个核心演示场景，用于展示 A2A 通信、A2UI 渲染、x402 支付、语音交互的完整链路。

---

## 前置准备

### 一键启动

```powershell
# 方式一：使用一键启动脚本
powershell -ExecutionPolicy Bypass -File scripts/start-all.ps1

# 方式二：手动逐个启动
# 终端 1 — x402 支付服务
pnpm --filter @wearable-hub/x402-pay dev

# 终端 2 — 核心后端
cd packages/core
E:\Miniconda3\envs\expr\python.exe -m uvicorn src.main:app --reload --port 8000

# 终端 3 — 翻译 Agent
cd examples/translate-agent
E:\Miniconda3\envs\expr\python.exe main.py

# 终端 4 — 导航 Agent
cd examples/nav-agent
E:\Miniconda3\envs\expr\python.exe main.py

# 终端 5 — 眼镜模拟器
pnpm --filter @wearable-hub/glasses-sim dev

# 终端 6 — 手表模拟器
pnpm --filter @wearable-hub/watch-sim dev

# 终端 7 — 管理面板
pnpm --filter @wearable-hub/dashboard dev
```

### 服务端口一览

| 服务 | 端口 | URL |
|------|------|-----|
| 核心后端 | 8000 | http://localhost:8000 |
| x402 支付 | 8002 | http://localhost:8002 |
| 翻译 Agent | 8001 | http://localhost:8001 |
| 导航 Agent | 8003 | http://localhost:8003 |
| 支付 Agent | 8004 | http://localhost:8004 |
| 眼镜 HUD | 5173 | http://localhost:5173 |
| 手表面盘 | 5174 | http://localhost:5174 |
| 管理面板 | 5175 | http://localhost:5175 |

### 健康检查

```powershell
# 检查后端
curl http://localhost:8000/health

# 检查 x402
curl http://localhost:8002/health

# 检查翻译 Agent
curl http://localhost:8001/health

# 检查 Agent Card
curl http://localhost:8001/.well-known/agent-card.json
```

---

## 场景 1：本地问答 + A2UI 渲染

**展示**：LLM 生成结构化数据 → A2UI 渲染为 HUD 卡片

**操作步骤**：

1. 打开眼镜模拟器 http://localhost:5173
2. 在输入框输入 `nearby cafes` 或点击快捷按钮
3. 观察 HUD 渲染结果

**预期结果**：

- 后端 AgentEngine 调用 LLM，返回结构化 JSON
- A2UIGenerator 将 JSON 转为 A2UI 消息
- 眼镜 HUD 渲染为卡片样式（标题 + 地点列表 + 评分）
- MessageBubble 显示 Agent 回复文本

**技术链路**：

```
眼镜输入 → WebSocket → AgentEngine.process() → LLM API →
结构化 JSON → A2UIGenerator → A2UIRenderer → HUD 显示
```

---

## 场景 2：A2A 跨 Agent 通信

**展示**：主 Agent 检测翻译意图 → 调用远程翻译 Agent → 返回结果

**操作步骤**：

1. 确保翻译 Agent 已启动（端口 8001）
2. 在眼镜 HUD 输入 `translate Hello World`
3. 观察 Agent 调用链路

**预期结果**：

- 主 Agent 检测到翻译意图（正则匹配 `translate`）
- A2AClientWrapper 发现翻译 Agent 的 AgentCard
- 通过 A2A 协议（JSON-RPC）发送翻译请求
- 翻译 Agent 返回 `Hello World → 你好世界`
- 眼镜 HUD 显示翻译结果，MessageBubble 标注 `source: a2a`

**技术链路**：

```
眼镜输入 "translate Hello" → AgentEngine._detect_a2a_intent() →
A2AClientWrapper.send_message() → A2A JSON-RPC → 翻译 Agent →
翻译结果 → A2UI → HUD
```

**验证命令**：

```powershell
# 直接调用翻译 Agent 的 A2A 端点
curl -X POST http://localhost:8001/a2a -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "test-1",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "translate hello"}],
      "messageId": "msg-1"
    }
  }
}'
```

---

## 场景 3：x402 支付结算

**展示**：Agent 调用付费服务 → x402 自动结算 → 支付状态 UI

**操作步骤**：

1. 确保 x402 支付服务已启动（端口 8002）
2. 在眼镜 HUD 输入 `translate 你好世界 to English`（触发支付意图）
3. 或输入 `health analysis for today`
4. 观察支付流程

**预期结果**：

- AgentEngine 检测到支付意图
- 调用 X402Client.pay_and_settle() 完成模拟支付
- 支付结果附加到回复中
- PaymentStatus 组件显示支付金额和交易 ID
- MessageBubble 显示绿色支付成功标记

**技术链路**：

```
眼镜输入 → AgentEngine._detect_payment_intent() →
X402Client.pay_and_settle() → x402 服务 →
模拟支付 → 交易回执 → 附加到回复 → PaymentStatus UI
```

**验证命令**：

```powershell
# 查看可用付费服务
curl http://localhost:8002/services

# 查看钱包余额
curl http://localhost:8002/wallets

# 手动发起支付
curl -X POST http://localhost:8002/pay-and-settle -H "Content-Type: application/json" -d '{"service": "translate"}'

# 查看支付记录
curl http://localhost:8002/payments
```

---

## 场景 4：多设备联动

**展示**：眼镜和手表同时连接，Dashboard 监控全局状态

**操作步骤**：

1. 打开眼镜 HUD http://localhost:5173
2. 打开手表表盘 http://localhost:5174
3. 打开管理面板 http://localhost:5175
4. 在眼镜 HUD 发送消息，观察手表和 Dashboard 的反应

**预期结果**：

- 眼镜和手表共享同一个 WebSocket session（`default`）
- 眼镜发送消息后，两端都能收到 A2UI 更新
- Dashboard 显示：
  - Overview 页面：实时任务计数、Agent 状态
  - Payments 页面：支付记录和金额统计
  - Agents 页面：已注册 Agent 列表
  - Logs 页面：实时日志流

**技术链路**：

```
眼镜输入 → WebSocket → 后端处理 →
  ├─ 眼镜 WebSocket → A2UI 渲染
  ├─ 手表 WebSocket → A2UI 渲染
  └─ Dashboard → 状态更新
```

---

## 场景 5：语音交互（文本模拟模式）

**展示**：语音按钮触发文本输入，模拟语音→Agent→回复的链路

**操作步骤**：

1. 在眼镜 HUD 底部找到麦克风图标（VoiceButton）
2. 点击麦克风按钮
3. 在弹出的 prompt 中输入文字（模拟语音转写）
4. 观察 Agent 处理和回复

**预期结果**：

- VoiceButton 点击后弹出文本输入（模拟语音转写）
- 输入的文字通过 Voice WebSocket 发送到后端
- 后端 `/voice/{session_id}` 处理请求
- 返回 transcript（转写文本）、reply（Agent 回复）、a2ui 消息
- HUD 显示交互结果

**技术链路**：

```
语音按钮 → 文本模拟 → /voice/{session_id} WebSocket →
后端处理 → 返回 {transcript, reply, a2ui} → HUD 渲染
```

**注意**：当前使用 `prompt()` 文本输入模拟语音，生产环境可替换为 OpenAI Realtime API 或 Web Speech API。

---

## 高级场景：多 Agent 协作

**展示**：导航 Agent + 翻译 Agent 联动

**操作步骤**：

1. 确保导航 Agent（8003）和翻译 Agent（8001）都已启动
2. 在眼镜输入 `find nearby cafes and translate the names to Chinese`

**预期结果**：

- 主 Agent 调用导航 Agent 获取咖啡店列表
- 调用翻译 Agent 翻译店名
- 组合结果通过 A2UI 渲染

---

## 故障排查

| 问题 | 排查步骤 |
|------|----------|
| HUD 无响应 | 检查后端是否在 8000 端口运行 |
| A2A 调用失败 | 检查翻译 Agent 是否在 8001 端口，`curl http://localhost:8001/health` |
| 支付失败 | 检查 x402 服务是否在 8002 端口，`curl http://localhost:8002/health` |
| WebSocket 断连 | 检查浏览器控制台，确认后端 CORS 配置 |
| 前端构建失败 | 检查是否有 BOM 编码问题，运行 `pnpm -w run build` |
| Agent Card 404 | 确认 A2A 路由已挂载：`curl http://localhost:8000/.well-known/agent-card.json` |