#!/usr/bin/env python3
"""Generate Veo 3 Fast shots for the tj-commander.js music video Phase 2.

Runs 2 prompts (03g1-terminal-spawn, 04g1-cowbell-macro), each producing
`number_of_videos=2` candidates, then downloads to `assets/veo/`. Audio-strips
via ffmpeg. Writes a manifest.jsonl for reproducibility.

Usage:
    python3 video/tj-commander-js/scripts/generate_veo_shots.py \\
        [--project sharp-leaf-451416-r4] [--location us-central1] \\
        [--only 03g1|04g1] [--dry-run]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: pip install google-genai", file=sys.stderr)
    sys.exit(1)

MAX_CLIPS = 4  # hard budget ceiling: 2 shots x 2 candidates

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "videos" / "tj-commander-js" / "assets" / "veo"
MANIFEST = OUT_DIR / "manifest.jsonl"

TERMINAL_PROMPT = (
    "Single continuous shot, no scene cuts. Portrait 9:16 macro of a vintage CRT "
    "computer monitor in a dark room, green phosphor text on black. The terminal is "
    "spawning child processes: lines of \"PID 1234 -> PID 1235 -> PID 1236\" cascade "
    "downward, one per second, with mild scanline flicker and chromatic aberration on "
    "the type. Slow, imperceptible zoom-in on the center of the screen. Sodium-vapor "
    "amber (#FF9500) light bleeds in from the top edge. Heavy film grain, VHS tracking "
    "artifacts at the edges. Dark, ominous, industrial. Camera perfectly still except "
    "for the slow push-in. No dialogue. No music. No sound effects. Silent."
)

COWBELL_PROMPT = (
    "Single continuous shot, no scene cuts. Portrait 9:16 extreme macro of a chrome "
    "808 cowbell suspended in black void, slowly rotating clockwise. Sodium-vapor "
    "amber (#FF9500) rim light catches the polished metal edges, red (#D8000F) "
    "accent from below. Extreme shallow depth of field, only the bell's edge is sharp. "
    "Slight camera drift, no cuts. Heavy grain, 35mm anamorphic flare when the light "
    "catches the surface. Dark, hypnotic, aggressive phonk music-video aesthetic. "
    "Camera slow-orbit around the bell. No dialogue. No music. No sound effects. Silent."
)


@dataclass
class Shot:
    slug: str
    prompt: str
    seed: int


SHOTS = [
    Shot("03g1-terminal-spawn", TERMINAL_PROMPT, 4711),
    Shot("04g1-cowbell-macro", COWBELL_PROMPT, 4712),
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def b64decode(b64_encoded_string: str) -> bytes:
    return base64.b64decode(b64_encoded_string.encode("utf-8"))


def strip_audio(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-an", "-c:v", "copy", str(dst)],
        check=True,
        capture_output=True,
    )


def append_manifest(row: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a") as f:
        f.write(json.dumps(row) + "\n")


def generate_shot(
    client: "genai.Client",
    shot: Shot,
    aspect_ratio: str,
    number_of_videos: int,
    budget_left: int,
) -> tuple[list[Path], int]:
    """Return (list of written mp4 paths, budget_used)."""
    if budget_left <= 0:
        print(f"  ! budget exhausted, skipping {shot.slug}", flush=True)
        return [], 0

    n = min(number_of_videos, budget_left)
    print(f"→ {shot.slug} (seed={shot.seed}, n={n}, aspect={aspect_ratio})", flush=True)

    source = types.GenerateVideosSource(prompt=shot.prompt)
    # Veo 2 supports duration 5-8s, aspect 9:16/16:9, no generate_audio flag.
    config = types.GenerateVideosConfig(
        aspect_ratio=aspect_ratio,
        number_of_videos=n,
        duration_seconds=8,
        person_generation="allow_all",
        resolution="720p",
        seed=shot.seed,
    )

    t0 = time.time()
    operation = client.models.generate_videos(
        model="veo-2.0-generate-001", source=source, config=config
    )
    while not operation.done:
        print(f"    polling... {int(time.time()-t0)}s", flush=True)
        time.sleep(10)
        operation = client.operations.get(operation)

    response = operation.result
    if not response or not response.generated_videos:
        print(f"  ! no videos returned for {shot.slug}", flush=True)
        append_manifest(
            {
                "slug": shot.slug,
                "seed": shot.seed,
                "aspect_ratio": aspect_ratio,
                "prompt_sha256": sha256_str(shot.prompt),
                "status": "empty",
                "ts": int(time.time()),
            }
        )
        return [], n

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, gv in enumerate(response.generated_videos):
        raw_path = OUT_DIR / f"{shot.slug}-take{i+1}.raw.mp4"
        out_path = OUT_DIR / f"{shot.slug}-take{i+1}.mp4"
        source_kind = None
        video = gv.video
        if video is None:
            print(f"  ! take{i+1}: empty video", flush=True)
            continue

        # Prefer uri when large; otherwise inline bytes.
        vuri = getattr(video, "uri", None)
        vbytes = getattr(video, "video_bytes", None)

        if vuri:
            source_kind = "uri"
            # SDK helper preferred; fall back to raw HTTP if needed.
            try:
                client.files.download(file=video)  # may not apply on vertex; safe attempt
            except Exception:
                pass
            try:
                video.save(str(raw_path))
                source_kind = "uri_save"
            except Exception:
                # Manual download via authorized session:
                import google.auth
                import google.auth.transport.requests as gart
                creds, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                auth_req = gart.Request()
                creds.refresh(auth_req)
                import requests as _rq

                r = _rq.get(
                    vuri,
                    headers={"Authorization": f"Bearer {creds.token}"},
                    timeout=600,
                )
                r.raise_for_status()
                raw_path.write_bytes(r.content)
                source_kind = "uri_download"
        elif vbytes:
            source_kind = "inline_b64"
            if isinstance(vbytes, (bytes, bytearray)):
                raw_path.write_bytes(bytes(vbytes))
            else:
                raw_path.write_bytes(b64decode(vbytes))
        else:
            print(f"  ! take{i+1}: neither uri nor bytes present", flush=True)
            continue

        # Strip audio (safety net; generate_audio was False).
        try:
            strip_audio(raw_path, out_path)
            raw_path.unlink(missing_ok=True)
        except subprocess.CalledProcessError as e:
            print(f"  ! ffmpeg strip failed on {raw_path}: {e.stderr!r}", flush=True)
            # Keep raw as out fallback
            raw_path.rename(out_path)

        row = {
            "slug": shot.slug,
            "take": i + 1,
            "seed": shot.seed,
            "aspect_ratio": aspect_ratio,
            "prompt_sha256": sha256_str(shot.prompt),
            "file": str(out_path.relative_to(REPO_ROOT)),
            "file_sha256": sha256_file(out_path),
            "size_bytes": out_path.stat().st_size,
            "source_kind": source_kind,
            "elapsed_s": int(time.time() - t0),
            "ts": int(time.time()),
        }
        append_manifest(row)
        print(f"  ✓ take{i+1}: {out_path.name} ({row['size_bytes']//1024} KB, {source_kind})", flush=True)
        written.append(out_path)

    return written, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="sharp-leaf-451416-r4")
    ap.add_argument("--location", default="us-central1")
    ap.add_argument("--only", choices=["03g1", "04g1"], default=None)
    ap.add_argument("--aspect", default="9:16", choices=["9:16", "16:9"])
    ap.add_argument("--candidates", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    shots = SHOTS
    if args.only == "03g1":
        shots = [SHOTS[0]]
    elif args.only == "04g1":
        shots = [SHOTS[1]]

    if args.dry_run:
        for s in shots:
            print(f"[dry-run] would generate {s.slug} seed={s.seed} @ {args.aspect}")
            print(f"  prompt: {s.prompt[:120]}...")
        return 0

    print(f"Vertex Veo 3 Fast · project={args.project} location={args.location}")
    client = genai.Client(vertexai=True, project=args.project, location=args.location)

    budget = MAX_CLIPS
    for shot in shots:
        aspect = args.aspect
        try:
            _, used = generate_shot(
                client, shot, aspect, args.candidates, budget
            )
            budget -= used
        except Exception as e:
            msg = str(e)
            print(f"  ! {shot.slug} failed on {aspect}: {msg}", flush=True)
            # Portrait fallback: try 16:9 once
            if aspect == "9:16" and (
                "aspect" in msg.lower()
                or "9:16" in msg
                or "invalid" in msg.lower()
            ):
                print(f"  ↺ retrying {shot.slug} at 16:9", flush=True)
                try:
                    _, used = generate_shot(
                        client, shot, "16:9", args.candidates, budget
                    )
                    budget -= used
                except Exception as e2:
                    print(f"  !! {shot.slug} 16:9 fallback also failed: {e2}", flush=True)
                    append_manifest(
                        {
                            "slug": shot.slug,
                            "seed": shot.seed,
                            "status": "failed",
                            "error": str(e2),
                            "ts": int(time.time()),
                        }
                    )

    print(f"\nDone. Manifest: {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
