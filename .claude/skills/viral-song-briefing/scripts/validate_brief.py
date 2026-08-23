#!/usr/bin/env python3
"""Validate an OriginalSongBrief JSON file.

Usage: validate_brief.py brief.json

Stdlib only. No network. Prints {"valid": bool, "errors": [...],
"safetyFindings": [...]} to stdout; exits 1 when invalid.
Rejects artist-imitation language and lyric-copying instructions anywhere in
the brief, and validates BPM range, structure values, and required
provenance/rights fields.
"""
import json
import re
import sys

RIGHTS = {"owned", "licensed", "public-metadata-only", "unknown"}
ENERGY = {"low", "medium", "high"}
RATINGS = {"clean", "explicit", "unknown"}
SECTIONS = {"intro", "verse", "pre-hook", "hook", "bridge", "outro", "unknown"}

NAME = r"[A-Z][\w''.-]*(?:\s+[A-Z][\w''.-]*)*"
IMITATION_PATTERNS = [
    ("exactly-like", re.compile(r"\bexactly like\b", re.I)),
    ("sound-like", re.compile(r"\bsound(?:s|ing)? like\b", re.I)),
    ("clone", re.compile(r"\bclone\b", re.I)),
    ("voice-of", re.compile(r"\bin the voice of\b", re.I)),
    ("copy-work", re.compile(r"\bcopy the (?:beat|lyrics|melody)\b", re.I)),
    ("lyric-copy", re.compile(r"\b(?:use|take|reuse|steal|lift|copy)\s+(?:the\s+)?(?:full\s+)?lyrics\b", re.I)),
    ("named-entity", re.compile(
        r"\b(?:like|imitate|mimic|impersonate|in the style of|voice of|style of)\s+" + NAME)),
]
NEGATION_WORDS = ("not ", "never ", "without ", "avoid ", "don't", "do not", "no ")


def negated(text, start):
    prefix = text[max(0, start - 40):start].lower()
    return any(w in prefix for w in NEGATION_WORDS)


def scan_strings(value, path, findings):
    # provenance.safetyTransformations quotes the offending input it rewrote;
    # it is a record of removals, not an instruction — skip it.
    if path == "provenance.safetyTransformations":
        return
    if isinstance(value, str):
        for label, pat in IMITATION_PATTERNS:
            m = pat.search(value)
            if m and not negated(value, m.start()):
                findings.append("%s: %s language: %r" % (path, label, m.group(0)))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            scan_strings(v, "%s[%d]" % (path, i), findings)
    elif isinstance(value, dict):
        for k, v in value.items():
            scan_strings(v, "%s.%s" % (path, k) if path else k, findings)


def main():
    errors, findings = [], []
    if len(sys.argv) != 2:
        print(json.dumps({"valid": False,
                          "errors": ["usage: validate_brief.py brief.json"],
                          "safetyFindings": []}))
        sys.exit(1)
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            brief = json.load(f)
        if not isinstance(brief, dict):
            raise ValueError("brief must be a JSON object")
    except (OSError, ValueError) as e:
        print(json.dumps({"valid": False, "errors": ["cannot read brief: %s" % e],
                          "safetyFindings": []}))
        sys.exit(1)

    # Safety scan over every string in the brief.
    scan_strings(brief, "", findings)

    # Required scalar fields
    for field in ("id", "title", "conceptSummary", "originalHookConcept"):
        if not isinstance(brief.get(field), str) or not brief[field].strip():
            errors.append("missing or empty required field: %s" % field)
    for field in ("allowedThemes", "prohibitedThemes", "brandVocabulary",
                  "sectionMap", "lyricalConstraints", "productionConstraints"):
        if not isinstance(brief.get(field), list):
            errors.append("field must be a list: %s" % field)
    refs = brief.get("referenceRecordIds")
    if not isinstance(refs, list) or not refs:
        errors.append("referenceRecordIds must be a non-empty list")
    if brief.get("contentRating") not in RATINGS:
        errors.append("contentRating must be one of %s" % sorted(RATINGS))
    if brief.get("rightsStatus") not in RIGHTS:
        errors.append("rightsStatus must be one of %s" % sorted(RIGHTS))

    hook = brief.get("originalHookConcept")
    if isinstance(hook, str) and ("\n" in hook.strip() or len(hook) > 300):
        errors.append("originalHookConcept must be a single short line (a concept, not lyrics)")

    # Neutral style attributes
    nsa = brief.get("neutralStyleAttributes")
    if not isinstance(nsa, dict):
        errors.append("neutralStyleAttributes must be an object")
    else:
        if nsa.get("energy") not in ENERGY:
            errors.append("neutralStyleAttributes.energy must be one of %s" % sorted(ENERGY))
        bpm = nsa.get("tempoBpmRange")
        if bpm is not None:
            if (not isinstance(bpm, list) or len(bpm) != 2
                    or not all(isinstance(v, (int, float)) and v > 0 for v in bpm)
                    or bpm[0] > bpm[1]):
                errors.append("tempoBpmRange must be [min, max] with positive values and min <= max")
        for field in ("genreFamily", "moods", "vocalFormat", "instrumentation",
                      "hookFormat", "structure"):
            if not isinstance(nsa.get(field), list):
                errors.append("neutralStyleAttributes.%s must be a list" % field)
        for s in nsa.get("structure") or []:
            if s not in SECTIONS:
                errors.append("invalid structure value %r; allowed: %s" % (s, sorted(SECTIONS)))

    # Provenance
    prov = brief.get("provenance")
    if not isinstance(prov, dict):
        errors.append("provenance is required")
    else:
        srcs = prov.get("referenceSources")
        if not isinstance(srcs, list) or not srcs:
            errors.append("provenance.referenceSources must be a non-empty list")
        if not isinstance(prov.get("generatedAt"), str) or not prov["generatedAt"].strip():
            errors.append("provenance.generatedAt is required")
        if not isinstance(prov.get("safetyTransformations"), list):
            errors.append("provenance.safetyTransformations must be a list")

    valid = not errors and not findings
    print(json.dumps({"valid": valid, "errors": errors, "safetyFindings": findings},
                     indent=2))
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
