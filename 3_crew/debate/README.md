# Debate Crew — 辩论团队

欢迎来到 Debate Crew 项目，基于 [crewAI](https://crewai.com) 构建。此模板帮助你快速搭建多智能体 AI 辩论系统，充分利用 crewAI 提供的强大且灵活的多 Agent 协作框架，完成复杂的辩论任务。

## 环境要求

确保系统已安装 Python >= 3.10 且 < 3.13。本项目使用 [UV](https://docs.astral.sh/uv/) 进行依赖管理和包处理，提供流畅的安装和执行体验。

首先，如果尚未安装 uv：

```bash
pip install uv
```

接着进入项目目录并安装依赖：

```bash
uv sync
```

（可选）也可以通过 CLI 命令锁定并安装依赖：
```bash
crewai install
```

## 自定义配置

**将你的 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY` 添加到 `.env` 文件中**

- 修改 `src/debate/config/agents.yaml` — 定义你的 Agent（辩手和裁判）
- 修改 `src/debate/config/tasks.yaml` — 定义任务（正方陈述、反方陈述、裁决）
- 修改 `src/debate/crew.py` — 添加自定义逻辑、工具和特定参数
- 修改 `src/debate/main.py` — 添加自定义输入（如辩论议题 motion）

## 运行项目

从项目根目录启动你的 AI Agent 辩论团队：

```bash
$ crewai run
```

该命令初始化 Debate Crew，按照配置组装 Agent 并分配辩论任务。

默认示例（未修改时）：辩手对议题 "There needs to be strict laws to regulate LLMs"（需要对大语言模型实施严格法律监管）进行正反方辩论，裁判做出裁决。输出文件保存在 `output/` 目录下：
- `propose.md` — 正方陈述
- `oppose.md` — 反方陈述
- `decide.md` — 裁判裁决

## 理解你的辩论团队

Debate Crew 由多个 AI Agent 组成，每个 Agent 都有独特的角色、目标和工具。这些 Agent 在 `config/tasks.yaml` 中定义的一系列任务上协作，利用集体技能完成三阶段辩论流程。

| 角色 | 职责 | 使用的模型 |
|------|------|-----------|
| **debater**（辩手） | 对辩论议题进行有说服力的论证，既能为正方也能为反方辩护 | `openai/gpt-4o-mini` |
| **judge**（裁判） | 基于辩手提出的论据，公正地裁决哪一方更有说服力 | `anthropic/claude-sonnet-4-6` |

`config/agents.yaml` 文件定义了每个 Agent 的能力和配置，`config/tasks.yaml` 定义了完整的辩论流程。

## 辩论流程

```text
议题输入 (motion)
      │
      ▼
┌─────────────┐
│  正方陈述    │  debater Agent 为议题辩护
│  propose.md │  输出 → output/propose.md
└─────────────┘
      │
      ▼
┌─────────────┐
│  反方陈述    │  debater Agent 反对议题
│  oppose.md  │  输出 → output/oppose.md
└─────────────┘
      │
      ▼
┌─────────────┐
│  裁判裁决    │  judge Agent 评估双方论据
│  decide.md  │  输出 → output/decide.md
└─────────────┘
```

## 支持与反馈

对于 Debate Crew 或 crewAI 的任何问题或反馈：
- 访问我们的[官方文档](https://docs.crewai.com)
- 通过 [GitHub 仓库](https://github.com/joaomdmoura/crewai) 联系我们
- [加入 Discord 社区](https://discord.com/invite/X4JWnZnxPb)
- [与文档对话](https://chatg.pt/DWjSBZn)

让我们一起借助 crewAI 的力量和简洁创造奇迹。
