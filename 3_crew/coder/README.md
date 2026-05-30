# Coder Crew

基于 [crewAI](https://crewai.com) 构建的多智能体编程助手项目。该模板帮助你快速搭建 AI 编程代理系统，让多个 AI Agent 协作完成复杂的编码任务。

## 环境要求

| 工具 | 用途 | 安装方式 |
| --- | --- | --- |
| Python >= 3.10 且 < 3.13 | 运行环境 | [python.org](https://www.python.org/downloads/) |
| [UV](https://docs.astral.sh/uv/) | 包管理 | `pip install uv` |
| [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) | 编译 C 扩展（chroma-hnswlib） | 下载安装时勾选 **"桌面 C++ 开发"** |
| [Docker Desktop](https://docs.docker.com/desktop/) | `code_execution_mode="safe"` 模式需要 | 安装并 **保持运行**（托盘图标不退出） |

> **Windows 必读**：CrewAI 的依赖链包含 `chroma-hnswlib`（C 扩展），没有 MSVC 编译工具会报 `Failed to build chroma-hnswlib` 错误。
>
> 如果不想装 Docker，将 `crew.py` 中的 `code_execution_mode` 改为 `"unsafe"`。

## 安装

```bash
# 1. 安装 uv（如已安装可跳过）
pip install uv

# 2. 进入项目目录
cd coder

# 3. 安装依赖（首次运行前执行一次）
uv sync
```

或者使用 CrewAI CLI：

```bash
crewai install
```

## 项目结构

```text
coder/
├── pyproject.toml              # 项目配置与依赖
├── README.md                   # 项目说明
├── .gitignore
├── knowledge/
│   └── user_preference.txt     # 用户偏好（Agent 参考）
├── output/                     # 输出目录
└── src/coder/
    ├── __init__.py
    ├── main.py                 # 入口：配置输入参数、启动 Crew
    ├── crew.py                 # Crew 定义：Agent、Task、Crew 组装
    ├── config/
    │   ├── agents.yaml         # Agent 配置（角色、目标、背景故事）
    │   └── tasks.yaml          # Task 配置（描述、预期输出）
    └── tools/
        ├── __init__.py
        └── custom_tool.py      # 自定义工具模板
```

## 配置说明

### 1. 设置 API Key

在项目根目录创建 `.env` 文件：

```bash
OPENAI_API_KEY=your-api-key-here
```

### 2. 自定义 Agent

编辑 `src/coder/config/agents.yaml`：

```yaml
coder:
  role: 角色名称
  goal: 目标任务
  backstory: 背景描述，影响 Agent 行为风格
  llm: gpt-4o-mini          # 使用的模型
```

### 3. 自定义 Task

编辑 `src/coder/config/tasks.yaml`：

```yaml
coding_task:
  description: 任务描述
  expected_output: 预期的输出格式
  agent: coder              # 绑定到哪个 Agent
  output_file: output/code_and_output.txt
```

### 4. 自定义 Crew 逻辑

编辑 `src/coder/crew.py` — 添加 Agent、Task、工具或自定义逻辑。

### 5. 自定义输入

编辑 `src/coder/main.py` — 修改 `inputs` 字典来改变传给 Agent 的变量。

## 运行

```bash
crewai run
```

该命令会初始化 Coder Crew，按配置组装 Agent 和 Task 并开始执行。默认示例会让 Agent 编写一段 Python 程序来计算莱布尼茨级数（π 的近似值），结果输出到 `output/code_and_output.txt`。

## 架构概览

```text
main.py (入口)                     crew.py (组装)
    │                                  │
    │  inputs = {                      │  @CrewBase
    │    'assignment': '...'           │  ├─ @agent → Agent (coder)
    │  }                               │  ├─ @task  → Task  (coding_task)
    │                                  │  └─ @crew  → Crew  (组装+执行模式)
    ▼                                  │
Coder().crew().kickoff(inputs)  ◄──────┘
```

## 支持与反馈

- [crewAI 官方文档](https://docs.crewai.com)
- [GitHub 仓库](https://github.com/joaomdmoura/crewai)
- [Discord 社区](https://discord.com/invite/X4JWnZnxPb)
