from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List
from .tools.push_tool import PushNotificationTool
from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
# 股票分析系统
# 定义模型输出数据结构,定义需要的需要的数据，以及是那些数据
class TrendingCompany(BaseModel):
    """ A company that is in the news and attracting attention """
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    reason: str = Field(description="Reason this company is trending in the news")
# 热门公司列表
class TrendingCompanyList(BaseModel):
    """ List of multiple trending companies that are in the news """
    companies: List[TrendingCompany] = Field(description="List of companies trending in the news")
# 热门公司研究
class TrendingCompanyResearch(BaseModel):
    """ Detailed research on a company """
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")
# 热门公司研究列表
class TrendingCompanyResearchList(BaseModel):
    """ A list of detailed research on all the companies """
    research_list: List[TrendingCompanyResearch] = Field(description="Comprehensive research on all trending companies")


@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    # 公司搜索
    def trending_company_finder(self) -> Agent:
        return Agent(config=self.agents_config['trending_company_finder'],
                     tools=[SerperDevTool()], memory=True)#memory=True 跨会话记忆，已经搜索过的公司，下次就不需要再搜索了
    
    @agent
    # 财务研究
    def financial_researcher(self) -> Agent:
        return Agent(config=self.agents_config['financial_researcher'], 
                     tools=[SerperDevTool()])

    @agent
    # 股票选择
    def stock_picker(self) -> Agent:
        return Agent(config=self.agents_config['stock_picker'], 
                     tools=[PushNotificationTool()], memory=True)
    
    @task
    # 查找热门公司
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'],
            output_pydantic=TrendingCompanyList,
        )

    @task
    # 研究热门公司
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'],
            output_pydantic=TrendingCompanyResearchList,
        )

    @task
    # 选择最佳公司
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company'],
        )
    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""

        manager = Agent(
            config=self.agents_config['manager'],
            # 允许这个 Agent 把任务委派给其他 Agent
            allow_delegation=True
        )
        # 记忆的检索是在请求前执行的，
        # 模型每次调用工具前都会先检索相关记忆，
        # 把相关信息作为上下文一起发送给工具，提升工具调用的智能和准确性。     
        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.hierarchical,
            # 层级模式：Manager 动态分配任务给专家，而非 fixed A→B→C 顺序
            # 对比：Process.sequential（coder/debate 用的串行模式）
            verbose=True, # 终端打印每个 Agent 的思考过程和执行日志，方便调试
            manager_agent=manager,# 定义主agent
            memory=True,#记忆总开关必须为 True，下面三种记忆才会实际生效
            # 长期记忆，跨会话持久化存储
            # Long-term memory for persistent storage across sessions
            # 3种类型记忆定义了那种类型就会存储那种类型。
            long_term_memory = LongTermMemory(
                storage=LTMSQLiteStorage(
                    db_path="./memory/long_term_memory_storage.db"
                )
            ),
            # 存储后端：SQLite 文件（结构化行记录）
            # 存储内容：任务结论和发现（如 "上次找到了 Tesla/Nvidia"）
            # 查找方式：关键词/SQL 匹配
            # 生命周期：跨会话持久，关终端再开还在
            # ============ 短期记忆 ============
            # Short-term memory for current context using RAG
            short_term_memory = ShortTermMemory(
                storage = RAGStorage(
                        embedder_config={
                            "provider": "openai",
                            "config": {
                                "model": 'text-embedding-3-small'
                            }
                        },
                        type="short_term",
                        path="./memory/"
                    )
                ),           
                # 存储后端：LanceDB 向量数据库
                # 存储内容：当前会话的对话片段和上下文
                # 查找方式：语义相似度搜索（"意思相近"，不是关键词匹配）
                # 生命周期：单次 kickoff(会话) 内有效，结束后清空 
                # 效果：模型可以回顾当前对话历史，获取相关信息，提升连贯性和上下文理解    
                
                 # ============ 实体记忆 ============
                # Entity memory for tracking key information about entities
            entity_memory = EntityMemory(
                storage=RAGStorage(
                    embedder_config={
                        "provider": "openai",
                        "config": {
                            "model": 'text-embedding-3-small'
                        }
                    },
                    type="short_term",
                    path="./memory/"
                )
            ),
                # 存储后端：LanceDB 向量数据库（和短期记忆同款）
                # 存储内容：以"实体"（公司名）为中心归类的所有历史信息
                # 查找方式：按实体名 + 语义搜索结合
                # 生命周期：跨会话持久
                # 效果：每次研究 "Tesla"，自动获取之前关于 Tesla 的所有积累信息
        )
