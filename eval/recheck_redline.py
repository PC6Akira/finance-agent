"""用语义判定重审红线违规率（对已保存的 B 层结果，不重跑 loop）。

用法：.venv/bin/python eval/recheck_redline.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.redline import check_redline_semantic

RESULTS = Path(__file__).parent / "results" / "b_results.jsonl"


def main() -> None:
    rows = [json.loads(l) for l in open(RESULTS, encoding="utf-8")]
    on = [r for r in rows if r["enable_verifier"]]

    total = viol = fail = 0
    by_cat: dict[str, dict] = {}
    false_pos: list[tuple] = []   # 关键词报了，但语义判合规 → 误报
    true_viol: list[tuple] = []   # 语义判真的违规
    for r in on:
        kw = r["redline_hits"]
        sem, reasons = check_redline_semantic(r["output"])
        cat = r["category"]
        by_cat.setdefault(cat, {"n": 0, "viol": 0})
        by_cat[cat]["n"] += 1
        if sem is None:
            fail += 1
            continue
        total += 1
        if sem:
            viol += 1
            by_cat[cat]["viol"] += 1
            true_viol.append((r["id"], r["question"], reasons))
        elif kw:
            false_pos.append((r["id"], r["question"], kw))

    print(f"语义红线违规率（开 verifier）= {viol}/{total} = {viol / total:.4f}  （判定失败 {fail} 条）\n")
    print("按类别：")
    for cat, m in sorted(by_cat.items()):
        v, n = m["viol"], m["n"]
        print(f"  {cat:<6} {v}/{n} = {v / n:.3f}")
    print(f"\n关键词误报（关键词报了但语义判合规）共 {len(false_pos)} 条：")
    for i, q, kw in false_pos:
        print(f"  {i} 命中{kw}  问:{q[:28]}")
    print(f"\n语义判真的违规共 {len(true_viol)} 条：")
    for i, q, reasons in true_viol:
        print(f"  {i} 问:{q[:28]} → {reasons}")


if __name__ == "__main__":
    main()
