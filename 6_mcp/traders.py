"""
traders.py - 交易员 Agent 模块

本文件定义了 Trader 类，它是整个交易系统的核心。
每个 Trader 是一个 AI 代理（Agent），拥有：
  - 自己的 MCP 服务器集合（账户、推送、市场数据）
  - 一个研究员子代理（Researcher）作为工具
  - 独立的投资策略和交易逻辑

架构：
  Trader Agent
    ├── MCP Server: accounts_server  （账户管理）
    ├── MCP Server: push_server      （推送通知）
    ├── MCP Server: market_server    （市场数据）
    └── Tool: Researcher Agent       （研究员子代理）
        ├── MCP Server: fetch         （网页抓取）
        ├── MCP Server: brave-search  （搜索引擎）
        └── MCP Server: memory        （知识图谱）
"""

from contextlib import AsyncExitStack
from accounts_client import read_accounts_resource, read_strategy_resource
from tracers import make_trace_id
from agents import Agent, Tool, Runner, OpenAIChatCompletionsModel, trace
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json
from agents.mcp import MCPServerStdio  # OpenAI Agents SDK 的 MCP 服务器封装
from templates import (
    researcher_instructions,
    trader_instructions,
    trade_message,
    rebalance_message,
    research_tool,
)
from mcp_params import trader_mcp_server_params, researcher_mcp_server_params

load_dotenv(override=True)

# ========== 多模型支持 ==========
# 支持 4 种不同的 LLM 提供商，每个交易员可以使用不同的模型
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
grok_api_key = os.getenv("GROK_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Agent 运行的最大轮次，防止无限循环
MAX_TURNS = 30

# 创建各提供商的异步客户端
openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key)
deepseek_client = AsyncOpenAI(base_url=DEEPSEEK_BASE_URL, api_key=deepseek_api_key)
grok_client = AsyncOpenAI(base_url=GROK_BASE_URL, api_key=grok_api_key)
gemini_client = AsyncOpenAI(base_url=GEMINI_BASE_URL, api_key=google_api_key)


def get_model(model_name: str):
    """根据模型名称选择对应的 LLM 提供商。

    路由规则：
      - 包含 "/" → OpenRouter（如 "anthropic/claude-3.5-sonnet"）
      - 包含 "deepseek" → DeepSeek
      - 包含 "grok" → Grok (xAI)
      - 包含 "gemini" → Google Gemini
      - 其他 → OpenAI 官方 API（直接返回模型名称字符串）

    Args:
        model_name: 模型标识符

    Returns:
        OpenAIChatCompletionsModel 或 str: 模型实例
    """
    if "/" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=openrouter_client)
    elif "deepseek" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=deepseek_client)
    elif "grok" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=grok_client)
    elif "gemini" in model_name:
        return OpenAIChatCompletionsModel(model=model_name, openai_client=gemini_client)
    else:
        # OpenAI 模型直接用字符串，Agents SDK 内部处理
        return model_name


async def get_researcher(mcp_servers, model_name) -> Agent:
    """创建研究员 Agent。

    研究员是一个独立的 AI 代理，负责：
      - 搜索财经新闻
      - 分析市场机会
      - 使用知识图谱存储研究发现

    Args:
        mcp_servers: 研究员的 MCP 服务器列表（fetch、brave-search、memory）
        model_name: 研究员使用的 LLM 模型

    Returns:
        Agent: 配置好的研究员代理实例
    """
    researcher = Agent(
        name="Researcher",
        instructions=researcher_instructions(),  # 研究员的系统提示词
        model=get_model(model_name),
        mcp_servers=mcp_servers,  # 绑定 MCP 服务器
    )
    return researcher


async def get_researcher_tool(mcp_servers, model_name) -> Tool:
    """将研究员 Agent 包装为一个工具（Tool）。

    这是 Agent-as-Tool 模式：交易员可以把研究员当作工具来调用。
    当交易员需要研究信息时，它会"调用"研究员工具，
    研究员独立完成研究后返回结果给交易员。

    Args:
        mcp_servers: 研究员的 MCP 服务器列表
        model_name: 模型名称

    Returns:
        Tool: 可被交易员 Agent 使用的工具对象
    """
    researcher = await get_researcher(mcp_servers, model_name)
    # as_tool() 将 Agent 转换为 Tool，其他 Agent 可以调用它
    return researcher.as_tool(tool_name="Researcher", tool_description=research_tool())


class Trader:
    """交易员类 - 封装一个完整的 AI 交易代理。

    属性：
        name: 交易员名称（如 "Warren", "George"）
        lastname: 交易风格后缀（如 "Patience", "Bold"）
        model_name: 使用的 LLM 模型
        agent: 底层的 Agent 实例
        do_trade: 交替标志 - True 时执行交易，False 时执行再平衡
    """

    def __init__(self, name: str, lastname="Trader", model_name="gpt-4o-mini"):
        self.name = name
        self.lastname = lastname
        self.agent = None
        self.model_name = model_name
        self.do_trade = True  # 交替执行交易/再平衡

    async def create_agent(self, trader_mcp_servers, researcher_mcp_servers) -> Agent:
        """创建交易员 Agent。

        交易员 Agent 的组成：
          - 系统提示词：定义交易员的角色和行为
          - 工具：研究员子代理（Agent-as-Tool）
          - MCP 服务器：账户管理、推送通知、市场数据

        Args:
            trader_mcp_servers: 交易员的 MCP 服务器列表
            researcher_mcp_servers: 研究员的 MCP 服务器列表

        Returns:
            Agent: 配置好的交易员代理
        """
        # 先将研究员包装为工具
        tool = await get_researcher_tool(researcher_mcp_servers, self.model_name)
        self.agent = Agent(
            name=self.name,
            instructions=trader_instructions(self.name),  # 个性化系统提示词
            model=get_model(self.model_name),
            tools=[tool],  # 研究员作为工具
            mcp_servers=trader_mcp_servers,  # 绑定 MCP 服务器
        )
        return self.agent

    async def get_account_report(self) -> str:
        """通过 MCP 资源协议获取账户报告。

        直接调用 accounts_client 的 read_accounts_resource，
        绕过 Agent，用于获取当前账户状态以构建提示词。

        Returns:
            str: JSON 格式的账户信息（移除了时间序列数据以减少 token）
        """
        account = await read_accounts_resource(self.name)
        account_json = json.loads(account)
        account_json.pop("portfolio_value_time_series", None)  # 移除冗长的时间序列
        return json.dumps(account_json)

    async def run_agent(self, trader_mcp_servers, researcher_mcp_servers):
        """运行交易员 Agent 执行一次交易或再平衡。

        流程：
          1. 创建 Agent（包含研究员工具和 MCP 服务器）
          2. 获取当前账户状态和投资策略
          3. 根据 do_trade 标志选择交易或再平衡消息
          4. 运行 Agent（最多 MAX_TURNS 轮）
        """
        self.agent = await self.create_agent(trader_mcp_servers, researcher_mcp_servers)
        account = await self.get_account_report()
        strategy = await read_strategy_resource(self.name)
        # 交替执行：奇数轮交易，偶数轮再平衡
        message = (
            trade_message(self.name, strategy, account)
            if self.do_trade
            else rebalance_message(self.name, strategy, account)
        )
        await Runner.run(self.agent, message, max_turns=MAX_TURNS)

    async def run_with_mcp_servers(self):
        """使用 AsyncExitStack 管理多个 MCP 服务器的生命周期。

        AsyncExitStack 确保所有 MCP 服务器子进程在退出时被正确关闭。
        两层嵌套：
          - 外层：交易员的 MCP 服务器（账户、推送、市场）
          - 内层：研究员的 MCP 服务器（fetch、brave-search、memory）
        """
        async with AsyncExitStack() as stack:
            # 启动交易员的 MCP 服务器
            trader_mcp_servers = [
                await stack.enter_async_context(
                    MCPServerStdio(params, client_session_timeout_seconds=120)
                )
                for params in trader_mcp_server_params
            ]
            async with AsyncExitStack() as stack:
                # 启动研究员的 MCP 服务器
                researcher_mcp_servers = [
                    await stack.enter_async_context(
                        MCPServerStdio(params, client_session_timeout_seconds=120)
                    )
                    for params in researcher_mcp_server_params(self.name)
                ]
                await self.run_agent(trader_mcp_servers, researcher_mcp_servers)

    async def run_with_trace(self):
        """带追踪的运行方式。

        使用 OpenAI 的 trace 功能记录 Agent 的完整执行过程，
        可在 https://platform.openai.com/traces 查看。
        """
        trace_name = f"{self.name}-trading" if self.do_trade else f"{self.name}-rebalancing"
        trace_id = make_trace_id(f"{self.name.lower()}")
        with trace(trace_name, trace_id=trace_id):
            await self.run_with_mcp_servers()

    async def run(self):
        """运行交易员的主入口方法。

        执行一次交易或再平衡，然后切换模式。
        异常会被捕获并打印，避免一个交易员的错误影响其他交易员。
        """
        try:
            await self.run_with_trace()
        except Exception as e:
            print(f"Error running trader {self.name}: {e}")
        # 切换模式：这次交易了，下次就再平衡，反之亦然
        self.do_trade = not self.do_trade
