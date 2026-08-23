#!/usr/bin/env python3
"""mp3_to_video.py — turn any MP3 + lyrics into a music video (HyperFrames + Claude).

Usage:
    python3 pipeline/mp3_to_video.py path/to/song.mp3 --lyrics path/to/lyrics.txt [OPTIONS]

Required:
    mp3                   Input MP3 file
    --lyrics FILE         Plain-text lyrics file (REQUIRED). The full lyrics are
                          split across frames and every frame keeps a readable
                          lyric line visible on screen.

Optional:
    --title "..."         Song title (default: derived from filename)
    --artist "..."        Artist name (default: "Unknown")
    --instructions TEXT   Custom creative direction (e.g. "cyberpunk vibe, red
                          highlights on nouns, glitch on the drops"). This gets
                          threaded into the planner + every frame worker.
    --instructions-file F Read custom instructions from a file (alternative
                          to --instructions).
    --out DIR             Output project dir (default: videos/<slug>/)
    --canvas WxH          Canvas size (default: 1080x1920 — 9:16 portrait)
    --fps N               Frames per second (default: 30)
    --skip-render         Author the project but don't render
    --keep-existing       Reuse existing project dir if present
    --model NAME          Claude model (default: claude-sonnet-4-5-20250929)

Prereqs:
    - ffmpeg, ffprobe, node, npx, python3 on PATH
    - librosa, numpy, soundfile, anthropic, python-dotenv installed
    - ANTHROPIC_API_KEY in env or .env
    - Skill scripts at /Users/user/.agents/skills/music-to-video/scripts/

What it does:
    1) Ingest MP3 → assets/bgm.mp3, run analyze-beatgrid.py → audiomap.json
    2) Stage the provided lyrics.txt → assets/lyrics.txt
    3) Ask Claude to plan a STORYBOARD.md (frames, lyric splits, visual direction)
    4) Ask Claude to write each frame's HTML composition (in parallel), each
       carrying its assigned lyric line, always visible
    5) Assemble index.html via assemble-index.mjs
    6) hyperframes check → auto-retry on lint errors
    7) hyperframes render → renders/final.mp4
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except Exception:
    pass

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic python-dotenv", file=sys.stderr)
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = Path("/Users/user/.agents/skills/music-to-video/scripts")

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────


def log(msg: str) -> None:
    print(f"[mp3→video] {msg}", flush=True)


def die(msg: str, code: int = 1) -> None:
    print(f"[mp3→video] FATAL: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-").lower()
    return s or "song"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    log(f"$ {' '.join(cmd)}" + (f"  (cwd={cwd})" if cwd else ""))
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        capture_output=capture,
    )


def probe_duration(mp3: Path) -> float:
    r = run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(mp3)],
        capture=True,
    )
    return float(r.stdout.strip())


def strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().startswith("json"):
            t = t.lstrip()[4:]
        t = t.strip()
        if t.endswith("```"):
            t = t[:-3].strip()
    return t


def strip_html_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().startswith("html"):
            t = t.lstrip()[4:]
        t = t.strip()
        if t.endswith("```"):
            t = t[:-3].strip()
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — scaffold project + ingest audio + analyze beatgrid
# ─────────────────────────────────────────────────────────────────────────────


def scaffold(project_dir: Path, canvas: tuple[int, int], fps: int, keep: bool) -> None:
    if project_dir.exists() and not keep:
        log(f"clearing existing project at {project_dir}")
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "assets").mkdir(exist_ok=True)
    (project_dir / "compositions" / "frames").mkdir(parents=True, exist_ok=True)
    (project_dir / "renders").mkdir(exist_ok=True)

    hf = {
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "paths": {
            "blocks": "compositions",
            "components": "compositions/components",
            "assets": "assets",
        },
        "media": {"autoProxy": True},
        "authoringSkill": "music-to-video",
    }
    (project_dir / "hyperframes.json").write_text(json.dumps(hf, indent=2))

    meta = {"id": project_dir.name, "name": project_dir.name}
    (project_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    pkg = {
        "name": project_dir.name,
        "private": True,
        "scripts": {
            "check": "npx --yes hyperframes@0.8.11 check .",
            "render": "npx --yes hyperframes@0.8.11 render",
            "publish": "npx --yes hyperframes@0.8.11 publish",
        },
    }
    (project_dir / "package.json").write_text(json.dumps(pkg, indent=2))


def ingest_audio(mp3: Path, project_dir: Path) -> Path:
    dst = project_dir / "assets" / "bgm.mp3"
    log(f"ingesting {mp3} → {dst.relative_to(REPO_ROOT)}")
    shutil.copyfile(mp3, dst)
    return dst


def analyze_audio(bgm: Path, project_dir: Path) -> dict:
    audiomap_path = project_dir / "audiomap.json"
    script = SKILL_SCRIPTS / "analyze-beatgrid.py"
    if not script.exists():
        die(f"missing analyzer at {script}")
    run(["python3", str(script), str(bgm), "-o", str(audiomap_path)])
    return json.loads(audiomap_path.read_text())


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — plan STORYBOARD.md via Claude
# ─────────────────────────────────────────────────────────────────────────────


PLAN_SYSTEM = """You are the Music Video Director for HyperFrames.

You receive an audiomap (beat/phrase/energy analysis of a song), the FULL lyrics,
and a brief that may include custom creative instructions.

Your job: return a JSON plan describing 3-8 FRAMES that tile the track gap-free.
Each frame is one scene = one HTML composition file.

The scene will be authored per-frame later, in a fresh context. Your plan is the
ONLY thing the author sees. So it must be self-contained.

═══ THE ONE INVIOLABLE RULE ═══
LYRICS ARE ALWAYS ON SCREEN. Every frame carries a `lyric_line` string that
will be rendered as a readable caption. There is NEVER a frame without a
visible lyric line. If the music has an instrumental gap, the previous line
holds as a dimmed ghost — but the field is never empty.

═══ FRAME PLANNING RULES ═══
- Frames tile the track gap-free. First frame starts at 0.0. Last frame ends at
  audio.duration_sec exactly. No gaps, no overlaps.
- 3-8 frames total. Snap boundaries to real audiomap anchors: phrase edges,
  hard_stops, key_moments (SURGE/DROP), or energy_phase edges.
- Each frame's `pacing` is one of:
    * `beat_cut` — rhythmic; hard cuts land on beat/onset.
    * `phrase_flow` — calm/sparse; slow crossfades, no per-beat cuts.
- Each frame's `mood` is 1-3 of: warm, dark, hype, elegant, glitch, cinematic,
  playful, tense, dreamy, aggressive.

═══ LYRIC SPLIT ═══
- Split the provided lyrics across frames IN ORDER (never reorder).
- Each frame's `lyric_line` is a short readable caption — 4-12 words, one or
  two phrases from the current section. Split long lines at natural breaks.
- Include section markers ([verse], [chorus], [bridge], [outro]) as short
  corner labels in the frame's `section_label` field — not inside the
  `lyric_line`.
- Every word from the source lyrics appears in exactly one frame's lyric_line.
- The `hero_words` field is 1-3 punchy words from the lyric_line to highlight
  in the accent color (usually a noun, verb, or brand mark).

═══ VISUAL DIRECTION ═══
- Each frame's `visual` note is 1-2 sentences of concrete direction: what type
  slams in, where, on which beat, with what accent effect. Not vague vibes.
- Every frame specifies colors (as hex) and fonts in the shared brand.
- If the brief contains custom `instructions`, propagate them into brand and
  per-frame visual direction. The user's instructions are LAW.

═══ OUTPUT — return ONLY this JSON shape (no fences, no commentary): ═══
{
  "brand": {
    "font_stack": "Impact, Arial Black, sans-serif",
    "palette": {
      "bg": "#1C1410",
      "ink": "#F5F2EF",
      "accent": "#D8000F",
      "muted": "#8A8681"
    },
    "notes": ["dark poster feel", "condensed all-caps", "middle-third safe"]
  },
  "frames": [
    {
      "id": "01-intro",
      "span_sec": [0.0, 6.4],
      "pacing": "beat_cut",
      "mood": ["dark", "tense"],
      "feel": "sparse intro, cowbell in distance",
      "section_label": "[verse]",
      "lyric_line": "NPM INSTALL COMMANDER, NOW I RUN THE THRONE",
      "hero_words": ["COMMANDER", "THRONE"],
      "visual": "Type slams in centered on beat 1; 'COMMANDER' pulses in accent red on the downbeat; corner tag reads 'VERSE 1A'."
    }
  ]
}

Frame IDs are two-digit-prefixed kebab-case: "01-intro", "02-verse-a", etc.
"""


def plan_storyboard(
    audiomap: dict,
    brief: dict,
    canvas: tuple[int, int],
    fps: int,
    model: str,
) -> dict:
    log("planning storyboard with Claude…")
    client = anthropic.Anthropic()

    # Compact audiomap for the LLM — full one is ~40 KB; trim beat_sec/events to summary.
    compact = {
        "summary": audiomap.get("summary"),
        "audio": audiomap.get("audio"),
        "tempo": audiomap.get("tempo"),
        "phrases": audiomap.get("phrases"),
        "hard_stops": audiomap.get("hard_stops"),
        "key_moments": audiomap.get("key_moments"),
        "energy_phases": audiomap.get("energy_phases"),
        "silences": audiomap.get("silences"),
        "rolls_count": len(audiomap.get("rolls", [])),
        "n_events": len(audiomap.get("events", [])),
    }

    lyrics_text = brief.get("lyrics") or ""
    instructions = brief.get("instructions") or ""
    inst_block = f"\n\nCUSTOM INSTRUCTIONS (VERBATIM — these are LAW):\n{instructions}\n" if instructions else ""

    user_msg = (
        f"BRIEF:\n{json.dumps({k: v for k, v in brief.items() if k not in ('lyrics', 'instructions')}, indent=2)}\n\n"
        f"CANVAS: {canvas[0]}x{canvas[1]} @ {fps}fps\n\n"
        f"FULL LYRICS (split ACROSS frames, in order, every word must appear exactly once):\n"
        f"---\n{lyrics_text}\n---\n"
        f"{inst_block}\n"
        f"AUDIOMAP (compact):\n{json.dumps(compact, indent=2)}\n\n"
        "Design the frame plan now. Return JSON only."
    )

    resp = client.messages.create(
        model=model,
        max_tokens=4000,
        system=PLAN_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text
    plan = json.loads(strip_json_fence(text))

    # Validate + snap to duration
    frames = plan["frames"]
    duration = float(audiomap["audio"]["duration_sec"])
    if not frames:
        die("Claude returned zero frames")
    frames[0]["span_sec"][0] = 0.0
    frames[-1]["span_sec"][1] = duration
    for i in range(len(frames) - 1):
        frames[i]["span_sec"][1] = frames[i + 1]["span_sec"][0]
    return plan


def storyboard_markdown(plan: dict, project_id: str, duration_s: float, canvas: tuple[int, int], fps: int) -> str:
    brand = plan["brand"]
    palette = brand["palette"]
    palette_list = [palette[k] for k in ["bg", "ink", "accent", "muted"] if k in palette]

    lines: list[str] = []
    lines.append("---")
    lines.append(f"compositionId: {project_id}")
    lines.append(f"duration_s: {duration_s:.3f}")
    lines.append(f'canvas: {{ "w": {canvas[0]}, "h": {canvas[1]}, "fps": {fps} }}')
    lines.append("style:")
    lines.append(f'  font: "{brand["font_stack"]}"')
    lines.append(f"  palette: {json.dumps(palette_list)}")
    lines.append("build_notes:")
    for n in brand.get("notes", []) + [
        "one paused timeline per frame",
        "no remote assets",
    ]:
        lines.append(f'  - "{n}"')
    lines.append("---")
    lines.append("")

    for i, f in enumerate(plan["frames"], 1):
        span = f["span_sec"]
        dur = span[1] - span[0]
        src = f"compositions/frames/{f['id']}.html"
        lyric_line = f.get("lyric_line", "")
        hero_words = f.get("hero_words", [])
        section_label = f.get("section_label", "")
        footage = f.get("footage")
        lines.append(f"## Frame {i} — {f['id']}")
        lines.append("")
        lines.append(f"- src: {src}")
        lines.append(f"- duration: {dur:.3f}s")
        lines.append(f"- span_sec: [{span[0]:.3f}, {span[1]:.3f}]")
        lines.append(f"- pacing: {f['pacing']}")
        lines.append(f"- mood: [{', '.join(f['mood'])}]")
        lines.append(f"- feel: {f['feel']}")
        if section_label:
            lines.append(f"- section: {section_label}")
        lines.append("")
        lines.append("### Groups")
        lines.append("")
        lines.append("- **g1** — free_design")
        lines.append(f"  - span_sec: [{span[0]:.3f}, {span[1]:.3f}]")
        lines.append(f'  - lyric_line: "{lyric_line}"')
        if hero_words:
            lines.append(f'  - hero_words: {json.dumps(hero_words)}')
        lines.append(f'  - visual: "{f["visual"]}"')
        if footage:
            lines.append(f'  - footage: {json.dumps(footage)}')
        lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — write each frame HTML via Claude, in parallel
# ─────────────────────────────────────────────────────────────────────────────


FRAME_SYSTEM = """You are a HyperFrames frame-worker.

You produce ONE self-contained HTML sub-composition for a music video frame.

═══ THE ONE INVIOLABLE RULE ═══
LYRICS ARE ALWAYS ON SCREEN. The `lyric_line` supplied in the prompt MUST be
rendered as a readable caption inside this frame — visible from t=0.05s until
the exit fade. Middle-third safe area. High contrast. Never off-screen, never
below 40px font, never over a busy edge without a scrim.

Words listed in `hero_words` must be highlighted in the accent color (pulse,
underline, box, glow — your call) so the eye lands on them.

If the frame has a footage bed (see FOOTAGE block below), the caption sits
ABOVE it with z-index ≥ 2 and a subtle text-shadow or dark scrim for legibility.

CONTRACT — every rule is mandatory or the linter fails the render:

1. File shape (exact):
   <!doctype html>
   <html>
     <head><meta charset="UTF-8" /></head>
     <body>
       <template>
         <div id="root" data-composition-id="{FRAME_ID}"
              data-width="{W}" data-height="{H}"
              data-duration="{DURATION}">
           <style>/* scoped under #root */</style>
           <!-- content -->
           <script>
             (function () {
               window.__timelines = window.__timelines || {};
               var tl = gsap.timeline({ paused: true });
               // ... animations ...
               tl.seek(0);
               window.__timelines["{FRAME_ID}"] = tl;
             })();
           </script>
         </div>
       </template>
     </body>
   </html>

2. #root must have position:absolute; inset:0; width:{W}px; height:{H}px;
   overflow:hidden; and the palette bg color.

3. Every timed element gets class="clip" and data-start / data-duration /
   data-track-index attributes (in TRACK-LOCAL time — starts at 0 for the
   frame's own clock). Also give each timed element a stable `id` attribute
   (e.g. id="hero-title", id="bar-1") so Studio can address them.

4. NEVER animate visibility/display on a .clip — animate opacity/autoAlpha only.
   The framework owns clip visibility.

5. No remote fetches, no Math.random(), no Date.now(). Deterministic only.

6. If you use Impact/Arial Black/Georgia/Courier New/Helvetica/Times/Consolas —
   those are OS-bundled; declare with @font-face { src: local("Impact"); } to
   satisfy the linter. Never reference remote font URLs.

7. Fade-in at 0.05s, exit hard-kill at end: at frame-local time (duration - 0.3)
   fade opacity to 0 over 0.3s, THEN at exactly `duration` do
   tl.set(el, {opacity: 0}) — this pair is REQUIRED for seek-safety.

8. Asset paths (if any) are root-relative: "assets/foo.mp4" — NEVER "../".

9. INITIAL HIDDEN STATE: use gsap.set(el, {autoAlpha: 0}) OUTSIDE the timeline
   (before `var tl = gsap.timeline(...)`), not `tl.set(...)` at position 0 — a
   zero-duration `tl.set` at 0 doesn't render on frame 0.

10. GSAP + CSS TRANSFORM CONFLICT: NEVER animate `x` / `y` / `scale` / `rotation`
    on an element whose CSS has `transform: translate(...)` for centering. GSAP
    overwrites the whole transform and centering breaks.
    Instead: use `left: 50%; top: 50%;` + `xPercent: -50; yPercent: -50` in a
    gsap.set(), then animate x/y freely. Or use `margin: auto` + flex/grid
    centering without transforms.

11. Do NOT overlap two tweens on the same property of the same element without
    `overwrite: "auto"`. If a group of elements share a class and each animates
    the same property, either use `overwrite: "auto"` or animate them via
    stagger on a single tween.

12. Keep the file under 300 lines when possible. Prefer 3-6 timed elements per
    frame, not 15+.

13. FOOTAGE BED (only if the prompt contains a FOOTAGE block): mount a
    <video class="clip" src="assets/footage/{FRAME_ID}.mp4" muted playsinline
    style="position:absolute; inset:0; width:100%; height:100%;
    object-fit:cover; opacity:0; z-index:0;"> as a DIRECT child of #root at
    z-index 0. Give it id="footage-bed", data-start="0",
    data-duration="{min(clip_dur, frame_dur)}", data-track-index="0",
    data-layout-allow-overlap. Animate opacity to 0.35 at 0.05s, back to 0 at
    (duration - 0.3), and tl.set(opacity:0) at exactly duration. Put a dark
    gradient scrim div ABOVE it (z-index 1) for lyric legibility. All lyric/
    hero text sits at z-index ≥ 2.

14. Return ONLY the HTML file contents. No markdown fences, no commentary.
"""


def frame_prompt(frame: dict, brand: dict, canvas: tuple[int, int], span_dur: float, instructions: str = "") -> str:
    palette = brand["palette"]
    lyric_line = frame.get("lyric_line", "")
    hero_words = frame.get("hero_words", [])
    section_label = frame.get("section_label", "")
    footage = frame.get("footage")

    footage_block = ""
    if footage:
        clip_dur = min(float(footage.get("duration_s", span_dur)), span_dur)
        footage_block = textwrap.dedent(
            f"""

            FOOTAGE BED (mount per rule 13):
              file: assets/footage/{frame['id']}.mp4
              clip_duration_s: {clip_dur:.3f}
              backend: {footage.get('backend', 'unknown')}
              shot_prompt: {footage.get('prompt', '')}
            """
        ).rstrip()

    inst_block = ""
    if instructions:
        inst_block = f"\n\nCUSTOM INSTRUCTIONS (VERBATIM — these are LAW):\n{instructions}\n"

    hero_str = ", ".join(hero_words) if hero_words else "(none — director's choice)"

    return textwrap.dedent(
        f"""
        FRAME ID: {frame['id']}
        CANVAS: {canvas[0]} x {canvas[1]}
        DURATION: {span_dur:.3f}s (frame-local; timeline starts at 0)
        PACING: {frame['pacing']}
        MOOD: {', '.join(frame['mood'])}
        FEEL: {frame['feel']}
        SECTION LABEL (optional small corner tag): {section_label or '(none)'}

        BRAND PALETTE:
          bg     = {palette.get('bg', '#000000')}
          ink    = {palette.get('ink', '#FFFFFF')}
          accent = {palette.get('accent', '#FF0055')}
          muted  = {palette.get('muted', '#888888')}
        FONT STACK: {brand['font_stack']}

        LYRIC LINE (MUST be visible on-screen the entire frame, middle third):
          "{lyric_line}"

        HERO WORDS (highlight in accent color): {hero_str}

        VISUAL DIRECTION:
        {frame['visual']}
        {footage_block}{inst_block}

        Design and animate this ONE frame end-to-end. Ship the full HTML file now.
        Remember: return ONLY the HTML, no fences. Lyric line MUST be readable.
        """
    ).strip()


def write_frame(client: anthropic.Anthropic, frame: dict, brand: dict, canvas: tuple[int, int], project_dir: Path, model: str, instructions: str = "") -> Path:
    span = frame["span_sec"]
    dur = span[1] - span[0]
    log(f"  authoring frame {frame['id']} ({dur:.2f}s)…")
    resp = client.messages.create(
        model=model,
        max_tokens=8000,
        system=FRAME_SYSTEM,
        messages=[{"role": "user", "content": frame_prompt(frame, brand, canvas, dur, instructions)}],
    )
    html = strip_html_fence(resp.content[0].text)
    out = project_dir / "compositions" / "frames" / f"{frame['id']}.html"
    out.write_text(html)
    log(f"    → {out.relative_to(REPO_ROOT)} ({len(html)} bytes)")
    return out


def write_all_frames(plan: dict, project_dir: Path, canvas: tuple[int, int], model: str, instructions: str = "") -> None:
    log(f"authoring {len(plan['frames'])} frames in parallel…")
    client = anthropic.Anthropic()
    brand = plan["brand"]

    with ThreadPoolExecutor(max_workers=min(6, len(plan["frames"]))) as ex:
        futs = {ex.submit(write_frame, client, f, brand, canvas, project_dir, model, instructions): f for f in plan["frames"]}
        for fut in as_completed(futs):
            f = futs[fut]
            try:
                fut.result()
            except Exception as e:
                log(f"  ! frame {f['id']} failed: {e}")
                raise


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — assemble index.html + check + render
# ─────────────────────────────────────────────────────────────────────────────


def assemble_index(project_dir: Path, audiomap_path: Path) -> None:
    log("assembling index.html…")
    script = SKILL_SCRIPTS / "assemble-index.mjs"
    if not script.exists():
        die(f"missing assembler at {script}")
    run(
        [
            "node",
            str(script),
            "--storyboard",
            "STORYBOARD.md",
            "--hyperframes",
            ".",
            "--audiomap",
            str(audiomap_path.relative_to(project_dir)),
        ],
        cwd=project_dir,
    )


def hyperframes_check(project_dir: Path) -> tuple[int, str]:
    """Run hyperframes check, return (error_count, full_output)."""
    log("running hyperframes check…")
    r = subprocess.run(
        ["npx", "--yes", "hyperframes@0.8.11", "check", "."],
        cwd=str(project_dir),
        text=True,
        capture_output=True,
    )
    combined = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"(\d+)\s+error\(s\)", combined)
    errs = int(m.group(1)) if m else (0 if r.returncode == 0 else 1)
    return errs, combined


def parse_lint_errors_by_file(output: str, project_dir: Path) -> dict[Path, list[str]]:
    """Parse `hyperframes check` output → { frame_html_path: [error_line, ...] }."""
    errors: dict[Path, list[str]] = {}
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if "✗" not in line:
            continue
        msg = line.strip()
        # Path is on the next non-empty line, indented.
        for j in range(i + 1, min(i + 5, len(lines))):
            path_line = lines[j].strip()
            if path_line.startswith("/") and ".html" in path_line:
                # extract just the path (may have trailing " #id t=...s")
                path_str = path_line.split(" ")[0]
                p = Path(path_str)
                if p.exists() and p.is_relative_to(project_dir):
                    errors.setdefault(p, []).append(msg)
                break
    return errors


REPAIR_SYSTEM = """You are a HyperFrames frame-worker fixing lint errors.

You receive: (a) an existing frame HTML file, and (b) a list of specific lint
errors the check found. Rewrite the file to fix EVERY error, changing as little
else as possible. Preserve the visual intent.

Common fixes:
- gsap_css_transform_conflict: remove `transform: translate(...)` from CSS.
  Replace with `left: 50%; top: 50%;` then `gsap.set(el, { xPercent: -50, yPercent: -50 })`.
- gsap_timeline_set_initial_hide: move `tl.set(el, {autoAlpha: 0}, 0)` calls to
  `gsap.set(el, {autoAlpha: 0})` OUTSIDE the timeline.
- overlapping_gsap_tweens: add `overwrite: "auto"` to overlapping tweens.
  If two tweens on the SAME property start at the SAME time (e.g. `x` on
  `#lyric-container` at 11.10s and 11.10s), delete the duplicate — one of
  them is redundant.
- studio_missing_editable_id: add `id="..."` to every timed element.
- media_missing_src: put `src="..."` directly on <video>, not on <source>.
- invalid_parent_traversal_in_asset_path: change "../../foo" to "foo".
- gsap_exit_missing_hard_kill: after fade-out, add `tl.set(el, {opacity: 0}, duration)`.
- gsap_animates_clip_element: never animate visibility/display on .clip — only
  opacity/autoAlpha.
- gsap_fullscreen_overlay_starts_visible: a full-frame overlay (like #vignette,
  #scrim, .overlay) needs `opacity: 0` in its CSS/inline style, or a
  `gsap.set(el, { opacity: 0 })` call OUTSIDE the timeline BEFORE `var tl = ...`.
  It must not be visible on the first rendered frame.
- gsap_infinite_repeat: change `repeat: -1` to a finite count that fits the
  composition duration (e.g. `repeat: 3`), or delete the repeat entirely and
  extend the tween duration to match the frame duration.
- timeline_track_too_dense: reduce the number of `.clip` elements on this
  track. Merge coherent groups into one wrapper element with staggered inner
  tweens. Aim for ≤ 3 elements per track index.

Return ONLY the fixed HTML. No fences, no commentary.
"""


def repair_frames(errors_by_file: dict[Path, list[str]], model: str) -> None:
    log(f"repairing {len(errors_by_file)} frame(s) with lint errors…")
    client = anthropic.Anthropic()

    def repair_one(path: Path, errors: list[str]) -> None:
        current_html = path.read_text()
        error_list = "\n".join(f"  - {e}" for e in errors)
        user = (
            f"FILE: {path.name}\n\nERRORS:\n{error_list}\n\n"
            f"CURRENT HTML:\n{current_html}\n\n"
            "Fix every error. Return the full corrected HTML."
        )
        log(f"  repairing {path.name} ({len(errors)} error(s))…")
        resp = client.messages.create(
            model=model,
            max_tokens=8000,
            system=REPAIR_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        fixed = strip_html_fence(resp.content[0].text)
        path.write_text(fixed)

    with ThreadPoolExecutor(max_workers=min(4, len(errors_by_file))) as ex:
        futs = [ex.submit(repair_one, p, es) for p, es in errors_by_file.items()]
        for fut in as_completed(futs):
            fut.result()


def hyperframes_render(project_dir: Path, out_name: str = "final.mp4", fps: int = 30) -> Path:
    out = project_dir / "renders" / out_name
    log(f"rendering → {out.relative_to(REPO_ROOT)}")
    run(
        [
            "npx",
            "--yes",
            "hyperframes@0.8.11",
            "render",
            ".",
            "-o",
            f"renders/{out_name}",
            "--fps",
            str(fps),
        ],
        cwd=project_dir,
    )
    if not out.exists():
        die(f"render finished but output not found at {out}")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description="Turn an MP3 + lyrics into a music video.")
    ap.add_argument("mp3", type=Path, help="input MP3 file")
    ap.add_argument("--lyrics", type=Path, required=True, help="plain-text lyrics file (REQUIRED)")
    ap.add_argument("--title", default=None)
    ap.add_argument("--artist", default="Unknown")
    ap.add_argument("--instructions", default=None, help="verbatim creative instructions (LAW)")
    ap.add_argument("--instructions-file", type=Path, default=None, help="read instructions from a file")
    ap.add_argument("--footage-backend", choices=["none", "veo", "cogvideox"], default="none",
                    help="AI footage bed source for select frames (default: none)")
    ap.add_argument("--footage-frames", type=int, default=2,
                    help="how many frames get a footage bed (default: 2, max 3)")
    ap.add_argument("--gcp-project", default=None, help="GCP project for Veo (or env GOOGLE_CLOUD_PROJECT)")
    ap.add_argument("--out", type=Path, default=None, help="project output dir")
    ap.add_argument("--canvas", default="1080x1920", help="WIDTHxHEIGHT (default 1080x1920)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--keep-existing", action="store_true")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    if not args.mp3.exists():
        die(f"mp3 not found: {args.mp3}")
    if not args.lyrics.exists():
        die(f"lyrics file not found: {args.lyrics}")
    if args.instructions and args.instructions_file:
        die("--instructions and --instructions-file are mutually exclusive")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        die("ANTHROPIC_API_KEY missing (set in env or .env)")

    canvas_parts = args.canvas.lower().split("x")
    if len(canvas_parts) != 2:
        die("--canvas must be WIDTHxHEIGHT, e.g. 1080x1920")
    canvas = (int(canvas_parts[0]), int(canvas_parts[1]))

    title = args.title or args.mp3.stem.replace("_", " ").replace("-", " ").title()
    slug = slugify(args.mp3.stem)
    project_dir = (args.out or (REPO_ROOT / "videos" / slug)).resolve()

    lyrics_text = args.lyrics.read_text().strip()
    log(f"loaded {len(lyrics_text)} chars of lyrics")

    instructions = ""
    if args.instructions:
        instructions = args.instructions.strip()
    elif args.instructions_file:
        if not args.instructions_file.exists():
            die(f"instructions file not found: {args.instructions_file}")
        instructions = args.instructions_file.read_text().strip()
    if instructions:
        log(f"custom instructions: {len(instructions)} chars")

    footage_frames = max(0, min(3, args.footage_frames))
    log(f"title  : {title}")
    log(f"artist : {args.artist}")
    log(f"project: {project_dir.relative_to(REPO_ROOT) if project_dir.is_relative_to(REPO_ROOT) else project_dir}")
    log(f"canvas : {canvas[0]}x{canvas[1]} @ {args.fps}fps")
    log(f"footage: backend={args.footage_backend} frames={footage_frames}")

    t0 = time.time()

    # Step 1: scaffold + ingest + analyze
    scaffold(project_dir, canvas, args.fps, keep=args.keep_existing)
    bgm = ingest_audio(args.mp3, project_dir)
    duration = probe_duration(bgm)
    log(f"track duration: {duration:.2f}s")
    audiomap = analyze_audio(bgm, project_dir)

    # Stage lyrics.txt into assets/ for archive/repro
    (project_dir / "assets" / "lyrics.txt").write_text(lyrics_text)

    brief = {
        "title": title,
        "artist": args.artist,
        "duration_sec": duration,
        "lyrics": lyrics_text,
        "lyrics_always_on": True,
        "instructions": instructions,
        "canvas": {"w": canvas[0], "h": canvas[1], "fps": args.fps},
    }

    # Step 2: plan STORYBOARD.md
    plan = plan_storyboard(audiomap, brief, canvas, args.fps, args.model)

    # Step 2b: optionally attach footage assignments to selected frames
    if args.footage_backend != "none" and footage_frames > 0:
        try:
            from pipeline.footage_backends import (  # type: ignore
                assign_footage_to_plan,
                generate_footage_for_plan,
            )
        except Exception:
            # Allow running from repo root without package install:
            sys.path.insert(0, str(REPO_ROOT))
            from pipeline.footage_backends import (  # type: ignore
                assign_footage_to_plan,
                generate_footage_for_plan,
            )

        assign_footage_to_plan(
            plan,
            backend_name=args.footage_backend,
            n=footage_frames,
            model=args.model,
        )
        generate_footage_for_plan(
            plan,
            project_dir=project_dir,
            backend_name=args.footage_backend,
            gcp_project=args.gcp_project or os.environ.get("GOOGLE_CLOUD_PROJECT"),
        )

    (project_dir / "plan.json").write_text(json.dumps(plan, indent=2))
    sb_md = storyboard_markdown(plan, project_dir.name, duration, canvas, args.fps)
    (project_dir / "STORYBOARD.md").write_text(sb_md)
    log(f"planned {len(plan['frames'])} frames")

    # Step 3: author frames in parallel
    write_all_frames(plan, project_dir, canvas, args.model, instructions)

    # Step 4: assemble + check + render
    assemble_index(project_dir, project_dir / "audiomap.json")

    MAX_REPAIR_PASSES = 2
    for attempt in range(MAX_REPAIR_PASSES + 1):
        errs, output = hyperframes_check(project_dir)
        if errs == 0:
            log("✓ check passed")
            break
        log(f"⚠ hyperframes check found {errs} error(s) (attempt {attempt + 1}/{MAX_REPAIR_PASSES + 1})")
        if attempt >= MAX_REPAIR_PASSES:
            print(output, file=sys.stderr)
            die(f"check still failing after {MAX_REPAIR_PASSES} repair pass(es) — inspect {project_dir}/")
        errors_by_file = parse_lint_errors_by_file(output, project_dir)
        if not errors_by_file:
            print(output, file=sys.stderr)
            die("could not attribute lint errors to any frame file — manual fix needed")
        repair_frames(errors_by_file, args.model)

    if args.skip_render:
        log(f"done (skipped render). Project ready at {project_dir}")
        return 0

    out = hyperframes_render(project_dir, out_name="final.mp4", fps=args.fps)
    elapsed = time.time() - t0
    log(f"✓ done in {elapsed:.1f}s — {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
