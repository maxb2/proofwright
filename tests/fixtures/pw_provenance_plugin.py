"""Example Proofwright plugin: frontmatter-sources provenance.

Wiki-specific, so it lives outside the core library and registers via the plugin hook.
It reads its own settings from a ``[frontmatter_sources]`` table in ``wiki.toml`` (exposed
to plugins as ``cfg.extra``):

    [plugins]
    modules = ["pw_provenance_plugin"]

    [frontmatter_sources]
    field = "sources"          # frontmatter list field of source paths
    type_field = "type"        # frontmatter key naming a page's type
    require_for = ["book"]     # page types that must carry at least one source

Checks that each listed source path exists (file or directory) and that pages of a
required type carry at least one source.
"""

from __future__ import annotations

from proofwright.report import Finding


def _settings(cfg):
    s = cfg.extra.get("frontmatter_sources", {})
    return (
        s.get("field", "sources"),
        s.get("type_field", "type"),
        set(s.get("require_for", [])),
    )


def _rel(wiki, path):
    try:
        return path.relative_to(wiki.root).as_posix()
    except ValueError:
        return str(path)


def check_frontmatter_sources(wiki, cfg):
    field, type_field, require_for = _settings(cfg)
    for page in wiki.pages:
        raw = page.frontmatter.get(field)
        entries = raw if isinstance(raw, list) else ([raw] if raw else [])
        entries = [e.strip() for e in entries if isinstance(e, str) and e.strip()]
        loc = _rel(wiki, page.path)
        if not entries:
            if page.frontmatter.get(type_field) in require_for:
                yield Finding(
                    "sources-missing",
                    "error",
                    f"page of type '{page.frontmatter.get(type_field)}' has no {field}",
                    loc,
                    1,
                )
            continue
        for entry in entries:
            if not (page.path.parent / entry).resolve().exists():
                yield Finding(
                    "sources-broken",
                    "error",
                    f"{field} entry '{entry}' does not exist",
                    loc,
                    1,
                )


def register(registry):
    registry.add("frontmatter-sources", "error", check_frontmatter_sources)
