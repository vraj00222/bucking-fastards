// Style presets. accent = the one loud color per style; caption = label copy.
export const PRESETS = {
  phonk: { accent: "#ff2d2d", caption: "Memphis menace for cursed monorepos" },
  hyperpop: { accent: "#ff5ce1", caption: "Pitched-up chaos, zero linting" },
  emo: { accent: "#7a8fff", caption: "It's not a phase, it's tech debt" },
  edm: { accent: "#00e5ff", caption: "Drop the bass, then the table" },
  shanty: { accent: "#2fd27d", caption: "Heave away on the merge queue" },
  bollywood: { accent: "#ffb300", caption: "A three-act saga in every diff" },
  drill: { accent: "#9aa0a6", caption: "Cold commits, no comments" },
  boyband: { accent: "#ff8fab", caption: "Five microservices, one dream" },
  citypop: { accent: "#b28dff", caption: "Neon nights on the main branch" },
  country: { accent: "#e0a458", caption: "Dust, heartbreak, and legacy code" },
} as const;

export type StyleId = keyof typeof PRESETS;

export function presetFor(style: string) {
  return PRESETS[style as StyleId] ?? PRESETS.phonk;
}
