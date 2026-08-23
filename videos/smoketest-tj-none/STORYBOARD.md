---
compositionId: smoketest-tj-none
duration_s: 60.000
canvas: { "w": 1080, "h": 1920, "fps": 30 }
style:
  font: "Consolas, 'Courier New', monospace"
  palette: ["#0D1117", "#C9D1D9", "#58A6FF", "#484F58"]
build_notes:
  - "terminal aesthetic"
  - "code-editor dark theme"
  - "monospace all-caps"
  - "vertical center safe zone"
  - "accent for code/commands"
  - "one paused timeline per frame"
  - "no remote assets"
---

## Frame 1 — 01-verse-a

- src: compositions/frames/01-verse-a.html
- duration: 12.423s
- span_sec: [0.000, 12.423]
- pacing: beat_cut
- mood: [dark, tense]
- feel: sparse intro building tension; heavy bass drops at t=5-6 and t=11
- section: [verse]

### Groups

- **g1** — free_design
  - span_sec: [0.000, 12.423]
  - lyric_line: "NPM INSTALL COMMANDER, NOW I RUN THE THRONE"
  - hero_words: ["COMMANDER", "THRONE"]
  - visual: "Type slams in centered at t=0.441 on first beat; 'COMMANDER' flashes accent blue on the SURGE at t=11; 'NPM INSTALL' locks top-third in muted gray as persistent ghost."

## Frame 2 — 02-verse-b

- src: compositions/frames/02-verse-b.html
- duration: 6.014s
- span_sec: [12.423, 18.437]
- pacing: beat_cut
- mood: [dark, cinematic]
- feel: heavy sub bass; DROP at t=16 then SURGE at t=17
- section: [verse]

### Groups

- **g1** — free_design
  - span_sec: [12.423, 18.437]
  - lyric_line: "LIB/COMMAND.JS SO MASSIVE IT'S A ZONE OF ITS OWN"
  - hero_words: ["COMMAND.JS", "ZONE"]
  - visual: "Filepath 'lib/command.js' types in letter-by-letter starting t=12.423; 'ZONE' explodes outward in accent on the SURGE at t=17; entire line glows briefly during DROP at t=16."

## Frame 3 — 03-verse-c

- src: compositions/frames/03-verse-c.html
- duration: 5.990s
- span_sec: [18.437, 24.427]
- pacing: phrase_flow
- mood: [dark, glitch]
- feel: steady heavy bass; building to phrase end
- section: [verse]

### Groups

- **g1** — free_design
  - span_sec: [18.437, 24.427]
  - lyric_line: "SPAWNING CHILD PROCESSES, FORWARDING SIGNALS RAW"
  - hero_words: ["PROCESSES", "SIGNALS"]
  - visual: "'PROCESSES' duplicates and offsets 2px in accent at t=20; 'RAW' slams bottom-right at phrase end t=24.427; line holds steady center with no per-beat cuts."

## Frame 4 — 04-verse-d-chorus

- src: compositions/frames/04-verse-d-chorus.html
- duration: 12.005s
- span_sec: [24.427, 36.432]
- pacing: beat_cut
- mood: [hype, aggressive]
- feel: HIGH energy t=28-30; chorus chant mantra
- section: [chorus]

### Groups

- **g1** — free_design
  - span_sec: [24.427, 36.432]
  - lyric_line: "EXAMPLES/PIZZA ORDERING CLI, THAT'S THE LAW — NPM INSTALL COMMANDER"
  - hero_words: ["PIZZA", "COMMANDER"]
  - visual: "'EXAMPLES/PIZZA' flashes top-left t=24.427; verse line fades at t=30.418; 'NPM INSTALL COMMANDER' pounds in stacked three times (one per phrase repeat) with accent underline on each 'COMMANDER'; hard cuts on every 'npm install' beat."

## Frame 5 — 05-bridge

- src: compositions/frames/05-bridge.html
- duration: 12.005s
- span_sec: [36.432, 48.437]
- pacing: phrase_flow
- mood: [dark, tense, cinematic]
- feel: sparse mid-section; DROPs at t=37, t=41, t=47-48
- section: [bridge]

### Groups

- **g1** — free_design
  - span_sec: [36.432, 48.437]
  - lyric_line: "THREE TODOs IN THE GIT HOOK, EACH ONE MORE VAGUE — NOBODY EDITS THAT FILE"
  - hero_words: ["TODO", "VAGUE"]
  - visual: "'TODO' repeats three times staggered vertically t=36.432-40; 'VAGUE' glitches/distorts on DROP at t=41; 'NOBODY EDITS' holds dimmed through silence t=48; slow crossfades, no beat cuts."

## Frame 6 — 06-chorus-reprise

- src: compositions/frames/06-chorus-reprise.html
- duration: 5.991s
- span_sec: [48.437, 54.428]
- pacing: beat_cut
- mood: [hype, glitch]
- feel: silence t=48-50, then rebuild; SURGE at t=53, massive DROP at t=54
- section: [chorus]

### Groups

- **g1** — free_design
  - span_sec: [48.437, 54.428]
  - lyric_line: "NPM INSTALL COMMANDER — ONE FILE RULES THE PARSER"
  - hero_words: ["COMMANDER", "PARSER"]
  - visual: "Silence t=48-50 holds previous ghost dimmed; 'NPM INSTALL' rebuilds t=50; 'COMMANDER' slams accent on SURGE t=53; 'PARSER' flashes white on DROP t=54; beat-synced cuts throughout."

## Frame 7 — 07-outro

- src: compositions/frames/07-outro.html
- duration: 5.572s
- span_sec: [54.428, 60.000]
- pacing: phrase_flow
- mood: [dark, playful]
- feel: silence t=54-56 then sparse wind-down; void at t=59
- section: [outro]

### Groups

- **g1** — free_design
  - span_sec: [54.428, 60.000]
  - lyric_line: "VUE CLI BOWED DOWN, CREATE REACT APP TOO — 28K STARS AND THE COWBELL NEVER STOPS"
  - hero_words: ["28K", "COWBELL"]
  - visual: "'VUE CLI' and 'CREATE REACT APP' fade in stacked t=54-56 during silence; '28K STARS' pulses accent t=56-57; 'COWBELL NEVER STOPS' holds bottom-center with trailing 'skrrt skrrt skrrt' in muted as final ghost through t=60."
