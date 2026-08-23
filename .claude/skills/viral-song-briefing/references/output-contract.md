# Output Contracts

All script and workflow outputs are machine-readable JSON on stdout. Three
contract types:

## original-song-brief

The full `OriginalSongBrief` object (see `briefing-schema.md`). Emitted by
`scripts/build_brief.py`.

```json
{
  "id": "uuid",
  "title": "...",
  "allowedThemes": ["..."],
  "prohibitedThemes": ["..."],
  "brandVocabulary": ["..."],
  "contentRating": "clean|explicit|unknown",
  "referenceRecordIds": ["..."],
  "neutralStyleAttributes": { "genreFamily": ["..."], "energy": "low|medium|high", "tempoBpmRange": [95, 110], "moods": ["..."], "vocalFormat": ["..."], "instrumentation": ["..."], "hookFormat": ["..."], "structure": ["..."] },
  "conceptSummary": "...",
  "originalHookConcept": "one line, a concept, never lyrics",
  "sectionMap": ["..."],
  "lyricalConstraints": ["..."],
  "productionConstraints": ["..."],
  "rightsStatus": "owned|licensed|public-metadata-only|unknown",
  "provenance": { "referenceSources": ["..."], "generatedAt": "ISO 8601", "safetyTransformations": ["..."] }
}
```

## style-normalization-result

Result of normalizing one style request.

```json
{
  "input": "the original request text",
  "normalized": "the neutral, artist-independent rewrite",
  "transformations": [
    "named-artist -> neutral genre/energy/tempo attributes"
  ]
}
```

## rights-review

Result of reviewing one reference record's rights before use.

```json
{
  "recordId": "rec-001",
  "rightsStatus": "owned|licensed|public-metadata-only|unknown",
  "allowedUses": [
    "high-level metadata",
    "themes",
    "broad structural and music descriptors",
    "original thematic summary"
  ],
  "deniedUses": [
    "lyrics reuse",
    "audio/video reuse",
    "stems",
    "transcript reuse",
    "artist voice or style imitation"
  ]
}
```

## Error output

Scripts print `{"error": "..."}` (build) or
`{"valid": false, "errors": [...], "safetyFindings": [...]}` (validate) and
exit non-zero on invalid input.
