# Week 4：LangGraph — 状态图编排

这是 6 周 Agent 开发课程的第四周。Week 3 用 CrewAI 实现了固定管线多 Agent 协作，本周用 **LangGraph** 把 Agent 工作流建模成**有向图**——对后端程序员来说，这是最自然的框架。

## 核心理念

LangGraph 不关心你是不是在用 LLM。它的本质是：**把任意 Python 函数编排成状态图（StateGraph）**。LLM 调用只是图中一个节点而已。

```
        ┌──────────┐
        │  START   │
        └────┬─────┘
             ▼
      ┌─────────────┐
      │   agent     │ ←── 处理节点（LLM 调用）
      └─────┬───────┘
            ▼
      ┌───────────┐
      │  router   │ ←── 条件路由：走 tools 还是 END？
      └─┬──────┬──┘
        │      │
   tools│      │END
        │      │
    ┌───▼──┐   │
    │tools │───┘
    └──────┘
```

## 5 步创建所有 LangGraph 应用

```python
# 1. 定义 State
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 2. 创建 StateGraph
graph_builder = StateGraph(State)

# 3. 添加节点（任意 Python 函数）
graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_node("tools", ToolNode(tools))

# 4. 添加边（普通边 + 条件边）
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)

# 5. 编译
graph = graph_builder.compile(checkpointer=MemorySaver())
```

## 项目结构

```
4_langgraph/
├── 1_lab1.ipynb           # Day 2：图的基础——StateGraph、Node、Edge
├── 2_lab2.ipynb           # Day 3：工具调用、条件路由、SQLite 检查点
├── 3_lab3.ipynb           # Day 4：异步图、Playwright 浏览器工具
├── 4_lab4.ipynb           # Day 4-5：Sidekick 多 Agent 项目
├── sidekick.py            # Sidekick 类的生产级实现
├── sidekick_tools.py      # 工具集（Playwright、搜索、文件、Python REPL）
├── app.py                 # Gradio UI 启动器
├── memory.db              # SQLite 检查点持久化
└── sandbox/               # 文件管理工具读写的工作目录
```

## 4 天学习路线

| Lab | 核心概念 | 难度 |
|-----|---------|------|
| `1_lab1.ipynb` | StateGraph / Node / Edge / compile | ⭐ |
| `2_lab2.ipynb` | ToolNode / 条件路由 / Agent Loop / SQLite 检查点 | ⭐⭐⭐ |
| `3_lab3.ipynb` | 异步图 / Playwright 浏览器自动化 | ⭐⭐ |
| `4_lab4.ipynb` + sidekick.py | 多 Agent 图 / 结构化输出 / 反馈循环 | ⭐⭐⭐⭐ |

## LangGraph 核心概念速查

| 概念 | 代码 | 用途 |
|------|------|------|
| 状态图 | `StateGraph(State)` | 定义图的结构 |
| 状态 | `TypedDict` + `Annotated[list, add_messages]` | 在节点间流动的数据 |
| 节点 | `graph.add_node("name", func)` | 图中的处理单元 |
| 普通边 | `graph.add_edge(A, B)` | 固定路由 |
| 条件边 | `graph.add_conditional_edges(A, router, {...})` | 动态路由 |
| 编译 | `graph.compile(checkpointer=...)` | 生成可执行的图 |
| 调用 | `graph.invoke(state)` / `graph.ainvoke(state)` | 执行图 |
| 工具绑定 | `llm.bind_tools(tools)` | 让 LLM 能调用工具 |
| 工具节点 | `ToolNode(tools)` | 执行工具调用的预构建节点 |
| 工具路由 | `tools_condition` | 判断是否有 tool_calls 的预构建路由 |
| 检查点 | `MemorySaver()` / `SqliteSaver(conn)` | 持久化状态 |
| 线程 | `{"configurable": {"thread_id": "1"}}` | 隔离对话 |
| 结构化输出 | `llm.with_structured_output(PydanticModel)` | 类型安全的 LLM 响应 |

## 用 DeepSeek 替代 OpenAI

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
```

## 什么时候用 LangGraph

- 需要精确控制 Agent 的每一步流程
- 需要条件分支、循环、人工审批
- 需要状态持久化和回滚
- 需要多个 Agent 之间有复杂的交互逻辑
- 对后端程序员来说思维模型最自然（图 = DAG）

## 参考资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangGraph 教程](https://langchain-ai.github.io/langgraph/tutorials/)
- 详细学习指南：[学习指南.md](学习指南.md)
- 中文导航：[../docs/中文学习导航.md](../docs/中文学习导航.md)
