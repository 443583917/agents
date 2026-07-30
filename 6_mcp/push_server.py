"""
push_server.py - 推送通知 MCP 服务器

本文件创建一个 MCP 服务器，提供发送推送通知的功能。
使用 Pushover 服务将通知推送到手机/桌面设备。

应用场景：交易员完成交易后，通过此服务器发送交易摘要通知。

运行方式：uv run push_server.py
"""

import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

# Pushover 服务配置 - 用于发送推送通知
# 需要在 .env 中配置 PUSHOVER_USER 和 PUSHOVER_TOKEN
pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

# 创建 MCP 服务器实例
mcp = FastMCP("push_server")


class PushModelArgs(BaseModel):
    """推送通知的参数模型。
    使用 Pydantic 定义参数结构和描述，MCP 框架会自动生成 JSON Schema。
    """
    message: str = Field(description="A brief message to push")


@mcp.tool()
def push(args: PushModelArgs):
    """Send a push notification with this brief message.

    Args:
        args: 包含 message 字段的参数对象
    """
    print(f"Push: {args.message}")
    # 调用 Pushover API 发送推送通知
    payload = {"user": pushover_user, "token": pushover_token, "message": args.message}
    requests.post(pushover_url, data=payload)
    return "Push notification sent"


if __name__ == "__main__":
    mcp.run(transport="stdio")
