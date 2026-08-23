# DropTable Records music service — adapted from Modal's official ACE-Step 1.5 example
# (modal-examples/06_gpu_and_ml/text-to-audio/generate_music.py)

from pathlib import Path
from typing import Optional

import modal

image = (
    modal.Image.from_registry(
        "nvidia/cuda:13.0.0-cudnn-devel-ubuntu22.04", add_python="3.12"
    )
    .apt_install("git", "ffmpeg")
    .run_commands(
        "git clone --branch v0.1.6 --depth 1 https://github.com/ace-step/ACE-Step-1.5.git /opt/ace-step",
    )
    .uv_pip_install(
        "/opt/ace-step", "hf_transfer==0.1.9", "torchcodec==0.10.0", "torch~=2.10.0"
    )
    .entrypoint([])
)

checkpoints_dir = "/opt/ace-step/checkpoints"
model_cache = modal.Volume.from_name("ACE-Step-v15-model-cache", create_if_missing=True)

image = image.env(
    {"ACESTEP_PROJECT_ROOT": "/opt/ace-step", "HF_HUB_ENABLE_HF_TRANSFER": "1"}
)

web_image = modal.Image.debian_slim(python_version="3.12").uv_pip_install(
    "fastapi[standard]==0.115.4"
)

app = modal.App("droptable-music")


@app.cls(gpu="l40s", image=image, volumes={checkpoints_dir: model_cache}, timeout=600)
class MusicGenerator:
    @modal.enter()
    def init(self):
        from acestep.handler import AceStepHandler
        from acestep.llm_inference import LLMHandler
        from acestep.model_downloader import ensure_lm_model, ensure_main_model

        lm_model_name = "acestep-5Hz-lm-4B"
        ensure_main_model(checkpoints_dir=checkpoints_dir)
        ensure_lm_model(model_name=lm_model_name, checkpoints_dir=checkpoints_dir)

        self.dit_handler = AceStepHandler()
        init_status, enable_generate = self.dit_handler.initialize_service(
            project_root="/opt/ace-step",
            config_path="acestep-v15-turbo",
            device="cuda",
        )
        if not enable_generate:
            raise RuntimeError(f"DiT model initialization failed: {init_status}")

        self.llm_handler = LLMHandler()
        lm_status, lm_success = self.llm_handler.initialize(
            checkpoint_dir=checkpoints_dir,
            lm_model_path=lm_model_name,
            backend="vllm",
            device="cuda",
        )
        if not lm_success:
            raise RuntimeError(f"LM initialization failed: {lm_status}")

    @modal.method()
    def run(
        self,
        prompt: str,
        lyrics: str,
        duration: float = 60.0,
        format: str = "mp3",
        manual_seeds: Optional[int] = 1,
    ) -> bytes:
        from acestep.inference import GenerationConfig, GenerationParams, generate_music

        params = GenerationParams(
            caption=prompt,
            lyrics=lyrics,
            duration=duration,
            thinking=True,
        )
        config = GenerationConfig(
            audio_format=format,
            batch_size=1,
            seeds=[manual_seeds] if manual_seeds is not None else None,
            use_random_seed=manual_seeds is None,
        )
        result = generate_music(
            self.dit_handler,
            self.llm_handler,
            params,
            config,
            save_dir="/dev/shm",
        )
        if not result.success:
            raise RuntimeError(f"Music generation failed: {result.error}")
        return Path(result.audios[0]["path"]).read_bytes()


@app.function(image=web_image, timeout=600)
@modal.fastapi_endpoint(method="POST")
def generate(body: dict):
    import base64

    gen = MusicGenerator()
    audio = gen.run.remote(
        body["caption"],
        body["lyrics"],
        duration=float(body.get("duration", 75.0)),
        format="mp3",
        manual_seeds=body.get("seed"),
    )
    return {"audio_b64": base64.b64encode(audio).decode()}


@app.local_entrypoint()
def main(
    prompt: Optional[str] = None,
    lyrics: Optional[str] = None,
    duration: float = 30.0,
    format: str = "mp3",
    manual_seeds: Optional[int] = 1,
    out: str = "/tmp/warmup.mp3",
):
    if prompt is None:
        prompt = "aggressive phonk, memphis rap, distorted 808 cowbell, dark, fast, male rap vocals"
        lyrics = "[verse]\ngit push at 3am, no tests, no fear\n[chorus]\nforce push, force push"
    clip = MusicGenerator().run.remote(
        prompt, lyrics, duration=duration, format=format, manual_seeds=manual_seeds
    )
    Path(out).write_bytes(clip)
    print(f"saved {len(clip)} bytes to {out}")


@app.local_entrypoint()
def generate_batch(
    prompt: str,
    lyrics: str,
    duration: float = 75.0,
    outdir: str = "/tmp/takes",
):
    gen = MusicGenerator()
    args = [(prompt, lyrics, duration, "mp3", seed) for seed in (1, 2, 3)]
    Path(outdir).mkdir(parents=True, exist_ok=True)
    for i, clip in enumerate(gen.run.starmap(args), 1):
        p = Path(outdir) / f"take{i}.mp3"
        p.write_bytes(clip)
        print(f"take{i}: {len(clip)} bytes -> {p}")
