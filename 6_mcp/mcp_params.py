"""
mcp_params.py - MCP 服务器参数配置模块

本文件集中配置所有 MCP 服务器的启动参数。
每个参数字典会被传递给 MCPServerStdio，用于以子进程方式启动对应的 MCP 服务器。

MCP 服务器启动方式：
  - "uvx"     → Python 包的临时运行工具（无需预先安装）
  - "uv run"  → 使用 uv 运行本地 Python 脚本
  - "npx"     → Node.js 包运行工具（用于 JS 生态的 MCP 服务器）
"""

import os
from dotenv import load_dotenv
from market import is_paid_polygon, is_realtime_polygon

load_dotenv(override=True)

# ========== API 密钥配置 ==========
# Brave Search API 密钥，用于网页搜索 MCP 服务器
brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
# Polygon API 密钥，用于股票市场数据 MCP 服务器
polygon_api_key = os.getenv("POLYGON_API_KEY")


# ========== 市场数据 MCP 服务器配置 ==========
# 根据 Polygon API 的订阅级别选择不同的启动方式

if is_paid_polygon or is_realtime_polygon:
    # 付费/实时订阅：使用官方 Polygon MCP 服务器（从 GitHub 安装）
    # uvx 会自动从 GitHub 拉取并运行 mcp_polygon 包
    market_mcp = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/polygon-io/mcp_polygon@v0.1.0", "mcp_polygon"],
        "env": {"POLYGON_API_KEY": polygon_api_key},  # 将 API 密钥注入子进程环境变量
    }
else:
    # 免费订阅：使用本地自定义的 market_server.py
    market_mcp = {"command": "uv", "args": ["run", "market_server.py"]}


# ========== 交易员（Trader）的 MCP 服务器列表 ==========
# 交易员需要 3 个 MCP 服务器：
#   1. accounts_server  → 账户管理（查询余额、买卖股票）
#   2. push_server      → 推送通知（交易完成后发送通知）
#   3. market_mcp       → 市场数据（查询股价）
trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "accounts_server.py"]},
    {"command": "uv", "args": ["run", "push_server.py"]},
    market_mcp,
]


# ========== 研究员（Researcher）的 MCP 服务器列表 ==========
# 研究员需要 3 个 MCP 服务器：
#   1. mcp-server-fetch        → 网页抓取（读取网页内容）
#   2. server-brave-search     → Brave 搜索引擎（搜索新闻和信息）
#   3. mcp-memory-libsql       → 知识图谱/持久记忆（存储和检索研究发现）
def researcher_mcp_server_params(name: str):
    """为指定研究员生成 MCP 服务器参数列表。

    Args:
        name: 研究员名称，用于创建独立的记忆数据库文件

    Returns:
        list: 包含 3 个 MCP 服务器参数字典的列表
    """
    return [
        # 网页抓取服务器 - 使用 uvx 临时运行
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        # Brave 搜索服务器 - 使用 npx 运行 Node.js 包
        {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": brave_env,  # 注入 Brave API 密钥
        },
        # 知识图谱记忆服务器 - 每个研究员有独立的 SQLite 数据库
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},  # 按名称隔离记忆
        },
    ]
