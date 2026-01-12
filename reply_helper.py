import os
import time
import json
import re
import threading
from pathlib import Path

import pyperclip
import keyboard
from openai import OpenAI

# Initialize OpenAI client using OPENAI_API_KEY from environment
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Path for session persistence (per-person conversation history)
BASE_DIR = Path(__file__).resolve().parent
SESSIONS_PATH = BASE_DIR / "sessions.json"

# Global state: mapping of person -> list of (role, content)
sessions = {}
# Current active conversation
active_person = "default"

# Throttle variables for hotkey triggering
lock = threading.Lock()
last_job_ts = 0.0

# System prompt and maximum number of turns (user+assistant pairs) to retain per person
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "你是一个简洁、专业的聊天回复助手。回复自然、有礼貌、不过度啰嗦。",
)
MAX_TURNS = int(os.getenv("MAX_TURNS", "6"))

# Regex patterns for parsing contact prefixes in copied text
PERSON_TAG_RE_1 = re.compile(r"^\s*\[([^\]]{1,40})\]\s*(.*)$", re.S)
PERSON_TAG_RE_2 = re.compile(
    r"^\s*[@#]([A-Za-z0-9_\-\u4e00-\u9fff]{1,40})\s*[:：]?\s*(.*)$", re.S
)


def parse_person_tag(text):
    """Parse contact prefix such as [Alice] or @Alice. Returns (person, remaining_text)."""
    m = PERSON_TAG_RE_1.match(text)
    if m:
        who = m.group(1).strip()
        rest = (m.group(2) or "").strip()
        if who:
            return who, rest
    m = PERSON_TAG_RE_2.match(text)
    if m:
        who = m.group(1).strip()
        rest = (m.group(2) or "").strip()
        if who:
            return who, rest
    return None, text


def load_sessions():
    """Load session history and metadata from sessions.json, if it exists."""
    global sessions, active_person
    if not SESSIONS_PATH.exists():
        sessions = {}
        return
    try:
        data = json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            active_person = data.get("_meta", {}).get("active_person", active_person)
            raw = data.get("sessions", {})
            if isinstance(raw, dict):
                sessions = {}
                for person, arr in raw.items():
                    cleaned = []
                    for item in arr:
                        if (
                            (isinstance(item, list) or isinstance(item, tuple))
                            and len(item) == 2
                        ):
                            role, content = item
                            if role in ("user", "assistant") and isinstance(content, str):
                                cleaned.append((role, content))
                    sessions[person] = cleaned
    except Exception:
        sessions = {}


def save_sessions():
    """Persist sessions and active_person to sessions.json."""
    data = {"_meta": {"active_person": active_person}, "sessions": sessions}
    SESSIONS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def ensure_person(person):
    """Ensure a person key exists in the sessions mapping."""
    if person not in sessions:
        sessions[person] = []


def trim_history(person):
    """Keep only the most recent MAX_TURNS turns for a person."""
    arr = sessions.get(person, [])
    max_items = max(2, MAX_TURNS * 2)
    while len(arr) > max_items:
        arr.pop(0)


def push_turn(person, role, text):
    """Append a conversation turn to a person's history."""
    ensure_person(person)
    sessions[person].append((role, text))
    trim_history(person)


def build_input(person, text):
    """Build input for OpenAI Responses API from session history and user text."""
    ensure_person(person)
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in sessions[person]:
        msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": text})
    return msgs


def extract_output_text(resp):
    """Extract the reply text from OpenAI Responses API response."""
    out = getattr(resp, "output_text", None)
    if isinstance(out, str) and out.strip():
        return out.strip()
    texts = []
    output = getattr(resp, "output", None)
    if isinstance(output, list):
        for item in output:
            content = getattr(item, "content", None)
            if isinstance(content, list):
                for c in content:
                    if getattr(c, "type", None) in ("output_text", "text"):
                        t = getattr(c, "text", None)
                        if isinstance(t, str) and t.strip():
                            texts.append(t.strip())
    return "\n".join(texts).strip() or "（模型未返回文本输出）"


def call_gpt(person, text):
    """Send a request to OpenAI and return the assistant reply."""
    resp = client.responses.create(model=MODEL, input=build_input(person, text))
    return extract_output_text(resp)


def set_active_person(name):
    """Switch the active conversation person and persist the change."""
    global active_person
    name = name.strip()
    if not name:
        return
    active_person = name
    ensure_person(active_person)
    save_sessions()
    print(f"[提示] 当前联系人会话：{active_person}")


def list_people():
    """List all person sessions with an indicator for the active one."""
    print("[联系人会话列表]")
    if not sessions:
        print("  (空)")
        return
    for k in sorted(sessions.keys()):
        mark = " <=" if k == active_person else ""
        print(f"  - {k}{mark}")


def reset_current_person_session():
    """Clear the history for the active person."""
    sessions[active_person] = []
    save_sessions()
    print(f"[提示] 已清空会话：{active_person}")


def cycle_person():
    """Cycle through persons in alphabetical order and set the next as active."""
    global active_person
    keys = sorted(sessions.keys()) if sessions else []
    if not keys:
        ensure_person(active_person)
        save_sessions()
        return
    if active_person not in keys:
        active_person = keys[0]
    else:
        idx = keys.index(active_person)
        active_person = keys[(idx + 1) % len(keys)]
    save_sessions()
    print(f"[提示] 已切换联系人会话：{active_person}")


def bind_person_hotkeys_10():
    """
    Bind up to 10 global hotkeys for switching to common person sessions.
    Ctrl+Alt+1..9 -> first 9 persons (sorted by name), Ctrl+Alt+0 -> 10th.
    """
    keys = sorted(sessions.keys())
    top10 = keys[:10]
    if not top10:
        print("  - (暂无联系人会话，先用 [Name] 前缀建立)")
        return
    print("[快捷键映射]")
    for idx, name in enumerate(top10, 1):
        combo = f"ctrl+alt+{idx}" if idx <= 9 else "ctrl+alt+0"
        keyboard.add_hotkey(combo, lambda n=name: set_active_person(n))
        print(f"  - {combo.upper()}：{name}")


def generate_reply_from_clipboard():
    """Generate a reply using OpenAI from text copied in the clipboard."""
    global last_job_ts, active_person
    with lock:
        now = time.time()
        if now - last_job_ts < 1.2:
            return
        last_job_ts = now
    raw = (pyperclip.paste() or "").strip()
    if not raw:
        print("[提示] 剪贴板为空或不是文本。")
        return
    person_tag, text = parse_person_tag(raw)
    person = person_tag or active_person
    text = (text or "").strip()
    if not text:
        print("[提示] 文本为空。")
        return
    if len(text) > 4000:
        print("[提示] 文本过长，请先精简。")
        return
    # If the text includes a prefix, switch active person automatically
    if person_tag and person_tag != active_person:
        active_person = person_tag
        ensure_person(active_person)
    print(f"\n[联系人会话] {person}")
    print("[输入]")
    print(text)
    print("\n[生成中…]")
    try:
        push_turn(person, "user", text)
        reply = call_gpt(person, text)
        push_turn(person, "assistant", reply)
        pyperclip.copy(reply)
        save_sessions()
        print("\n[输出，已复制到剪贴板]")
        print(reply)
        print("\n切回微信 Ctrl+V 粘贴发送。")
    except Exception as e:
        msg = str(e)
        if "insufficient_quota" in msg or "exceeded your current quota" in msg:
            print("[错误] API 额度不足/未开通计费，请检查 OpenAI 平台。")
        else:
            print(f"[错误] 调用 OpenAI 失败：{e}")


def main():
    """Entry point: load sessions, print help, bind hotkeys and run loop."""
    load_sessions()
    ensure_person(active_person)
    save_sessions()
    print("Reply Helper（每人独立会话）已启动：")
    print(
        "  - Ctrl+Alt+G：读取剪贴板并生成回复\n"
        "  - Ctrl+Alt+1~9,0：切换会话\n"
        "  - Ctrl+Alt+P：循环切换会话\n"
        "  - Ctrl+Alt+L：列出会话\n"
        "  - Ctrl+Alt+R：清空当前会话\n"
        "  - Ctrl+C：退出"
    )
    list_people()
    keyboard.add_hotkey("ctrl+alt+g", generate_reply_from_clipboard)
    keyboard.add_hotkey("ctrl+alt+p", cycle_person)
    keyboard.add_hotkey("ctrl+alt+l", list_people)
    keyboard.add_hotkey("ctrl+alt+r", reset_current_person_session)
    bind_person_hotkeys_10()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n退出。")


if __name__ == "__main__":
    main()