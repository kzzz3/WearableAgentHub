# WearableAgent Hub — 项目总览

## 项目定位

PC 端穿戴设备 AI Agent 模拟器 + 服务中枢，完整跑通 **A2A 通信**、**A2UI 界面渲染**、**x402 支付结算** 三大协议链路。

## 技术栈

- **前端**: React 18 + TypeScript + Vite（模拟 HUD/表盘 UI）
- **后端**: Python 3.13 (conda `expr`) + FastAPI + A2A Python SDK
- **语音**: OpenAI Realtime API（WebSocket 实时语音）
- **协议**:
  - A2A v1.0 — a2a-sdk (PyPI, 官方 Python SDK)
  - A2UI v0.9.1 — 自研穿戴端渲染器（参考 React/Lit 官方渲染器）
  - x402 — @x402/core + a2a-x402（TypeScript）
  - MCP — OpenAI MCP 集成工具服务

## 仓库结构

```
wearable-agent-hub/
├── AGENTS.md                  # 本文件
├── README.md                  # 项目说明
├── docs/                      # 设计文档
├── packages/
│   ├── core/                  # Agent 核心引擎（Python）
│   ├── a2a-server/            # A2A 协议服务端（Python/FastAPI）
│   ├── a2ui-renderer/         # 穿戴端 A2UI 渲染器（React/TS）
│   ├── x402-pay/              # x402 支付模块（TypeScript）
│   └── voice/                 # 语音交互模块（TypeScript/WebSocket）
├── apps/
│   ├── glasses-sim/           # AI 眼镜模拟器（React/Vite）
│   ├── watch-sim/             # AI 手表模拟器（React/Vite）
│   └── dashboard/             # Agent 管理面板（React/Vite）
└── examples/
    ├── translate-agent/       # 翻译 Agent 示例（Python）
    ├── nav-agent/             # 导航 Agent 示例（Python）
    └── pay-agent/             # 支付 Agent 示例（Python）
```

## 开发约定

### 语言与风格

- **Python**: 使用 ruff 格式化 + mypy 类型检查，遵循 Google Python Style Guide
- **TypeScript**: 使用 ESLint + Prettier，严格模式 (strict: true)
- **命名**: 文件名 kebab-case，Python 函数 snake_case，TS 接口 PascalCase

### Python 环境

- 统一使用 conda `expr` 环境（Python 3.13）
- 激活: `conda activate expr`
- 所有 Python 命令前缀: `conda run -n expr ...`
- 已安装: fastapi, uvicorn, openai, pydantic, httpx, websockets, ruff, mypy, pytest 等

### Git 规范

- 分支: feat/xxx, fix/xxx, docs/xxx
- 提交: Conventional Commits (feat:, fix:, docs:, refactor:)
- PR 需要至少一个 review

### 测试

- Python: pytest + pytest-asyncio（conda `expr` 已安装）
- TypeScript: Vitest
- E2E: Playwright（模拟器 UI 测试）

### 包管理

- Python: conda `expr` 环境
- TypeScript: pnpm workspaces（monorepo）

## 协议版本锁定

| 协议 | 版本 | SDK | 仓库 |
|------|------|-----|------|
| A2A | v1.0.0 | a2a-sdk (PyPI) | [a2aproject/A2A](https://github.com/a2aproject/A2A) |
| A2UI | v0.9.1 | 自研渲染器 | [a2ui-project/a2ui](https://github.com/a2ui-project/a2ui) |
| x402 | v0.1+ | @x402/core + a2a-x402 | [x402-foundation/x402](https://github.com/x402-foundation/x402) |
| MCP | latest | @modelcontextprotocol/sdk | [modelcontextprotocol.io](https://modelcontextprotocol.io) |

## 快速开始

```bash
# 后端
conda activate expr
cd packages/core && pip install -e . && uvicorn src.main:app --reload

# 前端
pnpm install && pnpm dev

# 运行示例 Agent
conda activate expr
cd examples/translate-agent && python main.py
```

## 注意事项

- 本项目为 PC 模拟器，不涉及真实穿戴设备硬件
- 语音功能需要 OpenAI API Key（Realtime API）
- x402 支付使用 Base Sepolia 测试网，需要测试网钱包
- Python 环境统一使用 conda `expr`，不要使用 uv 或系统 Python