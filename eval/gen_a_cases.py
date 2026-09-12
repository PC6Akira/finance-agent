"""生成 A 层构造样本（eval/fixtures/a_cases.jsonl）。

A 层直接喂 _check(answer, data_text) 测 verifier 的 precision/recall：
- has_error=True  → verifier 应报（报了=TP，没报=FN）
- has_error=False → verifier 应放行（放了=TN，报了=FP）

每只非货币基金生成 20 条：TP 5 / FN 5 / TN 5 / FP 5，共 5 只 × 20 = 100 条。

运行：.venv/bin/python eval/gen_a_cases.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.harness import load_universe

FIXTURES = Path(__file__).parent / "fixtures"
FUNDS = ["110022", "050008", "000001", "161725", "005827"]  # 5 只非货币基金


def _gen_fund_cases(code: str, universe: dict, other_code: str) -> list[dict]:
    fund = universe[code]
    other = universe[other_code]
    nav = fund["nav"][-1]
    prev = fund["nav"][-2]
    h0 = fund["holdings"][0]
    i0 = fund["industry"][0]

    n = f"{nav['nav']:.3f}"
    p = f"{h0['pct']:.1f}"
    ip = f"{i0['pct']:.1f}"
    other_n = f"{other['nav'][-1]['nav']:.3f}"
    other_h = other["holdings"][0]

    # (kind, has_error, answer)
    specs = [
        # TP：明显编造/错配，应报
        ("TP", True, f"基金 {code} 最新单位净值是 {nav['nav'] + 1.0:.3f}。"),
        ("TP", True, f"基金 {code} 最新单位净值是 {other_n}。"),
        ("TP", True, f"基金 {code} 的第一大重仓股是 {other_h['name']}。"),
        ("TP", True, f"基金 {code} 的第一大重仓股 {h0['name']} 占净值 {other_h['pct']:.1f}%。"),
        ("TP", True, f"基金 {code} 的 {i0['industry']} 行业占比 99.0%。"),
        # FN：明显错但隐蔽，可能漏
        ("FN", True, f"基金 {code} 最新单位净值是 {nav['nav'] - 0.002:.3f}。"),
        ("FN", True, f"基金 {code} 的第一大重仓股 {h0['name']} 占净值 {h0['pct'] + 0.1:.1f}%。"),
        ("FN", True, f"基金 {code} 的 {i0['industry']} 行业占比 {i0['pct'] - 1.0:.1f}%。"),
        ("FN", True, f"基金 {code} 在 2024-06-03 的净值为 {n}。"),
        ("FN", True, f"基金 {code} 的第二大重仓股是 {h0['name']}，占净值 {p}%。"),
        # TN：完全正确，应放行
        ("TN", False, f"基金 {code} 最新单位净值是 {n}。"),
        ("TN", False, f"基金 {code} 的第一大重仓股是 {h0['name']}，占净值 {p}%。"),
        ("TN", False, f"基金 {code} 的 {i0['industry']} 行业占比 {ip}%。"),
        ("TN", False, f"基金 {code} 在 {nav['date']} 的净值为 {n}。"),
        ("TN", False, f"基金 {code} 的 {h0['name']} 占净值 {p}%。"),
        # FP：正确但表述"绕"，可能误报
        ("FP", False, f"基金 {code} 最新单位净值约 {nav['nav']:.2f}。"),
        ("FP", False, f"基金 {code} 的 {i0['industry']} 占比约 {round(i0['pct'])}%。"),
        ("FP", False, f"基金 {code} 最新单位净值为 {n} 元。"),
        ("FP", False, f"基金 {code} 第一大重仓股是 {h0['name']}，占比约 {p}%。"),
        ("FP", False, f"基金 {code} 最新净值 {n}，前一日 {prev['nav']:.3f}，日增长 {nav['daily']}%。"),
    ]
    return [
        {"fund_code": code, "kind": kind, "has_error": has_error, "answer": ans}
        for kind, has_error, ans in specs
    ]


def main() -> None:
    universe = load_universe(FIXTURES / "universe.json")
    cases = []
    for i, code in enumerate(FUNDS):
        other = FUNDS[(i + 1) % len(FUNDS)]
        cases.extend(_gen_fund_cases(code, universe, other))

    # 写 a_cases.jsonl（data_text 不落盘，评测时按 fund_code 从 universe 重建）
    out = FIXTURES / "a_cases.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for idx, c in enumerate(cases, 1):
            c = {"id": f"a{idx:03d}", **c}
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    from collections import Counter
    print(f"生成 {len(cases)} 条 A 层样本 -> {out}")
    for kind, n in sorted(Counter(c["kind"] for c in cases).items()):
        print(f"  {kind}: {n}")
    print(f"  has_error=True: {sum(c['has_error'] for c in cases)} / False: {len(cases) - sum(c['has_error'] for c in cases)}")


if __name__ == "__main__":
    main()
