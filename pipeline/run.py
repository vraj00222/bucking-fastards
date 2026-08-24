"""Glue CLI: repo URL in, banger out.

python pipeline/run.py --repo owner/name --style phonk [--duration 75] [--takes 3] [--skip-index] [--master]
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import greptile_client
import github_target
import local_intel
import lyricist
import notify
import persona_intel

ROOT = Path(__file__).parent.parent
MODAL_ENDPOINT = "https://vrajpatel00222--droptable-music-generate.modal.run"
MASTER_FILTER = (
    "acompressor=threshold=-18dB:ratio=3:attack=20:release=250,"
    "equalizer=f=90:t=q:w=1:g=1.5,equalizer=f=3200:t=q:w=1:g=1,"
    "loudnorm=I=-14:TP=-1.2:LRA=9"
)


def log(msg):
    """stdout for the web UI parser, Telegram buffer for the subscribers."""
    print(msg, flush=True)
    notify.log(msg)


def gen_take(caption, lyrics, duration, seed, out_path):
    t0 = time.time()
    r = requests.post(
        MODAL_ENDPOINT,
        json={"caption": caption, "lyrics": lyrics, "duration": duration, "seed": seed},
        timeout=600,
    )
    r.raise_for_status()
    out_path.write_bytes(base64.b64decode(r.json()["audio_b64"]))
    log(f"  take (seed {seed}): {out_path.name} in {int(time.time() - t0)}s")
    return out_path


def previous_track(repo):
    tracks = json.loads((ROOT / "data/tracks.json").read_text()).get("tracks", [])
    hits = [t for t in tracks if t.get("repo") == repo]
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="GitHub profile, owner/name, GitHub repo URL, or GitHub PR URL")
    ap.add_argument("--style", default="phonk")
    ap.add_argument("--duration", type=float, default=75.0)
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--skip-index", action="store_true")
    ap.add_argument("--genius", action="store_true")
    ap.add_argument("--master", action="store_true")
    ap.add_argument("--pick", type=int, help="auto-pick take N (skip interactive picker)")
    ap.add_argument("--no-persona", action="store_true", help="skip public-persona web research")
    args = ap.parse_args()

    target = github_target.parse_target(args.repo)
    if target["kind"] == "profile":
        target = github_target.resolve_profile_repository(target["login"])
    repo = target["repo"]
    slug = target["slug"]
    existing = json.loads((ROOT / "data/tracks.json").read_text())["tracks"]
    if any(t["slug"] == slug and t.get("style") != args.style for t in existing):
        slug = f"{slug}-{args.style}"  # second album, don't clobber the first
    out = ROOT / "out" / slug
    out.mkdir(parents=True, exist_ok=True)
    timing = {}

    # 1. intel (cached)
    log("STAGE:intel")
    facts_path = out / "facts.json"
    t0 = time.time()
    if facts_path.exists():
        facts = json.loads(facts_path.read_text())
        log(f"facts: cached ({facts_path})")
    else:
        facts = None
        # Greptile indexing and queries are used whenever its key is configured.
        # Set GREPTILE_ENABLE=0 to choose the local fallback: indexing can take
        # time on a large repository and sends repository access context to a
        # third party. GitHub PR/issue context below is refreshed every run.
        greptile_enabled = os.environ.get("GREPTILE_ENABLE", "1").lower() not in {"0", "false", "no"}
        if greptile_enabled and os.environ.get("GREPTILE_API_KEY"):
            try:
                facts = greptile_client.mine(repo, genius=args.genius, skip_index=args.skip_index)
                if all(v.startswith("(query failed") for v in facts["answers"].values()):
                    raise RuntimeError("all greptile queries failed")
            except Exception as e:
                log(f"greptile unavailable ({e}); falling back to local intel")
                facts = None
        if facts is None:
            facts = local_intel.mine(repo)
    # Code intel can stay cached; live GitHub context (issues/PR/reviews) must
    # be refreshed for every release so lyrics do not joke about stale state.
    log("reading public GitHub context ...")
    repository_context = github_target.collect_repository_context(repo)
    facts["target_type"] = target["kind"]
    facts["target_label"] = target["label"]
    facts["github_context"] = repository_context
    if target["kind"] == "pull-request":
        log(f"reading pull request #{target['number']} ...")
        facts["pull_request"] = github_target.collect_pull_request(
            repo, target["number"], repository_context
        )
    if target.get("profile"):
        facts["profile_context"] = target["profile"]
        facts["repository_selection"] = target["selection"]
    if not args.no_persona and not facts.get("persona_context"):
        pr_author = ((facts.get("pull_request") or {}).get("author") or {})
        login = pr_author.get("login") or (facts.get("profile_context") or {}).get("login") or repo.split("/")[0]
        try:
            log(f"researching public persona of {login} ...")
            facts["persona_context"] = persona_intel.gather(
                login,
                name=pr_author.get("name"),
                context=facts.get("description"),
                cache_path=out / "persona.json",
            )
        except Exception as e:
            log(f"persona research unavailable ({e}); continuing without it")
    facts_path.write_text(json.dumps(facts, indent=2))
    timing["intel_s"] = round(time.time() - t0, 1)

    # teaser for the generation theater
    fact = (facts["answers"].get("comments") or facts["answers"].get("funny_names") or "")[:200]
    log(f"FACT:{fact}")
    notify.flush(f"🎧 {slug} — intel done in {timing['intel_s']}s")

    # 2. lyrics
    log("STAGE:lyrics")
    t0 = time.time()
    prev = previous_track(repo)
    if prev:
        log(f'the label remembers this artist: "{prev["song_title"]}"')
    song = lyricist.write_song(facts, args.style, previous=prev)
    timing["lyrics_s"] = round(time.time() - t0, 1)
    (out / "lyrics.json").write_text(json.dumps(song, indent=2))
    log(f'\n"{song["song_title"]}" by {song["artist_name"]}\ncaption: {song["caption"]}\n')

    log(f'TITLE:{song["song_title"]} — {song["artist_name"]}')
    notify.flush(f"🎤 {slug} — lyrics done in {timing['lyrics_s']}s")

    # 3. audio: N takes in parallel
    log("STAGE:audio")
    t0 = time.time()
    log(f"generating {args.takes} takes on Modal ({args.duration}s each) ...")
    with ThreadPoolExecutor(max_workers=args.takes) as ex:
        futs = [
            ex.submit(gen_take, song["caption"], song["lyrics"], args.duration, seed, out / f"take{seed}.mp3")
            for seed in range(1, args.takes + 1)
        ]
        [f.result() for f in futs]
    timing["audio_s"] = round(time.time() - t0, 1)
    notify.flush(f"🔊 {slug} — audio done in {timing['audio_s']}s")

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
        log("mastered.")

    meta = {
        "slug": slug,
        "repo": repo,
        "target": target["label"],
        "pull_request": facts.get("pull_request"),
        "github_context": facts.get("github_context"),
        "profile_context": facts.get("profile_context"),
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
    old = next((t for t in db["tracks"] if t.get("slug") == slug), None)
    if old and old.get("video_url") and not meta.get("video_url"):
        meta["video_url"] = old["video_url"]  # keep the published video on republish
    db["tracks"] = [t for t in db["tracks"] if t.get("slug") != slug] + [meta]
    db_path.write_text(json.dumps(db, indent=2))
    log(f"STAGE:done SLUG:{slug}")
    log(f"\ndone: {out}/track.mp3  |  meta: {out}/meta.json  |  published to tracks.json")
    notify.log(f"mp3: {notify.public_url(meta['audio_url'])}")
    if meta.get("video_url"):
        notify.log(f"video: {notify.public_url(meta['video_url'])}")
    notify.flush(f'🎉 released "{meta["song_title"]}" — {meta["artist_name"]}')


if __name__ == "__main__":
    main()
