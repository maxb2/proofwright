import json

import numpy as np

from proofwright.config import VectorConfig
from proofwright.cli import main
from proofwright.parse import load_wiki
from proofwright.retrieval import (
    BM25Index,
    IdentityReranker,
    RetrievalResult,
    VectorIndex,
    graph_candidates,
    load_embedder,
    rrf_fuse,
    search,
    tokenize,
)
from proofwright.graph import build_graph

from conftest import FIXTURES

MD = FIXTURES / "mini-wiki-md"


def _md_config():
    from proofwright import load_config

    return load_config(MD / "wiki.toml")


# --- tokenize ---------------------------------------------------------------------------


def test_tokenize_lowercases_and_drops_short():
    assert tokenize("The Book A, of X!") == ["the", "book", "of"]  # "a", "x" dropped (len<2)


def test_tokenize_min_len_override():
    assert tokenize("a of x", min_len=1) == ["a", "of", "x"]


# --- BM25 -------------------------------------------------------------------------------


def test_bm25_ranks_on_topic_page_first():
    wiki = load_wiki(_md_config())
    index = BM25Index(wiki.pages)
    ranked = index.search(tokenize("author books"))
    assert ranked, "expected at least one hit"
    # authors/auth-a says "Books by this author" + title "Auth A" -> strongest author match.
    assert ranked[0][0] == "authors/auth-a"


def test_bm25_omits_zero_score_and_is_deterministic():
    wiki = load_wiki(_md_config())
    index = BM25Index(wiki.pages)
    a = index.search(tokenize("book"))
    b = index.search(tokenize("book"))
    assert a == b
    assert all(score > 0 for _, score in a)


# --- graph expansion --------------------------------------------------------------------


def test_graph_expansion_pulls_linked_neighbor():
    wiki = load_wiki(_md_config())
    graph = build_graph(wiki)
    # book-a links to authors/auth-a; expanding from book-a must reach it.
    cands = dict(graph_candidates(["library/book-a"], graph, hops=2, decay=0.5))
    assert cands["library/book-a"] == 1.0  # seed at distance 0
    assert "authors/auth-a" in cands
    assert cands["authors/auth-a"] == 0.5  # one hop


def test_graph_expansion_respects_hops():
    adj_graph = build_graph(load_wiki(_md_config()))
    zero = graph_candidates(["library/book-a"], adj_graph, hops=0, decay=0.5)
    assert [slug for slug, _ in zero] == ["library/book-a"]


# --- RRF fusion -------------------------------------------------------------------------


def test_rrf_fuse_known_example():
    # x is rank0 in list1 and rank1 in list2 -> highest fused score.
    fused = rrf_fuse([["x", "y"], ["z", "x"]], k=60)
    slugs = [s for s, _ in fused]
    assert slugs[0] == "x"
    # x score = 1/61 + 1/62 ; y and z each appear once at rank0/rank1.
    scores = dict(fused)
    assert scores["x"] > scores["y"]
    assert scores["x"] > scores["z"]


def test_rrf_fuse_tie_breaks_by_slug():
    fused = rrf_fuse([["b", "a"]], k=60)  # different ranks, but check ordering stable
    assert [s for s, _ in fused] == ["b", "a"]
    tie = rrf_fuse([["b"], ["a"]], k=60)  # both rank0 -> equal score -> slug order
    assert [s for s, _ in tie] == ["a", "b"]


# --- engine -----------------------------------------------------------------------------


def test_search_returns_results_with_provenance():
    cfg = _md_config()
    wiki = load_wiki(cfg)
    results = search(wiki, cfg, "author books")
    assert results
    assert all(isinstance(r, RetrievalResult) for r in results)
    top = results[0]
    assert top.page is not None
    assert top.streams  # at least one stream contributed
    # bm25 rank is 0-based; the top result should be well-placed in bm25.
    assert "bm25" in top.streams


def test_search_respects_top_n():
    cfg = _md_config()
    cfg.retrieval.top_n = 1
    wiki = load_wiki(cfg)
    assert len(search(wiki, cfg, "book author summary")) == 1


def test_identity_reranker_is_noop():
    cfg = _md_config()
    wiki = load_wiki(cfg)
    baseline = search(wiki, cfg, "book")
    reranked = search(wiki, cfg, "book", reranker=IdentityReranker())
    assert [r.slug for r in baseline] == [r.slug for r in reranked]


# --- vector -----------------------------------------------------------------------------


class FakeEmbedder:
    """Deterministic, network-free embedder: hashed bag-of-tokens, L2-normalized.

    Semantically-close texts share tokens and therefore point in similar directions, which is
    enough to exercise the vector plumbing without downloading a real model.
    """

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    def encode(self, texts: list[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dim), dtype="float32")
        for row, text in enumerate(texts):
            for token in tokenize(text):
                matrix[row, hash(token) % self.dim] += 1.0
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms


def test_vector_index_ranks_and_is_deterministic():
    wiki = load_wiki(_md_config())
    index = VectorIndex(wiki.pages, FakeEmbedder())
    a = index.search("author books")
    b = index.search("author books")
    assert a == b  # deterministic
    assert a, "expected at least one hit"
    assert all(score > 0 for _, score in a)
    # best-first, slug-tie-broken ordering
    assert a == sorted(a, key=lambda x: (-x[1], x[0]))


def test_search_includes_vector_stream_when_enabled():
    cfg = _md_config()
    cfg.retrieval.vector.enabled = True
    wiki = load_wiki(cfg)
    results = search(wiki, cfg, "author books", embedder=FakeEmbedder())
    assert results
    assert any("vector" in r.streams for r in results)


def test_search_respects_top_n_with_vector():
    cfg = _md_config()
    cfg.retrieval.vector.enabled = True
    cfg.retrieval.top_n = 1
    wiki = load_wiki(cfg)
    assert len(search(wiki, cfg, "book author", embedder=FakeEmbedder())) == 1


def test_search_omits_vector_stream_by_default():
    cfg = _md_config()  # vector disabled by default
    wiki = load_wiki(cfg)
    results = search(wiki, cfg, "author books")
    assert results
    assert all("vector" not in r.streams for r in results)


def test_load_embedder_none_when_disabled():
    assert load_embedder(VectorConfig(enabled=False)) is None


# --- CLI --------------------------------------------------------------------------------


def test_cli_search_json(capsys):
    code = main(["search", "book", "--config", str(MD / "wiki.toml"), "--format", "json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert payload
    entry = payload[0]
    assert {"slug", "score", "title", "path", "streams"} <= entry.keys()


def test_cli_search_top_n_override(capsys):
    code = main(["search", "book author", "--config", str(MD / "wiki.toml"), "--top-n", "1"])
    assert code == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert len(lines) == 1
