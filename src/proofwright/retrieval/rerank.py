"""The rerank seam — the one bounded, optional LLM touch-point in retrieval.

The deterministic pipeline produces fused candidates; a reranker may reorder the top slice
using judgment the code cannot supply. Per the design brief, the LLM is a *callable tool inside
a deterministic pipeline*, never the workflow controller — so the package ships only the
protocol and a no-op default. A real LLM-backed reranker lives in the semantic layer and is
injected into :func:`proofwright.retrieval.engine.search`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from ..config import WikiConfig
from ..model import Wiki

if TYPE_CHECKING:
    from .engine import RetrievalResult


class Reranker(Protocol):
    """Reorder (a prefix of) fused candidates for a query."""

    def __call__(
        self,
        query: str,
        results: list["RetrievalResult"],
        wiki: Wiki,
        cfg: WikiConfig,
    ) -> list["RetrievalResult"]: ...


class IdentityReranker:
    """Default reranker: returns candidates unchanged (keeps the pipeline deterministic)."""

    def __call__(
        self,
        query: str,
        results: list["RetrievalResult"],
        wiki: Wiki,
        cfg: WikiConfig,
    ) -> list["RetrievalResult"]:
        return results
