# Style Normalization

Every style request is normalized into neutral, artist-independent production
attributes before it enters a brief. Imitation and copying requests are
rewritten, and each rewrite is recorded in `provenance.safetyTransformations`.

## Transformation table

| Input | Safe output |
|---|---|
| "Make it exactly like Drake." | "Create an original, high-energy rap-pop track with a hook-led arrangement, confident rhythmic vocal delivery, and a 95-110 BPM target range." |
| "Sound like Jeff Guo." | "Create an original, playful tech-satire track with upbeat rhythmic vocals, concise software-engineering references, a memorable repeated hook concept, and modern rap-pop energy." |
| "Copy the beat from this viral TikTok song." | "Create an original high-energy instrumental direction using broad attributes such as tempo range, energy, and hook-forward structure, without recreating a specific composition." |
| "Use the lyrics from Claude's Plan." | "Create new, original lyrics or a short original hook concept about AI-assisted engineering workflows. Do not reuse lyrics from the reference track." |

## General rules

1. Named artist reference -> replace with neutral genre/energy/tempo
   attributes. The artist's name never appears in style instructions.
2. Specific song or beat reference -> broad attributes only (tempo range,
   energy, mood, structure); never recreate the composition or recording.
3. Lyric reuse request -> replace with an original-concept instruction; no
   existing lyrics are quoted, interpolated, or closely paraphrased.
