"""汇总评测：跑 A 层 + B 层，算出 5 个指标，打印 + 落盘 JSONL/CSV。

用法：
    .venv/bin/python eval/report.py --limit 3 --a-limit 5   # 冒烟
    .venv/bin/python eval/report.py --a-only                 # 只跑 A 层
    .venv/bin/python eval/report.py                          # 全量（会调大量 DeepSeek）
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.verify import _check
from eval.harness import build_fund_data_text, load_cases, load_universe, run_case
from eval.judge import judge
from eval.redline import check_redline

FIXTURES = Path(__file__).parent / "fixtures"
UNIVERSE = load_universe(FIXTURES / "universe.json")


# ---------- A 层：precision / recall ----------

def run_a_layer(limit: int | None = None) -> dict:
    cases = load_cases(FIXTURES / "a_cases.jsonl")
    if limit:
        cases = cases[:limit]
    rows, tp, fp, fn, tn = [], 0, 0, 0, 0
    for c in cases:
        data_text = build_fund_data_text(c["fund_code"], UNIVERSE)
        ok, issues = _check(c["answer"], data_text)
        reported = not ok
        if c["has_error"] and reported:
            tp += 1
        elif c["has_error"] and not reported:
            fn += 1
        elif (not c["has_error"]) and reported:
            fp += 1
        else:
            tn += 1
        rows.append({**c, "verifier_ok": ok, "verifier_issues": issues})
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {"rows": rows, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall}


# ---------- B 层：含错率 / 净收益 / 红线 ----------

def run_b_layer(limit: int | None = None) -> dict:
    cases = load_cases(FIXTURES / "b_cases.jsonl")
    if limit:
        cases = cases[:limit]
    rows = []
    for c in cases:
        for ev in (False, True):
            r = run_case(c["question"], UNIVERSE, enable_verifier=ev)
            data_text = "\n\n".join(f"=== {tc['tool']} ===\n{tc['output']}" for tc in r["tool_calls"])
            has_err, errs = judge(r["output"], data_text)
            rows.append({
                "id": c["id"], "category": c["category"], "question": c["question"],
                "enable_verifier": ev, "output": r["output"],
                "judge_has_error": has_err, "judge_errors": errs,
                "redline_hits": check_redline(r["output"]),
            })
    return {"rows": rows}


def _err_rate(rs: list[dict]) -> tuple[float, int]:
    judged = [r["judge_has_error"] for r in rs if r["judge_has_error"] is not None]
    rate = (sum(judged) / len(judged)) if judged else 0.0
    return rate, len(rs) - len(judged)


def summarize_b(rows: list[dict]) -> dict:
    off = [r for r in rows if not r["enable_verifier"]]
    on = [r for r in rows if r["enable_verifier"]]
    off_rate, off_fail = _err_rate(off)
    on_rate, on_fail = _err_rate(on)
    on_viol = [r for r in on if r["redline_hits"]]
    redline_rate = len(on_viol) / len(on) if on else 0.0
    by_cat = {}
    for cat in sorted({r["category"] for r in on}):
        cat_rows = [r for r in on if r["category"] == cat]
        rate, _ = _err_rate(cat_rows)
        rl = sum(1 for r in cat_rows if r["redline_hits"]) / len(cat_rows) if cat_rows else 0.0
        by_cat[cat] = {"含错率": round(rate, 3), "红线违规率": round(rl, 3)}
    return {
        "基线含错率": round(off_rate, 4), "含错率_开verifier": round(on_rate, 4),
        "净收益": round(off_rate - on_rate, 4),
        "红线违规率": round(redline_rate, 4),
        "judge失败": off_fail + on_fail,
        "n_cases": len(on),
        "按类别": by_cat,
        "红线命中样例": [r["redline_hits"] for r in on_viol][:10],
    }


# ---------- 输出 ----------

def _dump(rows: list[dict], out_dir: Path, tag: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    jl = out_dir / f"{tag}.jsonl"
    with open(jl, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    if rows:
        with open(out_dir / f"{tag}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                r2 = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()}
                w.writerow(r2)
    print(f"已落盘：{jl} / {out_dir / (tag + '.csv')}")


def _print_summary(a: dict | None, b: dict | None) -> None:
    print("\n" + "=" * 60)
    print("评测结果")
    print("=" * 60)
    if a:
        print(f"\n【A 层 · verifier precision/recall】({len(a['rows'])} 条)")
        print(f"  TP={a['tp']}  FP={a['fp']}  FN={a['fn']}  TN={a['tn']}")
        print(f"  precision = {a['precision']:.3f}  （报出的问题里真问题占比）")
        print(f"  recall    = {a['recall']:.3f}  （真问题里被抓住占比）")
    if b:
        print(f"\n【B 层 · 含错率 / 净收益 / 红线】({b['n_cases']} 条 × 2 遍)")
        print(f"  基线含错率（关 verifier） = {b['基线含错率']:.4f}")
        print(f"  含错率（开 verifier）     = {b['含错率_开verifier']:.4f}")
        print(f"  净收益                     = {b['净收益']:.4f}")
        print(f"  红线违规率（开 verifier）  = {b['红线违规率']:.4f}")
        print(f"  judge 判定失败（待人工复核）= {b['judge失败']}")
        print("\n  按类别（开 verifier）：")
        for cat, m in b["按类别"].items():
            print(f"    {cat:<6} 含错率={m['含错率']}  红线违规率={m['红线违规率']}")
        if b["红线命中样例"]:
            print("\n  红线命中样例（前 10）：")
            for hits in b["红线命中样例"]:
                print(f"    {hits}")


def main() -> None:
    args = sys.argv[1:]
    a_limit = b_limit = None
    a_only = b_only = False
    if "--a-limit" in args:
        a_limit = int(args[args.index("--a-limit") + 1])
    if "--limit" in args:
        b_limit = int(args[args.index("--limit") + 1])
    if "--a-only" in args:
        a_only = True
    if "--b-only" in args:
        b_only = True

    out_dir = Path(__file__).parent / "results"

    a = b = None
    if not b_only:
        print("跑 A 层（verifier 判定器）…")
        a = run_a_layer(a_limit)
        _dump(a["rows"], out_dir, "a_results")
    if not a_only:
        print(f"跑 B 层（端到端，{'前 ' + str(b_limit) + ' 条' if b_limit else '全量'} × 开/关 verifier）…")
        b_rows = run_b_layer(b_limit)
        _dump(b_rows["rows"], out_dir, "b_results")
        b = summarize_b(b_rows["rows"])

    _print_summary(a, b)


if __name__ == "__main__":
    main()
