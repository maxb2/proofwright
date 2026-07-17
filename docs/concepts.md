# Concepts

## The `raw/ → LLM → wiki/` pattern

An **LLM Wiki** follows a research-synthesis loop popularized by Andrej Karpathy:

- `raw/` — immutable source material. Papers, notes, transcripts, exports. Never edited.
- **LLM** — reads `raw/`, synthesizes understanding, and authors pages.
- `wiki/` — the LLM-owned knowledge base: interlinked pages with frontmatter, citations,
  and a generated index.

The value is the synthesis. The risk is that synthesis silently drifts from its sources —
broken links accumulate, citations point nowhere, the index goes stale, claims lose their
provenance and become indistinguishable from hallucination.

## The deterministic-vs-LLM boundary

Proofwright draws a hard line:

| Deterministic layer (Proofwright)        | Semantic layer (LLM)                          |
| ---------------------------------------- | --------------------------------------------- |
| Does every `[[wikilink]]` resolve?       | Is this page *correct*?                        |
| Does every `[n]` map to a real `raw/` file? | Does the cited source actually support the claim? |
| Is the committed index current?          | Should these two pages be merged?              |
| Which pages are past their staleness threshold? | Is this page's *meaning* out of date?    |

Everything on the left is a checkable invariant — decidable by code, bit-reproducible, and
zero-LLM. Everything on the right requires judgment and stays with the LLM.

Proofwright deliberately **never authors content and never judges meaning**. Freshness
checks, for example, list *candidates* (pages whose recency marker is old) — they do not
decide whether a page is actually stale. Citation coverage flags uncited prose as a
*candidate*, not a verdict on whether a sentence is a factual claim.

## Why a "wright"

A *wright* is a maker/keeper (wheelwright, shipwright). Proofwright does more than lint: it
**rebuilds derived artifacts** — the table-of-contents index, the link graph, the report.
It is the deterministic pre-flight that runs before (and independently of) any LLM step, so
regressions surface as a nonzero exit code in CI rather than as quiet knowledge rot.

## Library, not framework

All per-wiki variance — paths, vocabularies, thresholds, policies — lives in
[`wiki.toml`](configuration.md). No subject-matter knowledge lives in the package. Anything
a specific wiki needs that the core doesn't cover registers as a [plugin](extending.md). The
one optional LLM touch-point, the retrieval [reranker](retrieval.md), is an injectable seam
whose package default is a no-op — so the shipped tool stays zero-LLM end to end.
