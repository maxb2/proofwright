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
uv run proofwright graph --report                       # graph-health report
uv run proofwright search "your query"                  # rank pages (BM25 + graph, RRF)
uv run proofwright search "your query" --format json    # ranked results with provenance
```

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
