from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import requests

# 定义调用工具时需要的输入格式。这是固定写法
class PushNotification(BaseModel):
    """A message to be sent to the user"""
    message: str = Field(..., description="The message to be sent to the user.")

# 推送服务的工具推送到手机
class PushNotificationTool(BaseTool):
    
    # 推送的内容由task中决定。
    # 写在pick_best_company的description中
    # Send a push notification to the user with the decision and 1 sentence rationale.
    # 模型是思考循环结构的。对于description可能会拆分成不同的task。在task中就完成工具的调用
    name: str = "Send a Push Notification"
    description: str = (
        "This tool is used to send a push notification to the user."
    )
    # args_schema 参数校验器，
    # 规定了工具需要什么样的输入，这里是一个PushNotification对象，包含一个message字段
    args_schema: Type[BaseModel] = PushNotification

    def _run(self, message: str) -> str:
        pushover_user = os.getenv("PUSHOVER_USER")
        pushover_token = os.getenv("PUSHOVER_TOKEN")
        pushover_url = "https://api.pushover.net/1/messages.json"

        print(f"Push: {message}")
        payload = {"user": pushover_user, "token": pushover_token, "message": message}
        requests.post(pushover_url, data=payload)
        return '{"notification": "ok"}'