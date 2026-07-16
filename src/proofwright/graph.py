"""Deterministic link graph (pass 1) and graph-aware health checks.

Pass 1 uses only explicit ``[[wikilinks]]``. Semantic / implied links are a deferred
LLM pass 2 and are out of scope here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import Wiki


@dataclass
class LinkGraph:
    # slug -> set of existing target slugs it links to (edges to missing pages excluded)
    adjacency: dict[str, set[str]] = field(default_factory=dict)
    # slug -> inbound count over ALL wikilink targets (existing or not)
    inbound: dict[str, int] = field(default_factory=dict)
    # target slugs referenced by a link but with no page file
    phantom_targets: set[str] = field(default_factory=set)

    def undirected(self) -> dict[str, set[str]]:
        adj: dict[str, set[str]] = {n: set() for n in self.adjacency}
        for a, targets in self.adjacency.items():
            for b in targets:
                adj[a].add(b)
                adj.setdefault(b, set()).add(a)
        return adj


def build_graph(wiki: Wiki) -> LinkGraph:
    graph = LinkGraph()
    for page in wiki.pages:
        graph.adjacency.setdefault(page.slug, set())
    for page in wiki.pages:
        for link in page.links:
            target = link.target_slug
            graph.inbound[target] = graph.inbound.get(target, 0) + 1
            if wiki.has_page(target):
                if target != page.slug:
                    graph.adjacency[page.slug].add(target)
            else:
                graph.phantom_targets.add(target)
    return graph


def articulation_points(adj: dict[str, set[str]]) -> set[str]:
    """Cut vertices of the undirected graph (Tarjan/Hopcroft), iterative DFS.

    A cut vertex is a "fragile bridge": removing it disconnects part of the graph.
    """
    disc: dict[str, int] = {}
    low: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    cuts: set[str] = set()
    timer = 0

    for start in adj:
        if start in disc:
            continue
        # iterative DFS; stack holds (node, iterator over neighbours)
        root_children = 0
        parent[start] = None
        stack = [(start, iter(sorted(adj[start])))]
        disc[start] = low[start] = timer
        timer += 1
        while stack:
            node, it = stack[-1]
            advanced = False
            for nb in it:
                if nb not in disc:
                    parent[nb] = node
                    disc[nb] = low[nb] = timer
                    timer += 1
                    if node == start:
                        root_children += 1
                    stack.append((nb, iter(sorted(adj[nb]))))
                    advanced = True
                    break
                elif nb != parent[node]:
                    low[node] = min(low[node], disc[nb])
            if not advanced:
                stack.pop()
                if stack:
                    p = stack[-1][0]
                    low[p] = min(low[p], low[node])
                    if parent[p] is not None and low[node] >= disc[p]:
                        cuts.add(p)
        if root_children > 1:
            cuts.add(start)
    return cuts
