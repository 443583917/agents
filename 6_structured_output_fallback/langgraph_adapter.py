"""
LangGraph 结构化输出适配器

提供两种使用方式：
1. create_structured_llm() — 返回一个可以当普通 LLM 用的对象，自动处理结构化输出
2. safe_evaluator() — 直接替换 4_lab4.py 中的 evaluator 节点逻辑

用法示例（替换 4_lab4.py 第 158-168 行）：

    from structured_output_fallback.langgraph_adapter import create_structured_llm

    evaluator_llm = ChatOpenAI(
        model="mimo-v2.5-pro",
        base_url="https://api.xiaomimimo.com/v1",
        api_key=os.getenv("MIMO_API_KEY"),
    )
    # 自动检测能力，不支持原生时走 prompt fallback
    evaluator_llm_with_output = create_structured_llm(evaluator_llm, EvaluatorOutput)
"""

import logging
from typing import Type, TypeVar, Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from .model_registry import get_model_config, ModelCapability
from .fallback_parser import StructuredOutputParser

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


# ========================================================================
# 核心：包装 LLM，使其始终返回结构化输出
# ========================================================================

class StructuredLLMWrapper:
    """包装任意 LLM，使其 invoke() 始终返回 Pydantic 实例

    内部自动选择最优的结构化输出策略：
    - 模型支持原生 → 走 with_structured_output()
    - 不支持 → 走 fallback_parser 的三层降级

    使用方式与 LangChain 的 with_structured_output() 返回值一致：
        wrapped = StructuredLLMWrapper(llm, EvaluatorOutput)
        result = wrapped.invoke(messages)  # 返回 EvaluatorOutput 实例
    """

    def __init__(
        self,
        llm: BaseChatModel,
        schema: Type[T],
        capability: Optional[ModelCapability] = None,
        max_retries: int = 3,
    ):
        self._llm = llm
        self._schema = schema
        self._max_retries = max_retries
        self._parser = StructuredOutputParser(max_retries=max_retries)

        # 确定模型能力
        if capability is not None:
            self._capability = capability
        else:
            model_name = getattr(llm, "model_name", None) or getattr(llm, "model", "unknown")
            config = get_model_config(str(model_name))
            self._capability = config.capability

        # 尝试预构建原生 structured LLM
        self._native_llm = None
        if self._capability in (ModelCapability.NATIVE_JSON_SCHEMA, ModelCapability.JSON_MODE):
            try:
                self._native_llm = llm.with_structured_output(schema)
                logger.info(f"✅ 预构建原生结构化 LLM 成功 ({self._capability.value})")
            except Exception as e:
                logger.warning(f"⚠️ 预构建原生结构化 LLM 失败，将使用 fallback: {e}")

    @property
    def model(self) -> str:
        """兼容 LangChain 的 model 属性"""
        return getattr(self._llm, "model_name", None) or getattr(self._llm, "model", "unknown")

    def invoke(self, messages: List[Any], **kwargs) -> T:
        """调用 LLM 并返回结构化结果

        优先使用原生结构化输出，失败时自动降级到 prompt fallback。
        返回值始终是 schema 的 Pydantic 实例。
        """
        # Layer 1: 原生
        if self._native_llm is not None:
            try:
                result = self._native_llm.invoke(messages, **kwargs)
                if isinstance(result, self._schema):
                    return result
                if isinstance(result, dict):
                    return self._schema.model_validate(result)
            except Exception as e:
                logger.warning(f"⚠️ 原生结构化调用失败，降级: {e}")

        # Layer 2-3 + 兜底: 使用 fallback_parser
        return self._parser.parse_sync(
            self._llm, messages, self._schema, self._capability
        )

    async def ainvoke(self, messages: List[Any], **kwargs) -> T:
        """异步版本"""
        if self._native_llm is not None:
            try:
                if hasattr(self._native_llm, "ainvoke"):
                    result = await self._native_llm.ainvoke(messages, **kwargs)
                else:
                    result = self._native_llm.invoke(messages, **kwargs)
                if isinstance(result, self._schema):
                    return result
                if isinstance(result, dict):
                    return self._schema.model_validate(result)
            except Exception as e:
                logger.warning(f"⚠️ 原生异步结构化调用失败，降级: {e}")

        return await self._parser.parse(
            self._llm, messages, self._schema, self._capability
        )


def create_structured_llm(
    llm: BaseChatModel,
    schema: Type[T],
    capability: Optional[ModelCapability] = None,
    max_retries: int = 3,
) -> StructuredLLMWrapper:
    """创建带容错的结构化 LLM

    这是 LangGraph 场景的主要入口。返回值可以直接替代
    llm.with_structured_output(schema) 的结果。

    参数：
        llm: 任意 LangChain ChatModel
        schema: Pydantic BaseModel 子类
        capability: 显式指定模型能力（可选，默认自动检测）
        max_retries: prompt fallback 最大重试次数

    返回：
        StructuredLLMWrapper，调用 invoke(messages) 返回 Pydantic 实例

    示例：
        # 原来的写法（不兼容 MiMo 等模型）
        evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        # 新写法（自动容错）
        evaluator_llm_with_output = create_structured_llm(evaluator_llm, EvaluatorOutput)
    """
    return StructuredLLMWrapper(llm, schema, capability, max_retries)


# ========================================================================
# 便捷函数：直接替换 4_lab4.py 的 evaluator 节点
# ========================================================================

def safe_evaluator(
    state: Dict[str, Any],
    evaluator_llm: BaseChatModel,
    evaluator_schema: Type[T],
    format_conversation_fn=None,
) -> Dict[str, Any]:
    """带容错的 evaluator 节点

    直接替换 4_lab4.py 中的 evaluator() 函数。
    内部自动处理结构化输出降级。

    参数：
        state: LangGraph State
        evaluator_llm: 评估用 LLM（不要求支持结构化输出）
        evaluator_schema: 输出 Pydantic Schema
        format_conversation_fn: 格式化对话历史的函数（可选）

    返回：
        Dict 格式的 state 更新
    """
    last_response = state["messages"][-1].content

    system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
and whether more input is needed from the user."""

    # 格式化对话历史
    if format_conversation_fn:
        conversation = format_conversation_fn(state["messages"])
    else:
        conversation = "Conversation history:\n\n"
        for message in state["messages"]:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"

    user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

The entire conversation with the assistant, with the user's original request and all replies, is:
{conversation}

The success criteria for this assignment is:
{state['success_criteria']}

And the final response from the Assistant that you are evaluating is:
{last_response}

Respond with your feedback, and decide if the success criteria is met by this response.
Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.
"""
    if state.get("feedback_on_work"):
        user_message += (
            f"Also, note that in a prior attempt from the Assistant, "
            f"you provided this feedback: {state['feedback_on_work']}\n"
        )
        user_message += (
            "If you're seeing the Assistant repeating the same mistakes, "
            "then consider responding that user input is required."
        )

    evaluator_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    # 使用容错解析器
    parser = StructuredOutputParser(max_retries=3)
    eval_result = parser.parse_sync(evaluator_llm, evaluator_messages, evaluator_schema)

    return {
        "messages": [
            AIMessage(content=f"Evaluator Feedback on this answer: {eval_result.feedback}")
        ],
        "feedback_on_work": eval_result.feedback,
        "success_criteria_met": eval_result.success_criteria_met,
        "user_input_needed": eval_result.user_input_needed,
    }
