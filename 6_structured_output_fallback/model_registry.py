"""
模型能力检测与注册表

核心问题：不同 LLM 对结构化输出的支持差异巨大
- GPT-4o/4o-mini: 原生支持 json_schema (response_format)
- DeepSeek: 支持 JSON mode，不支持 json_schema
- MiMo (小米): 不支持 response_format json_schema
- Ollama llama3.2: 部分支持，取决于量化版本和推理引擎

本模块提供：
1. ModelCapability 枚举：三级能力分类
2. 内置映射表：已知模型的能力
3. 运行时探测：发测试请求验证实际能力
4. 统一配置入口：根据模型名返回完整配置
"""

import os
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# ========================================================================
# 能力枚举
# ========================================================================

class ModelCapability(Enum):
    """模型结构化输出能力分级"""
    # 原生支持 json_schema (response_format={"type": "json_schema", ...})
    # GPT-4o, GPT-4o-mini, Claude 3.5, Gemini 1.5 Pro 等
    NATIVE_JSON_SCHEMA = "native_json_schema"

    # 支持 JSON mode (response_format={"type": "json_object"})
    # DeepSeek, 部分 Ollama 模型等
    JSON_MODE = "json_mode"

    # 不支持任何结构化输出，只能靠 prompt 引导
    # MiMo, 一些小模型, 本地部署的旧模型
    PROMPT_ONLY = "prompt_only"


# ========================================================================
# 模型配置
# ========================================================================

@dataclass
class ModelConfig:
    """单个模型的完整配置"""
    model_name: str
    capability: ModelCapability
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None  # 环境变量名
    supports_function_calling: bool = True
    supports_vision: bool = False
    max_output_tokens: int = 4096
    # 重试策略
    max_retries: int = 3
    # 自定义请求参数（透传给 LLM client）
    extra_params: Dict[str, Any] = field(default_factory=dict)


# ========================================================================
# 内置映射表 — 已知模型的能力
# ========================================================================

MODEL_REGISTRY: Dict[str, ModelConfig] = {
    # ——— OpenAI 系列 ———
    "gpt-4o": ModelConfig(
        model_name="gpt-4o",
        capability=ModelCapability.NATIVE_JSON_SCHEMA,
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gpt-4o-mini": ModelConfig(
        model_name="gpt-4o-mini",
        capability=ModelCapability.NATIVE_JSON_SCHEMA,
        supports_function_calling=True,
        supports_vision=True,
    ),
    "gpt-4.1-mini": ModelConfig(
        model_name="gpt-4.1-mini",
        capability=ModelCapability.NATIVE_JSON_SCHEMA,
        supports_function_calling=True,
        supports_vision=True,
    ),

    # ——— DeepSeek ———
    "deepseek-chat": ModelConfig(
        model_name="deepseek-chat",
        capability=ModelCapability.JSON_MODE,
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        supports_function_calling=True,
        supports_vision=False,
    ),
    "deepseek-reasoner": ModelConfig(
        model_name="deepseek-reasoner",
        capability=ModelCapability.JSON_MODE,
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        supports_function_calling=False,
        supports_vision=False,
    ),

    # ——— 小米 MiMo ———
    "mimo-v2.5-pro": ModelConfig(
        model_name="mimo-v2.5-pro",
        capability=ModelCapability.PROMPT_ONLY,
        base_url="https://api.xiaomimimo.com/v1",
        api_key_env="MIMO_API_KEY",
        supports_function_calling=False,
        supports_vision=False,
    ),

    # ——— Claude ———
    "claude-3-5-sonnet-20241022": ModelConfig(
        model_name="claude-3-5-sonnet-20241022",
        capability=ModelCapability.NATIVE_JSON_SCHEMA,
        supports_function_calling=True,
        supports_vision=True,
    ),

    # ——— Ollama 本地模型 ———
    "llama3.2": ModelConfig(
        model_name="llama3.2",
        capability=ModelCapability.PROMPT_ONLY,
        base_url="http://localhost:11434/v1",
        supports_function_calling=False,
        supports_vision=False,
    ),
    "llama3.1:8b": ModelConfig(
        model_name="llama3.1:8b",
        capability=ModelCapability.PROMPT_ONLY,
        base_url="http://localhost:11434/v1",
        supports_function_calling=False,
        supports_vision=False,
    ),
    "qwen2.5:7b": ModelConfig(
        model_name="qwen2.5:7b",
        capability=ModelCapability.PROMPT_ONLY,
        base_url="http://localhost:11434/v1",
        supports_function_calling=False,
        supports_vision=False,
    ),
}


# ========================================================================
# API
# ========================================================================

def get_model_config(model_name: str) -> ModelConfig:
    """获取模型配置，未知模型默认为 PROMPT_ONLY

    生产建议：首次使用未知模型时，调用 probe_capability() 探测实际能力，
    然后用 register_model() 写入映射表。
    """
    if model_name in MODEL_REGISTRY:
        return MODEL_REGISTRY[model_name]

    logger.warning(
        f"未知模型 '{model_name}'，默认为 PROMPT_ONLY。"
        f"建议调用 probe_capability() 探测实际能力后注册。"
    )
    return ModelConfig(
        model_name=model_name,
        capability=ModelCapability.PROMPT_ONLY,
    )


def register_model(config: ModelConfig) -> None:
    """注册或更新模型配置到映射表"""
    MODEL_REGISTRY[config.model_name] = config
    logger.info(f"已注册模型: {config.model_name} -> {config.capability.value}")


async def probe_capability(
    model_name: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> ModelCapability:
    """运行时探测模型的结构化输出能力

    策略：依次尝试 json_schema → json_mode → prompt_only，看哪个成功。
    这是最可靠的方式，因为：
    1. 模型提供商可能随时更新 API 能力
    2. 同一模型的不同部署版本能力可能不同
    3. 自定义部署（如 vLLM）的配置各异
    """
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel, Field

    # 简单的测试 schema
    class _Probe(BaseModel):
        answer: str = Field(description="Just say 'ok'")

    probe_messages = [
        {"role": "user", "content": "Reply with a JSON object: {\"answer\": \"ok\"}"}
    ]

    llm_params: Dict[str, Any] = {"model": model_name, "temperature": 0}
    if base_url:
        llm_params["base_url"] = base_url
    if api_key:
        llm_params["api_key"] = api_key

    # —— 测试 1: json_schema ——
    try:
        llm = ChatOpenAI(**llm_params)
        result = llm.with_structured_output(_Probe, method="json_schema")
        resp = result.invoke(probe_messages)
        if hasattr(resp, "answer") and resp.answer:
            logger.info(f"[probe] {model_name}: 支持 NATIVE_JSON_SCHEMA")
            return ModelCapability.NATIVE_JSON_SCHEMA
    except Exception as e:
        logger.debug(f"[probe] {model_name} json_schema 失败: {e}")

    # —— 测试 2: json_mode ——
    try:
        llm_params_copy = {**llm_params, "model_kwargs": {"response_format": {"type": "json_object"}}}
        llm = ChatOpenAI(**llm_params_copy)
        resp = llm.invoke(probe_messages)
        content = resp.content if hasattr(resp, "content") else str(resp)
        if "{" in content and "}" in content:
            logger.info(f"[probe] {model_name}: 支持 JSON_MODE")
            return ModelCapability.JSON_MODE
    except Exception as e:
        logger.debug(f"[probe] {model_name} json_mode 失败: {e}")

    logger.info(f"[probe] {model_name}: 仅支持 PROMPT_ONLY")
    return ModelCapability.PROMPT_ONLY
