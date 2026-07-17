# Proofwright

Deterministic, zero-LLM structural tooling for an **LLM Wiki** — the Karpathy
`raw/ → LLM → wiki/` research-synthesis pattern.

Proofwright is the *deterministic layer*: it **checks the wiki against invariants** and
rebuilds derived artifacts, but never authors content. A "wright" is a maker/keeper — it
builds the index, link graph, and report, not just flags problems.

## What it checks

- **Structural** — orphan pages, missing pages, broken `[[wikilinks]]`, stale index,
  missing provenance.
- **Frontmatter** — required keys, types, allowed tag/grade vocabularies.
- **Citation integrity** — every `[n]` resolves to a source that maps to a real file in
  `raw/`; prose lacking a citation is flagged. *(The primary defense against
  hallucination-baking.)*
- **Source grades** — every source graded, grades from a fixed vocabulary.
- **Graph** — phantom hubs, hub stubs, fragile bridges.
- **Freshness** — stale-page candidate list from recency markers.

Everything semantic (synthesis, meaning-level contradiction, supersession) stays with the
LLM and is out of scope by design.

## Usage

```sh
uv run proofwright check --config wiki.toml            # run all checks → report
uv run proofwright check --format json                 # machine-readable findings
uv run proofwright index --check                        # is the committed index stale?
uv run proofwright index --write                        # regenerate the index
uv run proofwright graph                                # graph-health report
uv run proofwright search "your query"                  # rank pages (BM25 + graph, RRF)
uv run proofwright search "your query" --format json    # ranked results with provenance
```

Invoke as `proofwright` or the short alias `pw`. Every subcommand defaults to
`--config wiki.toml`.

| Subcommand | Purpose | Key flags |
| --- | --- | --- |
| `check` (alias `lint`) | Run every registered invariant check → report. The zero-LLM pre-flight. | `--format {text,json}`; exits nonzero on `[checks].fail_on` severities |
| `index` | Rebuild or verify the generated table of contents. | `--write` rewrites it; `--check` (default) fails if stale |
| `graph` | Link-graph health: phantom hubs, hub stubs, fragile bridges. | `--format {text,json}` |
| `search "<query>"` | Rank pages (BM25 + graph, RRF). | `--format {text,json}` for stream provenance; `--top-n N` overrides `[retrieval].top_n` |

## Retrieval

`search` ranks pages with two deterministic streams — **BM25** (exact terms) and **graph
expansion** (structural links, seeded by the top BM25 hits) — fused with reciprocal rank
fusion. Each result reports which stream surfaced it. Tune it under `[retrieval]` in
`wiki.toml`.

The LLM rerank of the top slice is a *bounded, injectable* step (a `Reranker` protocol);
the package default is a no-op, so `search` stays zero-LLM. A vector stream can fuse in
later without changing the fusion.

`proofwright` is a *library, not a framework*: all per-wiki variance (paths, vocabularies,
thresholds) lives in `wiki.toml`; custom rules register via the plugin hook. No
subject-matter knowledge lives in the package.

See `templates/` for a starter `wiki.toml`, `CLAUDE.md` schema, and page templates.
