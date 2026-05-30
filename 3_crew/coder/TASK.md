# Task: 复刻 Coder Crew 项目

## 目标

基于 CrewAI 框架，从零开始创建一个名为 `coder` 的多智能体编程助手项目。该项目能让 AI Agent 根据用户给定的编程任务，自动编写 Python 代码、执行代码并输出结果。

项目的工作流程是：
用户提供一个编程任务（如"用 Python 计算莱布尼茨级数前 10000 项并乘以 4"） → 一个 Python Developer Agent 读取任务 → Agent 规划代码结构、编写代码、在本地执行代码 → 将代码和运行结果写入输出文件。

---

## 1. 项目结构

最终项目目录树如下：

```text
coder/
├── .gitignore
├── pyproject.toml
├── README.md
├── USAGE.md
├── .env                          # 用户自行创建，不纳入版本控制
├── knowledge/
│   └── user_preference.txt       # 用户偏好信息，Agent 执行时可参考
├── output/                       # 输出目录（运行时自动创建）
└── src/
    └── coder/
        ├── __init__.py
        ├── main.py               # 程序入口：定义输入参数、启动 Crew
        ├── crew.py               # Crew 定义：组装 Agent、Task、Crew
        ├── config/
        │   ├── agents.yaml       # Agent 配置（角色、目标、背景故事）
        │   └── tasks.yaml        # Task 配置（描述、预期输出）
        └── tools/
            ├── __init__.py
            └── custom_tool.py    # 自定义工具模板
```

---

## 2. 逐文件规格

### 2.1 `.gitignore`

忽略以下内容：
- `.env` 文件
- `__pycache__/` 目录
- `.DS_Store` 文件

---

### 2.2 `pyproject.toml`

使用 hatchling 作为构建后端。具体配置：

**项目元数据：**
- name: `coder`
- version: `0.1.0`
- description: `coder using crewAI`
- authors: `[{ name = "Your Name", email = "you@example.com" }]`
- requires-python: `>=3.10,<3.13`

**依赖（dependencies）：**
- `crewai[tools]>=0.108.0,<1.0.0`
- `gradio>=5.23.3`

**CLI 入口脚本（[project.scripts]）：**
- `coder` → `coder.main:run`
- `run_crew` → `coder.main:run`
- `train` → `coder.main:train`
- `replay` → `coder.main:replay`
- `test` → `coder.main:test`

**CrewAI 配置（[tool.crewai]）：**
- type: `crew`

---

### 2.3 `knowledge/user_preference.txt`

纯文本文件，包含以下 4 行内容：

```
User name is John Doe.
User is an AI Engineer.
User is interested in AI Agents.
User is based in San Francisco, California.
```

---

### 2.4 `src/coder/__init__.py`

空文件。

---

### 2.5 `src/coder/tools/__init__.py`

空文件。

---

### 2.6 `src/coder/tools/custom_tool.py`

定义一个 CrewAI 自定义工具。需要包含大量中文注释作为教程说明。具体要求：

**导入：**
- `BaseTool` from `crewai.tools`
- `Type` from `typing`
- `BaseModel`, `Field` from `pydantic`

**类 `MyCustomToolInput(BaseModel)`：**
- 有一个必填字段 `argument: str`，使用 `Field(..., description="Description of the argument.")`

**类 `MyCustomTool(BaseTool)`：**
- `name: str = "Name of my tool"`
- `description: str` — 一段说明工具用途的英文描述
- `args_schema: Type[BaseModel] = MyCustomToolInput`
- `_run(self, argument: str) -> str` 方法：返回 `"this is an example of a tool output, ignore it and move along."`

**代码中需要有详细的中文注释**，以分隔线 `====` 的形式分为三个章节说明：
1. 第一步：定义输入 Schema（告诉 Agent 调用工具时需要传什么参数）
2. 第二步：定义工具类（继承 BaseTool，设置工具名称、描述、输入格式）
3. 第三步：实现 _run() 方法（工具真正执行的代码）

---

### 2.7 `src/coder/config/agents.yaml`

定义一个名为 `coder` 的 Agent，配置如下（使用 YAML 多行字符串 `>` 语法）：

```yaml
coder:
  role: >
    Python Developer
  goal: >
    You write python code to achieve this assignment: {assignment}
    First you plan how the code will work, then you write the code, then you run it and check the output.
  backstory: >
    You're a seasoned python developer with a knack for writing clean, efficient code.
  llm: gpt-4o-mini
```

其中 `{assignment}` 是模板变量，会被 `main.py` 中传入的 `inputs` 字典自动替换。

**除此之外，YAML 文件后半部分需要有大量被注释掉的中文配置说明**，以注释形式列出 Agent 所有可配置参数及其用途，按类别分组：
- 必填项：role、goal、backstory 的说明
- 模型相关：llm、max_tokens、max_rpm
- 执行控制：verbose、max_iter、max_execution_time、max_retry_limit、allow_delegation、allow_code_execution、code_execution_mode
- 智能行为：planning、cache、respect_context_window、use_system_prompt、inject_date、date_format
- 提示词模板：system_template、prompt_template、response_template
- 输出校验：guardrail、guardrail_max_retries

---

### 2.8 `src/coder/config/tasks.yaml`

定义一个名为 `coding_task` 的任务：

```yaml
coding_task:
  description: >
    Write python code to achieve this: {assignment}
  expected_output: >
    A text file that includes the code itself, along with the output of the code.
  agent: coder
  output_file: output/code_and_output.txt
```

**同样，YAML 文件后半部分需要有大量被注释掉的中文配置说明**，按类别列出所有 Task 可配置参数：
- 绑定与依赖：agent、context
- 输出控制：output_file、output_json
- 执行控制：async_execution、human_input、tools、config

---

### 2.9 `src/coder/crew.py`

这是项目的核心文件。定义 `Coder` 类和 LLM 工厂函数。需要包含大量中文注释。

**函数 `create_llm(model: str | None = None)`：**
- 返回 `LLM(...)` 实例
- 参数优先级：传入的 model > 环境变量 `OPENAI_MODEL` > 默认值 `"openai/deepseek-chat"`
- 从环境变量读取 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`

**类 `Coder`，使用 `@CrewBase` 装饰器：**

类属性：
- `agents_config = 'config/agents.yaml'`
- `tasks_config = 'config/tasks.yaml'`

**方法 `coder(self) -> Agent`（使用 `@agent` 装饰器）：**
- 从 `self.agents_config['coder']` 读取配置
- `llm=create_llm()`
- `verbose=True`
- `tools=[MyCustomTool()]`（从 `coder.tools.custom_tool` 导入）
- `allow_code_execution=True`
- `code_execution_mode="unsafe"`
- `max_execution_time=30`
- `max_retry_limit=3`

**方法 `coding_task(self) -> Task`（使用 `@task` 装饰器）：**
- 从 `self.tasks_config['coding_task']` 读取配置

**方法 `crew(self) -> Crew`（使用 `@crew` 装饰器）：**
- `agents=self.agents`
- `tasks=self.tasks`
- `process=Process.sequential`
- `verbose=True`

**代码中需要包含详细的中文注释**，解释每个装饰器的作用（`@CrewBase`、`@agent`、`@task`、`@crew`），以及 `LLM` 的配置方式、`code_execution_mode` 的 "safe" vs "unsafe" 含义。

---

### 2.10 `src/coder/main.py`

程序入口文件。

**导入：**
- `sys`, `warnings`, `os`
- `datetime` from `datetime`
- `Coder` from `coder.crew`

**全局设置：**
- 过滤 `pysbd` 模块的 `SyntaxWarning`
- 创建 `output` 目录（如果不存在）：`os.makedirs('output', exist_ok=True)`

**全局变量 `assignment`：**
```python
assignment = 'Write a python program to calculate the first 10,000 terms \
    of this series, multiplying the total by 4: 1 - 1/3 + 1/5 - 1/7 + ...'
```

**函数 `run()`：**
- 构建 `inputs = {'assignment': assignment}`
- 调用 `Coder().crew().kickoff(inputs=inputs)`
- 打印 `result.raw`
- 函数上方有一段中文注释，说明设计思路：多任务用循环执行，由 crew.py 定义的 Coder 类负责执行，一个 crew 可以执行很多不同的任务，可以先用意图分析 agent 再调用不同工具

**函数 `train()`：**
- 构建 inputs（topic="AI LLMs"，current_year=当前年份）
- 调用 `Coder().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)`
- 异常处理：捕获异常后抛出包装过的异常信息

**函数 `replay()`：**
- 调用 `Coder().crew().replay(task_id=sys.argv[1])`
- 异常处理同上

**函数 `test()`：**
- 构建 inputs（同 train）
- 调用 `Coder().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)`
- 异常处理同上

---

### 2.11 `README.md`

使用中文和英文混排，包含以下章节：

1. **标题**：`# Coder Crew`，简介说明这是基于 CrewAI 的多智能体编程助手项目
2. **环境要求**：表格形式列出 Python>=3.10<3.13、UV、Visual C++ Build Tools、Docker Desktop 及其用途和安装方式
3. **Windows 必读**：说明 chroma-hnswlib 需要 MSVC 编译工具
4. **安装**：`pip install uv` 然后 `cd coder` 然后 `uv sync`，也提到 `crewai install`
5. **项目结构**：ASCII 目录树
6. **配置说明**：5 个子章节 — 设置 API Key（.env 文件）、自定义 Agent（编辑 agents.yaml）、自定义 Task（编辑 tasks.yaml）、自定义 Crew 逻辑、自定义输入
7. **运行**：`crewai run`，说明默认示例是计算莱布尼茨级数近似 π
8. **架构概览**：ASCII 流程图展示 main.py → crew.py → Agent/Task/Crew 的关系
9. **支持与反馈**：CrewAI 官方文档、GitHub、Discord 链接

---

### 2.12 `USAGE.md`

中文使用文档，包含以下章节：

1. **快速开始**：安装依赖、配置模型（以 DeepSeek 为例展示 .env 配置）、运行
2. **核心概念**：Agent（含代码示例）、Task（含代码示例）、Crew（含代码示例）
3. **自定义指南**：修改任务（修改 main.py 的 inputs）、添加新 Agent、添加新 Task、切换执行模式（sequential vs hierarchical）、添加自定义工具（完整的 FileReaderTool 示例）
4. **模型切换**：列出 DeepSeek / 通义千问 / 智谱 GLM / OpenAI 的 .env 配置方式，不同 Agent 用不同模型的代码示例，YAML 中指定模型的优先级说明
5. **常用命令**：表格列出 crewai run/install/train/replay/test 和 uv run coder
6. **YAML 模板变量**：说明 `{变量名}` 替换机制
7. **代码执行模式**：safe（Docker 隔离）和 unsafe（本地）的对比表格
8. **输出文件**：默认输出路径说明

---

## 3. 关键设计决策

1. **LLM 配置灵活**：通过 `create_llm()` 工厂函数 + 环境变量的方式，用户只需修改 `.env` 即可切换模型服务商（DeepSeek / OpenAI / 通义千问 / 智谱），无需改动代码。

2. **配置与代码分离**：Agent 和 Task 的静态属性（角色、目标、描述）放在 YAML 文件中，动态属性（工具、执行模式、超时）在 Python 代码中设置。代码中的设置优先级高于 YAML。

3. **YAML 模板变量**：`agents.yaml` 和 `tasks.yaml` 中使用 `{assignment}` 占位符，运行时由 `main.py` 的 `inputs` 字典替换。

4. **代码执行模式**：默认使用 `"unsafe"` 模式（本地直接执行），避免对 Docker 的强制依赖。生产环境应改为 `"safe"` 模式。

5. **执行模式**：Crew 使用 `Process.sequential`（串行），因为当前只有一个 Agent 和一个 Task。如果添加更多 Task，可以保持串行或切换为 `Process.hierarchical`。

6. **自定义工具**：`MyCustomTool` 是一个教学模板，展示 CrewAI 工具的三段式结构（Input Schema → Tool Class → _run 方法），实际使用时需要替换为真实功能。

---

## 4. 验证标准

项目创建完成后，应满足以下验证条件：

1. **目录结构完整**：所有 12 个文件/目录都存在且位于正确路径
2. **pyproject.toml 可解析**：`pip install -e .` 或 `uv sync` 能成功安装依赖
3. **CLI 命令可发现**：`crewai run` 能正常启动，或者 `python -m coder.main` 能执行
4. **Crew 能成功 kickoff**：Agent 能读取 assignment、编写 Python 代码、执行代码、输出结果到 `output/code_and_output.txt`
5. **输出文件格式正确**：包含 `CODE:` 和 `OUTPUT:` 两部分，计算结果为 π 的近似值（约 3.14159...）
6. **train/replay/test 函数接口正确**：通过 `sys.argv` 接收参数并传给 Crew 对应方法
