"""网络请求重试。"""
from tenacity import retry, stop_after_attempt, wait_fixed


def retry_network(fn):
    """失败自动重试：最多 3 次，每次间隔 2 秒。"""
    return retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)(fn)
