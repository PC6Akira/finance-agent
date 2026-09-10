"""verifier 辅助函数单测（确定性部分，不触发 LLM）。"""
from src.verify import _format_tool_outputs, _strip_fences


def test_strip_fences():
    assert _strip_fences('```json\n{"ok": true}\n```') == '{"ok": true}'
    assert _strip_fences('{"ok": false, "issues": []}') == '{"ok": false, "issues": []}'
    assert _strip_fences('  {"ok": true}  ') == '{"ok": true}'


def test_format_tool_outputs():
    s = _format_tool_outputs([("get_fund_nav", "净值 2.908"), ("get_fund_holdings", "贵州茅台")])
    assert "=== get_fund_nav ===" in s
    assert "净值 2.908" in s
    assert "=== get_fund_holdings ===" in s
    assert "贵州茅台" in s
