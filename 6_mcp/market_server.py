"""
market_server.py - 市场数据 MCP 服务器

本文件创建一个轻量级 MCP 服务器，提供股票价格查询功能。
当 Polygon API 未配置或使用免费计划时，使用此本地服务器。

运行方式：uv run market_server.py
"""

from mcp.server.fastmcp import FastMCP
from market import get_share_price  # 导入股价查询函数

# 创建 MCP 服务器实例
mcp = FastMCP("market_server")


@mcp.tool()
async def lookup_share_price(symbol: str) -> float:
    """This tool provides the current price of the given stock symbol.

    Args:
        symbol: the symbol of the stock (e.g., "AAPL", "GOOGL", "TSLA")
    """
    # 调用 market 模块的 get_share_price 函数
    # 如果配置了 Polygon API，使用真实数据；否则返回随机价格
    return get_share_price(symbol)


if __name__ == "__main__":
    mcp.run(transport='stdio')
