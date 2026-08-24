"""Build the HyperFrames instructions file for a released track.

Reads out/<slug>/{facts,lyrics,meta,persona}.json and writes
out/<slug>/video-brief.txt — the per-lyric "receipt" map plus art direction,
consumed by pipeline/mp3_to_video.py via --instructions-file.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

ART_DIRECTION = """
KARAOKE BLOCK (LAW — overrides any single-line caption habit):
- Every frame renders its ENTIRE assigned lyric chunk as a stacked block of lines,
  ALL lines visible on screen for the frame's whole duration.
- The line currently being sung is the FOCUS: full opacity, accent color, slightly
  scaled up, glow. All other lines sit dimmed (opacity ~0.35, ink color, normal size).
- Focus advances line by line in sung order, but each line's time window is weighted
  by its syllable count (longer lines hold focus longer) so focus tracks the vocal.
- Inside the focused line, reveal/pop the words one by one with a GSAP stagger paced
  across that line's window — word-level karaoke, never two focused lines at once.
- CHORUS frames are anthems: every line bright accent color, larger type, the whole
  block pulsing on the beat — visually louder than any verse frame.
- Long chunks may shrink font size to fit — the whole block must stay inside the
  middle 70% of the canvas, no clipping.

ART DIRECTION (LAW):
- Vertical 9:16, GitHub-dark palette: #0D1117 background, #58A6FF accent, #C9D1D9 ink.
- Huge kinetic typography; punch-in zooms and hard cuts on the roast lines; glitch stutters on drops.
- RECEIPT CARDS: whenever a mapped lyric below is on screen, ALSO render its receipt as a
  GitHub-styled UI card (PR header, diff gutter with +/- lines, review comment bubble,
  CI check row, or stat badge) drawn in HTML — never screenshots, never logos beyond plain text.
  The card is secondary to the lyric: smaller, offset, never occluding it.
- Comedic timing: let a joke land, then cut.
- No real-person imagery. The lyric line stays readable middle-third for its whole span.
""".strip()


def build_brief(slug):
    out = ROOT / "out" / slug
    lyrics = json.loads((out / "lyrics.json").read_text())
    meta_path = out / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    persona_path = out / "persona.json"
    persona = json.loads(persona_path.read_text()) if persona_path.exists() else {}

    lines = [
        f'Track: "{lyrics["song_title"]}" by {lyrics["artist_name"]} — a satirical song about '
        f'{meta.get("target") or meta.get("repo") or slug}.',
        "",
        "LYRIC -> RECEIPT MAP (LAW — sync references to the song as it plays):",
    ]
    receipts = lyrics.get("receipts") or [
        {"lyric": h, "show": h} for h in lyrics.get("facts_highlights", [])
    ]
    for r in receipts:
        lines.append(f'- When the lyric says "{r["lyric"]}" -> receipt card: {r["show"]}')
    if not receipts:
        lines.append("- (no mapped receipts; lean on repo name, stars, and section labels)")

    angles = (persona.get("joke_angles") or [])[:3]
    if angles:
        lines += ["", "PERSONA FLAVOR (public internet-persona, work-targeted only):"]
        lines += [f"- {a}" for a in angles]

    lines += ["", ART_DIRECTION]
    brief = "\n".join(lines)
    (out / "video-brief.txt").write_text(brief)
    return out / "video-brief.txt"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()
    path = build_brief(args.slug)
    print(f"wrote {path}")
