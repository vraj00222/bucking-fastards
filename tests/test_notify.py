"""Tests for the Telegram broadcast sink. Stdlib only, no network.

python3 tests/test_notify.py  (also runs under pytest)
"""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

import notify


class FakeRequests:
    """Stand-in for the requests module: records posts, raises nothing."""

    class RequestException(Exception):
        pass

    def __init__(self):
        self.posts = []

    def post(self, url, json=None, timeout=None):
        self.posts.append(json)


class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeRequests()
        self._real_requests = notify.requests
        notify.requests = self.fake
        notify._subs = {1, 2}  # skip getUpdates entirely
        notify._buf.clear()
        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

    def tearDown(self):
        notify.requests = self._real_requests
        notify._subs = None
        notify._buf.clear()
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)

    def test_log_buffers_until_flush(self):
        notify.log("line one")
        notify.log("line two")
        self.assertEqual(self.fake.posts, [])
        notify.flush("header")
        self.assertEqual([p["text"] for p in self.fake.posts],
                         ["header\nline one\nline two"] * 2)  # one per subscriber
        self.assertEqual(notify._buf, [])

    def test_flush_without_buffer_is_noop(self):
        notify.flush("header")
        self.assertEqual(self.fake.posts, [])

    def test_long_text_is_chunked(self):
        notify.send("x" * (notify.CHUNK * 2 + 10))
        per_sub = [p["text"] for p in self.fake.posts if p["chat_id"] == 1]
        self.assertEqual(len(per_sub), 3)
        self.assertTrue(all(len(t) <= 4096 for t in per_sub))

    def test_oversized_buffer_auto_flushes(self):
        notify.log("y" * (notify.CHUNK + 1))
        self.assertTrue(self.fake.posts)  # shipped without an explicit flush
        self.assertEqual(notify._buf, [])

    def test_no_token_is_noop(self):
        del os.environ["TELEGRAM_BOT_TOKEN"]
        notify.send("nobody home")
        self.assertEqual(self.fake.posts, [])

    def test_public_url_joins_cleanly(self):
        notify.BASE_URL = "https://example.com/"
        self.assertEqual(notify.public_url("/tracks/x.mp3"), "https://example.com/tracks/x.mp3")
        notify.BASE_URL = "https://example.com"
        self.assertEqual(notify.public_url("videos/x.mp4"), "https://example.com/videos/x.mp4")


if __name__ == "__main__":
    unittest.main()
