"""Retrieval orchestrator: BM25 + graph → RRF → (optional) rerank.

A deterministic pipeline. It generates candidates from two independent streams, fuses them
with reciprocal rank fusion, then hands the top slice to a reranker (identity by default). The
LLM, if any, only touches the last step and only as an injected tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import WikiConfig
from ..graph import build_graph
from ..model import Page, Wiki
from .bm25 import BM25Index
from .embed import Embedder, load_embedder
from .fusion import rrf_fuse
from .graph_expand import graph_candidates
from .rerank import IdentityReranker, Reranker
from .tokenize import tokenize
from .vector import VectorIndex


@dataclass
class RetrievalResult:
    slug: str
    score: float  # fused RRF score
    page: Page | None = None
    # Provenance: stream name -> this slug's 0-based rank within that stream.
    streams: dict[str, int] = field(default_factory=dict)


def search(
    wiki: Wiki,
    cfg: WikiConfig,
    query: str,
    reranker: Reranker | None = None,
    embedder: Embedder | None = None,
) -> list[RetrievalResult]:
    """Rank ``wiki`` pages against ``query`` and return the top ``retrieval.top_n`` results.

    ``embedder`` overrides the configured vector backend (mainly for tests); when omitted and
    ``retrieval.vector.enabled`` is set, one is built from config. The vector stream is skipped
    entirely when no embedder is available, leaving output identical to the BM25 + graph baseline.
    """
    rc = cfg.retrieval
    reranker = reranker or IdentityReranker()
    embedder = embedder or load_embedder(rc.vector)
    query_tokens = tokenize(query, rc.min_token_len)

    # Stream 1: BM25 exact-term ranking.
    bm25 = BM25Index(wiki.pages, k1=rc.bm25_k1, b=rc.bm25_b, min_token_len=rc.min_token_len)
    bm25_ranked = bm25.search(query_tokens)[: rc.candidate_limit]
    bm25_slugs = [slug for slug, _ in bm25_ranked]

    # Stream 2: graph expansion seeded by the top BM25 hits.
    graph = build_graph(wiki)
    seeds = bm25_slugs[: rc.seed_count]
    graph_ranked = graph_candidates(seeds, graph, hops=rc.graph_hops, decay=rc.graph_decay)
    graph_ranked = graph_ranked[: rc.candidate_limit]
    graph_slugs = [slug for slug, _ in graph_ranked]

    # Per-stream rank lookups for provenance.
    stream_ranks = {"bm25": bm25_slugs, "graph": graph_slugs}
    rankings = [bm25_slugs, graph_slugs]

    # Stream 3 (optional): dense vector similarity.
    if embedder is not None:
        vector_ranked = VectorIndex(wiki.pages, embedder).search(query)[: rc.vector.candidate_limit]
        vector_slugs = [slug for slug, _ in vector_ranked]
        stream_ranks["vector"] = vector_slugs
        rankings.append(vector_slugs)

    fused = rrf_fuse(rankings, k=rc.rrf_k)
    results: list[RetrievalResult] = []
    for slug, score in fused:
        streams = {name: order.index(slug) for name, order in stream_ranks.items() if slug in order}
        results.append(
            RetrievalResult(slug=slug, score=score, page=wiki.page(slug), streams=streams)
        )

    # Rerank the top slice, then truncate to top_n.
    top = reranker(query, results[: rc.top_n], wiki, cfg)
    return top[: rc.top_n]
