"""信息汇总：把多来源整合成结构化简报。"""
from datetime import datetime

from data_sources import fund as fund_ds
from src import diagnosis, metrics


def build_report(fund_code: str) -> str:
    """生成基金结构化简报：概况 / 业绩 / 持仓 / 风险点 / 近期公告。"""
    year = str(datetime.now().year)
    nav = fund_ds.get_fund_nav(fund_code)
    hold = fund_ds.get_fund_holdings(fund_code, year)
    ind = fund_ds.get_fund_industry_allocation(fund_code, year)
    reports = fund_ds.get_fund_reports(fund_code)

    if nav.empty:
        return f"未找到基金 {fund_code} 的数据。"

    recent = nav.tail(252)
    latest = nav.iloc[-1]
    fund_name = reports["基金名称"].iloc[0] if not reports.empty else fund_code

    lines = [f"# 基金简报：{fund_name}（{fund_code}）", ""]

    # 一、基本概况
    lines += [
        "## 一、基本概况",
        f"- 最新单位净值：{latest['单位净值']}（{latest['净值日期']}）",
        f"- 近 1 年收益率：{metrics.period_return(recent):.2f}%",
        "",
    ]

    # 二、业绩与风险（近1年）
    lines += [
        "## 二、业绩与风险（近 1 年）",
        f"- 收益率：{metrics.period_return(recent):.2f}%",
        f"- 年化波动率：{metrics.annualized_volatility(recent):.2f}%",
        f"- 最大回撤：{metrics.max_drawdown(recent):.2f}%",
        "",
    ]

    # 三、前十大重仓（最新季度）
    lines.append("## 三、前十大重仓（最新季度）")
    h = metrics.latest_quarter_holdings(hold)
    if not h.empty:
        for _, r in h.nlargest(10, "占净值比例").iterrows():
            lines.append(f"- {r['股票名称']}（{r['股票代码']}）：{r['占净值比例']}%")
    else:
        lines.append("- （暂无持仓数据）")
    lines.append("")

    # 四、风险点
    lines.append("## 四、风险点")
    points = diagnosis.diagnose(nav, hold, ind)
    if points:
        for p in points:
            lines.append(f"- {p['metric']}：{p['value']} → {p['risk']}")
    else:
        lines.append("- 未发现明显风险点（在设定阈值内）。")
    lines.append("")

    # 五、近期公告
    lines.append("## 五、近期公告")
    if not reports.empty:
        recent_reports = reports[["公告标题", "公告日期"]].sort_values("公告日期", ascending=False).head(5)
        for _, r in recent_reports.iterrows():
            lines.append(f"- {r['公告日期']}：{r['公告标题']}")
    else:
        lines.append("- （暂无公告）")

    return "\n".join(lines)
