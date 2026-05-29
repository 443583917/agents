# 10-Day Agent Development Intensive Learning Plan

## Context

- **Learner:** Backend engineer with Go expertise, no Python background
- **Goal:** Transition from Go backend to AI Agent development
- **Time budget:** 10 days × 18h/day = 180 hours
- **Course:** Ed Donner's 6-week Agentic AI Engineering (OpenAI SDK, CrewAI, LangGraph, AutoGen, MCP)

## Architecture: 7-Phase Waterfall

The course is inherently progressive — each week builds on prior concepts. Full coverage in 180h is achievable with disciplined time-boxing.

```
Phase 1 (36h)  → Python Bootcamp + Week 1 Foundations
Phase 2 (36h)  → Week 2: OpenAI Agents SDK (anchor framework)
Phase 3 (18h)  → Week 3: CrewAI Multi-Agent Roles
Phase 4 (36h)  → Week 4: LangGraph State Graph Orchestration
Phase 5 (18h)  → Week 5: AutoGen Distributed Agents
Phase 6 (18h)  → Week 6: MCP Protocol
Phase 7 (18h)  → Buffer / Review / Deep Dive
```

## Phase 1: Python Bootcamp + Foundations (Day 1-2, 36h)

### Learning strategy: Go→Python mapping, not Python-from-scratch

The learner already understands programming. Focus on syntax mapping, async model differences, and Python ecosystem tooling.

### Essential Go→Python mapping

| Go Concept | Python Equivalent |
|------------|-------------------|
| goroutine | asyncio.create_task() |
| channel | asyncio.Queue |
| errgroup | asyncio.gather() |
| interface | Protocol / duck typing |
| struct | dataclass / pydantic.BaseModel |
| defer | try/finally / contextlib |
| go mod / go.sum | uv / pyproject.toml / uv.lock |
| nil | None |

### Schedule

| Block | Content | Hours |
|-------|---------|-------|
| Setup | SETUP-PC.md, Python 3.12, uv, API keys, Cursor | 2h |
| CLI basics | guides/02_command_line.ipynb | 2h |
| Python syntax | guides/06_python_foundations.ipynb | 4h |
| Intermediate Python | guides/10_intermediate_python.ipynb (decorators, generators, context managers) | 4h |
| Async Python | guides/11_async_python.ipynb (CRITICAL — async/await model differs from goroutines) | 4h |
| APIs & Ollama | guides/09_ai_apis_and_ollama.ipynb | 2h |
| Debugging | guides/08_debugging.ipynb | 2h |
| Technical foundations | guides/04_technical_foundations.ipynb | 4h |
| Week 1 Labs 1-4 | First LLM call, system prompts, tool calling, agent loop | 10h |
| Extra | guides/05_notebooks.ipynb — Jupyter proficiency | 2h |

### Key concept: Agent Loop

```
while not done:
    response = llm.chat(messages, tools)
    if response.is_tool_call:
        result = execute_tool(response)
        messages.append(result)
    else:
        done = True
```

This is the fundamental unit of all agent frameworks covered in subsequent weeks.

## Phase 2: OpenAI Agents SDK (Day 3-5, 36h)

### Why this is the anchor

OpenAI Agents SDK is the most direct implementation of the agent abstraction. Understanding it deeply means every other framework is seen as "a different wrapper around the same concepts." Equivalent to net/http in Go — the standard library that everything else builds on.

### Core abstractions to master

- **Agent:** name + instructions + tools + handoffs + guardrails
- **Tool:** functions the LLM can invoke (hosted, function, custom)
- **Handoff:** agent-to-agent delegation (service mesh analogy)
- **Guardrail:** input/output validation (middleware analogy)
- **Tracing:** full execution trace (OpenTelemetry analogy)

### Schedule

| Block | Content | Hours |
|-------|---------|-------|
| Lab 1 | First SDK agent, Runner, result types | 4h |
| Lab 2 | Tools: function tool, hosted tool, custom tool | 6h |
| Lab 3 | Handoffs: inter-agent delegation patterns | 8h |
| Lab 4 | Guardrails + Tracing | 8h |
| Deep Research | Full project walkthrough | 6h |
| Self-directed | Add custom tools, experiment | 4h |

### Success criteria

Can build a single-purpose agent with custom tools, guardrails, and explain the execution lifecycle from Runner.run() to final output.

## Phase 3: CrewAI Multi-Agent (Day 6, 18h)

### Core concept

CrewAI models agent teams with Role/Goal/Backstory. A Crew orchestrates Tasks across Agents. Analogy: a microservice orchestration layer assigning work to specialized services.

### Schedule

| Block | Content | Hours |
|-------|---------|-------|
| Debate | Two-agent debate — understand Role/Goal/Backstory | 3h |
| Engineering Team | Multi-role pipeline | 5h |
| Stock Picker | Tool integration + role collaboration | 4h |
| Financial Researcher | Deep research synthesis | 3h |
| Coder | Code generation agent | 3h |

## Phase 4: LangGraph (Day 7-8, 36h)

### Core concept

LangGraph models agent execution as a directed graph. Nodes are processing steps, edges are state transitions. This is the control-flow framework — the learner's Go background makes this the most intuitive paradigm.

### Go analogies

- StateGraph = stateful DAG / workflow engine
- Node = handler function
- Edge = state transition
- ConditionalEdge = switch-case routing
- Checkpoint = write-ahead log / event sourcing

### Schedule

| Block | Content | Hours |
|-------|---------|-------|
| Lab 1 | StateGraph, Node, Edge fundamentals | 4h |
| Lab 2 | Conditional routing, cycles | 6h |
| Lab 3 | Human-in-loop, checkpoint, persistence | 8h |
| Lab 4 | Multi-agent graphs, subgraph nesting | 8h |
| Sidekick | Full app walkthrough | 6h |
| Self-directed | Rewrite a Week 2 agent using LangGraph | 4h |

## Phase 5: AutoGen (Day 8-9, 18h)

### Core concept

Microsoft's framework with distributed agent communication via async messaging. Topic/Subscription model resembles NATS/Kafka.

### Schedule

| Block | Content | Hours |
|-------|---------|-------|
| Lab 1 | AgentChat layer — conversational agents | 4h |
| Lab 2 | Multi-agent patterns, team, selector | 5h |
| Lab 3 | Core layer — Topic/Subscription messaging | 5h |
| Lab 4 | gRPC distributed deployment | 4h |

## Phase 6: MCP Protocol (Day 9-10, 18h)

### Core concept

Model Context Protocol standardizes agent-tool communication. JSON-RPC over stdio/SSE. Equivalent to a standardized gRPC-like protocol for AI tools.

### Key analogies

- tools/list = service discovery
- tools/call = remote function call
- resources/read = external data access
- stdio transport = local IPC
- SSE transport = HTTP streaming

### Schedule

| Block | Content | Hours |
|-------|---------|-------|
| Lab 1 | Protocol fundamentals, JSON-RPC, lifecycle | 3h |
| Lab 2 | First MCP Server (Tool Provider) | 3h |
| Lab 3 | Resources + Prompts | 4h |
| Lab 4 | Trading Floor multi-agent + MCP project | 4h |
| Lab 5 | Remote MCP, Docker deployment | 4h |

## Phase 7: Buffer (remaining hours)

Flex time for: deeper dives on any week, building a capstone project, reviewing community contributions, or catching up if any phase overran.

---

## Key Design Decisions

1. **Heavy Week 2 investment (36h, 20% of total):** The OpenAI Agents SDK is the anchor. Mastery here makes everything else recognizable as variations on the same pattern.

2. **Go→Python mapping over Python-from-scratch:** Teaching a senior engineer Python syntax from scratch is wasteful. The mapping approach leverages existing mental models.

3. **LangGraph gets equal time to Week 2:** It's the control-flow framework. For a Go engineer, directed graphs + state machines are the most natural way to reason about agent orchestration.

4. **CrewAI and AutoGen get compressed treatment (18h each):** They solve the same problem (multi-agent coordination) from different angles. Understanding their distinct philosophies matters more than deep implementation details.

5. **MCP is positioned as a protocol, not a framework:** It's the standard interface layer. Go engineers understand protocols and RPC — frame it that way from the start.

## Success Metrics

After 180 hours, the learner should be able to:
- Build a production agent with OpenAI Agents SDK (tools, guardrails, handoffs, tracing)
- Orchestrate multi-agent workflows with LangGraph
- Compare and choose between CrewAI, AutoGen, and LangGraph for different use cases
- Implement an MCP server exposing tools/resources
- Read and extend any Python-based agent framework
