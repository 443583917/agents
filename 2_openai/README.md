# Week 2：OpenAI Agents SDK

这是 6 周 Agent 开发课程的第二周——**第一个框架化模块**。Week 1（`1_foundations`）从零手写了 Agent Loop，本周用 OpenAI Agents SDK 把同样的模式封装成工业级原语。

## 你在这周会学到什么

| 概念 | 一句话解释 |
|------|-----------|
| **Agent** | 一个有名字、指令、可用工具的 AI 角色 |
| **Runner** | 执行 Agent 的运行时，同步/异步 |
| **Tool（@function_tool）** | LLM 可以调用的 Python 函数 |
| **Agent as Tool（.as_tool()）** | 把一个 Agent 包装成另一个 Agent 的工具 |
| **Handoff** | A Agent 把对话转交给 B Agent |
| **Structured Output** | 用 Pydantic 约束 Agent 的输出格式 |
| **Guardrail** | 输入/输出安全检查，阻止不合规消息 |
| **Trace** | 在 OpenAI 平台可视化查看 Agent 完整运行过程 |
| **WebSearchTool** | OpenAI 托管的网页搜索工具 |

## 项目结构

```
2_openai/
├── 1_lab1.ipynb           # Day 1：Hello World——第一个 Agent
├── 2_lab2.ipynb           # Day 2：冷销售邮件生成系统（Tool + Handoff）
├── 3_lab3.ipynb           # Day 3：多模型、结构化输出、Guardrail
├── 4_lab4.ipynb           # Day 4：Deep Research 深度研究 Agent
├── deep_research/         # Day 4 的重构版——带 Gradio UI 的完整项目
│   ├── deep_research.py       # Gradio 入口
│   ├── research_manager.py    # 编排器：规划→搜索→写报告→发邮件
│   ├── planner_agent.py       # 规划搜索查询（Structured Output）
│   ├── search_agent.py        # 执行网页搜索（WebSearchTool）
│   ├── writer_agent.py        # 合成为长文 markdown 报告
│   └── email_agent.py         # 通过 SendGrid 发送 HTML 邮件
├── community_contributions/   # 学员提交的 250+ 项目作品
└── community_contribution/    # 精选贡献（SDR Agent 等）
```

## 4 天学习路线

### Day 1 — 最小可用 Agent（1_lab1.ipynb）
用 5 行代码创建第一个 Agent：`Agent` + `Runner.run()` + `trace`。在 platform.openai.com/traces 查看运行轨迹。

### Day 2 — 第一个 Agent 项目（2_lab2.ipynb）
为虚构公司 "ComplAI"（SOC2 合规 SaaS）构建冷销售邮件生成系统：
- 3 个销售 Agent 并行生成不同风格的邮件
- `@function_tool` 装饰器暴露 `send_email` 函数
- `.as_tool()` 包装 Agent 为工具
- `handoffs` 实现 Sales Manager → Email Manager 委派
- SendGrid 真实邮件发送

### Day 3 — 生产化（3_lab3.ipynb）
- 切换模型提供商（DeepSeek、Gemini、Groq）
- Pydantic Structured Outputs
- `@input_guardrail` 输入安全检查

### Day 4 — Deep Research 深度研究（4_lab4.ipynb + deep_research/）
结合所有知识构建完整管线：规划搜索 → 并行搜索 → 写报告 → 发邮件。`deep_research/` 提供了 Gradio UI 重构版。

## 用 DeepSeek 替代 OpenAI

```python
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
import os

deepseek_client = AsyncOpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

deepseek_model = OpenAIChatCompletionsModel(
    model="deepseek-chat",
    openai_client=deepseek_client
)

agent = Agent(
    name="助手",
    instructions="你是一个有帮助的助手。",
    model=deepseek_model
)
```

## 前置要求

- 完成 `1_foundations/` 全部 4 个 Lab
- 理解 Agent Loop（思考→行动→观察→重复）
- 熟悉 async/await（参考 `guides/11_async_python.ipynb`）
- `.env` 中配置了 API Key（OpenAI 或 DeepSeek）

## 参考资源

- [OpenAI Agents SDK 文档](https://openai.github.io/openai-agents-python/)
- [OpenAI Traces 面板](https://platform.openai.com/traces)
- 详细学习指南：[学习指南.md](学习指南.md)
- 中文导航：[../docs/中文学习导航.md](../docs/中文学习导航.md)
