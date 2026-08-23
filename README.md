# DropTable Records

DropTable Records turns an open-source repository or public GitHub pull request
into a lyric-driven track: it mines repository/PR details, writes a song with
Claude, generates audio through a Modal-hosted ACE-Step service, and displays
the release in a Next.js catalog.

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
# Fill in ANTHROPIC_API_KEY and GITHUB_TOKEN.
.venv/bin/python pipeline/run.py --repo owner/repo --style phonk --takes 1 --pick 1
# Or write about one pull request:
.venv/bin/python pipeline/run.py --repo https://github.com/owner/repo/pull/123 --style techrap --takes 1 --pick 1
```

The command writes release metadata to `data/tracks.json` and the chosen audio
to `web/public/tracks/`. To use the UI's “Sign a repo” flow, set `PYTHON` to
the same virtual-environment interpreter if it is not `.venv/bin/python`.

PR songs use public GitHub PR, repository, review, and limited GitHub-profile
context only. The pipeline does not crawl LinkedIn or unrelated personal
profiles. Lyrics are instructed to roast the engineering work—not a person.

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
