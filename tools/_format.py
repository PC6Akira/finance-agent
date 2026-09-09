"""工具输出格式化辅助。"""


def df_to_str(df, max_rows: int = 10) -> str:
    """DataFrame 转可读字符串，限制行数。"""
    if df is None or getattr(df, "empty", True):
        return "（无数据）"
    return df.head(max_rows).to_string(index=False)


def truncate(s, n: int = 120) -> str:
    """截断长文本。"""
    s = s or ""
    return s if len(s) <= n else s[:n] + "…"
