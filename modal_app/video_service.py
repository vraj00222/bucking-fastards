# DropTable Records video service — generates music videos from track metadata
#
# Uses CogVideoX-5B (THUDM) to generate short cinematic clips driven by
# lyric-derived scene prompts, then concatenates them into a single MP4
# with the track audio mixed in.
#
# Request body:
#   {
#     "caption":    str,   # music style / mood description (same as audio caption)
#     "lyrics":     str,   # full lyrics with [verse]/[chorus] markers
#     "song_title": str,   # e.g. "npm install Commander"
#     "artist":     str,   # e.g. "Comma-nd.R"
#     "style":      str,   # one of the 13 presets ("phonk", "hyperpop", …)
#     "audio_b64":  str,   # optional — base64 MP3 to mix into the final video
#     "duration":   float, # optional — target video duration in seconds (default 60.0)
#     "num_scenes": int,   # optional — how many clips to generate (default 4)
#   }
#
# Response:
#   { "video_b64": str }   # base64-encoded MP4

from __future__ import annotations

import base64
import re
import textwrap
from pathlib import Path
from typing import Optional

import modal

# ---------------------------------------------------------------------------
# Image — CUDA + CogVideoX + diffusers
# ---------------------------------------------------------------------------
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04", add_python="3.11"
    )
    .apt_install("git", "ffmpeg")
    .uv_pip_install(
        "torch==2.4.0",
        "torchvision==0.19.0",
        "diffusers>=0.32.0",
        "transformers>=4.46.0",
        "accelerate>=0.34.0",
        "sentencepiece",
        "imageio[ffmpeg]",
        "opencv-python-headless",
        "Pillow",
        "hf_transfer==0.1.9",
        extra_index_url="https://download.pytorch.org/whl/cu124",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .entrypoint([])
)

model_cache = modal.Volume.from_name("cogvideox-model-cache", create_if_missing=True)
MODEL_CACHE_DIR = "/model-cache"

web_image = modal.Image.debian_slim(python_version="3.11").uv_pip_install(
    "fastapi[standard]==0.115.4"
)

app = modal.App("droptable-video")

# ---------------------------------------------------------------------------
# Style → visual palette mapping
# ---------------------------------------------------------------------------
STYLE_PALETTES: dict[str, str] = {
    "phonk":      "dark memphis night, neon red and amber, CRT scanlines, drift car smoke, aggressive",
    "hyperpop":   "glitchy digital, pastel acid colors, pixel shatter, chaotic energy, kawaii meets industrial",
    "emo":        "moody blue-green tones, rain-soaked streets, dramatic silhouettes, lens flare, raw emotion",
    "edm":        "laser beams, festival crowd, strobing lights, massive speaker stacks, euphoric",
    "shanty":     "roiling ocean, wooden ship deck, golden lantern light, dramatic storm clouds, epic",
    "bollywood":  "rich jewel tones, ornate architecture, swirling fabrics, vibrant celebration, cinematic",
    "drill":      "gritty urban nightscape, blue-grey concrete, hoodie silhouettes, slow-mo rain, tense",
    "boyband":    "soft studio light, confetti, matching outfits, dramatic emotional close-ups, stadium",
    "citypop":    "80s Tokyo neon, cassette tape, retro cityscape, pastel dusk, synthwave glow",
    "country":    "golden hour fields, pickup truck, dusty road, honest warmth, wide open sky",
    "boombap":    "black-and-white NYC rooftop, vinyl spinning, classic b-boy, warm grain, cinematic",
    "techrap":    "server racks glowing blue, terminal text cascading, hacker aesthetic, dark silicon vibes",
    "gfunk":      "lowrider hydraulics, Los Angeles dusk, palm trees, purple-and-gold palette, smooth",
}

# ---------------------------------------------------------------------------
# Scene-prompt builder
# ---------------------------------------------------------------------------

def _extract_sections(lyrics: str) -> list[tuple[str, str]]:
    """Return list of (section_type, text) from bracketed lyrics."""
    pattern = re.compile(r"\[(\w+)\](.*?)(?=\[|\Z)", re.DOTALL)
    sections = [(m.group(1).lower(), m.group(2).strip()) for m in pattern.finditer(lyrics)]
    return sections if sections else [("verse", lyrics.strip())]


def build_scene_prompts(
    caption: str,
    lyrics: str,
    song_title: str,
    artist: str,
    style: str,
    num_scenes: int = 4,
) -> list[str]:
    """
    Convert caption + lyrics into `num_scenes` cinematic shot prompts for
    CogVideoX.  Each prompt = palette + section-specific action + quality tags.
    """
    palette = STYLE_PALETTES.get(style, "cinematic music video, dramatic lighting")
    sections = _extract_sections(lyrics)

    # Pick evenly-spaced sections to represent the video
    step = max(1, len(sections) // num_scenes)
    chosen = sections[::step][:num_scenes]
    # Pad if fewer than num_scenes
    while len(chosen) < num_scenes:
        chosen.append(chosen[-1])

    prompts = []
    for sec_type, text in chosen:
        # Extract the first two lines as lyric snippet
        lines = [l.strip() for l in text.split("\n") if l.strip()][:2]
        snippet = " / ".join(lines) if lines else song_title

        # Trim snippet to avoid prompt overload
        snippet = textwrap.shorten(snippet, width=120, placeholder="…")

        if sec_type in ("chorus", "hook"):
            shot = (
                f"Wide cinematic shot, crowd energy, peak moment. "
                f"Visual interpretation of: '{snippet}'. "
                f"{palette}. "
                f"Music video aesthetic, high production value, 4K, dramatic."
            )
        elif sec_type in ("bridge", "breakdown"):
            shot = (
                f"Intimate close-up, tension building, slow motion. "
                f"Visual metaphor for: '{snippet}'. "
                f"{palette}. "
                f"Cinematic, moody, music video, shallow depth of field."
            )
        elif sec_type == "outro":
            shot = (
                f"Pull-back reveal shot, emotional resolution. "
                f"'{song_title}' by {artist} — closing image. "
                f"{palette}. "
                f"Cinematic, wide, music video ending, high production value."
            )
        else:  # verse, intro, pre-chorus
            shot = (
                f"Dynamic tracking shot, storytelling moment. "
                f"Visual narrative: '{snippet}'. "
                f"{palette}. "
                f"Music video, cinematic lighting, 4K, vivid."
            )
        prompts.append(shot)

    return prompts


# ---------------------------------------------------------------------------
# CogVideoX inference class
# ---------------------------------------------------------------------------

MODEL_ID = "THUDM/CogVideoX-5b"
# CogVideoX-5b generates 49 frames @ 8fps → ~6 seconds per clip.
# We stack clips to hit the target duration.

@app.cls(
    gpu="a100",
    image=image,
    volumes={MODEL_CACHE_DIR: model_cache},
    timeout=900,
    memory=32768,
)
class VideoGenerator:
    @modal.enter()
    def load_model(self):
        import torch
        from diffusers import CogVideoXPipeline
        from diffusers.utils import export_to_video  # noqa: F401 — imported for side-effects

        print("Loading CogVideoX-5b …", flush=True)
        self.pipe = CogVideoXPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
            cache_dir=MODEL_CACHE_DIR,
        )
        self.pipe.enable_model_cpu_offload()
        self.pipe.vae.enable_slicing()
        self.pipe.vae.enable_tiling()
        print("CogVideoX ready.", flush=True)

    @modal.method()
    def generate_clip(
        self,
        prompt: str,
        num_frames: int = 49,
        fps: int = 8,
        guidance_scale: float = 6.0,
        seed: int = 42,
    ) -> bytes:
        """
        Generate a single video clip from a prompt.
        Returns raw MP4 bytes.
        """
        import tempfile

        import torch
        from diffusers.utils import export_to_video

        generator = torch.Generator("cuda").manual_seed(seed)
        result = self.pipe(
            prompt=prompt,
            num_videos_per_prompt=1,
            num_inference_steps=50,
            num_frames=num_frames,
            guidance_scale=guidance_scale,
            generator=generator,
        )
        frames = result.frames[0]  # list of PIL images

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            out_path = tmp.name

        export_to_video(frames, out_path, fps=fps)
        data = Path(out_path).read_bytes()
        Path(out_path).unlink(missing_ok=True)
        return data


# ---------------------------------------------------------------------------
# FastAPI endpoint
# ---------------------------------------------------------------------------

@app.function(image=web_image, timeout=1200)
@modal.fastapi_endpoint(method="POST")
def generate(body: dict):
    """
    POST body keys:
        caption, lyrics, song_title, artist, style,
        audio_b64 (optional), duration (optional), num_scenes (optional)
    """
    import subprocess
    import tempfile

    caption = body["caption"]
    lyrics = body["lyrics"]
    song_title = body.get("song_title", "Untitled")
    artist = body.get("artist", "DropTable Records")
    style = body.get("style", "phonk")
    audio_b64: Optional[str] = body.get("audio_b64")
    duration: float = float(body.get("duration", 60.0))
    num_scenes: int = int(body.get("num_scenes", 4))

    # Build scene prompts
    prompts = build_scene_prompts(
        caption, lyrics, song_title, artist, style, num_scenes=num_scenes
    )

    # Clip duration for each scene: CogVideoX-5b generates ~6s @ 49 frames / 8fps
    CLIP_FRAMES = 49
    CLIP_FPS = 8

    gen = VideoGenerator()

    # Generate all clips in parallel via Modal's .map
    args = [
        (prompt, CLIP_FRAMES, CLIP_FPS, 6.0, seed)
        for seed, prompt in enumerate(prompts, start=1)
    ]
    clip_bytes_list: list[bytes] = list(gen.generate_clip.starmap(args))

    # Write clips to temp dir and concatenate with ffmpeg
    with tempfile.TemporaryDirectory() as tmpdir:
        clip_paths: list[Path] = []
        for i, clip_bytes in enumerate(clip_bytes_list):
            p = Path(tmpdir) / f"clip_{i:02d}.mp4"
            p.write_bytes(clip_bytes)
            clip_paths.append(p)

        # Build ffmpeg concat list
        concat_list = Path(tmpdir) / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p}'" for p in clip_paths)
        )

        silent_mp4 = Path(tmpdir) / "silent.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c", "copy",
                str(silent_mp4),
            ],
            check=True,
            capture_output=True,
        )

        final_mp4 = Path(tmpdir) / "final.mp4"

        if audio_b64:
            # Mix in the track audio
            audio_bytes = base64.b64decode(audio_b64)
            audio_path = Path(tmpdir) / "track.mp3"
            audio_path.write_bytes(audio_bytes)

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(silent_mp4),
                    "-i", str(audio_path),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    str(final_mp4),
                ],
                check=True,
                capture_output=True,
            )
        else:
            final_mp4 = silent_mp4

        video_bytes = final_mp4.read_bytes()

    return {"video_b64": base64.b64encode(video_bytes).decode()}


# ---------------------------------------------------------------------------
# Local test entrypoint
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main(
    caption: str = "aggressive phonk, memphis rap, distorted 808 cowbell, dark, fast",
    lyrics: str = "[verse]\ngit push at 3am\n[chorus]\nforce push, no tests, no fear",
    song_title: str = "3AM Force Push",
    artist: str = "DropTable Records",
    style: str = "phonk",
    num_scenes: int = 4,
    out: str = "/tmp/droptable_test.mp4",
):
    gen = VideoGenerator()
    prompts = build_scene_prompts(caption, lyrics, song_title, artist, style, num_scenes)
    print(f"Generated {len(prompts)} scene prompts:")
    for i, p in enumerate(prompts, 1):
        print(f"  Scene {i}: {p[:100]}…")

    args = [(p, 49, 8, 6.0, seed) for seed, p in enumerate(prompts, 1)]
    clips = list(gen.generate_clip.starmap(args))
    print(f"Got {len(clips)} clips, writing to {out} …")

    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        clip_paths = []
        for i, clip_bytes in enumerate(clips):
            p = Path(tmpdir) / f"clip_{i:02d}.mp4"
            p.write_bytes(clip_bytes)
            clip_paths.append(p)

        concat_list = Path(tmpdir) / "concat.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in clip_paths))

        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(concat_list), "-c", "copy", out],
            check=True,
        )

    print(f"Saved {Path(out).stat().st_size // 1024} KB → {out}")
