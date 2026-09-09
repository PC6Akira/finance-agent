"""持仓诊断工具。"""
from datetime import datetime

from langchain_core.tools import tool

from data_sources import fund as fund_ds
from src import diagnosis


@tool
def diagnose_fund(fund_code: str) -> str:
    """对基金做持仓诊断，输出风险点提示（集中度/行业暴露/漂移/回撤）。fund_code: 6 位基金代码。"""
    year = str(datetime.now().year)
    nav = fund_ds.get_fund_nav(fund_code)
    hold = fund_ds.get_fund_holdings(fund_code, year)
    ind = fund_ds.get_fund_industry_allocation(fund_code, year)

    points = diagnosis.diagnose(nav, hold, ind)
    if not points:
        return "未发现明显风险点（在设定阈值内）。"
    return "持仓诊断风险点：\n" + "\n".join(
        f"- {p['metric']}：{p['value']} → {p['risk']}" for p in points
    )
