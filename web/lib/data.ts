import { readFileSync } from "fs";
import { join } from "path";

// Data lives outside the Next root, so pages that render from it should opt out
// of static caching to pick up newly generated tracks:
//   export const dynamic = "force-dynamic";

export type Source = {
  filepath: string;
  linestart?: number;
  summary?: string;
};

export type Track = {
  slug: string;
  repo: string;
  style: string;
  song_title: string;
  artist_name: string;
  caption: string;
  lyrics: string; // [verse]/[chorus] tags on their own lines
  facts_highlights: string[];
  audio_url: string; // "/tracks/<slug>.mp3"
  cover_url: string | null; // null -> derive via lib/art
  stars: number;
  language: string;
  description: string;
  sources: Source[];
  timing: { intel_s: number; lyrics_s: number; audio_s: number };
  take: number;
};

export function getTracks(): Track[] {
  try {
    const raw = readFileSync(join(process.cwd(), "../data/tracks.json"), "utf8");
    return (JSON.parse(raw).tracks ?? []) as Track[];
  } catch {
    return [];
  }
}

export function getTrack(slug: string): Track | undefined {
  return getTracks().find((t) => t.slug === slug);
}
