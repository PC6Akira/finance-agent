"""eval 评测 harness：monkeypatch 工具注册表为假数据 → 跑 run() → 收集输出。

用法：
    python eval/harness.py --self-test
    python eval/harness.py --cases eval/fixtures/b_cases.jsonl --out eval/results.jsonl
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.tools import tool

from tools import registry
from src import loop as loop_mod


# ---------- 假基金宇宙 ----------

def load_universe(path: str | Path) -> dict:
    """读取假基金宇宙 JSON：{fund_code: {nav, holdings, industry, reports}}。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_cases(path: str | Path) -> list[dict]:
    """读取 JSONL 样本：每行 {id, category, question}。"""
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _fmt_nav(fund: dict) -> str:
    lines = [f"{r['date']} 净值 {r['nav']} 日增长 {r['daily']}%" for r in fund["nav"]]
    return "单位净值走势：\n" + "\n".join(lines)


def _fmt_holdings(fund: dict) -> str:
    lines = [f"{h['code']} {h['name']} 占净值 {h['pct']}%" for h in fund["holdings"]]
    return "重仓股持仓：\n" + "\n".join(lines)


def _fmt_industry(fund: dict) -> str:
    lines = [f"{i['industry']} 占净值 {i['pct']}%" for i in fund["industry"]]
    return "行业配置：\n" + "\n".join(lines)


def _fmt_reports(fund: dict) -> str:
    lines = [f"{r['title']} {r['date']}" for r in fund["reports"]]
    return "定期报告公告：\n" + "\n".join(lines)


def build_fake_tools(universe: dict) -> dict:
    """按真实工具同名同参，构造返回假数据的 tool 字典（dict[str, BaseTool]）。"""
    @tool
    def get_fund_nav(fund_code: str) -> str:
        """查询基金单位净值走势，看最新净值和近期涨跌。fund_code: 6 位基金代码，如 110022。"""
        fund = universe.get(fund_code)
        return _fmt_nav(fund) if fund else f"未找到基金 {fund_code}"

    @tool
    def get_fund_holdings(fund_code: str, year: str = "2026") -> str:
        """查询基金季度重仓股持仓（占净值比例）。fund_code: 6 位基金代码。"""
        fund = universe.get(fund_code)
        return _fmt_holdings(fund) if fund else f"未找到基金 {fund_code}"

    @tool
    def get_fund_industry_allocation(fund_code: str, year: str = "2026") -> str:
        """查询基金季报的行业配置（各行业占净值比例）。fund_code: 6 位基金代码。"""
        fund = universe.get(fund_code)
        return _fmt_industry(fund) if fund else f"未找到基金 {fund_code}"

    @tool
    def get_fund_reports(fund_code: str) -> str:
        """查询基金的定期报告（季报/年报）公告列表。fund_code: 6 位基金代码。"""
        fund = universe.get(fund_code)
        return _fmt_reports(fund) if fund else f"未找到基金 {fund_code}"

    return {
        t.name: t
        for t in [get_fund_nav, get_fund_holdings, get_fund_industry_allocation, get_fund_reports]
    }


# ---------- patch + 运行 ----------

def run_case(goal: str, universe: dict, enable_verifier: bool = True) -> dict:
    """用假宇宙跑一个 goal，返回 {goal, enable_verifier, output, tool_calls}。

    注入方式：替换 tools.registry._TOOLS（loop 的 list_tools/call_tool 读它时生效），
    并包装 loop.call_tool 记录每次调用 + 返回内容。
    """
    fake_tools = build_fake_tools(universe)
    orig_tools = registry._TOOLS
    orig_call = loop_mod.call_tool
    calls = []

    def recording_call(name: str, args: dict) -> str:
        result = orig_call(name, args)
        calls.append({"tool": name, "args": args, "output": result})
        return result

    registry._TOOLS = fake_tools
    loop_mod.call_tool = recording_call
    try:
        output = loop_mod.run(goal, enable_verifier=enable_verifier)
    finally:
        registry._TOOLS = orig_tools
        loop_mod.call_tool = orig_call
    return {"goal": goal, "enable_verifier": enable_verifier, "output": output, "tool_calls": calls}


def run_cases(cases: list[dict], universe: dict, enable_verifier: bool = True) -> list[dict]:
    """批量跑样本，返回结果列表（追加 enable_verifier 字段）。"""
    return [run_case(c["question"], universe, enable_verifier=enable_verifier) for c in cases]


# ---------- 自检（不调 LLM、不联网） ----------

def self_test() -> None:
    universe = load_universe(Path(__file__).parent / "fixtures" / "universe.json")
    fake_tools = build_fake_tools(universe)
    assert set(fake_tools) == {
        "get_fund_nav", "get_fund_holdings", "get_fund_industry_allocation", "get_fund_reports",
    }, fake_tools.keys()

    orig = registry._TOOLS
    registry._TOOLS = fake_tools
    try:
        nav_out = registry.call_tool("get_fund_nav", {"fund_code": "110022"})
        assert "2.908" in nav_out, nav_out
        hold_out = registry.call_tool("get_fund_holdings", {"fund_code": "110022", "year": "2026"})
        assert "贵州茅台" in hold_out, hold_out
        assert "未找到" in registry.call_tool("get_fund_nav", {"fund_code": "999999"})
    finally:
        registry._TOOLS = orig
    print("✅ harness 自检通过：假数据注入生效，call_tool 返回假基金数据（未联网）")


def main() -> None:
    args = sys.argv[1:]
    if "--self-test" in args:
        self_test()
        return
    if "--check-cases" in args:
        from collections import Counter
        i = args.index("--check-cases")
        cases = load_cases(args[i + 1])
        print(f"样本数：{len(cases)}")
        for cat, n in sorted(Counter(c["category"] for c in cases).items()):
            print(f"  {cat}: {n}")
        ids = [c["id"] for c in cases]
        assert len(ids) == len(set(ids)), "存在重复 id"
        print("✅ 样本校验通过：无重复 id，分类统计如上")
        return
    print("用法：--self-test 或 --check-cases PATH（--cases 全量跑在 judge/redline 就绪后接入）")


if __name__ == "__main__":
    main()
