# OriginalSongBrief Schema

Single source of truth for the brief format, verbatim:

```typescript
type OriginalSongBrief = { id: string; title: string; projectName?: string; targetPlatform?: string; intendedAudience?: string; targetDurationSeconds?: number; allowedThemes: string[]; prohibitedThemes: string[]; brandVocabulary: string[]; contentRating: "clean"|"explicit"|"unknown"; referenceRecordIds: string[]; neutralStyleAttributes: { genreFamily: string[]; energy: "low"|"medium"|"high"; tempoBpmRange?: [number, number]; moods: string[]; vocalFormat: string[]; instrumentation: string[]; hookFormat: string[]; structure: string[] }; conceptSummary: string; originalHookConcept: string; sectionMap: string[]; lyricalConstraints: string[]; productionConstraints: string[]; rightsStatus: "owned"|"licensed"|"public-metadata-only"|"unknown"; provenance: { referenceSources: string[]; generatedAt: string; safetyTransformations: string[] } }
```

## Field docs

- `id` — unique brief id (UUID).
- `title` — working title of the ORIGINAL track to be produced.
- `projectName`, `targetPlatform`, `intendedAudience` — optional product context (e.g. "DropTable Records", "tiktok", "developers").
- `targetDurationSeconds` — optional target length, >= 0.
- `allowedThemes` / `prohibitedThemes` — topical guardrails for the lyricist.
- `brandVocabulary` — words/phrases the lyrics may use for brand identity.
- `contentRating` — target rating of the new track.
- `referenceRecordIds` — ids of the `MusicCatalogRecord`s consulted (metadata-level inspiration only).
- `neutralStyleAttributes` — the ONLY place style lives. Broad, artist-neutral descriptors:
  - `genreFamily` — broad genre labels ("rap-pop"), never "like <artist>".
  - `energy` — `low` | `medium` | `high`.
  - `tempoBpmRange` — optional `[min, max]`, both positive, min <= max.
  - `moods`, `vocalFormat`, `instrumentation` — broad descriptors.
  - `hookFormat` — hook shape ("short repeated hook", "chant").
  - `structure` — broad section labels from: intro, verse, pre-hook, hook, bridge, outro, unknown.
- `conceptSummary` — original high-level concept in ORIGINAL language.
- `originalHookConcept` — ONE line describing the hook idea. A concept, never lyrics.
- `sectionMap` — ordered section plan for the new track.
- `lyricalConstraints` — rules for the lyricist (originality, rating, prohibited themes).
- `productionConstraints` — rules for production (no recreation of existing recordings).
- `rightsStatus` — most restrictive rights status among the references.
- `provenance.referenceSources` — source URLs of the references.
- `provenance.generatedAt` — ISO 8601 timestamp.
- `provenance.safetyTransformations` — one entry per imitation/copy request that was rewritten to neutral attributes.

## Valid example

```json
{
  "id": "9f1c2b3a-4d5e-4f60-8a71-b2c3d4e5f607",
  "title": "DropTable Launch Anthem",
  "projectName": "DropTable Records",
  "targetPlatform": "tiktok",
  "intendedAudience": "developers",
  "targetDurationSeconds": 60,
  "allowedThemes": ["shipping code", "AI pair programming"],
  "prohibitedThemes": ["violence"],
  "brandVocabulary": ["DropTable", "drop the table"],
  "contentRating": "clean",
  "referenceRecordIds": ["rec-001"],
  "neutralStyleAttributes": {
    "genreFamily": ["rap-pop"],
    "energy": "high",
    "tempoBpmRange": [95, 110],
    "moods": ["playful", "confident"],
    "vocalFormat": ["rhythmic rap vocal"],
    "instrumentation": ["808 bass", "synth lead", "drum machine"],
    "hookFormat": ["short repeated hook"],
    "structure": ["intro", "verse", "hook", "verse", "hook", "outro"]
  },
  "conceptSummary": "An upbeat, playful anthem about shipping code with an AI pair programmer, celebrating developer culture without referencing any existing song or artist.",
  "originalHookConcept": "A chantable one-liner about dropping the table and shipping anyway.",
  "sectionMap": ["intro", "verse", "hook", "verse", "hook", "outro"],
  "lyricalConstraints": [
    "Write fully original lyrics; do not quote, interpolate, or closely paraphrase any existing song.",
    "Keep content rating: clean.",
    "Avoid prohibited themes: violence."
  ],
  "productionConstraints": [
    "Compose an original arrangement; do not recreate any specific existing recording, beat, or melody.",
    "No voice cloning or impersonation of any named artist."
  ],
  "rightsStatus": "public-metadata-only",
  "provenance": {
    "referenceSources": ["https://www.youtube.com/watch?v=abc123"],
    "generatedAt": "2026-08-23T12:00:00+00:00",
    "safetyTransformations": [
      "requirements.styleRequest: rewrote imitation request to neutral attributes"
    ]
  }
}
```
