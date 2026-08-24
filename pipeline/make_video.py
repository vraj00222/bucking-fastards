"""Glue: released track -> HyperFrames video -> published on the site.

python3 pipeline/make_video.py --slug <slug> [--footage veo|cogvideox|none]

Reads out/<slug>/ (track.mp3, lyrics.json, video-brief.txt), runs mp3_to_video.py
(Veo first, auto-fallback to CogVideoX), copies the render to
web/public/videos/<slug>.mp4 and sets video_url in data/tracks.json.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notify

VIDEO_ROOT = Path(__file__).resolve().parent.parent
MAIN_ROOT = VIDEO_ROOT                                         # same checkout; override with --main-root


def log(msg):
    print(msg, flush=True)
    notify.log(msg)


def die(msg):
    notify.flush(f"❌ video render failed")
    sys.exit(msg)


def sh(cmd, **kw):
    log(f"$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run([str(c) for c in cmd], **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--footage", default="veo", choices=["veo", "cogvideox", "none"])
    ap.add_argument("--main-root", type=Path, default=MAIN_ROOT)
    args = ap.parse_args()

    out = args.main_root / "out" / args.slug
    lyrics = json.loads((out / "lyrics.json").read_text())
    mp3 = out / "track.mp3"
    brief = out / "video-brief.txt"
    for p in (mp3, brief):
        if not p.exists():
            die(f"missing {p} (run pipeline/run.py then pipeline/video_brief.py first)")

    log(f"🎬 rendering video for {args.slug} (footage: {args.footage})")

    lyrics_txt = out / "lyrics.txt"
    lyrics_txt.write_text(lyrics["lyrics"])
    project = VIDEO_ROOT / ".local-video-output" / args.slug

    def render(backend):
        cmd = [
            sys.executable, VIDEO_ROOT / "pipeline" / "mp3_to_video.py", mp3,
            "--lyrics", lyrics_txt,
            "--title", lyrics["song_title"], "--artist", lyrics["artist_name"],
            "--instructions-file", brief, "--out", project,
        ]
        if backend != "none":
            cmd += ["--footage-backend", backend, "--footage-frames", "2"]
        return sh(cmd, cwd=VIDEO_ROOT).returncode

    rc = render(args.footage)
    if rc != 0 and args.footage == "veo":
        log("veo failed; retrying with cogvideox")
        rc = render("cogvideox")
    if rc != 0 and args.footage != "none":
        log("footage backend failed; retrying type-only")
        rc = render("none")
    if rc != 0:
        die("video render failed")

    renders = sorted((project / "renders").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not renders:
        die(f"no renders in {project / 'renders'}")
    final = renders[-1]

    dest = args.main_root / "web" / "public" / "videos" / f"{args.slug}.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(final, dest)

    db_path = args.main_root / "data" / "tracks.json"
    db = json.loads(db_path.read_text())
    for track in db["tracks"]:
        if track.get("slug") == args.slug:
            track["video_url"] = f"/videos/{args.slug}.mp4"
            break
    else:
        die(f"slug {args.slug} not found in tracks.json (video copied, url not set)")
    db_path.write_text(json.dumps(db, indent=2))
    log(f"published: {dest}  |  video_url set for {args.slug}")
    notify.flush(f"🎬 {args.slug} — render log")
    notify.send(
        f'🎬 video ready — "{track["song_title"]}" by {track["artist_name"]}\n'
        f'mp3: {notify.public_url(track.get("audio_url") or f"/tracks/{args.slug}.mp3")}\n'
        f'video: {notify.public_url(track["video_url"])}'
    )


if __name__ == "__main__":
    main()
