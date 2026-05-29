# 10-Day Agent Development Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Ed Donner's 6-week Agentic AI Engineering course in 10 days (180h), transitioning from Go backend to AI Agent development, starting from zero Python.

**Architecture:** 7-phase waterfall following course progression. Each phase builds on core concepts established in prior phases. Python learned via Go→Python mapping rather than from-scratch. Heavy investment in OpenAI Agents SDK (anchor framework) and LangGraph (control-flow framework).

**Tech Stack:** Python 3.12, uv, Cursor IDE, OpenAI Agents SDK, CrewAI, LangGraph, AutoGen, MCP, Jupyter Notebooks

---

## Pre-Flight: Environment Setup

### Task 0: Environment Bootstrap

**Files:**
- Create: `.env`
- Read: `setup/SETUP-PC.md` (Windows) or `setup/SETUP-linux.md` (Linux)
- Modify: none

- [ ] **Step 1: Fix Windows long path limit (Windows only)**

Open PowerShell as Administrator and run:
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```
Restart computer afterward.

- [ ] **Step 2: Install Microsoft Build Tools (Windows only)**

Download from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
During install, select "Desktop development with C++" workload, then install.
Verify: `where cl` should find the compiler.

- [ ] **Step 3: Install uv package manager**

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux/macOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify: `uv --version`

- [ ] **Step 4: Install Cursor IDE**

Download from https://www.cursor.com/ and install.
Open Cursor, install recommended extensions: Python (ms-python), Jupyter (ms-toolsai.jupyter).

- [ ] **Step 5: Clone repo and sync dependencies**

```bash
cd ~/projects  # or C:\Users\<you>\projects
git clone https://github.com/ed-donner/agents.git
cd agents
uv self update
uv sync
```

Verify:
- `.venv/` directory exists in project root
- `uv python list` shows Python 3.12
- `uv run python -c "import openai; print(openai.__version__)"` works

- [ ] **Step 6: Install CrewAI globally**

```bash
uv tool install crewai==0.130.0 --python 3.12
uv tool upgrade crewai==0.130.0 --python 3.12
```

Verify: `uv tool list` shows crewai

- [ ] **Step 7: Set up OpenAI API key**

1. Go to https://platform.openai.com/api-keys
2. Create new secret key, copy it
3. Create `.env` in project root with content:
```
OPENAI_API_KEY=sk-proj-your_key_here
```

Verify: `uv run python setup/diagnostics.py` — should pass all checks

- [ ] **Step 8: Test Jupyter kernel in Cursor**

1. Open `1_foundations/1_lab1.ipynb` in Cursor
2. Click "Select Kernel" → `.venv (Python 3.12.x)`
3. Run first code cell with Shift+Enter
4. Expected: no errors

- [ ] **Step 9: Commit setup checkpoint**

```bash
git add -A
git commit -m "chore: environment setup complete"
```

---

## Phase 1: Python Bootcamp + Foundations (Day 1-2, 36h)

### Task 1.1: Python Syntax — Go Perspective (4h)

**Files:**
- Open: `guides/06_python_foundations.ipynb`
- Open: `guides/10_intermediate_python.ipynb`

- [ ] **Step 1: Run through Python foundations notebook (2h)**

Execute every cell in `guides/06_python_foundations.ipynb`. For each concept, mentally map to Go:

| Python | Go |
|--------|-----|
| `x: int = 5` (type hint) | `var x int = 5` |
| `def f(a: str) -> str:` | `func f(a string) string` |
| `[x*2 for x in range(10)]` | manual for loop |
| `{"key": "val"}` | `map[string]string{"key": "val"}` |
| `{"a", "b", "c"}` | no built-in set, use `map[T]struct{}` |
| `(1, "hello")` | no tuple, use struct |
| `if __name__ == "__main__":` | `func main()` in `package main` |
| `class Dog(Animal):` | `type Dog struct { Animal }` (embedding) |
| `try/except/finally` | `defer` + `recover` (different model) |

- [ ] **Step 2: Intermediate Python — decorators, generators, context managers (2h)**

Execute every cell in `guides/10_intermediate_python.ipynb`.

Key Go mappings:
- **Decorator** (`@something`) = middleware pattern. Functions wrapping functions.
  ```python
  @retry(max_attempts=3)
  def call_api():
      ...  # retry is a function that takes call_api and returns a wrapped version
  ```
  In Go you'd write: `http.Handle("/path", loggingMiddleware(authMiddleware(handler)))`

- **Generator** (`yield`) = lazy iterator. Closest Go equivalent: channel that yields values one at a time.
- **Context manager** (`with` statement) = `defer` but scoped. `with open("f") as f:` ≈ `f, _ := os.Open("f"); defer f.Close()`

- [ ] **Step 3: Write a Go→Python reference card (30 min)**

Create `~/go-python-cheatsheet.md` with the mappings above plus these patterns:
```markdown
# Go → Python Quick Reference

## Variable declaration
Go:   var name string = "value"
Py:   name: str = "value"

## Function
Go:   func add(a int, b int) int { return a + b }
Py:   def add(a: int, b: int) -> int: return a + b

## Error handling
Go:   if err != nil { return err }
Py:   raise Exception("msg") / try: ... except: ...

## Concurrency
Go:   go func() { ... }()
Py:   asyncio.create_task(async_func())

## Package
Go:   import "fmt"; fmt.Println(x)
Py:   from pathlib import Path; Path("/tmp")

## Struct/Dataclass
Go:   type User struct { Name string; Age int }
Py:   @dataclass
      class User:
          name: str
          age: int

## Interface/Protocol
Go:   type Reader interface { Read([]byte) (int, error) }
Py:   class Reader(Protocol):
          def read(self, size: int) -> bytes: ...

## Run main
Go:   func main() { ... } in package main
Py:   if __name__ == "__main__": main()
```

- [ ] **Step 4: Commit**

```bash
git add ~/go-python-cheatsheet.md
git commit -m "docs: Go→Python reference card"
```

### Task 1.2: Async Python — The Critical Difference (4h)

**Files:**
- Open: `guides/11_async_python.ipynb`

> This is the most important Python concept for an Agent developer. Every Agent framework uses async/await. The mental model is DIFFERENT from goroutines — Python async is single-threaded cooperative multitasking, not preemptive.

- [ ] **Step 1: Understand the event loop model (1h)**

Execute cells in first half of `guides/11_async_python.ipynb`.

Critical difference to internalize:
```
Go goroutines: OS threads + preemptive scheduling
    go foo()  → runs immediately, may run in parallel
    
Python async: Single-thread event loop + cooperative await points
    await foo()  → foo gets queued, runs when current task yields at await
```

**When Python async code actually runs:**
```python
async def fetch(url):
    data = await http_get(url)  # ← yields control HERE only
    return data

# This does NOTHING until you schedule it:
task = asyncio.create_task(fetch("http://example.com"))
# Still might not have run yet — need await to yield:
result = await task  # ← NOW the scheduler gives fetch() CPU time
```

- [ ] **Step 2: Understand asyncio.gather = errgroup (1h)**

Execute remaining cells.

```python
# Python: concurrent execution with gather
async def fetch_all(urls):
    tasks = [asyncio.create_task(fetch(url)) for url in urls]
    results = await asyncio.gather(*tasks)  # ≈ errgroup.Wait()
    return results
```

Go equivalent:
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

- [ ] **Step 3: Understand async generators (2h)**

Async generators are used heavily in streaming Agent responses:
```python
async for chunk in agent.stream_response("query"):
    print(chunk, end="")
```

This is conceptually similar to reading from a channel:
```go
for chunk := range agent.StreamResponse(ctx, "query") {
    fmt.Print(chunk)
}
```

- [ ] **Step 4: Verify understanding**

Write a small async program and run it:
```python
import asyncio
import time

async def worker(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name} done"

async def main():
    start = time.time()
    results = await asyncio.gather(
        worker("A", 1.0),
        worker("B", 0.5),
        worker("C", 1.5),
    )
    elapsed = time.time() - start
    print(f"Results: {results}")
    print(f"Elapsed: {elapsed:.1f}s (should be ~1.5s, not 3.0s)")

asyncio.run(main())
```

Run: `uv run python test_async.py`
Expected: elapsed ~1.5s, proving concurrent execution.

- [ ] **Step 5: Commit**

```bash
git add test_async.py
git commit -m "learn: async/await — concurrent worker pattern"
```

### Task 1.3: CLI, Git, Notebooks, Debugging (4h)

**Files:**
- Open: `guides/02_command_line.ipynb`
- Open: `guides/03_git_and_github.ipynb`
- Open: `guides/05_notebooks.ipynb`
- Open: `guides/08_debugging.ipynb`

- [ ] **Step 1: CLI fundamentals (1h)**

Skim `guides/02_command_line.ipynb`. As a Go developer, you already know these — just note:
- `uv run script.py` instead of `python script.py`
- `uv run pytest` instead of `go test ./...`
- `uv add package` instead of `go get package`

- [ ] **Step 2: Git refresher (1h)**

Skim `guides/03_git_and_github.ipynb`. Confirm workflow: clone → branch → commit → PR.

- [ ] **Step 3: Jupyter notebooks (1h)**

Work through `guides/05_notebooks.ipynb`. Key operations:
- `Shift+Enter`: execute cell and move to next
- `Ctrl+Enter`: execute cell and stay
- `Esc → A`: insert cell above
- `Esc → B`: insert cell below
- `Esc → D D`: delete cell

- [ ] **Step 4: Debugging techniques (1h)**

Work through `guides/08_debugging.ipynb`. Key tools:
- `print()` — always works
- `breakpoint()` — Python's interactive debugger (≈ `dlv` in Go)
- Cursor's debugger — set breakpoints, step through

### Task 1.4: Technical Foundations + APIs (6h)

**Files:**
- Open: `guides/04_technical_foundations.ipynb`
- Open: `guides/09_ai_apis_and_ollama.ipynb`

- [ ] **Step 1: Technical foundations (3h)**

Execute all cells in `guides/04_technical_foundations.ipynb`. Key concepts:
- Environment variables (`.env` file, `os.getenv()`, `load_dotenv()`)
- HTTP/HTTPS basics (requests library ≈ `net/http` in Go)
- REST APIs (GET/POST, headers, JSON body)
- Authentication (API keys, Bearer tokens)

- [ ] **Step 2: AI APIs and Ollama (3h)**

Execute all cells in `guides/09_ai_apis_and_ollama.ipynb`. Key concepts:
- OpenAI chat completion API format
- Anthropic messages API format
- Running local models with Ollama (free alternative to paid APIs)
- Token usage tracking and cost management

- [ ] **Step 3: Practice API call (self-directed)**

Write a Python script that calls OpenAI:
```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",  # cheapest model for practice
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain goroutines to a Python developer in 3 sentences."},
    ],
)
print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
```

Run: `uv run python test_api.py`
Expected: 3-sentence explanation + token count.

- [ ] **Step 4: Commit**

```bash
git add test_api.py
git commit -m "learn: OpenAI API basics — chat completion"
```

### Task 1.5: Week 1 Labs — The Agent Loop (10h)

**Files:**
- Open: `1_foundations/1_lab1.ipynb`
- Open: `1_foundations/2_lab2.ipynb`
- Open: `1_foundations/3_lab3.ipynb`
- Open: `1_foundations/4_lab4.ipynb`
- Open: `1_foundations/5_extra.ipynb`

- [ ] **Step 1: Lab 1 — First LLM Call (2h)**

Execute all cells in `1_foundations/1_lab1.ipynb`. Understand:
- The `messages` list format: `[{"role": "system/user/assistant", "content": "..."}]`
- Temperature parameter (0=deterministic, 1=creative)
- The chat completion response object

After completing: you can call an LLM from code.

- [ ] **Step 2: Lab 2 — System Prompts (2h)**

Execute all cells in `1_foundations/2_lab2.ipynb`. Understand:
- System prompt shapes agent personality and behavior
- Prompt engineering: be specific, give examples, set constraints
- Different models respond differently to the same prompt

After completing: you can design an agent's personality.

- [ ] **Step 3: Lab 3 — Tool Calling (3h)** *CRITICAL*

Execute all cells in `1_foundations/3_lab3.ipynb`. This is THE most important concept.

**The fundamental pattern:**
```python
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # actual implementation
    return f"Weather in {city}: 22°C, sunny"

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }
    }
}]

# LLM decides WHEN to call the tool and with WHAT args
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
)
# response may contain a tool_call instead of text
```

Go perspective: this is like the LLM dynamically picking which function to call — no `switch` statement needed.

After completing: you understand how agents use tools.

- [ ] **Step 4: Lab 4 — Agent Loop (2h)** *CRITICAL*

Execute all cells in `1_foundations/4_lab4.ipynb`.

**The complete Agent Loop pattern (memorize this):**
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
    
    if msg.tool_calls:                    # LLM wants to use a tool
        messages.append(msg)              # Add assistant's tool_call to history
        for tool_call in msg.tool_calls:
            result = execute_tool(tool_call.function.name, 
                                  json.loads(tool_call.function.arguments))
            messages.append({             # Add tool result to history
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })
    else:                                  # LLM is done
        messages.append({"role": "assistant", "content": msg.content})
        break

return msg.content
```

This is the foundation of EVERY agent framework you'll learn in this course.

- [ ] **Step 5: Extra lab (1h)**

Execute all cells in `1_foundations/5_extra.ipynb`. Consolidates Labs 1-4 into a complete mini-agent.

- [ ] **Step 6: Self-check — rebuild agent loop from scratch**

Close all notebooks. Write a new `.py` file that:
1. Takes a user question from `input()`
2. Has a `calculate(expression: str) -> float` tool
3. Runs the agent loop, calling the tool when needed
4. Prints the final answer

Run: `uv run python my_first_agent.py`
Enter: "What is 15 * 23 plus 100?"
Expected: correct answer via tool call.

- [ ] **Step 7: Commit**

```bash
git add my_first_agent.py
git commit -m "learn: complete agent loop — think→act→observe→repeat"
```

---

## Phase 2: OpenAI Agents SDK (Day 3-5, 36h)

> This is your anchor framework. Master it the way you mastered `net/http`. Every other framework is just a different wrapper around these concepts.

### Task 2.1: First SDK Agent (4h)

**Files:**
- Open: `2_openai/1_lab1.ipynb`

- [ ] **Step 1: Understand the SDK abstraction (1h)**

The OpenAI Agents SDK wraps the raw API into higher-level primitives:

```python
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    model="gpt-4o",
)

result = Runner.run_sync(agent, "What is the capital of France?")
print(result.final_output)
```

Compare to the raw agent loop you wrote in Task 1.5 — the SDK does the loop, tool execution, and message management for you.

- [ ] **Step 2: Execute all cells in Lab 1 (3h)**

Work through every cell. Understand:
- `Agent` — the core abstraction (name, instructions, model, tools, handoffs)
- `Runner.run_sync()` vs `Runner.run()` (sync vs async)
- `RunResult` — final_output, new_items, last_agent
- `RunConfig` — workflow_name, trace_id, etc.

### Task 2.2: Tools Deep Dive (6h)

**Files:**
- Open: `2_openai/2_lab2.ipynb`

- [ ] **Step 1: Function tools (2h)**

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # In production, call a real weather API
    return f"Weather in {city}: 22°C, sunny"

agent = Agent(
    name="Weather Bot",
    instructions="You help users check weather.",
    tools=[get_weather],
)
```

The `@function_tool` decorator auto-generates the JSON schema from the function signature + docstring. In raw API, you had to write it manually (Task 1.5 Step 3).

- [ ] **Step 2: Hosted tools (1h)**

SDK provides pre-built tools:
```python
from agents.extensions.tools import WebSearchTool, FileSearchTool
```

- [ ] **Step 3: Custom tool classes (2h)**

When tools need state:
```python
from agents import Tool

class DatabaseTool(Tool):
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def __call__(self, query: str) -> str:
        result = await self.db.execute(query)
        return str(result)
```

- [ ] **Step 4: Tool error handling (1h)**

Tools can fail. The SDK handles this:
```python
@function_tool
def risky_tool(param: str) -> str:
    try:
        return do_thing(param)
    except Exception as e:
        return f"Error: {e}"  # LLM sees this and can retry differently
```

### Task 2.3: Handoffs — Agent-to-Agent Delegation (8h)

**Files:**
- Open: `2_openai/3_lab3.ipynb`

- [ ] **Step 1: Understand handoff concept (2h)**

Handoff is the SDK's mechanism for one agent delegating to another. Go analogy: a load balancer routing to specialized microservices.

```python
from agents import Agent, handoff

billing_agent = Agent(
    name="Billing",
    instructions="You handle billing questions.",
    tools=[lookup_invoice, process_refund],
)

support_agent = Agent(
    name="Support",
    instructions="You handle general support. Handoff billing to Billing agent.",
    handoffs=[handoff(billing_agent)],  # Can delegate to billing
)
```

When the user asks a billing question, `support_agent` automatically hands off to `billing_agent`. The user sees a seamless experience, but internally, a different agent with different tools took over.

- [ ] **Step 2: Handoff with filters (2h)**

Control when handoffs trigger:
```python
handoff(
    billing_agent,
    input_filter=lambda history: history[-1]["content"],  # What to pass
)
```

- [ ] **Step 3: Multi-agent chains (2h)**

```python
triage = Agent(name="Triage", handoffs=[handoff(support), handoff(sales)])
support = Agent(name="Support", handoffs=[handoff(billing), handoff(technical)])
billing = Agent(name="Billing", tools=[...])
technical = Agent(name="Technical", tools=[...])
```

This forms a delegation graph — but it's dynamic (LLM decides when to hand off), not static like a DAG.

- [ ] **Step 4: Execute all cells in Lab 3 (2h)**

Build the full handoff chain from the notebook. Experiment with multi-turn conversations that trigger multiple handoffs.

### Task 2.4: Guardrails + Tracing (8h)

**Files:**
- Open: `2_openai/4_lab4.ipynb`

- [ ] **Step 1: Input guardrails (2h)**

```python
from agents import Agent, Runner, input_guardrail
from pydantic import BaseModel

class ContentCheck(BaseModel):
    is_harmful: bool
    reasoning: str

@input_guardrail
async def no_harmful_content(context, agent, input):
    result = await check_harmfulness(input)
    return result  # True = block, False = allow

agent = Agent(
    name="Safe Agent",
    instructions="...",
    input_guardrails=[no_harmful_content],
)
```

Go analogy: HTTP middleware that validates request body before the handler runs.

- [ ] **Step 2: Output guardrails (2h)**

Same pattern but runs on agent output:
```python
@output_guardrail
async def check_factual_accuracy(context, agent, output):
    ...
```

- [ ] **Step 3: Tracing (2h)**

The SDK automatically traces every agent run:
```python
from agents import trace

with trace("My Workflow"):
    result = Runner.run_sync(agent, "query")
    # Every step is recorded: LLM calls, tool executions, handoffs
```

Go analogy: OpenTelemetry spans. Traces show the full execution tree.

- [ ] **Step 4: Execute all cells in Lab 4 (2h)**

Complete the notebook, experimenting with guardrails that block/allows various inputs.

### Task 2.5: Deep Research Project (6h)

**Files:**
- Open: `2_openai/deep_research/`

- [ ] **Step 1: Read and understand the full project (2h)**

Read every file in `2_openai/deep_research/`. This is a production-quality agent that:
- Takes a research question
- Searches the web
- Synthesizes findings
- Produces a structured report

- [ ] **Step 2: Run the deep research agent (2h)**

```bash
uv run python 2_openai/deep_research/main.py
```

Test with: "What are the key differences between Go's concurrency model and Python's asyncio?"

- [ ] **Step 3: Trace the execution (1h)**

Look at the trace output. Identify each: LLM call → tool call → handoff → final output.

- [ ] **Step 4: Modify (1h)**

Add a new capability — e.g., add a tool that can read local files to include in research.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "learn: OpenAI Agents SDK — tools, handoffs, guardrails, tracing"
```

### Task 2.6: Self-Directed Practice (4h)

- [ ] **Step 1: Build a Go-interview-prep agent (2h)**

Create `my_go_tutor.py`:
```python
from agents import Agent, Runner, function_tool

@function_tool
def search_go_docs(query: str) -> str:
    """Search Go documentation (mocked for now)."""
    return f"Results for '{query}': ..."

@function_tool  
def evaluate_code(code: str) -> str:
    """Evaluate Go code for correctness."""
    # In production, run go build/go vet
    return "Code looks good, no syntax errors."

tutor = Agent(
    name="Go Tutor",
    instructions="You help Go developers prepare for interviews. "
                 "Use search_go_docs for factual questions. "
                 "Use evaluate_code to check code submissions.",
    tools=[search_go_docs, evaluate_code],
    model="gpt-4o",
)

result = Runner.run_sync(tutor, "Write a Go function that finds duplicates in a slice using a map.")
print(result.final_output)
```

- [ ] **Step 2: Add guardrails (1h)**

Add input guardrail that rejects non-Go questions.

- [ ] **Step 3: Add a handoff (1h)**

Add a `PythonTutor` agent. When the user asks a Python question, handoff to it. When Go, stay on GoTutor.

- [ ] **Step 4: Commit**

```bash
git add my_go_tutor.py
git commit -m "learn: custom agent with tools, guardrails, and handoffs"
```

---

## Phase 3: CrewAI — Multi-Agent Roles (Day 6, 18h)

### Task 3.1: CrewAI Fundamentals (3h)

**Files:**
- Open: `3_crew/debate/`

> CrewAI models agents as a "crew" with defined roles, goals, and backstories. Analogy: an engineering team where each member has a specialized role.

- [ ] **Step 1: Understand the CrewAI model (1h)**

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Senior Researcher",
    goal="Uncover groundbreaking insights",
    backstory="You are a veteran researcher with 20 years of experience...",
    tools=[search_tool],
    verbose=True,
)

writer = Agent(
    role="Tech Writer",
    goal="Craft compelling narratives from research",
    backstory="You excel at simplifying complex topics...",
    tools=[],
    verbose=True,
)

research_task = Task(
    description="Research the latest in Go 1.24 generics",
    agent=researcher,
    expected_output="A detailed research brief",
)

write_task = Task(
    description="Write a blog post from the research",
    agent=writer,
    expected_output="A 500-word blog post",
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,  # Tasks run in order
)

result = crew.kickoff()
```

Go analogy: This is like defining service roles in a workflow orchestration — researcher service → writer service, with defined inputs/outputs.

- [ ] **Step 2: Run the debate crew (2h)**

```bash
cd 3_crew/debate
uv run crewai run
```

Observe: two agents with opposing views debate a topic. Understand how Role/Goal/Backstory shape behavior.

### Task 3.2: Engineering Team (5h)

**Files:**
- Open: `3_crew/engineering_team/`

- [ ] **Step 1: Analyze the multi-role architecture (2h)**

Read all files. Identify:
- Which agents exist and their roles
- The task pipeline (which tasks feed into which)
- How tools are shared/distributed among agents

- [ ] **Step 2: Run the engineering team (2h)**

```bash
cd 3_crew/engineering_team
uv run crewai run
```

Observe the complete pipeline: requirements → design → implementation → review.

- [ ] **Step 3: Add a new role (1h)**

Add a "Security Reviewer" agent that checks code for vulnerabilities. Hook it into the task pipeline.

### Task 3.3: Stock Picker + Financial Researcher (7h)

**Files:**
- Open: `3_crew/stock_picker/`
- Open: `3_crew/financial_researcher/`
- Open: `3_crew/coder/`

- [ ] **Step 1: Stock Picker (3h)**

Run and analyze: `cd 3_crew/stock_picker && uv run crewai run`
Key learning: agents using financial data tools, role-based analysis pipeline.

- [ ] **Step 2: Financial Researcher (2h)**

Run and analyze: `cd 3_crew/financial_researcher && uv run crewai run`
Key learning: research → analysis → report generation pipeline.

- [ ] **Step 3: Coder Agent (2h)**

Run and analyze: `cd 3_crew/coder && uv run crewai run`
Key learning: code generation with role-based review.

### Task 3.4: CrewAI Summary (3h)

- [ ] **Step 1: Compare CrewAI to OpenAI Agents SDK (1h)**

| Concept | OpenAI SDK | CrewAI |
|---------|------------|--------|
| Single agent | `Agent(name, instructions, tools)` | `Agent(role, goal, backstory, tools)` |
| Multi-agent | Handoffs (dynamic routing) | Crew + Tasks (static pipeline) |
| Task definition | Implicit (user query) | Explicit `Task(description, agent, expected_output)` |
| Orchestration | LLM decides handoffs | `Process.sequential` or `Process.hierarchical` |
| Best for | Unpredictable, conversational flows | Structured multi-step pipelines |

- [ ] **Step 2: When to use which (1h)**

- **OpenAI SDK:** Chatbots, customer support, any agent where the conversation path is unpredictable
- **CrewAI:** Research reports, content generation, any multi-step pipeline with clear handoffs
- **LangGraph (next):** When you need explicit control over the state machine
- **AutoGen (later):** When agents need to be distributed across processes

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "learn: CrewAI — role-based multi-agent crews and task pipelines"
```

---

## Phase 4: LangGraph — State Graph Orchestration (Day 7-8, 36h)

> LangGraph models agent workflows as directed graphs. For a Go engineer, this is the most natural paradigm — you understand state machines and DAGs deeply.

### Task 4.1: StateGraph Fundamentals (4h)

**Files:**
- Open: `4_langgraph/1_lab1.ipynb`

- [ ] **Step 1: Understand the StateGraph model (2h)**

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # Append-only list
    next_step: str

def chatbot(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    return {"messages": [response], "next_step": END}

graph = StateGraph(AgentState)
graph.add_node("chatbot", chatbot)
graph.set_entry_point("chatbot")
graph.add_edge("chatbot", END)
app = graph.compile()

result = app.invoke({"messages": [HumanMessage(content="Hello!")]})
```

Go analogy:
```go
type AgentState struct {
    Messages []Message
    NextStep string
}

// StateGraph ≈ explicit state machine
// Node ≈ handler function
// Edge ≈ state transition
```

- [ ] **Step 2: Execute all cells in Lab 1 (2h)**

Build increasingly complex graphs. Understand:
- `StateGraph` construction
- `add_node(name, function)`
- `add_edge(from, to)` and `add_conditional_edges(from, router, path_map)`
- `set_entry_point(name)`
- `compile()` to create the runnable app

### Task 4.2: Conditional Routing + Cycles (6h)

**Files:**
- Open: `4_langgraph/2_lab2.ipynb`

- [ ] **Step 1: Conditional edges (3h)**

```python
def router(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if "tool_calls" in last_message:
        return "tools"
    return "end"

graph.add_conditional_edges(
    "agent",
    router,                     # Router function
    {"tools": "tool_executor",  # If router returns "tools" → go to tool_executor
     "end": END},               # If router returns "end" → END
)
```

Go analogy: This is a `switch` statement in the state machine transition logic.

- [ ] **Step 2: Agent loop as a graph (3h)**

The agent loop (think→act→observe) expressed as a graph:

```
START → agent → [router] → tool_executor → agent
                    ↓
                   END
```

This is the same loop you built in Task 1.5, but now it's a declarative graph that LangGraph orchestrates.

Execute all cells in Lab 2. Build the full agent loop graph.

### Task 4.3: Human-in-the-Loop + Checkpoints (8h)

**Files:**
- Open: `4_langgraph/3_lab3.ipynb`

- [ ] **Step 1: Interrupt before execution (3h)**

```python
graph = StateGraph(AgentState)
# ... add nodes ...
graph.compile(interrupt_before=["tool_executor"])  # Pause here for human approval

# Run step by step
for event in app.stream(input, config):
    snapshot = app.get_state(config)
    if snapshot.next:  # Graph is waiting at an interrupt point
        user_approval = input("Approve tool execution? (y/n): ")
        if user_approval == "y":
            app.invoke(None, config)  # Resume
```

Go analogy: circuit breaker / manual approval gate before a critical operation.

- [ ] **Step 2: Checkpoint persistence (3h)**

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# Each invocation is checkpointed
config1 = {"configurable": {"thread_id": "1"}}
app.invoke(input1, config1)
app.invoke(input2, config1)  # Graph remembers past state for thread "1"

config2 = {"configurable": {"thread_id": "2"}}
app.invoke(input3, config2)  # Separate thread, separate state
```

Go analogy: event sourcing — each state transition is recorded, the full history is replayable.

- [ ] **Step 3: Time travel (2h)**

```python
# Rewind to a previous checkpoint
previous_state = app.get_state(config).values
# Or replay from a specific checkpoint
for event in app.stream(None, config):
    ...
```

Execute all cells in Lab 3.

### Task 4.4: Multi-Agent LangGraph (8h)

**Files:**
- Open: `4_langgraph/4_lab4.ipynb`

- [ ] **Step 1: Subgraph nesting (4h)**

```python
# Define a sub-agent as a compiled graph
researcher_graph = StateGraph(ResearchState)
# ... build researcher ...
researcher = researcher_graph.compile()

# Use it as a node in a larger graph
main_graph = StateGraph(MainState)
main_graph.add_node("researcher", researcher)  # Subgraph as a node!
main_graph.add_node("writer", writer_node)
main_graph.add_edge("researcher", "writer")
```

Go analogy: composing services — a service that internally uses other services.

- [ ] **Step 2: Multi-agent coordination patterns (4h)**

Execute all cells in Lab 4. Build: supervisor → worker pattern, parallel agent execution, debate pattern.

### Task 4.5: Sidekick Project (6h)

**Files:**
- Open: `4_langgraph/sidekick.py`
- Open: `4_langgraph/sidekick_tools.py`
- Open: `4_langgraph/app.py`

- [ ] **Step 1: Read and understand all files (2h)**

Map the graph structure: identify all nodes, edges, conditional routes, tools.

- [ ] **Step 2: Run the sidekick (2h)**

```bash
uv run python 4_langgraph/sidekick.py
```

Test with various queries. Observe the graph execution path.

- [ ] **Step 3: Trace the execution (1h)**

For one query, draw the actual execution path through the graph. Which nodes were visited? What was the state at each step?

- [ ] **Step 4: Modify (1h)**

Add a new node to the graph — e.g., a "fact checker" node that verifies output before returning to user.

### Task 4.6: Rewrite Week 2 Agent in LangGraph (4h)

- [ ] **Step 1: Plan the graph (1h)**

Take your `my_go_tutor.py` from Task 2.6. Design it as a LangGraph graph:
```
START → tutor → [router] → search_go_docs → tutor
                    ↓           ↓
                 evaluate ←────┘
                    ↓
                   END
```

- [ ] **Step 2: Implement the graph (2h)**

Write `my_go_tutor_graph.py` implementing the above graph.

- [ ] **Step 3: Compare the two implementations (1h)**

| Aspect | OpenAI SDK | LangGraph |
|--------|-----------|-----------|
| Code structure | Agent definition + Runner | Graph definition + compile |
| Control flow | Implicit (LLM decides) | Explicit (graph defines it) |
| Visibility | Trace after the fact | Graph visible before execution |
| Debugging | Read traces | Step through nodes |
| Flexibility | Dynamic routing | Explicit routing |

- [ ] **Step 4: Commit**

```bash
git add my_go_tutor_graph.py
git commit -m "learn: LangGraph — state graph orchestration of multi-agent workflows"
```

---

## Phase 5: AutoGen — Distributed Agents (Day 8-9, 18h)

### Task 5.1: AgentChat Layer (4h)

**Files:**
- Open: `5_autogen/1_lab1_autogen_agentchat.ipynb`

- [ ] **Step 1: AutoGen's mental model (1h)**

AutoGen has two layers:
- **AgentChat** (high-level): conversational agents, teams, selectors — like CrewAI
- **Core** (low-level): Topic/Subscription messaging, distributed runtime — like NATS/Kafka

- [ ] **Step 2: Execute Lab 1 (3h)**

Build conversational agents with AutoGen's AgentChat API. Compare to CrewAI's Agent model.

### Task 5.2: Multi-Agent Teams (5h)

**Files:**
- Open: `5_autogen/2_lab2_autogen_agentchat.ipynb`

- [ ] **Step 1: Team patterns (2h)**

```python
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat

# RoundRobin: agents take turns
round_robin_team = RoundRobinGroupChat([agent1, agent2])

# Selector: LLM chooses which agent speaks next
selector_team = SelectorGroupChat([agent1, agent2, agent3],
                                   model_client=llm)
```

- [ ] **Step 2: Execute Lab 2 (3h)**

Build and experiment with both team types. Understand when each pattern is appropriate.

### Task 5.3: Core Layer — Topic/Subscription (5h)

**Files:**
- Open: `5_autogen/3_lab3_autogen_core.ipynb`

- [ ] **Step 1: Topic/Subscription messaging (2h)**

```python
from autogen_core import TopicId, RoutedAgent, message_handler

class AnalystAgent(RoutedAgent):
    @message_handler
    async def handle_query(self, message: Query, ctx):
        result = await self.analyze(message.data)
        await self.publish_message(Result(result), topic_id=TopicId("results"))
```

Go analogy: This is literally a message queue system:
- `TopicId` = Kafka topic / NATS subject
- `publish_message` = producer
- `@message_handler` = consumer
- `RoutedAgent` = service that subscribes to topics

- [ ] **Step 2: Execute Lab 3 (3h)**

Build a distributed agent system using Topic/Subscription. Observe how agents communicate through the message bus without direct references to each other.

### Task 5.4: Distributed Deployment (4h)

**Files:**
- Open: `5_autogen/4_lab4_autogen_distributed.ipynb`

- [ ] **Step 1: gRPC runtime (2h)**

Agents running in different processes communicate via gRPC:
```python
# Process 1: host agent runtime
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime

# Process 2: connect to host
worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")
```

This should feel very familiar as a Go developer — gRPC service registration and discovery.

- [ ] **Step 2: Execute Lab 4 (2h)**

Run distributed agents across multiple processes. Observe message passing across process boundaries.

### Task 5.5: AutoGen Summary

- [ ] **Step 1: Framework comparison matrix (1h)**

| Dimension | OpenAI SDK | CrewAI | LangGraph | AutoGen |
|-----------|-----------|--------|-----------|---------|
| Paradigm | Agent definition | Role/Task/Crew | State Graph | Topic/Subscription |
| Multi-agent | Dynamic handoff | Static pipeline | Graph routing | Message bus |
| Distribution | No | No | Checkpoint share | gRPC native |
| Debugging | Traces | Verbose logs | State snapshots | Message traces |
| Best for | Conversational AI | Structured workflows | Complex state mgmt | Distributed systems |

---

## Phase 6: MCP — Model Context Protocol (Day 9-10, 18h)

### Task 6.1: MCP Protocol Fundamentals (3h)

**Files:**
- Open: `6_mcp/1_lab1.ipynb`

- [ ] **Step 1: Understand the protocol (1h)**

MCP is a JSON-RPC 2.0 protocol for agent-tool communication:
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

Go analogy: This is a standardized gRPC-like interface definition. Think of it as protobuf for AI tools — everyone agrees on the message format, so any client can talk to any server.

- [ ] **Step 2: Transport mechanisms (1h)**

Two transports:
- **stdio**: Server runs as subprocess, communicates via stdin/stdout. Like a Unix pipe.
- **SSE (Server-Sent Events)**: Server runs as HTTP endpoint. Like WebSocket but unidirectional.

- [ ] **Step 3: Execute Lab 1 (1h)**

### Task 6.2: Build an MCP Server (3h)

**Files:**
- Open: `6_mcp/2_lab2.ipynb`

- [ ] **Step 1: Create a tool-providing MCP server (2h)**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("my-tools")

@server.tool()
async def get_time(timezone: str = "UTC") -> str:
    """Get the current time in a timezone."""
    import datetime
    return datetime.datetime.now().isoformat()

@server.tool()
async def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)  # sanitize in production!

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write)
```

- [ ] **Step 2: Execute Lab 2 (1h)**

Build and test the MCP server. Connect it to an MCP client (Claude Desktop, Cursor, etc.).

### Task 6.3: Resources + Prompts (4h)

**Files:**
- Open: `6_mcp/3_lab3.ipynb`

- [ ] **Step 1: Resources — giving agents context (2h)**

```python
@server.resource("file://documents/{name}")
async def read_document(name: str) -> str:
    """Read a document by name."""
    with open(f"docs/{name}") as f:
        return f.read()

@server.resource("database://users/{id}")
async def get_user(id: int) -> dict:
    """Get user data from database."""
    return await db.users.find_one(id)
```

Resources are data sources the agent can access. Tools do things, resources provide information.

- [ ] **Step 2: Prompts — templated interactions (2h)**

```python
@server.prompt()
async def code_review(code: str, language: str) -> str:
    return f"""You are a code reviewer. Review this {language} code:

```{language}
{code}
```

Check for: bugs, security issues, style problems, performance issues."""
```

Prompts are reusable templates that users can invoke. They standardize common interaction patterns.

### Task 6.4: Trading Floor Project (4h)

**Files:**
- Open: `6_mcp/4_lab4.ipynb`
- Open: All files in `6_mcp/`

- [ ] **Step 1: Understand the architecture (1h)**

The Trading Floor is a full MCP-based multi-agent system:
- Multiple MCP servers (market data, accounts, trading)
- Multiple agent types (traders with different strategies)
- Central trading floor that coordinates

- [ ] **Step 2: Run the trading floor (2h)**

```bash
uv run python 6_mcp/trading_floor.py
```

Observe: MCP servers start → agents connect → trading begins → agents use tools via MCP.

- [ ] **Step 3: Trace an MCP call end-to-end (1h)**

Pick one agent tool call and trace it:
1. Agent decides to call tool
2. MCP client sends `tools/call` JSON-RPC request
3. MCP server receives and executes
4. Server returns result
5. Agent receives result and continues

### Task 6.5: Remote MCP + Docker (4h)

**Files:**
- Open: `6_mcp/5_lab5.ipynb`

- [ ] **Step 1: Remote MCP server (2h)**

SSE transport for remote access:
```python
from mcp.server.sse import SseServerTransport

# Server runs as HTTP endpoint
# Clients connect via SSE URL
```

- [ ] **Step 2: Docker deployment (2h)**

Containerize an MCP server:
```dockerfile
FROM python:3.12-slim
COPY server.py .
RUN pip install mcp
CMD ["python", "server.py"]
```

Go perspective: this is deploying a gRPC service in Docker — same pattern, different protocol.

### Task 6.6: MCP in Go (Bonus — optional)

- [ ] **Step 1: Check Go MCP SDK**

Visit https://github.com/modelcontextprotocol/go-sdk — there's an official Go SDK for building MCP servers/clients. As a Go developer, this may be your preferred way to build MCP services.

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "learn: MCP protocol — tools, resources, prompts, remote servers"
```

---

## Phase 7: Capstone + Review (Day 10 remaining hours, ~18h buffer)

### Task 7.1: Framework Decision Matrix (2h)

- [ ] **Step 1: Create a decision guide**

Write `~/agent-framework-guide.md`:

```markdown
# Which Agent Framework Should I Use?

## Decision Tree

1. **Single agent, conversational?** → OpenAI Agents SDK
2. **Multi-agent with defined pipeline?** → CrewAI
3. **Complex state machine, branching logic?** → LangGraph
4. **Distributed agents across processes?** → AutoGen
5. **Standardized tool interface?** → Always use MCP for tool servers

## Framework Strengths

| Framework | Strengths | Weaknesses |
|-----------|-----------|------------|
| OpenAI SDK | Simple, well-designed, good tracing | OpenAI-centric (though supports other models) |
| CrewAI | Great for defined workflows | Less flexible for dynamic routing |
| LangGraph | Full control, checkpoints, time travel | More boilerplate, steeper learning curve |
| AutoGen | Distributed-native, Topic/Sub model | Two APIs (AgentChat vs Core) can confuse |
| MCP | Universal protocol, any language | Adds infrastructure overhead |

## My Go Perspective

As a Go developer:
- **OpenAI SDK** feels like a well-designed Go library — minimal, focused, composable
- **LangGraph** feels like a state machine library — explicit, traceable, testable
- **MCP** feels like protobuf/gRPC — standard interface definition
- **CrewAI** feels like a workflow engine — pipeline DSL
- **AutoGen** feels like NATS + microservices — message-driven distributed system
```

### Task 7.2: Build a Capstone Project (12h)

- [ ] **Step 1: Pick a project (1h)**

Choose one:
- **DevOps Agent:** Monitors a repo, reviews PRs, suggests fixes — use OpenAI SDK + MCP tools
- **Research Pipeline:** Deep research on a topic, multiple agents with specialized roles — use CrewAI
- **Customer Support Bot:** Triage → route → resolve, with human escalation — use LangGraph
- **Distributed Data Pipeline:** Multiple agents processing data streams — use AutoGen

- [ ] **Step 2: Design the architecture (2h)**

Draw the agent graph / crew structure / handoff chain. Define all tools and their interfaces.

- [ ] **Step 3: Implement (7h)**

Build it. Use the framework that best fits the use case.

- [ ] **Step 4: Test and document (2h)**

Run through 5 different scenarios. Document what works and what doesn't.

### Task 7.3: Go Back and Build an MCP Server in Go (4h)

- [ ] **Step 1: Set up Go MCP project**

```bash
mkdir ~/go-mcp-server
cd ~/go-mcp-server
go mod init go-mcp-server
go get github.com/modelcontextprotocol/go-sdk
```

- [ ] **Step 2: Implement the same tools in Go**

Port one of your Python MCP tools to Go. Compare the experience.

- [ ] **Step 3: Connect to Python client**

Test: Python MCP client calls Go MCP server → works seamlessly (that's the point of MCP).

---

## Success Checklist

After completing all tasks, verify:

- [ ] Can build a production agent with OpenAI Agents SDK (tools, guardrails, handoffs, tracing)
- [ ] Can orchestrate multi-agent workflows with LangGraph
- [ ] Can compare CrewAI, AutoGen, and LangGraph — and pick the right one
- [ ] Can implement an MCP server exposing tools and resources
- [ ] Can read and extend any Python-based agent framework
- [ ] Can explain the Agent Loop to another engineer
- [ ] Can build an MCP server in Go and connect it to any MCP client
