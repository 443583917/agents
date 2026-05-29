# 学习任务追踪清单

> 创建时间：2026-05-24 | 目标：10天180h | 当前：Day 1

---

## 阻塞项 / 未完成准备

- [ ] **安装 MS Build Tools** — Week 3 CrewAI 依赖，Day 6 之前完成  
      下载：https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022  
      勾选 "Desktop development with C++"

---

## 进度总览

| 阶段 | 状态 | 时间 | 关键交付 |
|------|------|------|----------|
| 0 环境搭建 | 🔄 进行中 | — | .venv, .env, API key |
| 1 Python速成 + 基础 | ⬜ | 36h | 理解 Agent Loop |
| 2 OpenAI Agents SDK | ⬜ | 36h | SDK 原语：Agent/Tool/Handoff/Guardrail |
| 3 CrewAI | ⬜ | 18h | 多角色协作管线 |
| 4 LangGraph | ⬜ | 36h | 状态图编排 |
| 5 AutoGen | ⬜ | 18h | 分布式消息 |
| 6 MCP | ⬜ | 18h | 协议/Tool Server |
| 7 综合项目 | ⬜ | 18h | 自选项目 + Go MCP Server |

---

## 任务 0：环境搭建

- [x] Windows 长路径已启用
- [ ] 安装 MS Build Tools → **跳过，Day 6 前完成**
- [ ] 安装 uv 包管理器
- [ ] `uv sync` 同步依赖
- [ ] `uv tool install crewai` 安装 CrewAI
- [ ] 配置 `.env` 文件（OpenAI API key）
- [ ] 运行 `setup/diagnostics.py` 环境诊断
- [ ] Jupyter kernel 测试

## 任务 1.1：Python 语法 — Go 视角（4h）

- [ ] Python 基础 notebook (`06_python_foundations.ipynb`)
- [ ] 中级 Python notebook (`10_intermediate_python.ipynb`)
- [ ] 编写 Go→Python 速查卡

## 任务 1.2：异步 Python（4h）

- [ ] 异步 Python notebook (`11_async_python.ipynb`)
- [ ] 编写异步验证脚本 `test_async.py`

## 任务 1.3：CLI/Git/Notebook/调试（4h）

- [ ] 命令行基础 (`02_command_line.ipynb`)
- [ ] Git 复习 (`03_git_and_github.ipynb`)
- [ ] Jupyter 操作 (`05_notebooks.ipynb`)
- [ ] 调试技巧 (`08_debugging.ipynb`)

## 任务 1.4：技术基础 + API（6h）

- [ ] 技术基础 (`04_technical_foundations.ipynb`)
- [ ] AI API + Ollama (`09_ai_apis_and_ollama.ipynb`)
- [ ] API 调用练习脚本 `test_api.py`

## 任务 1.5：Week 1 Labs — Agent Loop（10h）

- [ ] Lab 1：第一个 LLM 调用
- [ ] Lab 2：系统提示词
- [ ] Lab 3：Tool Calling
- [ ] Lab 4：Agent Loop
- [ ] Extra Lab：综合练习
- [ ] 自检：从零重建 Agent Loop (`my_first_agent.py`)

## 任务 2.1：第一个 SDK Agent（4h）

- [ ] Lab 1：SDK 抽象 (`2_openai/1_lab1.ipynb`)

## 任务 2.2：工具深入（6h）

- [ ] Lab 2：Function/Hosted/Custom Tool (`2_openai/2_lab2.ipynb`)

## 任务 2.3：Handoff（8h）

- [ ] Lab 3：Agent 间委托 (`2_openai/3_lab3.ipynb`)

## 任务 2.4：护栏 + 追踪（8h）

- [ ] Lab 4：Guardrail + Tracing (`2_openai/4_lab4.ipynb`)

## 任务 2.5：深度研究项目（6h）

- [ ] 阅读 `2_openai/deep_research/` 整个项目
- [ ] 运行并追踪
- [ ] 自主修改

## 任务 2.6：自主练习（4h）

- [ ] 构建 `my_go_tutor.py`
- [ ] 添加护栏 + Handoff

## 任务 3.1-3.4：CrewAI（18h）

- [ ] Debate Crew
- [ ] Engineering Team
- [ ] Stock Picker + Financial Researcher + Coder
- [ ] CrewAI vs OpenAI SDK 对比总结

## 任务 4.1-4.6：LangGraph（36h）

- [ ] Lab 1：StateGraph 基础
- [ ] Lab 2：条件路由 + 循环
- [ ] Lab 3：人机协作 + Checkpoint
- [ ] Lab 4：多 Agent 子图
- [ ] Sidekick 项目
- [ ] LangGraph 重写 Week 2 Agent

## 任务 5.1-5.5：AutoGen（18h）

- [ ] Lab 1：AgentChat 层
- [ ] Lab 2：多 Agent 团队
- [ ] Lab 3：Core 层 Topic/Subscription
- [ ] Lab 4：分布式部署
- [ ] 框架对比矩阵

## 任务 6.1-6.6：MCP（18h）

- [ ] Lab 1：协议基础
- [ ] Lab 2：构建 MCP Server
- [ ] Lab 3：Resources + Prompts
- [ ] Lab 4：Trading Floor 项目
- [ ] Lab 5：远程 MCP + Docker
- [ ] 用 Go 构建 MCP Server

## 任务 7.1-7.3：综合项目 + 回顾（18h）

- [ ] 框架决策矩阵文档
- [ ] 自选综合项目
- [ ] Go MCP Server 实现

---

## 已交付文档

- [设计文档](specs/2026-05-24-agent-learning-plan-design.md)
- [执行计划（英文）](plans/2026-05-24-agent-learning-execution-plan.md)
- [执行计划（中文）](plans/2026-05-24-agent-learning-plan-cn.md)
