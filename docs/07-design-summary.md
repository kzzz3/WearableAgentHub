# 07 设计总览与实施方案（WearableAgent Hub）

> 本文档是对当前项目目标、设计决策、系统需求、架构方案与实施成果的汇总版，便于快速对齐。
>
> 最后更新：与 docs/09（MIMO 集成）、docs/10（实施路线图）、docs/11（验证状态）同步。

---

## 1. 项目定位

WearableAgent Hub 不是一个穿戴产品原型，而是一个**协议验证平台**。

它的核心价值是验证三件事：

1. **A2A** 是否适合穿戴场景下的多 Agent 协作
2. **A2UI** 是否适合 HUD / 表盘等轻量信息界面
3. **x402** 是否适合微付费与 API 服务结算

一句话：**穿戴 AI Agent 的本地协议联调平台**。

---

## 2. 设计目标（6 条）

1. **协议真实联调**：A2A / A2UI / x402 三条链路真实跑通
2. **真实模型接入**：默认 LLM 使用 MIMO（OpenAI 兼容接口，已配置接入）
3. **本地可复现**：一台 PC 完成启动、演示、调试
4. **穿戴优先**：UI 面向 HUD 小屏信息展示（眼镜 400×600 / 手表 280×280）
5. **渐进交付**：Phase 1→5 逐步构建，每阶段独立验收
6. **可讲解可交接**：文档、架构、协议、验证步骤齐全

---

## 3. 当前阶段

> 从"功能拼装完成"进入"真实联调与交付收口"。

### 已完成（Phase 1 ~ 5）

| 阶段 | 目标 | 状态 |
|------|------|------|
| Phase 1 | 文字问答 + A2UI 渲染 + 眼镜 HUD | ✅ 完成 |
| Phase 2 | A2A 协议接入 + 翻译 Agent | ✅ 完成 |
| Phase 3 | x402 支付链路 | ✅ 完成 |
| Phase 4 | 语音 + 手表模拟器 + Dashboard | ✅ 完成 |
| Phase 5 | 演示打磨 + 导航/支付 Agent + 一键启动 | ✅ 完成 |

### 已验证指标

| 检查项 | 结果 |
|--------|------|
| Python 单测（30 个） | ✅ 全部通过 |
| TypeScript 构建（6 个项目） | ✅ 全部通过 |
| BOM 编码扫描 | ✅ 全部清除 |

### 验证状态总览

详细分类见 `docs/11-verification-status.md`，汇总如下：

| 类别 | 数量 |
|------|------|
| ✅ 真实已验证 | 45 项 |
| ⚙️ 仅配置/设计 | 3 项 |
| 🔲 待补验证 | 10 项 |

---

## 4. 关键技术决策（ADR）

### ADR-1：Python/FastAPI 主后端
a2a-sdk 官方 Python 版最成熟（v1.1.0），FastAPI 原生支持 WebSocket + SSE。

### ADR-2：a2a-sdk v1.1.0 边界层适配
SDK 是 protobuf 类型（非 Pydantic），业务层用 Pydantic，A2A 边界做类型转换。

### ADR-3：conda expr 统一 Python 环境
路径 `E:\Miniconda3\envs\expr\python.exe`，不使用 `conda run`。

### ADR-4：pnpm monorepo 前端
glasses-sim / watch-sim / dashboard 共享 a2ui-renderer。

### ADR-5：x402 TypeScript Hono 微服务
官方 SDK 只有 TS 版，Python 通过 HTTP REST 桥接。

### ADR-6：LLM OpenAI 兼容接口
通过 `base_url` 接入任意兼容 API。默认使用 MIMO（`mimo-v2.5-pro`）。

### ADR-7：A2UI 自研穿戴渲染器
精确控制 HUD 组件外观（半透明、网格、科技感配色）。

---

## 5. MIMO 集成状态

当前 MIMO 已**配置层真实接入**：

- `.env` 包含真实 endpoint、API key、model
- `config.py` 通过 pydantic-settings 读取
- `agent_engine.py` 使用 `AsyncOpenAI` + `chat.completions.create`
- `main.py` 启动时日志输出 provider 配置

> **配置已接入 ≠ 全链路已验收。** 端到端验证见 docs/11 第 3.1 节。

---

## 6. 架构方案

### 分层

1. **前端层**：glasses-sim / watch-sim / dashboard
2. **主服务层**：packages/core（FastAPI + WS + REST + A2A Server + Voice）
3. **A2UI 渲染层**：packages/a2ui-renderer（React 组件库）
4. **支付层**：packages/x402-pay（Hono 微服务）
5. **示例层**：examples/translate-agent / nav-agent / pay-agent

### 核心调用链

#### A：用户问答 → HUD
```
前端 WebSocket → core.AgentEngine → LLM API → A2UIGenerator → WS → A2UIRenderer
```

#### B：主 Agent → 子 Agent（A2A）
```
AgentEngine → _detect_a2a_intent → A2AClientWrapper → A2A JSON-RPC → 子 Agent → A2UI
```

#### C：付费调用（x402）
```
AgentEngine → _detect_payment_intent → X402Client → x402 服务 → 支付回执
```

#### D：语音交互
```
VoiceButton → useVoiceSession WS → /voice/{session_id} → AgentEngine
```

---

## 7. 端口分配

| 服务 | 端口 | 技术 |
|------|------|------|
| 核心后端 | 8000 | Python/FastAPI |
| 翻译 Agent | 8001 | Python/A2A |
| x402 支付 | 8002 | TypeScript/Hono |
| 导航 Agent | 8003 | Python/A2A |
| 支付 Agent | 8004 | Python/A2A |
| 眼镜 HUD | 5173 | React/Vite |
| 手表面盘 | 5174 | React/Vite |
| 管理面板 | 5175 | React/Vite |

---

## 8. 需求总览

### 功能需求（全部已实现代码）

| 能力 | 说明 |
|------|------|
| 文字问答 | 眼镜 HUD → LLM → A2UI 渲染 |
| A2A 通信 | 主 Agent ↔ 子 Agent |
| A2UI 渲染 | HUD 组件（Text/Card/List/StatusBar/Badge/Divider）|
| x402 支付 | 付费服务自动结算 |
| 语音交互 | WebSocket 文本模拟 |
| 手表模拟 | 圆形表盘 + 健康组件 |
| Dashboard | Overview/Payments/Agents/Logs |

### 非功能需求

- 本地可运行（不依赖云服务）
- 单测覆盖关键链路
- 文档与代码同步
- 可扩展（独立模块）

---

## 9. 实施路线图

详见 `docs/10-implementation-roadmap.md`，核心路径：

1. **文档收口** — 更新 AGENTS.md、docs 统一（✅ 已完成）
2. **核心链路稳定** — MIMO 推理 + A2UI 渲染
3. **协议逐项验证** — A2A 翻译 → x402 支付
4. **多设备联调** — 眼镜 + 手表 + Dashboard
5. **演示化收口** — 优化启动说明和故障排查

---

## 10. 后续扩展方向

| 方向 | 说明 |
|------|------|
| OpenAI Realtime 语音 | 替换文本模拟为真正的实时语音 |
| Electron 桌面端 | 眼镜 HUD 打包为 overlay |
| 更多 Agent | 天气/日历/音乐 Agent |
| MCP 工具集成 | 接入 MCP Server |
| Agent Card 动态发现 | 运行时自动发现局域网 Agent |
| 持久化存储 | SQLite → PostgreSQL |

---

## 11. 相关文档索引

| 文档 | 主题 |
|------|------|
| docs/01 | 设计目标 |
| docs/02 | 需求规格 |
| docs/03 | 系统架构 |
| docs/04 | 实施计划 |
| docs/05 | 技术栈选型 |
| docs/06 | A2A 集成指南 |
| docs/07 | 设计总览（本文档）|
| docs/08 | 演示指南 |
| docs/09 | MIMO 接入与验证 |
| docs/10 | 实施路线图 |
| docs/11 | 验证状态总览 |