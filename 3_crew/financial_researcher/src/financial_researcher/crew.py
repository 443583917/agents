# src/financial_researcher/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
# 金融研究管线 agent
# 一个智能体编排框架要用好善用内部提供的工具
@CrewBase
class ResearchCrew():
    """Research crew for comprehensive topic analysis and reporting"""

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
            tools=[SerperDevTool()] 
            # 工具调用可以直接调用封装好的方法,不过有在.env文件中配好对应的key
            # 工具中添加正确的description,可以让智能体更好地理解工具的功能和使用场景,
            # 从而更有效地利用工具来完成任务
        )

    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['analyst'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task']
        )

    @task
    # 如果一个任务需要基于上个任务的输出完成,配置context指向上个task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],
            output_file='output/report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )