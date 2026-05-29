# Week 6：MCP — Agent 的通用接口协议

这是 6 周 Agent 开发课程的第六周——收官模块。前五周学了各种 Agent 框架，本周学 MCP（Model Context Protocol）：**把 Tool 标准化成可插拔的独立服务**。像微服务一样，每个 MCP Server 是一个独立进程，任何 Agent 框架都能调用。

## 核心理念

MCP 是一个基于 JSON-RPC 的开放协议，定义了 Agent（Host/Client）和工具提供者（Server）之间的标准通信方式。

```
┌──────────────┐  tools/list     ┌──────────────┐
│  Host/Client │◄───────────────►│  MCP Server  │
│  (你的 Agent) │  tools/call     │  (你用任何   │
│              │  resources/read │   语言写的)   │
└──────────────┘                 └──────────────┘
       ▲                                ▲
       │ JSON-RPC over stdio/SSE        │ FastMCP / MCP SDK
```

**一句话：你写 MCP Server 定义工具 → 任何 MCP Client 都能发现和调用 → 工具实现和 Agent 框架彻底解耦。**

## 5 天学习路线：Consume → Build → Categorize → Compose → Orchestrate

| Lab | 主题 | 核心概念 | 难度 |
|-----|------|---------|------|
| `1_lab1.ipynb` | **Consume** 消费 | MCPServerStdio、预构建 MCP Server、list_tools | ⭐ |
| `2_lab2.ipynb` | **Build** 构建 | FastMCP、@mcp.tool()、@mcp.resource()、raw ClientSession | ⭐⭐ |
| `3_lab3.ipynb` | **Categorize** 分类 | 三种 Server 类型、Brave Search、Polygon.io、记忆 MCP | ⭐⭐⭐ |
| `4_lab4.ipynb` | **Compose** 组合 | Agent-as-Tool、5 MCP Server 组合、AsyncExitStack | ⭐⭐⭐⭐ |
| `5_lab5.ipynb` | **Orchestrate** 编排 | 4 Trader 并行、Gradio 仪表盘、TracingProcessor、调度循环 | ⭐⭐⭐⭐⭐ |

## 项目结构

```
6_mcp/
├── 1_lab1.ipynb              # Day 1：消费 3 个预构建 MCP Server
├── 2_lab2.ipynb              # Day 2：构建自己的 MCP Server 和 Client
├── 3_lab3.ipynb              # Day 3：三种 MCP Server 类型 + 金融数据
├── 4_lab4.ipynb              # Day 4：自主交易 Agent（Researcher-as-Tool）
├── 5_lab5.ipynb              # Day 5：四交易员并行 + Gradio 仪表盘
│
├── accounts.py               # 账户领域模型（Pydantic + SQLite）
├── accounts_server.py        # FastMCP Server：5 tools + 2 resources
├── accounts_client.py        # 原始 MCP Client（list_tools/call_tool/read_resource）
├── market.py                 # Polygon.io 股价查询 + SQLite 缓存
├── market_server.py          # FastMCP Server：lookup_share_price
├── push_server.py            # FastMCP Server：Pushover 推送通知
├── mcp_params.py             # MCP Server 启动参数集中配置
├── templates.py              # Agent System Prompt 模板
├── tracers.py                # 自定义 TracingProcessor（追踪 → SQLite）
├── traders.py                # Trader 类：Agent + MCP Server 装配
├── trading_floor.py          # 入口：调度循环（while True: gather → sleep）
├── app.py                    # Gradio 仪表盘（实时投资组合可视化）
├── database.py               # SQLite 持久化（accounts / logs / market）
├── reset.py                  # 重置四个交易员账户和策略
├── util.py                   # CSS/JS/Color 工具
│
├── memory/                   # 知识图谱记忆数据库
├── sandbox/                  # 文件操作沙箱目录
└── community_contributions/  # 55+ 学员项目
```

## 6 大架构模式

### 1. FastMCP Server（构建工具提供者）
```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("server_name")

@mcp.tool()
async def my_tool(arg: str) -> str: ...

@mcp.resource("scheme://path/{param}")
async def my_resource(param: str) -> str: ...

mcp.run(transport='stdio')
```

### 2. Agent 消费 MCP Server
```python
async with MCPServerStdio(params={"command": "uv", "args": ["run", "server.py"]}) as server:
    agent = Agent(..., mcp_servers=[server])
    result = await Runner.run(agent, "task")
```

### 3. Agent-as-Tool（Agent 嵌套）
```python
researcher = Agent(..., mcp_servers=[fetch, brave])
researcher_tool = researcher.as_tool(tool_name="Researcher", ...)
trader = Agent(..., tools=[researcher_tool])
```

### 4. AsyncExitStack（多 Server 管理）
```python
async with AsyncExitStack() as stack:
    servers = [await stack.enter_async_context(MCPServerStdio(p)) for p in params_list]
```

### 5. 原始 MCP Client（最大控制）
```python
async with stdio_client(StdioServerParameters(...)) as streams:
    async with ClientSession(*streams) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("tool_name", {...})
```

### 6. 自定义 TracingProcessor（可观测性）
```python
class LogTracer(TracingProcessor):
    def on_trace_start(self, trace): ...
    def on_span_start(self, span): ...

add_trace_processor(LogTracer())
```

## MCP 核心概念速查

| 概念 | 代码 | 用途 |
|------|------|------|
| FastMCP Server | `FastMCP("name")` + `mcp.run(transport='stdio')` | 创建工具提供者 |
| Tool 定义 | `@mcp.tool()` | 暴露函数为 MCP 工具 |
| Resource 定义 | `@mcp.resource("uri://{param}")` | 暴露数据为 REST 风格资源 |
| SDK 集成 | `MCPServerStdio(params=...)` | OpenAI SDK 连接 MCP |
| 列出工具 | `await server.list_tools()` | 发现可用工具 |
| 调用工具 | `await session.call_tool(name, args)` | 执行工具 |
| 读取资源 | `await session.read_resource(uri)` | 读取数据资源 |
| 原始 Client | `stdio_client` + `ClientSession` | 不依赖 SDK 的 MCP 访问 |
| 转换为 FunctionTool | `FunctionTool(name, schema, on_invoke_tool)` | 把 MCP 工具转成 SDK 工具 |
| STDIO 传输 | `StdioServerParameters(command, args)` | 子进程通信 |
| SSE 传输 | `MCPServerSse(params={"url": "..."})` | HTTP 远程通信 |

## MCP Server 的三种类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **Type 1：本地独立** | Server 不访问外部 API，自包含 | `mcp-memory-libsql`（SQLite 知识图谱） |
| **Type 2：本地→远程 API** | Server 本地运行，代理到外部 API | Brave Search、Polygon.io |
| **Type 3：远程托管** | Server 部署在远程，通过 SSE 连接 | CloudFlare 托管、企业内部 API |

## Capstone：自主交易大厅

这是整个 6 周课程的终极项目——4 个 AI 交易员各有独立策略，并行运行，通过 MCP 连接账户、市场、搜索、记忆服务：

```
trading_floor.py (调度循环)
    │
    ├── Trader "Warren" (价值投资)     ──┐
    ├── Trader "George" (宏观/逆向)    ──┤
    ├── Trader "Ray" (系统化/分散化)   ──┤ asyncio.gather 并行
    └── Trader "Cathie" (颠覆性创新)   ──┘
            │
    每个 Trader 连接 5 个 MCP Server:
    ├── accounts_server (交易/持仓/余额)
    ├── market_server (股价查询)
    ├── push_server (推送通知)
    ├── mcp-server-fetch (网页获取)
    └── @modelcontextprotocol/server-brave-search (搜索)
    +
    Researcher Agent as Tool (搜索+分析)
    +
    mcp-memory-libsql (共享知识图谱)
            │
            ▼
    Gradio 仪表盘 (app.py)
    ├── 实时投资组合价值图表
    ├── 持仓/交易记录
    └── Agent 思考日志流
```

## 用 DeepSeek 替代 OpenAI

在 `traders.py` 中通过环境变量配置：

```bash
# .env
USE_MANY_MODELS=True
DEEPSEEK_API_KEY=sk-xxx
```

## 什么时候用 MCP

- 构建可被多个 Agent 框架复用的工具服务
- 工具逻辑复杂、需要独立部署和扩展
- 需要用不同编程语言写工具（MCP Server 可以用任何语言）
- 需要工具和服务的热更新（不重启 Agent）
- 企业级工具治理和权限控制

## 参考资源

- [MCP 官方规范](https://modelcontextprotocol.io/)
- [MCP Server 市场](https://github.com/modelcontextprotocol/servers)
- [FastMCP 文档](https://github.com/jlowin/fastmcp)
- [Smithery](https://smithery.ai/) / [Glama](https://glama.ai/mcp) / [mcp.so](https://mcp.so)
- 详细学习指南：[学习指南.md](学习指南.md)
- 中文导航：[../docs/中文学习导航.md](../docs/中文学习导航.md)
