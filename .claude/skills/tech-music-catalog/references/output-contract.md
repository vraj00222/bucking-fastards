# Output Contract

Every task produces exactly ONE JSON object with a `type` field, one of the three below.

## 1. `catalog-record`

A normalized `MusicCatalogRecord` (full shape in `catalog-schema.md`).

```json
{
  "type": "catalog-record",
  "record": { "...": "a complete MusicCatalogRecord, see catalog-schema.md example" }
}
```

Example:

```json
{
  "type": "catalog-record",
  "record": {
    "id": "cat-0001",
    "slug": "git-push-anthem",
    "title": "Git Push Anthem",
    "sourceUrl": "https://www.youtube.com/watch?v=abc123XYZ90",
    "sourceType": "youtube-video",
    "themes": ["version control"],
    "tags": ["tech-rap"],
    "contentRating": "clean",
    "structure": ["intro", "verse", "hook", "outro"],
    "musicAttributes": {
      "energy": "high",
      "moods": ["playful"],
      "vocalFormats": ["rap"],
      "instrumentation": ["808s"]
    },
    "rightsStatus": "public-metadata-only",
    "trustLevel": "untrusted",
    "provenance": { "retrievedAt": "2026-08-23T00:00:00+00:00", "extractionMethod": "manual" },
    "createdAt": "2026-08-23T00:00:00+00:00",
    "updatedAt": "2026-08-23T00:00:00+00:00"
  }
}
```

## 2. `source-research-summary`

Rights-aware research notes about a source — public metadata plus an original summary. No expressive content.

Payload shape: `source` (normalized intake object, see `source-schema.md`), `summary` (short ORIGINAL high-level summary), `key_metadata` (object of the allowed public fields found), `open_questions` (array of strings).

```json
{
  "type": "source-research-summary",
  "source": {
    "source_url": "https://youtu.be/abc123XYZ90?si=tracker",
    "canonical_url": "https://www.youtube.com/watch?v=abc123XYZ90",
    "source_type": "youtube-video",
    "title": "Git Push Anthem (Official Video)",
    "publisher": "DropTable Records",
    "retrieved_at": "2026-08-23T00:00:00+00:00",
    "rights_status": "public-metadata-only",
    "trust_level": "untrusted",
    "extraction_method": "manual",
    "notes": "Metadata read from the public watch page."
  },
  "summary": "High-energy tech-rap track about shipping code; hook-forward structure with a celebratory tone.",
  "key_metadata": { "durationSeconds": 187, "releaseDate": "2026-07-04" },
  "open_questions": ["Confirm rights status with the channel owner."]
}
```

## 3. `catalog-validation-report`

The result of validating a record (matches `scripts/validate_catalog.py` output plus the record id).

Payload shape: `recordId` (string or null), `valid` (bool), `errors` (array of strings), `warnings` (array of strings).

```json
{
  "type": "catalog-validation-report",
  "recordId": "cat-0001",
  "valid": false,
  "errors": ["slug must be kebab-case", "sourceUrl must be a valid http(s) URL"],
  "warnings": ["sourceType 'youtube-video' with trustLevel 'verified': confirm a human verified this import"]
}
```
