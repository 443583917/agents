# Week 1：Agent 基础 — 从零搭建你的第一个 AI Agent

## 一、完整目录结构

```
1_foundations/
│
├── 📓 1_lab1.ipynb              ← 实验1：第一次调用 LLM API
├── 📓 2_lab2.ipynb              ← 实验2：调用多个模型对比评测
├── 📓 3_lab3.ipynb              ← 实验3：用 Gradio 搭建个人 AI 聊天网站（带质量评估）
├── 📓 4_lab4.ipynb              ← 实验4：Tool Calling + Agent Loop（核心！）
├── 📓 5_extra.ipynb             ← 实验5：从零手写 Agent Loop + Todo 规划工具
├── 🐍 app.py                    ← Lab4 的独立 Python 版本，可部署到 HuggingFace
├── 📄 requirements.txt          ← 1_foundations 专属的 Python 依赖清单
│
├── 📁 me/                       ← 存放你个人的资料（Agent 的知识库）
│   ├── linkedin.pdf             ←  你的 LinkedIn 简历 PDF 导出
│   └── summary.txt              ←  你的个人简介文本
│
└── 📁 community_contributions/  ← 全球学员的贡献代码（252个文件夹/文件）
    │
    ├── 📄 1_lab1_xxx.ipynb ×20+    ← 学员用不同模型实现的 Lab1 变体
    │     （如 1_lab1_gemini / 1_lab1_groq / 1_lab1_open_router / 
    │       1_lab1_azure_openai 等）
    │
    ├── 📄 2_lab2_xxx.ipynb ×25+    ← 学员实现的 Lab2 变体
    │     （涵盖 Parallelization / Reflection / Routing / ReAct /
    │       Orchestrator-Worker / Chain of Thought / 六顶思考帽等模式）
    │
    ├── 📄 3_lab3_xxx.ipynb ×5+     ← 学员实现的 Lab3 变体
    │     （Azure OpenAI / Claude Evaluator / Groq+Gemini 组合等）
    │
    ├── 📄 4_lab4_xxx.ipynb ×8+     ← 学员实现的 Lab4 变体
    │     （Slack / Telegram / Spotify 集成、旅行规划器等）
    │
    ├── 📄 5_extra_xxx.ipynb        ← Lab5 学员变体
    │
    ├── 📁 项目1: 1_medtech_opportunity_finder/     ← 医疗器械商机发现 Agent
    ├── 📁 项目2: 2_medguard_debate/                ← 医疗防护辩论 Agent
    ├── 📁 项目3: 3_pagebotai_crawler/              ← 网页爬虫 Agent
    ├── 📁 项目4: 4_weathermate_agent/              ← 天气助手 Agent
    │
    ├── 📁 1_foundations_using_gemini/              ← 全套 Lab 1-4 的 Gemini 版本
    │   ├── 1_lab1.ipynb / 2_lab2.ipynb / 3_lab3.ipynb / 4_lab4.ipynb
    │   ├── app.py / email_writeup.ipynb
    │   └── me/ (linkedin.pdf + summary.txt)
    │
    └── 📁 100+ 学员个人项目文件夹             ← 每个学员的完整 Agent 项目
          （如 career_agent / digital_twin / chatbot_rag_evaluation /
            deep_research / expense_splitter / hidden_gems_travel_guide /
            novel_generator / career_doppelganger / 等等）
```

---

## 二、每个文件的功能详解

### 2.1 核心实验 Notebook（必须按顺序学）

| 文件 | 功能 | 学完后你能做什么 | 建议时长 |
|------|------|-----------------|---------|
| `1_lab1.ipynb` | 导入 openai 库、加载 .env 密钥、构造 messages、调用 chat.completions.create()、多轮对话链 | 用 Python 代码调用任何 LLM | 2h |
| `2_lab2.ipynb` | 同一个问题发给 5+ 个模型，收集答案，再用一个裁判 LLM 打分排名；包含 Anthropic/Gemini/DeepSeek/Groq/Ollama 的调用方式 | 对多个模型做基准测试 | 2h |
| `3_lab3.ipynb` | 读取 PDF 简历 + 文本简介，构造 System Prompt 注入知识，用 Gradio 搭建 Web Chat UI，用一个 LLM 做 Evaluator 评估回答质量，不合格自动重试 | 搭建带质量控制的个人 AI 助手网站 | 3h |
| `4_lab4.ipynb` | 定义 Tool 的 JSON Schema、实现 Agent Loop（循环调用 LLM + 执行工具）、集成 Pushover 推送通知 | 写一个能调用外部工具的自主 Agent | 3h |
| `5_extra.ipynb` | 完全从零写 Agent Loop（不依赖任何框架）、用 Todo List 工具让 Agent 分步规划+执行、解数学题 | 彻底理解 Agent 底层原理 | 1h |

### 2.2 独立 Python 文件

| 文件 | 功能 | 运行方式 |
|------|------|---------|
| `app.py` | Lab 4 的完整独立版。用 `class Me` 封装了个人资料读取、System Prompt 生成、Agent Loop、Gradio Chat UI。可直接部署到 HuggingFace Spaces 成为公网可访问的网站 | `uv run python app.py` 本地运行；`uv run gradio deploy` 部署到 HuggingFace |
| `requirements.txt` | 声明 `1_foundations` 文件夹代码所需的包：requests、python-dotenv、gradio、pypdf、openai、openai-agents | 项目根目录的 `uv sync` 已全覆盖，无需单独安装 |

### 2.3 me/ 文件夹（你的个人资料）

Agent 需要的知识库。Lab 3 和 Lab 4 会读取这些文件来构建 System Prompt：

| 文件 | 功能 | 如何准备 |
|------|------|---------|
| `me/linkedin.pdf` | 你的 LinkedIn 简历 PDF。Agent 用它了解你的职业背景 | 从 LinkedIn 网页导出：Me → Settings & Privacy → Data Privacy → Get a copy of your data → 选 PDF |
| `me/summary.txt` | 你的个人简介文本。Agent 用它快速了解你 | 自己写一段 200-500 字的自我介绍，包含技能、经历、兴趣 |

### 2.4 community_contributions/ 文件夹（252 个贡献）

全球学员提交的代码，是一个**免费的学习资源宝库**。不需要全部看，按需浏览。

**按内容分为 4 类：**

#### 类型 A：Lab 变体文件（约 60 个单文件）
学员把同一个 Lab 用不同模型/不同方法重写了一遍：
- `1_lab1_gemini.ipynb` — 用 Gemini 替代 OpenAI
- `1_lab1_groq.ipynb` — 用 Groq 平台
- `1_lab1_open_router.ipynb` — 用 OpenRouter 聚合平台
- `1_lab1_azure_openai.ipynb` — 用 Azure OpenAI
- `2_lab2_ReAct_Pattern.ipynb` — 用 ReAct（Reasoning + Acting）模式
- `2_lab2_reflection_pattern.ipynb` — Reflection（自我反思）模式
- `2_lab2_orchestrator.ipynb` — Orchestrator-Worker 编排模式
- `2_lab2_parallelization.ipynb` — 并行调用多个模型
- `2_lab2_six-thinking-hats-simulator.ipynb` — 六顶思考帽决策模式

> **怎么用：** 学完某个 Lab 后，打开对应的学员变体看别人怎么用不同模型/模式的，拓宽思路。

#### 类型 B：编号项目（4 个完整项目）
课程设计的多步骤项目，编号表示推荐顺序：
| 项目 | 内容 | 学完 Lab 几后可看 |
|------|------|------------------|
| `1_medtech_opportunity_finder/` | 医疗器械行业的 Agent 商机发现器 | Lab 1 后 |
| `2_medguard_debate/` | 医疗 AI 安全性的多模型辩论系统 | Lab 2 后 |
| `3_pagebotai_crawler/` | 网页爬虫 + AI 分析 Agent | Lab 3 后 |
| `4_weathermate_agent/` | 天气助手 Agent（含外部 API 调用） | Lab 4 后 |

#### 类型 C：完整 Lab 替代版（1 个）
| 文件夹 | 内容 |
|--------|------|
| `1_foundations_using_gemini/` | 全套 Lab 1-4 全部改为用 Gemini API，包含 email_writeup.ipynb 分析文档 |

> **怎么用：** 如果你主要用 Gemini 而不是 OpenAI/DeepSeek，可以参考这个文件夹的所有代码。

#### 类型 D：学员个人项目（100+ 个文件夹）
学员在学完 Week 1 后自己做的 Agent 项目。精选几个值得看的：

| 文件夹 | 做了什么 | 亮点 |
|--------|---------|------|
| `career_agent/` | 职业顾问 Agent | 完整聊天机器人 |
| `deep_research_by_ashir_haroon/` | 深度研究 Agent | 多步骤研究流程 |
| `chatbot_rag_evaluation/` | 带 RAG 知识库的聊天机器人 | RAG + 评估 |
| `digital_twin_joshua/` | 个人数字分身 | 含 CI/CD 部署 |
| `hidden_gems_world_travel_guide/` | 小众旅行指南 Agent | 含 GitHub Actions |
| `expense-splitter-agent/` | 费用分摊 Agent | 实用工具型 |
| `novel-generator/` | 小说生成 Agent | 创意生成型 |
| `career_doppelganger/` | 职业生涯克隆 Agent | 个人品牌 |
| `weather-tool/` | 天气工具 Agent | 外部 API 集成 |
| `medical_note_classification_eval/` | 医疗笔记分类评估 | 行业应用 |
| `immigrant-assistance/` | 移民辅助 Agent | 社会公益 |
| `Multi-Model-Resume-JD-Match-Analyzer/` | 多模型简历-职位匹配分析 | 求职工具 |
| `discord_over_pushover/` | Discord 通知替代 Pushover | 通知集成 |
| `Hareesh_Debugger agent/` | 调试器 Agent | 开发工具 |

> **怎么用：** 学完所有 5 个 Lab 后，挑 2-3 个感兴趣的项目看代码，理解别人怎么把基础概念变成完整应用。

---

## 三、学习路线图

```
Lab 1 (2h)          Lab 2 (2h)         Lab 3 (3h)          Lab 4 (3h)          Lab 5 (1h)
┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│ 调用 LLM │  →    │ 多模型   │  →    │ System   │  →    │ Tool     │  →    │ 从零实现 │
│ 基础 API │       │ 对比评测 │       │ Prompt   │       │ Calling  │       │ Agent    │
│          │       │          │       │ + 评估   │       │ + Loop   │       │ Loop     │
└──────────┘       └──────────┘       └──────────┘       └──────────┘       └──────────┘

最终产出: app.py — 一个可部署到 HuggingFace 的个人 AI 聊天网站
```

**每学完一个 Lab，建议做的事：**
1. 打开 `community_contributions/` 里对应的学员变体，看看别人怎么做的
2. 自己改代码实验（换模型、换提示词、换工具）

---

## 四、各 Lab 核心概念速查

### Lab 1：第一次 LLM 调用

```python
from openai import OpenAI
openai = OpenAI()

response = openai.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "2+2等于多少？"}]
)
print(response.choices[0].message.content)
```

**用 DeepSeek（你的配置）：**

```python
import os
openai = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY")
)
# 模型名改成 "deepseek-chat"
```

### Lab 2：多模型对比

```
同一个问题 → GPT → 答案1 ┐
           → Claude → 答案2 ├→ 裁判 LLM → 排名
           → Gemini → 答案3 │
           → DeepSeek → 答案4┘
```

### Lab 3：System Prompt + 评估反馈

```
用户提问 → Agent 生成回答 → Evaluator LLM 评估
                ↑                    ↓
                │              合格？→ 返回给用户
                │              不合格？→ 给出反馈 → Agent 重写
                └────────────────────────────────┘
```

### Lab 4：Agent Loop（整个课程最重要的模式）

```
                    ┌─────────────┐
                    │  用户提问    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
              ┌────►│  LLM 思考   │
              │     └──────┬──────┘
              │            ▼
              │     ┌─────────────┐
              │     │ 需要调工具？  │
              │     └──┬──────┬───┘
              │        │YES   │NO
              │        ▼      ▼
              │  ┌────────┐ ┌──────────┐
              │  │执行工具 │ │返回最终答案│
              │  └───┬────┘ └──────────┘
              │      │
              └──────┘
              (结果喂回 LLM，继续循环)
```

**Agent Loop 核心代码：**

```python
def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": message})
    
    done = False
    while not done:
        response = openai.chat.completions.create(
            model="gpt-4o-mini", 
            messages=messages, 
            tools=tools  # ← 关键：告诉 LLM 有哪些工具可用
        )
        
        if response.choices[0].finish_reason == "tool_calls":
            msg = response.choices[0].message
            results = handle_tool_calls(msg.tool_calls)
            messages.append(msg)
            messages.extend(results)
        else:
            done = True
    
    return response.choices[0].message.content
```

### Lab 5：课程对 Agent 的定义

> **Agent = LLM + Tools + Loop**
>
> 一个 LLM 在循环中运行工具来达成目标。

---

## 五、配套指南（遇到问题看这里）

中文版指南在 `guides/guides-Chinese/` 中：

| 问题 | 看哪个 |
|------|--------|
| ImportError / ModuleNotFoundError | 运行 `uv sync` |
| NameError（变量未定义） | `guides/guides-Chinese/06_python_foundations.ipynb` 最后部分 |
| API Key 配置问题 | `guides/guides-Chinese/04_technical_foundations.ipynb` 主题 3 |
| 不知道怎么用 Jupyter Notebook | `guides/guides-Chinese/05_notebooks.ipynb` |
| Python 语法不熟 | `guides/guides-Chinese/06_python_foundations.ipynb` |
| async/await 不懂 | `guides/guides-Chinese/11_async_python.ipynb` |
| DeepSeek 怎么配 | `guides/guides-Chinese/09_ai_apis_and_ollama.ipynb` 示例 2 |

---

## 六、立即开始

1. 在 Cursor 中打开 `1_foundations/1_lab1.ipynb`
2. 右上角选择 `.venv (Python 3.12.x)` 作为 kernel
3. 按 `Shift+Enter` 逐个执行代码单元
4. 按顺序：Lab 1 → Lab 2 → Lab 3 → Lab 4 → Lab 5

**每个 Lab 完成标准：** 所有代码单元都能在你的 DeepSeek 配置下成功运行，理解每段代码在做什么。
