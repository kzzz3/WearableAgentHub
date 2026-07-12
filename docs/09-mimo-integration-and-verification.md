# MIMO 接入与验证说明

## 1. 目的

本文档用于明确 WearableAgent Hub 当前对 MIMO API 的接入状态，并给出后续验证方法。

## 2. 当前结论

当前项目已经完成 **配置层的真实 MIMO 接入**。

也就是说：
- `.env` 已经配置了 MIMO endpoint、API key、模型名
- 核心引擎已经通过标准 OpenAI 兼容方式发起请求
- 后端启动时会读取并输出这些配置

因此可以明确：

> MIMO API 已经作为默认 LLM 提供方接入项目。

## 3. 当前接入方式

当前接入方式不是“专用 MIMO SDK”，而是通过 **OpenAI 兼容接口** 接入。

配置项包括：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1`
- `OPENAI_MODEL=mimo-v2.5-pro`
- `PROVIDER_TYPE=openai_compatible`

代码层面：

- `packages/core/src/config.py` 负责读取配置
- `packages/core/src/engine/agent_engine.py` 使用 `AsyncOpenAI` 创建客户端
- `packages/core/src/engine/agent_engine.py` 调用 `chat.completions.create`
- `packages/core/src/main.py` 在启动日志中输出：
  - `provider_type`
  - `model`
  - `base_url`

## 4. 这意味着什么

这意味着项目当前具备以下能力：

- 默认推理链路指向真实 MIMO
- 不必手工替换为其他模型即可运行
- 代码与配置已经解耦，后续可以替换为其他兼容接口

但也要注意：

> “配置已接入”不等于“全链路真实验收已完成”。

## 5. 已验证点

从当前仓库状态看，以下部分已确认成立：

- `.env` 已包含真实配置
- `.env.example` 保留了相同默认配置结构
- `config.py` 已定义相关字段
- `agent_engine.py` 已使用标准 chat-completion 调用
- `main.py` 已在启动日志输出 provider 配置

## 6. 建议验证步骤

### 6.1 启动验证

启动后端后，检查日志是否包含：

- `provider_type=openai_compatible`
- `model=mimo-v2.5-pro`
- `base_url=https://token-plan-cn.xiaomimimo.com/v1`

### 6.2 健康检查验证

访问后端健康检查接口，确认服务正常运行，并检查是否携带当前模型信息。

### 6.3 文字链路验证

在眼镜 HUD 或通过接口发送一条普通问题，确认：

- 后端能返回结果
- 前端能渲染结果
- 结果不是 mock 占位，而是真实模型返回

### 6.4 错误链路验证

故意修改 API key 或 base_url，确认系统能返回可理解的错误，而不是静默失败。

## 7. 当前限制

当前阶段的限制主要有两点：

1. 尽管已接入 MIMO，但项目还需要进行更完整的端到端验证  
2. 当前 `provider_type` 主要用于标识和日志，还没有扩展成完整的多 provider 策略框架

## 8. 后续建议

### 短期建议
- 围绕 MIMO 建立一条稳定的核心演示链路
- 把“配置接入”升级为“可重复验收”

### 中期建议
- 增加 provider 切换能力
- 增加请求失败与重试策略
- 增加 dashboard 中对当前模型配置的展示

### 长期建议
- 将 LLM 接入抽象为统一 provider 层
- 支持 MIMO / OpenAI / 本地模型等多后端切换
