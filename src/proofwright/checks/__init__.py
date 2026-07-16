"""Check protocol and registry.

A **check** is a callable ``(Wiki, WikiConfig) -> Iterable[Finding]`` carrying an ``id``
and a default ``severity``. Built-in checks register at import; wiki-specific checks
register via :mod:`proofwright.plugins`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Protocol

from pathlib import Path

from ..config import WikiConfig
from ..model import Wiki
from ..report import Finding

CheckFn = Callable[[Wiki, WikiConfig], Iterable[Finding]]


def rel(wiki: Wiki, path: Path) -> str:
    """Render a path relative to the wiki root (posix), for finding locations."""
    try:
        return path.relative_to(wiki.root).as_posix()
    except ValueError:
        return str(path)


class Check(Protocol):
    id: str
    severity: str

    def __call__(self, wiki: Wiki, cfg: WikiConfig) -> Iterable[Finding]: ...


@dataclass
class _Check:
    id: str
    severity: str
    fn: CheckFn

    def __call__(self, wiki: Wiki, cfg: WikiConfig) -> Iterable[Finding]:
        return self.fn(wiki, cfg)


class Registry:
    def __init__(self) -> None:
        self._checks: dict[str, _Check] = {}

    def register(self, id: str, severity: str = "error"):
        """Decorator registering a function as a check with a default severity."""

        def deco(fn: CheckFn) -> CheckFn:
            self.add(id, severity, fn)
            return fn

        return deco

    def add(self, id: str, severity: str, fn: CheckFn) -> None:
        if id in self._checks:
            raise ValueError(f"duplicate check id: {id}")
        self._checks[id] = _Check(id=id, severity=severity, fn=fn)

    def clone(self) -> "Registry":
        """A fresh registry with the same checks — so per-run plugin loading is idempotent."""
        new = Registry()
        new._checks = dict(self._checks)
        return new

    def ids(self) -> list[str]:
        return sorted(self._checks)

    def enabled(self, cfg: WikiConfig) -> list[_Check]:
        disabled = set(cfg.checks.disabled)
        return [c for cid, c in sorted(self._checks.items()) if cid not in disabled]


# The built-in registry. Check modules import this and decorate their functions.
registry = Registry()


def load_builtins() -> Registry:
    """Import built-in check modules so they register, then return the registry."""
    from . import (  # noqa: F401
        citation,
        frontmatter,
        freshness,
        grade,
        graphlint,
        structural,
    )

    return registry
