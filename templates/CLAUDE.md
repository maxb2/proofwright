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

## Tooling — running Proofwright

The deterministic layer runs via the `proofwright` CLI (short alias `pw`). In this repo
call it as `uv run pw ...`; once installed, just `pw ...`. Every subcommand reads config
from `--config wiki.toml` (the default), so plain `pw check` works from the wiki root.

- `pw check` (alias `lint`) — run every registered invariant check and print a report.
  This is the zero-LLM pre-flight: **run it after every ingest.** `--format json` emits
  machine-readable findings; the process exits nonzero when any finding hits a severity
  listed in `[checks].fail_on` (default `error`).
- `pw index --write` — rebuild the generated table of contents after adding, removing, or
  renaming pages. `pw index --check` (the default with no flag) fails if the committed
  index is stale — use it in CI. Never hand-edit the index.
- `pw graph` — print a link-graph health report (phantom hubs, hub stubs, fragile
  bridges).
- `pw search "<query>"` — rank pages for the Query op, fusing BM25 and graph expansion
  with RRF. `--format json` adds per-result stream provenance; `--top-n N` overrides
  `[retrieval].top_n`.

## Conventions (LLM judgement — out of Proofwright's scope)

- Synthesis across sources, summarization at ingest, meaning-level contradiction
  resolution, and supersession of stale claims. See `SKILL.md`.
