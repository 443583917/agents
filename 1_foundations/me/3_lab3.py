# ============================================================
#  必须在所有 import 之前：禁用系统代理对本机地址的影响
#  这台机器有 127.0.0.1:7897 代理，httpx 会读它导致 Gradio 自检 502
# ============================================================
import os
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

import json
from pathlib import Path
from pypdf import PdfReader
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# ============================================================
# 1. 初始化：加载 .env 和读取数据文件
# ============================================================
BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

NAME = "Ed Donner"

txt_path = BASE_DIR / "linkedin.txt"
if txt_path.exists():
    with open(txt_path, "r", encoding="utf-8") as f:
        linkedin_text = f.read()
else:
    reader = PdfReader(str(BASE_DIR / "linkedin.pdf"))
    linkedin_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            linkedin_text += text
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(linkedin_text)

with open(BASE_DIR / "summary.txt", "r", encoding="utf-8") as f:
    summary_text = f.read()


# ============================================================
# 2. 模型配置 — 全部从 .env 动态读取
# ============================================================
def _load_model_configs() -> dict[str, dict[str, str]]:
    models_env = os.getenv("MODELS", "deepseek")
    keys = [k.strip() for k in models_env.split(",") if k.strip()]
    configs = {}
    for key in keys:
        prefix = key.upper()
        api_key = os.getenv(f"{prefix}_API_KEY", "")
        base_url = os.getenv(f"{prefix}_BASE_URL", "")
        model = os.getenv(f"{prefix}_MODEL", key)
        if not api_key:
            print(f"  [跳过] {key}: {prefix}_API_KEY 未设置")
            continue
        configs[key] = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
        }
        print(f"  [已加载] {key}: {model} @ {base_url}")
    if not configs:
        raise RuntimeError("没有可用的模型！请在 .env 中至少配置一个模型的 API_KEY")
    return configs


MODEL_CONFIGS = _load_model_configs()
DEFAULT_MODEL = list(MODEL_CONFIGS.keys())[0]
MODEL_CHOICES = list(MODEL_CONFIGS.keys())


def make_client(model_choice: str) -> OpenAI:
    cfg = MODEL_CONFIGS[model_choice]
    return OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])


def get_model_name(model_choice: str) -> str:
    return MODEL_CONFIGS[model_choice]["model"]


# ============================================================
# 3. System Prompt 构建
# ============================================================
# 从文件加载提示词模板（启动时读取，修改 prompt.md 后重启服务即可生效）
PROMPT_TEMPLATE = (BASE_DIR / "prompt.md").read_text(encoding="utf-8")


def build_system_prompt(preferences: dict) -> str:
    style = preferences.get("style", "professional")
    tone = preferences.get("tone", "warm")
    max_len = preferences.get("max_length", 300)

    return PROMPT_TEMPLATE.format(
        name=NAME,
        style=style,
        tone=tone,
        max_len=max_len,
        summary=summary_text,
        linkedin=linkedin_text,
    )


# ============================================================
# 4. Evaluator
# ============================================================
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


EVALUATOR_SYSTEM_PROMPT = f"""You are an evaluator. Your task is to evaluate the assistant's final response \
and determine if it is acceptable, replying with JSON: {{"is_acceptable": bool, "feedback": str}}.

When determining if the response is acceptable, check for:
- Does the response answer the user's question?
- Is the response factually consistent with {NAME}'s profile?
- Any wrong facts or hallucinations?
- Is the response professional and engaging?"""


def evaluate(reply: str, message: str, history: list, model_choice: str) -> Evaluation:
    client = make_client(model_choice)
    model = get_model_name(model_choice)

    user_prompt = f"Conversation history:\n{history}\n\nUser message: {message}\n\nAgent response: {reply}\n\nPlease evaluate."

    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        dump_raw("Evaluator 发送的数据", model, messages)
        response = client.chat.completions.create(
            model=model, messages=messages, response_format={"type": "json_object"}
        )
        raw = response.choices[0].message.content
        dump_raw("Evaluator 返回的原始数据", model, raw, is_response=True)
        data = json.loads(raw)
        return Evaluation(is_acceptable=data.get("is_acceptable", True), feedback=data.get("feedback", ""))
    except Exception as e:
        return Evaluation(is_acceptable=True, feedback=f"Evaluator error: {e}")


# ============================================================
# 5. Rerun
# ============================================================
def rerun(reply: str, message: str, history: list, feedback: str, preferences: dict, model_choice: str) -> str:
    client = make_client(model_choice)
    model = get_model_name(model_choice)

    system = build_system_prompt(preferences)
    system += "\n\n## Previous answer rejected\n"
    system += f"Your attempted answer: {reply}\n"
    system += f"Reason for rejection: {feedback}\n"
    system += "Please fix these issues and provide a better response."

    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content


# ============================================================
# 6. 数据透视工具 — 记录每次与大模型的完整交互
# ============================================================
import datetime as _dt

def _split_system_prompt(text: str) -> dict[str, str]:
    """将 system prompt 按 ## 标题拆分成结构化段落"""
    sections = {}
    current_title = "前言"
    current_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            if current_lines:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = stripped[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections[current_title] = "\n".join(current_lines).strip()
    return sections


def dump_raw(label: str, model: str, data, is_response: bool = False):
    """将原始数据写入 logs/ 目录，结构清晰便于阅读"""
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bar = "─" * 70

    if is_response:
        path = log_dir / f"{timestamp}_response.txt"
        lines = [bar, f"  {label}", bar, f"  模型: {model}", f"  时间: {timestamp}", bar, ""]
        if isinstance(data, str):
            lines.append(data)
        else:
            lines.append(str(data))
        content = "\n".join(lines)

    else:
        path = log_dir / f"{timestamp}_request.txt"
        lines = [bar, f"  {label}", bar, f"  模型: {model}", f"  时间: {timestamp}", f"  消息条数: {len(data)}", bar, ""]

        for i, msg in enumerate(data):
            role = msg["role"].upper()
            text = msg["content"]

            if role == "SYSTEM":
                sections = _split_system_prompt(text)
                lines.append(f"{'═'*70}")
                lines.append(f"  [{i}] SYSTEM PROMPT — 共 {len(text)} 字符，{len(sections)} 个段落")
                lines.append(f"{'═'*70}")
                for title, body in sections.items():
                    lines.append(f"")
                    lines.append(f"  ▸ {title}")
                    lines.append(f"  {'─'*60}")
                    for line in body.split("\n"):
                        lines.append(f"  │ {line}")
                    lines.append(f"  {'─'*60}")
            elif role == "USER":
                lines.append(f"")
                lines.append(f"  [{i}] USER — {len(text)} 字符")
                lines.append(f"  {'─'*60}")
                for line in text.split("\n"):
                    lines.append(f"    {line}")
                lines.append(f"  {'─'*60}")
            elif role == "ASSISTANT":
                lines.append(f"")
                lines.append(f"  [{i}] ASSISTANT — {len(text)} 字符")
                lines.append(f"  {'─'*60}")
                for line in text.split("\n")[:20]:  # 历史消息限制行数
                    lines.append(f"    {line}")
                if len(text.split("\n")) > 20:
                    lines.append(f"    ... (截断)")
                lines.append(f"  {'─'*60}")
            else:
                lines.append(f"  [{i}] {role}: {text[:500]}")

            lines.append("")

        lines.append(f"{'═'*70}")
        lines.append(f"  Token 估算: ~{len(text)//4} tokens (system) + 用户消息部分")
        lines.append(f"{'═'*70}")

        content = "\n".join(lines)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  [日志] {path.name}", flush=True)


# ============================================================
# 7. Gradio Chat 回调
# ============================================================
MAX_RETRIES = 2
API_TIMEOUT = 30


def chat(message: str, history: list, model_choice: str, style: str, tone: str, max_length: int, enable_eval: bool):
    """接收消息 → 生成 → (可选)评估+重试 → 返回回复"""
    preferences = {"style": style, "tone": tone, "max_length": max_length}
    client = make_client(model_choice)
    model = get_model_name(model_choice)
    system = build_system_prompt(preferences)

    # 构建 messages 这边要注意每次请求message都会包含完整的对话历史，
    # 所以要把历史消息也按照格式放到 messages 里，保持和模型交互的一致性
    # 如果传递了空的messages，模型就不知道之前说了什么了，就像每次都从新开始一样，这样就无法进行连续对话了
    messages = [{"role": "system", "content": system}]
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if assistant_msg:
            messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})

    # ====== 输出：发送给大模型的原始数据 ======
    dump_raw("发送给大模型的数据", model, messages)

    # 生成回复
    print(f"\n[请求] {message[:80]}... | 模型={model_choice}", flush=True)
    try: #尝试执行
        response = client.chat.completions.create(model=model, messages=messages, timeout=API_TIMEOUT)
        reply = response.choices[0].message.content
        print(f"[回复] {reply[:120]}...", flush=True)
    except Exception as e: #错误处理
        print(f"[错误] {e}", flush=True)
        return f"[API 调用失败: {e}]"

    # ====== 输出：模型返回的原始数据 ======
    dump_raw("模型返回的原始回复", model, reply, is_response=True)

    # 评估 + 重试
    if enable_eval:
        for attempt in range(MAX_RETRIES):
            print(f"  [评估] 第{attempt+1}轮...", flush=True)
            evaluation = evaluate(reply, message, history, model_choice)
            if evaluation.is_acceptable:
                print(f"  [评估] 通过", flush=True)
                break
            print(f"  [评估] 未通过: {evaluation.feedback[:100]}", flush=True)
            reply = rerun(reply, message, history, evaluation.feedback, preferences, model_choice)
            print(f"  [重试] 新回复 ({len(reply)}字符)", flush=True)

    return reply


# ============================================================
# 7. Gradio UI
# ============================================================
def build_ui():
    with gr.Blocks(title=f"{NAME}'s Chatbot", theme=gr.themes.Soft()) as ui:
        gr.Markdown(f"# {NAME}'s AI Chatbot")
        gr.Markdown("Ask about career, skills, background. Powered by AI.")

        with gr.Row():
            with gr.Column(scale=3):
                _ = gr.ChatInterface(
                    fn=chat,
                    additional_inputs=[
                        gr.Dropdown(choices=MODEL_CHOICES, value=DEFAULT_MODEL, label="模型"),
                        gr.Dropdown(choices=["professional", "casual", "storytelling", "concise"], value="professional", label="风格"),
                        gr.Dropdown(choices=["warm", "formal", "friendly", "direct"], value="warm", label="语气"),
                        gr.Slider(minimum=50, maximum=800, value=300, step=50, label="最长词数"),
                        gr.Checkbox(value=False, label="质量评估 (会稍慢)", info="默认关闭快速响应"),
                    ],
                )
    return ui


# ============================================================
# 8. 启动
# ============================================================
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  {NAME}'s AI Chatbot 启动中...")
    print(f"  模型: {MODEL_CHOICES} (默认: {DEFAULT_MODEL})")
    print(f"  LinkedIn ({len(linkedin_text)}字符) + Summary ({len(summary_text)}字符)")
    print(f"  代理已 bypass: HTTP_PROXY='' | NO_PROXY=127.0.0.1,localhost")
    print(f"{'='*50}\n")

    ui = build_ui()
    ui.launch(server_name="127.0.0.1", server_port=7860, inbrowser=False, share=False)
