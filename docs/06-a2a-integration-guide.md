# 06 A2A 集成指南（a2a-sdk v1.1.0）

> 本文档基于当前工程已验证的 `a2a-sdk==1.1.0` API，给出可直接落地的集成模式。

---

## 1. 背景与约束

- `a2a-sdk v1.1.0` 的核心类型为 **protobuf 消息**（非 Pydantic）。
- 字段通过属性访问，枚举是整型语义（比较时注意使用枚举对象而非裸字符串）。
- 服务端核心：`AgentExecutor` + `DefaultRequestHandler` + `A2AStarletteApplication`。
- 客户端核心：`A2AClient` + `A2ACardResolver` + `create_client`。

---

## 2. 服务端集成（把 A2A 挂到 FastAPI）

### 2.1 最小可运行结构

```python
from fastapi import FastAPI
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handler import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard
```

### 2.2 定义 AgentCard

```python
agent_card = AgentCard(
    name="wearable-main-agent",
    description="主 Agent：接收穿戴端请求，调度 A2A 子任务",
    version="0.1.0",
)
```

### 2.3 实现 AgentExecutor

```python
class WearableMainExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # 1) 取输入
        user_text = context.get_user_input()

        # 2) 业务处理（LLM / 工具 / 规则）
        reply = f"收到：{user_text}"

        # 3) 通过事件队列返回结果
        通过 TaskUpdater（如 task_updater.complete / task_updater.failed）发送结果
```

### 2.4 创建 RequestHandler 并挂载

```python
executor = WearableMainExecutor()
task_store = InMemoryTaskStore()
handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=task_store,
    agent_card=agent_card,
)

a2a_app = A2AStarletteApplication(
    agent_card=agent_card,
    request_handler=handler,
)

app = FastAPI()
app.mount("/a2a", a2a_app.build())
```

---

## 3. 客户端集成（主 Agent 调用子 Agent）

### 3.1 解析 Agent Card

```python
from a2a.client import A2ACardResolver

resolver = A2ACardResolver(base_url="http://localhost:8010")
agent_card = await resolver.get_agent_card()
```

### 3.2 创建 Client 并发消息

```python
from a2a.client import create_client
from a2a.types import SendMessageRequest, Message, Part, Role

client = create_client(agent_card)

request = SendMessageRequest(
    message=Message(
        role=Role.ROLE_USER,
        parts=[Part(text="Hello World")],
    )
)

async for event in client.send_message(request):
    # 按 SDK 返回结构处理 task/stream
    pass
```

---

## 4. 任务生命周期（建议）

| 阶段 | 服务端动作 | 客户端期望 |
|------|-----------|-----------|
| 开始处理 | 标记 working | 收到中间状态 |
| 完成 | complete + artifact/message | 收到最终结果 |
| 失败 | failed | 收到错误信息 |
| 需要支付 | AUTH_REQUIRED + metadata | 客户端触发 x402 流程 |

---

## 5. 与当前工程的落地建议

### 5.1 目录落地

- `packages/a2a-server/`：放服务端集成抽象与默认实现
- `packages/core/`：保持现有 FastAPI 业务不变
- `examples/translate-agent/`：独立子进程 A2A Agent

### 5.2 渐进式接入顺序

1. 先给主 Agent 增加 `/a2a` 和 `/.well-known/agent-card.json`
2. 用最简 Executor 回显消息（验证链路）
3. 接入真实 LLM 逻辑
4. 引入 A2A Client 调用外部 Agent

---

## 6. 排错清单

| 现象 | 可能原因 | 排查点 |
|------|---------|--------|
| Agent Card 404 | 路由未挂载或挂载前缀错 | 检查 `app.mount(...)` 与访问路径 |
| 客户端连接超时 | 子 Agent 未启动 | 检查目标端口、健康检查 |
| 结果未到前端 | 事件未 enqueue | 检查 `通过 TaskUpdater（如 task_updater.complete / task_updater.failed）发送结果` |
| 字段读取报错 | 当成 dict 用了 | 改成属性访问（protobuf 对象） |
