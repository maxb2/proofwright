# Wiki schema (starter)

This file is the conventions contract the ingest/query agent follows. Proofwright reads it
to learn which pages are **canonical** — every `[[slug]]` linked below must have a page
file, or the `missing-page` check fails.

## Canonical pages

- [[index]]

## Conventions (enforced deterministically by Proofwright)

- Every claim in a page body cites a source with a bracketed marker `[n]`.
- The page's `## References` section maps each `[n]` to an immutable file in `raw/`.
- Every source carries a reliability grade from the fixed vocabulary in `wiki.toml`.
- Pages carry frontmatter with the required keys; the index is generated, never hand-edited.

## Conventions (LLM judgement — out of Proofwright's scope)

- Synthesis across sources, summarization at ingest, meaning-level contradiction
  resolution, and supersession of stale claims. See `SKILL.md`.
