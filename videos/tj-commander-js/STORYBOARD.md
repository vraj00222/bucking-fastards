---
compositionId: tj-commander-js
duration_s: 60.0
canvas: { "w": 1080, "h": 1920, "fps": 30 }
style:
  font: "Shrikhand / Libre Baskerville / Space Grotesk"
  palette: ["#FFFFFF", "#1C1410", "#D8000F", "#F5F2EF"]
build_notes:
  [
    "one paused timeline per frame",
    "no remote assets",
    "lyrics are always on screen — every frame ships with a readable lyric line",
    "condensed all-caps captions in middle third safe area (9:16)",
    "keyword highlight color = red (#D8000F) on: commander, parser, cowbell, skrrt, TODO",
  ]
avoid:
  [
    "silent frames with no lyric on screen",
    "captions in top or bottom 15% (social platform UI safe area)",
    "generic slideshow feel",
  ]
---

## Frame 1 — 01-intro

- src: compositions/frames/01-intro.html
- duration: 6.432s
- span_sec: [0.0, 6.432]
- pacing: beat_cut
- mood: [dark, tense]
- feel: cold intro, sparse VOID energy phases, cowbell + hihat only, title card territory before the first lyric line lands

### Groups

- **g1** — template: `intro-kinetic-cascade`
  - span_sec: [0.0, 6.432]
  - params:
    {
      theme: "dark",
      icon: "bolt",
      phrases:
        [
          { text: "NPM INSTALL", heroWord: "INSTALL" },
          { text: "COMMANDER", heroWord: "COMMANDER" },
          { text: "COMMA-ND.R", heroWord: "COMMA-ND.R" },
        ],
      climax: { text: "NPM INSTALL COMMANDER", heroWord: "COMMANDER" },
    }
  - role_bindings:
    {
      phrase: { times: [0.44, 2.5, 4.5] },
      climax: { in: 6.0, iconAt: 6.3 },
    }
  - copy: "NPM INSTALL COMMANDER — COMMA-ND.R"

## Frame 2 — 02-verse-open

- src: compositions/frames/02-verse-open.html
- duration: 12.005s
- span_sec: [6.432, 18.437]
- pacing: beat_cut
- mood: [aggressive, hype]
- feel: two verse phrases carrying "npm install commander, now I run the throne" through "lib/command.js so massive it's a zone of its own", SURGEs at t=11 and t=17 drive punch-ins on downbeats

### Groups

- **g1** — template: `typewriter-phrase-keyword-shuffle`
  - span_sec: [6.432, 12.423]
  - params:
    {
      bgColor: "#1C1410",
      textColor: "#F5F2EF",
      accentColor: "#D8000F",
      lead1: "NPM INSTALL",
      lead2: "COMMANDER, NOW I",
      lead3: "RUN THE",
      keyword: "THRONE",
      periodChar: "▮",
    }
  - role_bindings:
    { onsets: [6.5, 7.5, 8.4, 9.3, 10.2, 11.1, 11.8], keywordShuffleAt: 11.0 }
  - copy: "NPM INSTALL COMMANDER, NOW I RUN THE THRONE"
- **g2** — template: `typewriter-phrase-keyword-shuffle`
  - span_sec: [12.423, 18.437]
  - params:
    {
      bgColor: "#1C1410",
      textColor: "#F5F2EF",
      accentColor: "#D8000F",
      lead1: "LIB/COMMAND.JS",
      lead2: "SO MASSIVE IT'S A",
      lead3: "ZONE OF ITS",
      keyword: "OWN",
      periodChar: "▮",
    }
  - role_bindings:
    { onsets: [12.5, 13.5, 14.5, 15.5, 16.5, 17.0], keywordShuffleAt: 17.0 }
  - copy: "LIB/COMMAND.JS SO MASSIVE IT'S A ZONE OF ITS OWN"

## Frame 3 — 03-verse-body

- src: compositions/frames/03-verse-body.html
- duration: 11.990s
- span_sec: [18.437, 30.427]
- pacing: beat_cut
- mood: [aggressive, glitch]
- feel: two phrases of dense verse — spawning child processes, examples/pizza, suggestSimilar.js, command.option-misuse.test.js — hard hihat drive, cowbell relentless, one line per two bars

### Groups

- **g1** — template: `split-anchor-word-slot`
  - span_sec: [18.437, 24.427]
  - params:
    {
      bgColor: "#1C1410",
      anchors:
        [
          "SPAWNING",
          "CHILD",
          "PROCESSES",
          "FORWARDING",
          "SIGNALS",
          "RAW",
        ],
      theme: "dark",
      showText: true,
      program: "anchor-lock,slot-cycle,jitter",
    }
  - role_bindings: { onsets: [18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.0] }
  - copy: "SPAWNING CHILD PROCESSES, FORWARDING SIGNALS RAW"
  - asset:
      treatment: bg_under_text
      clips: ["assets/03g1-terminal-spawn.mp4"]
      dim: 0.35
      overlay_copy: "SPAWNING CHILD PROCESSES, FORWARDING SIGNALS RAW"
      source: veo-2.0-generate-001 seed=4711 aspect=9:16
- **g2** — template: `typewriter-phrase-keyword-shuffle`
  - span_sec: [24.427, 30.427]
  - params:
    {
      bgColor: "#1C1410",
      textColor: "#F5F2EF",
      accentColor: "#D8000F",
      lead1: "EXAMPLES/PIZZA",
      lead2: "ORDERING CLI",
      lead3: "THAT'S THE",
      keyword: "LAW",
      periodChar: "▮",
    }
  - role_bindings:
    { onsets: [24.5, 25.5, 26.5, 27.5, 28.5, 29.5], keywordShuffleAt: 29.5 }
  - copy: "EXAMPLES/PIZZA ORDERING CLI, THAT'S THE LAW"

## Frame 4 — 04-chorus-hook

- src: compositions/frames/04-chorus-hook.html
- duration: 12.005s
- span_sec: [30.427, 42.432]
- pacing: beat_cut
- mood: [hype, aggressive]
- feel: chorus territory — "npm install commander" hammer, hard_stop at 41s marks the exit; kinetic caps flashing on every downbeat

### Groups

- **g1** — template: `poster-tile-mosaic`
  - span_sec: [30.427, 36.437]
  - params:
    {
      bgColor: "#1C1410",
      tiles: 8,
      bands: ["#D8000F", "#F5F2EF", "#1C1410"],
      gap: 12,
      showText: true,
      labels:
        [
          "NPM",
          "INSTALL",
          "COMMANDER",
          "NPM",
          "INSTALL",
          "COMMANDER",
          "ONE FILE",
          "PARSER",
        ],
      program: "accumulate,recolor,fill",
    }
  - role_bindings:
    { onsets: [30.5, 31.5, 32.5, 33.5, 34.5, 35.5, 36.0] }
  - copy: "NPM INSTALL COMMANDER — ONE FILE RULES THE PARSER"
  - asset:
      treatment: bg_under_text
      clips: ["assets/04g1-cowbell-macro.mp4"]
      dim: 0.35
      overlay_copy: "NPM INSTALL COMMANDER — ONE FILE RULES THE PARSER"
      source: veo-2.0-generate-001 seed=4712 aspect=9:16
- **g2** — template: `typewriter-phrase-keyword-shuffle`
  - span_sec: [36.437, 42.432]
  - params:
    {
      bgColor: "#1C1410",
      textColor: "#F5F2EF",
      accentColor: "#D8000F",
      lead1: "ONE FILE",
      lead2: "RULES THE",
      lead3: "NPM INSTALL",
      keyword: "COMMANDER",
      periodChar: "▮",
    }
  - role_bindings:
    { onsets: [36.5, 37.5, 38.5, 39.5, 40.5, 41.0], keywordShuffleAt: 41.0 }
  - copy: "ONE FILE RULES THE PARSER — NPM INSTALL COMMANDER"

## Frame 5 — 05-bridge-todos

- src: compositions/frames/05-bridge-todos.html
- duration: 12.005s
- span_sec: [42.432, 54.437]
- pacing: beat_cut
- mood: [tense, dark]
- feel: the bridge — DROPs at 47/48s and again at 54s carve the "three TODOs" line; hold the TODO caption across the drops as the beat empties out

### Groups

- **g1** — template: `typewriter-phrase-keyword-shuffle`
  - span_sec: [42.432, 48.437]
  - params:
    {
      bgColor: "#1C1410",
      textColor: "#F5F2EF",
      accentColor: "#D8000F",
      lead1: "THREE",
      lead2: "IN THE",
      lead3: "GIT HOOK,",
      keyword: "TODO",
      periodChar: "▮",
    }
  - role_bindings:
    { onsets: [42.5, 43.5, 44.5, 45.5, 46.5, 47.0], keywordShuffleAt: 47.0 }
  - copy: "THREE TODOS IN THE GIT HOOK"
- **g2** — template: `held-text-strobe-burst`
  - span_sec: [48.437, 54.437]
  - params:
    {
      markText: "TODO TODO TODO",
      fontStyle: "display",
      markScale: 1.0,
      idleColor: "#1C1410",
      idleInk: "#D8000F",
      frames: 6,
      strobePlan: "roll",
      decor: "hairline",
      duration: 6.0,
    }
  - role_bindings: { onsets: [48.5, 49.5, 50.5, 51.5, 52.5, 53.5] }
  - copy: "REPLACE WITH APPROPRIATE CHECKS — THREE TIMES"

## Frame 6 — 06-outro-skrrt

- src: compositions/frames/06-outro-skrrt.html
- duration: 5.563s
- span_sec: [54.437, 60.0]
- pacing: beat_cut
- mood: [hype, glitch]
- feel: outro sting — hard_stops at 57s and 59s, final "skrrt skrrt skrrt" and 28k stars card lands on the last hit

### Groups

- **g1** — template: `logo-split-lockup-pulse`
  - span_sec: [54.437, 60.0]
  - params:
    {
      bgColor: "#1C1410",
      markColor: "#D8000F",
      textColor: "#F5F2EF",
      leftMark: "★",
      rightMark: "★",
      word1: "28K",
      word2: "STARS",
      word3: "SKRRT",
      word4: "SKRRT",
    }
  - role_bindings:
    { onsets: [54.5, 55.5, 56.5, 57.4, 58.3, 59.1] }
  - copy: "28K STARS — TJ/COMMANDER.JS — SKRRT SKRRT SKRRT"
