"""最小对话：接 DeepSeek，一问一答（纯 LLM，无工具）。

用法：
    python -m src.chat "你好"        # 单轮问答
    python -m src.chat               # 交互模式，输入 exit 退出
"""
import sys

from src.llm import get_llm


def chat(prompt: str) -> str:
    """单轮对话，返回文本回复。"""
    return get_llm().invoke(prompt).content


def main() -> None:
    # 带参数：单轮问答
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(chat(prompt))
        return

    # 无参数：交互循环
    print("最小对话模式（输入 exit / quit / 退出 结束）")
    llm = get_llm()
    while True:
        user_input = input("你：").strip()
        if user_input.lower() in ("exit", "quit", "退出"):
            print("再见")
            break
        if not user_input:
            continue
        print("Agent：", llm.invoke(user_input).content)


if __name__ == "__main__":
    main()
