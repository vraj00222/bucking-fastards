"""Glue CLI: repo URL in, banger out.

python pipeline/run.py --repo owner/name --style phonk [--duration 75] [--takes 3] [--skip-index] [--master]
"""
import argparse
import base64
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import greptile_client
import local_intel
import lyricist

ROOT = Path(__file__).parent.parent
MODAL_ENDPOINT = "https://vrajpatel00222--droptable-music-generate.modal.run"
MASTER_FILTER = (
    "acompressor=threshold=-18dB:ratio=3:attack=20:release=250,"
    "equalizer=f=90:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1:g=1,"
    "loudnorm=I=-14:TP=-1.2:LRA=9"
)


def gen_take(caption, lyrics, duration, seed, out_path):
    t0 = time.time()
    r = requests.post(
        MODAL_ENDPOINT,
        json={"caption": caption, "lyrics": lyrics, "duration": duration, "seed": seed},
        timeout=600,
    )
    r.raise_for_status()
    out_path.write_bytes(base64.b64decode(r.json()["audio_b64"]))
    print(f"  take (seed {seed}): {out_path.name} in {int(time.time() - t0)}s", flush=True)
    return out_path


def previous_track(repo):
    tracks = json.loads((ROOT / "data/tracks.json").read_text()).get("tracks", [])
    hits = [t for t in tracks if t.get("repo") == repo]
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="owner/name or full GitHub URL")
    ap.add_argument("--style", default="phonk")
    ap.add_argument("--duration", type=float, default=75.0)
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--skip-index", action="store_true")
    ap.add_argument("--genius", action="store_true")
    ap.add_argument("--master", action="store_true")
    ap.add_argument("--pick", type=int, help="auto-pick take N (skip interactive picker)")
    args = ap.parse_args()

    repo = args.repo.removeprefix("https://github.com/").removesuffix(".git").strip("/")
    slug = greptile_client.slugify(repo)
    out = ROOT / "out" / slug
    out.mkdir(parents=True, exist_ok=True)
    timing = {}

    # 1. intel (cached)
    print("STAGE:intel", flush=True)
    facts_path = out / "facts.json"
    t0 = time.time()
    if facts_path.exists():
        facts = json.loads(facts_path.read_text())
        print(f"facts: cached ({facts_path})")
    else:
        try:
            facts = greptile_client.mine(repo, genius=args.genius, skip_index=args.skip_index)
            if all(v.startswith("(query failed") for v in facts["answers"].values()):
                raise RuntimeError("all greptile queries failed")
        except Exception as e:
            print(f"greptile unavailable ({e}); falling back to local intel")
            facts = local_intel.mine(repo)
        facts_path.write_text(json.dumps(facts, indent=2))
    timing["intel_s"] = round(time.time() - t0, 1)

    # teaser for the generation theater
    fact = (facts["answers"].get("comments") or facts["answers"].get("funny_names") or "")[:200]
    print(f"FACT:{fact}", flush=True)

    # 2. lyrics
    print("STAGE:lyrics", flush=True)
    t0 = time.time()
    prev = previous_track(repo)
    if prev:
        print(f'the label remembers this artist: "{prev["song_title"]}"')
    song = lyricist.write_song(facts, args.style, previous=prev)
    timing["lyrics_s"] = round(time.time() - t0, 1)
    (out / "lyrics.json").write_text(json.dumps(song, indent=2))
    print(f'\n"{song["song_title"]}" by {song["artist_name"]}\ncaption: {song["caption"]}\n')

    print(f'TITLE:{song["song_title"]} — {song["artist_name"]}', flush=True)

    # 3. audio: N takes in parallel
    print("STAGE:audio", flush=True)
    t0 = time.time()
    print(f"generating {args.takes} takes on Modal ({args.duration}s each) ...")
    with ThreadPoolExecutor(max_workers=args.takes) as ex:
        futs = [
            ex.submit(gen_take, song["caption"], song["lyrics"], args.duration, seed, out / f"take{seed}.mp3")
            for seed in range(1, args.takes + 1)
        ]
        [f.result() for f in futs]
    timing["audio_s"] = round(time.time() - t0, 1)

    # 4. pick winner
    if args.pick:
        choice = args.pick
    elif args.takes == 1:
        choice = 1
    else:
        choice = int(input(f"listen ({out}/take*.mp3) and choose 1-{args.takes}: ") or "1")
    shutil.copy(out / f"take{choice}.mp3", out / "track.mp3")

    if args.master:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(out / "track.mp3"), "-af", MASTER_FILTER,
             "-ar", "44100", "-b:a", "320k", str(out / "track_master.mp3")],
            check=True, capture_output=True,
        )
        shutil.copy(out / "track_master.mp3", out / "track.mp3")
        print("mastered.")

    meta = {
        "slug": slug,
        "repo": repo,
        "style": args.style,
        "song_title": song["song_title"],
        "artist_name": song["artist_name"],
        "caption": song["caption"],
        "lyrics": song["lyrics"],
        "facts_highlights": song.get("facts_highlights", []),
        "audio_url": f"/tracks/{slug}.mp3",
        "cover_url": None,
        "stars": facts.get("stars"),
        "language": facts.get("language"),
        "description": facts.get("description"),
        "sources": facts.get("sources", [])[:30],
        "timing": timing,
        "take": choice,
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2))

    # publish to site + label memory
    shutil.copy(out / "track.mp3", ROOT / "web/public/tracks" / f"{slug}.mp3")
    db_path = ROOT / "data/tracks.json"
    db = json.loads(db_path.read_text())
    db["tracks"] = [t for t in db["tracks"] if t.get("slug") != slug] + [meta]
    db_path.write_text(json.dumps(db, indent=2))
    print(f"STAGE:done SLUG:{slug}", flush=True)
    print(f"\ndone: {out}/track.mp3  |  meta: {out}/meta.json  |  published to tracks.json")


if __name__ == "__main__":
    main()
