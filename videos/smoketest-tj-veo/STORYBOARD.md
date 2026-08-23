---
compositionId: smoketest-tj-veo
duration_s: 60.000
canvas: { "w": 1080, "h": 1920, "fps": 30 }
style:
  font: "Menlo, Consolas, Monaco, 'Courier New', monospace"
  palette: ["#0D1117", "#C9D1D9", "#58A6FF", "#8B949E"]
build_notes:
  - "terminal dark mode aesthetic"
  - "monospace code feel"
  - "CLI-inspired typography"
  - "accent pops like hyperlinks"
  - "one paused timeline per frame"
  - "no remote assets"
---

## Frame 1 — 01-verse-a

- src: compositions/frames/01-verse-a.html
- duration: 12.423s
- span_sec: [0.000, 12.423]
- pacing: beat_cut
- mood: [dark, tense, glitch]
- feel: sparse intro build with cowbell, heavy sub drops on 5s and 11s
- section: [verse]

### Groups

- **g1** — free_design
  - span_sec: [0.000, 12.423]
  - lyric_line: "npm install commander, now I run the throne"
  - hero_words: ["commander", "throne"]
  - visual: "Type types in left-aligned at 0.441s like terminal input; 'commander' glows accent blue on beat at 5s; 'throne' slams in bold on the SURGE at 11s with heavy sub punch."
  - footage: {"backend": "veo", "prompt": "Extreme macro shot of a mechanical keyboard with backlit keys in deep blue (#58A6FF) and white (#C9D1D9) glowing through keycaps, fingers striking keys in slow motion creating ripples of light, heavy film grain, 35mm anamorphic lens with shallow depth of field, dark ambient lighting (#0D1117) with sodium-vapor accent glow, slow dolly-in toward the spacebar as fingers type command sequences, dust particles visible in the blue backlight, 9:16 portrait framing, cinematic tension, glitch artifacts flickering across the frame edges, high contrast shadows, silent", "seed": 4711, "duration_s": 8.0, "path": "assets/footage/01-verse-a.mp4"}

## Frame 2 — 02-verse-b

- src: compositions/frames/02-verse-b.html
- duration: 6.014s
- span_sec: [12.423, 18.437]
- pacing: beat_cut
- mood: [dark, aggressive]
- feel: heavy bass, hihat fill at 11.6s carries into phrase, SURGE at 17s
- section: [verse]

### Groups

- **g1** — free_design
  - span_sec: [12.423, 18.437]
  - lyric_line: "lib/command.js so massive it's a zone of its own"
  - hero_words: ["command.js", "zone"]
  - visual: "Line enters top-third on phrase start at 12.423s; 'command.js' flickers monospace at 14s beats; 'zone' expands scale on 17s SURGE with accent glow."

## Frame 3 — 03-verse-c

- src: compositions/frames/03-verse-c.html
- duration: 5.990s
- span_sec: [18.437, 24.427]
- pacing: beat_cut
- mood: [tense, glitch]
- feel: medium energy ride, sub bass steady
- section: [verse]

### Groups

- **g1** — free_design
  - span_sec: [18.437, 24.427]
  - lyric_line: "spawning child processes, forwarding signals raw"
  - hero_words: ["processes", "signals"]
  - visual: "Words spawn in staggered on beats 18-20s like forked processes; 'signals' pulses accent blue on snare hits; bottom-third placement."

## Frame 4 — 04-verse-d-chorus

- src: compositions/frames/04-verse-d-chorus.html
- duration: 5.991s
- span_sec: [24.427, 30.418]
- pacing: beat_cut
- mood: [hype, dark]
- feel: energy ramp to HIGH at 28s, phrase closes hot
- section: [verse→chorus]

### Groups

- **g1** — free_design
  - span_sec: [24.427, 30.418]
  - lyric_line: "examples/pizza ordering CLI, that's the law"
  - hero_words: ["pizza", "CLI", "law"]
  - visual: "Line locked center at 24.427s; 'CLI' blinks cursor-style; 'law' scales huge at 28s energy peak with accent stroke."

## Frame 5 — 05-chorus-a

- src: compositions/frames/05-chorus-a.html
- duration: 12.005s
- span_sec: [30.418, 42.423]
- pacing: phrase_flow
- mood: [hype, cinematic]
- feel: steady heavy sub, DROP at 37s and 41s, chorus mantra loop
- section: [chorus]

### Groups

- **g1** — free_design
  - span_sec: [30.418, 42.423]
  - lyric_line: "npm install commander — one file rules the parser"
  - hero_words: ["commander", "parser"]
  - visual: "Chorus hook centers full-width at 30.418s; 'npm install commander' repeats as ghost echo on each 4-bar; 'parser' holds bright on DROP at 41s."

## Frame 6 — 06-verse-bridge

- src: compositions/frames/06-verse-bridge.html
- duration: 6.014s
- span_sec: [42.423, 48.437]
- pacing: beat_cut
- mood: [tense, dark]
- feel: medium energy, hard DROPs at 47s and 48s close the section
- section: [verse→bridge]

### Groups

- **g1** — free_design
  - span_sec: [42.423, 48.437]
  - lyric_line: "incrementing inspector ports in the dead of night"
  - hero_words: ["inspector", "night"]
  - visual: "Line fades in top-left at 42.423s; 'inspector' glitches on snare at 44s; whole line shakes on DROP at 47s then cuts to silence."

## Frame 7 — 07-bridge-chorus

- src: compositions/frames/07-bridge-chorus.html
- duration: 5.991s
- span_sec: [48.437, 54.428]
- pacing: phrase_flow
- mood: [dreamy, glitch]
- feel: VOID silence 48-50s, sparse return, hihat accel-roll at 52.3s, SURGE at 53s
- section: [bridge]

### Groups

- **g1** — free_design
  - span_sec: [48.437, 54.428]
  - lyric_line: "three TODOs in the git hook — nobody edits that file"
  - hero_words: ["TODOs", "git"]
  - visual: "Silence holds previous line as muted ghost 48-50s; new line types in slowly at 50s; 'TODOs' blinks three times; roll at 52.3s shakes text; DROP at 54s kills it."

## Frame 8 — 08-outro

- src: compositions/frames/08-outro.html
- duration: 5.572s
- span_sec: [54.428, 60.000]
- pacing: phrase_flow
- mood: [playful, glitch]
- feel: VOID 54-56s, sparse cowbell return, final DROP at 59s
- section: [outro]

### Groups

- **g1** — free_design
  - span_sec: [54.428, 60.000]
  - lyric_line: "Vue CLI bowed down, Create React App too — skrrt skrrt skrrt"
  - hero_words: ["Vue", "React", "skrrt"]
  - visual: "Text drifts in from silence at 56s; 'Vue' and 'React' dim to muted; 'skrrt skrrt skrrt' rapid-fires center on cowbell hits 57-59s; final word fades on DROP at 59s."
