# Catalog Schema

Single source of truth for catalog records.

## TypeScript definition

```typescript
type MusicCatalogRecord = { id: string; slug: string; title: string; artist?: string; sourceUrl: string; canonicalUrl?: string; sourceType: "web-page"|"youtube-video"|"manual-entry"|"user-upload"|"documentation"|"github-repository"|"pdf"; publisher?: string; releaseDate?: string; durationSeconds?: number; themes: string[]; tags: string[]; contentRating: "clean"|"explicit"|"unknown"; structure: Array<"intro"|"verse"|"pre-hook"|"hook"|"bridge"|"outro"|"unknown">; musicAttributes: { energy: "low"|"medium"|"high"; tempoBpmRange?: [number, number]; moods: string[]; vocalFormats: string[]; instrumentation: string[] }; originalSynopsis?: string; rightsStatus: "owned"|"licensed"|"public-metadata-only"|"unknown"; trustLevel: "untrusted"|"reviewed"|"verified"; provenance: { retrievedAt: string; extractionMethod: "manual"|"metadata-import"|"approved-scraper"; sourceNotes?: string }; createdAt: string; updatedAt: string; }
```

## Field definitions

| Field | Required | Definition |
|---|---|---|
| `id` | yes | Stable unique identifier string. |
| `slug` | yes | kebab-case identifier: lowercase letters/digits separated by single hyphens (`^[a-z0-9]+(-[a-z0-9]+)*$`). |
| `title` | yes | Public page/video/track title. |
| `artist` | no | Artist/author/channel as publicly displayed. |
| `sourceUrl` | yes | Valid http(s) URL of the source. |
| `canonicalUrl` | no | Canonicalized form of the source URL (see scraping-policy.md). |
| `sourceType` | yes | One of: `web-page`, `youtube-video`, `manual-entry`, `user-upload`, `documentation`, `github-repository`, `pdf`. |
| `publisher` | no | Publisher/label/channel as publicly displayed. |
| `releaseDate` | no | Public release date, ISO date string. |
| `durationSeconds` | no | Duration where publicly displayed; number >= 0. |
| `themes` | yes | High-level thematic descriptors; deduplicated, trimmed strings. |
| `tags` | yes | Public tags/categories; deduplicated, trimmed strings. |
| `contentRating` | yes | `clean`, `explicit`, or `unknown` (when not publicly identified). |
| `structure` | yes | Ordered broad structural descriptors; each one of `intro`, `verse`, `pre-hook`, `hook`, `bridge`, `outro`, `unknown`. Repetition is allowed (it is a sequence, not a set). |
| `musicAttributes.energy` | yes | `low`, `medium`, or `high`. |
| `musicAttributes.tempoBpmRange` | no | `[min, max]`; both positive, min <= max. |
| `musicAttributes.moods` | yes | Broad mood words; deduplicated, trimmed. |
| `musicAttributes.vocalFormats` | yes | Broad vocal formats (e.g. "rap", "sung", "spoken"); deduplicated, trimmed. |
| `musicAttributes.instrumentation` | yes | Broad instrumentation descriptors; deduplicated, trimmed. |
| `originalSynopsis` | no | Short high-level summary written in ORIGINAL language — never copied text. |
| `rightsStatus` | yes | `owned`, `licensed`, `public-metadata-only`, or `unknown`. See rights-policy.md. |
| `trustLevel` | yes | `untrusted`, `reviewed`, or `verified`. Every web/video import defaults to `untrusted`. |
| `provenance.retrievedAt` | yes | ISO timestamp of retrieval. |
| `provenance.extractionMethod` | yes | `manual`, `metadata-import`, or `approved-scraper`. |
| `provenance.sourceNotes` | no | Free-text provenance notes. |
| `createdAt` / `updatedAt` | yes | ISO timestamps for record lifecycle. |

## Validation rules

- `slug` is kebab-case; `sourceUrl` is a valid http(s) URL.
- `durationSeconds` >= 0; BPM values positive and min <= max.
- String arrays (`themes`, `tags`, `moods`, `vocalFormats`, `instrumentation`) deduplicated and trimmed.
- Records with `rightsStatus` `unknown` or `public-metadata-only` REJECT any of: `fullLyrics`, `lyrics`, `transcript`, `audioFile`, `videoFile`, `audioUrl`, `stems`. Presence of copyrighted expressive-content fields requires `rightsStatus` `owned` or `licensed`.
- Every web/video import defaults `trustLevel` `"untrusted"`.
- `sourceUrl` + `provenance.retrievedAt` are required.

## Complete valid example

```json
{
  "id": "cat-0001",
  "slug": "git-push-anthem",
  "title": "Git Push Anthem",
  "artist": "DropTable Records",
  "sourceUrl": "https://www.youtube.com/watch?v=abc123XYZ90",
  "canonicalUrl": "https://www.youtube.com/watch?v=abc123XYZ90",
  "sourceType": "youtube-video",
  "publisher": "DropTable Records",
  "releaseDate": "2026-07-04",
  "durationSeconds": 187,
  "themes": ["version control", "developer life"],
  "tags": ["tech-rap", "viral"],
  "contentRating": "clean",
  "structure": ["intro", "verse", "hook", "verse", "hook", "outro"],
  "musicAttributes": {
    "energy": "high",
    "tempoBpmRange": [140, 150],
    "moods": ["playful", "triumphant"],
    "vocalFormats": ["rap"],
    "instrumentation": ["808s", "synth lead"]
  },
  "originalSynopsis": "An upbeat rap that frames the git push as the victory moment of a developer's day, celebrating shipped code over perfect code.",
  "rightsStatus": "owned",
  "trustLevel": "reviewed",
  "provenance": {
    "retrievedAt": "2026-08-23T00:00:00+00:00",
    "extractionMethod": "manual",
    "sourceNotes": "Entered by label staff from the official upload."
  },
  "createdAt": "2026-08-23T00:00:00+00:00",
  "updatedAt": "2026-08-23T00:00:00+00:00"
}
```
