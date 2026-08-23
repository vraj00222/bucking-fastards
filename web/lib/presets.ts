// Style presets. accent = the one loud color per style (tuned for paper ground);
// caption = label copy.
export const PRESETS = {
  phonk: { accent: "#c11212", caption: "Memphis menace for cursed monorepos" },
  hyperpop: { accent: "#d81b9e", caption: "Pitched-up chaos, zero linting" },
  emo: { accent: "#4a5fd0", caption: "It's not a phase, it's tech debt" },
  edm: { accent: "#0e7fa8", caption: "Drop the bass, then the table" },
  shanty: { accent: "#1c7a4a", caption: "Heave away on the merge queue" },
  bollywood: { accent: "#c77800", caption: "A three-act saga in every diff" },
  drill: { accent: "#444a52", caption: "Cold commits, no comments" },
  boyband: { accent: "#d24a6e", caption: "Five microservices, one dream" },
  citypop: { accent: "#7a3fd1", caption: "Neon nights on the main branch" },
  country: { accent: "#a06a1f", caption: "Dust, heartbreak, and legacy code" },
  boombap: {
    accent: "#8a5a12",
    caption:
      "classic 90s boom-bap hip-hop, dusty drum breaks, vinyl crackle, jazzy horn stabs, confident male rap vocals, 92 bpm, head-nod groove, chanted hook",
  },
  techrap: {
    accent: "#1e3a9e",
    caption:
      "playful tech-satire rap-pop, upbeat rhythmic male vocals, punchy synth bass, bouncy 808s, memorable repeated hook, viral energy, 102 bpm",
  },
  gfunk: {
    accent: "#5b2fb8",
    caption:
      "laid-back 90s west coast g-funk, whiny portamento synth lead, deep rolling bassline, smooth male rap vocals, sunny groove, 94 bpm, singalong hook",
  },
} as const;

export type StyleId = keyof typeof PRESETS;

export function presetFor(style: string) {
  return PRESETS[style as StyleId] ?? PRESETS.phonk;
}
