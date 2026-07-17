"""Deterministic retrieval primitives: BM25 + graph candidates, RRF fusion, rerank seam.

Everything here is content-agnostic and (save the injectable reranker) zero-LLM. The public
entry point is :func:`search`.
"""

from __future__ import annotations

from .bm25 import BM25Index
from .engine import RetrievalResult, search
from .fusion import rrf_fuse
from .graph_expand import graph_candidates
from .rerank import IdentityReranker, Reranker
from .tokenize import tokenize

__all__ = [
    "search",
    "RetrievalResult",
    "BM25Index",
    "graph_candidates",
    "rrf_fuse",
    "tokenize",
    "Reranker",
    "IdentityReranker",
]
