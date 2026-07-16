from proofwright.graph import articulation_points, build_graph
from proofwright.parse import load_wiki


def test_triangle_has_no_cut_vertex(good_config):
    wiki = load_wiki(good_config)
    graph = build_graph(wiki)
    # index->page-a, index->page-b, page-a->page-b forms a triangle
    assert articulation_points(graph.undirected()) == set()


def test_path_graph_middle_is_cut_vertex():
    # a - b - c : removing b disconnects a from c
    adj = {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}
    assert articulation_points(adj) == {"b"}


def test_phantom_target_detected(broken_config):
    wiki = load_wiki(broken_config)
    graph = build_graph(wiki)
    assert "ghost" in graph.phantom_targets
