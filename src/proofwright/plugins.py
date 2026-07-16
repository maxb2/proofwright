"""Loading wiki-specific checks.

Two registration paths, per the design brief's "honest test of generality":

1. ``[plugins] modules`` in ``wiki.toml`` — dotted module paths, each exposing
   ``register(registry)``.
2. The ``proofwright.checks`` entry-point group — for installed third-party packages,
   each entry point resolving to a ``register(registry)`` callable.

A universal invariant ships in ``checks/`` core; anything wiki-specific registers here.
"""

from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from importlib import metadata

from .checks import Registry
from .config import WikiConfig


@contextmanager
def _wiki_on_syspath(cfg: WikiConfig):
    """Temporarily put the wiki root on sys.path so wiki-local plugins are importable."""
    root = str(cfg.root)
    added = root not in sys.path
    if added:
        sys.path.insert(0, root)
    try:
        yield
    finally:
        if added and root in sys.path:
            sys.path.remove(root)


def load_plugins(registry: Registry, cfg: WikiConfig) -> None:
    with _wiki_on_syspath(cfg):
        for dotted in cfg.plugins.modules:
            module = importlib.import_module(dotted)
            register = getattr(module, "register", None)
            if register is None:
                raise AttributeError(f"plugin module '{dotted}' has no register(registry)")
            register(registry)

    if cfg.plugins.load_entry_points:
        for ep in metadata.entry_points(group="proofwright.checks"):
            register = ep.load()
            register(registry)
