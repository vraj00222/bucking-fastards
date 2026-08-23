#!/usr/bin/env python3
"""Validate a MusicCatalogRecord JSON file. Stdlib only; never fetches URLs.

Usage: python3 validate_catalog.py record.json
Prints {"valid": bool, "errors": [...], "warnings": [...]}; exits 1 when invalid.
"""
import json
import re
import sys
from urllib.parse import urlparse

SOURCE_TYPES = {"web-page", "youtube-video", "manual-entry", "user-upload",
                "documentation", "github-repository", "pdf"}
CONTENT_RATINGS = {"clean", "explicit", "unknown"}
STRUCTURE_PARTS = {"intro", "verse", "pre-hook", "hook", "bridge", "outro", "unknown"}
ENERGY_LEVELS = {"low", "medium", "high"}
RIGHTS_STATUSES = {"owned", "licensed", "public-metadata-only", "unknown"}
TRUST_LEVELS = {"untrusted", "reviewed", "verified"}
EXTRACTION_METHODS = {"manual", "metadata-import", "approved-scraper"}
EXPRESSIVE_FIELDS = ("fullLyrics", "lyrics", "transcript", "audioFile",
                     "videoFile", "audioUrl", "stems")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED_FIELDS = ("id", "slug", "title", "sourceUrl", "sourceType", "themes",
                   "tags", "contentRating", "structure", "musicAttributes",
                   "rightsStatus", "trustLevel", "provenance", "createdAt",
                   "updatedAt")


def is_http_url(value):
    if not isinstance(value, str):
        return False
    try:
        parts = urlparse(value)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def check_enum(value, allowed, name, errors):
    if value not in allowed:
        errors.append(f"{name} must be one of {sorted(allowed)}, got {value!r}")


def check_string_list(value, name, errors):
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        errors.append(f"{name} must be a list of strings")
        return
    if any(x != x.strip() or not x.strip() for x in value):
        errors.append(f"{name} entries must be non-empty and trimmed")
    if len(set(x.strip() for x in value)) != len(value):
        errors.append(f"{name} entries must be deduplicated")


def validate(rec):
    errors, warnings = [], []
    if not isinstance(rec, dict):
        return ["record must be a JSON object"], []

    for field in REQUIRED_FIELDS:
        if field not in rec:
            errors.append(f"missing required field: {field}")

    if "slug" in rec and (not isinstance(rec["slug"], str) or not SLUG_RE.match(rec["slug"])):
        errors.append("slug must be kebab-case (lowercase letters/digits separated by single hyphens)")
    if "sourceUrl" in rec and not is_http_url(rec["sourceUrl"]):
        errors.append("sourceUrl must be a valid http(s) URL")
    if rec.get("canonicalUrl") is not None and not is_http_url(rec["canonicalUrl"]):
        errors.append("canonicalUrl must be a valid http(s) URL")
    if "sourceType" in rec:
        check_enum(rec["sourceType"], SOURCE_TYPES, "sourceType", errors)
    if "contentRating" in rec:
        check_enum(rec["contentRating"], CONTENT_RATINGS, "contentRating", errors)
    if "rightsStatus" in rec:
        check_enum(rec["rightsStatus"], RIGHTS_STATUSES, "rightsStatus", errors)
    if "trustLevel" in rec:
        check_enum(rec["trustLevel"], TRUST_LEVELS, "trustLevel", errors)

    duration = rec.get("durationSeconds")
    if duration is not None and (not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration < 0):
        errors.append("durationSeconds must be a number >= 0")

    for name in ("themes", "tags"):
        if name in rec:
            check_string_list(rec[name], name, errors)

    structure = rec.get("structure")
    if structure is not None:
        if not isinstance(structure, list):
            errors.append("structure must be a list")
        else:
            for part in structure:
                if part not in STRUCTURE_PARTS:
                    errors.append(f"structure entry must be one of {sorted(STRUCTURE_PARTS)}, got {part!r}")

    attrs = rec.get("musicAttributes")
    if attrs is not None:
        if not isinstance(attrs, dict):
            errors.append("musicAttributes must be an object")
        else:
            check_enum(attrs.get("energy"), ENERGY_LEVELS, "musicAttributes.energy", errors)
            bpm = attrs.get("tempoBpmRange")
            if bpm is not None:
                ok = (isinstance(bpm, list) and len(bpm) == 2
                      and all(isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 for v in bpm))
                if not ok:
                    errors.append("tempoBpmRange must be [min, max] with both values positive numbers")
                elif bpm[0] > bpm[1]:
                    errors.append("tempoBpmRange min must be <= max")
            for name in ("moods", "vocalFormats", "instrumentation"):
                if name in attrs:
                    check_string_list(attrs[name], f"musicAttributes.{name}", errors)
                else:
                    errors.append(f"missing required field: musicAttributes.{name}")

    prov = rec.get("provenance")
    if prov is not None:
        if not isinstance(prov, dict):
            errors.append("provenance must be an object")
        else:
            if not prov.get("retrievedAt"):
                errors.append("provenance.retrievedAt is required")
            check_enum(prov.get("extractionMethod"), EXTRACTION_METHODS,
                       "provenance.extractionMethod", errors)

    # Rights constraints: expressive content requires owned/licensed.
    present = [f for f in EXPRESSIVE_FIELDS if rec.get(f)]
    if present and rec.get("rightsStatus") not in ("owned", "licensed"):
        errors.append(
            "expressive-content fields %s require rightsStatus 'owned' or 'licensed' "
            "(got %r)" % (present, rec.get("rightsStatus")))

    if rec.get("sourceType") in ("web-page", "youtube-video") and rec.get("trustLevel") in ("reviewed", "verified"):
        warnings.append(
            "sourceType %r with trustLevel %r: web/video imports default to 'untrusted'; "
            "confirm a human actually reviewed this record" % (rec["sourceType"], rec["trustLevel"]))

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"valid": False, "errors": ["usage: validate_catalog.py record.json"], "warnings": []}))
        return 1
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [f"cannot read record: {exc}"], "warnings": []}))
        return 1
    errors, warnings = validate(rec)
    print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
