"""Turn facts.json + style preset into song JSON via Claude."""
import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from presets import PRESETS

SYSTEM = """You are the head songwriter at DropTable Records, a label that signs open-source repos as artists. You write FUNNY, hyper-specific song lyrics about codebases. Rules:
- Use the provided repo facts. Quote real function names, real TODO comments, real commands (like `npm install X`), real file names. Specificity is the joke.
- Structure with tags on their own lines: [verse] [chorus] [verse] [bridge] [chorus] [outro]. Total 140-240 words (target a 60-90 second song).
- The chorus must be a simple, repeatable, catchy hook - ideally built on a command, an error message, or the repo's one-line purpose.
- Write in the requested style's voice (a phonk track brags; an emo ballad mourns a deprecated dependency; a sea shanty is about the crew merging to main).
- Emotional and human, not a feature list. One vivid image beats three facts.
- Never copy lyrics/melodies from real songs. Style, not song, is the reference.
- artist_name: a music-artist pun on the repo name. song_title: short and punchy.
- caption: comma-separated style tags for a music model (genre, mood, instruments, tempo, vocal type). Start from the preset given, add 2-3 tags that fit this repo's personality.
Output ONLY the JSON object."""


def write_song(facts, style, previous=None):
    client = anthropic.Anthropic()
    user = (
        f"Style preset: {style}\nBase caption: {PRESETS[style]}\n\n"
        f"Repo facts:\n{json.dumps({k: facts[k] for k in ('repo', 'stars', 'language', 'description', 'answers')}, indent=2)}\n\n"
        'Output JSON keys: "song_title", "artist_name", "caption", "lyrics", "facts_highlights".\n'
        "facts_highlights: array of the exact substrings of your lyrics that quote real repo details "
        "(function names, TODO comments, commands, file names) - copy them verbatim from the lyrics."
    )
    if previous:
        user += (
            f"\n\nThe label REMEMBERS this artist. Their previous track was "
            f'"{previous["song_title"]}" with the hook "{previous.get("hook", "")}". '
            "You MUST reference the previous song somewhere in the lyrics (the difficult second album)."
        )
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", required=True)
    ap.add_argument("--style", default="phonk")
    args = ap.parse_args()
    facts = json.loads(Path(args.facts).read_text())
    song = write_song(facts, args.style)
    print(json.dumps(song, indent=2))
