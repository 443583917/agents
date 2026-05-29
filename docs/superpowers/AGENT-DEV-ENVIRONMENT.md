# Agent 开发环境搭建指南（新电脑从零开始）

> 适用：Windows / macOS / Linux | 目标：能运行本课程所有代码

---

## 工具清单总览

| # | 工具 | 作用 | 必需 |
|---|------|------|------|
| 1 | Git | 版本控制，克隆课程仓库 | ✅ |
| 2 | Cursor IDE | 编程 IDE，内置 AI 辅助、Jupyter 支持 | ✅ |
| 3 | uv | Python 包管理器和虚拟环境（替代 pip） | ✅ |
| 4 | Python 3.12 | 课程唯一支持的 Python 版本（uv 自动安装） | ✅ |
| 5 | OpenAI API Key | 调用 GPT-4o 等模型（付费，可选免费替代） | 推荐 |
| 6 | Anthropic API Key | 调用 Claude 模型（Week 4-6 需要） | Week4+ |
| 7 | Google API Key | 调用 Gemini 模型（Week 3+ 需要） | Week3+ |
| 8 | MS Build Tools | 编译带 C 扩展的 Python 包（仅 Windows） | Week3 |
| 9 | Ollama | 本地运行开源模型（免费替代 API） | 可选 |
| 10 | Docker | 容器化部署 MCP Server（Week 6） | Week6 |

---

## 一、Git — 版本控制

**作用：** 克隆课程代码仓库，管理本地代码版本。

**安装：**
- Windows：https://git-scm.com/download/win 下载安装
- macOS：`brew install git` 或系统自带
- Linux：`sudo apt install git` (Debian) / `sudo dnf install git` (Fedora)

**验证：** `git --version`

---

## 二、Cursor IDE — 编程环境

**作用：** 写代码、运行 Jupyter Notebook、AI 辅助编程。基于 VS Code，内置 Python 和 Jupyter 支持（比普通 VS Code 开箱即用更好）。

**为什么不用 VS Code：** Cursor 预配置了 AI Agent 开发需要的扩展，且内置多模型切换。用 VS Code 也可以，需要手动装 Python + Jupyter 扩展。

**安装：** https://www.cursor.com/ 下载安装，注册免费账号。

**首次打开课程项目后：**
1. 安装推荐扩展（Python、Jupyter）
2. `Ctrl+Shift+N` 打开新窗口 → "Open project" → 选 `agents` 目录

---

## 三、uv — Python 包管理器

**作用：** 代替传统的 `pip + venv + pyenv` 三件套。管理 Python 版本、虚拟环境、依赖安装，速度快 10-100 倍。

**类比 Go 开发者：** `uv` ≈ `go mod` + 自动管理 Go 版本

**常用命令对比：**

| 传统 pip 方式 | uv 方式 |
|--------------|---------|
| `pip install xxx` | `uv add xxx` |
| `python script.py` | `uv run script.py` |
| `python -m venv .venv` | 自动创建，不用管 |
| `pip freeze > requirements.txt` | `pyproject.toml` + `uv.lock` |

**安装：**
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**验证：** `uv --version`

---

## 四、Python 3.12 — 运行时

**作用：** 课程所有代码基于 Python 3.12。uv 运行 `uv sync` 时如果检测到没有 3.12 会自动下载，**不需要手动安装 Python**。

**验证：** `uv run python --version` → Python 3.12.x

---

## 五、API Keys — 模型调用凭证

### 5.1 OpenAI API Key

**作用：** 调用 GPT-4o、GPT-4o-mini 等模型。Agent 的"大脑"。

**获取：**
1. 注册 https://platform.openai.com/
2. 充值最低 $5（课程大概消耗 $2-3）
3. https://platform.openai.com/api-keys → 创建密钥
4. **关闭自动充值**（Settings > Billing）

**配置：** 在项目根目录创建 `.env` 文件：
```
OPENAI_API_KEY=sk-proj-你的密钥
```

### 5.2 Anthropic API Key（Week 4 开始需要）

**作用：** 调用 Claude 模型。LangGraph（Week 4）、AutoGen（Week 5）和 MCP（Week 6）会用到。

**获取：** https://console.anthropic.com/ → 注册 → 创建密钥

**配置：** 在 `.env` 文件中加一行：
```
ANTHROPIC_API_KEY=sk-ant-你的密钥
```

### 5.3 Google API Key（Week 3 开始需要）

**作用：** 调用 Gemini 模型。CrewAI（Week 3）会用到。

**获取：** https://aistudio.google.com/ → 创建 API Key

**配置：** 在 `.env` 文件中加一行：
```
GOOGLE_API_KEY=你的密钥
```

### 免费替代方案

如果不想付费：
- **Ollama（见下方）** — 本地免费运行模型
- **DeepSeek API** — 中文友好，极低成本
- 课程指南：`guides/09_ai_apis_and_ollama.ipynb`

---

## 六、MS Build Tools — 仅 Windows

**作用：** 编译 Chroma（向量数据库）等带 C/C++ 扩展的 Python 包。CrewAI（Week 3）依赖 Chroma，没装会报 obscure error。

**不做这个的话：** Week 1-2 完全不受影响。Week 3 如果报错再装也来得及。

**安装：**
1. 下载 https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
2. 运行安装程序，**勾选 "Desktop development with C++"**
3. 等待完成（约 5-10 分钟）

**验证：** 打开命令行，`where cl` 应返回路径

---

## 七、Ollama — 本地模型（可选）

**作用：** 在本地运行开源模型（Llama、Mistral 等），完全免费、无需网络、数据不外传。

**安装：** https://ollama.com/ 下载安装

**使用：**
```bash
ollama pull llama3.2    # 下载模型（约 2GB）
ollama pull mistral     # 备选
```

**课程中如何使用：** 参考 `guides/09_ai_apis_and_ollama.ipynb`，将 API 调用改为本地 Ollama 地址。

---

## 八、Docker — 容器化（Week 6）

**作用：** Week 6 MCP 部分会用到 Docker 部署远程 MCP Server。

**安装：** https://www.docker.com/products/docker-desktop/

**验证：** `docker --version`

**不需要提前装：** Week 1-5 完全用不到，Day 9 再装就行。

---

## 完整安装顺序（新电脑）

```bash
# 1. 装 Git
#    下载：https://git-scm.com/download

# 2. 装 Cursor
#    下载：https://www.cursor.com/

# 3. 克隆项目
mkdir ~/projects
cd ~/projects
git clone https://github.com/ed-donner/agents.git
cd agents

# 4. 装 uv
#    Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
#    macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# 5. 同步依赖（自动装 Python 3.12 + 所有包）
uv sync

# 6. 装 CrewAI（Week 3 需要）
uv tool install crewai==0.130.0 --python 3.12

# 7. 创建 .env 文件（填入 API Keys）
echo "OPENAI_API_KEY=sk-proj-你的密钥" > .env
echo "ANTHROPIC_API_KEY=sk-ant-你的密钥" >> .env
echo "GOOGLE_API_KEY=你的密钥" >> .env

# 8. 诊断检查
uv run python setup/diagnostics.py

# 9. 在 Cursor 中打开项目，装推荐扩展，选 .venv kernel
```

---

## 环境诊断清单

| 检查项 | 命令 | 预期 |
|--------|------|------|
| Git | `git --version` | 2.x |
| uv | `uv --version` | 0.11+ |
| Python | `uv run python --version` | 3.12.x |
| .venv | `ls .venv/` | 存在 |
| CrewAI | `uv tool list` | crewai 在列表中 |
| OpenAI | `uv run python -c "from openai import OpenAI; print('OK')"` | OK |
| Agent SDK | `uv run python -c "from agents import Agent; print('OK')"` | OK |
| LangGraph | `uv run python -c "from langgraph.graph import StateGraph; print('OK')"` | OK |
| Jupyter | 在 Cursor 中打开 .ipynb → Shift+Enter | 无报错 |
