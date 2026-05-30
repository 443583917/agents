# Coder Crew 使用文档

## 快速开始

### 1. 安装依赖

```bash
cd coder
uv sync
```

### 2. 配置模型

在 `coder/` 目录下创建 `.env` 文件：

```bash
# 使用 DeepSeek（示例）
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=openai/deepseek-chat
```

> CrewAI 通过 OpenAI 兼容协议调用各类模型，`OPENAI_BASE_URL` 决定请求发往哪里，`OPENAI_MODEL` 指定模型名。

### 3. 运行

```bash
crewai run
```

运行后 Agent 会编写 Python 代码并执行，结果保存到 `output/code_and_output.txt`。

---

## 核心概念

### Agent（智能体）

一个有角色、目标和工具加持的 AI。定义在 `crew.py` 中通过 `@agent` 装饰器标记。

```python
@agent
def coder(self) -> Agent:
    return Agent(
        config=self.agents_config['coder'],  # 从 YAML 读取配置
        verbose=True,                        # 打印详细日志
        allow_code_execution=True,           # 允许执行代码
        code_execution_mode="safe",          # "safe"=Docker 隔离 / "unsafe"=本地
        max_execution_time=30,               # 代码最长执行时间（秒）
        max_retry_limit=3                    # 最大重试次数
    )
```

### Task（任务）

Agent 要完成的一件具体工作。定义在 `crew.py` 中通过 `@task` 装饰器标记。

```python
@task
def coding_task(self) -> Task:
    return Task(
        config=self.tasks_config['coding_task'],
    )
```

### Crew（团队）

把 Agent 和 Task 组装成一个可执行的团队。

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,              # 自动收集的 Agent 列表
        tasks=self.tasks,                # 自动收集的 Task 列表
        process=Process.sequential,      # sequential=串行 / hierarchical=层级委派
        verbose=True,
    )
```

---

## 自定义指南

### 修改任务

编辑 `src/coder/main.py`，修改 `inputs` 字典：

```python
def run():
    inputs = {
        'assignment': '用 Python 写一个计算斐波那契数列的函数，并输出前 20 项',
    }
    result = Coder().crew().kickoff(inputs=inputs)
    print(result.raw)
```

`{assignment}` 会自动替换到 `agents.yaml` 和 `tasks.yaml` 中的对应位置。

### 添加新 Agent

在 `crew.py` 中添加新方法：

```python
@agent
def reviewer(self) -> Agent:
    return Agent(
        config=self.agents_config['reviewer'],
        verbose=True,
    )
```

同时在 `config/agents.yaml` 中添加对应配置：

```yaml
reviewer:
  role: >
    Code Reviewer
  goal: >
    审查代码，检查逻辑错误和代码风格问题
  backstory: >
    你是一个经验丰富的代码审查者，擅长发现潜在问题。
  llm: gpt-4o-mini
```

### 添加新 Task

在 `crew.py` 中添加：

```python
@task
def review_task(self) -> Task:
    return Task(
        config=self.tasks_config['review_task'],
    )
```

同时在 `config/tasks.yaml` 中添加：

```yaml
review_task:
  description: >
    审查 coder 生成的代码，提出改进建议
  expected_output: >
    一份代码审查报告，包含问题和改进建议
  agent: reviewer
  context: [coding_task]      # 把 coding_task 的输出作为输入
```

### 切换执行模式

在 `crew.py` 的 `@crew` 方法中修改 `process` 参数：

```python
process=Process.sequential      # 串行：按顺序逐个执行 Task
process=Process.hierarchical    # 层级：一个管理 Agent 自动委派任务
```

### 添加自定义工具

编辑 `src/coder/tools/custom_tool.py`，或新建工具文件：

```python
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class FileReaderInput(BaseModel):
    filepath: str = Field(..., description="要读取的文件路径")

class FileReaderTool(BaseTool):
    name: str = "文件读取工具"
    description: str = "读取指定文件的内容"
    args_schema: Type[BaseModel] = FileReaderInput

    def _run(self, filepath: str) -> str:
        with open(filepath, 'r') as f:
            return f.read()
```

然后在 Agent 中引用：

```python
from coder.tools.custom_tool import FileReaderTool

@agent
def coder(self) -> Agent:
    return Agent(
        config=self.agents_config['coder'],
        tools=[FileReaderTool()],     # 挂载工具
        ...
    )
```

---

## 模型切换

CrewAI 通过 OpenAI 兼容协议调用模型。只要服务商提供 OpenAI 格式的 API，就能接入。

### 切换模型只需改 `.env`

```bash
# DeepSeek
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=openai/deepseek-chat

# 阿里通义千问
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=openai/qwen-plus

# 智谱 GLM
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
OPENAI_MODEL=openai/glm-4

# OpenAI 官方（BASE_URL 可省略）
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=openai/gpt-4o
```

改完 `.env` 直接 `crewai run`，无需改代码。

### 不同 Agent 用不同模型

在 `crew.py` 中为每个 Agent 创建独立的 LLM：

```python
def create_llm(model: str):
    return LLM(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

@agent
def coder(self) -> Agent:
    return Agent(
        config=self.agents_config['coder'],
        llm=create_llm("openai/gpt-4o"),       # coder 用 GPT-4o
        ...
    )

@agent
def reviewer(self) -> Agent:
    return Agent(
        config=self.agents_config['reviewer'],
        llm=create_llm("openai/deepseek-chat"), # reviewer 用 DeepSeek
        ...
    )
```

### 或直接在 YAML 中指定

```yaml
# agents.yaml
coder:
  llm: openai/gpt-4o          # 优先级低于代码中的 llm= 参数

reviewer:
  llm: openai/deepseek-chat
```

> 优先级：代码 `llm=` > YAML `llm:` > `.env` 中的 `OPENAI_MODEL`

---

## 常用命令

| 命令 | 作用 |
|------|------|
| `crewai run` | 运行 Crew |
| `crewai install` | 安装项目依赖 |
| `crewai train` | 训练 Crew（如配置了训练） |
| `crewai replay` | 重放上次执行 |
| `crewai test` | 运行测试 |
| `uv run coder` | 通过 uv 运行（等价于 `crewai run`） |

---

## YAML 模板变量

在 `agents.yaml` 和 `tasks.yaml` 中可以使用 `{变量名}` 引用 `main.py` 中 `inputs` 传入的变量：

```yaml
# main.py: inputs = {'assignment': '写一个排序算法'}
# agents.yaml:
goal: >
  完成以下任务：{assignment}
```

---

## 代码执行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `"safe"` | 在 Docker 容器中隔离执行 | 不信任的代码、生产环境 |
| `"unsafe"` | 直接在本地环境执行 | 自己写的代码、开发测试 |

使用 `"safe"` 模式前需安装 Docker Desktop：https://docs.docker.com/desktop/

---

## 输出文件

默认输出到 `output/code_and_output.txt`。可在 `tasks.yaml` 中修改 `output_file` 字段更改输出路径。
