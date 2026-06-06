"""
结构化输出容错方案 — 完整演示

运行方式：
    cd d:/GitHub/agents
    python -m 6_structured_output_fallback.demo

演示内容：
  1. 模型能力检测与注册
  2. LangGraph 集成（替换 with_structured_output）
  3. AutoGen 集成（替换 output_content_type）
  4. 三层降级策略的实际表现
  5. JSON 修复能力展示

注意：需要在 .env 中配置对应模型的 API Key
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any

# Windows 终端 UTF-8 兼容
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

# 配置日志，观察降级过程
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("demo")

# 导入本模块
from .schemas import EvaluatorOutput, ImageDescription
from .model_registry import (
    ModelCapability, get_model_config, register_model, ModelConfig
)
from .fallback_parser import StructuredOutputParser, _try_parse_json, _fix_json_string


# ========================================================================
# Demo 1: 模型能力注册表
# ========================================================================

def demo_model_registry():
    """展示模型能力检测与注册"""
    print("\n" + "=" * 60)
    print("📋 Demo 1: 模型能力注册表")
    print("=" * 60)

    # 查询已知模型
    models_to_check = ["gpt-4o-mini", "deepseek-chat", "mimo-v2.5-pro", "llama3.2"]
    for model in models_to_check:
        config = get_model_config(model)
        print(f"  {model:25s} → {config.capability.value}")
        print(f"    {'':25s}   function_calling={config.supports_function_calling}, vision={config.supports_vision}")

    # 注册自定义模型
    print("\n  注册自定义模型 'my-local-qwen':")
    register_model(ModelConfig(
        model_name="my-local-qwen",
        capability=ModelCapability.PROMPT_ONLY,
        base_url="http://localhost:11434/v1",
        supports_function_calling=False,
    ))
    config = get_model_config("my-local-qwen")
    print(f"    → {config.capability.value}, base_url={config.base_url}")

    # 未知模型默认行为
    print("\n  查询未知模型 'some-new-model':")
    config = get_model_config("some-new-model")
    print(f"    → {config.capability.value} (默认降级策略)")


# ========================================================================
# Demo 2: JSON 修复能力
# ========================================================================

def demo_json_repair():
    """展示 JSON 修复能力 — 这是 Layer 2/3 成功的关键"""
    print("\n" + "=" * 60)
    print("🔧 Demo 2: JSON 修复能力")
    print("=" * 60)

    test_cases = [
        (
            "markdown code block",
            '```json\n{"feedback": "Good job", "success_criteria_met": true, "user_input_needed": false}\n```'
        ),
        (
            "前后有文本",
            'Here is my evaluation:\n{"feedback": "Good job", "success_criteria_met": true, "user_input_needed": false}\nHope this helps!'
        ),
        (
            "尾逗号",
            '{"feedback": "Good job", "success_criteria_met": true, "user_input_needed": false,}'
        ),
        (
            "单引号",
            "{'feedback': 'Good job', 'success_criteria_met': true, 'user_input_needed': false}"
        ),
        (
            "有注释",
            '{\n  "feedback": "Good job", // 评估反馈\n  "success_criteria_met": true,\n  "user_input_needed": false\n}'
        ),
        (
            "嵌套在长文本中",
            'I analyzed the response. The result is:\n{\n  "feedback": "The assistant provided a comprehensive answer",\n  "success_criteria_met": true,\n  "user_input_needed": false\n}\nOverall, the task was completed well.'
        ),
    ]

    for name, raw_text in test_cases:
        parsed = _try_parse_json(raw_text)
        status = "✅" if parsed else "❌"
        print(f"\n  {status} {name}:")
        print(f"    输入: {raw_text[:80]}...")
        if parsed:
            print(f"    解析: {json.dumps(parsed, ensure_ascii=False)[:80]}")


# ========================================================================
# Demo 3: 三层降级解析（模拟场景）
# ========================================================================

def demo_fallback_parsing():
    """展示三层降级策略（使用 Mock LLM，不需要真实 API）"""
    print("\n" + "=" * 60)
    print("🔄 Demo 3: 三层降级策略")
    print("=" * 60)

    class MockLLM:
        """模拟 LLM，返回可解析的 JSON"""
        def __init__(self, response: str, model_name: str = "mock-model"):
            self._response = response
            self.model_name = model_name

        def invoke(self, messages):
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            return MockResponse(self._response)

    # 场景 1: LLM 返回标准 JSON（Layer 2 直接成功）
    print("\n  场景 1: LLM 返回标准 JSON")
    mock_llm = MockLLM(
        '{"feedback": "Well done", "success_criteria_met": true, "user_input_needed": false}'
    )
    parser = StructuredOutputParser(max_retries=3)
    result = parser.parse_sync(mock_llm, [], EvaluatorOutput)
    print(f"    结果: feedback='{result.feedback}', met={result.success_criteria_met}")

    # 场景 2: LLM 返回 markdown 包裹的 JSON（Layer 2 + JSON 修复）
    print("\n  场景 2: LLM 返回 markdown 包裹的 JSON")
    mock_llm = MockLLM(
        '```json\n{"feedback": "Needs improvement", "success_criteria_met": false, "user_input_needed": true}\n```'
    )
    result = parser.parse_sync(mock_llm, [], EvaluatorOutput)
    print(f"    结果: feedback='{result.feedback}', met={result.success_criteria_met}, input_needed={result.user_input_needed}")

    # 场景 3: LLM 返回带噪声的 JSON（Layer 2 + 修复）
    print("\n  场景 3: LLM 返回带噪声的 JSON")
    mock_llm = MockLLM(
        'Sure! Here is the evaluation:\n{"feedback": "Great work on the analysis", "success_criteria_met": true, "user_input_needed": false}\nLet me know if you need anything else.'
    )
    result = parser.parse_sync(mock_llm, [], EvaluatorOutput)
    print(f"    结果: feedback='{result.feedback}', met={result.success_criteria_met}")

    # 场景 4: 使用 ImageDescription schema
    print("\n  场景 4: ImageDescription schema")
    mock_llm = MockLLM(
        '{"scene": "A cat sitting on a windowsill", "message": "Peaceful domestic life", "style": "photorealistic", "orientation": "portrait"}'
    )
    result = parser.parse_sync(mock_llm, [], ImageDescription)
    print(f"    结果: scene='{result.scene}', orientation='{result.orientation}'")


# ========================================================================
# Demo 4: LangGraph 集成示例
# ========================================================================

def demo_langgraph_integration():
    """展示如何在 LangGraph 中使用适配器"""
    print("\n" + "=" * 60)
    print("🔷 Demo 4: LangGraph 集成")
    print("=" * 60)

    try:
        from langchain_openai import ChatOpenAI
        from .langgraph_adapter import create_structured_llm, safe_evaluator

        # —— 原始写法（不兼容 MiMo）——
        print("\n  ❌ 原始写法（MiMo 会报错）:")
        print('    evaluator_llm = ChatOpenAI(model="mimo-v2.5-pro", ...)')
        print('    evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)')
        print('    # → NotImplementedError 或 API Error')

        # —— 新写法（自动容错）——
        print("\n  ✅ 新写法（自动容错）:")
        print('    from langgraph_adapter import create_structured_llm')
        print('    evaluator_llm_with_output = create_structured_llm(evaluator_llm, EvaluatorOutput)')

        # 实际创建（使用 gpt-4o-mini 演示，因为它一定可用）
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            llm = ChatOpenAI(model="gpt-4o-mini")
            wrapped = create_structured_llm(llm, EvaluatorOutput)
            print(f"\n    ✅ 创建成功: {type(wrapped).__name__}")
            print(f"    模型: {wrapped.model}")
            print(f"    调用方式: wrapped.invoke(messages) → EvaluatorOutput")
        else:
            print("\n    ⚠️ 未配置 OPENAI_API_KEY，跳过实际调用演示")

        # —— safe_evaluator 用法 ——
        print("\n  safe_evaluator() 用法（替换 4_lab4.py 的 evaluator 函数）:")
        print("""
    from langgraph_adapter import safe_evaluator

    def evaluator(state: State) -> Dict[str, Any]:
        return safe_evaluator(
            state=state,
            evaluator_llm=evaluator_llm,  # 不需要 with_structured_output
            evaluator_schema=EvaluatorOutput,
            format_conversation_fn=format_conversation,
        )
        """)

    except ImportError as e:
        print(f"\n  ⚠️ 缺少依赖: {e}")
        print("  安装: pip install langchain-openai langgraph")


# ========================================================================
# Demo 5: AutoGen 集成示例
# ========================================================================

def demo_autogen_integration():
    """展示如何在 AutoGen 中使用适配器"""
    print("\n" + "=" * 60)
    print("🔶 Demo 5: AutoGen 集成")
    print("=" * 60)

    try:
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        # —— 原始写法 ——
        print("\n  ❌ 原始写法（MiMo/Llama 会报错）:")
        print('    describer = AssistantAgent(')
        print('        name="description_agent",')
        print('        model_client=model_client,')
        print('        output_content_type=ImageDescription,  # 依赖 function calling')
        print('    )')

        # —— 新写法 ——
        print("\n  ✅ 新写法（自动容错）:")
        print('    from autogen_adapter import create_structured_agent')
        print('    describer = create_structured_agent(')
        print('        name="description_agent",')
        print('        model_client=model_client,')
        print('        schema=ImageDescription,')
        print('        system_message="You are good at describing images in detail",')
        print('    )')

        # 展示配置
        print("\n  模型能力自动检测:")
        for model in ["gpt-4o-mini", "mimo-v2.5-pro", "llama3.2"]:
            config = get_model_config(model)
            mode = "原生 output_content_type" if config.supports_function_calling else "Fallback prompt+JSON"
            print(f"    {model:20s} → {mode}")

    except ImportError as e:
        print(f"\n  ⚠️ 缺少依赖: {e}")
        print("  安装: pip install autogen-agentchat autogen-ext[openai]")


# ========================================================================
# Demo 6: 真实 API 调用（可选）
# ========================================================================

async def demo_real_api():
    """真实 API 调用演示（需要配置 API Key）"""
    print("\n" + "=" * 60)
    print("🚀 Demo 6: 真实 API 调用")
    print("=" * 60)

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
    except ImportError:
        print("  ⚠️ 缺少 langchain-openai，跳过")
        return

    test_message = [
        HumanMessage(content="""Evaluate this response:
The assistant said: "The capital of France is Paris, which has been the capital since the 10th century."
Success criteria: "Answer should be accurate and include historical context"
Please provide your evaluation.""")
    ]

    # 测试不同模型
    models_to_test = []

    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        models_to_test.append(("gpt-4o-mini (NATIVE)", {
            "model": "gpt-4o-mini",
            "capability": ModelCapability.NATIVE_JSON_SCHEMA,
        }))

    # DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        models_to_test.append(("deepseek-chat (JSON_MODE)", {
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "capability": ModelCapability.JSON_MODE,
        }))

    # MiMo
    if os.getenv("MIMO_API_KEY"):
        models_to_test.append(("mimo-v2.5-pro (PROMPT_ONLY)", {
            "model": "mimo-v2.5-pro",
            "base_url": "https://api.xiaomimimo.com/v1",
            "api_key": os.getenv("MIMO_API_KEY"),
            "capability": ModelCapability.PROMPT_ONLY,
        }))

    if not models_to_test:
        print("  ⚠️ 未配置任何 API Key，跳过真实调用")
        print("  请在 .env 中配置 OPENAI_API_KEY / DEEPSEEK_API_KEY / MIMO_API_KEY")
        return

    parser = StructuredOutputParser(max_retries=3)

    for name, params in models_to_test:
        print(f"\n  测试 {name}:")
        try:
            capability = params.pop("capability")
            llm = ChatOpenAI(**params)
            result = parser.parse_sync(llm, test_message, EvaluatorOutput, capability=capability)
            print(f"    ✅ feedback: '{result.feedback[:60]}...'")
            print(f"    ✅ success_criteria_met: {result.success_criteria_met}")
            print(f"    ✅ user_input_needed: {result.user_input_needed}")
        except Exception as e:
            print(f"    ❌ 失败: {e}")


# ========================================================================
# 主入口
# ========================================================================

def main():
    print("╔" + "═" * 58 + "╗")
    print("║  结构化输出容错方案 — 生产级演示                          ║")
    print("║  Structured Output Fallback — Production Demo           ║")
    print("╚" + "═" * 58 + "╝")

    # 同步 demo
    demo_model_registry()
    demo_json_repair()
    demo_fallback_parsing()
    demo_langgraph_integration()
    demo_autogen_integration()

    # 异步 demo（真实 API）
    print("\n" + "=" * 60)
    print("是否运行真实 API 调用演示？(需要配置 API Key)")
    print("=" * 60)

    try:
        asyncio.run(demo_real_api())
    except Exception as e:
        print(f"  ⚠️ 异步演示出错: {e}")

    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)

    # 总结
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    生产环境使用指南                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. LangGraph 场景：                                         ║
║     from langgraph_adapter import create_structured_llm      ║
║     wrapped = create_structured_llm(llm, YourSchema)         ║
║     result = wrapped.invoke(messages)                        ║
║                                                              ║
║  2. AutoGen 场景：                                           ║
║     from autogen_adapter import create_structured_agent      ║
║     agent = create_structured_agent(                         ║
║         name="agent", model_client=client, schema=Schema)   ║
║                                                              ║
║  3. 通用场景：                                                ║
║     from fallback_parser import StructuredOutputParser       ║
║     parser = StructuredOutputParser(max_retries=3)           ║
║     result = parser.parse_sync(llm, messages, Schema)       ║
║                                                              ║
║  4. 注册自定义模型：                                          ║
║     from model_registry import register_model, ModelConfig   ║
║     register_model(ModelConfig(...))                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
