# 05 技术栈与环境（WearableAgent Hub）

> 本文档记录当前已验证的技术栈、依赖版本、开发环境配置与运行命令。

---

## 1. 项目技术栈总览

| 层 | 技术 | 说明 |
|----|------|------|
| 前端模拟器 | React 19 + TypeScript + Vite 6 + Tailwind | 眼镜/手表 HUD 模拟 |
| A2UI 渲染 | 自研 React 渲染器（`@wearable-hub/a2ui-renderer`） | 小屏 HUD 组件（Text/Card/List/StatusBar/Badge/Divider/HudCard/HudList/HudStatusBar） |
| 后端服务 | Python 3.13 + FastAPI + Uvicorn | 核心 Agent 引擎、WebSocket、REST API |
| A2A 协议 | `a2a-sdk==1.1.0`（protobuf-based） | Agent 间通信、Task 生命周期 |
| 语音交互 | WebSocket + 文本模拟模式 | `useVoiceSession` React Hook + 后端 WS 端点 |
| 支付 | TypeScript + Hono + x402 模拟 | 独立微服务（端口 8002），Mock 钱包 + 模拟结算 |
| 包管理 | pnpm 9.x（前端）+ conda expr（Python） | monorepo + 独立 Python 环境 |

---

## 2. 已验证依赖版本（开发机）

### 2.1 Python（conda `expr`）

- Python：`3.13`
- `a2a-sdk==1.1.0`
- `fastapi>=0.115`
- `uvicorn==0.43.0`
- `openai>=1.60`
- `pydantic>=2.12`
- `pydantic-settings`
- `httpx==0.28.1`
- `websockets==16.0`
- `sse-starlette>=3.4`
- `python-dotenv>=1.2.2`（环境变量）
- `pytest==9.1.1`（测试）

> 运行始终使用：`E:\Miniconda3\envs\expr\python.exe`

### 2.2 Node / 前端

- `vite==6.3.5`
- `typescript==~5.8.3`
- `react==^19.1.0`
- `react-dom==^19.1.0`
- `zustand==^4.5.7`
- `tailwindcss==^3.4.17`
- `recharts`（Dashboard 图表）
- `hono`（x402-pay 微服务）

---

## 3. 开发环境配置

### 3.1 Python 环境

```powershell
conda activate expr
python --version
# Python 3.13.x
```

**重要**：不要使用 `conda run`（本机存在临时文件锁问题），统一直接调用完整路径：

```powershell
E:\Miniconda3\envs\expr\python.exe -m pytest packages/core -q
```

### 3.2 前端环境

```powershell
pnpm install
pnpm dev
```

### 3.3 环境变量（.env）

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
OPENAI_MODEL=...
PROVIDER_TYPE=openai_compatible
BACKEND_PORT=8000
FRONTEND_PORT=5173
A2A_BASE_URL=http://localhost:8000
X402_PAY_URL=http://localhost:8002
```

---

## 4. 当前项目运行方式

### 4.1 一键启动

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-all.ps1
```

### 4.2 手动启动后端

```powershell
cd packages/core
E:\Miniconda3\envs\expr\python.exe -m uvicorn src.main:app --reload --port 8000
```

### 4.3 手动启动前端

```powershell
pnpm install
pnpm --filter @wearable-hub/glasses-sim dev
pnpm --filter @wearable-hub/watch-sim dev
pnpm --filter @wearable-hub/dashboard dev
```

### 4.4 启动示例 Agent

```powershell
# 翻译 Agent
cd examples/translate-agent
E:\Miniconda3\envs\expr\python.exe main.py

# 导航 Agent
cd examples/nav-agent
E:\Miniconda3\envs\expr\python.exe main.py

# 支付 Agent
cd examples/pay-agent
E:\Miniconda3\envs\expr\python.exe main.py
```

### 4.5 启动 x402 支付服务

```powershell
pnpm --filter @wearable-hub/x402-pay dev
```

---

## 5. 测试与质量

### 5.1 Python 单测

```powershell
E:\Miniconda3\envs\expr\python.exe -m pytest packages/core -q
```

当前状态：**30 个测试全部通过**。

### 5.2 TypeScript 构建验证

```powershell
pnpm -w run build
```

当前状态：**6 个项目全部构建成功**。

### 5.3 代码风格

- Python：`ruff` 格式化
- TypeScript：`prettier` 格式化

### 5.4 类型检查

- Python：`mypy`（建议开启）
- TypeScript：`tsc --noEmit`（strict 模式，`noUncheckedIndexedAccess: true`）

---

## 6. 端口分配

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