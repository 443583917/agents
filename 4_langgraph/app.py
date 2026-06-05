"""
Sidekick Personal Co-Worker — 基于 Gradio 的 Web 聊天界面
==========================================================
该模块使用 Gradio 构建一个网页聊天应用，后端由 Sidekick（基于 LangGraph 的
智能助手）驱动。用户输入消息和成功标准后，Sidekick 会调用工具执行多步推理。

主要组件：
  - setup(): 初始化 Sidekick 实例
  - process_message(): 核心处理函数，接收消息并运行 superstep
  - reset(): 重置会话，创建全新的 Sidekick
  - free_resources(): 清理资源的回调
  - Gradio UI：包含聊天框、输入框、成功标准输入和按钮
"""

import gradio as gr
from sidekick import Sidekick


async def setup():
    """
    异步初始化 Sidekick 实例并执行 setup 流程。

    在页面加载时调用（ui.load 事件），创建一个新的 Sidekick 对象，
    执行异步初始化（如加载模型、建立连接等）。

    Returns:
        Sidekick: 已初始化完成的 Sidekick 实例
    """
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    """
    处理用户消息的核心异步函数。

    接收用户输入、成功标准和对话历史，调用 Sidekick 的 run_superstep
    方法执行一步推理操作（可能涉及多轮工具调用）。

    Args:
        sidekick (Sidekick): 当前的 Sidekick 实例（通过 gr.State 维护状态）
        message (str): 用户输入的消息/请求
        success_criteria (str): 用户定义的成功标准，用于判断任务是否完成
        history (list): 对话历史记录，Gradio Chatbot 的 messages 格式

    Returns:
        tuple: (results, sidekick)
            - results (dict): superstep 的执行结果字典
            - sidekick (Sidekick): 更新后的 Sidekick 实例（状态可能已变化）
    """
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset():
    """
    重置会话状态，创建一个全新的 Sidekick 实例。

    当用户点击 Reset 按钮时触发，清空所有输入和对话历史，
    并初始化一个新的 Sidekick 对象。

    Returns:
        tuple: ("", "", None, new_sidekick)
            - 空字符串清空 message 输入框
            - 空字符串清空 success_criteria 输入框
            - None 清空 chatbot 对话历史
            - new_sidekick 为全新的 Sidekick 实例
    """
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick


def free_resources(sidekick):
    """
    Gradio State 的 delete_callback，用于释放 Sidekick 占用的资源。

    当 gradio.State 被销毁（如会话结束、页面刷新）时自动调用，
    尝试调用 Sidekick 的 cleanup() 方法释放模型、连接等资源。

    Args:
        sidekick (Sidekick | None): 当前持有的 Sidekick 实例，可能为 None
    """
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


# ============================================================================
# Gradio UI 构建
# ============================================================================
with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    # 页面标题
    gr.Markdown("## Sidekick Personal Co-Worker")

    # 全局状态：存储 Sidekick 实例，页面刷新/关闭时触发 free_resources 清理
    sidekick = gr.State(delete_callback=free_resources)

    # 聊天框 - 显示对话历史
    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")

    # 输入区域
    with gr.Group():
        with gr.Row():
            # 用户请求输入框
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            # 成功标准输入框 - 告诉 Sidekick 什么才算完成任务
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success critiera?"
            )

    # 操作按钮行
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")   # 红色停止样式
        go_button = gr.Button("Go!", variant="primary")      # 主色调按钮

    # ========================================================================
    # 事件绑定
    # ========================================================================

    # 页面加载时：调用 setup() 初始化 Sidekick，结果存入 gr.State
    ui.load(setup, [], [sidekick])

    # 在 message 输入框中按回车：触发 process_message
    message.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )

    # 在 success_criteria 输入框中按回车：同样触发 process_message
    success_criteria.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )

    # 点击 Go! 按钮：触发 process_message
    go_button.click(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )

    # 点击 Reset 按钮：清空所有输入和对话，创建新的 Sidekick
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])


# 启动 Gradio 应用（自动在浏览器中打开）
ui.launch(inbrowser=True)
