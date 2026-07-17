"""Dense vector ranking over wiki pages — the semantic retrieval stream.

Mirrors :class:`~proofwright.retrieval.bm25.BM25Index`: the corpus unit is a page, its text is
:func:`~proofwright.retrieval.pagetext.page_text`, and scoring is deterministic with slug
tie-breaks. An injected :class:`~proofwright.retrieval.embed.Embedder` supplies L2-normalized
vectors, so cosine similarity is a plain dot product.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..model import Page
from .pagetext import page_text

if TYPE_CHECKING:
    from .embed import Embedder


class VectorIndex:
    """A dense-embedding index over a list of pages, ranked by cosine similarity."""

    def __init__(self, pages: list[Page], embedder: "Embedder") -> None:
        self.slugs: list[str] = [p.slug for p in pages]
        self._matrix = embedder.encode([page_text(p) for p in pages])
        self._embedder = embedder

    def search(self, query: str) -> list[tuple[str, float]]:
        """Rank every page against ``query``; best-first, slug-tie-broken.

        Pages with a non-positive similarity are omitted (cosine over normalized vectors).
        """
        if not self.slugs:
            return []
        query_vec = self._embedder.encode([query])[0]
        sims = self._matrix @ query_vec
        scored = [
            (slug, float(score)) for slug, score in zip(self.slugs, sims, strict=True) if score > 0
        ]
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored
