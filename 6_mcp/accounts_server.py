"""
accounts_server.py - 账户管理 MCP 服务器

本文件使用 FastMCP 框架创建一个 MCP 服务器，提供股票交易账户的管理功能。

核心概念：
  - @mcp.tool()    → 将函数注册为 MCP 工具（Tool），AI 代理可以调用
  - @mcp.resource() → 将函数注册为 MCP 资源（Resource），提供只读数据访问
  - mcp.run(transport='stdio') → 以标准输入/输出方式运行服务器（子进程通信）

运行方式：uv run accounts_server.py
"""

from mcp.server.fastmcp import FastMCP  # FastMCP 是 MCP 服务器的快速开发框架
from accounts import Account  # 导入账户业务逻辑类

# 创建 MCP 服务器实例，名称为 "accounts_server"
# 这个名称会出现在客户端的服务器列表中
mcp = FastMCP("accounts_server")


# ========== MCP 工具（Tools）==========
# 工具是 AI 代理可以主动调用的函数
# 每个工具都有 docstring，AI 会根据描述决定何时调用

@mcp.tool()
async def get_balance(name: str) -> float:
    """Get the cash balance of the given account name.

    Args:
        name: The name of the account holder
    """
    # 根据名称获取账户，返回现金余额
    return Account.get(name).balance


@mcp.tool()
async def get_holdings(name: str) -> dict[str, int]:
    """Get the holdings of the given account name.

    Args:
        name: The name of the account holder
    """
    # 返回持仓字典，格式如 {"AAPL": 10, "GOOGL": 5}
    return Account.get(name).holdings


@mcp.tool()
async def buy_shares(name: str, symbol: str, quantity: int, rationale: str) -> float:
    """Buy shares of a stock.

    Args:
        name: The name of the account holder
        symbol: The symbol of the stock
        quantity: The quantity of shares to buy
        rationale: The rationale for the purchase and fit with the account's strategy
    """
    # rationale 参数要求 AI 说明买入理由，便于记录和审计
    return Account.get(name).buy_shares(symbol, quantity, rationale)


@mcp.tool()
async def sell_shares(name: str, symbol: str, quantity: int, rationale: str) -> float:
    """Sell shares of a stock.

    Args:
        name: The name of the account holder
        symbol: The symbol of the stock
        quantity: The quantity of shares to sell
        rationale: The rationale for the sale and fit with the account's strategy
    """
    return Account.get(name).sell_shares(symbol, quantity, rationale)


@mcp.tool()
async def change_strategy(name: str, strategy: str) -> str:
    """At your discretion, if you choose to, call this to change your investment strategy for the future.

    Args:
        name: The name of the account holder
        strategy: The new strategy for the account
    """
    # AI 代理可以根据市场变化自主调整投资策略
    return Account.get(name).change_strategy(strategy)


# ========== MCP 资源（Resources）==========
# 资源是只读的数据端点，使用 URI 模板定义
# 客户端可以通过 URI 直接读取数据，无需调用工具

@mcp.resource("accounts://accounts_server/{name}")
async def read_account_resource(name: str) -> str:
    """读取指定账户的完整信息（余额、持仓、交易记录等）"""
    account = Account.get(name.lower())
    return account.report()  # 返回 JSON 格式的账户报告


@mcp.resource("accounts://strategy/{name}")
async def read_strategy_resource(name: str) -> str:
    """读取指定账户的投资策略"""
    account = Account.get(name.lower())
    return account.get_strategy()


# ========== 服务器入口 ==========
if __name__ == "__main__":
    # 以 stdio（标准输入/输出）传输方式运行服务器
    # MCP 客户端通过 stdin/stdout 管道与此子进程通信
    mcp.run(transport='stdio')
