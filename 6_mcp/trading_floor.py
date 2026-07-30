"""
trading_floor.py - 交易大厅调度器

本文件是交易系统的主调度程序。
它创建 4 个交易员（Warren, George, Ray, Cathie），每个使用不同的 LLM 模型，
然后按固定时间间隔循环运行所有交易员。

架构概览：
  trading_floor.py（调度器）
    ├── Trader("Warren")   → GPT 4.1 Mini   → 价值投资策略
    ├── Trader("George")   → DeepSeek V3     → 宏观交易策略
    ├── Trader("Ray")      → Gemini 2.5 Flash → 系统化策略
    └── Trader("Cathie")   → Grok 3 Mini     → 加密 ETF 策略

每个 Trader 内部都有自己的 MCP 服务器和研究员子代理。

运行方式：python trading_floor.py
"""

from traders import Trader
from typing import List
import asyncio
from tracers import LogTracer
from agents import add_trace_processor
from market import is_market_open
from dotenv import load_dotenv
import os

load_dotenv(override=True)

# ========== 调度配置 ==========
# 每 N 分钟运行一次交易循环
RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "60"))
# 是否在股市关闭时也运行（用于测试）
RUN_EVEN_WHEN_MARKET_IS_CLOSED = (
    os.getenv("RUN_EVEN_WHEN_MARKET_IS_CLOSED", "false").strip().lower() == "true"
)
# 是否使用多种不同的 LLM 模型（false 时全部使用 gpt-4o-mini）
USE_MANY_MODELS = os.getenv("USE_MANY_MODELS", "false").strip().lower() == "true"


# ========== 交易员配置 ==========
# 4 个交易员，分别致敬不同的投资大师
names = ["Warren", "George", "Ray", "Cathie"]
lastnames = ["Patience", "Bold", "Systematic", "Crypto"]

if USE_MANY_MODELS:
    # 多模型模式：每个交易员使用不同的 LLM
    model_names = [
        "gpt-4.1-mini",                        # Warren → OpenAI
        "deepseek-chat",                        # George → DeepSeek
        "gemini-2.5-flash-preview-04-17",       # Ray → Google Gemini
        "grok-3-mini-beta",                     # Cathie → xAI Grok
    ]
    short_model_names = ["GPT 4.1 Mini", "DeepSeek V3", "Gemini 2.5 Flash", "Grok 3 Mini"]
else:
    # 单模型模式：全部使用 GPT 4o mini（节省成本）
    model_names = ["gpt-4o-mini"] * 4
    short_model_names = ["GPT 4o mini"] * 4


def create_traders() -> List[Trader]:
    """创建所有交易员实例。

    Returns:
        List[Trader]: 4 个交易员对象
    """
    traders = []
    for name, lastname, model_name in zip(names, lastnames, model_names):
        traders.append(Trader(name, lastname, model_name))
    return traders


async def run_every_n_minutes():
    """主循环：每隔 N 分钟运行一次所有交易员。

    流程：
      1. 注册日志追踪器（将 Agent 执行日志写入数据库）
      2. 创建 4 个交易员
      3. 无限循环：
         - 检查股市是否开盘（可配置跳过此检查）
         - 并发运行所有交易员（asyncio.gather）
         - 等待 N 分钟后重复
    """
    # 注册自定义追踪处理器，将 trace/span 事件写入 SQLite 日志
    add_trace_processor(LogTracer())
    traders = create_traders()
    while True:
        if RUN_EVEN_WHEN_MARKET_IS_CLOSED or is_market_open():
            # 并发运行所有交易员，充分利用异步 IO
            await asyncio.gather(*[trader.run() for trader in traders])
        else:
            print("Market is closed, skipping run")
        # 等待指定时间后进入下一轮
        await asyncio.sleep(RUN_EVERY_N_MINUTES * 60)


if __name__ == "__main__":
    print(f"Starting scheduler to run every {RUN_EVERY_N_MINUTES} minutes")
    asyncio.run(run_every_n_minutes())
