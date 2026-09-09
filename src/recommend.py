"""个性化推荐问题：根据用户持仓生成 3 个「您可能想问」。"""
from src import user


def generate_questions(username: str) -> list[str]:
    """按用户持仓生成 3 个推荐问题。无持仓时返回提示。"""
    holdings = user.list_holdings(username)
    if not holdings:
        return ["先添加你的持仓，我才能推荐问题"]

    holdings.sort(key=lambda h: h["amount"] or 0, reverse=True)
    top = holdings[0]
    name1 = top["fund_name"] or top["fund_code"]

    q1 = f"我持有的{name1}昨天涨跌多少？"
    q2 = "我的持仓有哪些风险点？"

    if len(holdings) >= 2:
        name2 = holdings[1]["fund_name"] or holdings[1]["fund_code"]
        q3 = f"对比我持有的{name1}和{name2}"
    else:
        q3 = f"分析我持有的{name1}的投资风格"

    return [q1, q2, q3]
