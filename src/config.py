"""集中配置加载：读 .env（密钥）+ config.yaml（配置），合并为 Settings。"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent  # finance-agent/
ENV_PATH = BASE_DIR / ".env"
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

load_dotenv(str(ENV_PATH))


class Settings(BaseModel):
    # 密钥（来自 .env，缺失则为空串）
    deepseek_api_key: str = ""
    qwen_api_key: str = ""
    bocha_api_key: str = ""

    # 模型
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0
    embedding_model: str = "text-embedding-v3"

    # 存储（相对项目根，已解析为绝对路径）
    db_path: Path = BASE_DIR / "db" / "finance.db"
    chroma_path: Path = BASE_DIR / "chroma_db"

    # Redis（缓存 + 限流；连接失败自动降级，不影响业务）
    redis_url: str = "redis://localhost:6379/0"

    # goal loop
    max_steps: int = 12

    # 输出
    disclaimer: str = "本内容仅供参考，不构成任何投资建议。"

    # 服务启动（Gradio，部署时通过环境变量覆盖）
    gradio_server_name: str = "127.0.0.1"
    gradio_server_port: int = 7860
    gradio_auth_username: str = ""
    gradio_auth_password: str = ""


def _get(node: dict, dotted: str, default=None):
    """按 'a.b.c' 路径取嵌套字典值，缺失返回 default。"""
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def load_settings() -> Settings:
    raw = {}
    if CONFIG_PATH.exists():
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}

    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        qwen_api_key=os.getenv("QWEN_API_KEY", ""),
        bocha_api_key=os.getenv("BOCHA_API_KEY", ""),
        llm_model=_get(raw, "llm.model", "deepseek-chat"),
        llm_temperature=_get(raw, "llm.temperature", 0),
        embedding_model=_get(raw, "embedding.model", "text-embedding-v3"),
        db_path=BASE_DIR / _get(raw, "storage.db_path", "db/finance.db"),
        chroma_path=BASE_DIR / _get(raw, "storage.chroma_path", "chroma_db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        max_steps=_get(raw, "goal_loop.max_steps", 12),
        disclaimer=_get(raw, "output.disclaimer", "本内容仅供参考，不构成任何投资建议。"),
        gradio_server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        gradio_server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        gradio_auth_username=os.getenv("GRADIO_AUTH_USERNAME", ""),
        gradio_auth_password=os.getenv("GRADIO_AUTH_PASSWORD", ""),
    )


settings = load_settings()
