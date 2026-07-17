"""Graph-traversal candidate generation — the structural retrieval stream.

Given seed slugs (typically the top BM25 hits), expand along explicit ``[[wikilinks]]`` /
markdown links to surface structurally-related pages that lexical search missed. Scoring is
``decay ** distance`` so nearer neighbours rank higher; seeds sit at distance 0.
"""

from __future__ import annotations

from ..graph import LinkGraph


def graph_candidates(
    seeds: list[str],
    graph: LinkGraph,
    hops: int = 2,
    decay: float = 0.5,
) -> list[tuple[str, float]]:
    """BFS from ``seeds`` over the undirected link graph out to ``hops``.

    Returns ``(slug, score)`` best-first, slug-tie-broken. Each reachable page keeps the score
    of its shortest distance to any seed (``decay ** distance``).
    """
    adj = graph.undirected()
    best: dict[str, float] = {}
    frontier = {s for s in seeds if s in adj}
    for distance in range(hops + 1):
        if not frontier:
            break
        score = decay**distance
        nxt: set[str] = set()
        for slug in frontier:
            if slug not in best:  # first (shortest) time we reach it wins
                best[slug] = score
            for nb in adj.get(slug, ()):
                if nb not in best:
                    nxt.add(nb)
        frontier = nxt
    ranked = sorted(best.items(), key=lambda x: (-x[1], x[0]))
    return ranked
