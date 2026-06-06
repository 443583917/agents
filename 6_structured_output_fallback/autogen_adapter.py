"""
AutoGen 结构化输出适配器

AutoGen 的 output_content_type 依赖模型的 function calling 能力，
对于不支持的模型（MiMo、本地 Llama 等），本适配器提供 fallback。

提供两种使用方式：
1. create_structured_agent() — 创建带容错的 AssistantAgent
2. StructuredAgentWrapper — 包装现有 agent，拦截输出并解析

用法示例（替换 AutoGen Lab2 的写法）：

    from structured_output_fallback.autogen_adapter import create_structured_agent

    # 原来的写法（不兼容 MiMo 等模型）
    # describer = AssistantAgent(
    #     name="description_agent",
    #     model_client=model_client,
    #     output_content_type=ImageDescription,
    # )

    # 新写法（自动容错）
    describer = create_structured_agent(
        name="description_agent",
        model_client=model_client,
        schema=ImageDescription,
        system_message="You are good at describing images in detail",
    )
"""

import json
import logging
from typing import Type, TypeVar, Optional, Any

from pydantic import BaseModel

from .model_registry import get_model_config, ModelCapability
from .fallback_parser import StructuredOutputParser, _build_system_prompt

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


# ========================================================================
# 核心：创建带容错的 AssistantAgent
# ========================================================================

def create_structured_agent(
    name: str,
    model_client: Any,
    schema: Type[T],
    system_message: str = "",
    max_retries: int = 3,
    **agent_kwargs,
) -> Any:
    """创建带容错的 AutoGen AssistantAgent

    自动检测模型能力：
    - 支持原生 structured output → 使用 output_content_type
    - 不支持 → 注入 JSON 指令到 system_message，运行时解析输出

    参数：
        name: Agent 名称
        model_client: AutoGen ChatCompletionClient 实例
        schema: Pydantic BaseModel 子类（期望的输出格式）
        system_message: 系统提示词
        max_retries: prompt fallback 最大重试次数
        **agent_kwargs: 透传给 AssistantAgent 的其他参数

    返回：
        AssistantAgent 实例（原生模式）或 StructuredAgentWrapper（fallback 模式）
    """
    from autogen_agentchat.agents import AssistantAgent

    # 检测模型能力
    model_name = getattr(model_client, "model", None)
    if isinstance(model_name, dict):
        model_name = model_name.get("model", "unknown")
    config = get_model_config(str(model_name))

    # —— 原生模式：模型支持 function calling ——
    if config.supports_function_calling:
        try:
            agent = AssistantAgent(
                name=name,
                model_client=model_client,
                system_message=system_message,
                output_content_type=schema,
                **agent_kwargs,
            )
            logger.info(f"✅ 创建原生结构化 Agent: {name} (model={model_name})")
            return agent
        except Exception as e:
            logger.warning(f"⚠️ 原生 output_content_type 失败，降级: {e}")

    # —— Fallback 模式：注入 JSON 指令 ——
    logger.info(f"⚠️ 使用 fallback 模式创建 Agent: {name} (model={model_name})")

    # 修改 system_message，注入 JSON schema 指令
    schema_json = json.dumps(schema.model_json_schema(), indent=2, ensure_ascii=False)
    enhanced_system_message = (
        f"{system_message}\n\n"
        f"IMPORTANT: You MUST respond with a valid JSON object that matches this schema:\n"
        f"{schema_json}\n\n"
        f"Rules:\n"
        f"1. Respond with ONLY the JSON object\n"
        f"2. No markdown code blocks, no explanation\n"
        f"3. Use double quotes for strings\n"
        f"4. All fields are required\n"
        f"5. Boolean values must be true or false (lowercase)"
    )

    agent = AssistantAgent(
        name=name,
        model_client=model_client,
        system_message=enhanced_system_message,
        **agent_kwargs,
    )

    # 用 wrapper 包装，拦截输出并解析
    return StructuredAgentWrapper(agent, schema, max_retries)


# ========================================================================
# Agent 包装器
# ========================================================================

class StructuredAgentWrapper:
    """包装 AutoGen AssistantAgent，拦截输出并解析为 Pydantic 实例

    当模型不支持原生结构化输出时使用。
    拦截 agent.run() / agent 的输出，从自由文本中提取 JSON 并验证。
    """

    def __init__(self, agent: Any, schema: Type[T], max_retries: int = 3):
        self._agent = agent
        self._schema = schema
        self._parser = StructuredOutputParser(max_retries=max_retries)

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def _model_client(self):
        return self._agent._model_client

    async def run(self, *, task: str = None, messages: list = None, **kwargs) -> Any:
        """运行 agent 并返回结构化结果

        拦截 agent 的输出，从文本中解析 JSON。
        返回 AutoGen 的 TaskResult，但最后一条消息的 content 会被替换为 Pydantic 实例。
        """
        result = await self._agent.run(task=task, messages=messages, **kwargs)

        # 从最后一条消息中提取结构化数据
        if hasattr(result, "messages") and result.messages:
            last_msg = result.messages[-1]
            content = getattr(last_msg, "content", "")

            if isinstance(content, str) and content.strip():
                # 尝试解析
                from .fallback_parser import _try_parse_json
                parsed = _try_parse_json(content)
                if parsed is not None:
                    try:
                        structured = self._schema.model_validate(parsed)
                        # 替换最后一条消息的 content 为 Pydantic 实例
                        last_msg.content = structured
                        logger.info(f"✅ Fallback 解析成功: {self._schema.__name__}")
                    except Exception as e:
                        logger.warning(f"⚠️ Fallback 解析失败: {e}")

        return result

    async def run_stream(self, *, task: str = None, messages: list = None, **kwargs):
        """流式运行（fallback 模式下收集完整输出后解析）"""
        full_content = ""
        last_message = None

        async for msg in self._agent.run_stream(task=task, messages=messages, **kwargs):
            # 收集文本内容
            if hasattr(msg, "content") and isinstance(msg.content, str):
                full_content = msg.content
                last_message = msg
            yield msg

        # 流结束后尝试解析
        if full_content and last_message:
            from .fallback_parser import _try_parse_json
            parsed = _try_parse_json(full_content)
            if parsed is not None:
                try:
                    structured = self._schema.model_validate(parsed)
                    last_message.content = structured
                except Exception:
                    pass
