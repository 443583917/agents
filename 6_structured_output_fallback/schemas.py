"""
共享 Pydantic Schema — 结构化输出的类型定义

复用 LangGraph Lab4 的 EvaluatorOutput 和 AutoGen Lab2 的 ImageDescription，
作为结构化输出适配器的示例目标格式。
"""

from typing import Literal
from pydantic import BaseModel, Field


class EvaluatorOutput(BaseModel):
    """评估器输出：对 Agent 回复的评估结果

    来源：4_langgraph/4_lab4.py
    用途：Worker ↔ Evaluator 多 Agent 循环中的评估反馈
    """
    feedback: str = Field(
        description="Feedback on the assistant's response"
    )
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, "
                    "or clarifications, or the assistant is stuck"
    )


class ImageDescription(BaseModel):
    """图片描述结构化输出

    来源：5_autogen/2_lab2_autogen_agentchat.ipynb
    用途：Agent 生成图片提示词时的结构化描述
    """
    scene: str = Field(
        description="A detailed description of the scene in the image"
    )
    message: str = Field(
        description="The main message or story the image conveys"
    )
    style: str = Field(
        description="The artistic style of the image (e.g. photorealistic, cartoon, watercolor)"
    )
    orientation: Literal["portrait", "landscape", "square"] = Field(
        description="The orientation of the image"
    )
