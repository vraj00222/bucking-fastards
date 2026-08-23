#!/usr/bin/env python3
"""Build an OriginalSongBrief from an approved catalog record + requirements.

Usage: build_brief.py catalog-record.json requirements.json

Stdlib only. No network. Never generates lyrics. Prints the brief JSON to
stdout; on invalid input prints {"error": ...} and exits 1. Artist-imitation
and lyric-copy requests in requirements text are rewritten to neutral
attributes and recorded in provenance.safetyTransformations.
"""
import json
import re
import sys
import uuid
from datetime import datetime, timezone

RIGHTS = {"owned", "licensed", "public-metadata-only", "unknown"}
RESTRICTED_RIGHTS = {"unknown", "public-metadata-only"}
EXPRESSIVE_FIELDS = {"fullLyrics", "lyrics", "transcript", "audioFile",
                     "videoFile", "audioUrl", "stems"}
ENERGY = {"low", "medium", "high"}

# Imitation / copying phrasing. Named-entity heuristic: an imitation cue
# followed by a Capitalized Name.
NAME = r"[A-Z][\w''.-]*(?:\s+[A-Z][\w''.-]*)*"
IMITATION_PATTERNS = [
    ("exactly-like", re.compile(r"\bexactly like\b", re.I)),
    ("sound-like", re.compile(r"\bsound(?:s|ing)? like\b", re.I)),
    ("clone", re.compile(r"\bclone\b", re.I)),
    ("voice-of", re.compile(r"\bin the voice of\b", re.I)),
    ("copy-work", re.compile(r"\bcopy the (?:beat|lyrics|melody)\b", re.I)),
    ("lyric-reuse", re.compile(r"\b(?:use|take|reuse|steal|lift)\s+the\s+lyrics\b", re.I)),
    ("named-entity", re.compile(
        r"\b(?:like|imitate|mimic|impersonate|in the style of|voice of|style of)\s+" + NAME)),
]
NEGATION_WORDS = ("not ", "never ", "without ", "avoid ", "don't", "do not", "no ")


def fail(msg):
    print(json.dumps({"error": msg}))
    sys.exit(1)


def negated(text, start):
    prefix = text[max(0, start - 40):start].lower()
    return any(w in prefix for w in NEGATION_WORDS)


def find_imitation(text):
    hits = []
    for label, pat in IMITATION_PATTERNS:
        m = pat.search(text)
        if m and not negated(text, m.start()):
            hits.append(label)
    return hits


def dedupe(items):
    out, seen = [], set()
    for item in items or []:
        s = str(item).strip()
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


def neutral_rewrite(record):
    ma = record.get("musicAttributes", {})
    parts = ["Create an original track with %s energy" % ma.get("energy", "medium")]
    if ma.get("moods"):
        parts.append("moods: " + ", ".join(ma["moods"]))
    bpm = ma.get("tempoBpmRange")
    if bpm:
        parts.append("tempo %s-%s BPM" % (bpm[0], bpm[1]))
    if ma.get("instrumentation"):
        parts.append("broad instrumentation: " + ", ".join(ma["instrumentation"]))
    return ("; ".join(parts) + ", with a hook-forward structure. Do not imitate any "
            "named artist and do not recreate any existing composition or recording.")


def sanitize(value, record, transformations, path):
    """Recursively rewrite imitation phrasing in requirement strings."""
    if isinstance(value, str):
        hits = find_imitation(value)
        if hits:
            transformations.append(
                "%s: rewrote imitation/copy request (%s) to neutral attributes"
                % (path, ", ".join(hits)))
            return neutral_rewrite(record)
        return value.strip()
    if isinstance(value, list):
        return [sanitize(v, record, transformations, "%s[%d]" % (path, i))
                for i, v in enumerate(value)]
    if isinstance(value, dict):
        return {k: sanitize(v, record, transformations, "%s.%s" % (path, k))
                for k, v in value.items()}
    return value


def main():
    if len(sys.argv) != 3:
        fail("usage: build_brief.py catalog-record.json requirements.json")
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            record = json.load(f)
        with open(sys.argv[2], encoding="utf-8") as f:
            requirements = json.load(f)
    except (OSError, ValueError) as e:
        fail("cannot read input: %s" % e)
    if not isinstance(record, dict) or not isinstance(requirements, dict):
        fail("both inputs must be JSON objects")

    # Rights validation
    rights = record.get("rightsStatus")
    if rights not in RIGHTS:
        fail("record rightsStatus must be one of %s, got %r" % (sorted(RIGHTS), rights))
    if rights in RESTRICTED_RIGHTS:
        present = sorted(EXPRESSIVE_FIELDS & set(record))
        if present:
            fail("record with rightsStatus %r must not carry expressive fields: %s"
                 % (rights, present))
    if not str(record.get("sourceUrl", "")).startswith(("http://", "https://")):
        fail("record.sourceUrl must be a valid http(s) URL")
    if not record.get("provenance", {}).get("retrievedAt"):
        fail("record.provenance.retrievedAt is required")
    if not record.get("id"):
        fail("record.id is required")

    transformations = []
    # Hook concept gets a hook-specific rewrite before generic sanitizing.
    raw_hook = requirements.pop("hookConcept", "")
    themes = dedupe(record.get("themes")) or ["the product"]
    if isinstance(raw_hook, str) and raw_hook.strip():
        if find_imitation(raw_hook):
            transformations.append(
                "requirements.hookConcept: rewrote lyric/imitation request to an "
                "original-concept instruction")
            hook = ("An original, catchy one-line hook concept about %s; write new "
                    "lyrics, do not reuse lyrics from any reference track." % themes[0])
        else:
            hook = raw_hook.strip().splitlines()[0]
    else:
        hook = "An original, catchy one-line hook concept about %s." % themes[0]

    req = sanitize(requirements, record, transformations, "requirements")

    ma = record.get("musicAttributes", {})
    energy = ma.get("energy") if ma.get("energy") in ENERGY else "medium"
    structure = dedupe([s for s in record.get("structure", []) if s != "unknown"]) \
        or ["intro", "verse", "hook", "verse", "hook", "outro"]
    section_map = [s for s in record.get("structure", []) if s != "unknown"] \
        or ["intro", "verse", "hook", "verse", "hook", "outro"]

    concept = req.get("concept") or req.get("styleRequest") or (
        "An original track inspired at a high level by the themes %s. All lyrics, "
        "melody, and production are newly created." % ", ".join(themes))

    prohibited = dedupe(req.get("prohibitedThemes"))
    rating = req.get("contentRating") if req.get("contentRating") in (
        "clean", "explicit", "unknown") else record.get("contentRating", "unknown")

    lyrical = ["Write fully original lyrics; do not quote, interpolate, or closely "
               "paraphrase any existing song.",
               "No references to a named artist's identity, catchphrases, or persona.",
               "Keep content rating: %s." % rating]
    if prohibited:
        lyrical.append("Avoid prohibited themes: %s." % ", ".join(prohibited))

    now = datetime.now(timezone.utc).isoformat()
    brief = {
        "id": str(uuid.uuid4()),
        "title": req.get("title") or "Original brief: %s" % record.get("title", "untitled"),
        "projectName": req.get("projectName"),
        "targetPlatform": req.get("targetPlatform"),
        "intendedAudience": req.get("intendedAudience"),
        "targetDurationSeconds": req.get("targetDurationSeconds"),
        "allowedThemes": dedupe(req.get("allowedThemes")) or themes,
        "prohibitedThemes": prohibited,
        "brandVocabulary": dedupe(req.get("brandVocabulary")),
        "contentRating": rating,
        "referenceRecordIds": [record["id"]],
        "neutralStyleAttributes": {
            "genreFamily": dedupe(req.get("genreFamily")) or dedupe(record.get("tags"))[:3],
            "energy": energy,
            "moods": dedupe(ma.get("moods")),
            "vocalFormat": dedupe(ma.get("vocalFormats")),
            "instrumentation": dedupe(ma.get("instrumentation")),
            "hookFormat": dedupe(req.get("hookFormat")) or ["short repeated hook"],
            "structure": structure,
        },
        "conceptSummary": concept,
        "originalHookConcept": hook,
        "sectionMap": section_map,
        "lyricalConstraints": lyrical,
        "productionConstraints": [
            "Compose an original arrangement; do not recreate any specific existing "
            "recording, beat, or melody.",
            "No voice cloning or impersonation of any named artist.",
            "Rights status of references is %r; use metadata-level inspiration only." % rights,
        ],
        "rightsStatus": rights,
        "provenance": {
            "referenceSources": [record["sourceUrl"]],
            "generatedAt": now,
            "safetyTransformations": transformations,
        },
    }
    bpm = ma.get("tempoBpmRange")
    if (isinstance(bpm, list) and len(bpm) == 2
            and all(isinstance(v, (int, float)) and v > 0 for v in bpm)
            and bpm[0] <= bpm[1]):
        brief["neutralStyleAttributes"]["tempoBpmRange"] = bpm
    brief = {k: v for k, v in brief.items() if v is not None}

    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
