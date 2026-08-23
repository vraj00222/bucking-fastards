# DropTable Records — build log

## Decisions & fallbacks taken

- **Modal**: adapted official `generate_music.py` example verbatim (image, Cls, GenerationParams). App `droptable-music`, endpoint `https://vrajpatel00222--droptable-music-generate.modal.run` (POST {caption, lyrics, duration, seed} → {audio_b64}). Weights were already cached in the `ACE-Step-v15-model-cache` Volume → warmup was instant. GATE 1 ✅ (endpoint curl → playable mp3, 91s incl. cold start).
- **Greptile FALLBACK TAKEN**: `/v2/repositories` (index/status) still works, but `POST /v2/query` is GONE — server says "Cannot POST /v2/query" on every path variant; current Greptile docs only cover code-review/MCP/knowledge-bases (product pivoted). Old docs host `docs.greptile.com` refuses connections. → `pipeline/local_intel.py` (shallow clone + grep TODO/FIXME + README → Claude) is the automatic fallback in `run.py`; greptile client stays primary-attempt. **ASK THE GREPTILE BOOTH for the current query endpoint** — if they give one, patch `greptile_client.query()` only.
- **Lyricist**: anthropic SDK 1.x dropped `temperature` kwarg → removed (default is fine). Model per spec: claude-sonnet-4-6.
- **Stage markers**: run.py prints `STAGE:intel|lyrics|audio|done SLUG:x`, `FACT:...`, `TITLE:...` — the web /api/sign route parses these for the theater.
- **Demo repos indexed on Greptile** (for the sponsor story): tj/commander.js, ace-step/ACE-Step-1.5, vraj00222/zephyr.
- GitHub user is `vraj00222` (spec said vrajpatel/agent-farm — doesn't exist; using vraj00222/zephyr as the personal repo).

## TODO before judging
- `min_containers=1` on MusicGenerator during judging hours (edit modal_app/music_service.py `@app.cls(..., min_containers=1)` + redeploy) — costs ~$2/hr, only enable at the venue.
- claude-mem plugin: install via `/plugin marketplace add thedotmack/claude-mem` then `/plugin install claude-mem@thedotmack` in Claude Code, restart session.
- Pre-generate 2 hero tracks with `--takes 3 --master`, pick best by ear.
- Wired audio out. Charge laptop.

## Commands
- Full pipeline: `.venv/bin/python pipeline/run.py --repo owner/name --style phonk --duration 75 --takes 3 --master`
- Warmup/keepalive: `.venv/bin/modal run modal_app/music_service.py::main --duration 10`
- Web: `cd web && npm run dev`
