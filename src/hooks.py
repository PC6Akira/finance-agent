"""通用 hook 注册表：按事件分发检查函数，循环不直接调用具体检查。

用法：
    register("PreToolUse", some_check)
    result = trigger_hooks("PreToolUse", block)
"""
HOOKS: dict[str, list] = {}


class HookResult:
    """hook 检查结果。kind: allow | forbid | require_permission"""

    def __init__(self, kind: str, reason: str = ""):
        self.kind = kind
        self.reason = reason


ALLOW = HookResult("allow")


def register(event: str, fn) -> None:
    """注册一个 hook 到某个事件。幂等：同一函数不重复注册。"""
    lst = HOOKS.setdefault(event, [])
    if fn not in lst:
        lst.append(fn)


def trigger_hooks(event: str, block: dict) -> HookResult:
    """依次运行该事件的所有 hook，返回第一个非 allow 的结果；全过则返回 ALLOW。"""
    for fn in HOOKS.get(event, []):
        result = fn(block)
        if result.kind != "allow":
            return result
    return ALLOW
