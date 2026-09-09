"""T4 补测：loop 的 forbid / require_permission / allow 分支（确定性，不依赖 LLM）。

运行：python tests/test_loop_guards.py   （或 pytest tests/）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 让 src/tools 可导入

from src.guards.checks import register_guard_hooks
from src.loop import _handle_tool_call

register_guard_hooks()  # 模块加载时注册（幂等）


def _tc(name: str, args: dict) -> dict:
    return {"name": name, "args": args}


def test_forbid():
    """🔴 黑名单工具 → 硬拦截，返回拦截原因。"""
    out = _handle_tool_call(_tc("trade_execute", {}), ask_user=lambda _: "y")
    assert "已拦截" in out, f"forbid 应拦截，实际：{out}"


def test_permission_denied():
    """🟡 需许可 + 用户拒绝 → 提示拒绝。"""
    out = _handle_tool_call(_tc("db_write", {}), ask_user=lambda _: "n")
    assert "拒绝" in out, f"拒绝后应提示，实际：{out}"


def test_permission_granted():
    """🟡 需许可 + 用户允许 → 先询问用户（ask_user 被调用）。"""
    calls = []
    _handle_tool_call(_tc("db_write", {}), ask_user=lambda q: calls.append(q) or "y")
    assert calls, "ask_user 应被调用（需许可流程）"


def test_allow():
    """🟢 放行 → 调用注册表 call_tool（monkeypatch 避免网络依赖）。"""
    import src.loop as loop_mod
    orig = loop_mod.call_tool
    loop_mod.call_tool = lambda name, args: f"CALLED:{name}"
    try:
        out = _handle_tool_call(_tc("any_tool", {"x": 1}), ask_user=lambda _: "n")
        assert out == "CALLED:any_tool", f"放行后应调用 call_tool，实际：{out}"
    finally:
        loop_mod.call_tool = orig


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"✅ {fn.__name__}")
    print(f"全部 {len(tests)} 项通过")
