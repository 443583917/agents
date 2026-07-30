# MCP（Model Context Protocol）知识总结

## 一、什么是 MCP？

MCP（Model Context Protocol，模型上下文协议）是由 Anthropic 提出的**开放标准协议**，用于规范 AI 模型与外部工具/数据源之间的通信。

**核心思想**：将 AI 模型需要的"能力"（工具、数据、提示词）标准化为可插拔的 MCP 服务器，任何 AI 客户端都能通过统一协议调用。

### 类比理解

```
USB 协议：电脑 ←→ 各种外设（键盘、鼠标、U盘）
MCP 协议：AI Agent ←→ 各种能力（搜索、数据库、文件系统）
```

---

## 二、MCP 核心概念

### 2.1 三大原语（Primitives）

| 原语 | 说明 | 方向 | 本项目示例 |
|------|------|------|-----------|
| **Tools（工具）** | AI 可主动调用的函数 | Model → Server | `buy_shares()`, `lookup_share_price()` |
| **Resources（资源）** | 只读的数据端点，通过 URI 访问 | Client → Server | `accounts://accounts_server/{name}` |
| **Prompts（提示词）** | 预定义的提示词模板 | Client → Server | 本项目未使用 |

### 2.2 通信方式

| 传输方式 | 适用场景 | 本项目使用 |
|----------|----------|-----------|
| **stdio** | 本地子进程通信 | ✅ 所有服务器 |
| **SSE** | 远程 HTTP 通信 | ❌ |
| **Streamable HTTP** | 新一代远程通信 | ❌ |

### 2.3 架构角色

```
┌─────────────────────────────────────────────────────┐
│                    MCP 客户端                         │
│  (MCPServerStdio / stdio_client)                     │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Tool调用  │  │ Resource │  │ Prompt   │           │
│  │          │  │ 读取     │  │ 获取     │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │              │              │                 │
│       └──────────────┼──────────────┘                 │
│                      │ stdin/stdout                   │
└──────────────────────┼───────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
│ MCP Server  │ │ MCP Server  │ │ MCP Server  │
│ (accounts)  │ │ (market)    │ │ (push)      │
│             │ │             │ │             │
│ @mcp.tool() │ │ @mcp.tool() │ │ @mcp.tool() │
│ @mcp.resource│ │             │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
```

---

## 三、本项目架构解析

### 3.1 项目结构

```
6_mcp/
├── 核心业务逻辑
│   ├── accounts.py          # 账户模型（余额、持仓、交易）
│   ├── database.py          # SQLite 数据库操作
│   ├── market.py            # 股价查询（Polygon API / 随机数）
│   └── templates.py         # Agent 提示词模板
│
├── MCP 服务器（3个）
│   ├── accounts_server.py   # 账户管理 MCP 服务器
│   ├── market_server.py     # 市场数据 MCP 服务器
│   └── push_server.py       # 推送通知 MCP 服务器
│
├── MCP 客户端
│   └── accounts_client.py   # 原生 MCP 客户端示例
│
├── Agent 系统
│   ├── traders.py           # 交易员 Agent（核心）
│   ├── trading_floor.py     # 调度器（并发运行4个交易员）
│   └── mcp_params.py        # MCP 服务器参数配置
│
├── 可视化
│   ├── app.py               # Gradio Web UI
│   ├── tracers.py           # 执行日志追踪
│   └── util.py              # UI 工具函数
│
└── 辅助
    └── reset.py             # 重置交易员账户
```

### 3.2 数据流

```
用户运行 trading_floor.py
        │
        ▼
创建 4 个 Trader（Warren, George, Ray, Cathie）
        │
        ▼
每个 Trader 启动 6 个 MCP 服务器子进程
  ├── accounts_server.py  （账户管理）
  ├── push_server.py      （推送通知）
  ├── market_server.py    （市场数据）
  ├── mcp-server-fetch    （网页抓取）
  ├── brave-search        （搜索引擎）
  └── memory-libsql       （知识图谱）
        │
        ▼
Trader Agent 调用 Researcher Agent（作为工具）搜索新闻
        │
        ▼
Trader Agent 根据研究结果调用 buy_shares / sell_shares
        │
        ▼
accounts_server 更新 SQLite 数据库
        │
        ▼
push_server 发送交易通知
        │
        ▼
Gradio UI 从数据库读取数据实时展示
```

---

## 四、MCP 服务器开发详解

### 4.1 使用 FastMCP 创建服务器

```python
# 最简 MCP 服务器模板
from mcp.server.fastmcp import FastMCP

# 1. 创建服务器实例
mcp = FastMCP("my_server")

# 2. 注册工具（AI 可调用的函数）
@mcp.tool()
async def my_tool(param: str) -> str:
    """工具描述 - AI 根据这个描述决定何时调用

    Args:
        param: 参数说明
    """
    return f"结果: {param}"

# 3. 注册资源（只读数据端点）
@mcp.resource("my://data/{id}")
async def read_data(id: str) -> str:
    """通过 URI 读取数据"""
    return f"数据内容: {id}"

# 4. 运行服务器
if __name__ == "__main__":
    mcp.run(transport='stdio')  # 使用 stdio 传输
```

### 4.2 本项目中的 3 个 MCP 服务器

#### accounts_server.py — 账户管理服务器

```python
# 提供 5 个工具 + 2 个资源
@mcp.tool()  get_balance(name)        → 查询现金余额
@mcp.tool()  get_holdings(name)       → 查询持仓
@mcp.tool()  buy_shares(...)          → 买入股票
@mcp.tool()  sell_shares(...)         → 卖出股票
@mcp.tool()  change_strategy(...)     → 更改投资策略

@mcp.resource("accounts://accounts_server/{name}")  → 账户报告
@mcp.resource("accounts://strategy/{name}")          → 投资策略
```

#### market_server.py — 市场数据服务器

```python
# 提供 1 个工具
@mcp.tool()  lookup_share_price(symbol) → 查询股价
```

#### push_server.py — 推送通知服务器

```python
# 提供 1 个工具
@mcp.tool()  push(args) → 发送手机推送通知
```

---

## 五、MCP 客户端使用详解

### 5.1 方式一：OpenAI Agents SDK（推荐）

```python
from agents.mcp import MCPServerStdio
from agents import Agent, Runner

# 配置服务器启动参数
params = {"command": "uv", "args": ["run", "accounts_server.py"]}

# 启动 MCP 服务器并创建 Agent
async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as server:
    # 列出服务器提供的工具
    tools = await server.list_tools()

    # 创建 Agent 并绑定 MCP 服务器
    agent = Agent(
        name="my_agent",
        instructions="你是一个交易助手",
        model="gpt-4o-mini",
        mcp_servers=[server]  # Agent 自动发现并使用 MCP 工具
    )

    # 运行 Agent
    result = await Runner.run(agent, "帮我查询 Warren 的账户余额")
    print(result.final_output)
```

### 5.2 方式二：原生 MCP 客户端

```python
import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

params = StdioServerParameters(command="uv", args=["run", "accounts_server.py"], env=None)

async with stdio_client(params) as streams:
    async with mcp.ClientSession(*streams) as session:
        await session.initialize()

        # 列出工具
        tools = await session.list_tools()

        # 调用工具
        result = await session.call_tool("get_balance", {"name": "Warren"})

        # 读取资源
        resource = await session.read_resource("accounts://accounts_server/warren")
```

### 5.3 方式三：转换为 OpenAI FunctionTool

```python
from agents import FunctionTool

# 将 MCP 工具转换为 OpenAI Agents SDK 的 FunctionTool
for tool in await server.list_tools():
    schema = {**tool.inputSchema, "additionalProperties": False}
    openai_tool = FunctionTool(
        name=tool.name,
        description=tool.description,
        params_json_schema=schema,
        on_invoke_tool=lambda ctx, args, tn=tool.name: call_tool(tn, json.loads(args))
    )
```

---

## 六、外部 MCP 服务器使用

### 6.1 常用外部 MCP 服务器

| 服务器 | 用途 | 启动命令 |
|--------|------|----------|
| `mcp-server-fetch` | 网页抓取 | `uvx mcp-server-fetch` |
| `@modelcontextprotocol/server-brave-search` | Brave 搜索 | `npx -y @modelcontextprotocol/server-brave-search` |
| `mcp-memory-libsql` | 知识图谱/持久记忆 | `npx -y mcp-memory-libsql` |
| `@playwright/mcp@latest` | 浏览器自动化 | `npx @playwright/mcp@latest` |
| `@modelcontextprotocol/server-filesystem` | 文件系统访问 | `npx -y @modelcontextprotocol/server-filesystem` |
| `mcp_polygon` | Polygon 股票数据 | `uvx --from git+... mcp_polygon` |

### 6.2 启动命令对照

```python
# Python 包 - 使用 uvx（临时运行，无需安装）
{"command": "uvx", "args": ["mcp-server-fetch"]}

# Python 脚本 - 使用 uv run
{"command": "uv", "args": ["run", "my_server.py"]}

# Node.js 包 - 使用 npx
{"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"]}

# 带环境变量的启动
{
    "command": "npx",
    "args": ["-y", "mcp-memory-libsql"],
    "env": {"LIBSQL_URL": "file:./memory/my.db"}  # 注入环境变量
}
```

---

## 七、高级模式

### 7.1 Agent-as-Tool（代理即工具）

本项目的核心设计模式：将一个 Agent 包装为另一个 Agent 的工具。

```python
# 创建研究员 Agent
researcher = Agent(name="Researcher", instructions="...", mcp_servers=[...])

# 将研究员转换为工具
researcher_tool = researcher.as_tool(
    tool_name="Researcher",
    tool_description="研究在线新闻和投资机会"
)

# 交易员 Agent 使用研究员工具
trader = Agent(
    name="Warren",
    instructions="...",
    tools=[researcher_tool],  # 研究员作为工具
    mcp_servers=[...]         # 交易员自己的 MCP 服务器
)
```

**优势**：
- 关注点分离：研究员专注研究，交易员专注交易
- 可复用：多个交易员共享同一个研究员工具
- 可追踪：每次研究调用都有独立的 trace

### 7.2 多服务器管理

```python
from contextlib import AsyncExitStack

async with AsyncExitStack() as stack:
    # 批量启动多个 MCP 服务器
    servers = [
        await stack.enter_async_context(
            MCPServerStdio(params, client_session_timeout_seconds=120)
        )
        for params in server_params_list
    ]

    # 所有服务器在退出 with 块时自动关闭
    agent = Agent(..., mcp_servers=servers)
    await Runner.run(agent, "任务描述")
```

### 7.3 多模型支持

```python
from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

# 不同 LLM 提供商使用 OpenAI 兼容接口
deepseek = OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=AsyncOpenAI(base_url="https://api.deepseek.com/v1", api_key=...)
)

gemini = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=AsyncOpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=...)
)

# Agent 选择模型
agent = Agent(name="...", model=deepseek)  # 或 model="gpt-4o-mini"
```

---

## 八、可执行案例代码

### 案例 1：最简 MCP 服务器 + 客户端

```python
# === server.py ===
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool()
async def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b

@mcp.tool()
async def greet(name: str) -> str:
    """打招呼"""
    return f"你好，{name}！"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

```python
# === client.py ===
from agents.mcp import MCPServerStdio
from agents import Agent, Runner

async def main():
    params = {"command": "uv", "args": ["run", "server.py"]}

    async with MCPServerStdio(params=params) as server:
        tools = await server.list_tools()
        print("可用工具:", [t.name for t in tools])

        agent = Agent(
            name="demo_agent",
            instructions="使用工具回答用户问题",
            model="gpt-4o-mini",
            mcp_servers=[server]
        )

        result = await Runner.run(agent, "计算 3 + 5，然后用中文跟我打招呼，我叫小明")
        print(result.final_output)

import asyncio
asyncio.run(main())
```

### 案例 2：带资源的 MCP 服务器

```python
# === resource_server.py ===
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resource_demo")

# 模拟数据库
users = {
    "alice": {"name": "Alice", "age": 30, "role": "engineer"},
    "bob": {"name": "Bob", "age": 25, "role": "designer"},
}

@mcp.tool()
async def list_users() -> list:
    """列出所有用户"""
    return list(users.keys())

@mcp.resource("users://profile/{username}")
async def get_user_profile(username: str) -> str:
    """获取用户资料"""
    import json
    user = users.get(username)
    return json.dumps(user) if user else "用户不存在"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### 案例 3：带推送通知的 MCP 服务器

```python
# === notify_server.py ===
import os
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("notify")

@mcp.tool()
async def send_notification(title: str, message: str) -> str:
    """发送桌面通知

    Args:
        title: 通知标题
        message: 通知内容
    """
    # Windows: 使用 toast 通知
    if os.name == 'nt':
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=5)
    # macOS: 使用 osascript
    else:
        os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
    return "通知已发送"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### 案例 4：连接外部 MCP 服务器（Fetch + Search）

```python
# === external_mcp.py ===
from agents.mcp import MCPServerStdio
from agents import Agent, Runner

async def main():
    # 配置外部 MCP 服务器
    fetch_params = {"command": "uvx", "args": ["mcp-server-fetch"]}
    search_params = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": "your-api-key-here"}
    }

    # 启动多个服务器
    from contextlib import AsyncExitStack
    async with AsyncExitStack() as stack:
        servers = [
            await stack.enter_async_context(MCPServerStdio(p, client_session_timeout_seconds=60))
            for p in [fetch_params, search_params]
        ]

        agent = Agent(
            name="researcher",
            instructions="你是一个网络研究员，可以搜索网页和抓取网页内容",
            model="gpt-4o-mini",
            mcp_servers=servers
        )

        result = await Runner.run(agent, "搜索今天的科技新闻，抓取一篇详细阅读并总结")
        print(result.final_output)

import asyncio
asyncio.run(main())
```

### 案例 5：Agent-as-Tool 模式

```python
# === agent_tool.py ===
from agents import Agent, Runner

async def main():
    # 创建专家 Agent
    math_expert = Agent(
        name="数学专家",
        instructions="你是数学专家，擅长计算和数学推理",
        model="gpt-4o-mini"
    )

    # 将专家转换为工具
    math_tool = math_expert.as_tool(
        tool_name="ask_math_expert",
        tool_description="向数学专家提问，获取数学计算和推理结果"
    )

    # 创建主 Agent，使用专家工具
    assistant = Agent(
        name="助手",
        instructions="你是一个通用助手，遇到数学问题时使用数学专家工具",
        model="gpt-4o-mini",
        tools=[math_tool]
    )

    result = await Runner.run(assistant, "计算斐波那契数列的第20项是多少？")
    print(result.final_output)

import asyncio
asyncio.run(main())
```

---

## 九、常见问题

### Q1: Windows 上报 `UnsupportedOperation: fileno`

**原因**：MCP 使用 stdin/stdout 管道通信，Windows 的 Jupyter Notebook 不支持。

**解决**：使用 WSL（Windows Subsystem for Linux）运行 Jupyter Notebook。详见 [setup/SETUP-WSL.md](../setup/SETUP-WSL.md)。

### Q2: `await server.list_tools()` 报错缺少参数

**原因**：OpenAI Agents SDK 做了破坏性变更。

**解决**：替换为 `await server.session.list_tools()`，返回值改为 `fetch_tools.tools`。

### Q3: MCP 服务器需要 API Key 吗？

**不需要**。MCP 服务器是本地子进程，通过 stdin/stdout 通信。API Key 只在调用云端 LLM 模型时需要。

### Q4: 如何查找更多 MCP 服务器？

- https://mcp.so — MCP 服务器市场
- https://glama.ai/mcp — MCP 服务器目录
- https://smithery.ai/ — MCP 服务器注册中心

---

## 十、关键文件索引

| 文件 | 作用 | 关键知识点 |
|------|------|-----------|
| [mcp_params.py](mcp_params.py) | MCP 服务器参数配置 | uvx / uv run / npx 启动方式 |
| [accounts_server.py](accounts_server.py) | 账户管理 MCP 服务器 | `@mcp.tool()` / `@mcp.resource()` |
| [accounts_client.py](accounts_client.py) | 原生 MCP 客户端 | `stdio_client` / `ClientSession` |
| [market_server.py](market_server.py) | 市场数据 MCP 服务器 | 最简 MCP 服务器模板 |
| [push_server.py](push_server.py) | 推送通知 MCP 服务器 | Pydantic 参数模型 |
| [traders.py](traders.py) | 交易员 Agent | Agent-as-Tool / 多 MCP 服务器管理 |
| [trading_floor.py](trading_floor.py) | 调度器 | asyncio.gather 并发运行 |
| [app.py](app.py) | Gradio Web UI | 实时监控面板 |
