# Week 5：AutoGen — 分布式多 Agent 系统

这是 6 周 Agent 开发课程的第五周。Week 4 用 LangGraph 精确控制单进程内的 Agent 流程，本周用微软的 **AutoGen** 把 Agent 分布到不同进程、不同机器上运行——通过消息总线通信。

## 核心理念

AutoGen 把 Agent 之间的通信抽象成**消息传递**。Agent 不直接调用彼此，而是向 Runtime 发送和接收消息。Runtime 可以是单线程的（SingleThreadedAgentRuntime），也可以是通过 gRPC 跨进程的（GrpcWorkerAgentRuntime）。

```
Agent A ──send(message)──►  Runtime  ──route──► Agent B
                                                        │
                                              @message_handler
                                                        │
Agent A ◄── return Message ◄── Runtime ◄── return Message
```

## AutoGen 三层架构

```
┌──────────────────────────────────────────────┐
│  AgentChat（高层 API）                         │
│  AssistantAgent + Tool + RoundRobinGroupChat  │
│  适合：快速搭建多 Agent 对话                   │
├──────────────────────────────────────────────┤
│  Core（中层 API）                              │
│  RoutedAgent + @message_handler + AgentId     │
│  适合：精确控制消息路由                        │
├──────────────────────────────────────────────┤
│  Distributed Core（底层）                      │
│  GrpcWorkerAgentRuntime + gRPC Host           │
│  适合：跨进程 / 跨机器分布式部署               │
└──────────────────────────────────────────────┘
```

## 项目结构

```
5_autogen/
├── 1_lab1_autogen_agentchat.ipynb    # Day 1：AgentChat 入门（Model/Message/Agent/Tool）
├── 2_lab2_autogen_agentchat.ipynb    # Day 2：AgentChat 进阶（多模态/结构化输出/Team/MCP）
├── 3_lab3_autogen_core.ipynb         # Day 3：AutoGen Core（RoutedAgent/Runtime/消息路由）
├── 4_lab4_autogen_distributed.ipynb  # Day 4：分布式 gRPC（跨进程 Agent）
├── agent.py                          # RoutedAgent 模板（创意企业家角色）
├── creator.py                        # Creator Agent——动态生成新 Agent 代码
├── messages.py                       # 通用 Message 类型 + find_recipient()
├── world.py                          # 分布式编排器——启动 20 个 Agent
├── sandbox/                          # 文件输出目录
└── community_contributions/          # 学员项目（~45 个）
```

## 4 天学习路线

| Lab | 核心概念 | 难度 |
|-----|---------|------|
| `1_lab1_autogen_agentchat.ipynb` | ModelClient / AssistantAgent / on_messages / FunctionTool | ⭐ |
| `2_lab2_autogen_agentchat.ipynb` | 多模态 / 结构化输出 / RoundRobinGroupChat / MCP | ⭐⭐⭐ |
| `3_lab3_autogen_core.ipynb` | RoutedAgent / @message_handler / AgentId / Runtime.send_message | ⭐⭐⭐⭐ |
| `4_lab4_autogen_distributed.ipynb` + world.py | gRPC Host/Worker / 分布式 / Creator 自复制 Agent | ⭐⭐⭐⭐⭐ |

## AutoGen 核心概念速查

| 概念 | 代码 | 用途 |
|------|------|------|
| 模型客户端 | `OpenAIChatCompletionClient(model="gpt-4o-mini")` | 统一封装各种 LLM |
| 消息 | `TextMessage` / `MultiModalMessage` | Agent 间通信的载体 |
| Agent（高层） | `AssistantAgent(name, model_client, tools)` | 开箱即用的 Agent |
| 工具函数 | `tools=[my_function]` | Agent 可调用的 Python 函数 |
| LangChain 工具适配 | `LangChainToolAdapter(tool)` | 复用 LangChain 生态的工具 |
| 结构化输出 | `output_content_type=PydanticModel` | 类型安全的 Agent 输出 |
| 团队 | `RoundRobinGroupChat(agents, termination)` | 多 Agent 轮流对话 |
| 终止条件 | `TextMentionTermination("APPROVE")` | 检测到特定文本时停止 |
| MCP | `mcp_server_tools(StdioServerParams(...))` | 接入 MCP 工具 |
| RoutedAgent | `class MyAgent(RoutedAgent):` | 自定义消息路由 Agent |
| 消息处理器 | `@message_handler` | 标记处理特定消息的方法 |
| Agent ID | `AgentId(type, key)` | 唯一标识一个 Agent |
| 单线程 Runtime | `SingleThreadedAgentRuntime()` | 进程内消息路由 |
| gRPC Host | `GrpcWorkerAgentRuntimeHost(address)` | 分布式消息中枢 |
| gRPC Worker | `GrpcWorkerAgentRuntime(host_address)` | 远程 Agent 运行时 |
| Agent 注册 | `await Agent.register(runtime, name, factory)` | 向 Runtime 注册 Agent |
| 发送消息 | `runtime.send_message(msg, agent_id)` | 向指定 Agent 发消息 |
| Agent 间通信 | `self.send_message(msg, agent_id)` | Agent 直接向其他 Agent 发消息 |
| 桥接模式 | `self._delegate = AssistantAgent(...)` | Core 包装 AgentChat |

## 用 DeepSeek 替代 OpenAI

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
```

## 什么时候用 AutoGen

- Agent 需要分布在不同的进程/机器上运行
- 需要 Agent 之间通过消息总线松耦合通信
- 需要动态创建和销毁 Agent
- 需要多个 Agent 并发执行并通过消息协调

## 注意

AutoGen 于 2025 年 9 月宣布进入"维护模式"，其继任者是 **Microsoft Agent Framework**（`agent_framework`）。本课程仍有学习价值——消息驱动、分布式 Agent 的模式在后续框架中延续。

## 参考资源

- [AutoGen 官方文档](https://microsoft.github.io/autogen/)
- 详细学习指南：[学习指南.md](学习指南.md)
- 中文导航：[../docs/中文学习导航.md](../docs/中文学习导航.md)
