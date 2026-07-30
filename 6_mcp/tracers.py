"""
tracers.py - 追踪处理器模块

本文件实现自定义的追踪处理器（TracingProcessor），用于将 Agent 的执行日志
写入 SQLite 数据库，以便在 Gradio UI 中展示。

OpenAI Agents SDK 的追踪系统：
  - Trace: 一次完整的 Agent 运行（如 "Warren-trading"）
  - Span:  Trace 中的单个步骤（如 function 调用、LLM 生成等）

追踪处理器通过 trace_id 中嵌入的名称来识别属于哪个交易员。
"""

from agents import TracingProcessor, Trace, Span
from database import write_log
import secrets
import string

# 用于生成随机 trace_id 的字符集
ALPHANUM = string.ascii_lowercase + string.digits


def make_trace_id(tag: str) -> str:
    """生成带有标签的 trace_id。

    格式：trace_<tag>0<random>
    其中 tag 是交易员名称，0 是分隔符，random 是随机后缀。
    总长度固定为 32 字符（不含 "trace_" 前缀）。

    Args:
        tag: 标签（通常是交易员名称的小写形式）

    Returns:
        str: 格式化的 trace_id
    """
    tag += "0"
    pad_len = 32 - len(tag)
    random_suffix = ''.join(secrets.choice(ALPHANUM) for _ in range(pad_len))
    return f"trace_{tag}{random_suffix}"


class LogTracer(TracingProcessor):
    """自定义追踪处理器 - 将 trace/span 事件写入数据库日志。

    通过解析 trace_id 中的标签来确定事件属于哪个交易员，
    然后将事件记录到该交易员的日志中。
    """

    def get_name(self, trace_or_span: Trace | Span) -> str | None:
        """从 trace_id 中提取交易员名称。

        trace_id 格式：trace_<name>0<random>
        提取 <name> 部分作为交易员名称。

        Args:
            trace_or_span: Trace 或 Span 对象

        Returns:
            str 或 None: 交易员名称，无法解析时返回 None
        """
        trace_id = trace_or_span.trace_id
        name = trace_id.split("_")[1]
        if '0' in name:
            return name.split("0")[0]
        else:
            return None

    def on_trace_start(self, trace) -> None:
        """Trace 开始时的回调"""
        name = self.get_name(trace)
        if name:
            write_log(name, "trace", f"Started: {trace.name}")

    def on_trace_end(self, trace) -> None:
        """Trace 结束时的回调"""
        name = self.get_name(trace)
        if name:
            write_log(name, "trace", f"Ended: {trace.name}")

    def on_span_start(self, span) -> None:
        """Span 开始时的回调。

        记录 span 的类型、名称、关联的 MCP 服务器等信息。
        """
        name = self.get_name(span)
        type = span.span_data.type if span.span_data else "span"
        if name:
            message = "Started"
            if span.span_data:
                if span.span_data.type:
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
                if hasattr(span.span_data, "server") and span.span_data.server:
                    message += f" {span.span_data.server}"
            if span.error:
                message += f" {span.error}"
            write_log(name, type, message)

    def on_span_end(self, span) -> None:
        """Span 结束时的回调"""
        name = self.get_name(span)
        type = span.span_data.type if span.span_data else "span"
        if name:
            message = "Ended"
            if span.span_data:
                if span.span_data.type:
                    message += f" {span.span_data.type}"
                if hasattr(span.span_data, "name") and span.span_data.name:
                    message += f" {span.span_data.name}"
                if hasattr(span.span_data, "server") and span.span_data.server:
                    message += f" {span.span_data.server}"
            if span.error:
                message += f" {span.error}"
            write_log(name, type, message)

    def force_flush(self) -> None:
        """强制刷新（本实现无需操作）"""
        pass

    def shutdown(self) -> None:
        """关闭处理器（本实现无需操作）"""
        pass
