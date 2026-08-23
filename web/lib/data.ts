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
  video_url?: string | null; // "/videos/<slug>.mp4" rendered locally from the release
  cover_url: string | null; // null -> derive via lib/art
  stars: number;
  language: string;
  description: string;
  sources: Source[];
  timing: { intel_s: number; lyrics_s: number; audio_s: number; video_s?: number };
  take: number;
};

export type SourceReviewRecord = {
  id: string;
  priority: "P0" | "P1" | "P2" | "P3";
  sourceName: string;
  sourceType: string;
  sourceUrl: string;
  collectionTags: string[];
  rightsStatus: "public-metadata-only" | "unknown";
  trustLevel: "untrusted";
  extractionStatus: "queued" | "metadata-captured" | "reviewed" | "rejected";
  linkedCatalogRecordCount: number;
  reviewerDecision: "pending" | "approved" | "rejected";
  rejectionReason: string | null;
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

export function getSourceReviewQueue(): SourceReviewRecord[] {
  try {
    const raw = readFileSync(join(process.cwd(), "../data/source-review-queue.json"), "utf8");
    return (JSON.parse(raw).records ?? []) as SourceReviewRecord[];
  } catch {
    return [];
  }
}
