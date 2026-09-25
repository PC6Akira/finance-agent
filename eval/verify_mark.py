"""验证「只标注不改写」方向：同一份 loop 原始输出，对比重答改写 vs 只标注的端到端含错。

方法（公平 A/B，隔离 verifier 步骤）：
  1. 每样本跑一次 goal loop（关闭 verifier），拿到原始回答 + 工具调用。
  2. 对这份原始输出分别套两种 verifier：regenerate=True（重答改写）与 False（只标注）。
  3. 用同一 judge 判两种最终输出的含错，对比错误集合。

用法：
    .venv/bin/python eval/verify_mark.py --limit 3   # 冒烟
    .venv/bin/python eval/verify_mark.py             # 全量 100 条
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.verify import verify_and_correct
from eval.harness import load_cases, load_universe, run_case
from eval.judge import judge

FIXTURES = Path(__file__).parent / "fixtures"
UNIVERSE = load_universe(FIXTURES / "universe.json")


def _data_text(tool_calls: list[dict]) -> str:
    return "\n\n".join(f"=== {tc['tool']} ===\n{tc['output']}" for tc in tool_calls)


def run(case: dict) -> dict:
    raw = run_case(case["question"], UNIVERSE, enable_verifier=False)
    calls = [(tc["tool"], tc["output"]) for tc in raw["tool_calls"]]
    data_text = _data_text(raw["tool_calls"])
    out_rewrite = verify_and_correct(raw["output"], calls, regenerate=True)
    out_mark = verify_and_correct(raw["output"], calls, regenerate=False)
    rewrite_err, _ = judge(out_rewrite, data_text)
    mark_err, _ = judge(out_mark, data_text)
    return {
        "id": case["id"], "category": case["category"], "question": case["question"],
        "raw": raw["output"],
        "rewrite_output": out_rewrite, "rewrite_err": rewrite_err,
        "mark_output": out_mark, "mark_err": mark_err,
        "mark_flagged": "⚠️" in out_mark,
    }


def main() -> None:
    args = sys.argv[1:]
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    cases = load_cases(FIXTURES / "b_cases.jsonl")
    if limit:
        cases = cases[:limit]

    rows = [run(c) for c in cases]

    err = lambda key: {r["id"] for r in rows if r[key] is True}
    none = lambda key: [r["id"] for r in rows if r[key] is None]
    e_rw, e_mk = err("rewrite_err"), err("mark_err")

    print("=" * 64)
    print(f"只标注不改写 · 公平 A/B（同一份原始输出）· {len(rows)} 条")
    print("=" * 64)
    print("\n【错误用例集合】")
    print(f"  重答改写 : {sorted(e_rw)}")
    print(f"  只标注   : {sorted(e_mk)}")
    print(f"\n【重答改写引入的新错（重答有、只标注无）】: {sorted(e_rw - e_mk)}")
    print(f"【只标注引入的新错（只标注有、重答无）】   : {sorted(e_mk - e_rw)}")
    print(f"\n【judge 判定失败】")
    print(f"  重答改写 : {none('rewrite_err')}")
    print(f"  只标注   : {none('mark_err')}")
    flagged = [r["id"] for r in rows if r["mark_flagged"]]
    print(f"\n【标注覆盖率】{len(flagged)}/{len(rows)} 条输出带 ⚠️ 标注")
    print(f"  被标注用例: {sorted(flagged)}")

    out = Path(__file__).parent / "results" / "verify_mark.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"\n已落盘：{out}")


if __name__ == "__main__":
    main()
