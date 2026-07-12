# 实施方案

## 1. 项目里程碑

`
Week 1-2:  Phase 1 — 最短链路 MVP（文字输入 → HUD 显示）
Week 3:    Phase 2 — A2A 协议完整实现
Week 4:    Phase 3 — x402 支付结算
Week 5:    Phase 4 — 语音交互 + 体验优化
`

---

## 2. Phase 1: 最短链路 MVP（Week 1-2）

### 目标

跑通 "文字输入 → LLM → A2UI JSON → WebSocket → HUD 渲染" 的最短链路。

### 2.1 Day 1-2: 项目脚手架

**任务**:

1. 初始化 pnpm monorepo
2. 配置 TypeScript/Vite (前端)
3. 配置 Python/FastAPI (后端)
4. 配置 ESLint/Prettier/ruff
5. 编写 pnpm-workspace.yaml
6. 配置 Git hooks (husky + lint-staged)

**目录结构创建**:

`ash
wearable-agent-hub/
├── package.json           # root package.json (pnpm workspace)
├── pnpm-workspace.yaml
├── tsconfig.base.json
├── .eslintrc.cjs
├── .prettierrc
├── packages/
│   ├── core/              # Python package (pyproject.toml)
│   │   ├── pyproject.toml
│   │   └── src/
│   ├── a2ui-renderer/     # TS library package
│   │   ├── package.json
│   │   └── src/
│   └── voice/             # TS library package
│       ├── package.json
│       └── src/
├── apps/
│   └── glasses-sim/       # Vite + React app
│       ├── package.json
│       ├── vite.config.ts
│       └── src/
└── examples/
    └── translate-agent/
        └── pyproject.toml
`

**交付物**: 可运行的空项目骨架，pnpm dev 能启动前端，uvicorn 能启动后端。

### 2.3 Day 3-4: 后端 Agent 引擎

**文件清单**:

`
packages/core/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── agent_engine.py      # Agent 核心引擎
│   │   ├── intent_parser.py     # 意图解析（LLM）
│   │   └── response_builder.py  # 响应构建
│   ├── a2ui/
│   │   ├── __init__.py
│   │   ├── generator.py         # A2UI JSON 生成器
│   │   └── templates.py         # 预定义模板
│   ├── ws/
│   │   ├── __init__.py
│   │   └── manager.py           # WebSocket 管理器
│   └── models/
│       ├── __init__.py
│       └── message.py           # 消息模型
└── tests/
    ├── test_agent_engine.py
    ├── test_a2ui_generator.py
    └── test_ws_manager.py
`

**关键代码设计**:

`python
# packages/core/src/engine/agent_engine.py
class AgentEngine:
    """Agent 核心引擎：接收用户输入，调用 LLM，返回 A2UI 消息"""

    def __init__(self, llm_client, a2ui_generator):
        self.llm = llm_client
        self.a2ui = a2ui_generator

    async def process(self, user_input: str, context: dict) -> list[dict]:
        """
        处理用户输入，返回 A2UI 消息列表

        Returns:
            A2UI JSON-RPC 消息列表：
            [createSurface, updateComponents, updateDataModel, ...]
        """
        # 1. LLM 理解意图
        intent = await self.llm.parse(user_input, context)

        # 2. 执行动作（调用工具/Agent 或直接回复）
        result = await self._execute(intent)

        # 3. 生成 A2UI 消息
        return self.a2ui.generate(result)


# packages/core/src/a2ui/generator.py
class A2UIGenerator:
    """A2UI JSON 消息生成器"""

    def generate(self, data: dict) -> list[dict]:
        """将结构化数据转为 A2UI 消息序列"""
        messages = []
        surface_id = f"surface-{uuid4().hex[:8]}"

        # 1. 创建 Surface
        messages.append({
            "type": "createSurface",
            "surfaceId": surface_id,
            "presentation": {"mode": "card"}
        })

        # 2. 添加组件
        components = self._build_components(data)
        messages.append({
            "type": "updateComponents",
            "surfaceId": surface_id,
            "components": components
        })

        # 3. 绑定数据
        if data.get("data"):
            messages.append({
                "type": "updateDataModel",
                "surfaceId": surface_id,
                "operations": [{"op": "add", "path": "/", "value": data["data"]}]
            })

        return messages
`

**依赖**:

`	oml
# packages/core/pyproject.toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "openai>=1.60",
    "pydantic>=2.10",
    "websockets>=14.0",
]
`

**交付物**: FastAPI 后端可接收 POST /chat 请求，返回 A2UI JSON 消息。

### 2.4 Day 5-6: A2UI 渲染器 + 眼镜模拟器

**文件清单**:

`
packages/a2ui-renderer/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts
│   ├── core/
│   │   ├── A2UIParser.ts        # JSON 流解析器
│   │   ├── SurfaceManager.ts    # Surface 状态管理
│   │   ├── ComponentRegistry.ts # 组件注册表
│   │   └── DataModel.ts         # 数据模型
│   ├── components/
│   │   ├── base/
│   │   │   ├── Text.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Button.tsx
│   │   │   ├── List.tsx
│   │   │   └── Image.tsx
│   │   └── wearable/
│   │       ├── HudCard.tsx      # HUD 信息卡片
│   │       └── StatusBar.tsx    # 状态栏
│   ├── hooks/
│   │   ├── useA2UIStream.ts     # WebSocket 流 Hook
│   │   └── useSurface.ts
│   └── themes/
│       └── glasses-dark.ts      # 眼镜深色主题

apps/glasses-sim/
├── package.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── pages/
│   │   ├── HudView.tsx          # HUD 主视图
│   │   └── Settings.tsx         # 设置页
│   ├── components/
│   │   ├── HudOverlay.tsx       # HUD 浮层
│   │   ├── VoiceIndicator.tsx   # 语音状态指示
│   │   └── InputBar.tsx         # 文字输入栏（MVP 阶段）
│   ├── services/
│   │   └── ws.ts                # WebSocket 服务
│   └── styles/
│       ├── glasses.css          # 眼镜主题样式
│       └── global.css
`

**关键代码设计**:

`	ypescript
// packages/a2ui-renderer/src/core/SurfaceManager.ts
class SurfaceManager {
  private surfaces = new Map<string, Surface>();

  handleMessage(msg: A2UIMessage) {
    switch (msg.type) {
      case 'createSurface':
        this.surfaces.set(msg.surfaceId, new Surface(msg));
        break;
      case 'updateComponents':
        this.surfaces.get(msg.surfaceId)?.updateComponents(msg.components);
        break;
      case 'updateDataModel':
        this.surfaces.get(msg.surfaceId)?.updateData(msg.operations);
        break;
      case 'deleteSurface':
        this.surfaces.delete(msg.surfaceId);
        break;
    }
  }
}

// packages/a2ui-renderer/src/hooks/useA2UIStream.ts
function useA2UIStream(wsUrl: string) {
  const [surfaces, setSurfaces] = useState<Surface[]>([]);
  const manager = useRef(new SurfaceManager());

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      manager.current.handleMessage(msg);
      setSurfaces(manager.current.getAll());
    };
    return () => ws.close();
  }, [wsUrl]);

  return surfaces;
}
`

**交付物**: 眼镜模拟器可在浏览器打开，通过 WebSocket 接收 A2UI 消息并渲染 HUD 卡片。

### 2.5 Day 7-8: WebSocket 连通 + 端到端联调

**任务**:

1. 后端 WebSocket 端点 (/ws)
2. 前端 WebSocket 服务连接
3. 文字输入 → 后端 LLM → A2UI JSON → WebSocket → 前端渲染
4. 端到端测试

**交付物**: 完整链路可运行。用户在输入框输入文字，眼镜 HUD 显示 Agent 回复。

### 2.6 Day 9-10: 联调 + Bug 修复 + 文档

**任务**:

1. 端到端测试
2. 错误处理完善
3. 加载状态/错误状态 UI
4. README 编写
5. Demo 录制

**Phase 1 完成标准**:

- [ ] 输入 "附近有什么咖啡店" → HUD 显示咖啡店列表卡片
- [ ] 输入 "帮我翻译 Hello World" → HUD 显示翻译结果
- [ ] WebSocket 连接稳定，断线自动重连
- [ ] 无 TypeScript/Python 编译错误

---

## 3. Phase 2: A2A 协议（Week 3）

### 目标

实现 A2A v1.0 协议，让两个 Agent 可以互相发现和调用。

### 任务清单

| Day | 任务 | 交付物 |
|-----|------|--------|
| D1 | A2A Server 基础框架 | JSON-RPC 2.0 端点 /a2a |
| D2 | Agent Card 实现 | /.well-known/agent.json 端点 |
| D3 | Task 状态机 | submitted → working → completed |
| D4 | 示例翻译 Agent | examples/translate-agent/ |
| D5 | A2A Client + Dashboard | Agent 列表、通信日志 |

### 关键实现

`python
# packages/a2a-server/src/handlers/message_handler.py
class MessageHandler:
    async def handle_send(self, params: SendMessageParams) -> Task:
        """处理 message/send 请求"""
        task = self.task_manager.create_or_update(
            task_id=params.task_id,
            message=params.message,
        )
        # 异步处理任务
        asyncio.create_task(self._process_task(task))
        return task

    async def _process_task(self, task: Task):
        """处理任务：调用 LLM 或转发给其他 Agent"""
        try:
            task.status = "working"
            result = await self.engine.process(task.messages[-1])
            task.artifacts = result.artifacts
            task.status = "completed"
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
`

`json
// Agent Card 示例
{
  "name": "WearableHub Translator Agent",
  "description": "多语言翻译 Agent",
  "url": "http://localhost:8010/a2a",
  "version": "0.1.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "translate",
      "name": "翻译",
      "description": "支持中英日韩翻译",
      "inputModes": ["text"],
      "outputModes": ["text"]
    }
  ]
}
`

---

## 4. Phase 3: x402 支付（Week 4）

### 目标

实现 Agent 间的 x402 自动支付结算。

### 任务清单

| Day | 任务 | 交付物 |
|-----|------|--------|
| D1 | x402 支付服务搭建 | TypeScript 支付微服务 |
| D2 | 测试网钱包配置 | Base Sepolia + USDC |
| D3 | A2A x402 扩展集成 | payment-required 流程 |
| D4 | 付费翻译 Agent | 0.01 USDC/次翻译 |
| D5 | Dashboard 支付记录 | 支付历史页面 |

### 支付流程实现

`	ypescript
// packages/x402-pay/src/payment_flow.ts
class PaymentFlow {
  async handlePaymentRequired(task: Task, paymentRequired: PaymentRequired) {
    // 1. 获取支付需求
    const requirements = paymentRequired.accepts[0];

    // 2. 验证价格合理性
    if (BigInt(requirements.maxAmountRequired) > MAX_PAYMENT) {
      throw new Error('Payment exceeds maximum allowed');
    }

    // 3. 签名支付
    const signature = await this.wallet.signPayment(requirements);

    // 4. 提交支付
    return {
      scheme: requirements.scheme,
      network: requirements.network,
      payload: signature,
    };
  }
}
`

---

## 5. Phase 4: 语音 + 体验优化（Week 5）

### 目标

集成 OpenAI Realtime API，完成手表模拟器，优化整体体验。

### 任务清单

| Day | 任务 | 交付物 |
|-----|------|--------|
| D1 | OpenAI Realtime API 集成 | 实时语音对话 |
| D2 | VAD + 打断检测 | 语音活动检测 |
| D3 | 手表模拟器 | watch-sim 应用 |
| D4 | 多 Agent 协作示例 | 眼镜+手表联动 |
| D5 | 主题系统 + 文档 | 完整文档 |

---

## 6. 开发环境搭建

### 前置条件

`ash
# 安装 Node.js 20+
winget install OpenJS.NodeJS.LTS

# 安装 pnpm
npm install -g pnpm

# Python 环境: 使用 conda expr (Python 3.13)
# 已有 conda expr 环境，无需额外安装

# 安装 uv (Python 包管理)
# uv not needed — using conda expr

# 安装 Git
winget install Git.Git
`

### 项目初始化

`ash
# 克隆仓库
git clone <repo-url>
cd wearable-agent-hub

# 安装前端依赖
pnpm install

# 安装后端依赖
cd packages/core && pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 启动开发
pnpm dev          # 前端（所有 app 并行启动）
conda run -n expr uvicorn src.main:app --reload  # 后端
`

### 环境变量

`ash
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# x402 支付
X402_WALLET_PRIVATE_KEY=0x...
X402_NETWORK=base-sepolia

# A2A
A2A_BASE_URL=http://localhost:8000

# Python 环境
# 所有 Python 命令使用: conda activate expr
# 或: conda run -n expr <command>
`

---

## 7. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| OpenAI Realtime API 延迟高 | 语音体验差 | 降级为 Chat API + TTS 方案 |
| A2A SDK 更新导致 API 变化 | 开发返工 | 锁定 SDK 版本，关注 changelog |
| x402 测试网不稳定 | 支付测试受阻 | 实现 mock 支付模式 |
| A2UI 组件不够丰富 | HUD 表现力不足 | 参考官方渲染器扩展组件 |
| 跨语言调用复杂（Python↔TS） | x402 集成困难 | 使用 HTTP API 桥接 |
