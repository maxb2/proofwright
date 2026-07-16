"""Graph-aware structural lint: phantom hubs, hub stubs, fragile bridges.

All derived from the deterministic pass-1 link graph (explicit ``[[wikilinks]]`` only).
"""

from __future__ import annotations

from ..config import WikiConfig
from ..graph import articulation_points, build_graph
from ..model import Wiki
from ..report import Finding
from . import registry, rel


@registry.register("phantom-hub", severity="warn")
def phantom_hubs(wiki: Wiki, cfg: WikiConfig):
    graph = build_graph(wiki)
    threshold = cfg.graph.hub_min_inbound
    for target in sorted(graph.phantom_targets):
        inbound = graph.inbound.get(target, 0)
        if inbound >= threshold:
            yield Finding(
                check_id="phantom-hub",
                severity="warn",
                message=f"[[{target}]] is linked {inbound}× but has no page (phantom hub)",
                data={"target": target, "inbound": inbound},
            )


@registry.register("hub-stub", severity="warn")
def hub_stubs(wiki: Wiki, cfg: WikiConfig):
    graph = build_graph(wiki)
    for page in wiki.pages:
        inbound = graph.inbound.get(page.slug, 0)
        if inbound >= cfg.graph.hub_min_inbound and page.body_chars < cfg.graph.stub_max_chars:
            yield Finding(
                check_id="hub-stub",
                severity="warn",
                message=f"hub page ({inbound} inbound) is only {page.body_chars} chars (stub)",
                path=rel(wiki, page.path),
                line=1,
                data={"inbound": inbound, "chars": page.body_chars},
            )


@registry.register("fragile-bridge", severity="info")
def fragile_bridges(wiki: Wiki, cfg: WikiConfig):
    graph = build_graph(wiki)
    for slug in sorted(articulation_points(graph.undirected())):
        page = wiki.page(slug)
        yield Finding(
            check_id="fragile-bridge",
            severity="info",
            message="removing this page would disconnect part of the graph (fragile bridge)",
            path=rel(wiki, page.path) if page else None,
            line=1 if page else None,
            data={"slug": slug},
        )
