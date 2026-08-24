---
name: viral-song-briefing
description: "Creates rights-aware original song-production briefs from user-owned, licensed, or public-metadata-only references. Use when turning approved music references and product requirements into a neutral, original creative brief without artist imitation or lyric copying."
---

# Viral Song Briefing

Turns approved catalog references plus product requirements into an ORIGINAL
song-production brief (`OriginalSongBrief`). Everything in the brief is new
creative direction expressed in neutral attributes — never imitation of a
named artist, never reuse of existing lyrics, melodies, or recordings.

## Workflow

1. Read `references/briefing-schema.md` for the `OriginalSongBrief` schema and a valid example.
2. Read `references/rights-policy.md` and apply it to every reference record.
3. Validate all selected reference records: `rightsStatus` must be one of
   `owned`, `licensed`, `public-metadata-only`, `unknown`; records with
   `unknown` or `public-metadata-only` rights must carry NO expressive-content
   fields (lyrics, transcript, audio/video files, stems).
4. If a reference's rights are `unknown`, use only its high-level metadata and
   themes — nothing expressive.
5. Normalize any style request into neutral production attributes using the
   transformation table in `references/style-normalization.md`.
6. Reject or rewrite any request to imitate a named artist or copy a specific
   song. Rewrites become neutral genre/energy/tempo/mood attributes, and each
   rewrite is recorded in `provenance.safetyTransformations`.
7. Generate the original brief: concept summary, one-line original hook
   concept (a concept, not lyrics), section map, lyrical and production
   constraints, neutral style attributes.
8. Include full provenance (`referenceSources`, `generatedAt`), rights notes,
   and every `safetyTransformations` entry. Output contracts are in
   `references/output-contract.md`.
9. For a repository or pull-request roast, read
   `references/pr-satire-briefing.md`. It defines the evidence, privacy, and
   section rules for the first two verses and reviewer/maintainer bridge.

Scripts: `scripts/build_brief.py catalog-record.json requirements.json`
builds a brief; `scripts/validate_brief.py brief.json` validates one. Both
are stdlib-only, offline, and print machine-readable JSON.

## Hard NEVERs

- NEVER copy lyrics — not full, not partial, not paraphrased-close.
- NEVER generate "sound exactly like [artist]" instructions.
- NEVER instruct voice-cloning of a named artist.
- NEVER recreate a specific copyrighted composition, beat, or melody.
- NEVER claim permissions that are not recorded in the reference's rights status.

## DropTable integration

`neutralStyleAttributes` flatten into an ACE-Step caption string — genre,
mood, instruments, tempo, vocal type, comma-separated, same format as the
preset strings in `pipeline/presets.py` (e.g. "upbeat rap-pop, playful,
808 bass, synth lead, 95-110 bpm, rhythmic male vocals"). `lyricalConstraints`
feed the lyricist system prompt.

For GitHub pull requests, use GitHub REST metadata as the primary source of
truth. A public GitHub login, PR author, merger, organisation/repository
one-liner, title, file counts, review states, and unchecked tasks may inform
the song when supplied. Do not crawl LinkedIn, social networks, or unrelated
personal pages; do not invent a missing reviewer concern or personal detail.
