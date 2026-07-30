"""
util.py - UI 工具模块

本文件包含 Gradio Web UI 使用的 CSS 样式、JavaScript 代码和颜色枚举。
"""

from enum import Enum


# ========== CSS 样式 ==========
css = """
.positive-pnl {
    color: green !important;
    font-weight: bold;
}
.positive-bg {
    background-color: green !important;
    font-weight: bold;
}
.negative-bg {
    background-color: red !important;
    font-weight: bold;
}
.negative-pnl {
    color: red !important;
    font-weight: bold;
}
.dataframe-fix-small .table-wrap {
min-height: 150px;
max-height: 150px;
}
.dataframe-fix .table-wrap {
min-height: 200px;
max-height: 200px;
}
footer{display:none !important}
"""


# ========== JavaScript ==========
js = """
function refresh() {
    const url = new URL(window.location);
    // 自动切换到深色主题
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""


# ========== 颜色枚举 ==========
class Color(Enum):
    """日志类型对应的颜色，用于在 UI 中区分不同类型的事件。"""
    RED = "#dd0000"
    GREEN = "#00dd00"
    YELLOW = "#dddd00"
    BLUE = "#0000ee"
    MAGENTA = "#aa00dd"
    CYAN = "#00dddd"
    WHITE = "#87CEEB"
