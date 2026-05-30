# 标准库导入 — 读取系统环境变量（如 .env 文件中的 API Key）
import os

# CrewAI 核心类导入
#   Agent   → 定义一个 AI 智能体（角色、目标、工具）
#   Crew    → 将 Agent 和 Task 组装成可执行的团队
#   LLM     → 显式创建大语言模型实例，用于连接不同模型服务商
#   Process → 执行模式枚举：Process.sequential（串行）或 Process.hierarchical（层级委派）
#   Task    → 定义一个具体的工作任务
from crewai import Agent, Crew, LLM, Process, Task

# CrewAI 装饰器 + 基类导入
#   CrewBase → 类装饰器：将 Python 类标记为 Crew 项目入口，负责加载 YAML 配置、收集子组件
#   agent    → 方法装饰器：标记方法为 Agent 工厂，返回值自动加入 self.agents 列表
#   crew     → 方法装饰器：标记方法为 Crew 组装入口（每个类只能有一个）
#   task     → 方法装饰器：标记方法为 Task 工厂，返回值自动加入 self.tasks 列表
from crewai.project import CrewBase, agent, crew, task

from coder.tools.custom_tool import MyCustomTool
# ============================================================
# 模型配置 — 通过 .env 文件切换不同模型服务商
#
# .env 文件示例（DeepSeek）:
#   OPENAI_API_KEY=sk-your-key        # 你的 API 密钥
#   OPENAI_BASE_URL=https://api.deepseek.com  # API 服务地址
#   OPENAI_MODEL=openai/deepseek-chat  # 模型名称（可选，可在 YAML 中覆盖）
#
# 切换其他模型只需改 .env：
#   通义千问: BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  MODEL=openai/qwen-plus
#   GPT-4o:   BASE_URL=（不设，用默认 OpenAI 地址）     MODEL=openai/gpt-4o
# ============================================================

def create_llm(model: str | None = None):
    """创建 LLM（大语言模型）实例，自动从 .env 读取 API 地址和密钥。

    参数:
        model: 模型名称，如 "openai/deepseek-chat"。传 None 时从环境变量 OPENAI_MODEL 读取。

    返回:
        LLM 实例，可直接传给 Agent(llm=...) 参数。
    """
    return LLM(
        # 模型名称：优先用传入参数，其次读环境变量 OPENAI_MODEL，默认 deepseek-chat
        model=model or os.getenv("OPENAI_MODEL", "openai/deepseek-chat"),
        # API 密钥：从 .env 的 OPENAI_API_KEY 读取
        api_key=os.getenv("OPENAI_API_KEY"),
        # API 地址：从 .env 的 OPENAI_BASE_URL 读取（决定了请求发给 OpenAI / DeepSeek / 通义千问...）
        base_url=os.getenv("OPENAI_BASE_URL"),
    )


# @CrewBase — 类装饰器，将 Coder 类注册为 CrewAI 项目入口
# 它做了三件事：
#   1. 加载 agents_config / tasks_config 指向的 YAML 配置文件
#   2. 扫描类中所有 @agent / @task 装饰的方法，收集返回值到 self.agents / self.tasks
#   3. 使类能被 crewai CLI 命令（如 crewai run）自动发现和执行
@CrewBase
class Coder():
    """Coder crew — 编程助手团队"""

    # agents_config: Agent 的 YAML 配置文件路径（相对于 src/coder/）
    # YAML 中定义每个 Agent 的 role（角色）、goal（目标）、backstory（背景）、llm（模型）
    agents_config = 'config/agents.yaml'

    # tasks_config: Task 的 YAML 配置文件路径（相对于 src/coder/）
    # YAML 中定义每个 Task 的 description（描述）、expected_output（预期输出）、agent（由谁执行）
    tasks_config = 'config/tasks.yaml'

    # @agent — 方法装饰器
    # 将 coder() 标记为 Agent 工厂方法。CrewBase 会自动调用它，
    # 把返回的 Agent 对象加入 self.agents 列表（供 @crew 方法使用）
    @agent
    def coder(self) -> Agent:
        """定义名为 'coder' 的 Agent — Python 开发者角色"""
        return Agent(
            # config: 从 YAML 文件中 key='coder' 的配置段读取 role/goal/backstory
            # 注意: self.agents_config 返回字典，['coder'] 取 'coder' 这个 Agent 的配置
            config=self.agents_config['coder'],

            # llm: 显式指定该 Agent 使用的大语言模型
            # 优先级: 代码中的 llm= > YAML 中的 llm: 字段 > .env 的默认值
            llm=create_llm(),

            # verbose=True: 打印 Agent 的思考过程和执行日志，方便调试
            verbose=True,
            # 如果用工具agent，就在这里添加工具列表，示例代码没有用到
            tools=[MyCustomTool()],
            # allow_code_execution=True: 允许 Agent 编写并执行代码
            allow_code_execution=True,

            # code_execution_mode: 代码运行方式
            #   "safe"   → 在 Docker 容器中隔离执行（需安装 Docker Desktop）
            #   "unsafe" → 直接在本地环境执行（仅用于可信任的代码）
            code_execution_mode="unsafe",  # safe=Docker 隔离 / unsafe=本地

            # max_execution_time: 代码最长运行时间（秒），超时会终止
            max_execution_time=30,

            # max_retry_limit: 任务失败后的最大重试次数
            max_retry_limit=3
        )

    # @task — 方法装饰器
    # 将 coding_task() 标记为 Task 工厂方法。CrewBase 会自动调用它，
    # 把返回的 Task 对象加入 self.tasks 列表（供 @crew 方法使用）
    @task
    def coding_task(self) -> Task:
        """定义名为 'coding_task' 的任务 — 编写代码并执行"""
        return Task(
            # config: 从 YAML 文件中 key='coding_task' 的配置段读取任务描述
            # 包含 description（任务内容）、expected_output（预期产出）、agent（谁来做）
            config=self.tasks_config['coding_task'],
        )

    # @crew — 方法装饰器
    # 将 crew() 标记为 Crew 组装方法。这是整个团队的"总装线"，
    # 负责把前面收集的 Agent 和 Task 组合成一个可执行的 Crew 对象。
    # 每个 @CrewBase 类必须有且仅有一个 @crew 方法。
    @crew
    def crew(self) -> Crew:
        """组装并返回 Coder Crew — Agent + Task + 执行模式"""
        return Crew(
            # agents: 自动收集所有 @agent 方法的返回值（即 Agent 实例列表）
            # 这里 self.agents = [coder() 返回的 Agent]
            agents=self.agents,

            # tasks: 自动收集所有 @task 方法的返回值（即 Task 实例列表）
            # 这里 self.tasks = [coding_task() 返回的 Task]
            tasks=self.tasks,

            # process: 指定执行模式
            #   Process.sequential   → 串行流水线（按 @task 定义顺序逐个执行）
            #   Process.hierarchical → 层级委派（由一个管理 Agent 自动分配任务给其他 Agent）
            process=Process.sequential,

            # verbose=True: 打印 Crew 执行过程的详细日志
            verbose=True,
        )
