# DropTable Records

DropTable Records turns an open-source repository into a lyric-driven track: it
mines repository details, writes a song with Claude, generates audio through a
Modal-hosted ACE-Step service, and displays the release in a Next.js catalog.

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
```

The command writes release metadata to `data/tracks.json` and the chosen audio
to `web/public/tracks/`. To use the UI's “Sign a repo” flow, set `PYTHON` to
the same virtual-environment interpreter if it is not `.venv/bin/python`.

## Deploy the audio service

The generator is defined in `modal_app/music_service.py`. Configure Modal and
deploy it with:

```bash
modal deploy modal_app/music_service.py
```

If Modal gives the deployment a different URL, update `MODAL_ENDPOINT` in
`pipeline/run.py`.
