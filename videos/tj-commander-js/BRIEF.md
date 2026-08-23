# BRIEF — npm install Commander (music video)

Track: `web/public/tracks/tj-commander.js.mp3` → `assets/song.wav`
Artist: Comma-nd.R
Duration: 60s (measured)
Genre: aggressive phonk, memphis rap, distorted 808 cowbell, dark, fast, male rap vocals

## Format
- Primary render: 1080x1920 (9:16 portrait, Shorts/Reels/TikTok)
- Multi-AR variants deferred to Phase 3

## The single rule that overrides everything else
**Lyrics are ALWAYS on screen.** No empty frames. If there is no active sung line, the previous line holds as a dimmed ghost until the next line begins.

## Cut / edit direction (AI decides specifics from the beat grid)
- Cut on the beat grid; punch-in on downbeats.
- Hard cut on cowbell hits.
- Whip-pan transitions ONLY on phrase (section) changes.
- Bridge: hold 4 bars on "three TODOs in the git hook". No cuts.
- Outro: end on a hard musical stop at the final `skrrt`.

## Caption style
- Condensed all-caps sans, one line at a time on the beat.
- Keyword highlight in acid green (#B6FF00) on: `commander`, `parser`, `cowbell`, `skrrt`, `TODO`.
- Section labels (`[verse]`, `[chorus]`, `[bridge]`, `[outro]`) render as small monospace overlays in a corner. They do NOT replace the lyric line.
- Middle-third safe area reserved for the active lyric line so future footage (Phase 2) leaves it readable.

## Instrumental-tail rule
- Intro (before line 1): show song title + artist card ("NPM INSTALL COMMANDER / COMMA-ND.R"). Still counts as "lyrics on screen."
- Outro tail (after final `skrrt`): show repo card ("tj/commander.js — 28,370 ★"). Hold to the end.

## Aesthetic (typography-only, Phase 1)
- Sodium-vapor amber (#FF9500) + acid-green highlight (#B6FF00) on near-black (#0A0A0A).
- CRT green terminal panels as background texture.
- 808 cowbell chrome macro cutaways as graphic elements between phrases.
- Slight film grain, VHS chroma bleed on hard cuts.
- No photoreal footage in this phase. Type alone carries the video.

## Do NOT do
- Do NOT generate any audio; the song is the only audio.
- Do NOT leave the screen lyric-empty at any point.
- Do NOT place captions in the top 15% or bottom 15% (safe area for social platform UI).
- Do NOT force a cut onto every beat during the bridge.
