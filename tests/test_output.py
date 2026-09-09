"""输出合规：免责声明统一注入 + 去重。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.output import finalize


def test_appends_disclaimer():
    out = finalize("基金 110022 近一年回撤较大")
    assert "不构成" in out


def test_no_duplicate():
    out = finalize("结论：风险较高。以上内容不构成任何投资建议。")
    assert out.count("不构成") == 1


def test_empty_text():
    assert "不构成" in finalize("")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"全部 {len(tests)} 项通过")
