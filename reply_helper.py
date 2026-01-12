import os
import time
import sys
import threading
import pyperclip
import keyboard
from openai import OpenAI

client = OpenAI()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "你是一个简洁、专业的聊天回复助手。回复自然、有礼貌、不过度啰嗦。"
)

# 简易“会话记忆”（仅在本程序运行期间有效）
history = []  # list[tuple(role, content)]
MAX_TURNS = 6  # 最多保留最近 N 轮（user+assistant）

def trim_history():
    # 每轮两条，最多保留 2*MAX_TURNS 条
    max_items = 2 * MAX_TURNS
    while len(history) > max_items:
        history.pop(0)

def build_input(user_text: str) -> list:
    # 用 Responses API 的 input 结构（system + 多轮历史 + user）
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in history:
        msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": user_text})
    return msgs

def call_gpt(user_text: str) -> str:
    # 调用 OpenAI Responses API
    resp = client.responses.create(
        model=MODEL,
        input=build_input(user_text),
    )
    out = (getattr(resp, "output_text", "") or "").strip()
    return out if out else "（模型未返回文本输出）"

lock = threading.Lock()
last_job_ts = 0.0

def generate_reply_from_clipboard():
    global last_job_ts
    with lock:
        # 简单限流：2 秒内只响应一次，避免误触
        now = time.time()
        if now - last_job_ts < 2.0:
            return
        last_job_ts = now

    text = (pyperclip.paste() or "").strip()
    if not text:
        print("[提示] 剪贴板为空或不是文本。")
        return
    if len(text) > 4000:
        print("[提示] 文本过长，建议先手动精简后再生成回复。")
        return

    print("\n[输入(来自剪贴板)]")
    print(text)
    print("\n[生成中…]")

    try:
        reply = call_gpt(text)
        # 记录会话
        history.append(("user", text))
        history.append(("assistant", reply))
        trim_history()

        pyperclip.copy(reply)
        print("\n[输出(已复制到剪贴板)]")
        print(reply)
        print("\n你可以回到微信里 Ctrl+V 粘贴发送。")
    except Exception as e:
        print(f"[错误] 调用 OpenAI 失败：{e}")

def reset_session():
    history.clear()
    print("[提示] 会话已清空。")

def main():
    print("Reply Helper 已启动：")
    print("  - Ctrl+Alt+G：读取剪贴板 -> 调 GPT -> 复制回复到剪贴板")
    print("  - Ctrl+Alt+R：清空会话上下文")
    print("  - Ctrl+C：退出")
    print("\n建议用法：在微信里复制对方消息（Ctrl+C），再按 Ctrl+Alt+G。")

    keyboard.add_hotkey("ctrl+alt+g", generate_reply_from_clipboard)
    keyboard.add_hotkey("ctrl+alt+r", reset_session)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n退出。")
        sys.exit(0)

if __name__ == "__main__":
    main()
