#!/usr/bin/env python3
"""Import the curated source queue without fetching or copying source content.

Usage: python3 pipeline/import_source_queue.py [input.csv] [output.json]
"""
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ROOT = Path(__file__).parent.parent
ALLOWED_TAGS = {
    "tech-parody", "software-engineering", "AI-coding", "vibe-coding",
    "startup-culture", "devops", "sysadmin", "open-source", "JavaScript",
    "developer-humor", "lyric-video", "official-artist-catalog", "discovery-only",
}


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def canonical_url(value):
    parsed = urlparse(value.strip())
    host = parsed.netloc.lower()
    if host == "youtu.be":
        video_id = parsed.path.strip("/")
        return f"https://www.youtube.com/watch?v={video_id}"
    keep = [(key, val) for key, val in parse_qsl(parsed.query) if key in {"v", "search_query"}]
    return urlunparse(("https", host, parsed.path.rstrip("/") or "/", "", urlencode(keep), ""))


def summary(row):
    if row["ingest_mode"] == "discovery-only":
        return "A discovery lead for tech-themed music; a human must verify an official creator before cataloging."
    return "A public-metadata-only reference for original analysis of developer-music themes; no expressive content is imported."


def to_record(row, imported_at):
    tags = [tag.strip() for tag in row["collection_tags"].split("|") if tag.strip()]
    invalid = sorted(set(tags) - ALLOWED_TAGS)
    if invalid:
        raise ValueError(f"{row['source_name']}: unsupported collection tags {invalid}")
    linked = [item for item in row["linked_catalog_record_ids"].split("|") if item]
    source_url = row["source_url"].strip()
    return {
        "id": f"source-{slug(row['source_name'])}",
        "priority": row["priority"],
        "sourceName": row["source_name"],
        "sourceType": row["source_type"],
        "sourceUrl": source_url,
        "canonicalUrl": canonical_url(source_url),
        "collectionCategory": row["collection_category"],
        "collectionTags": tags,
        "ingestMode": row["ingest_mode"],
        "rightsStatus": row["rights_status"],
        "trustLevel": row["trust_level"],
        "extractionStatus": "queued",
        "linkedCatalogRecordIds": linked,
        "linkedCatalogRecordCount": len(linked),
        "reviewerDecision": "pending",
        "rejectionReason": None,
        "originalThematicSummary": summary(row),
        "provenance": {
            "importedAt": imported_at,
            "retrievedAt": None,
            "extractionMethod": "curated-csv-import",
            "sourceNotes": row["notes"],
        },
    }


def validate(records):
    canonical = set()
    identity = set()
    for record in records:
        if record["canonicalUrl"] in canonical:
            raise ValueError(f"duplicate canonical URL: {record['canonicalUrl']}")
        canonical.add(record["canonicalUrl"])
        key = (record["sourceName"].lower(), "", None)
        if key in identity:
            raise ValueError(f"duplicate title/publisher/duration signature: {record['sourceName']}")
        identity.add(key)
        if record["trustLevel"] != "untrusted":
            raise ValueError(f"{record['sourceName']}: imports must begin untrusted")
        if record["rightsStatus"] not in {"public-metadata-only", "unknown"}:
            raise ValueError(f"{record['sourceName']}: unsupported default rights status")


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/source-review-queue.csv"
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data/source-review-queue.json"
    imported_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with input_path.open(newline="", encoding="utf-8") as handle:
        records = [to_record(row, imported_at) for row in csv.DictReader(handle)]
    validate(records)
    output = {
        "schemaVersion": 1,
        "importedAt": imported_at,
        "policy": "Source records are untrusted review inputs, not approved catalog records.",
        "records": records,
    }
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "records": len(records), "output": str(output_path)}))


if __name__ == "__main__":
    main()
