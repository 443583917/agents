import os
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, trace, function_tool
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
import resend
import asyncio
import sys

load_dotenv(override=True)

# ============================================================
# DeepSeek 模型配置
# ============================================================
deepseek_client = AsyncOpenAI(
    api_key="sk-1784e2115de34c99984acfbbb8ed8dd8",
    base_url="https://api.deepseek.com"
)
deepseek_model = OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=deepseek_client
)

# ============================================================
# 3个销售 Agent — 不同风格
# ============================================================
instructions1 = "You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails."

instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

instructions3 = "You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."

sales_agent1 = Agent(name="Professional Sales Agent", instructions=instructions1, model=deepseek_model)
sales_agent2 = Agent(name="Engaging Sales Agent", instructions=instructions2, model=deepseek_model)
sales_agent3 = Agent(name="Busy Sales Agent", instructions=instructions3, model=deepseek_model)

# ============================================================
# 工具函数 — Resend 发送 HTML 邮件
# ============================================================
@function_tool
def send_html_email(subject: str, html_body: str):
    # """ 发送带主题和 HTML 正文的邮件 """ 定义函数用途，
    # 大模型从这段文本理解这个函数是干什么的，以及如何使用它，
    # 不需要像之前定义一个函数描述json
    """ 发送带主题和 HTML 正文的邮件 """
    resend.api_key = 're_QTqQh9Yx_6ceG31HmFphEhpSncDhgBrZh'
    params = {
        'from': 'zzh@ztest.online',
        'to': ['443583917@qq.com'],
        'subject': subject,
        'html': html_body,
    }
    r = resend.Emails.send(params)
    return {"status": "success", "id": r.get("id")}

# ============================================================
# 辅助 Agent — 写标题 + 转HTML
# ============================================================
subject_writer = Agent(
    name="Email subject writer",
    instructions="You can write a subject for a cold sales email. \
You are given a message and you need to write a subject for an email that is likely to get a response.",
    model=deepseek_model
)
subject_tool = subject_writer.as_tool(
    tool_name="subject_writer",
    tool_description="Write a subject for a cold sales email"
)

html_converter = Agent(
    name="HTML email body converter",
    instructions="You can convert a text email body to an HTML email body. \
You are given a text email body which might have some markdown \
and you need to convert it to an HTML email body with simple, clear, compelling layout and design.",
    model=deepseek_model
)
html_tool = html_converter.as_tool(
    tool_name="html_converter",
    tool_description="Convert a text email body to an HTML email body"
)

# ============================================================
# Email Manager — 收到底稿后：写标题 → 转HTML → 发送
# ============================================================
emailer_agent = Agent(
    name="Email Manager",
    instructions="You are an email formatter and sender. You receive the body of an email to be sent. \
You first use the subject_writer tool to write a subject for the email, then use the html_converter tool to convert the body to HTML. \
Finally, you use the send_html_email tool to send the email with the subject and HTML body.",
    tools=[subject_tool, html_tool, send_html_email],
    model=deepseek_model,
    handoff_description="Convert an email to HTML and send it"
)

# ============================================================
# 3个销售 Agent 转为工具 — Sales Manager 可以调用它们写邮件
# ============================================================
description = "Write a cold sales email"
tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)
tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description)

# ============================================================
# Sales Manager — 调3个销售写邮件 → 挑最好的 → 交接给 Email Manager
# ============================================================
sales_manager_instructions = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.

Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.

2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
You can use the tools multiple times if you're not satisfied with the results from the first try.

3. Handoff for Sending: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will take care of formatting and sending.

Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must hand off exactly ONE email to the Email Manager — never more than one.
"""

sales_manager = Agent(
    name="Sales Manager",
    instructions=sales_manager_instructions,
    tools=[tool1, tool2, tool3],
    handoffs=[emailer_agent],
    model=deepseek_model
)

# ============================================================
# 执行
# ============================================================
async def main():
    message = "Send out a cold sales email addressed to Dear CEO from Alice"
    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)
    print(f"\n\n{'='*60}")
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"Final output:\n{result.final_output}")

asyncio.run(main())
