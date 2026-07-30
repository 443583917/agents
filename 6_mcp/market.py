"""
market.py - 市场数据模块

本文件提供股票价格查询功能，支持两种数据源：
  1. Polygon API（真实市场数据）
     - 免费计划：仅提供前一日收盘价（EOD）
     - 付费计划：提供实时/延迟 15 分钟的报价
  2. 随机数（备用方案，当 API 不可用时）

环境变量配置：
  - POLYGON_API_KEY: Polygon.io 的 API 密钥
  - POLYGON_PLAN: 订阅级别 ("paid" / "realtime" / 其他)
"""

from polygon import RESTClient
from dotenv import load_dotenv
import os
from datetime import datetime
import random
from database import write_market, read_market
from functools import lru_cache
from datetime import timezone

load_dotenv(override=True)

# ========== Polygon API 配置 ==========
polygon_api_key = os.getenv("POLYGON_API_KEY")
polygon_plan = os.getenv("POLYGON_PLAN")

# 判断订阅级别
is_paid_polygon = polygon_plan == "paid"       # 付费计划（延迟 15 分钟）
is_realtime_polygon = polygon_plan == "realtime"  # 实时计划


def is_market_open() -> bool:
    """检查美股市场是否开盘。

    Returns:
        bool: True 表示开盘，False 表示休市
    """
    client = RESTClient(polygon_api_key)
    market_status = client.get_market_status()
    return market_status.market == "open"


def get_all_share_prices_polygon_eod() -> dict[str, float]:
    """获取所有股票的前一日收盘价（End of Day）。

    使用 Polygon 的 Grouped Daily Aggs API，
    一次请求获取所有股票在指定日期的收盘价。

    Returns:
        dict: {股票代码: 收盘价} 的字典
    """
    client = RESTClient(polygon_api_key)
    # 先获取 SPY 的前一个交易日数据来确定日期
    probe = client.get_previous_close_agg("SPY")[0]
    last_close = datetime.fromtimestamp(probe.timestamp / 1000, tz=timezone.utc).date()
    # 获取该日期的所有股票数据
    results = client.get_grouped_daily_aggs(last_close, adjusted=True, include_otc=False)
    return {result.ticker: result.close for result in results}


@lru_cache(maxsize=2)
def get_market_for_prior_date(today):
    """获取指定日期的市场数据（带缓存）。

    优先从本地数据库读取缓存，缓存未命中时调用 Polygon API。
    lru_cache 装饰器在内存中也缓存最近 2 次查询结果。

    Args:
        today: 日期字符串（如 "2025-01-15"）

    Returns:
        dict: {股票代码: 价格} 的字典
    """
    market_data = read_market(today)
    if not market_data:
        market_data = get_all_share_prices_polygon_eod()
        write_market(today, market_data)
    return market_data


def get_share_price_polygon_eod(symbol) -> float:
    """获取单只股票的前一日收盘价（免费计划）。

    Args:
        symbol: 股票代码（如 "AAPL"）

    Returns:
        float: 收盘价，未找到时返回 0.0
    """
    today = datetime.now().date().strftime("%Y-%m-%d")
    market_data = get_market_for_prior_date(today)
    return market_data.get(symbol, 0.0)


def get_share_price_polygon_min(symbol) -> float:
    """获取单只股票的实时/分钟级价格（付费计划）。

    Args:
        symbol: 股票代码

    Returns:
        float: 最新价格
    """
    client = RESTClient(polygon_api_key)
    result = client.get_snapshot_ticker("stocks", symbol)
    # 优先返回分钟级数据，否则返回前一日收盘价
    return result.min.close or result.prev_day.close


def get_share_price_polygon(symbol) -> float:
    """根据订阅级别选择价格查询方式。

    Args:
        symbol: 股票代码

    Returns:
        float: 股票价格
    """
    if is_paid_polygon:
        return get_share_price_polygon_min(symbol)
    else:
        return get_share_price_polygon_eod(symbol)


def get_share_price(symbol) -> float:
    """获取股票价格的统一入口函数。

    优先使用 Polygon API，失败时返回随机价格作为备用。

    Args:
        symbol: 股票代码

    Returns:
        float: 股票价格
    """
    if polygon_api_key:
        try:
            return get_share_price_polygon(symbol)
        except Exception as e:
            print(f"Was not able to use the polygon API due to {e}; using a random number")
    # 备用方案：返回 1-100 的随机整数
    return float(random.randint(1, 100))
