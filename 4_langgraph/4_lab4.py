"""
agent_env\Scripts\python.exe 4_langgraph\4_lab4.py  服务启动指定py版本环境
================================================================================
第四周第四天 — The Sidekick（贴身助手）

一个多 Agent 协作系统：
  - Worker Agent（DeepSeek）：执行任务 + 调用浏览器工具
  - Evaluator Agent（MiMo / 小米大模型）：评估 Worker 输出是否达标
6
核心概念:
  1. 结构化输出（Pydantic BaseModel → LLM.with_structured_output()）
  2. 多 Agent 流程（Worker ↔ Evaluator 循环，直到达标或需要用户输入）

从 .ipynb 提取并适配为独立 .py 脚本
================================================================================
"""

# ============================================================
#  必须在所有 import 之前：禁用系统代理对本机地址的影响
# ============================================================
import os
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

# ============================================================
#  异步支持（必须在 Playwright 初始化之前）
#  - 使用默认 ProactorEventLoop（Python 3.12+ 均支持 subprocess）
#  - 手动创建事件循环（Python 3.12/3.14 都兼容）
#  - nest_asyncio：允许 Gradio 事件循环内嵌套 run_until_complete
# ============================================================
import asyncio

# 手动创建事件循环（Python 3.12 无害，Python 3.14 必须）
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

# nest_asyncio: 允许 Gradio 事件循环内嵌套 run_until_complete
# 注意：保存原始 asyncio.run，nest_asyncio 的包装不接受 uvicorn 的 loop_factory 参数
_asyncio_run_original = asyncio.run
import nest_asyncio
nest_asyncio.apply()
asyncio.run = _asyncio_run_original  # 恢复原始 asyncio.run

# ========================================================================
# 导入
# ========================================================================
from typing import Annotated, TypedDict, List, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
import gradio as gr
import uuid
from dotenv import load_dotenv

# ========================================================================
# 环境配置
# ========================================================================
load_dotenv(override=True)

# ========================================================================
# 结构化输出 Schema — Evaluator 的输出格式
# ========================================================================
class EvaluatorOutput(BaseModel):
    """评估器输出：对 Worker Agent 回复的评估结果"""
    feedback: str = Field(
        description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, "
                    "or clarifications, or the assistant is stuck"
    )


# ========================================================================
# State 定义 — Agent 内部上下文流转
# ========================================================================
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


# ========================================================================
# Playwright 浏览器工具初始化（Async API + nest_asyncio）
# 与 notebook 一致：async_browser 在主线程事件循环中运行，不跨线程
# ========================================================================
async_browser = create_async_playwright_browser(headless=True)

# 创建浏览器上下文并设置 10 秒全局超时
async def _init_context():
    ctx = await async_browser.new_context()
    ctx.set_default_timeout(10000)
    ctx.set_default_navigation_timeout(10000)
    return ctx
_loop.run_until_complete(_init_context())

toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
_raw_tools = toolkit.get_tools()

# 给每个工具加带进度打印的超时等待
# 每秒输出等待状态，超时后返回错误字符串，不会卡死流程
import functools
TOOL_TIMEOUT = 60  # 1分钟

def _wrap_tool_timeout(tool):
    if not hasattr(tool, '_arun'):
        return tool
    _original_arun = tool._arun
    tool_name = getattr(tool, 'name', tool.__class__.__name__)

    @functools.wraps(_original_arun)
    async def _arun_with_timeout(*args, **kwargs):
        task = asyncio.ensure_future(_original_arun(*args, **kwargs))
        elapsed = 0
        while not task.done():
            print(f"\r   ⏳ 等待 [{tool_name}] 完成... ({elapsed}s)", end="")
            await asyncio.sleep(1)
            elapsed += 1
            if elapsed >= TOOL_TIMEOUT:
                task.cancel()
                print(f"\r   ❌ [{tool_name}] 超时 ({TOOL_TIMEOUT}s)，已中断    ")
                return f"[TOOL TIMEOUT] 执行超过 {TOOL_TIMEOUT} 秒，已中断"
        try:
            result = task.result()
        except Exception as e:
            print(f"\r   ❌ [{tool_name}] 异常: {e}    ")
            return f"[TOOL ERROR] {e}"
        print(f"\r   ✅ [{tool_name}] 完成 ({elapsed}s)    ")
        return result
    tool._arun = _arun_with_timeout
    return tool

tools = [_wrap_tool_timeout(t) for t in _raw_tools]


# ========================================================================
# 初始化 LLM
# ========================================================================
# ——— Worker LLM：DeepSeek（执行任务 + 调用浏览器工具）———
worker_llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-1784e2115de34c99984acfbbb8ed8dd8"),
)
worker_llm_with_tools = worker_llm.bind_tools(tools)

# ——— Evaluator LLM：MiMo（评估 Worker 输出是否达标）———
# 注意：MiMo 不支持 response_format json_schema，evaluator 函数用 prompt JSON + 手动解析
evaluator_llm = ChatOpenAI(
    model="mimo-v2.5-pro",
    base_url="https://api.xiaomimimo.com/v1",
    api_key=os.getenv("MIMO_API_KEY", "sk-ct6ct1y17ry3m9xh2rce3bbx68kbsqs19y326ym89hxw2k64"),
)
# 这里定义的输出大模型必须按EvaluatorOutput输出。调用evaluator_llm_with_output后
# with_structured_output这个方法会要求大模型强制按需要的格式化输出，
# 只有gpt有。其他大模型要考虑替代
evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

# ========================================================================
# Worker 节点：执行任务的 Agent
# ========================================================================
def worker(state: State) -> Dict[str, Any]:
    system_message = f"""You are a helpful assistant that can use tools to complete tasks.
You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.

IMPORTANT - Web Search Rules:
- When searching the web, use https://www.bing.com/
- Each tool call has a 10-second timeout, keep searches simple and fast

This is the success criteria:
{state['success_criteria']}
You should reply either with a question for the user about this assignment, or with your final response.
If you have a question for the user, you need to reply by clearly stating your question. An example might be:

Question: please clarify whether you want a summary or a detailed answer

If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
"""
    if state.get("feedback_on_work"):
        system_message += f"""
Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
Here is the feedback on why this was rejected:
{state['feedback_on_work']}
With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""

    # 注入/更新 SystemMessage（复制列表，避免修改 state）
    found_system_message = False
    messages = list(state["messages"])
    for i, message in enumerate(messages):
        if isinstance(message, SystemMessage):
            messages[i] = SystemMessage(content=system_message)
            found_system_message = True

    if not found_system_message:
        messages = [SystemMessage(content=system_message)] + messages

    print(f"🤖 Worker(DeepSeek) 推理中... (上下文 {len(messages)} 条消息)")
    response = worker_llm_with_tools.invoke(messages)

    # 打印 LLM 返回了什么
    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"   → LLM 决定调用工具")
    else:
        print(f"   → LLM 文本回复: {str(response.content)[:120]}...")
    return {"messages": [response]}


# ========================================================================
# Worker 路由器：判断 Worker 输出后该走 tools 还是 evaluator
# ========================================================================
def worker_router(state: State) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # 打印详细的工具调用信息
        print("\n" + "=" * 60)
        print(f"🔧 Worker(DeepSeek) 请求调用工具")
        for i, tc in enumerate(last_message.tool_calls):
            print(f"   工具 {i+1}: {tc.get('name', 'unknown')}")
            print(f"   参数: {tc.get('args', {})}")
        print("=" * 60 + "\n")
        return "tools"
    else:
        return "evaluator"


# ========================================================================
# 格式化对话历史（供 Evaluator 评估时查看）
# ========================================================================
def format_conversation(messages: List[Any]) -> str:
    conversation = "Conversation history:\n\n"
    for message in messages:
        if isinstance(message, HumanMessage):
            conversation += f"User: {message.content}\n"
        elif isinstance(message, AIMessage):
            text = message.content or "[Tools use]"
            conversation += f"Assistant: {text}\n"
    return conversation


# ========================================================================
# Evaluator 节点：评估 Worker 的输出是否达标
# ========================================================================
def evaluator(state: State) -> Dict[str, Any]:
    last_response = state["messages"][-1].content

    system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
and whether more input is needed from the user."""

    user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

The entire conversation with the assistant, with the user's original request and all replies, is:
{format_conversation(state['messages'])}

The success criteria for this assignment is:
{state['success_criteria']}

And the final response from the Assistant that you are evaluating is:
{last_response}

Respond with your feedback, and decide if the success criteria is met by this response.
Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.
"""
    if state["feedback_on_work"]:
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
    raw = evaluator_llm.invoke(evaluator_messages)
    print(raw.content)

    eval_result = evaluator_llm_with_output.invoke(evaluator_messages)
    return {
        "messages": [
            AIMessage(content=f"Evaluator Feedback on this answer: {eval_result.feedback}")
        ],
        "feedback_on_work": eval_result.feedback,
        "success_criteria_met": eval_result.success_criteria_met,
        "user_input_needed": eval_result.user_input_needed,
    }


# ========================================================================
# 评估结果路由器：达标或需用户输入 → 结束，否则 → 返回 Worker 重试
# ========================================================================
def route_based_on_evaluation(state: State) -> str:
    if state["success_criteria_met"] or state["user_input_needed"]:
        return "END"
    else:
        return "worker"


# ========================================================================
# 构建 Graph
# ========================================================================
def tool_logger(state: State) -> Dict[str, Any]:
    """打印工具执行结果（成功/失败）"""
    last_msg = state["messages"][-1]
    tool_name = getattr(last_msg, "name", "unknown_tool")
    content = str(last_msg.content)[:200]
    if "Error" in content or "Timeout" in content or "error" in content:
        print(f"❌ 工具 [{tool_name}] 执行失败: {content}")
    else:
        print(f"✅ 工具 [{tool_name}] 执行成功: {content}")
    return {}
# 用 State 初始化 Graph Builder
graph_builder = StateGraph(State)
# 添加4个节点
graph_builder.add_node("worker", worker)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_node("tool_logger", tool_logger)
graph_builder.add_node("evaluator", evaluator)
# 添加边
# worker → 条件路由（调工具 / 去评估）
# 这里是流程  worker处理-路由处理-两种结果调用工具或者进行评估
# 条件边使用add_conditional_edges
graph_builder.add_conditional_edges(
    "worker", worker_router,
    {"tools": "tools", "evaluator": "evaluator"}
)
# 工具执行完后 → 回到 tool_logger 继续
graph_builder.add_edge("tools", "tool_logger")
# tool_logger执行完后 → 回到 worker 继续
graph_builder.add_edge("tool_logger", "worker")
# evaluator → 条件路由（重试 / 结束）
graph_builder.add_conditional_edges(
    "evaluator", route_based_on_evaluation,
    {"worker": "worker", "END": END}
)
# 从 worker 开始
graph_builder.add_edge(START, "worker")

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)


# ========================================================================
# Gradio 回调函数（异步，与 notebook 一致）
# ========================================================================
def make_thread_id() -> str:
    return str(uuid.uuid4())


async def process_message(message: str, success_criteria: str,
                          history: list, thread_id: str) -> list:
    """接收消息 → LangGraph Worker+Evaluator 循环 → 返回完整对话历史

    关键设计（与 notebook 一致）：
    - async def → Gradio 在主线程事件循环中执行
    - await graph.ainvoke() → 异步调用，ToolNode 走 _arun()
    - async_browser → 所有 Playwright 操作绑定主线程，不跨线程
    - nest_asyncio → 允许 ToolNode 内部嵌套 run_until_complete
    """
    config = {"configurable": {"thread_id": thread_id}}

    state = {
        "messages": message,
        "success_criteria": success_criteria,
        "feedback_on_work": None,
        "success_criteria_met": False,
        "user_input_needed": False,
    }

    result = await graph.ainvoke(state, config=config)

    user = {"role": "user", "content": message}
    reply = {"role": "assistant", "content": result["messages"][-2].content}
    feedback = {"role": "assistant", "content": result["messages"][-1].content}

    return history + [user, reply, feedback]


async def reset():
    """重置会话：清空输入框和对话历史，生成新 thread_id"""
    return "", "", [], make_thread_id()


# ========================================================================
# Gradio 界面 & 启动入口
# ========================================================================
def build_ui():
    with gr.Blocks(title="Sidekick Personal Co-worker") as ui:
        gr.Markdown("## Sidekick Personal Co-worker")
        thread = gr.State(make_thread_id())

        with gr.Row():
            chatbot = gr.Chatbot(label="Sidekick", height=400)

        with gr.Group():
            with gr.Row():
                message = gr.Textbox(
                    show_label=False,
                    placeholder="Your request to your sidekick",
                    scale=3,
                )
                success_criteria = gr.Textbox(
                    show_label=False,
                    placeholder="Success criteria (e.g. 'Find top 3 AI news today')",
                    scale=2,
                )

        with gr.Row():
            go_button = gr.Button("Go!", variant="primary")
            reset_button = gr.Button("Reset", variant="stop")

        # 事件绑定
        msg_inputs = [message, success_criteria, chatbot, thread]
        msg_outputs = [chatbot]

        message.submit(process_message, msg_inputs, msg_outputs)
        success_criteria.submit(process_message, msg_inputs, msg_outputs)
        go_button.click(process_message, msg_inputs, msg_outputs)
        reset_button.click(reset, [], [message, success_criteria, chatbot, thread])

    return ui


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sidekick Personal Co-worker")
    parser.add_argument("--port", type=int, default=None,
                        help="Gradio server port (default: auto-detect free port)")
    parser.add_argument("--share", action="store_true",
                        help="Enable Gradio share link")
    args = parser.parse_args()

    # 自动检测空闲端口
    if args.port is None:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
    else:
        port = args.port

    print(f"\n{'='*50}")
    print(f"  Sidekick Personal Co-worker 启动中...")
    print(f"  Worker: DeepSeek | Evaluator: MiMo")
    print(f"  Port: {port}")
    print(f"{'='*50}\n")

    ui = build_ui()
    ui.launch(
        server_name="127.0.0.1",
        server_port=port,
        inbrowser=False,
        share=args.share,
        theme=gr.themes.Default(primary_hue="emerald"),
        show_error=True,
    )
