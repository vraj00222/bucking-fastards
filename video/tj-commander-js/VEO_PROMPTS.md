# Veo prompt pack — Phase 2 footage under lyrics

Model: `veo-3.0-fast-generate-001`
Project: `sharp-leaf-451416-r4`, Location: `us-central1`
Per-call config: `aspect_ratio="9:16"` (fallback `"16:9"` if preflight fails),
`number_of_videos=2`, `duration_seconds=8`, `generate_audio=False`,
`resolution="720p"`, `person_generation="allow_all"`.

We keep the best take per slot and discard the rest.
Total kept: 2 clips × ~6s each = ~12s of Veo footage (of 60s track).
Hard ceiling: MAX_CLIPS=4 (2 prompts × 2 candidates).

---

## Shot 1 — `03g1-terminal-spawn` (frame 3, group 1 bed, dur=5.99s)

Seed: **4711**

Prompt:

```
Single continuous shot, no scene cuts. Portrait 9:16 macro of a vintage CRT
computer monitor in a dark room, green phosphor text on black. The terminal is
spawning child processes: lines of "PID 1234 → PID 1235 → PID 1236" cascade
downward, one per second, with mild scanline flicker and chromatic aberration
on the type. Slow, imperceptible zoom-in on the center of the screen.
Sodium-vapor amber (#FF9500) light bleeds in from the top edge. Heavy film
grain, VHS tracking artifacts at the edges. Dark, ominous, industrial. Camera
perfectly still except for the slow push-in. No dialogue. No music. No sound
effects. Silent.
```

## Shot 2 — `04g1-cowbell-macro` (frame 4, group 1 bed, dur=6.01s)

Seed: **4712**

Prompt:

```
Single continuous shot, no scene cuts. Portrait 9:16 extreme macro of a chrome
808 cowbell suspended in black void, slowly rotating clockwise. Sodium-vapor
amber (#FF9500) rim light catches the polished metal edges, red (#D8000F)
accent from below. Extreme shallow depth of field, only the bell's edge is
sharp. Slight camera drift, no cuts. Heavy grain, 35mm anamorphic flare when
the light catches the surface. Dark, hypnotic, aggressive phonk music-video
aesthetic. Camera slow-orbit around the bell. No dialogue. No music. No sound
effects. Silent.
```
