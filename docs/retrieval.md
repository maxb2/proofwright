# Retrieval

`pw search "<query>"` ranks pages with deterministic retrieval primitives. Everything here is
content-agnostic and — save the injectable reranker — zero-LLM. The public entry point is
[`proofwright.retrieval.search`](api/retrieval.md).

## The streams

`search` runs two deterministic streams and fuses them:

- **BM25** — classic Okapi BM25 over tokenized page text. Surfaces pages that share exact
  terms with the query. Tuned by `bm25_k1` (term-frequency saturation) and `bm25_b`
  (document-length normalization).
- **Graph expansion** — seeds from the top BM25 hits (`seed_count`) and walks the
  `[[wikilink]]` graph outward `graph_hops` hops, decaying each hop by `graph_decay`.
  Surfaces structurally-related pages the query terms alone would miss.

Each stream caps its candidates at `candidate_limit` before fusion.

## Fusion

The streams fuse with **reciprocal rank fusion (RRF)** — each stream contributes
`1 / (rrf_k + rank)` per page, summed across streams. RRF needs no score calibration between
streams, so BM25 scores and graph-decay scores combine cleanly. `top_n` results are returned;
each carries provenance for which stream(s) surfaced it (visible in `--format json`, or the
`[streams]` column in text output).

## The rerank seam

The one bounded, optional LLM touch-point. The deterministic pipeline produces fused
candidates; a **`Reranker`** may reorder the top slice using judgment the code cannot supply.
Per the design stance, the LLM is a *callable tool inside a deterministic pipeline*, never the
workflow controller — so the package ships only the `Reranker` protocol and a no-op
`IdentityReranker` default. A real LLM-backed reranker lives in the semantic layer and is
injected into `search`. Out of the box, `search` is zero-LLM.

## Optional dense vector stream

A third stream adds dense vector similarity via **static embeddings** (model2vec) —
numpy-only, no torch, and bit-deterministic. It is off by default and requires the extra:

```sh
pip install 'proofwright[vector]'
```

Enable and configure it under `[retrieval.vector]`:

```toml
[retrieval.vector]
enabled = true                              # off by default; opt in here
backend = "model2vec"                       # static embeddings, deterministic
model = "minishlab/potion-retrieval-32M"    # HuggingFace id or local directory
candidate_limit = 50                        # per-stream cap before fusion
```

When enabled, the vector stream fuses in through the same RRF step — no change to the fusion
logic, just another ranked candidate list.

## Tuning reference

All knobs live under `[retrieval]` in [`wiki.toml`](configuration.md):

| Key | Default | Meaning |
| --- | --- | --- |
| `bm25_k1` | 1.5 | BM25 term-frequency saturation. |
| `bm25_b` | 0.75 | BM25 document-length normalization. |
| `rrf_k` | 60 | Reciprocal rank fusion damping constant. |
| `graph_hops` | 2 | How far graph expansion walks from the seeds. |
| `graph_decay` | 0.5 | Per-hop score decay for graph candidates. |
| `seed_count` | 10 | Top BM25 hits used to seed graph expansion. |
| `candidate_limit` | 50 | Per-stream cap before fusion. |
| `top_n` | 10 | Number of results returned (override per-run with `--top-n`). |
| `min_token_len` | 2 | Tokens shorter than this are dropped. |
