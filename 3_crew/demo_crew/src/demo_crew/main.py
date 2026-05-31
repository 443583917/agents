#!/usr/bin/env python
# ============================================================
# 程序入口文件 — main.py
# 这是整个 CrewAI 项目的启动入口，负责：
#   1. 配置运行环境（过滤警告、创建输出目录）
#   2. 定义传给 Agent 的输入变量
#   3. 提供四个 CLI 命令：run / train / replay / test
#
# CLI 命令由 pyproject.toml 中的 [project.scripts] 段注册
# 例如：train = "demo_crew.main:train"  → 运行 python -m demo_crew.main train
# ============================================================

# 系统模块：
#   sys      → 读取命令行参数 (sys.argv)
#   warnings → 过滤第三方库的警告
import sys
import warnings

# datetime: 获取当前年份，自动注入到 inputs 中供模板变量 {current_year} 使用
from datetime import datetime

# DemoCrew: 从 crew.py 导入组装好的 Crew 类
from demo_crew.crew import DemoCrew

# ============================================================
# 优化输出格式
# 过滤 pysbd 模块的 SyntaxWarning（句子边界检测库的已知问题）
# 避免运行时控制台输出无关警告影响阅读体验
# ============================================================
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crew.
    正式执行任务 — 最常用的命令
    构建 inputs 字典（包含 topic 和 current_year），
    将变量注入 YAML 模板后启动 Crew。
    """
    inputs = {
        # topic: 研究主题，对应 YAML 中的 {topic} 占位符
        'topic': 'AI LLMs',

        # current_year: 当前年份，对应 YAML 中的 {current_year} 占位符
        # 自动从系统时间获取年份，无需手动更新
        'current_year': str(datetime.now().year)
    }

    try:
        # 实例化 Crew → 组装 Agent + Task → kickoff 启动执行
        DemoCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    训练模式 — 对 Crew 进行多轮训练以优化表现

    命令行参数：
        sys.argv[1]  → n_iterations（迭代次数，如 10）
        sys.argv[2]  → filename（训练数据保存路径，如 training_data.pkl）

    调用示例：
        crewai train 10 training_data.pkl
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        # train() 接受迭代次数、保存文件名和输入参数
        DemoCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    回放模式 — 按 task_id 重放某次历史执行中的特定任务
    适用场景：想观察某个 Task 的执行详过程，而不需要完整重跑整个 Crew

    命令行参数：
        sys.argv[1]  → task_id（要回放的任务 ID）

    调用示例：
        crewai replay <task_id>
    """
    try:
        # replay() 通过 task_id 精准回放某个已执行过的 Task
        DemoCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    测试模式 — 用评估 LLM 对 Crew 执行结果进行打分评估
    与 train() 的区别：train 产生训练数据用于改进模型，
    test 是用外部评估模型来评分当前 Crew 的表现

    命令行参数：
        sys.argv[1]  → n_iterations（测试迭代次数，如 5）
        sys.argv[2]  → eval_llm（用于评估的 LLM 名称，如 openai/gpt-4o）

    调用示例：
        crewai test 5 openai/gpt-4o
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        # test() 接受迭代次数、评估模型名称和输入参数
        DemoCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
