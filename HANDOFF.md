# HANDOFF — DropTable Records (hackathon, 2026-08-23)

**Concept:** record label for codebases. Paste GitHub repo → Greptile-style intel → Claude lyrics → ACE-Step 1.5 song on Modal → web player. Full spec lives in the first user message of the original session; decisions log in `SCRATCH.md`.

## State of the gates
- **GATE 1 ✅** Modal service `droptable-music` deployed. Endpoint: `POST https://vrajpatel00222--droptable-music-generate.modal.run` body `{caption, lyrics, duration, seed}` → `{audio_b64}`. Weights cached in Volume `ACE-Step-v15-model-cache` (warm gen ≈ 60-110s for 60-80s song). Warmup: `.venv/bin/modal run modal_app/music_service.py::main --duration 10`.
- **GATE 2 ✅** (via fallback) — Greptile `/v2/query` is DEAD platform-wide (product pivoted to code review; only `/v2/repositories` index/status still answers, but `filesProcessed: 0` = no-op). `pipeline/local_intel.py` (clone+grep+Claude) is the automatic fallback inside `run.py`. **Ask the Greptile booth for a working query endpoint**; if given, fix only `greptile_client.query()`.
- **GATE 3 ✅** Lyricist (claude-sonnet-4-6; SDK 1.x — no `temperature` kwarg) quotes 10+ real repo artifacts per song. Adds `facts_highlights[]` for UI highlighting.
- **GATE 4 ✅** `python pipeline/run.py --repo tj/commander.js --style phonk --takes 1 --pick 1` → `out/tj-commander.js/track.mp3` + published to `data/tracks.json` + `web/public/tracks/`. First track: "npm install Commander" by Comma-nd.R.
- **GATE 5 ⏳** Website being built by workflow `build-droptable-site` (Next.js 15 + Tailwind v4 + wavesurfer, dark classical×phonk aesthetic, art in `web/public/art/`). API contract: `/api/sign` spawns run.py and parses stdout markers `STAGE:intel|lyrics|audio|done SLUG:x`, `FACT:…`, `TITLE:…`; `/api/status/[job]` polls.

## Running/pending (as of handoff)
- Hero tracks generating: ace-step/ACE-Step-1.5 (hyperpop) + vraj00222/zephyr (shanty), 3 takes each, `--master`. Takes land in `out/<slug>/take{1..3}.mp3`; track.mp3 = take1 — **listen and swap by copying a better take over `web/public/tracks/<slug>.mp3` + out/<slug>/track.mp3**.
- Skills package workflow `skills-package`: `.claude/skills/{tech-music-catalog,viral-song-briefing}/` + `data/catalog/` seeds + `tests/test_skills.py` (plain python asserts). Rights-aware music-reference cataloging + original-brief generation; Jeff Guo sources seeded public-metadata-only.

## Environment
- Keys in `.env` (gitignored, never committed): GREPTILE_API_KEY, GITHUB_TOKEN, ANTHROPIC_API_KEY. Modal auth in `~/.modal.toml` (profile vrajpatel00222). GitHub user: **vraj00222**.

## GITHUB_TOKEN security (action needed by user)
Current fine-grained PAT is over-scoped: probes confirmed it can READ PRIVATE REPOS and WRITE (issue-create passes auth). The pipeline only ever reads public data.
- **Rotate it**: github.com/settings/personal-access-tokens → delete current → new fine-grained token: Repository access = "Public repositories" (read-only), Account permissions = none, expiry = 7 days. Paste into `.env`.
- **Code layers already in place**: token is optional everywhere (pipeline runs unauthenticated on public repos if GITHUB_TOKEN is unset — only cost is GitHub's 60 req/hr anonymous rate limit); token is only ever sent to api.github.com; Greptile (the one third party that received it) is now OPT-IN via `GREPTILE_ENABLE=1` and off by default since their query API is sunset.
- Python: `.venv/` (3.14; modal, requests, python-dotenv, anthropic 1.x). Web: `web/` npm.
- claude-mem plugin installed (user scope) — activates on session restart; worker UI localhost:37777.

## Demo checklist (Section 10 of spec)
1. Before judging: set `min_containers=1` in `@app.cls` (modal_app/music_service.py) + `modal deploy` — kill cold starts (~$2/hr, revert after).
2. Live flow: paste pre-mined repo (facts.json cached in `out/` = instant intel) → theater → track page → `/roster`.
3. Wired audio. Charged laptop. Rehearse once end-to-end.
