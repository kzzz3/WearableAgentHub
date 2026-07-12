# WearableAgent Hub

PC 端穿戴设备 AI Agent 模拟器 + 服务中枢，完整跑通 **A2A 通信**、**A2UI 界面渲染**、**x402 支付结算** 三大协议链路。

## 快速开始

### 前置条件

- Node.js 20+
- pnpm 9+
- conda（使用 `expr` 环境，Python 3.13）
- OpenAI 兼容 API Key（可选，本地 LLM fallback）

### 安装

```powershell
# 克隆仓库
git clone <repo-url>
cd WearableAgentHub

# 前端依赖
pnpm install

# Python 依赖（conda expr 环境）
E:\Miniconda3\envs\expr\python.exe -m pip install -e packages/core
E:\Miniconda3\envs\expr\python.exe -m pip install -r examples/translate-agent/requirements.txt
E:\Miniconda3\envs\expr\python.exe -m pip install -r examples/nav-agent/requirements.txt
E:\Miniconda3\envs\expr\python.exe -m pip install -r examples/pay-agent/requirements.txt
```

### 环境变量

```powershell
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 一键启动

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-all.ps1
```

### 手动启动

```powershell
# 终端 1 — x402 支付服务 (8002)
pnpm --filter @wearable-hub/x402-pay dev

# 终端 2 — 核心后端 (8000)
cd packages/core
E:\Miniconda3\envs\expr\python.exe -m uvicorn src.main:app --reload --port 8000

# 终端 3 — 翻译 Agent (8001)
cd examples/translate-agent
E:\Miniconda3\envs\expr\python.exe main.py

# 终端 4 — 导航 Agent (8003)
cd examples/nav-agent
E:\Miniconda3\envs\expr\python.exe main.py

# 终端 5 — 眼镜模拟器 (5173)
pnpm --filter @wearable-hub/glasses-sim dev

# 终端 6 — 手表模拟器 (5174)
pnpm --filter @wearable-hub/watch-sim dev

# 终端 7 — 管理面板 (5175)
pnpm --filter @wearable-hub/dashboard dev
```

## 服务端口

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

## 项目结构

```
WearableAgentHub/
├── AGENTS.md                    # 开发规范
├── README.md                    # 本文件
├── docs/                        # 设计文档
│   ├── 01-design-goals.md       # 设计目标
│   ├── 02-requirements.md       # 需求规格
│   ├── 03-architecture.md       # 系统架构
│   ├── 04-implementation-plan.md # 实施计划
│   ├── 05-tech-stack.md         # 技术栈
│   ├── 06-a2a-integration-guide.md # A2A 集成指南
│   ├── 07-design-summary.md     # 设计总览
│   └── 08-demo-guide.md         # 演示指南
├── packages/
│   ├── core/                    # Agent 核心引擎（Python/FastAPI）
│   ├── a2ui-renderer/           # A2UI 穿戴端渲染器（React/TS）
│   ├── x402-pay/                # x402 支付微服务（TypeScript/Hono）
│   └── voice/                   # 语音交互模块（React Hook）
├── apps/
│   ├── glasses-sim/             # AI 眼镜 HUD 模拟器
│   ├── watch-sim/               # AI 手表表盘模拟器
│   └── dashboard/               # Agent 管理面板
├── examples/
│   ├── translate-agent/         # 翻译 Agent（A2A，8001）
│   ├── nav-agent/               # 导航 Agent（A2A，8003）
│   └── pay-agent/               # 支付 Agent（A2A + x402，8004）
└── scripts/
    └── start-all.ps1            # 一键启动脚本
```

## 核心链路

### 链路 A：用户问答 → A2UI 渲染

```
眼镜 HUD → WebSocket → AgentEngine → LLM → 结构化 JSON → A2UI → HUD
```

### 链路 B：A2A 跨 Agent 通信

```
眼镜 HUD → AgentEngine → A2A Client → 翻译/导航 Agent → 结果 → A2UI → HUD
```

### 链路 C：x402 支付结算

```
眼镜 HUD → AgentEngine → X402Client → 支付服务 → 交易回执 → PaymentStatus UI
```

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS + Zustand |
| 后端 | Python 3.13 + FastAPI + a2a-sdk v1.1.0 (protobuf) |
| 支付 | TypeScript + Hono + x402 协议模拟 |
| 语音 | WebSocket + OpenAI Realtime API（可选） |
| 包管理 | pnpm 9 (monorepo) + conda (Python) |

## 协议

| 协议 | 版本 | SDK | 用途 |
|------|------|-----|------|
| A2A | v1.0 | a2a-sdk v1.1.0 (PyPI) | Agent 间发现与通信 |
| A2UI | v0.9.1 | 自研渲染器 | 声明式 UI → HUD 渲染 |
| x402 | v0.1+ | 自研模拟 | HTTP 原生支付结算 |
| MCP | latest | @modelcontextprotocol/sdk | 工具服务集成（可选） |

## 测试

```powershell
# Python 单测（30 个）
E:\Miniconda3\envs\expr\python.exe -m pytest packages/core -q

# TypeScript 构建验证
pnpm -w run build
```

## 文档

- [设计目标](docs/01-design-goals.md)
- [需求规格](docs/02-requirements.md)
- [系统架构](docs/03-architecture.md)
- [实施方案](docs/04-implementation-plan.md)
- [技术栈](docs/05-tech-stack.md)
- [A2A 集成指南](docs/06-a2a-integration-guide.md)
- [设计总览](docs/07-design-summary.md)
- [演示指南](docs/08-demo-guide.md)

## License

MIT