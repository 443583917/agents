# Week 3：CrewAI — 多 Agent 角色协作

这是 6 周 Agent 开发课程的第三周。Week 2 用 OpenAI Agents SDK 构建了单 Agent 工作流，本周用 **CrewAI** 解决"怎么让多个 Agent 像团队一样协作"。

## 核心理念

CrewAI 给 Agent 赋予**角色（Role）、目标（Goal）、背景故事（Backstory）**，再把 Agent 分配给 Task，用 Crew 编排执行流程。对后端程序员来说，这很像"把函数签名改成角色定义"。

```python
# 一个 CrewAI Agent
Agent(
    role="高级研究员",                    # 角色
    goal="发现关于 {topic} 的突破性洞见",  # 目标
    backstory="20年行业经验的资深分析师",   # 背景故事（影响语气和风格）
    tools=[搜索工具],
    llm="openai/gpt-4o"
)

# Task 有明确的输入和输出
Task(
    description="研究 {topic} 的最新趋势",
    expected_output="500字报告，含3个关键发现",
    agent=researcher,
    output_file="output/report.md"
)

# Crew 编排任务管线
Crew(agents=[...], tasks=[...], process=Process.sequential)
```

## 5 个项目（按学习顺序）

| 顺序 | 项目 | Agent 数 | 核心新概念 | 难度 |
|------|------|---------|-----------|------|
| 1 | `coder/` | 1 | 单 Agent + Docker 代码执行 | ⭐ |
| 2 | `debate/` | 2 | 多 Agent、Agent 复用、多 LLM 供应商 | ⭐⭐ |
| 3 | `financial_researcher/` | 2 | 工具集成、Task context（链式依赖） | ⭐⭐ |
| 4 | `stock_picker/` | 4 | **层级流程**、Pydantic 结构化输出、**持久化记忆** | ⭐⭐⭐⭐ |
| 5 | `engineering_team/` | 4 | 多 Agent SDLC 管线、代码执行 Agent | ⭐⭐⭐ |

## 项目结构（5 个项目共用模板）

```
<project_name>/
├── README.md                    # CrewAI 项目模板说明
├── pyproject.toml               # UV 管理，依赖 crewai[tools]>=0.108.0
├── knowledge/
│   └── user_preference.txt      # Agent 知识文件
├── output/                      # 生成的输出（报告、代码等）
└── src/<project_name>/
    ├── main.py                  # 入口：Crew().kickoff(inputs=...)
    ├── crew.py                  # @CrewBase 类：@agent + @task + @crew
    ├── config/
    │   ├── agents.yaml          # Agent 定义（role/goal/backstory/llm）
    │   └── tasks.yaml           # Task 定义（description/expected_output）
    └── tools/
        ├── __init__.py
        └── custom_tool.py       # 自定义工具（BaseTool 子类）
```

## CrewAI 核心概念速查

| 概念 | 代码 | 用途 |
|------|------|------|
| Agent | `@agent` + `Agent(config=...)` | 定义 AI 角色 |
| Task | `@task` + `Task(config=...)` | 定义任务 |
| Crew | `@crew` + `Crew(agents, tasks, process)` | 编排执行 |
| 顺序流程 | `Process.sequential` | A→B→C 固定顺序 |
| 层级流程 | `Process.hierarchical` + `manager_agent` | Manager 动态委派 |
| 工具 | `tools=[SerperDevTool()]` | Agent 可以调用的函数 |
| 结构化输出 | `output_pydantic=MyModel` | 类型安全的 Task 输出 |
| 任务链 | `Task(context=[prior_task])` | 一个 Task 读取另一个的输出 |
| 代码执行 | `allow_code_execution=True` | Docker 沙箱执行代码 |
| 记忆 | `memory=True` + LTM/STM/Entity | 跨会话持久化 |
| 模板变量 | `{variable}` | YAML 中的动态参数 |

## 用 DeepSeek 替代 OpenAI

在 `agents.yaml` 中指定 llm 时使用：

```yaml
# 方式1：直接在 YAML 中配 base_url
my_agent:
  role: 助手
  goal: 帮助用户
  llm: deepseek/deepseek-chat
  # 需设置环境变量 DEEPSEEK_API_KEY 和 DEEPSEEK_API_BASE

# 方式2：在 crew.py 中传自定义 LLM
from crewai import LLM
deepseek_llm = LLM(
    model="deepseek/deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
agent = Agent(..., llm=deepseek_llm)
```

## 什么时候用 CrewAI

- 需要固定的多步骤工作管线（A→B→C→输出）
- Agent 之间有明确的角色分工
- 不需要运行时动态路由或人工审批
- 追求快速搭建、YAML 驱动配置

## 参考资源

- [CrewAI 官方文档](https://docs.crewai.com/)
- 详细学习指南：[学习指南.md](学习指南.md)
- 中文导航：[../docs/中文学习导航.md](../docs/中文学习导航.md)
