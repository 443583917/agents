# ============================================================
# CrewAI 核心类导入
#   Agent   → 定义一个 AI 智能体（角色、目标、工具）
#   Crew    → 将 Agent 和 Task 组装成可执行的团队
#   Process → 执行模式：Process.sequential（串行）或 Process.hierarchical（层级委派）
#   Task    → 定义一个具体的工作任务
# ============================================================
from crewai import Agent, Crew, Process, Task

# ============================================================
# CrewAI 装饰器 + 基类导入
#   CrewBase → 类装饰器：将 Python 类标记为 Crew 项目入口，负责加载 YAML 配置、收集子组件
#   agent    → 方法装饰器：标记方法为 Agent 工厂，返回值自动加入 self.agents 列表
#   crew     → 方法装饰器：标记方法为 Crew 组装入口（每个类只能有一个）
#   task     → 方法装饰器：标记方法为 Task 工厂，返回值自动加入 self.tasks 列表
# ============================================================
from crewai.project import CrewBase, agent, crew, task

# BaseAgent: Agent 的类型基类，用于 agents 列表的类型注解
from crewai.agents.agent_builder.base_agent import BaseAgent

# List: 类型注解中声明 agents 和 tasks 列表
from typing import List

# ============================================================
# 可选的生命周期装饰器：
#   @before_kickoff → Crew 启动前执行的钩子
#   @after_kickoff  → Crew 完成后执行的钩子
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators
# ============================================================


# ============================================================
# @CrewBase — 类装饰器，将 DemoCrew 类注册为 CrewAI 项目入口
# 它做了三件事：
#   1. 加载 agents_config / tasks_config 指向的 YAML 配置文件
#   2. 扫描类中所有 @agent / @task 装饰的方法，收集返回值到 self.agents / self.tasks
#   3. 使类能被 crewai CLI 命令（如 crewai run）自动发现和执行
# ============================================================
@CrewBase
class DemoCrew():
    """DemoCrew crew — 多智能体研究团队

    团队组成：
    - researcher（研究员）：负责收集和整理信息
    - reporting_analyst（报告分析员）：负责将信息撰写成结构化报告
    """

    # agents: Agent 实例列表，由 @agent 装饰器自动填充
    #   → @agent 装饰的方法返回值会自动加入这个列表
    agents: List[BaseAgent]

    # tasks: Task 实例列表，由 @task 装饰器自动填充
    #   → @task 装饰的方法返回值会自动加入这个列表
    tasks: List[Task]

    # ============================================================
    # Agent 配置说明：
    #   推荐使用 YAML 配置（config/agents.yaml），每个 Agent 在 YAML 中定义一个
    #   独立的配置段（key），包含 role（角色）、goal（目标）、backstory（背景故事）
    #   YAML 配置文档：https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    #
    # 工具挂载：
    #   通过 tools= 参数为 Agent 绑定工具，使其能执行具体操作（读文件、调 API 等）
    #   https://docs.crewai.com/concepts/agents#agent-tools
    # ============================================================

    # @agent — 方法装饰器
    # 将 researcher() 标记为 Agent 工厂方法。CrewBase 会自动调用它，
    # 把返回的 Agent 对象加入 self.agents 列表（供 @crew 方法使用）
    @agent
    def researcher(self) -> Agent:
        """定义名为 'researcher' 的 Agent — 高级数据研究员

        职责：根据给定的 {topic} 主题，研究并收集该领域的
        最新发展动态和前沿信息。
        """
        return Agent(
            # config: 从 YAML 文件中 key='researcher' 的配置段读取 role/goal/backstory
            # self.agents_config 返回配置字典，['researcher'] 取该 Agent 的配置
            config=self.agents_config['researcher'],  # type: ignore[index]

            # verbose=True: 打印 Agent 的思考过程和执行日志，方便调试和观察
            verbose=True
        )

    # @agent — 方法装饰器
    # 将 reporting_analyst() 标记为 Agent 工厂方法
    @agent
    def reporting_analyst(self) -> Agent:
        """定义名为 'reporting_analyst' 的 Agent — 报告分析员

        职责：根据 researcher 收集的研究数据和发现，
        创建详细、结构化、易读的报告。
        """
        return Agent(
            # config: 从 YAML 文件中 key='reporting_analyst' 的配置段读取
            config=self.agents_config['reporting_analyst'],  # type: ignore[index]

            # verbose=True: 打印 Agent 的思考过程和执行日志
            verbose=True
        )

    # ============================================================
    # Task 配置说明：
    #   推荐使用 YAML 配置（config/tasks.yaml），每个 Task 在 YAML 中定义一个
    #   独立的配置段（key），包含 description（任务描述）、expected_output（预期输出）、
    #   agent（由哪个 Agent 执行）
    #
    # 更多概念：
    #   - 结构化输出：让 Task 产出 JSON 而非纯文本
    #   - 任务依赖：通过 context= 参数串联上下游 Task
    #   - 任务回调：在 Task 执行前后插入自定义逻辑
    #   https://docs.crewai.com/concepts/tasks#overview-of-a-task
    # ============================================================

    # @task — 方法装饰器
    # 将 research_task() 标记为 Task 工厂方法。CrewBase 会自动调用它，
    # 把返回的 Task 对象加入 self.tasks 列表（供 @crew 方法使用）
    @task
    def research_task(self) -> Task:
        """定义名为 'research_task' 的任务 — 执行研究

        这是流水线的第一步：由 researcher Agent 对 {topic} 进行
        全面研究，输出 10 条关键发现。
        """
        return Task(
            # config: 从 YAML 文件中 key='research_task' 的配置段读取
            # 包含 description（做什么）、expected_output（输出什么格式）
            config=self.tasks_config['research_task'],  # type: ignore[index]
        )

    # @task — 方法装饰器
    # 将 reporting_task() 标记为 Task 工厂方法
    @task
    def reporting_task(self) -> Task:
        """定义名为 'reporting_task' 的任务 — 撰写报告

        这是流水线的第二步：由 reporting_analyst Agent 将 research_task
        的研究结果扩展成完整的 Markdown 报告，并保存为文件。
        """
        return Task(
            # config: 从 YAML 文件中 key='reporting_task' 的配置段读取
            config=self.tasks_config['reporting_task'],  # type: ignore[index]

            # output_file: 将 Task 的输出写入指定文件
            # 这里将报告保存为 report.md（Markdown 格式）
            output_file='report.md'
        )

    # ============================================================
    # @crew — 方法装饰器
    # 将 crew() 标记为 Crew 组装方法。这是整个团队的"总装线"，
    # 负责把前面收集的 Agent 和 Task 组合成一个可执行的 Crew 对象。
    # 每个 @CrewBase 类必须有且仅有一个 @crew 方法。
    # ============================================================
    @crew
    def crew(self) -> Crew:
        """组装并返回 DemoCrew — Agent + Task + 执行模式

        Crew 执行流程：
        1. researcher Agent 执行 research_task
           在 {topic} 主题下收集信息，输出 10 条关键发现
        2. reporting_analyst Agent 读取 research_task 的输出
           将其扩展为完整报告，保存为 report.md
        """
        return Crew(
            # agents: 自动收集所有 @agent 方法的返回值（即 Agent 实例列表）
            # 这里 self.agents = [researcher(), reporting_analyst()]
            agents=self.agents,

            # tasks: 自动收集所有 @task 方法的返回值（即 Task 实例列表）
            # 这里 self.tasks = [research_task(), reporting_task()]
            # 执行顺序 = 方法在类中的定义顺序（research_task → reporting_task）
            tasks=self.tasks,

            # process: 指定执行模式
            #   Process.sequential   → 串行流水线（按 @task 定义顺序逐个执行）
            #   Process.hierarchical → 层级委派（由一个管理 Agent 自动分配任务给其他 Agent）
            #   层级模式文档：https://docs.crewai.com/how-to/Hierarchical/
            process=Process.sequential,

            # verbose=True: 打印 Crew 执行过程的详细日志
            verbose=True,
        )

    # ============================================================
    # 知识源集成（可选）：
    #   CrewAI 支持将外部知识（文本文件、PDF、数据库等）注入到
    #   Agent 的上下文中，让 Agent 基于特定领域知识工作
    #   https://docs.crewai.com/concepts/knowledge#what-is-knowledge
    # ============================================================
