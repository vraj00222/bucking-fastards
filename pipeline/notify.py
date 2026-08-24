"""Telegram notifications: broadcast pipeline logs/URLs to everyone who messaged the bot.

Token comes from TELEGRAM_BOT_TOKEN in .env. Subscribers = every chat seen in
getUpdates, merged into data/telegram_subscribers.json (getUpdates only keeps
24h of history, so we persist chat ids).

log() buffers lines; flush() ships the buffer as one message. Stage-batched so a
run costs ~5 messages instead of tripping Telegram's ~1 msg/sec per-chat limit.
"""
import atexit
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUBS_PATH = ROOT / "data" / "telegram_subscribers.json"
BASE_URL = os.environ.get("DROPTABLE_BASE_URL", "https://droptable-127827893419.us-central1.run.app")
CHUNK = 3500  # Telegram hard-caps a message at 4096 chars

_buf = []
_subs = None


def public_url(path):
    """Relative /tracks/x.mp3 -> absolute site URL."""
    return f"{BASE_URL.rstrip('/')}/{str(path).lstrip('/')}"


def _api(method):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return None
    return f"https://api.telegram.org/bot{token}/{method}"


def _subscribers():
    global _subs
    if _subs is not None:
        return _subs  # one getUpdates per process, not per message
    subs = set(json.loads(SUBS_PATH.read_text())) if SUBS_PATH.exists() else set()
    url = _api("getUpdates")
    if url:
        try:
            for u in requests.get(url, timeout=15).json().get("result", []):
                chat = (u.get("message") or u.get("my_chat_member") or {}).get("chat") or {}
                if chat.get("id"):
                    subs.add(chat["id"])
        except requests.RequestException:
            pass  # offline: fall back to persisted list
    if subs:
        SUBS_PATH.write_text(json.dumps(sorted(subs)))
    _subs = subs
    return subs


def send(text):
    """Broadcast to all subscribers. Never raises — notifications are best-effort."""
    url = _api("sendMessage")
    if not url or not text.strip():
        return
    chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)]
    for chat_id in _subscribers():
        for chunk in chunks:
            try:
                requests.post(url, json={"chat_id": chat_id, "text": chunk,
                                         "disable_web_page_preview": False}, timeout=15)
            except requests.RequestException:
                pass


def log(line):
    """Buffer a log line; auto-ships if the buffer would outgrow one message."""
    _buf.append(str(line))
    if sum(len(l) + 1 for l in _buf) > CHUNK:
        flush()


def flush(header=None):
    if not _buf:
        return
    body = "\n".join(_buf)
    _buf.clear()
    send(f"{header}\n{body}" if header else body)


atexit.register(flush)  # a crash still delivers the tail


if __name__ == "__main__":
    import sys
    send(" ".join(sys.argv[1:]) or "DropTable Records test notification")
    print(f"sent to {len(_subscribers())} subscriber(s)")
