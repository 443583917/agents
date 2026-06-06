"""
结构化输出容错方案 — 生产级适配器

三层降级策略：
  Layer 1: 原生结构化输出 (with_structured_output / response_format)
  Layer 2: Prompt 注入 JSON 指令 + Pydantic 解析（带重试）
  Layer 3: 正则提取 JSON 片段 + Pydantic 解析
  兜底:   返回默认值或抛出明确异常
"""

from .schemas import EvaluatorOutput, ImageDescription
from .model_registry import ModelCapability, ModelConfig, get_model_config, register_model
from .fallback_parser import StructuredOutputParser, create_parser
from .langgraph_adapter import create_structured_llm, safe_evaluator
from .autogen_adapter import create_structured_agent

__all__ = [
    # Schema
    "EvaluatorOutput",
    "ImageDescription",
    # Registry
    "ModelCapability",
    "ModelConfig",
    "get_model_config",
    "register_model",
    # Parser
    "StructuredOutputParser",
    "create_parser",
    # LangGraph
    "create_structured_llm",
    "safe_evaluator",
    # AutoGen
    "create_structured_agent",
]
