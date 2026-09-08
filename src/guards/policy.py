"""黑名单与许可策略常量 —— 权限模型的代码来源（不依赖 markdown/提示词）。

本文件是唯一执行依据，memory/permissions.md 只是给人看的一致性镜像。
"""

# 🔴 永不执行的工具名（黑名单）
BLACKLIST_TOOLS: set[str] = {
    "trade_execute",       # 任何交易下单
    "delete_db_records",   # 删除数据库记录
    "write_env_file",      # 写 .env / 密钥
}

# 🟡 需用户许可才能执行的工具名
NEEDS_PERMISSION: set[str] = {
    "db_write",
    "db_delete",
    "file_delete",
}

# 🔴 参数为真时禁止的标志
FORBIDDEN_FLAGS: set[str] = {
    "delete",
    "confirm_delete",
    "force",
}
