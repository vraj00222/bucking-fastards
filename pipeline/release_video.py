"""Render a local, original lyric video for a generated DropTable track.

The renderer intentionally uses only generated release material and the
label-owned illustrated A&R character. It never downloads or reuses artist
footage. Pillow pre-renders text overlays so the renderer works with lean
ffmpeg builds that omit libass and libfreetype.
"""
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).parent.parent
CHARACTER_ART = ROOT / "web" / "public" / "art" / "long.jpg"


def lyric_lines(lyrics):
    """Return displayable lyric lines; section tags are narration, not captions."""
    return [line.strip() for line in lyrics.splitlines() if line.strip() and not line.lstrip().startswith("[")]


def lyric_cues(lyrics, duration):
    """Assign lyric lines to track windows with a little intro/outro breathing room."""
    lines = lyric_lines(lyrics)
    start, end = 2.0, max(3.2, float(duration) - 2.2)
    slot = max(1.4, (end - start) / len(lines)) if lines else 1.4
    return [(line, start + index * slot, min(end, start + index * slot + slot + 0.25)) for index, line in enumerate(lines)]


def _font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    words, rows, current = text.split(), [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), trial, font=font)[2] > max_width:
            rows.append(current)
            current = word
        else:
            current = trial
    if current:
        rows.append(current)
    return rows or [text]


def _panel_overlay(song_title, artist_name, repo, path):
    canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((54, 52, 716, 294), fill=(23, 33, 61, 210), outline=(195, 148, 29, 235), width=2)
    draw.text((82, 82), "DROP TABLE RECORDS // SOURCE SESSION", font=_font(18), fill=(195, 148, 29, 255))
    draw.text((80, 118), song_title.upper()[:34], font=_font(46, bold=True), fill=(246, 242, 232, 255))
    draw.text((82, 180), artist_name.upper()[:48], font=_font(20), fill=(213, 208, 196, 255))
    draw.text((82, 238), f"> {repo}"[:62], font=_font(22), fill=(155, 177, 231, 255))
    draw.text((82, 266), "PR / ARCHITECTURE / REVIEW IN SESSION", font=_font(16), fill=(213, 208, 196, 255))
    canvas.save(path)


def _caption_overlay(text, path):
    canvas = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = _font(42, bold=True)
    rows = _wrap(draw, text, font, 990)[:3]
    line_height = 53
    max_width = max(draw.textbbox((0, 0), row, font=font)[2] for row in rows)
    height = len(rows) * line_height + 36
    x, y = 80, 510 - height
    draw.rounded_rectangle((x - 24, y - 16, x + max_width + 24, y + height - 5), radius=8, fill=(23, 33, 61, 226), outline=(195, 148, 29, 230), width=2)
    for index, row in enumerate(rows):
        draw.text((x, y + index * line_height), row, font=font, fill=(246, 242, 232, 255))
    canvas.save(path)


def _duration(audio_path):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return max(1.0, float(probe.stdout.strip()))


def render_release_video(audio_path, lyrics, song_title, artist_name, repo, output_path):
    """Burn source-session framing, cross-faded lyric captions, and waveform into MP4."""
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required for local lyric-video rendering.")
    if not CHARACTER_ART.exists():
        raise RuntimeError(f"Missing label character art: {CHARACTER_ART}")

    audio_path = Path(audio_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration = _duration(audio_path)
    panel_path = output_path.with_name(f"{output_path.stem}-panel.png")
    _panel_overlay(song_title, artist_name, repo, panel_path)
    cues = lyric_cues(lyrics, duration)
    caption_paths = []
    for index, (line, _, _) in enumerate(cues):
        caption_path = output_path.with_name(f"{output_path.stem}-caption-{index:02d}.png")
        _caption_overlay(line, caption_path)
        caption_paths.append(caption_path)

    filters = (
        "[0:v]scale=390:720:force_original_aspect_ratio=increase,crop=390:720,format=rgba,"
        "colorchannelmixer=aa=0.88[character];"
        "[1:a]asplit=2[audio][waveinput];"
        "[waveinput]showwaves=s=1120x70:mode=line:colors=0xc3941d@0.95[wave];"
        "[2:v]format=rgba,drawbox=x=54:y=52:w=662:h=242:color=0xf6f2e8@0.12:t=fill,"
        "drawbox=x=54:y=52:w=662:h=242:color=0xc3941d@0.85:t=2[base];"
        "[base][character]overlay=x=W-w-28:y=H-h-2:shortest=1[portrait];"
        "[portrait][3:v]overlay=shortest=1[panel];"
        "[panel][wave]overlay=x=80:y=615:shortest=1[video0]"
    )
    previous = "video0"
    for index, (_, start, end) in enumerate(cues):
        caption_input = index + 4
        next_label = f"video{index + 1}"
        fade_out = max(start + 0.2, end - 0.16)
        filters += (
            f";[{caption_input}:v]format=rgba,fade=t=in:st={start:.3f}:d=0.18:alpha=1,"
            f"fade=t=out:st={fade_out:.3f}:d=0.14:alpha=1[caption{index}];"
            f"[{previous}][caption{index}]overlay=shortest=1[{next_label}]"
        )
        previous = next_label

    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "30", "-i", str(CHARACTER_ART),
        "-i", str(audio_path),
        "-f", "lavfi", "-i", f"color=c=0x17213d:s=1280x720:r=30:d={math.ceil(duration)}",
        "-loop", "1", "-framerate", "30", "-i", str(panel_path),
    ]
    for caption_path in caption_paths:
        command.extend(["-loop", "1", "-framerate", "30", "-i", str(caption_path)])
    command.extend([
        "-filter_complex", filters,
        "-map", f"[{previous}]", "-map", "[audio]",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output_path),
    ])
    subprocess.run(command, check=True, capture_output=True, text=True)
    return {"path": output_path, "duration": round(duration, 2), "captions": caption_paths}
