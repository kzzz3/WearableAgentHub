# WearableAgent Hub

PC 端穿戴设备 AI Agent 模拟器 + 服务中枢，完整跑通 **A2A 通信**、**A2UI 界面渲染**、**x402 支付结算** 三大协议链路。

## 快速开始

### 前置条件

- Node.js 20+
- pnpm 9+
- conda（使用 `expr` 环境）
- OpenAI 兼容 API Key

### 安装

```bash
# 前端依赖
pnpm install

# Python 依赖
conda activate expr
pip install -e packages/core
```

### 环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 API Key
```

### 启动

```bash
# 后端
conda run -n expr uvicorn src.main:app --reload --port 8000

# 前端
pnpm dev
```

## 项目结构

```
wearable-agent-hub/
├── packages/
│   ├── core/              # Agent 核心引擎（Python/FastAPI）
│   ├── a2ui-renderer/     # 穿戴端 A2UI 渲染器（React/TS）
│   └── voice/             # 语音交互模块
├── apps/
│   ├── glasses-sim/       # AI 眼镜模拟器
│   ├── watch-sim/         # AI 手表模拟器
│   └── dashboard/         # Agent 管理面板
├── examples/
│   └── translate-agent/   # 翻译 Agent 示例
└── docs/                  # 设计文档
```

## 文档

- [系统架构](docs/architecture.md)
- [需求规格](docs/requirements.md)
- [实施方案](docs/implementation-plan.md)
- [技术栈](docs/tech-stack.md)

## 协议

| 协议 | 版本 | 用途 |
|------|------|------|
| A2A | v1.0.0 | Agent 间通信 |
| A2UI | v0.9.1 | 声明式 UI 渲染 |
| x402 | v0.1+ | HTTP 原生支付 |
| MCP | latest | 工具服务集成 |

## License

MIT