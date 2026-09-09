"""基金投研 Agent 图形化测试台（Gradio）。

运行：.venv/bin/python app.py
"""
from datetime import datetime

import gradio as gr
import plotly.graph_objects as go

from data_sources import fund as fund_ds
from src import backtest, diagnosis, metrics
from src.loop import run

# dataviz 参考调色板（light 模式）
BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

YEAR = str(datetime.now().year)


def _base_layout(fig: go.Figure, title: str, showlegend: bool) -> go.Figure:
    fig.update_layout(
        title=title,
        template=None,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=INK, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        xaxis=dict(gridcolor=GRID, zeroline=False, linecolor=MUTED),
        yaxis=dict(gridcolor=GRID, zeroline=False, linecolor=MUTED),
        margin=dict(l=48, r=20, t=48, b=40),
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def _nav_figure(nav_df) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=nav_df["净值日期"], y=nav_df["单位净值"],
        mode="lines", name="单位净值", line=dict(color=BLUE, width=2),
    ))
    return _base_layout(fig, "单位净值走势", showlegend=False)


def _industry_figure(ind_df) -> go.Figure:
    latest = ind_df[ind_df["截止时间"] == ind_df["截止时间"].max()]
    latest = latest.sort_values("占净值比例", ascending=True).tail(8)
    fig = go.Figure(go.Bar(
        x=latest["占净值比例"], y=latest["行业类别"],
        orientation="h", marker_color=BLUE,
        text=[f"{v:.1f}%" for v in latest["占净值比例"]], textposition="outside",
    ))
    return _base_layout(fig, "行业配置（最新报告期）", showlegend=False)


def _backtest_figure(nav_df) -> go.Figure:
    recent = nav_df.tail(252 * 3)  # 近 3 年
    eh, ih = backtest.buy_hold(recent, {"initial_capital": 10000})
    ed, id_ = backtest.dca(recent, {"amount": 1000})
    x = recent["净值日期"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=(eh / ih - 1) * 100, mode="lines",
                             name="买入持有", line=dict(color=BLUE, width=2)))
    fig.add_trace(go.Scatter(x=x, y=(ed / id_ - 1) * 100, mode="lines",
                             name="定投", line=dict(color=ORANGE, width=2)))
    fig.update_yaxes(title="累计收益率 %")
    return _base_layout(fig, "回测净值曲线（近 3 年，归一化为收益率）", showlegend=True)


def render_fund(fund_code: str):
    """输入基金代码，返回净值图 / 行业图 / 持仓表 / 风险点 / 回测图。"""
    fund_code = fund_code.strip()
    try:
        nav = fund_ds.get_fund_nav(fund_code)
        hold = fund_ds.get_fund_holdings(fund_code, YEAR)
        ind = fund_ds.get_fund_industry_allocation(fund_code, YEAR)
    except Exception as e:
        raise gr.Error(f"数据获取失败：{e}")

    nav_fig = _nav_figure(nav)
    industry_fig = _industry_figure(ind)

    h = metrics.latest_quarter_holdings(hold).nlargest(10, "占净值比例")
    holdings_df = (h[["股票代码", "股票名称", "占净值比例"]]
                   .rename(columns={"占净值比例": "占净值比例%"})
                   .reset_index(drop=True))

    points = diagnosis.diagnose(nav, hold, ind)
    if points:
        risk_md = "**风险点**\n\n" + "\n".join(
            f"- {p['metric']}：{p['value']} → {p['risk']}" for p in points
        )
    else:
        risk_md = "**风险点**\n\n- 未发现明显风险点（在设定阈值内）。"

    backtest_fig = _backtest_figure(nav)

    return nav_fig, industry_fig, holdings_df, risk_md, backtest_fig


def chat_fn(message, history):
    return run(message)


with gr.Blocks(title="基金投研 Agent 测试台") as demo:
    gr.Markdown("# 基金投研 Agent 测试台")

    with gr.Tab("对话"):
        gr.ChatInterface(fn=chat_fn)

    with gr.Tab("基金数据"):
        with gr.Row():
            code = gr.Textbox(label="基金代码", value="110022", scale=2)
            btn = gr.Button("查询", scale=1)
        with gr.Row():
            nav_plot = gr.Plot(label="净值")
            industry_plot = gr.Plot(label="行业配置")
        with gr.Row():
            holdings_table = gr.Dataframe(label="前十大持仓（最新季度）", interactive=False)
            risk_md = gr.Markdown()
        backtest_plot = gr.Plot(label="回测")
        btn.click(render_fund, inputs=code,
                  outputs=[nav_plot, industry_plot, holdings_table, risk_md, backtest_plot])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")
