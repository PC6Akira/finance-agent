"""确保系统提示词包含红线 + 措辞边界（防回归）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "system.md").read_text(encoding="utf-8")


def test_has_red_line():
    assert "不预测未来收益率" in PROMPT
    assert "不给买卖建议" in PROMPT


def test_has_wording_guard():
    assert "措辞边界" in PROMPT
    for w in ["适合", "建议", "推荐", "关注", "买入", "卖出", "加仓", "减仓"]:
        assert w in PROMPT, f"应明确禁止「{w}」"


def test_has_fixed_pattern():
    assert "风险含义" in PROMPT
    assert "固定句式" in PROMPT


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"全部 {len(tests)} 项通过")
