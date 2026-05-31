# ============================================================
# CrewAI 自定义工具模板
#
# 工具（Tool）是 Agent 的"手"——让 Agent 不只停留在生成文字，
# 还能执行实际操作：读文件、查数据库、调 API、运行代码……
#
# 结构（三段式）：
#   1. Input Schema（Pydantic）  → 定义工具的输入参数格式
#   2. Tool Class（继承 BaseTool）→ 定义工具的元信息和执行逻辑
#   3. _run() 方法              → 工具被调用时实际执行的代码
# ============================================================

# BaseTool: CrewAI 提供的工具基类，所有自定义工具必须继承它
from crewai.tools import BaseTool

# Type: 类型注解辅助（Pydantic 要求 args_schema 字段标注 Type[BaseModel]）
from typing import Type

# BaseModel: Pydantic 基类，用于定义输入参数的 Schema（结构校验）
# Field:     Pydantic 字段描述器，给每个参数添加说明和约束
from pydantic import BaseModel, Field


# ============================================================
# 第一步：定义输入 Schema
# 告诉 Agent "调用这个工具时需要传什么参数"
#
# Agent 在决定使用工具时，会看到这个 Schema 中定义的参数列表
# 和每个参数的 description，从而准确地传递参数
# ============================================================

class MyCustomToolInput(BaseModel):
    """定义工具的输入参数格式 — Agent 会看到这个 Schema 来决定如何传参"""

    # argument: 一个必填的字符串参数
    #   ...           → 省略号表示这是必填参数（无默认值，不传会报错）
    #   description=  → 告诉 Agent 这个参数的用途，Agent 读了这个就知道传什么
    argument: str = Field(..., description="Description of the argument.")


# ============================================================
# 第二步：定义工具类
# 继承 BaseTool，设置工具的名称、描述、输入格式
#
# 每个属性的作用：
#   name        → Agent 用它来识别和选择工具（显示在工具列表中）
#   description → Agent 根据这段文字决定"什么时候该用这个工具"
#                 必须写清楚：工具做什么、什么情况下用、返回什么
#   args_schema → 绑定第一步定义的输入 Schema 类
#                 CrewAI 会用这个 Schema 自动校验 Agent 传入的参数
# ============================================================

class MyCustomTool(BaseTool):
    """自定义工具 — Agent 可以调用它来执行具体操作"""

    # name: 工具名称（Agent 用它来识别和选择工具）
    name: str = "Name of my tool"

    # description: 工具的用途说明
    #   关键：Agent 根据 description 判断"什么时候该用这个工具"
    #   所以要写清楚触发条件、工具功能、返回内容
    description: str = (
        "Clear description for what this tool is useful for, "
        "your agent will need this information to use it."
    )

    # args_schema: 绑定第一步定义的输入 Schema 类
    #   Type[BaseModel] 类型注解告诉 Pydantic/CrewAI 这是一个 Schema 类
    #   CrewAI 会用这个 Schema 自动校验 Agent 传入的参数格式
    args_schema: Type[BaseModel] = MyCustomToolInput

    # ============================================================
    # 第三步：实现 _run() 方法
    # 这是工具真正执行的代码，Agent 调用工具时实际运行的就是这个
    #
    # 参数说明：
    #   argument 对应 MyCustomToolInput 中定义的必填字段
    #   CrewAI 会自动把 Agent 传入的参数映射到这里
    #
    # 返回说明：
    #   返回 str 类型的执行结果，会返回给 Agent 供其继续推理
    # ============================================================

    def _run(self, argument: str) -> str:
        """工具的核也执行逻辑

        参数:
            argument: 对应 MyCustomToolInput 中定义的必填字段
                      CrewAI 会自动把 Agent 传入的参数映射到这里

        返回:
            str 类型的执行结果，会返回给 Agent 供其继续推理
        """
        # 在此编写你的实际逻辑：
        #   读文件   → with open(...) as f: return f.read()
        #   调 API   → requests.get(...)
        #   查数据库 → db.query(...)
        #   执行代码 → subprocess.run(...)

        # 当前是示例实现：返回一个占位输出，告诉 Agent 忽略并继续
        return "this is an example of a tool output, ignore it and move along."
