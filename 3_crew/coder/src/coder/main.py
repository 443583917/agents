#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from coder.crew import Coder
# 优化输出格式
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)
# 输入要完成的任务
assignment = 'Write a python program to calculate the first 10,000 terms \
    of this series, multiplying the total by 4: 1 - 1/3 + 1/5 - 1/7 + ...'

def run():
    """
    Run the crew.
    """
    inputs = {
        'assignment': assignment,
    }
    # 多个任务用循环执行
    # from coder.crew import Coder  还是由 crew.py 
    # 定义的 Coder 类负责执行任务
    # 一个crew可以执行很多不同的任务，
    # 针对每次请求可以先做一个意图分析的agent，
    # 分析完了之后再调用不同的工具来完成任务
    result = Coder().crew().kickoff(inputs=inputs)
    print(result.raw)

# 训练和测试函数，供 CLI 命令调用
def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        Coder().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Coder().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    
    try:
        Coder().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


