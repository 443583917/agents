from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# 如何设计一个agent?
# 1.先考虑角色组成这个辩论系统一个有3个角色正方，反方，法官。
# 2.为每个角色设计任务
# 3.编排流程让agent按照流程执行任务
# 4.流程是怎么执行的？是按任务执行的,每个任务会指定由哪个agent来执行，执行完了之后再执行下一个任务
# 5.每个agent是怎么执行任务的？agent会根据任务的描述
@CrewBase
class Debate():
    """Debate crew"""


    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def debater(self) -> Agent:
        return Agent(
            config=self.agents_config['debater'],
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'],
            verbose=True
        )

    @task
    def propose(self) -> Task:
        return Task(
            config=self.tasks_config['propose'],
        )

    @task
    def oppose(self) -> Task:
        return Task(
            config=self.tasks_config['oppose'],
        )

    @task
    def decide(self) -> Task:
        return Task(
            config=self.tasks_config['decide'],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Debate crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
