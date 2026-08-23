#!/usr/bin/env python3
"""Normalize a source intake object (see references/source-schema.md).

Stdlib only; never fetches URLs; never generates lyrics or transcripts.

Usage: python3 normalize_source.py source.json   (or pipe JSON on stdin)
Prints the normalized JSON object; exits 1 on invalid input.
"""
import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

TRACKING_PARAM = re.compile(r"^(si|utm_.*|fbclid|gclid)$")


def canonicalize_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"source_url is not a valid http(s) URL: {url!r}")
    host = parts.netloc.lower()
    path = parts.path
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not TRACKING_PARAM.match(k)]
    if host == "youtu.be":
        video_id = path.strip("/").split("/")[0]
        if not video_id:
            raise ValueError(f"youtu.be URL missing video id: {url!r}")
        host, path = "www.youtube.com", "/watch"
        query = [("v", video_id)] + [(k, v) for k, v in query if k != "v"]
    return urlunsplit((parts.scheme, host, path, urlencode(query), ""))


def dedup_trim(values):
    seen, out = set(), []
    for value in values:
        trimmed = str(value).strip()
        if trimmed and trimmed not in seen:
            seen.add(trimmed)
            out.append(trimmed)
    return out


def normalize(src):
    if not isinstance(src, dict):
        raise ValueError("source must be a JSON object")
    if not src.get("source_url"):
        raise ValueError("source_url is required")

    src["canonical_url"] = canonicalize_url(src.get("canonical_url") or src["source_url"])

    if isinstance(src.get("title"), str):
        src["title"] = " ".join(src["title"].split())

    for name in ("tags", "themes"):
        if isinstance(src.get(name), list):
            src[name] = dedup_trim(src[name])

    if not src.get("retrieved_at"):
        src["retrieved_at"] = datetime.now(timezone.utc).isoformat()

    if src.get("source_type") in ("web-page", "youtube-video") and not src.get("trust_level"):
        src["trust_level"] = "untrusted"

    return src


def main():
    try:
        if len(sys.argv) > 1:
            with open(sys.argv[1], encoding="utf-8") as fh:
                src = json.load(fh)
        else:
            src = json.load(sys.stdin)
        print(json.dumps(normalize(src), indent=2))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
