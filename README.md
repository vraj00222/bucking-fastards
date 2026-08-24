# Bucking Fastard: Code to Video Generation Agent

**Point it at a GitHub repo or pull request. Get back a music video that roasts the code.**

Bucking Fastard is an automated record label for software, releasing under the
name **DropTable Records**. Feed it any public
repository or PR link and it reads the actual code, writes a satirical song about
what it found, generates the audio on a GPU, renders a karaoke-style music video
where every lyric pops on screen as it is sung, and publishes the release to a
browsable catalog.

Every joke is grounded. Behind each line of every song is a "receipt card"
showing the real diff hunk, review comment, or issue title that the lyric is
making fun of. Nothing is hallucinated. If the song says your error handling is
three nested try/catches, the video shows you the three nested try/catches.



https://github.com/user-attachments/assets/e46e1062-2889-4c44-86f6-4581157e09b7



## Watch a release

<!-- ============================================================
     TO EMBED THE VIDEO:
     1. Open a NEW ISSUE on this repo (do not submit it).
     2. Drag web/public/videos/insforge-insforge-pr-1940.mp4 into the box.
     3. Copy the https://github.com/user-attachments/assets/<uuid> URL.
     4. Replace the src below. Close the issue tab without saving.
     Do NOT use a raw.githubusercontent.com or /blob/ URL. GitHub serves
     repo files as application/octet-stream with nosniff, so they will
     not play in a browser.
     ============================================================ -->

<video src="https://github.com/user-attachments/assets/REPLACE-WITH-YOUR-UUID" controls muted playsinline width="400"></video>

*"insforge/insforge PR #1940" — a real pull request turned into a rock-pop
single, with word-by-word karaoke timing and live PR receipts on screen.*

Direct file: [`web/public/videos/insforge-insforge-pr-1940.mp4`](web/public/videos/insforge-insforge-pr-1940.mp4)

## The idea

Code review feedback is forgettable. A song about your code is not.

Open source is full of artifacts that are genuinely funny in context: the TODO
from 2019, the 4,000 line file everyone is scared to touch, the PR that changed
one character and needed six rounds of review. That comedy is invisible unless
you already live in the repo.

DropTable Records makes it legible. It turns the raw material of engineering
work into a shareable three-part artifact:

1. **A song** with lyrics that only make sense if you actually read the code.
2. **A music video** with kinetic typography, so the joke is readable without audio.
3. **A receipt trail** linking each lyric back to the real artifact it references.

The design constraint that makes this work: the model never sees the raw
repository. It sees a size-limited, structured evidence pack. That keeps the
lyrics specific and factual instead of generic AI slop about "clean code" and
"best practices."

**It roasts the engineering, never the engineer.** Jokes target commits, diffs,
architecture, and public technical persona. The pipeline never touches private
life, family, contacts, or protected traits, and it does not crawl LinkedIn or
unrelated personal profiles. Issue titles are treated as untrusted context, never
as proof that a given PR caused a bug.

## How it works

```
  GitHub repo / PR / profile URL
              |
    [1] EVIDENCE GATHERING
        GitHub API  -> repo metadata, PR scope, diff hunks, reviews, issues
        Greptile    -> architecture, entrypoints, hotspots, funny comments
        Persona     -> bounded web search of public technical persona
              |
    [2] LYRIC WRITING (Claude)
        grounded satirical lyrics + a lyric -> fact receipt for every line
              |
    [3] AUDIO (Modal, L40S GPU)
        ACE-Step 1.5 renders a 75s track from caption + lyrics
              |
    [4] VISUALS
        Claude storyboards and authors each animated HTML/GSAP frame
        Veo 2 generates 9:16 AI footage beds behind the typography
              |
    [5] RENDER (HyperFrames)
        frames -> MP4 with audio mixed in, lyric readability linted first
              |
    [6] PUBLISH
        release lands in data/tracks.json and the Next.js catalog
```

## Sponsor stack

| Tool | Role in the pipeline |
| --- | --- |
| **Anthropic Claude** | Writes grounded lyrics and receipts, plans the storyboard, authors every animated HTML frame |
| **Greptile** | Deep codebase intelligence for lyric evidence via `pipeline/greptile_client.py`, with a local clone-and-analyze fallback |
| **Modal** | ACE-Step 1.5 on an L40S GPU generates each 75s track (`modal_app/music_service.py`); CogVideoX runs there as a footage fallback |
| **Google Veo 2 (Vertex AI)** | 9:16 AI footage beds behind the kinetic typography (`droptable-video/pipeline/footage_backends.py`) |
| **HyperFrames** | Renders Claude-authored HTML/GSAP frames into the final MP4, linting lyric readability before every render |
| **GitHub API** | Repo, PR, diff-hunk, review, and org context that grounds every joke (`pipeline/github_target.py`) |

## Run the catalog

```bash
cd web
npm ci
npm run dev
```

Artwork and audio ship under `web/public/`. Then open:

- http://localhost:3000/track/insforge-insforge-pr-1940 (PR mode, karaoke video)
- http://localhost:3000/track/garrytan-gstack (repo mode, Veo 2 footage beds)

## Generate a release

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, GITHUB_TOKEN, and GREPTILE_API_KEY.
```

Three target modes:

```bash
# Repo mode
.venv/bin/python pipeline/run.py --repo owner/repo --style phonk --takes 1 --pick 1

# Pull request mode
.venv/bin/python pipeline/run.py --repo https://github.com/owner/repo/pull/123 \
  --style techrap --takes 1 --pick 1 --genius

# Profile mode: picks the highest-starred eligible public, non-fork repo
.venv/bin/python pipeline/run.py --repo https://github.com/garrytan \
  --style techrap --takes 1 --pick 1 --genius
```

Output lands in `data/tracks.json` with the chosen audio in `web/public/tracks/`.
For the UI's "Sign a repo" flow, set `PYTHON` to the same virtualenv interpreter
if it is not `.venv/bin/python`.

**Flags worth knowing**

| Flag / env | Effect |
| --- | --- |
| `--genius` / `GREPTILE_GENIUS=1` | Deeper Greptile query mode |
| `GREPTILE_ENABLE=0` | Skip Greptile, use the local analysis fallback |
| `--no-persona` | Skip the bounded public-persona web search |
| `--takes` / `--pick` | Generate N candidate tracks, publish the best M |

## Lyrics

Released lyrics and metadata live in [`data/tracks.json`](data/tracks.json) and
render through [`web/components/Lyrics.tsx`](web/components/Lyrics.tsx).

## Review music references

The curated source intake lives in `data/source-review-queue.csv`. Its generated
review-only queue is `data/source-review-queue.json`, visible at `/sources`.
These are untrusted source records, not approved catalog entries: no lyrics,
transcripts, or media are imported.

```bash
python3 pipeline/import_source_queue.py
python3 pipeline/validate_source_queue.py data/source-review-queue.json
```

## Deploy the audio service

```bash
modal deploy modal_app/music_service.py
```

If Modal assigns a different URL, update `MODAL_ENDPOINT` in `pipeline/run.py`.
