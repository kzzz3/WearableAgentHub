# WearableAgent Hub — AGENTS.md

## 项目定位

WearableAgent Hub 是一个面向 PC 本地的穿戴 AI Agent 原型系统。  
它的核心价值不是做一个完整产品，而是用来验证三件事：

1. **A2A 是否适合穿戴场景下的多 Agent 协作**
2. **A2UI 是否适合 HUD / 表盘等轻量信息界面**
3. **x402 是否适合微付费与 API 服务结算**

因此，这个仓库的正确理解方式是：

- 一个可运行的协议联调平台
- 一个穿戴 AI 场景的交互原型
- 一个可以给别人演示、讲解、学习的实验项目

## 设计目标

### 1. 真实协议联调
项目要能把 A2A、A2UI、x402 三条链路真实跑起来，而不是停留在文档描述。

### 2. 真实模型接入
默认 LLM 接入应基于真实 API。当前默认使用 MIMO 兼容接口，通过以下配置驱动：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `PROVIDER_TYPE`

也就是说，当前项目已经**配置接入了真实 MIMO API**，并且走的是标准 **chat-completion** 格式。

### 3. 本地可复现
整个系统应能在一台 PC 上完成启动、演示、调试，不依赖外部硬件。

### 4. 穿戴优先
UI 优先服务小屏信息展示：

- AI 眼镜 HUD
- AI 手表表盘
- 状态栏、卡片、列表、消息气泡等轻量组件

### 5. 渐进交付
优先保证最短链路可用，再扩展多设备、多 Agent、支付结算、语音模拟等能力。

### 6. 可讲解、可交接
仓库不仅要有代码，还要有清晰的：

- 目标说明
- 架构说明
- 协议说明
- 验证步骤
- 后续扩展方向

## 当前设计结论

### 已确认接入方式
当前 LLM 接入不是“仅写在文档里”，而是已经落到了配置和代码中：

- `.env` 已配置 MIMO endpoint、key、model
- `packages/core/src/config.py` 读取这些配置
- `packages/core/src/engine/agent_engine.py` 使用标准 `AsyncOpenAI` 发起 `chat.completions.create`
- `packages/core/src/main.py` 在启动日志中输出 `provider_type`、`model`、`base_url`

因此可以明确：

> **MIMO API 已经作为配置层真实接入。**

但也要注意一个重要边界：

> 当前是“配置已接入真实 API”，并不等同于“全链路真实联调已验收完毕”。

也就是说：
- 接入路径已经打通
- 默认配置已经指向真实 MIMO
- 但是否能在 A2A / A2UI / x402 全链路中稳定跑通，还需要实际端到端验证

## 项目结构

```text
WearableAgentHub/
├── AGENTS.md
├── README.md
├── docs/
├── packages/
│   ├── core/
│   ├── a2ui-renderer/
│   ├── x402-pay/
│   └── voice/
├── apps/
│   ├── glasses-sim/
│   ├── watch-sim/
│   └── dashboard/
├── examples/
│   ├── translate-agent/
│   ├── nav-agent/
│   └── pay-agent/
└── scripts/
```

## 开发约定

### Python 环境
- 使用 conda `expr` 环境
- 实际 Python 路径：`E:\Miniconda3\envs\expr\python.exe`
- 不使用 `conda run`

### 前端环境
- 使用 pnpm workspace 管理前端项目
- 前端与后端分离，但共享设计语言和协议约定

### 文档语言
- 面向开发者的说明文档可使用中文
- 代码标识符保持英文

### 命名与风格
- 文件名优先 `kebab-case`
- Python 函数优先 `snake_case`
- TypeScript 接口优先 `PascalCase`
- 配置项通过 `.env` 管理，不硬编码到业务代码

## 协议与接口约定

### A2A
- 用于 Agent 之间的发现与通信
- 优先遵循官方 SDK 的集成模式
- 在边界层处理协议类型与业务模型的转换

### A2UI
- 用于将 Agent 结构化结果渲染为穿戴端 UI
- 当前项目采用自研穿戴渲染器，而非通用后台 UI 方案

### x402
- 用于演示付费服务调用与结算链路
- 当前阶段以模拟支付和测试链路为主

## 验收原则

一个功能是否“完成”，应同时满足以下条件：

1. **文档里写清楚了目标**
2. **代码里实现了核心路径**
3. **本地实际可以运行**
4. **有可重复的验证方式**

例如对于 MIMO 接入，完整验收标准不是“写了 API key”，而是：

- 配置已生效
- 后端启动时可读取
- 真实请求可以发出
- 异常时有可理解的错误信息

## 后续目标

### 短期
- 把最短链路进一步打磨成稳定演示链路
- 明确哪些能力是“真实联调”，哪些仍是“模拟模式”

### 中期
- 增加更多 Agent 示例
- 增强 Dashboard 的观测能力
- 完善语音链路

### 长期
- 从 PC 模拟走向更接近真实穿戴体验的交互形态
- 从单机 demo 走向更完整的协议研究平台
