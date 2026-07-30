"""
accounts_client.py - 账户 MCP 服务器的客户端

本文件演示如何用原生 MCP 客户端 SDK 连接并调用 accounts_server.py。
这是最底层的 MCP 客户端用法，不依赖 OpenAI Agents SDK。

核心概念：
  - StdioServerParameters → 配置子进程启动参数
  - stdio_client()        → 启动子进程并建立 stdin/stdout 通信流
  - ClientSession         → MCP 客户端会话，提供 list_tools / call_tool / read_resource 等方法
"""

import mcp  # MCP 协议核心库
from mcp.client.stdio import stdio_client  # stdio 传输客户端
from mcp import StdioServerParameters  # 子进程启动参数
from agents import FunctionTool  # OpenAI Agents SDK 的工具封装
import json


# ========== 服务器启动参数 ==========
# 指定以 "uv run accounts_server.py" 命令启动 MCP 服务器子进程
params = StdioServerParameters(command="uv", args=["run", "accounts_server.py"], env=None)


async def list_accounts_tools():
    """列出 accounts_server 提供的所有工具。

    流程：
      1. stdio_client(params) 启动子进程，返回 (read_stream, write_stream)
      2. ClientSession 建立 MCP 会话
      3. session.initialize() 完成握手
      4. session.list_tools() 获取工具列表

    Returns:
        list: 工具对象列表，每个包含 name、description、inputSchema 等
    """
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def call_accounts_tool(tool_name, tool_args):
    """调用 accounts_server 上的指定工具。

    Args:
        tool_name: 工具名称，如 "buy_shares"
        tool_args: 工具参数字典，如 {"name": "Warren", "symbol": "AAPL", "quantity": 10, "rationale": "..."}

    Returns:
        ToolResult: 工具执行结果
    """
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result


async def read_accounts_resource(name):
    """通过 MCP 资源协议读取账户信息。

    与工具调用不同，资源是只读的 URI 端点。
    URI 格式：accounts://accounts_server/{name}

    Args:
        name: 账户持有人名称

    Returns:
        str: JSON 格式的账户报告
    """
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://accounts_server/{name}")
            return result.contents[0].text


async def read_strategy_resource(name):
    """通过 MCP 资源协议读取投资策略。

    URI 格式：accounts://strategy/{name}

    Args:
        name: 账户持有人名称

    Returns:
        str: 策略文本
    """
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.read_resource(f"accounts://strategy/{name}")
            return result.contents[0].text


async def get_accounts_tools_openai():
    """将 MCP 工具转换为 OpenAI Agents SDK 的 FunctionTool 格式。

    这是 MCP 与 OpenAI Agents SDK 的桥接层：
      1. 从 MCP 服务器获取工具列表
      2. 将每个 MCP 工具的 inputSchema 转换为 OpenAI 的 params_json_schema
      3. 创建 FunctionTool，其 on_invoke_tool 回调会调用 MCP 服务器

    Returns:
        list[FunctionTool]: OpenAI Agents SDK 可直接使用的工具列表
    """
    openai_tools = []
    for tool in await list_accounts_tools():
        # 构建 JSON Schema，additionalProperties=False 确保严格验证
        schema = {**tool.inputSchema, "additionalProperties": False}
        # 创建 FunctionTool：名称、描述、参数 schema、以及调用回调
        openai_tool = FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=schema,
            # on_invoke_tool: 当 AI 决定调用此工具时执行的回调函数
            # toolname=tool.name 是闭包捕获，确保每个工具绑定正确的名称
            on_invoke_tool=lambda ctx, args, toolname=tool.name: call_accounts_tool(toolname, json.loads(args))
        )
        openai_tools.append(openai_tool)
    return openai_tools
