"""BM25-Okapi ranking over wiki pages — the exact-term retrieval stream.

Pure Python, zero dependencies. The corpus unit is a :class:`~proofwright.model.Page`; its
text is the frontmatter ``title`` plus the body. Scores are deterministic; ties break by slug
so results are stable run to run.
"""

from __future__ import annotations

import math
from collections import Counter

from ..model import Page
from .pagetext import page_text
from .tokenize import tokenize


class BM25Index:
    """A BM25-Okapi index over a list of pages.

    ``k1`` controls term-frequency saturation, ``b`` the document-length normalization.
    """

    def __init__(
        self,
        pages: list[Page],
        k1: float = 1.5,
        b: float = 0.75,
        min_token_len: int = 2,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.min_token_len = min_token_len
        self.slugs: list[str] = [p.slug for p in pages]
        self._tf: list[Counter[str]] = []
        self._len: list[int] = []
        df: Counter[str] = Counter()
        for page in pages:
            tokens = tokenize(page_text(page), min_token_len)
            tf = Counter(tokens)
            self._tf.append(tf)
            self._len.append(len(tokens))
            df.update(tf.keys())
        n = len(pages)
        self.avgdl = (sum(self._len) / n) if n else 0.0
        # BM25 idf with the +1 guard so it never goes negative.
        self._idf: dict[str, float] = {
            term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()
        }

    def search(self, query_tokens: list[str]) -> list[tuple[str, float]]:
        """Rank every page against ``query_tokens``; best-first, slug-tie-broken.

        Pages with score 0 (no query term present) are omitted.
        """
        scored: list[tuple[str, float]] = []
        for i, slug in enumerate(self.slugs):
            tf = self._tf[i]
            dl = self._len[i]
            score = 0.0
            for term in query_tokens:
                f = tf.get(term, 0)
                if not f:
                    continue
                idf = self._idf.get(term, 0.0)
                denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += idf * (f * (self.k1 + 1)) / denom
            if score > 0:
                scored.append((slug, score))
        scored.sort(key=lambda x: (-x[1], x[0]))
        return scored
