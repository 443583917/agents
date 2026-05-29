# 10天 Agent 开发强化学习执行计划

> **给执行者：** 按任务逐个执行，每完成一步勾选 `[x]`。

**目标：** 10天180小时内完成 Ed Donner 的6周 Agentic AI 工程课程，从 Go 后端转型 AI Agent 开发，Python 零基础起步。

**整体架构：** 7阶段瀑布式推进，沿课程递进结构。Python 通过 Go→Python 映射学习而非从零学起。重点投入 OpenAI Agents SDK（锚点框架）和 LangGraph（控制流框架）。

**技术栈：** Python 3.12, uv, Cursor IDE, OpenAI Agents SDK, CrewAI, LangGraph, AutoGen, MCP, Jupyter Notebooks

---

## 前置准备：环境搭建

### 任务 0：环境初始化

- [ ] **步骤 1：修复 Windows 长路径限制（仅 Windows）**

以管理员身份打开 PowerShell，运行：
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```
重启电脑。

- [ ] **步骤 2：安装 Microsoft Build Tools（仅 Windows）**

下载地址：https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
安装时勾选"Desktop development with C++"工作负载。
验证：`where cl` 应能找到编译器。

- [ ] **步骤 3：安装 uv 包管理器**

Windows (PowerShell)：
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux/macOS：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

验证：`uv --version`

- [ ] **步骤 4：安装 Cursor IDE**

从 https://www.cursor.com/ 下载安装。
打开 Cursor，安装推荐扩展：Python (ms-python)、Jupyter (ms-toolsai.jupyter)。

- [ ] **步骤 5：克隆仓库并同步依赖**

```bash
cd ~/projects  # 或 C:\Users\<你的用户名>\projects
git clone https://github.com/ed-donner/agents.git
cd agents
uv self update
uv sync
```

验证：
- 项目根目录出现 `.venv/` 文件夹
- `uv python list` 显示 Python 3.12
- `uv run python -c "import openai; print(openai.__version__)"` 能正常运行

- [ ] **步骤 6：全局安装 CrewAI**

```bash
uv tool install crewai==0.130.0 --python 3.12
uv tool upgrade crewai==0.130.0 --python 3.12
```

验证：`uv tool list` 显示 crewai

- [ ] **步骤 7：配置 OpenAI API 密钥**

1. 访问 https://platform.openai.com/api-keys
2. 创建新密钥，复制
3. 在项目根目录创建 `.env` 文件：
```
OPENAI_API_KEY=sk-proj-你的密钥
```

验证：`uv run python setup/diagnostics.py` — 所有检查应通过

- [ ] **步骤 8：测试 Jupyter 内核**

1. 在 Cursor 中打开 `1_foundations/1_lab1.ipynb`
2. 点击"Select Kernel" → `.venv (Python 3.12.x)`
3. 按 Shift+Enter 运行第一个代码单元
4. 预期：无报错

- [ ] **步骤 9：提交环境检查点**

```bash
git add -A
git commit -m "chore: 环境搭建完成"
```

---

## 阶段一：Python 速成 + 基础（第1-2天，36小时）

### 任务 1.1：Python 语法 — Go 视角（4h）

**文件：**
- 打开：`guides/06_python_foundations.ipynb`
- 打开：`guides/10_intermediate_python.ipynb`

- [ ] **步骤 1：通读 Python 基础 notebook（2h）**

执行 `guides/06_python_foundations.ipynb` 中的每个单元。每个概念都在脑中做 Go 对照：

| Python | Go |
|--------|-----|
| `x: int = 5`（类型标注） | `var x int = 5` |
| `def f(a: str) -> str:` | `func f(a string) string` |
| `[x*2 for x in range(10)]` | 手写 for 循环 |
| `{"key": "val"}` | `map[string]string{"key": "val"}` |
| `{"a", "b", "c"}` | 无内置 set，用 `map[T]struct{}` |
| `(1, "hello")` | 无 tuple，用 struct |
| `if __name__ == "__main__":` | `func main()` in `package main` |
| `class Dog(Animal):` | `type Dog struct { Animal }`（嵌入） |
| `try/except/finally` | `defer` + `recover`（模式不同） |

- [ ] **步骤 2：中级 Python — 装饰器、生成器、上下文管理器（2h）**

执行 `guides/10_intermediate_python.ipynb` 中每个单元。

关键 Go 对照：
- **装饰器**（`@something`）= 中间件模式。函数包装函数。
  ```python
  @retry(max_attempts=3)
  def call_api():
      ...  # retry 接受 call_api 并返回包装后的版本
  ```
  Go 等价写法：`http.Handle("/path", loggingMiddleware(authMiddleware(handler)))`

- **生成器**（`yield`）= 惰性迭代器。Go 中最接近的是返回单值的 channel。
- **上下文管理器**（`with` 语句）= 作用域 `defer`。`with open("f") as f:` ≈ `f, _ := os.Open("f"); defer f.Close()`

- [ ] **步骤 3：编写 Go→Python 速查卡（30min）**

创建 `~/go-python-cheatsheet.md`：
```markdown
# Go → Python 速查手册

## 变量声明
Go:   var name string = "value"
Py:   name: str = "value"

## 函数
Go:   func add(a int, b int) int { return a + b }
Py:   def add(a: int, b: int) -> int: return a + b

## 错误处理
Go:   if err != nil { return err }
Py:   raise Exception("msg") / try: ... except: ...

## 并发
Go:   go func() { ... }()
Py:   asyncio.create_task(async_func())

## 包管理
Go:   import "fmt"; fmt.Println(x)
Py:   from pathlib import Path; Path("/tmp")

## 结构体/数据类
Go:   type User struct { Name string; Age int }
Py:   @dataclass
      class User:
          name: str
          age: int

## 接口/协议
Go:   type Reader interface { Read([]byte) (int, error) }
Py:   class Reader(Protocol):
          def read(self, size: int) -> bytes: ...

## 主函数
Go:   func main() { ... } in package main
Py:   if __name__ == "__main__": main()
```

- [ ] **步骤 4：提交**

```bash
git add ~/go-python-cheatsheet.md
git commit -m "docs: Go→Python 速查手册"
```

### 任务 1.2：异步 Python — 关键差异（4h）

**文件：**
- 打开：`guides/11_async_python.ipynb`

> 这是 Agent 开发者最重要的 Python 概念。每个 Agent 框架都使用 async/await。心智模型与 goroutine 不同 —— Python async 是单线程协作式多任务，而非抢占式。

- [ ] **步骤 1：理解事件循环模型（1h）**

执行 `guides/11_async_python.ipynb` 前半部分的单元。

需要内化的核心差异：
```
Go goroutine: OS线程 + 抢占式调度
    go foo()  → 立即执行，可能并行运行

Python async: 单线程事件循环 + 协作式 await 点
    await foo()  → foo 入队，当前任务在 await 处让出控制权时才执行
```

**Python async 代码何时真正执行：**
```python
async def fetch(url):
    data = await http_get(url)  # ← 只在这里让出控制权
    return data

# 在调度之前什么都不做：
task = asyncio.create_task(fetch("http://example.com"))
# 可能仍未执行 —— 需要 await 来让出：
result = await task  # ← 现在调度器才给 fetch() 分配 CPU 时间
```

- [ ] **步骤 2：理解 asyncio.gather = errgroup（1h）**

执行剩余单元。

```python
# Python：用 gather 并发执行
async def fetch_all(urls):
    tasks = [asyncio.create_task(fetch(url)) for url in urls]
    results = await asyncio.gather(*tasks)  # ≈ errgroup.Wait()
    return results
```

Go 等价写法：
```go
func fetchAll(urls []string) ([]Result, error) {
    g, _ := errgroup.WithContext(ctx)
    results := make([]Result, len(urls))
    for i, url := range urls {
        i, url := i, url
        g.Go(func() error {
            r, err := fetch(url)
            results[i] = r
            return err
        })
    }
    return results, g.Wait()
}
```

- [ ] **步骤 3：理解异步生成器（2h）**

异步生成器在流式 Agent 响应中大量使用：
```python
async for chunk in agent.stream_response("query"):
    print(chunk, end="")
```

概念上类似于从 channel 读取：
```go
for chunk := range agent.StreamResponse(ctx, "query") {
    fmt.Print(chunk)
}
```

- [ ] **步骤 4：验证理解**

写一个小型异步程序并运行：
```python
import asyncio
import time

async def worker(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name} 完成"

async def main():
    start = time.time()
    results = await asyncio.gather(
        worker("A", 1.0),
        worker("B", 0.5),
        worker("C", 1.5),
    )
    elapsed = time.time() - start
    print(f"结果: {results}")
    print(f"耗时: {elapsed:.1f}s（应约为 1.5s，而非 3.0s）")

asyncio.run(main())
```

运行：`uv run python test_async.py`
预期：耗时约 1.5s，证明并发执行。

- [ ] **步骤 5：提交**

```bash
git add test_async.py
git commit -m "learn: async/await — 并发 worker 模式"
```

### 任务 1.3：命令行、Git、Notebook、调试（4h）

**文件：**
- 打开：`guides/02_command_line.ipynb`
- 打开：`guides/03_git_and_github.ipynb`
- 打开：`guides/05_notebooks.ipynb`
- 打开：`guides/08_debugging.ipynb`

- [ ] **步骤 1：命令行基础（1h）**

浏览 `guides/02_command_line.ipynb`。作为 Go 开发者你应该已经掌握了这些，只需注意：
- 用 `uv run script.py` 而非 `python script.py`
- 用 `uv run pytest` 而非 `go test ./...`
- 用 `uv add package` 而非 `go get package`

- [ ] **步骤 2：Git 复习（1h）**

浏览 `guides/03_git_and_github.ipynb`。确认工作流：clone → branch → commit → PR。

- [ ] **步骤 3：Jupyter Notebook（1h）**

通读 `guides/05_notebooks.ipynb`。关键操作：
- `Shift+Enter`：执行单元并移到下一个
- `Ctrl+Enter`：执行单元并停留
- `Esc → A`：在上方插入单元
- `Esc → B`：在下方插入单元
- `Esc → D D`：删除单元

- [ ] **步骤 4：调试技巧（1h）**

通读 `guides/08_debugging.ipynb`。关键工具：
- `print()` — 永远可用
- `breakpoint()` — Python 交互式调试器（≈ Go 的 `dlv`）
- Cursor 调试器 — 设断点、单步执行

### 任务 1.4：技术基础 + API（6h）

**文件：**
- 打开：`guides/04_technical_foundations.ipynb`
- 打开：`guides/09_ai_apis_and_ollama.ipynb`

- [ ] **步骤 1：技术基础（3h）**

执行 `guides/04_technical_foundations.ipynb` 中所有单元。关键概念：
- 环境变量（`.env` 文件、`os.getenv()`、`load_dotenv()`）
- HTTP/HTTPS 基础（requests 库 ≈ Go 的 `net/http`）
- REST API（GET/POST、headers、JSON body）
- 认证（API key、Bearer token）

- [ ] **步骤 2：AI API 和 Ollama（3h）**

执行 `guides/09_ai_apis_and_ollama.ipynb` 中所有单元。关键概念：
- OpenAI Chat Completion API 格式
- Anthropic Messages API 格式
- 用 Ollama 运行本地模型（替代付费 API 的免费方案）
- Token 用量追踪和成本管理

- [ ] **步骤 3：练习 API 调用（自主练习）**

写一个调用 OpenAI 的 Python 脚本：
```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",  # 练习用最便宜的模型
    messages=[
        {"role": "system", "content": "你是一个有帮助的助手。"},
        {"role": "user", "content": "用3句话向Python开发者解释goroutine。"},
    ],
)
print(response.choices[0].message.content)
print(f"消耗 Token: {response.usage.total_tokens}")
```

运行：`uv run python test_api.py`
预期：3句话解释 + token 计数。

- [ ] **步骤 4：提交**

```bash
git add test_api.py
git commit -m "learn: OpenAI API 基础 — chat completion"
```

### 任务 1.5：Week 1 实验 — Agent Loop（10h）

**文件：**
- 打开：`1_foundations/1_lab1.ipynb`
- 打开：`1_foundations/2_lab2.ipynb`
- 打开：`1_foundations/3_lab3.ipynb`
- 打开：`1_foundations/4_lab4.ipynb`
- 打开：`1_foundations/5_extra.ipynb`

- [ ] **步骤 1：Lab 1 — 第一个 LLM 调用（2h）**

执行 `1_foundations/1_lab1.ipynb` 中所有单元。理解：
- `messages` 列表格式：`[{"role": "system/user/assistant", "content": "..."}]`
- Temperature 参数（0=确定性，1=创造性）
- Chat Completion 响应对象

完成标准：能从代码中调用 LLM。

- [ ] **步骤 2：Lab 2 — 系统提示词（2h）**

执行 `1_foundations/2_lab2.ipynb` 中所有单元。理解：
- 系统提示词塑造 Agent 人格和行为
- 提示词工程：具体化、举例、设约束
- 不同模型对同一提示词有不同响应

完成标准：能设计 Agent 的"人格"。

- [ ] **步骤 3：Lab 3 — Tool Calling（3h）** *关键*

执行 `1_foundations/3_lab3.ipynb` 中所有单元。这是最重要的概念。

**基础模式：**
```python
def get_weather(city: str) -> str:
    """获取城市当前天气。"""
    return f"{city}天气：22°C，晴"

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取城市当前天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        }
    }
}]

# LLM 决定何时调用工具以及用什么参数
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "巴黎天气怎么样？"}],
    tools=tools,
)
# response 可能包含 tool_call 而非文本
```

Go 视角：这就像 LLM 动态选择调用哪个函数 — 不需要 `switch` 语句。

完成标准：理解 Agent 如何使用工具。

- [ ] **步骤 4：Lab 4 — Agent Loop（2h）** *关键*

执行 `1_foundations/4_lab4.ipynb` 中所有单元。

**完整 Agent Loop 模式（务必记住）：**
```python
messages = [{"role": "system", "content": system_prompt}]
messages.append({"role": "user", "content": user_query})

while True:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )
    msg = response.choices[0].message

    if msg.tool_calls:                    # LLM 想使用工具
        messages.append(msg)              # 将助手的 tool_call 加入历史
        for tool_call in msg.tool_calls:
            result = execute_tool(tool_call.function.name,
                                  json.loads(tool_call.function.arguments))
            messages.append({             # 将工具结果加入历史
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })
    else:                                  # LLM 完成任务
        messages.append({"role": "assistant", "content": msg.content})
        break

return msg.content
```

这是本课程所有 Agent 框架的基础。

- [ ] **步骤 5：Extra Lab（1h）**

执行 `1_foundations/5_extra.ipynb` 中所有单元。将 Lab 1-4 整合为一个完整的 mini-agent。

- [ ] **步骤 6：自检 — 从零重建 Agent Loop**

关闭所有 notebook。新建一个 `.py` 文件，实现：
1. 从 `input()` 接收用户问题
2. 包含 `calculate(expression: str) -> float` 工具
3. 运行 Agent Loop，需要时调用工具
4. 打印最终答案

运行：`uv run python my_first_agent.py`
输入："15乘23再加100是多少？"
预期：通过工具调用得到正确答案。

- [ ] **步骤 7：提交**

```bash
git add my_first_agent.py
git commit -m "learn: 完整 Agent Loop — 思考→行动→观察→重复"
```

---

## 阶段二：OpenAI Agents SDK（第3-5天，36小时）

> 这是你的锚点框架。像掌握 `net/http` 一样掌握它。之后每个框架都只是对这些概念的不同封装。

### 任务 2.1：第一个 SDK Agent（4h）

**文件：**
- 打开：`2_openai/1_lab1.ipynb`

- [ ] **步骤 1：理解 SDK 抽象（1h）**

OpenAI Agents SDK 将原始 API 封装为更高级的抽象：

```python
from agents import Agent, Runner

agent = Agent(
    name="助手",
    instructions="你是一个有帮助的助手。",
    model="gpt-4o",
)

result = Runner.run_sync(agent, "法国首都是什么？")
print(result.final_output)
```

对比你在任务 1.5 中写的原始 Agent Loop — SDK 帮你做了循环、工具执行和消息管理。

- [ ] **步骤 2：执行 Lab 1 所有单元（3h）**

逐一理解：
- `Agent` — 核心抽象（name, instructions, model, tools, handoffs）
- `Runner.run_sync()` vs `Runner.run()`（同步 vs 异步）
- `RunResult` — final_output, new_items, last_agent
- `RunConfig` — workflow_name, trace_id 等

### 任务 2.2：工具深入（6h）

**文件：**
- 打开：`2_openai/2_lab2.ipynb`

- [ ] **步骤 1：函数工具（2h）**

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """获取城市当前天气。"""
    return f"{city}天气：22°C，晴"

agent = Agent(
    name="天气机器人",
    instructions="你帮助用户查询天气。",
    tools=[get_weather],
)
```

`@function_tool` 装饰器从函数签名 + docstring 自动生成 JSON schema。在原始 API 中你需要手写（任务 1.5 步骤 3）。

- [ ] **步骤 2：内置工具（1h）**

SDK 提供预构建工具：
```python
from agents.extensions.tools import WebSearchTool, FileSearchTool
```

- [ ] **步骤 3：自定义工具类（2h）**

当工具需要维护状态时：
```python
from agents import Tool

class DatabaseTool(Tool):
    def __init__(self, db_connection):
        self.db = db_connection

    async def __call__(self, query: str) -> str:
        result = await self.db.execute(query)
        return str(result)
```

- [ ] **步骤 4：工具错误处理（1h）**

工具可能失败。SDK 的处理方式：
```python
@function_tool
def risky_tool(param: str) -> str:
    try:
        return do_thing(param)
    except Exception as e:
        return f"错误: {e}"  # LLM 看到错误可以换方式重试
```

### 任务 2.3：Handoff — Agent 间委托（8h）

**文件：**
- 打开：`2_openai/3_lab3.ipynb`

- [ ] **步骤 1：理解 Handoff 概念（2h）**

Handoff 是 SDK 的 Agent 间委托机制。Go 类比：负载均衡器将请求路由到专门化微服务。

```python
from agents import Agent, handoff

billing_agent = Agent(
    name="计费",
    instructions="你处理计费相关问题。",
    tools=[lookup_invoice, process_refund],
)

support_agent = Agent(
    name="支持",
    instructions="你处理一般支持。将计费问题转给计费Agent。",
    handoffs=[handoff(billing_agent)],  # 可以委托给计费Agent
)
```

用户问计费问题时，`support_agent` 自动 handoff 给 `billing_agent`。用户感受到无缝体验，但内部是不同 Agent 带着不同工具接管。

- [ ] **步骤 2：带过滤器的 Handoff（2h）**

控制何时触发 handoff：
```python
handoff(
    billing_agent,
    input_filter=lambda history: history[-1]["content"],  # 传递什么内容
)
```

- [ ] **步骤 3：多 Agent 链（2h）**

```python
triage = Agent(name="分诊", handoffs=[handoff(support), handoff(sales)])
support = Agent(name="支持", handoffs=[handoff(billing), handoff(technical)])
billing = Agent(name="计费", tools=[...])
technical = Agent(name="技术", tools=[...])
```

这形成委托图 — 但它是动态的（LLM 决定何时 handoff），而非静态 DAG。

- [ ] **步骤 4：执行 Lab 3 所有单元（2h）**

构建完整的 Handoff 链。用触发多次 Handoff 的多轮对话做实验。

### 任务 2.4：护栏 + 追踪（8h）

**文件：**
- 打开：`2_openai/4_lab4.ipynb`

- [ ] **步骤 1：输入护栏（2h）**

```python
from agents import Agent, Runner, input_guardrail
from pydantic import BaseModel

class ContentCheck(BaseModel):
    is_harmful: bool
    reasoning: str

@input_guardrail
async def no_harmful_content(context, agent, input):
    result = await check_harmfulness(input)
    return result  # True = 阻止, False = 放行

agent = Agent(
    name="安全助手",
    instructions="...",
    input_guardrails=[no_harmful_content],
)
```

Go 类比：处理前验证请求体的 HTTP 中间件。

- [ ] **步骤 2：输出护栏（2h）**

同样模式，但作用在 Agent 输出上：
```python
@output_guardrail
async def check_factual_accuracy(context, agent, output):
    ...
```

- [ ] **步骤 3：追踪（2h）**

SDK 自动追踪每次 Agent 运行：
```python
from agents import trace

with trace("我的工作流"):
    result = Runner.run_sync(agent, "问题")
    # 记录每一步：LLM调用、工具执行、handoff
```

Go 类比：OpenTelemetry spans。追踪记录完整的执行树。

- [ ] **步骤 4：执行 Lab 4 所有单元（2h）**

完成 notebook，尝试阻止/放行各种输入的护栏。

### 任务 2.5：深度研究项目（6h）

**文件：**
- 打开：`2_openai/deep_research/`

- [ ] **步骤 1：阅读并理解整个项目（2h）**

阅读 `2_openai/deep_research/` 中的每个文件。这是一个生产级 Agent，它：
- 接收研究问题
- 搜索网络
- 综合发现
- 生成结构化报告

- [ ] **步骤 2：运行深度研究 Agent（2h）**

```bash
uv run python 2_openai/deep_research/main.py
```

测试问题："Go的并发模型和Python的asyncio的主要区别是什么？"

- [ ] **步骤 3：追踪执行（1h）**

查看追踪输出。识别每一步：LLM 调用 → 工具调用 → handoff → 最终输出。

- [ ] **步骤 4：修改（1h）**

添加新能力 — 例如添加能读取本地文件的工具用于研究。

- [ ] **步骤 5：提交**

```bash
git add -A
git commit -m "learn: OpenAI Agents SDK — 工具、handoff、护栏、追踪"
```

### 任务 2.6：自主练习（4h）

- [ ] **步骤 1：构建 Go 面试准备 Agent（2h）**

创建 `my_go_tutor.py`：
```python
from agents import Agent, Runner, function_tool

@function_tool
def search_go_docs(query: str) -> str:
    """搜索 Go 文档（暂为模拟）。"""
    return f"'{query}' 的搜索结果：..."

@function_tool
def evaluate_code(code: str) -> str:
    """评估 Go 代码的正确性。"""
    # 生产环境可运行 go build/go vet
    return "代码无误，无语法错误。"

tutor = Agent(
    name="Go导师",
    instructions="你帮助 Go 开发者准备面试。"
                 "用 search_go_docs 回答事实性问题。"
                 "用 evaluate_code 检查代码提交。",
    tools=[search_go_docs, evaluate_code],
    model="gpt-4o",
)

result = Runner.run_sync(tutor, "写一个用 map 查找切片中重复元素的 Go 函数。")
print(result.final_output)
```

- [ ] **步骤 2：添加护栏（1h）**

添加输入护栏，拒绝非 Go 问题。

- [ ] **步骤 3：添加 Handoff（1h）**

添加 `PythonTutor` Agent。用户问 Python 问题时 handoff 给它，Go 问题留在 GoTutor。

- [ ] **步骤 4：提交**

```bash
git add my_go_tutor.py
git commit -m "learn: 自定义 Agent — 工具、护栏和 handoff"
```

---

## 阶段三：CrewAI — 多 Agent 角色协作（第6天，18小时）

### 任务 3.1：CrewAI 基础（3h）

**文件：**
- 打开：`3_crew/debate/`

> CrewAI 将 Agent 建模为有角色、目标和背景故事的"团队"。类比：每个成员有专门职责的工程团队。

- [ ] **步骤 1：理解 CrewAI 模型（1h）**

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="高级研究员",
    goal="发现突破性洞见",
    backstory="你是有20年经验的资深研究员...",
    tools=[search_tool],
    verbose=True,
)

writer = Agent(
    role="技术作家",
    goal="将研究转化为引人入胜的叙述",
    backstory="你擅长将复杂主题简单化...",
    tools=[],
    verbose=True,
)

research_task = Task(
    description="研究 Go 1.24 泛型最新进展",
    agent=researcher,
    expected_output="详细研究简报",
)

write_task = Task(
    description="基于研究写一篇博客",
    agent=writer,
    expected_output="500字博客文章",
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,  # 任务按顺序执行
)

result = crew.kickoff()
```

Go 类比：这就像在工作流编排中定义服务角色 — researcher 服务 → writer 服务，有明确输入/输出。

- [ ] **步骤 2：运行辩论 Crew（2h）**

```bash
cd 3_crew/debate
uv run crewai run
```

观察：两个持相反观点的 Agent 辩论话题。理解 Role/Goal/Backstory 如何塑造行为。

### 任务 3.2：工程团队（5h）

**文件：**
- 打开：`3_crew/engineering_team/`

- [ ] **步骤 1：分析多角色架构（2h）**

阅读所有文件。识别：
- 有哪些 Agent 及其角色
- 任务管线（哪些任务输入哪些）
- 工具如何在 Agent 间共享/分配

- [ ] **步骤 2：运行工程团队（2h）**

```bash
cd 3_crew/engineering_team
uv run crewai run
```

观察完整管线：需求 → 设计 → 实现 → 审查。

- [ ] **步骤 3：添加新角色（1h）**

添加一个检查代码漏洞的"安全审查员" Agent。将其接入任务管线。

### 任务 3.3：股票分析 + 金融研究 + 代码Agent（7h）

**文件：**
- 打开：`3_crew/stock_picker/`
- 打开：`3_crew/financial_researcher/`
- 打开：`3_crew/coder/`

- [ ] **步骤 1：股票分析（3h）**

运行并分析：`cd 3_crew/stock_picker && uv run crewai run`
要点：Agent 使用金融数据工具、基于角色的分析管线。

- [ ] **步骤 2：金融研究（2h）**

运行并分析：`cd 3_crew/financial_researcher && uv run crewai run`
要点：研究 → 分析 → 报告生成管线。

- [ ] **步骤 3：代码 Agent（2h）**

运行并分析：`cd 3_crew/coder && uv run crewai run`
要点：带角色审查的代码生成。

### 任务 3.4：CrewAI 总结（3h）

- [ ] **步骤 1：CrewAI vs OpenAI Agents SDK 对比（1h）**

| 概念 | OpenAI SDK | CrewAI |
|------|-----------|--------|
| 单Agent | `Agent(name, instructions, tools)` | `Agent(role, goal, backstory, tools)` |
| 多Agent | Handoff（动态路由） | Crew + Tasks（静态管线） |
| 任务定义 | 隐式（用户查询） | 显式 `Task(description, agent, expected_output)` |
| 编排 | LLM决定handoff | `Process.sequential` 或 `Process.hierarchical` |
| 最适合 | 不可预测的对话流 | 结构化多步骤管线 |

- [ ] **步骤 2：何时使用哪个（1h）**

- **OpenAI SDK：** 聊天机器人、客服、对话路径不可预测的任何场景
- **CrewAI：** 研究报告、内容生成、有明确交接的多步骤管线
- **LangGraph（下一章）：** 需要对状态机进行显式控制时
- **AutoGen（后续）：** Agent 需要跨进程分布时

- [ ] **步骤 3：提交**

```bash
git add -A
git commit -m "learn: CrewAI — 基于角色的多Agent团队和任务管线"
```

---

## 阶段四：LangGraph — 状态图编排（第7-8天，36小时）

> LangGraph 将 Agent 工作流建模为有向图。对 Go 工程师来说这是最自然的范式 — 你对状态机和 DAG 有深层理解。

### 任务 4.1：StateGraph 基础（4h）

**文件：**
- 打开：`4_langgraph/1_lab1.ipynb`

- [ ] **步骤 1：理解 StateGraph 模型（2h）**

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # 只追加的列表
    next_step: str

def chatbot(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    return {"messages": [response], "next_step": END}

graph = StateGraph(AgentState)
graph.add_node("chatbot", chatbot)
graph.set_entry_point("chatbot")
graph.add_edge("chatbot", END)
app = graph.compile()

result = app.invoke({"messages": [HumanMessage(content="你好!")]})
```

Go 类比：
```go
type AgentState struct {
    Messages []Message
    NextStep string
}

// StateGraph ≈ 显式状态机
// Node ≈ 处理函数
// Edge ≈ 状态转移
```

- [ ] **步骤 2：执行 Lab 1 所有单元（2h）**

构建越来越复杂的图。理解：
- `StateGraph` 构造
- `add_node(name, function)`
- `add_edge(from, to)` 和 `add_conditional_edges(from, router, path_map)`
- `set_entry_point(name)`
- `compile()` 创建可运行的 app

### 任务 4.2：条件路由 + 循环（6h）

**文件：**
- 打开：`4_langgraph/2_lab2.ipynb`

- [ ] **步骤 1：条件边（3h）**

```python
def router(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if "tool_calls" in last_message:
        return "tools"
    return "end"

graph.add_conditional_edges(
    "agent",
    router,                     # 路由函数
    {"tools": "tool_executor",  # router返回"tools" → 去tool_executor
     "end": END},               # router返回"end" → END
)
```

Go 类比：状态机转移逻辑中的 `switch` 语句。

- [ ] **步骤 2：Agent Loop 在图中的表达（3h）**

Agent Loop（思考→行动→观察）用图表达：

```
START → agent → [router] → tool_executor → agent
                    ↓
                   END
```

这与任务 1.5 中构建的循环相同，但现在是由 LangGraph 编排的声明式图。

执行 Lab 2 所有单元。构建完整的 Agent Loop 图。

### 任务 4.3：人机协作 + 检查点（8h）

**文件：**
- 打开：`4_langgraph/3_lab3.ipynb`

- [ ] **步骤 1：执行前中断（3h）**

```python
graph = StateGraph(AgentState)
# ... 添加节点 ...
graph.compile(interrupt_before=["tool_executor"])  # 在此暂停等待人工批准

# 逐步运行
for event in app.stream(input, config):
    snapshot = app.get_state(config)
    if snapshot.next:  # 图在中断点等待
        user_approval = input("批准工具执行？(y/n): ")
        if user_approval == "y":
            app.invoke(None, config)  # 恢复
```

Go 类比：关键操作前的断路器/手动审批门。

- [ ] **步骤 2：检查点持久化（3h）**

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# 每次调用都被检查点记录
config1 = {"configurable": {"thread_id": "1"}}
app.invoke(input1, config1)
app.invoke(input2, config1)  # 图记住 thread "1" 的过往状态

config2 = {"configurable": {"thread_id": "2"}}
app.invoke(input3, config2)  # 独立的thread，独立的状态
```

Go 类比：事件溯源 — 每个状态转移都被记录，完整历史可回放。

- [ ] **步骤 3：时间旅行（2h）**

```python
# 回退到之前的检查点
previous_state = app.get_state(config).values
# 或从特定检查点重放
for event in app.stream(None, config):
    ...
```

执行 Lab 3 所有单元。

### 任务 4.4：多 Agent LangGraph（8h）

**文件：**
- 打开：`4_langgraph/4_lab4.ipynb`

- [ ] **步骤 1：子图嵌套（4h）**

```python
# 定义子 Agent 为编译后的图
researcher_graph = StateGraph(ResearchState)
# ... 构建 researcher ...
researcher = researcher_graph.compile()

# 在更大的图中作为节点使用
main_graph = StateGraph(MainState)
main_graph.add_node("researcher", researcher)  # 子图作为节点！
main_graph.add_node("writer", writer_node)
main_graph.add_edge("researcher", "writer")
```

Go 类比：服务组合 — 内部使用其他服务的服务。

- [ ] **步骤 2：多 Agent 协调模式（4h）**

执行 Lab 4 所有单元。构建：管理者→工作者模式、并行 Agent 执行、辩论模式。

### 任务 4.5：Sidekick 项目（6h）

**文件：**
- 打开：`4_langgraph/sidekick.py`
- 打开：`4_langgraph/sidekick_tools.py`
- 打开：`4_langgraph/app.py`

- [ ] **步骤 1：阅读并理解所有文件（2h）**

绘制图结构：识别所有节点、边、条件路由、工具。

- [ ] **步骤 2：运行 Sidekick（2h）**

```bash
uv run python 4_langgraph/sidekick.py
```

用各种查询测试。观察图执行路径。

- [ ] **步骤 3：追踪执行（1h）**

针对一个查询，画出图中实际的执行路径。访问了哪些节点？各步骤状态是什么？

- [ ] **步骤 4：修改（1h）**

向图中添加新节点 — 例如在返回用户之前验证输出的"事实核查"节点。

### 任务 4.6：用 LangGraph 重写 Week 2 Agent（4h）

- [ ] **步骤 1：规划图结构（1h）**

将任务 2.6 中的 `my_go_tutor.py` 设计为 LangGraph 图：
```
START → tutor → [router] → search_go_docs → tutor
                    ↓           ↓
                 evaluate ←─────┘
                    ↓
                   END
```

- [ ] **步骤 2：实现图（2h）**

编写 `my_go_tutor_graph.py` 实现上述图。

- [ ] **步骤 3：对比两种实现（1h）**

| 方面 | OpenAI SDK | LangGraph |
|------|-----------|-----------|
| 代码结构 | Agent定义 + Runner | 图定义 + compile |
| 控制流 | 隐式（LLM决定） | 显式（图定义） |
| 可见性 | 事后追踪 | 执行前可见图结构 |
| 调试 | 读追踪 | 逐步执行节点 |
| 灵活性 | 动态路由 | 显式路由 |

- [ ] **步骤 4：提交**

```bash
git add my_go_tutor_graph.py
git commit -m "learn: LangGraph — 多Agent工作流的状态图编排"
```

---

## 阶段五：AutoGen — 分布式 Agent（第8-9天，18小时）

### 任务 5.1：AgentChat 层（4h）

**文件：**
- 打开：`5_autogen/1_lab1_autogen_agentchat.ipynb`

- [ ] **步骤 1：AutoGen 心智模型（1h）**

AutoGen 有两层：
- **AgentChat**（高层）：对话式 Agent、团队、选择器 — 类似 CrewAI
- **Core**（底层）：Topic/Subscription 消息、分布式运行时 — 类似 NATS/Kafka

- [ ] **步骤 2：执行 Lab 1（3h）**

用 AutoGen 的 AgentChat API 构建对话式 Agent。与 CrewAI 的 Agent 模型对比。

### 任务 5.2：多 Agent 团队（5h）

**文件：**
- 打开：`5_autogen/2_lab2_autogen_agentchat.ipynb`

- [ ] **步骤 1：团队模式（2h）**

```python
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat

# RoundRobin：Agent轮流发言
round_robin_team = RoundRobinGroupChat([agent1, agent2])

# Selector：LLM选择下一个发言的Agent
selector_team = SelectorGroupChat([agent1, agent2, agent3],
                                   model_client=llm)
```

- [ ] **步骤 2：执行 Lab 2（3h）**

构建并实验两种团队类型。理解每种模式适合什么场景。

### 任务 5.3：Core 层 — Topic/Subscription（5h）

**文件：**
- 打开：`5_autogen/3_lab3_autogen_core.ipynb`

- [ ] **步骤 1：Topic/Subscription 消息（2h）**

```python
from autogen_core import TopicId, RoutedAgent, message_handler

class AnalystAgent(RoutedAgent):
    @message_handler
    async def handle_query(self, message: Query, ctx):
        result = await self.analyze(message.data)
        await self.publish_message(Result(result), topic_id=TopicId("results"))
```

Go 类比：这字面上就是一个消息队列系统：
- `TopicId` = Kafka topic / NATS subject
- `publish_message` = producer
- `@message_handler` = consumer
- `RoutedAgent` = 订阅 topic 的服务

- [ ] **步骤 2：执行 Lab 3（3h）**

用 Topic/Subscription 构建分布式 Agent 系统。观察 Agent 如何通过消息总线通信而不直接引用彼此。

### 任务 5.4：分布式部署（4h）

**文件：**
- 打开：`5_autogen/4_lab4_autogen_distributed.ipynb`

- [ ] **步骤 1：gRPC 运行时（2h）**

运行在不同进程中的 Agent 通过 gRPC 通信：
```python
# 进程1：宿主Agent运行时
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime

# 进程2：连接到宿主
worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
```

作为 Go 开发者这应该非常熟悉 — gRPC 服务注册和发现。

- [ ] **步骤 2：执行 Lab 4（2h）**

跨多个进程运行分布式 Agent。观察跨进程边界的消息传递。

### 任务 5.5：AutoGen 总结

- [ ] **步骤 1：框架对比矩阵（1h）**

| 维度 | OpenAI SDK | CrewAI | LangGraph | AutoGen |
|------|-----------|--------|-----------|---------|
| 范式 | Agent定义 | Role/Task/Crew | 状态图 | Topic/Subscription |
| 多Agent | 动态handoff | 静态管线 | 图路由 | 消息总线 |
| 分布式 | 否 | 否 | Checkpoint共享 | gRPC原生 |
| 调试 | 追踪 | 详细日志 | 状态快照 | 消息追踪 |
| 最适合 | 对话式AI | 结构化工作流 | 复杂状态管理 | 分布式系统 |

---

## 阶段六：MCP — Model Context Protocol（第9-10天，18小时）

### 任务 6.1：MCP 协议基础（3h）

**文件：**
- 打开：`6_mcp/1_lab1.ipynb`

- [ ] **步骤 1：理解协议（1h）**

MCP 是基于 JSON-RPC 2.0 的 Agent-工具通信协议：
```
Client (Host)                    Server (Tool Provider)
    │                                    │
    ├── initialize ─────────────────────►│
    │◄─ capabilities ────────────────────┤
    │                                    │
    ├── tools/list ─────────────────────►│
    │◄─ [tool1, tool2, ...] ────────────┤
    │                                    │
    ├── tools/call(name, args) ─────────►│
    │◄─ result ──────────────────────────┤
    │                                    │
    ├── resources/read(uri) ────────────►│
    │◄─ content ─────────────────────────┤
```

Go 类比：这是标准化的 gRPC-like 接口定义。把它想成 AI 工具的 protobuf — 所有人约定好消息格式，任何客户端都能与任何服务端通信。

- [ ] **步骤 2：传输机制（1h）**

两种传输方式：
- **stdio**：Server 作为子进程运行，通过 stdin/stdout 通信。类似 Unix 管道。
- **SSE (Server-Sent Events)**：Server 作为 HTTP 端点运行。类似 WebSocket 但是单向。

- [ ] **步骤 3：执行 Lab 1（1h）**

### 任务 6.2：构建 MCP Server（3h）

**文件：**
- 打开：`6_mcp/2_lab2.ipynb`

- [ ] **步骤 1：创建提供工具的 MCP Server（2h）**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("my-tools")

@server.tool()
async def get_time(timezone: str = "UTC") -> str:
    """获取时区当前时间。"""
    import datetime
    return datetime.datetime.now().isoformat()

@server.tool()
async def calculate(expression: str) -> float:
    """计算数学表达式。"""
    return eval(expression)  # 生产环境需清理输入！

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write)
```

- [ ] **步骤 2：执行 Lab 2（1h）**

构建并测试 MCP Server。连接到 MCP Client（Claude Desktop、Cursor 等）。

### 任务 6.3：Resources + Prompts（4h）

**文件：**
- 打开：`6_mcp/3_lab3.ipynb`

- [ ] **步骤 1：Resources — 为 Agent 提供上下文（2h）**

```python
@server.resource("file://documents/{name}")
async def read_document(name: str) -> str:
    """按名称读取文档。"""
    with open(f"docs/{name}") as f:
        return f.read()

@server.resource("database://users/{id}")
async def get_user(id: int) -> dict:
    """从数据库获取用户数据。"""
    return await db.users.find_one(id)
```

Resources 是 Agent 可访问的数据源。Tool 做事情，Resource 提供信息。

- [ ] **步骤 2：Prompts — 模板化交互（2h）**

```python
@server.prompt()
async def code_review(code: str, language: str) -> str:
    return f"""你是一个代码审查者。审查以下 {language} 代码：

```{language}
{code}
```

检查：bug、安全问题、风格问题、性能问题。"""
```

Prompts 是用户可调用的可复用模板。标准化常见的交互模式。

### 任务 6.4：Trading Floor 项目（4h）

**文件：**
- 打开：`6_mcp/4_lab4.ipynb`
- 打开：`6_mcp/` 中所有文件

- [ ] **步骤 1：理解架构（1h）**

Trading Floor 是基于 MCP 的完整多 Agent 系统：
- 多个 MCP Server（行情数据、账户、交易）
- 多种 Agent 类型（不同策略的交易员）
- 中央交易大厅协调

- [ ] **步骤 2：运行 Trading Floor（2h）**

```bash
uv run python 6_mcp/trading_floor.py
```

观察：MCP Server 启动 → Agent 连接 → 交易开始 → Agent 通过 MCP 使用工具。

- [ ] **步骤 3：端到端追踪 MCP 调用（1h）**

选一个 Agent 工具调用并追踪全程：
1. Agent 决定调用工具
2. MCP Client 发送 `tools/call` JSON-RPC 请求
3. MCP Server 接收并执行
4. Server 返回结果
5. Agent 接收结果并继续

### 任务 6.5：远程 MCP + Docker（4h）

**文件：**
- 打开：`6_mcp/5_lab5.ipynb`

- [ ] **步骤 1：远程 MCP Server（2h）**

SSE 传输用于远程访问：
```python
from mcp.server.sse import SseServerTransport

# Server 作为 HTTP 端点运行
# Client 通过 SSE URL 连接
```

- [ ] **步骤 2：Docker 部署（2h）**

容器化 MCP Server：
```dockerfile
FROM python:3.12-slim
COPY server.py .
RUN pip install mcp
CMD ["python", "server.py"]
```

Go 视角：在 Docker 中部署 gRPC 服务 — 同样的模式，不同的协议。

### 任务 6.6：Go 中的 MCP（加分项 — 可选）

- [ ] **步骤 1：了解 Go MCP SDK**

访问 https://github.com/modelcontextprotocol/go-sdk — 有官方的 Go SDK 用于构建 MCP server/client。作为 Go 开发者，这可能是你构建 MCP 服务的首选方式。

- [ ] **步骤 2：提交**

```bash
git add -A
git commit -m "learn: MCP 协议 — 工具、资源、提示模板、远程服务器"
```

---

## 阶段七：综合项目 + 回顾（第10天剩余时间，约18h缓冲）

### 任务 7.1：框架决策矩阵（2h）

- [ ] **步骤 1：创建决策指南**

编写 `~/agent-framework-guide.md`：

```markdown
# 该用哪个 Agent 框架？

## 决策树

1. **单Agent，对话式？** → OpenAI Agents SDK
2. **多Agent，固定管线？** → CrewAI
3. **复杂状态机，分支逻辑？** → LangGraph
4. **分布式Agent，跨进程？** → AutoGen
5. **标准化工具接口？** → 始终用 MCP 构建工具服务

## 框架优劣

| 框架 | 优势 | 劣势 |
|------|------|------|
| OpenAI SDK | 简洁、设计好、追踪完善 | OpenAI中心化（但支持其他模型） |
| CrewAI | 适合固定工作流 | 动态路由灵活性差 |
| LangGraph | 完全控制、检查点、时间旅行 | 样板代码多、学习曲线陡 |
| AutoGen | 分布原生、Topic/Sub模型 | 双API（AgentChat vs Core）易混淆 |
| MCP | 通用协议、跨语言 | 增加基础设施开销 |

## Go 开发者的视角

作为 Go 开发者：
- **OpenAI SDK** 像精心设计的 Go 库 — 最小化、专注、可组合
- **LangGraph** 像状态机库 — 显式、可追踪、可测试
- **MCP** 像 protobuf/gRPC — 标准接口定义
- **CrewAI** 像工作流引擎 — 管线DSL
- **AutoGen** 像 NATS + 微服务 — 消息驱动分布式系统
```

### 任务 7.2：构建综合项目（12h）

- [ ] **步骤 1：选题（1h）**

选择其一：
- **DevOps Agent：** 监控仓库、审查PR、建议修复 — 用 OpenAI SDK + MCP 工具
- **研究管线：** 主题深度研究、多Agent专门分工 — 用 CrewAI
- **客服机器人：** 分诊 → 路由 → 解决、人工升级 — 用 LangGraph
- **分布式数据管线：** 多Agent处理数据流 — 用 AutoGen

- [ ] **步骤 2：设计架构（2h）**

画出 Agent 图 / Crew 结构 / Handoff 链。定义所有工具及其接口。

- [ ] **步骤 3：实现（7h）**

构建。选择最适合用例的框架。

- [ ] **步骤 4：测试和文档（2h）**

跑5个不同场景。记录什么可行、什么不行。

### 任务 7.3：用 Go 构建 MCP Server（4h）

- [ ] **步骤 1：搭建 Go MCP 项目**

```bash
mkdir ~/go-mcp-server
cd ~/go-mcp-server
go mod init go-mcp-server
go get github.com/modelcontextprotocol/go-sdk
```

- [ ] **步骤 2：用 Go 实现同样的工具**

将你的一个 Python MCP 工具移植到 Go。对比开发体验。

- [ ] **步骤 3：连接 Python Client**

测试：Python MCP Client 调用 Go MCP Server → 无缝工作（这就是 MCP 的意义）。

---

## 完成检查清单

全部完成后验证：

- [ ] 能用 OpenAI Agents SDK 构建生产级 Agent（工具、护栏、handoff、追踪）
- [ ] 能用 LangGraph 编排多 Agent 工作流
- [ ] 能对比 CrewAI、AutoGen 和 LangGraph — 并选择正确的框架
- [ ] 能实现暴露工具和资源的 MCP Server
- [ ] 能阅读和扩展任何基于 Python 的 Agent 框架
- [ ] 能给另一个工程师讲清楚 Agent Loop
- [ ] 能用 Go 构建 MCP Server 并连接到任意 MCP Client
