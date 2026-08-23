#!/usr/bin/env python3
"""Tests for the DropTable Records catalog skills.

Runs standalone (python3 tests/test_skills.py) and under pytest.
Stdlib only. Cross-skill tests invoke the skill scripts via subprocess.
"""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(ROOT, ".claude", "skills")
CATALOG_DIR = os.path.join(ROOT, "data", "catalog")
VALIDATE_CATALOG = os.path.join(
    SKILLS_DIR, "tech-music-catalog", "scripts", "validate_catalog.py"
)

# Titles are test DATA here (asserted ABSENT from skill files, per rights policy).
SEED_VIDEO_TITLES = [
    "I made a music player app, except it's only my music",
    "I asked Fable 5 to make me a lyric video",
]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _run(script, *args, stdin=None):
    return subprocess.run(
        [sys.executable, script, *args], capture_output=True, text=True, input=stdin
    )


def _find_script(name):
    hits = sorted(glob.glob(os.path.join(SKILLS_DIR, "*", "scripts", name)))
    assert hits, f"{name} not found under {SKILLS_DIR}/*/scripts/"
    return hits[0]


def _seed_records():
    records = sorted(glob.glob(os.path.join(CATALOG_DIR, "*.json")))
    assert len(records) >= 3, f"expected >=3 seed records in {CATALOG_DIR}"
    return records


def _tmp_json(obj):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path


# --- (1) seed records pass validate_catalog.py -------------------------------

def test_seed_records_valid():
    assert os.path.isfile(VALIDATE_CATALOG), f"missing {VALIDATE_CATALOG}"
    for record in _seed_records():
        p = _run(VALIDATE_CATALOG, record)
        assert p.returncode == 0, (
            f"{record} rejected (exit {p.returncode}): {p.stdout} {p.stderr}"
        )


# --- (2) unknown rights + expressive-content field => rejected ---------------

def _assert_unknown_rights_rejects(field):
    with open(_seed_records()[0], encoding="utf-8") as f:
        rec = json.load(f)
    rec["rightsStatus"] = "unknown"
    rec[field] = "PLACEHOLDER EXPRESSIVE CONTENT"
    path = _tmp_json(rec)
    try:
        p = _run(VALIDATE_CATALOG, path)
        assert p.returncode == 1, (
            f"unknown-rights record with '{field}' must be rejected with exit 1, "
            f"got {p.returncode}: {p.stdout} {p.stderr}"
        )
    finally:
        os.unlink(path)


def test_unknown_rights_rejects_fullLyrics():
    _assert_unknown_rights_rejects("fullLyrics")


def test_unknown_rights_rejects_transcript():
    _assert_unknown_rights_rejects("transcript")


def test_unknown_rights_rejects_audioFile():
    _assert_unknown_rights_rejects("audioFile")


def test_unknown_rights_rejects_videoFile():
    _assert_unknown_rights_rejects("videoFile")


# --- (3)(4)(5) build_brief.py rewrites unsafe requirements -------------------

def _build_brief(requirement_text, banned_phrase):
    build = _find_script("build_brief.py")
    fixture = _tmp_json({"concept": requirement_text})
    try:
        p = _run(build, _seed_records()[0], fixture)
    finally:
        os.unlink(fixture)
    assert p.returncode == 0, f"build_brief.py failed: {p.stdout} {p.stderr}"
    out = p.stdout
    assert banned_phrase.lower() not in out.lower(), (
        f"brief still contains banned phrase {banned_phrase!r}"
    )
    brief = json.loads(out)
    if isinstance(brief.get("brief"), dict):  # tolerate a {"brief": {...}} wrapper
        brief = brief["brief"]
    prov = brief.get("provenance") or {}
    assert prov.get("safetyTransformations"), (
        "provenance.safetyTransformations missing or empty"
    )
    return brief


def test_brief_rewrites_artist_imitation():
    _build_brief("Make it exactly like Drake.", "exactly like Drake")


def test_brief_rewrites_lyric_reuse():
    _build_brief(
        "Use the lyrics from Claude's Plan", "lyrics from Claude's Plan"
    )


def test_brief_provenance_and_validation():
    brief = _build_brief("Make it exactly like Drake.", "exactly like Drake")
    prov = brief.get("provenance") or {}
    assert prov.get("generatedAt"), "provenance.generatedAt missing"
    assert "referenceSources" in prov, "provenance.referenceSources missing"
    assert brief.get("rightsStatus"), "rightsStatus missing"
    validate = _find_script("validate_brief.py")
    path = _tmp_json(brief)
    try:
        p = _run(validate, path)
        assert p.returncode == 0, (
            f"validate_brief.py rejected brief (exit {p.returncode}): "
            f"{p.stdout} {p.stderr}"
        )
    finally:
        os.unlink(path)


# --- (6) both skills discoverable with valid frontmatter ---------------------

def test_skills_discoverable():
    skill_mds = sorted(glob.glob(os.path.join(SKILLS_DIR, "*", "SKILL.md")))
    assert len(skill_mds) >= 2, f"expected >=2 skills, found {skill_mds}"
    for md in skill_mds:
        text = _read(md)
        m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
        assert m, f"{md}: missing --- delimited YAML frontmatter"
        fm = m.group(1)
        name = re.search(r"^name:\s*(.+)$", fm, re.M)
        assert name, f"{md}: frontmatter missing 'name:'"
        assert re.search(r"^description:\s*\S", fm, re.M), (
            f"{md}: frontmatter missing 'description:'"
        )
        dirname = os.path.basename(os.path.dirname(md))
        assert name.group(1).strip().strip("'\"") == dirname, (
            f"{md}: frontmatter name != directory name {dirname!r}"
        )


# --- (7) no scraped source content inside skill files ------------------------

def test_no_scraped_content_in_skill_files():
    files = sorted(
        glob.glob(os.path.join(SKILLS_DIR, "**", "*.md"), recursive=True)
        + glob.glob(os.path.join(SKILLS_DIR, "**", "*.py"), recursive=True)
    )
    assert files, f"no skill files found under {SKILLS_DIR}"
    for fp in files:
        text = _read(fp)
        for title in SEED_VIDEO_TITLES:
            assert title not in text, (
                f"{fp} contains imported source title verbatim: {title!r}"
            )


# --- (8) no network access in skill scripts ----------------------------------

def test_no_network_access_in_scripts():
    scripts = sorted(
        glob.glob(os.path.join(SKILLS_DIR, "*", "scripts", "*.py"))
    )
    assert scripts, f"no scripts found under {SKILLS_DIR}/*/scripts/"
    # urllib.parse is allowed, so match the network modules precisely.
    literals = ["urllib.request", "http.client", "socket.connect"]
    for fp in scripts:
        text = _read(fp)
        for pat in literals:
            assert pat not in text, f"{fp} references {pat}"
        assert not re.search(r"^\s*(?:import|from)\s+requests\b", text, re.M), (
            f"{fp} imports requests"
        )


# --- standalone runner -------------------------------------------------------

def _main():
    tests = sorted(
        (n, f) for n, f in globals().items()
        if n.startswith("test_") and callable(f)
    )
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {name}: {e}", file=sys.stderr)
        except Exception as e:  # missing script, bad JSON, etc.
            failed += 1
            print(f"ERROR {name}: {e!r}", file=sys.stderr)
    if failed:
        print(f"{failed} of {len(tests)} test(s) failed", file=sys.stderr)
        sys.exit(1)
    print(f"ALL TESTS PASSED ({len(tests)})")


if __name__ == "__main__":
    _main()
