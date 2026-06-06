"""
MiMo 搜索工具 — 修复版

原代码问题：
  1. OpenAIChatCompletionClient (AutoGen) 传给 initialize_agent (LangChain) — 接口不兼容
  2. agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION 参数名错误，且覆盖变量
  3. langchain_serper 未定义
  4. 混用 LangChain Agent + AutoGen Client

修复方案：按 notebook cell-11 的正确模式，统一用 AutoGen 的 AssistantAgent
"""

import os
import asyncio
import requests
from langchain.tools import BaseTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.tools.langchain import LangChainToolAdapter
from dotenv import load_dotenv

load_dotenv(override=True)


# ========================================================================
# 1. MiMo 搜索工具（继承 LangChain BaseTool）
# ========================================================================

class MiMoSearchTool(BaseTool):
    """封装小米 MiMo 大模型的内置搜索能力为 LangChain 工具

    Pydantic v2 要求所有字段必须有类型注解。
    继承 BaseTool 时，覆盖字段要写 name: str = "xxx"，不能直接 name = "xxx"
    """
    name: str = "mimo_search"
    description: str = "使用小米 MiMo 大模型的内置搜索工具进行实时网页搜索"

    def _run(self, query: str) -> str:
        url = "https://api.xiaomimimo.com/v1/chat/completions"
        headers = {
            "api-key": os.getenv("MIMO_API_KEY", "sk-ct6ct1y17ry3m9xh2rce3bbx68kbsqs19y326ym89hxw2k64"),
            "Content-Type": "application/json",
        }
        payload = {
            "model": "mimo-v2.5-pro",
            "messages": [{"role": "user", "content": query}],
            "tools": [{
                "type": "web_search",
                "max_keyword": 3,
                "force_search": True,
                "limit": 1,
                "user_location": {
                    "type": "approximate",
                    "country": "China",
                    "region": "Hubei",
                    "city": "Wuhan",
                },
            }],
            "max_completion_tokens": 512,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def _arun(self, query: str) -> str:
        return self._run(query)


# ========================================================================
# 2. 包装为 AutoGen 工具（LangChain BaseTool → AutoGen Tool）
# ========================================================================

# 创建 LangChain 工具实例
mimo_search_tool = MiMoSearchTool()

# 用 LangChainToolAdapter 桥接（和 notebook cell-11 一样的模式）
autogen_mimo_search = LangChainToolAdapter(mimo_search_tool)


# ========================================================================
# 3. 创建 AutoGen Agent（不是 LangChain Agent！）
# ========================================================================

model_client = OpenAIChatCompletionClient(
    model="mimo-v2.5-pro",
    base_url="https://api.xiaomimimo.com/v1",
    api_key=os.getenv("MIMO_API_KEY", "sk-ct6ct1y17ry3m9xh2rce3bbx68kbsqs19y326ym89hxw2k64"),
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
        "structured_output": False,
    },
)

# ✅ 正确：用 AutoGen 的 AssistantAgent，而不是 LangChain 的 initialize_agent
agent = AssistantAgent(
    name="mimo_searcher",
    model_client=model_client,
    tools=[autogen_mimo_search],
    system_message="你是一个搜索助手，使用 MiMo 搜索工具来查找信息。用中文回复。",
    reflect_on_tool_use=True,  # 工具调用后让 LLM 整合结果
)


# ========================================================================
# 4. 运行
# ========================================================================

async def main():
    prompt = "搜索一下雷军的最新动态"
    message = TextMessage(content=prompt, source="user")

    result = await agent.on_messages([message], cancellation_token=CancellationToken())

    # 打印中间过程（工具调用等）
    for msg in result.inner_messages:
        print(f"[{msg.source}] {msg.content}\n")

    # 打印最终回复
    print(f"[最终回复] {result.chat_message.content}")


if __name__ == "__main__":
    asyncio.run(main())
