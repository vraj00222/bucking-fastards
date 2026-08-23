# Source Review Queue

The source queue is a pre-catalog intake list. Every row is a **Source
Record**, never an approved song/catalog record.

Required review fields:

- source URL and canonical URL
- source title/name, source type, collection tags, and intake mode
- rights status and trust level
- extraction status, reviewer decision, rejection reason
- linked catalog record count and provenance timestamps

## Import rules

1. Canonicalize and deduplicate by canonical URL. Also flag matching title,
   publisher, and duration when available.
2. Begin with `trustLevel: untrusted` and `reviewerDecision: pending`.
3. Use `rightsStatus: public-metadata-only` for declared metadata-only sources;
   use `unknown` for discovery-only/unknown sources.
4. Do not create lyrics, transcripts, audio, video, stems, or expressive
   fields for `public-metadata-only` or `unknown` records.
5. Preserve the curated-import date separately from the date public metadata
   is actually fetched. A reviewer must approve a discovery lead and identify
   an official creator before it can become a catalog record.
