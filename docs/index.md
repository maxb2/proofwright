# Proofwright

Deterministic, zero-LLM structural tooling for an **LLM Wiki** — the Karpathy
`raw/ → LLM → wiki/` research-synthesis pattern.

Proofwright is the *deterministic layer*: it **checks the wiki against invariants** and
rebuilds derived artifacts, but never authors content. A "wright" is a maker/keeper — it
builds the index, link graph, and report, not just flags problems.

Everything semantic (synthesis, meaning-level contradiction, supersession) stays with the
LLM and is out of scope by design. See [Concepts](concepts.md) for the why.

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

See the full [Checks](checks.md) reference for what each check flags and why.

## Quickstart

```sh
uv add proofwright                    # or: pip install proofwright
```

```sh
pw check --config wiki.toml           # run all checks → report
pw index --write                      # regenerate the table of contents
pw graph                              # link-graph health report
pw search "your query"                # rank pages (BM25 + graph, RRF)
```

Invoke as `proofwright` or the short alias `pw`. Every subcommand defaults to
`--config wiki.toml`. Full details in the [CLI reference](cli.md).

## Design stance

`proofwright` is a *library, not a framework*: all per-wiki variance (paths, vocabularies,
thresholds) lives in `wiki.toml`; custom rules register via the plugin hook. No
subject-matter knowledge lives in the package.

- [Configuration](configuration.md) — the full `wiki.toml` reference.
- [Retrieval](retrieval.md) — how `search` fuses BM25 + graph expansion.
- [Extending](extending.md) — register your own checks.
- [API reference](api/model.md) — the library surface.
