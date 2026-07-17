"""Reciprocal rank fusion (RRF).

Combines any number of ranked slug lists into one, using only each item's *rank* per stream
(not raw scores, which are not comparable across BM25 and graph). Generic over N streams, so a
future vector stream fuses in with no change here. Score for a slug is
``sum over streams of 1 / (k + rank)``.
"""

from __future__ import annotations


def rrf_fuse(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse ``rankings`` (each an ordered, best-first list of slugs) into one ranking.

    Returns ``(slug, score)`` best-first, slug-tie-broken. ``k`` damps the contribution of
    top ranks (the standard RRF constant is 60).
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, slug in enumerate(ranking):  # rank 0 = best
            scores[slug] = scores.get(slug, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))
