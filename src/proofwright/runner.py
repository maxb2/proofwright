"""Wire config → wiki → checks → report."""

from __future__ import annotations

from .checks import load_builtins
from .config import WikiConfig
from .model import Wiki
from .parse import load_wiki
from .plugins import load_plugins
from .report import Report


def build_registry(cfg: WikiConfig):
    """A fresh registry with built-ins + this wiki's plugins."""
    registry = load_builtins().clone()
    load_plugins(registry, cfg)
    return registry


def run_checks(cfg: WikiConfig) -> tuple[Wiki, Report]:
    registry = build_registry(cfg)
    wiki = load_wiki(cfg)
    report = Report()
    for check in registry.enabled(cfg):
        report.extend(check(wiki, cfg))
    return wiki, report
