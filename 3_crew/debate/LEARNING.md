# Debate Crew 学习手册

## 1. 项目概述

Debate Crew 是一个基于 CrewAI 的**多智能体辩论系统**。它模拟了一场完整的辩论流程：正方辩手陈述 → 反方辩手陈述 → 裁判裁决。这是学习 CrewAI 框架中"多 Agent 协作 + 串行任务流水线"模式的绝佳范例。

### 核心亮点

- **同一 Agent 执行不同任务**：`debater` Agent 既能为正方辩护，也能为反方辩护，任务描述决定了立场
- **跨模型协作**：辩手使用 GPT-4o-mini，裁判使用 Claude Sonnet，展示了不同模型混用的实际场景
- **三阶段流水线**：propose → oppose → decide，每个阶段的输出自动成为下一阶段的上下文

---

## 2. 项目结构

```
debate/
├── .gitignore
├── pyproject.toml              # 项目配置与依赖
├── README.md                   # 项目说明
├── .env                        # API 密钥（自行创建）
├── knowledge/
│   └── user_preference.txt     # 用户偏好（Agent 参考）
├── output/                     # 输出目录
│   ├── propose.md              # 正方陈述
│   ├── oppose.md               # 反方陈述
│   └── decide.md               # 裁判裁决
└── src/debate/
    ├── __init__.py
    ├── main.py                 # 入口：定义议题、启动 Crew
    ├── crew.py                 # Crew 定义：组装 Agent、Task、Crew
    ├── config/
    │   ├── agents.yaml         # Agent 配置（辩手、裁判）
    │   └── tasks.yaml          # Task 配置（正方、反方、裁决）
    └── tools/
        ├── __init__.py
        └── custom_tool.py      # 自定义工具模板
```

---

## 3. 核心架构解析

### 3.1 角色设计

项目定义了 2 个 Agent，但执行 3 个 Task。关键在于：**Agent 是角色，Task 是具体工作**。

| 组件 | 名称 | 角色定位 | 模型 |
|------|------|----------|------|
| Agent | `debater` | 有说服力的辩手 | `openai/gpt-4o-mini` |
| Agent | `judge` | 公正的裁判 | `anthropic/claude-sonnet-4-6` |
| Task | `propose` | 为议题辩护（正方） | 由 debater 执行 |
| Task | `oppose` | 反对议题（反方） | 由 debater 执行 |
| Task | `decide` | 裁决胜负 | 由 judge 执行 |

**设计要点**：`debater` 这一个 Agent 同时承担正反两方的角色。它之所以能在两个 Task 中产生相反的立场，是因为每个 Task 的 `description` 字段给出了不同的指令（"You are proposing the motion" vs "You are in opposition to the motion"）。这说明 **Agent 的行为更多由 Task 描述驱动，而非 Agent 自身固化的立场**。

### 3.2 执行流程

```text
main.py                           crew.py
  │                                  │
  │  inputs = {                      │  @CrewBase
  │    'motion': '...'               │  ├─ debater()  → Agent
  │  }                               │  ├─ judge()    → Agent
  │                                  │  ├─ propose()  → Task
  ▼                                  │  ├─ oppose()   → Task
Debate().crew().kickoff(inputs) ────►│  ├─ decide()   → Task
                                     │  └─ crew()     → Crew
                                     │       └─ Process.sequential
```

执行顺序是严格串行的：

```
Step 1: debater Agent 执行 propose Task
        → 读取议题，生成正方论据
        → 输出写入 output/propose.md

Step 2: debater Agent 执行 oppose Task
        → 读取议题（自动获取 propose 的上下文）
        → 生成反方论据
        → 输出写入 output/oppose.md

Step 3: judge Agent 执行 decide Task
        → 读取正反双方的论据（自动获取前两个 Task 的输出）
        → 评估并裁决胜负
        → 输出写入 output/decide.md
```

### 3.3 上下文传递机制

CrewAI 在串行模式下，**前面 Task 的输出会自动成为后续 Task 的上下文**。这意味着：

- `oppose` Task 执行时，Agent 能看到 `propose` Task 的输出
- `decide` Task 执行时，Agent 能看到 `propose` 和 `oppose` 两个 Task 的输出

这使得裁判能够"阅读"双方论据后再做裁决，而反方也能针对正方的论点进行反驳。不需要手动传递上下文。

---

## 4. 关键代码解析

### 4.1 crew.py — 团队组装

```python
@CrewBase
class Debate():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def debater(self) -> Agent:
        return Agent(
            config=self.agents_config['debater'],
            verbose=True
        )
```

只需要通过 `config=` 引用 YAML 中的 key，CrewAI 自动完成配置加载。Agent 的所有静态属性（角色、目标、背景、模型）都在 YAML 中定义。

### 4.2 agents.yaml — 一个 Agent 两个立场

```yaml
debater:
  role: A compelling debater
  goal: >
    Present a clear argument either in favor of or against the motion.
    The motion is: {motion}
  backstory: >
    You're an experienced debator with a knack for giving concise
    but convincing arguments. The motion is: {motion}
  llm: openai/gpt-4o-mini
```

注意 `goal` 中写的是 "either in favor of or against"——Agent 本身是中立的，立场完全由 Task 的 `description` 决定。

### 4.3 tasks.yaml — 任务定义决定立场

```yaml
propose:
  description: >
    You are proposing the motion: {motion}.
    Come up with a clear argument in favor of the motion.
    Be very convincing.
  agent: debater
  output_file: output/propose.md

oppose:
  description: >
    You are in opposition to the motion: {motion}.
    Come up with a clear argument against the motion.
    Be very convincing.
  agent: debater
  output_file: output/oppose.md
```

两个 Task 绑定到同一个 `debater` Agent，但 `description` 给出了完全相反的指令。这就是"同一角色执行对立任务"的实现方式。

### 4.4 跨模型配置

```yaml
# 辩手使用 GPT-4o-mini（速度快、成本低）
debater:
  llm: openai/gpt-4o-mini

# 裁判使用 Claude Sonnet（推理能力强，适合做判断）
judge:
  llm: anthropic/claude-sonnet-4-6
```

两个 Agent 使用不同厂商的模型，通过 YAML 中的 `llm` 字段直接指定。这是 CrewAI 的一个强大特性：**每个 Agent 可以独立选择最合适的模型**。例如辩手任务量大且需要快速响应，用便宜的 GPT-4o-mini；裁判需要深度推理和公正判断，用更强的 Claude Sonnet。

使用不同模型时，需在 `.env` 中配置对应的 API Key：
```bash
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### 4.5 main.py — 议题输入

```python
def run():
    inputs = {
        'motion': 'There needs to be strict laws to regulate LLMs',
    }
    result = Debate().crew().kickoff(inputs=inputs)
    print(result.raw)
```

`{motion}` 模板变量在 `agents.yaml` 和 `tasks.yaml` 中多处使用，由这里的 `inputs` 字典统一替换。修改议题只需改这一处。

---

## 5. 设计模式分析

### 5.1 同一 Agent 多任务模式

本项目展示了 CrewAI 的一个重要设计模式：**一个 Agent 可以被多个 Task 复用**。

适用场景：
- 同一角色需要执行多个不同立场或不同角度的任务
- 减少 Agent 定义数量，保持配置简洁
- 通过 Task 的 `description` 动态切换 Agent 的行为模式

不适用场景：
- 不同任务需要不同的工具集
- 不同任务需要不同的模型
- Agent 的角色定位有本质冲突（此时应定义独立的 Agent）

### 5.2 串行辩论流水线

`Process.sequential` 模式确保辩论流程严格按照"正方 → 反方 → 裁判"的顺序执行。这是辩论场景的自然映射——裁判必须在听完双方陈述后才能裁决。

如果改为 `Process.hierarchical`，一个管理 Agent 会自行决定任务分配和执行顺序，这在辩论场景中会导致逻辑混乱。

### 5.3 模型分层策略

辩手用便宜模型（GPT-4o-mini），裁判用强模型（Claude Sonnet），体现了成本与能力的平衡：

- 辩手任务：生成文本，量大但对推理深度要求不高 → 用廉价模型
- 裁判任务：需要公正评估、深度推理、对比分析 → 用强模型

这种分层的成本优化在真实项目中非常重要。

---

## 6. 自定义指南

### 6.1 修改辩论议题

编辑 `src/debate/main.py` 中的 `motion` 值：

```python
inputs = {
    'motion': 'AI will replace most human jobs within 10 years',
}
```

### 6.2 添加更多辩论环节

在 `crew.py` 中添加新的 Task 方法：

```python
@task
def rebuttal_pro(self) -> Task:
    return Task(
        config=self.tasks_config['rebuttal_pro'],
    )
```

在 `tasks.yaml` 中添加对应配置：

```yaml
rebuttal_pro:
  description: >
    You are proposing the motion: {motion}.
    Read the opposition's arguments and provide a rebuttal.
  expected_output: >
    A clear rebuttal against the opposition's points.
  agent: debater
  output_file: output/rebuttal_pro.md
```

注意 Task 在 `crew.py` 中的定义顺序决定了执行顺序，新 Task 放在 `oppose` 之后、`decide` 之前即可。

### 6.3 替换模型

修改 `agents.yaml` 中的 `llm` 字段：

```yaml
debater:
  llm: openai/gpt-4o          # 升级到更强的模型

judge:
  llm: openai/gpt-4o          # 统一使用 OpenAI 模型
```

也可以像 `coder` 项目那样，在 `crew.py` 中通过 `create_llm()` 函数动态创建 LLM 实例，优先级高于 YAML 中的 `llm` 字段。

### 6.4 添加自定义工具

辩手可以挂载搜索工具来查找事实依据，裁判可以挂载事实核查工具。在 `tools/custom_tool.py` 中定义工具，然后在 `crew.py` 的 Agent 中引用：

```python
@agent
def debater(self) -> Agent:
    return Agent(
        config=self.agents_config['debater'],
        tools=[WebSearchTool(), FactCheckTool()],
        verbose=True
    )
```

---

## 7. 运行与调试

### 7.1 基本运行

```bash
cd debate
crewai run
```

### 7.2 查看输出

```bash
cat output/propose.md    # 正方陈述
cat output/oppose.md     # 反方陈述
cat output/decide.md     # 裁判裁决
```

### 7.3 开启详细日志

在 `crew.py` 中设置 `verbose=True`（已经是默认值），运行时会在终端打印每个 Agent 的思考过程和执行细节。

---

## 8. 与其他 CrewAI 项目的对比

| 维度 | Debate Crew | Coder Crew | Demo Crew |
|------|------------|------------|-----------|
| Agent 数量 | 2 | 1 | 2 |
| Task 数量 | 3 | 1 | 2 |
| 核心模式 | 同一 Agent 多立场 | 单 Agent 代码执行 | 多 Agent 研究链 |
| 模型策略 | 跨厂商混用 | 统一模型 | 统一模型 |
| 输出文件 | 3 个（正反方+裁决） | 1 个（代码+结果） | 1 个（报告） |
| 执行模式 | Sequential | Sequential | Sequential |
| 学习重点 | 上下文传递、立场切换 | 代码执行、LLM 工厂 | Agent 协作流水线 |

---

## 9. 常见问题

### Q: 为什么辩手不会"混淆"正反立场？

因为每个 Task 的 `description` 明确给出了立场指令。Agent 在执行 `propose` 时会收到 "You are proposing the motion"，在执行 `oppose` 时会收到 "You are in opposition to the motion"。Agent 的行为由当前 Task 的描述驱动。

### Q: 裁判如何看到双方的论据？

CrewAI 的 `Process.sequential` 模式会自动将前置 Task 的输出作为上下文传递给后续 Task。`decide` Task 执行时，`propose` 和 `oppose` 的输出都在上下文中。

### Q: 可以同时使用多个模型服务商吗？

可以。每个 Agent 在 YAML 中独立配置 `llm` 字段，只要在 `.env` 中提供对应服务商的 API Key 即可。CrewAI 会为每个 Agent 创建独立的 LLM 连接。

### Q: 能否让辩论变成交互式的（人类参与）？

可以在 Task 中设置 `human_input: true`，这样在执行该 Task 之前，系统会暂停等待人类输入。这可以用来让人类参与辩论或做出最终裁决。
