#!/usr/bin/env python3
"""footage_backends.py — pluggable AI-footage bed generators for mp3_to_video.

Three backends:
    NoneBackend        — no-op (default; kinetic type only)
    VeoBackend         — Google Vertex AI Veo 2 (9:16 native, ~8s max)
    CogVideoXBackend   — Modal-hosted CogVideoX-5B (~6s max, 720x480 landscape)

All backends implement generate_clip(prompt, slug, seed, duration_s, out_path).
The caller composes a small library on top:

    - `assign_footage_to_plan(plan, backend, n)` picks the top-N hookiest frames
      (deterministic scorer), then calls Claude for a shot prompt per frame and
      attaches `frames[i].footage = {backend, prompt, seed, duration_s, path}`.

    - `generate_footage_for_plan(plan, project_dir, backend, ...)` walks the
      selected frames, calls backend.generate_clip in parallel, and writes MP4s
      to project/assets/footage/<frame_id>.mp4 plus manifest.jsonl.

Failure policy (non-fatal per user directive #7): if a clip generation fails,
we DROP the footage assignment from that frame and continue. The frame falls
back to pure-type rendering.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
COGVIDEOX_ENDPOINT = "https://vaibhavgeek--droptable-video-generate.modal.run"
COGVIDEOX_TIMEOUT_S = 1200  # 20 min per clip (Modal A100 cold start)


# ─────────────────────────────────────────────────────────────────────────────
# Small utilities
# ─────────────────────────────────────────────────────────────────────────────


def _log(msg: str) -> None:
    print(f"[footage] {msg}", flush=True)


def _sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _strip_audio(src: Path, dst: Path) -> None:
    """ffmpeg -an belt-and-suspenders. If it fails, rename src → dst as fallback."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-an", "-c:v", "copy", str(dst)],
            check=True,
            capture_output=True,
        )
        src.unlink(missing_ok=True)
    except subprocess.CalledProcessError:
        src.rename(dst)


def _append_manifest(project_dir: Path, row: dict) -> None:
    manifest = project_dir / "assets" / "footage" / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("a") as f:
        f.write(json.dumps(row) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Backend protocol + implementations
# ─────────────────────────────────────────────────────────────────────────────


class FootageBackend(Protocol):
    name: str
    max_clip_seconds: float

    def generate_clip(
        self,
        prompt: str,
        slug: str,
        seed: int,
        duration_s: float,
        out_path: Path,
        aspect: str = "9:16",
    ) -> Path: ...


class NoneBackend:
    name = "none"
    max_clip_seconds = 0.0

    def generate_clip(self, *_args, **_kwargs) -> Path:
        raise RuntimeError("NoneBackend does not generate clips; do not call.")


class VeoBackend:
    """Google Vertex AI Veo 2. 5-8s clips, 9:16 native, 720p."""

    name = "veo"
    max_clip_seconds = 8.0

    def __init__(self, project: Optional[str] = None, location: str = "us-central1") -> None:
        self.project = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or "sharp-leaf-451416-r4"
        self.location = location
        try:
            from google import genai  # noqa: F401
            from google.genai import types  # noqa: F401
        except ImportError:
            raise RuntimeError(
                "VeoBackend requires: pip install google-genai"
            )
        from google import genai as _genai
        self._genai = _genai
        self._client = _genai.Client(vertexai=True, project=self.project, location=self.location)

    def generate_clip(
        self,
        prompt: str,
        slug: str,
        seed: int,
        duration_s: float,
        out_path: Path,
        aspect: str = "9:16",
    ) -> Path:
        from google.genai import types

        dur = int(max(5, min(8, round(duration_s))))
        out_path.parent.mkdir(parents=True, exist_ok=True)

        def _once(_aspect: str) -> Path:
            _log(f"veo → {slug} (seed={seed}, dur={dur}s, aspect={_aspect})")
            source = types.GenerateVideosSource(prompt=prompt)
            config = types.GenerateVideosConfig(
                aspect_ratio=_aspect,
                number_of_videos=1,
                duration_seconds=dur,
                person_generation="allow_all",
                resolution="720p",
                seed=seed,
            )
            t0 = time.time()
            op = self._client.models.generate_videos(
                model="veo-2.0-generate-001", source=source, config=config
            )
            while not op.done:
                _log(f"  polling veo {slug}... {int(time.time()-t0)}s")
                time.sleep(10)
                op = self._client.operations.get(op)

            resp = op.result
            if not resp or not resp.generated_videos:
                raise RuntimeError(f"veo returned no videos for {slug}")

            gv = resp.generated_videos[0]
            video = gv.video
            if video is None:
                raise RuntimeError(f"veo returned empty video for {slug}")

            raw_path = out_path.with_suffix(".raw.mp4")
            vuri = getattr(video, "uri", None)
            vbytes = getattr(video, "video_bytes", None)

            if vuri:
                try:
                    video.save(str(raw_path))
                except Exception:
                    import google.auth
                    import google.auth.transport.requests as gart
                    import requests as _rq
                    creds, _ = google.auth.default(
                        scopes=["https://www.googleapis.com/auth/cloud-platform"]
                    )
                    creds.refresh(gart.Request())
                    r = _rq.get(
                        vuri,
                        headers={"Authorization": f"Bearer {creds.token}"},
                        timeout=600,
                    )
                    r.raise_for_status()
                    raw_path.write_bytes(r.content)
            elif vbytes:
                if isinstance(vbytes, (bytes, bytearray)):
                    raw_path.write_bytes(bytes(vbytes))
                else:
                    raw_path.write_bytes(base64.b64decode(vbytes))
            else:
                raise RuntimeError(f"veo returned neither uri nor bytes for {slug}")

            _strip_audio(raw_path, out_path)
            return out_path

        try:
            return _once(aspect)
        except Exception as e:
            msg = str(e)
            if aspect == "9:16" and (
                "aspect" in msg.lower() or "9:16" in msg or "invalid" in msg.lower()
            ):
                _log(f"  ↺ retrying {slug} at 16:9")
                return _once("16:9")
            # rate limit — one polite retry
            if "resource_exhausted" in msg.lower() or "429" in msg:
                _log(f"  ⏳ rate-limited, sleeping 60s then retrying {slug}")
                time.sleep(60)
                return _once(aspect)
            raise


class CogVideoXBackend:
    """CogVideoX-5B via Modal endpoint. ~6s per clip (49 frames @ 8fps), 720x480."""

    name = "cogvideox"
    max_clip_seconds = 6.0

    def __init__(self, endpoint: str = COGVIDEOX_ENDPOINT, timeout_s: float = COGVIDEOX_TIMEOUT_S) -> None:
        self.endpoint = endpoint
        self.timeout_s = timeout_s
        try:
            import requests  # noqa: F401
        except ImportError:
            raise RuntimeError("CogVideoXBackend requires: pip install requests")

    def generate_clip(
        self,
        prompt: str,
        slug: str,
        seed: int,  # accepted for interface parity; endpoint doesn't expose it
        duration_s: float,
        out_path: Path,
        aspect: str = "9:16",  # accepted for parity; endpoint is 720x480 landscape
    ) -> Path:
        import requests

        # Reuse the existing /generate endpoint with num_scenes=1 → single ~6s clip.
        # We stuff the shot prompt into `caption` and echo it into `lyrics` so the
        # server-side prompt builder has enough signal; style is a neutral default.
        body = {
            "caption": prompt,
            "lyrics": f"[scene]\n{prompt}\n",
            "song_title": slug,
            "artist": "hyperframes",
            "style": "phonk",
            "num_scenes": 1,
            "duration": min(duration_s, self.max_clip_seconds),
            # no audio_b64 → server keeps silent output
        }

        _log(f"cogvideox → {slug} (dur={body['duration']:.1f}s, endpoint={self.endpoint})")
        t0 = time.time()
        r = requests.post(self.endpoint, json=body, timeout=self.timeout_s)
        r.raise_for_status()
        payload = r.json()
        if "video_b64" not in payload:
            raise RuntimeError(f"cogvideox response missing video_b64: {list(payload.keys())}")

        raw_path = out_path.with_suffix(".raw.mp4")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(base64.b64decode(payload["video_b64"]))
        _strip_audio(raw_path, out_path)
        _log(f"  ✓ cogvideox {slug}: {out_path.stat().st_size//1024} KB ({int(time.time()-t0)}s)")
        return out_path


def get_backend(name: str, gcp_project: Optional[str] = None) -> FootageBackend:
    if name == "none":
        return NoneBackend()
    if name == "veo":
        return VeoBackend(project=gcp_project)
    if name == "cogvideox":
        return CogVideoXBackend()
    raise ValueError(f"unknown backend: {name}")


# ─────────────────────────────────────────────────────────────────────────────
# Frame selection (deterministic scorer)
# ─────────────────────────────────────────────────────────────────────────────


HOOKY_MOODS = {"hype", "aggressive", "cinematic", "glitch", "tense"}


def score_frame_hookyness(frame: dict) -> float:
    mood = frame.get("mood") or []
    pacing = frame.get("pacing", "")
    feel = (frame.get("feel") or "").lower()
    visual = (frame.get("visual") or "").lower()

    score = 0.0
    for m in mood:
        if m in HOOKY_MOODS:
            score += 2.0
    if pacing == "beat_cut":
        score += 1.0
    # crude "chorus / drop / hook" bonus from feel/visual text
    for kw in ("chorus", "drop", "hook", "climax", "surge"):
        if kw in feel or kw in visual:
            score += 3.0
            break
    # duration bonus — prefer frames long enough to actually host a 5-6s bed
    dur = frame.get("span_sec", [0, 0])[1] - frame.get("span_sec", [0, 0])[0]
    if dur >= 5.0:
        score += 1.5
    elif dur < 3.0:
        score -= 2.0
    return score


def pick_top_frames(plan: dict, n: int) -> list[dict]:
    ranked = sorted(plan["frames"], key=score_frame_hookyness, reverse=True)
    picked = ranked[: max(0, n)]
    # Preserve original ordering for downstream determinism
    picked_ids = {f["id"] for f in picked}
    return [f for f in plan["frames"] if f["id"] in picked_ids]


# ─────────────────────────────────────────────────────────────────────────────
# Shot-prompt planner (small Claude call)
# ─────────────────────────────────────────────────────────────────────────────


SHOT_SYSTEM = """You are a music-video shot designer.

You receive: song brand palette + one frame's context (mood, feel, visual note,
lyric_line, hero_words). Return ONE JSON object with a single shot prompt for a
generative video model (Veo 2 or CogVideoX-5B).

RULES for the prompt:
- Single continuous shot, NO scene cuts, NO dialogue, NO music, NO sound effects. Silent.
- 5-8 seconds worth of visible motion.
- No text overlays inside the generated footage (text is added later by the caller).
- Concrete camera direction (dolly-in, slow orbit, static macro, tilt-down, etc).
- Concrete subject (an object, a texture, a scene) — NOT a person unless the mood demands it.
- Palette-consistent lighting; call out 1-2 hex colors from the brand palette.
- Film-grade language: "35mm anamorphic", "shallow depth of field", "heavy grain", "sodium-vapor light", etc.
- 9:16 portrait framing.

Return ONLY JSON of shape:
  { "prompt": "...", "seed": 4711 }
Seed is a stable integer between 1000 and 9999.
"""


def plan_shot_prompts(
    plan: dict,
    selected_ids: list[str],
    model: str,
) -> dict[str, dict]:
    """Return { frame_id: {prompt, seed} } via one Claude call per selected frame."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("plan_shot_prompts requires anthropic")

    client = anthropic.Anthropic()
    brand = plan["brand"]
    frames_by_id = {f["id"]: f for f in plan["frames"]}
    out: dict[str, dict] = {}

    def _one(fid: str) -> tuple[str, dict]:
        f = frames_by_id[fid]
        user = textwrap.dedent(
            f"""
            BRAND PALETTE: {json.dumps(brand.get('palette', {}))}
            FONT STACK: {brand.get('font_stack', '')}

            FRAME: {fid}
            MOOD: {', '.join(f.get('mood') or [])}
            PACING: {f.get('pacing', '')}
            FEEL: {f.get('feel', '')}
            LYRIC LINE: "{f.get('lyric_line', '')}"
            HERO WORDS: {json.dumps(f.get('hero_words') or [])}
            VISUAL: {f.get('visual', '')}

            Return the JSON now.
            """
        ).strip()
        resp = client.messages.create(
            model=model,
            max_tokens=800,
            system=SHOT_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        text = resp.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.lstrip().startswith("json"):
                text = text.lstrip()[4:]
            text = text.strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        parsed = json.loads(text)
        return fid, {"prompt": parsed["prompt"], "seed": int(parsed.get("seed", 4711))}

    with ThreadPoolExecutor(max_workers=min(4, len(selected_ids))) as ex:
        futs = {ex.submit(_one, fid): fid for fid in selected_ids}
        for fut in as_completed(futs):
            fid, entry = fut.result()
            out[fid] = entry
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Public API for mp3_to_video.py
# ─────────────────────────────────────────────────────────────────────────────


def assign_footage_to_plan(
    plan: dict,
    backend_name: str,
    n: int,
    model: str,
) -> None:
    """Attach `footage` dicts to the top-N frames in `plan` in place.

    Each attached entry:
        { "backend": name, "prompt": str, "seed": int, "duration_s": float, "path": str }
    """
    if backend_name == "none" or n <= 0:
        return
    backend = get_backend(backend_name)
    picked = pick_top_frames(plan, n)
    if not picked:
        _log("no frames selected for footage; skipping")
        return
    _log(f"selected {len(picked)} frame(s) for footage: {[f['id'] for f in picked]}")

    shot_map = plan_shot_prompts(plan, [f["id"] for f in picked], model)

    for f in picked:
        entry = shot_map.get(f["id"])
        if not entry:
            continue
        span = f["span_sec"]
        frame_dur = span[1] - span[0]
        clip_dur = min(backend.max_clip_seconds, frame_dur)
        f["footage"] = {
            "backend": backend.name,
            "prompt": entry["prompt"],
            "seed": entry["seed"],
            "duration_s": clip_dur,
            "path": f"assets/footage/{f['id']}.mp4",
        }
        _log(f"  {f['id']}: seed={entry['seed']} clip_dur={clip_dur:.2f}s")


def generate_footage_for_plan(
    plan: dict,
    project_dir: Path,
    backend_name: str,
    gcp_project: Optional[str] = None,
) -> None:
    """Walk plan frames that have `footage`, generate each clip in parallel, and
    write to project_dir/assets/footage/<frame_id>.mp4.

    Failures are non-fatal per policy: the frame's `footage` key is deleted so
    the frame falls back to pure-type rendering.
    """
    if backend_name == "none":
        return
    frames_with_footage = [f for f in plan["frames"] if f.get("footage")]
    if not frames_with_footage:
        _log("no frames have footage assignments; skipping generation")
        return

    backend = get_backend(backend_name, gcp_project=gcp_project)
    out_dir = project_dir / "assets" / "footage"
    out_dir.mkdir(parents=True, exist_ok=True)
    _log(f"generating {len(frames_with_footage)} clip(s) via {backend.name}…")

    def _one(f: dict) -> tuple[str, Optional[Path], Optional[str]]:
        fid = f["id"]
        footage = f["footage"]
        out_path = project_dir / footage["path"]
        try:
            backend.generate_clip(
                prompt=footage["prompt"],
                slug=fid,
                seed=int(footage["seed"]),
                duration_s=float(footage["duration_s"]),
                out_path=out_path,
                aspect="9:16",
            )
            row = {
                "slug": fid,
                "backend": backend.name,
                "seed": int(footage["seed"]),
                "duration_s": float(footage["duration_s"]),
                "prompt_sha256": _sha256_str(footage["prompt"]),
                "file": str(out_path.relative_to(REPO_ROOT)) if out_path.is_relative_to(REPO_ROOT) else str(out_path),
                "file_sha256": _sha256_file(out_path),
                "size_bytes": out_path.stat().st_size,
                "ts": int(time.time()),
            }
            _append_manifest(project_dir, row)
            return fid, out_path, None
        except Exception as e:
            return fid, None, str(e)

    max_workers = 2 if backend.name == "veo" else 1  # cogvideox is single-A100, serialize
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_one, f): f for f in frames_with_footage}
        for fut in as_completed(futs):
            fid, path, err = fut.result()
            if err:
                _log(f"  ! {fid} footage failed: {err} — dropping footage bed for this frame")
                # Drop assignment so the frame worker doesn't try to mount a missing file
                for f in plan["frames"]:
                    if f["id"] == fid and "footage" in f:
                        del f["footage"]
                        _append_manifest(
                            project_dir,
                            {"slug": fid, "backend": backend.name, "status": "failed", "error": err, "ts": int(time.time())},
                        )
                        break
            else:
                _log(f"  ✓ {fid} → {path.relative_to(project_dir)}")


if __name__ == "__main__":
    # Smoke: `python3 pipeline/footage_backends.py cogvideox|veo|none`
    if len(sys.argv) < 2:
        print("usage: footage_backends.py <none|veo|cogvideox>")
        sys.exit(2)
    name = sys.argv[1]
    backend = get_backend(name)
    print(f"loaded backend: {backend.name} (max_clip={backend.max_clip_seconds}s)")
