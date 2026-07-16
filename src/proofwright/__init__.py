"""Proofwright — deterministic, zero-LLM structural tooling for an LLM Wiki."""

from __future__ import annotations

from .config import WikiConfig, load_config
from .model import Citation, Page, Source, Wiki, WikiLink
from .parse import load_wiki
from .report import Finding, Report
from .runner import run_checks

__version__ = "0.1.0"

__all__ = [
    "WikiConfig",
    "load_config",
    "Wiki",
    "Page",
    "WikiLink",
    "Citation",
    "Source",
    "load_wiki",
    "Finding",
    "Report",
    "run_checks",
]
