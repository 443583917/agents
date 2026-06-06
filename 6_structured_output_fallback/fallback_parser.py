"""
核心容错解析器 — 三层降级策略

当模型不支持原生结构化输出时，按以下顺序降级：
  Layer 1: 原生结构化输出 (with_structured_output / response_format)
  Layer 2: Prompt 注入 JSON 指令 + Pydantic 解析（带重试 + 错误反馈）
  Layer 3: 正则提取 JSON 片段 + Pydantic 解析
  兜底:   返回默认值或抛出明确异常

关键设计：
  - 重试时把 Pydantic 验证错误反馈给 LLM，让它自我修正
  - JSON 修复处理常见格式问题（markdown 包裹、尾逗号、单引号）
  - 每次降级都记录日志，生产环境可追溯
  - 同步/异步双支持
"""

import re
import json
import logging
from typing import Type, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel, ValidationError

from .model_registry import ModelCapability, get_model_config

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


# ========================================================================
# JSON 修复工具
# ========================================================================

def _fix_json_string(text: str) -> str:
    """修复 LLM 返回的常见 JSON 格式问题

    处理场景：
    1. markdown code block 包裹: ```json\n{...}\n```
    2. 前后有多余文本: "Here is the result: {...} Hope this helps!"
    3. 尾逗号: {"a": 1, "b": 2,}
    4. 单引号: {'a': 'b'}
    5. 注释: // or /* */
    """
    # 1. 提取 markdown code block 中的 JSON
    code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if code_block:
        text = code_block.group(1).strip()

    # 2. 提取最外层的 { ... } 或 [ ... ]
    json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if json_match:
        text = json_match.group(1)

    # 3. 移除单行注释
    text = re.sub(r"//[^\n]*", "", text)

    # 4. 移除多行注释
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)

    # 5. 修复尾逗号 (,} 或 ,])
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # 6. 单引号替换为双引号（简单场景，不处理嵌套）
    # 注意：这可能破坏包含单引号的值，所以只在解析失败后尝试
    return text.strip()


def _try_parse_json(text: str) -> Optional[dict | list]:
    """尝试从文本中解析 JSON，返回 None 表示失败"""
    # 第一次尝试：直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 第二次尝试：修复后解析
    fixed = _fix_json_string(text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 第三次尝试：单引号替换
    try:
        return json.loads(fixed.replace("'", '"'))
    except (json.JSONDecodeError, Exception):
        pass

    return None


# ========================================================================
# Prompt 模板
# ========================================================================

_JSON_INSTRUCTION_TEMPLATE = """You MUST respond with a valid JSON object that matches this Pydantic schema exactly.

Schema:
{schema_json}

Rules:
1. Respond with ONLY the JSON object, no markdown, no explanation, no code blocks
2. All fields are required
3. Use double quotes for strings
4. Do not include trailing commas
5. Boolean values must be true or false (lowercase)

{error_feedback}"""

_ERROR_FEEDBACK_TEMPLATE = """
IMPORTANT: Your previous response had validation errors. Fix them and try again.

Your previous response:
```
{previous_response}
```

Validation errors:
{errors}

Please respond with the corrected JSON object only."""


def _build_system_prompt(schema: Type[BaseModel], error_feedback: Optional[str] = None) -> str:
    """构建引导 LLM 输出 JSON 的 system prompt"""
    schema_json = schema.model_json_schema()
    # 简化 schema，去掉冗余的 title/description
    schema_str = json.dumps(schema_json, indent=2, ensure_ascii=False)

    return _JSON_INSTRUCTION_TEMPLATE.format(
        schema_json=schema_str,
        error_feedback=error_feedback or "",
    )


# ========================================================================
# 核心解析器
# ========================================================================

class StructuredOutputParser:
    """生产级结构化输出解析器

    使用方式：
        parser = StructuredOutputParser()
        result = await parser.parse(llm, messages, EvaluatorOutput)
        # result 是 EvaluatorOutput 实例
    """

    def __init__(self, max_retries: int = 3, log_level: int = logging.WARNING):
        self.max_retries = max_retries
        self._log_level = log_level

    # ——————————————————————————————————————
    #  公开 API
    # ——————————————————————————————————————

    def parse_sync(
        self,
        llm: Any,
        messages: List[Any],
        schema: Type[T],
        capability: Optional[ModelCapability] = None,
    ) -> T:
        """同步解析入口"""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # 已在异步上下文中，用 nest_asyncio 兼容
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(
                self._parse_impl(llm, messages, schema, capability)
            )
        else:
            return asyncio.run(
                self._parse_impl(llm, messages, schema, capability)
            )

    async def parse(
        self,
        llm: Any,
        messages: List[Any],
        schema: Type[T],
        capability: Optional[ModelCapability] = None,
    ) -> T:
        """异步解析入口"""
        return await self._parse_impl(llm, messages, schema, capability)

    # ——————————————————————————————————————
    #  内部实现
    # ——————————————————————————————————————

    async def _parse_impl(
        self,
        llm: Any,
        messages: List[Any],
        schema: Type[T],
        capability: Optional[ModelCapability] = None,
    ) -> T:
        """三层降级解析"""
        # 自动探测能力
        if capability is None:
            model_name = getattr(llm, "model_name", None) or getattr(llm, "model", "unknown")
            config = get_model_config(str(model_name))
            capability = config.capability

        # —— Layer 1: 原生结构化输出 ——
        if capability in (ModelCapability.NATIVE_JSON_SCHEMA, ModelCapability.JSON_MODE):
            try:
                result = await self._try_native(llm, messages, schema)
                if result is not None:
                    logger.info("✅ Layer 1 成功: 原生结构化输出")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Layer 1 失败，降级到 Layer 2: {e}")

        # —— Layer 2: Prompt JSON + 重试 ——
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await self._try_prompt_json(llm, messages, schema, attempt)
                if result is not None:
                    logger.info(f"✅ Layer 2 成功: Prompt JSON (第 {attempt} 次尝试)")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Layer 2 第 {attempt} 次失败: {e}")

        # —— Layer 3: 正则提取 ——
        try:
            result = await self._try_regex_extract(llm, messages, schema)
            if result is not None:
                logger.warning("⚠️ Layer 3 成功: 正则提取 JSON（质量可能较低）")
                return result
        except Exception as e:
            logger.warning(f"⚠️ Layer 3 失败: {e}")

        # —— 兜底 ——
        logger.error("❌ 所有降级策略均失败，返回 schema 默认值")
        return self._get_default(schema)

    async def _try_native(
        self, llm: Any, messages: List[Any], schema: Type[T]
    ) -> Optional[T]:
        """Layer 1: 使用 LLM 原生的 with_structured_output()"""
        try:
            structured_llm = llm.with_structured_output(schema)
            result = structured_llm.invoke(messages)
            if isinstance(result, schema):
                return result
            # 有些实现返回 dict
            if isinstance(result, dict):
                return schema.model_validate(result)
        except Exception as e:
            logger.debug(f"原生结构化输出失败: {e}")
            raise

    async def _try_prompt_json(
        self,
        llm: Any,
        messages: List[Any],
        schema: Type[T],
        attempt: int = 1,
    ) -> Optional[T]:
        """Layer 2: 注入 JSON 指令到 prompt，手动解析返回"""
        from langchain_core.messages import SystemMessage, HumanMessage

        # 构建错误反馈（重试时）
        error_feedback = None
        if attempt > 1 and hasattr(self, "_last_error"):
            error_feedback = self._last_error

        system_prompt = _build_system_prompt(schema, error_feedback)

        # 注入/替换 SystemMessage
        llm_messages = []
        has_system = False
        for msg in messages:
            if isinstance(msg, SystemMessage):
                llm_messages.append(SystemMessage(content=system_prompt))
                has_system = True
            else:
                llm_messages.append(msg)
        if not has_system:
            llm_messages.insert(0, SystemMessage(content=system_prompt))

        # 调用 LLM
        response = llm.invoke(llm_messages)
        content = response.content if hasattr(response, "content") else str(response)

        # 解析 JSON
        parsed = _try_parse_json(content)
        if parsed is None:
            self._last_error = f"无法从 LLM 输出中解析 JSON。原始输出:\n{content[:500]}"
            logger.warning(f"Layer 2 解析失败 (第 {attempt} 次)")
            return None

        # Pydantic 验证
        try:
            result = schema.model_validate(parsed)
            return result
        except ValidationError as e:
            error_msg = "; ".join(
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in e.errors()
            )
            self._last_error = (
                f"Pydantic 验证失败: {error_msg}\n"
                f"原始 JSON: {json.dumps(parsed, ensure_ascii=False)[:500]}"
            )
            logger.warning(f"Layer 2 验证失败 (第 {attempt} 次): {error_msg}")
            return None

    async def _try_regex_extract(
        self, llm: Any, messages: List[Any], schema: Type[T]
    ) -> Optional[T]:
        """Layer 3: 让 LLM 自由回答，用正则提取 JSON 片段"""
        from langchain_core.messages import SystemMessage

        # 简单指令，不强制 JSON 格式
        simple_messages = list(messages)
        for i, msg in enumerate(simple_messages):
            if isinstance(msg, SystemMessage):
                simple_messages[i] = SystemMessage(
                    content=msg.content
                    + "\n\nPlease include a JSON object in your response "
                    "that matches this structure: "
                    + json.dumps(schema.model_json_schema(), ensure_ascii=False)
                )
                break

        response = llm.invoke(simple_messages)
        content = response.content if hasattr(response, "content") else str(response)

        # 正则提取
        parsed = _try_parse_json(content)
        if parsed is None:
            return None

        try:
            return schema.model_validate(parsed)
        except ValidationError as e:
            logger.debug(f"Layer 3 验证失败: {e}")
            return None

    @staticmethod
    def _get_default(schema: Type[T]) -> T:
        """兜底：尝试构造一个最小的默认实例

        策略：
        - 字符串字段 → ""
        - 布尔字段 → False
        - 数值字段 → 0
        - Literal 字段 → 取第一个选项
        """
        defaults: Dict[str, Any] = {}
        for field_name, field_info in schema.model_fields.items():
            annotation = field_info.annotation
            # 有默认值
            if field_info.default is not None and field_info.default is not ...:
                defaults[field_name] = field_info.default
            elif annotation is str:
                defaults[field_name] = ""
            elif annotation is bool:
                defaults[field_name] = False
            elif annotation is int:
                defaults[field_name] = 0
            elif annotation is float:
                defaults[field_name] = 0.0
            else:
                # Literal 或其他类型，取第一个参数
                args = getattr(annotation, "__args__", None)
                if args:
                    defaults[field_name] = args[0]
                else:
                    defaults[field_name] = None

        return schema.model_validate(defaults)


# ========================================================================
# 便捷函数
# ========================================================================

def create_parser(max_retries: int = 3) -> StructuredOutputParser:
    """创建解析器实例的工厂函数"""
    return StructuredOutputParser(max_retries=max_retries)
