"""
app.py - Gradio Web UI 应用

本文件创建一个 Gradio Web 界面，用于实时监控 4 个交易员的交易状态。

功能：
  - 每个交易员显示：投资组合价值、损益曲线、持仓、交易记录、执行日志
  - 自动刷新：价值和图表每 120 秒刷新，日志每 0.5 秒刷新
  - 深色主题界面

运行方式：python app.py
"""

import gradio as gr
from util import css, js, Color
import pandas as pd
from trading_floor import names, lastnames, short_model_names
import plotly.express as px
from accounts import Account
from database import read_log

# 日志类型 → 颜色映射，用于在 UI 中区分不同类型的日志
mapper = {
    "trace": Color.WHITE,     # 追踪事件 → 白色
    "agent": Color.CYAN,      # Agent 事件 → 青色
    "function": Color.GREEN,  # 函数调用 → 绿色
    "generation": Color.YELLOW,  # LLM 生成 → 黄色
    "response": Color.MAGENTA,   # 响应 → 品红色
    "account": Color.RED,     # 账户操作 → 红色
}


class Trader:
    """交易员数据模型 - 用于 UI 展示。

    与 traders.py 中的 Trader 类不同，这个类只负责数据展示，
    不涉及 AI Agent 或 MCP 服务器。
    """

    def __init__(self, name: str, lastname: str, model_name: str):
        self.name = name
        self.lastname = lastname
        self.model_name = model_name
        self.account = Account.get(name)

    def reload(self):
        """从数据库重新加载账户数据"""
        self.account = Account.get(self.name)

    def get_title(self) -> str:
        """生成交易员标题 HTML"""
        return f"<div style='text-align: center;font-size:34px;'>{self.name}<span style='color:#ccc;font-size:24px;'> ({self.model_name}) - {self.lastname}</span></div>"

    def get_strategy(self) -> str:
        """获取投资策略文本"""
        return self.account.get_strategy()

    def get_portfolio_value_df(self) -> pd.DataFrame:
        """将投资组合价值时间序列转换为 DataFrame"""
        df = pd.DataFrame(self.account.portfolio_value_time_series, columns=["datetime", "value"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def get_portfolio_value_chart(self):
        """生成投资组合价值折线图（Plotly）"""
        df = self.get_portfolio_value_df()
        fig = px.line(df, x="datetime", y="value")
        margin = dict(l=40, r=20, t=20, b=40)
        fig.update_layout(
            height=300,
            margin=margin,
            xaxis_title=None,
            yaxis_title=None,
            paper_bgcolor="#bbb",
            plot_bgcolor="#dde",
        )
        fig.update_xaxes(tickformat="%m/%d", tickangle=45, tickfont=dict(size=8))
        fig.update_yaxes(tickfont=dict(size=8), tickformat=",.0f")
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        """将持仓转换为 DataFrame"""
        holdings = self.account.get_holdings()
        if not holdings:
            return pd.DataFrame(columns=["Symbol", "Quantity"])
        df = pd.DataFrame(
            [{"Symbol": symbol, "Quantity": quantity} for symbol, quantity in holdings.items()]
        )
        return df

    def get_transactions_df(self) -> pd.DataFrame:
        """将交易记录转换为 DataFrame"""
        transactions = self.account.list_transactions()
        if not transactions:
            return pd.DataFrame(columns=["Timestamp", "Symbol", "Quantity", "Price", "Rationale"])
        return pd.DataFrame(transactions)

    def get_portfolio_value(self) -> str:
        """生成投资组合价值的 HTML 显示（带颜色标识盈亏）"""
        portfolio_value = self.account.calculate_portfolio_value() or 0.0
        pnl = self.account.calculate_profit_loss(portfolio_value) or 0.0
        color = "green" if pnl >= 0 else "red"
        emoji = "⬆" if pnl >= 0 else "⬇"
        return f"<div style='text-align: center;background-color:{color};'><span style='font-size:32px'>${portfolio_value:,.0f}</span><span style='font-size:24px'>&nbsp;&nbsp;&nbsp;{emoji}&nbsp;${pnl:,.0f}</span></div>"

    def get_logs(self, previous=None) -> str:
        """获取最近的日志条目并格式化为彩色 HTML"""
        logs = read_log(self.name, last_n=13)
        response = ""
        for log in logs:
            timestamp, type, message = log
            color = mapper.get(type, Color.WHITE).value
            response += f"<span style='color:{color}'>{timestamp} : [{type}] {message}</span><br/>"
        response = f"<div style='height:250px; overflow-y:auto;'>{response}</div>"
        # 仅在内容变化时返回新值，避免不必要的 UI 刷新
        if response != previous:
            return response
        return gr.update()


class TraderView:
    """交易员 UI 视图 - 构建单个交易员的界面组件。

    每个交易员的面板包含：
      - 标题（名称 + 模型 + 风格）
      - 投资组合价值（大数字 + 盈亏）
      - 价值走势图（Plotly 折线图）
      - 执行日志（彩色滚动区域）
      - 持仓表格
      - 交易记录表格
    """

    def __init__(self, trader: Trader):
        self.trader = trader
        self.portfolio_value = None
        self.chart = None
        self.holdings_table = None
        self.transactions_table = None

    def make_ui(self):
        """构建 UI 组件"""
        with gr.Column():
            gr.HTML(self.trader.get_title())
            with gr.Row():
                self.portfolio_value = gr.HTML(self.trader.get_portfolio_value)
            with gr.Row():
                self.chart = gr.Plot(
                    self.trader.get_portfolio_value_chart, container=True, show_label=False
                )
            with gr.Row(variant="panel"):
                self.log = gr.HTML(self.trader.get_logs)
            with gr.Row():
                self.holdings_table = gr.Dataframe(
                    value=self.trader.get_holdings_df,
                    label="Holdings",
                    headers=["Symbol", "Quantity"],
                    row_count=(5, "dynamic"),
                    col_count=2,
                    max_height=300,
                    elem_classes=["dataframe-fix-small"],
                )
            with gr.Row():
                self.transactions_table = gr.Dataframe(
                    value=self.trader.get_transactions_df,
                    label="Recent Transactions",
                    headers=["Timestamp", "Symbol", "Quantity", "Price", "Rationale"],
                    row_count=(5, "dynamic"),
                    col_count=5,
                    max_height=300,
                    elem_classes=["dataframe-fix"],
                )

        # 定时刷新：价值和图表每 120 秒刷新
        timer = gr.Timer(value=120)
        timer.tick(
            fn=self.refresh,
            inputs=[],
            outputs=[
                self.portfolio_value,
                self.chart,
                self.holdings_table,
                self.transactions_table,
            ],
            show_progress="hidden",
            queue=False,
        )
        # 日志每 0.5 秒刷新（更频繁，因为日志更新快）
        log_timer = gr.Timer(value=0.5)
        log_timer.tick(
            fn=self.trader.get_logs,
            inputs=[self.log],
            outputs=[self.log],
            show_progress="hidden",
            queue=False,
        )

    def refresh(self):
        """刷新所有数据组件"""
        self.trader.reload()
        return (
            self.trader.get_portfolio_value(),
            self.trader.get_portfolio_value_chart(),
            self.trader.get_holdings_df(),
            self.trader.get_transactions_df(),
        )


def create_ui():
    """创建主 Gradio UI。

    布局：4 个交易员面板并排显示（每列一个交易员）。

    Returns:
        gr.Blocks: Gradio 应用实例
    """
    traders = [
        Trader(trader_name, lastname, model_name)
        for trader_name, lastname, model_name in zip(names, lastnames, short_model_names)
    ]
    trader_views = [TraderView(trader) for trader in traders]

    with gr.Blocks(
        title="Traders", css=css, js=js, theme=gr.themes.Default(primary_hue="sky"), fill_width=True
    ) as ui:
        with gr.Row():
            for trader_view in trader_views:
                trader_view.make_ui()

    return ui


if __name__ == "__main__":
    ui = create_ui()
    ui.launch(inbrowser=True)
