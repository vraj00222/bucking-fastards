# DropTable Records

DropTable Records turns any open-source repository or public GitHub pull request
into a satirical song **and a lyric-synced music video**: it mines repo/PR
details (including the actual diff), writes grounded roast lyrics with Claude,
generates audio on a Modal GPU, renders a karaoke-style HyperFrames video where
each lyric pops as it's sung alongside a "receipt card" of the real artifact it
references, and publishes everything to a Next.js catalog.

## Demo

Run the catalog (below), then open a release with its music video:

- http://localhost:3000/track/insforge-insforge-pr-1940 — a real PR turned into
  a rock-pop single with word-by-word karaoke video and on-screen PR receipts
  (`web/public/videos/insforge-insforge-pr-1940.mp4`)
- http://localhost:3000/track/garrytan-gstack — repo-mode demo with Veo 2
  footage beds (`web/public/videos/garrytan-gstack.mp4`)

## How we use our sponsors

- **Greptile** — deep codebase intelligence (architecture, hotspots, funny
  comments) for lyric evidence via `pipeline/greptile_client.py`, with a local
  clone-and-analyze fallback when unavailable.
- **Anthropic Claude** — writes the grounded satirical lyrics + lyric→fact
  receipts, plans the video storyboard, and authors every animated HTML frame.
- **Modal** — ACE-Step 1.5 on an L40S GPU generates each 75s track from a
  caption + lyrics (`modal_app/music_service.py`); CogVideoX video service runs
  there too as a footage fallback.
- **Google Veo 2 (Vertex AI)** — generates 9:16 AI footage beds behind the
  kinetic typography (`droptable-video/pipeline/footage_backends.py`).
- **HyperFrames** — renders the Claude-authored HTML/GSAP frames into the final
  MP4 with the audio mixed in, linting lyric readability before every render.
- **GitHub API** — repo, PR, diff-hunk, review, and org context that grounds
  every joke (`pipeline/github_target.py`).

## Lyrics

Released-song lyrics and their metadata are stored in
[`data/tracks.json`](data/tracks.json). The catalog renders them with
[`web/components/Lyrics.tsx`](web/components/Lyrics.tsx).

## Run the catalog

```bash
cd web
npm ci
npm run dev
```

The catalog includes its published artwork and audio under `web/public/`.

## Generate a release

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, GITHUB_TOKEN, and GREPTILE_API_KEY.
.venv/bin/python pipeline/run.py --repo owner/repo --style phonk --takes 1 --pick 1
# Or write about one pull request:
.venv/bin/python pipeline/run.py --repo https://github.com/owner/repo/pull/123 --style techrap --takes 1 --pick 1 --genius
# Or resolve an eligible public repository from a public GitHub profile:
.venv/bin/python pipeline/run.py --repo https://github.com/garrytan --style techrap --takes 1 --pick 1 --genius
```

The command writes release metadata to `data/tracks.json` and the chosen audio
to `web/public/tracks/`. To use the UI's “Sign a repo” flow, set `PYTHON` to
the same virtual-environment interpreter if it is not `.venv/bin/python`.

GitHub supplies fresh public repository metadata, active issue titles, PR
scope, review state/comments, and limited GitHub-profile context on every run.
When `GREPTILE_API_KEY` is configured, Greptile additionally indexes the
default branch and answers bounded architecture, entrypoint, dependency,
test/CI, hotspot, command, and source-location questions. The lyric model gets
a size-limited evidence pack—not raw repository contents—and is instructed to
make jokes about engineering work, not people. Set `GREPTILE_ENABLE=0` to use
the local analysis fallback; set `GREPTILE_GENIUS=1` for the UI's deeper query
mode. A profile target chooses the highest-starred eligible public, non-fork
repository and records that selection in its release metadata.

Person context comes from the GitHub API plus, when enabled, a bounded web
search for the subject's PUBLIC internet persona (their own posts, talks,
launches, press coverage, community reaction) via `pipeline/persona_intel.py`
(`--no-persona` skips it). It never collects private life, family, contacts,
or protected traits, and the pipeline does not crawl LinkedIn or unrelated
personal profiles. Jokes target the public work and persona, never the person.
Issue titles remain untrusted project context, never proof that a PR caused a
bug.

## Review music references

The curated source intake lives in `data/source-review-queue.csv`; its generated
review-only queue is `data/source-review-queue.json`, visible at `/sources`.
It contains untrusted source records, not approved catalog entries: no lyrics,
transcripts, or media are imported. Rebuild and validate it with:

```bash
python3 pipeline/import_source_queue.py
python3 pipeline/validate_source_queue.py data/source-review-queue.json
```

## Deploy the audio service

The generator is defined in `modal_app/music_service.py`. Configure Modal and
deploy it with:

```bash
modal deploy modal_app/music_service.py
```

If Modal gives the deployment a different URL, update `MODAL_ENDPOINT` in
`pipeline/run.py`.
