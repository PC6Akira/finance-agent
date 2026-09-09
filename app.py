"""基金投研 Agent 图形化测试台（Gradio）。

运行：.venv/bin/python app.py
"""
from datetime import datetime

import gradio as gr
import pandas as pd
import plotly.graph_objects as go

from data_sources import fund as fund_ds
from data_sources import news as news_ds
from data_sources import search as search_ds
from src import auth, backtest, diagnosis, metrics, recommend, user
from src.loop import run

# dataviz 参考调色板（light 模式）
BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

YEAR = str(datetime.now().year)


# --- 图表 ---

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
    recent = nav_df.tail(252 * 3)
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
    risk_md = "**风险点**\n\n" + (
        "\n".join(f"- {p['metric']}：{p['value']} → {p['risk']}" for p in points)
        if points else "- 未发现明显风险点（在设定阈值内）。"
    )

    backtest_fig = _backtest_figure(nav)
    return nav_fig, industry_fig, holdings_df, risk_md, backtest_fig


# --- 数据源测试 ---

def _test_nav(fund_code):
    return fund_ds.get_fund_nav(fund_code.strip())


def _test_holdings(fund_code):
    return fund_ds.get_fund_holdings(fund_code.strip(), YEAR)


def _test_industry(fund_code):
    return fund_ds.get_fund_industry_allocation(fund_code.strip(), YEAR)


def _test_reports(fund_code):
    return fund_ds.get_fund_reports(fund_code.strip())


def _test_cls_news():
    return news_ds.get_cls_news()[["标题", "发布日期", "发布时间"]]


def _test_personnel(fund_code):
    return news_ds.get_fund_personnel_announcements(fund_code.strip())


def _test_dividend(fund_code):
    return news_ds.get_fund_dividend_announcements(fund_code.strip())


def _test_search(query):
    return pd.DataFrame(search_ds.bocha_search(query, 5))


# --- 账户 / 持仓 / 推荐 ---

def _holdings_df(username):
    rows = user.list_holdings(username)
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=["fund_code", "fund_name", "amount", "cost"])


def _question_updates(username):
    qs = recommend.generate_questions(username)
    return [
        gr.update(value=qs[i], visible=True) if i < len(qs) else gr.update(value="", visible=False)
        for i in range(3)
    ]


def do_login(username, password):
    ok, msg = auth.login(username, password)
    if not ok:
        return "", f"❌ {msg}", gr.update(visible=False), _holdings_df(""), *_question_updates("")
    return username, f"✅ {msg}", gr.update(visible=True), _holdings_df(username), *_question_updates(username)


def do_register(username, password):
    ok, msg = auth.register(username, password)
    return f"{'✅' if ok else '❌'} {msg}"


def do_logout():
    return "", "已退出登录", gr.update(visible=False), _holdings_df(""), *_question_updates("")


def add_holding_ui(username, fund_code, amount, cost):
    if not username:
        return "请先登录", _holdings_df(""), *_question_updates("")
    ok, msg = user.add_holding(username, fund_code, amount, cost if cost else None)
    return f"{'✅' if ok else '❌'} {msg}", _holdings_df(username), *_question_updates(username)


def remove_holding_ui(username, fund_code):
    if username and fund_code:
        user.remove_holding(username, fund_code.strip())
    return _holdings_df(username), *_question_updates(username)


def respond(message, history, username):
    if not username:
        return history, "请先登录"
    message = (message or "").strip()
    if not message:
        return history, ""
    past = user.recent_messages(username, limit=20)  # 最近 10 轮
    reply = run(message, history=past)
    user.add_message(username, "user", message)
    user.add_message(username, "assistant", reply)
    history = history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
    return history, ""


with gr.Blocks(title="基金投研 Agent 测试台") as demo:
    state = gr.State("")

    # 登录区
    with gr.Row():
        username_in = gr.Textbox(label="用户名", scale=2)
        password_in = gr.Textbox(label="密码", type="password", scale=2)
        login_btn = gr.Button("登录", scale=1)
        register_btn = gr.Button("注册", scale=1)
        logout_btn = gr.Button("退出登录", scale=1)
    auth_msg = gr.Markdown()

    with gr.Column(visible=False) as main:
        gr.Markdown("# 基金投研 Agent 测试台")

        with gr.Tab("对话"):
            with gr.Row():
                rec1 = gr.Button("", scale=1)
                rec2 = gr.Button("", scale=1)
                rec3 = gr.Button("", scale=1)
            chatbot = gr.Chatbot(height=480)
            msg = gr.Textbox(placeholder="输入你的问题，例如：我持有的基金昨天涨跌多少？", container=False)

        with gr.Tab("我的持仓"):
            with gr.Row():
                add_code = gr.Textbox(label="基金代码", scale=2)
                add_amount = gr.Number(label="持有金额", scale=1)
                add_cost = gr.Number(label="成本价（可空）", scale=1)
                add_btn = gr.Button("添加持仓", scale=1)
            holdings_df = gr.Dataframe(label="我的持仓", interactive=False)
            with gr.Row():
                remove_code = gr.Textbox(label="要删除的基金代码", scale=2)
                remove_btn = gr.Button("删除", scale=1)
            hold_msg = gr.Markdown()

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

        with gr.Tab("数据源测试"):
            gr.Markdown("#### 基金数据源（akshare）")
            with gr.Row():
                code2 = gr.Textbox(label="基金代码", value="110022", scale=3)
                btn_nav = gr.Button("净值", scale=1)
                btn_hold = gr.Button("持仓", scale=1)
                btn_ind = gr.Button("行业配置", scale=1)
                btn_rep = gr.Button("报告公告", scale=1)
            fund_out = gr.Dataframe(label="基金数据")

            gr.Markdown("#### 资讯数据源（akshare）")
            with gr.Row():
                btn_cls = gr.Button("财联社舆情", scale=1)
                btn_pers = gr.Button("人事公告", scale=1)
                btn_div = gr.Button("分红公告", scale=1)
            news_out = gr.Dataframe(label="资讯数据")

            gr.Markdown("#### 搜索数据源（博查 Bocha）")
            with gr.Row():
                query = gr.Textbox(label="搜索关键词", value="基金经理访谈", scale=3)
                btn_search = gr.Button("搜索", scale=1)
            search_out = gr.Dataframe(label="搜索结果")

            btn_nav.click(_test_nav, inputs=code2, outputs=fund_out)
            btn_hold.click(_test_holdings, inputs=code2, outputs=fund_out)
            btn_ind.click(_test_industry, inputs=code2, outputs=fund_out)
            btn_rep.click(_test_reports, inputs=code2, outputs=fund_out)
            btn_cls.click(_test_cls_news, outputs=news_out)
            btn_pers.click(_test_personnel, inputs=code2, outputs=news_out)
            btn_div.click(_test_dividend, inputs=code2, outputs=news_out)
            btn_search.click(_test_search, inputs=query, outputs=search_out)

    # 事件绑定
    login_btn.click(do_login, [username_in, password_in],
                    [state, auth_msg, main, holdings_df, rec1, rec2, rec3])
    register_btn.click(do_register, [username_in, password_in], [auth_msg])
    logout_btn.click(do_logout, None, [state, auth_msg, main, holdings_df, rec1, rec2, rec3])
    msg.submit(respond, [msg, chatbot, state], [chatbot, msg])
    rec1.click(respond, [rec1, chatbot, state], [chatbot, msg])
    rec2.click(respond, [rec2, chatbot, state], [chatbot, msg])
    rec3.click(respond, [rec3, chatbot, state], [chatbot, msg])
    add_btn.click(add_holding_ui, [state, add_code, add_amount, add_cost],
                  [hold_msg, holdings_df, rec1, rec2, rec3])
    remove_btn.click(remove_holding_ui, [state, remove_code], [holdings_df, rec1, rec2, rec3])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1")
