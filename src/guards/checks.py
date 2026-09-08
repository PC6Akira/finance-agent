"""权限检查：每个检查独立注册为 PreToolUse hook。"""
from src.guards.policy import BLACKLIST_TOOLS, FORBIDDEN_FLAGS, NEEDS_PERMISSION
from src.hooks import ALLOW, HookResult, register


def blacklist_check(block: dict) -> HookResult:
    """🔴 黑名单：命中即禁止。"""
    if block["tool"] in BLACKLIST_TOOLS:
        return HookResult("forbid", f"⛔ 已拦截：工具 {block['tool']} 属黑名单，拒绝执行。")
    return ALLOW


def permission_check(block: dict) -> HookResult:
    """🟡 需许可：命中即要求用户确认。"""
    if block["tool"] in NEEDS_PERMISSION:
        return HookResult("require_permission", f"🔒 工具 {block['tool']} 需要你的许可才能执行。")
    return ALLOW


def args_check(block: dict) -> HookResult:
    """🔴 参数校验：命中禁止标志即拒绝。"""
    args = block.get("args") or {}
    for flag in FORBIDDEN_FLAGS:
        if args.get(flag):
            return HookResult("forbid", f"⛔ 已拦截：参数 {flag}=True 命中禁止模式。")
    return ALLOW


def register_guard_hooks() -> None:
    """注册所有权限检查 hook（幂等）。"""
    register("PreToolUse", blacklist_check)
    register("PreToolUse", permission_check)
    register("PreToolUse", args_check)
