#!/usr/bin/env python3
"""Validate a generated source-review queue without fetching source URLs."""
import json
import sys
from urllib.parse import urlparse

EXPRESSIVE_FIELDS = {"lyrics", "fullLyrics", "transcript", "audioUrl", "videoUrl", "stems"}
REQUIRED = {
    "id", "priority", "sourceName", "sourceType", "sourceUrl", "canonicalUrl",
    "collectionTags", "ingestMode", "rightsStatus", "trustLevel", "extractionStatus",
    "linkedCatalogRecordCount", "reviewerDecision", "provenance",
}


def is_url(value):
    parsed = urlparse(value or "")
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate(payload):
    errors = []
    seen_urls = set()
    for index, record in enumerate(payload.get("records", [])):
        prefix = f"records[{index}]"
        missing = REQUIRED - record.keys()
        if missing:
            errors.append(f"{prefix}: missing {sorted(missing)}")
        if not is_url(record.get("sourceUrl")) or not is_url(record.get("canonicalUrl")):
            errors.append(f"{prefix}: source URLs must be HTTPS")
        if record.get("canonicalUrl") in seen_urls:
            errors.append(f"{prefix}: duplicate canonical URL")
        seen_urls.add(record.get("canonicalUrl"))
        if record.get("trustLevel") != "untrusted":
            errors.append(f"{prefix}: imported sources must default to untrusted")
        if record.get("rightsStatus") not in {"public-metadata-only", "unknown"}:
            errors.append(f"{prefix}: invalid imported rights status")
        if record.get("reviewerDecision") != "pending":
            errors.append(f"{prefix}: imported records must await human review")
        bad_fields = EXPRESSIVE_FIELDS & record.keys()
        if bad_fields:
            errors.append(f"{prefix}: prohibited expressive fields {sorted(bad_fields)}")
    return errors


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"valid": False, "errors": ["usage: validate_source_queue.py queue.json"]}))
        return 1
    with open(sys.argv[1], encoding="utf-8") as handle:
        payload = json.load(handle)
    errors = validate(payload)
    print(json.dumps({"valid": not errors, "records": len(payload.get("records", [])), "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
