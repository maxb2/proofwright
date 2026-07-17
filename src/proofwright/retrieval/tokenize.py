"""Tokenization for retrieval.

Deliberately regex-based and content-agnostic, matching :mod:`proofwright.parse`'s discipline
(no markdown engine, no stemming, no language model). Shared by the BM25 index and query
parsing so corpus and query are tokenized identically.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str, min_len: int = 2) -> list[str]:
    """Lowercase ``text`` and split into alphanumeric tokens shorter than ``min_len`` dropped."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= min_len]
