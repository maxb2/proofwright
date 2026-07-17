"""Command-line interface: ``proofwright check | lint | index | graph | search``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .graph import build_graph
from .index import render_index, write_index
from .parse import load_wiki
from .report import Report
from .retrieval import search
from .runner import build_registry, run_checks


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", default="wiki.toml", help="path to wiki.toml (default: ./wiki.toml)")
    p.add_argument("--format", choices=["text", "json"], default="text", help="report format")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofwright", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("check", "lint"):  # lint is an alias
        p = sub.add_parser(name, help="run all registered checks")
        _add_common(p)

    p_index = sub.add_parser("index", help="regenerate or verify the index")
    p_index.add_argument("--config", default="wiki.toml")
    group = p_index.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="fail if index is stale (default)")
    group.add_argument("--write", action="store_true", help="rewrite the index file")

    p_graph = sub.add_parser("graph", help="print a link-graph health report")
    _add_common(p_graph)

    p_search = sub.add_parser("search", help="rank pages against a query (BM25 + graph, RRF)")
    p_search.add_argument("query", help="free-text query")
    _add_common(p_search)
    p_search.add_argument("--top-n", type=int, default=None, help="override retrieval.top_n")

    return parser


def _cmd_check(args) -> int:
    cfg = load_config(args.config)
    wiki, report = run_checks(cfg)
    _emit(report, args.format, cfg.root)
    return report.exit_code(cfg.checks.fail_on)


def _cmd_index(args) -> int:
    cfg = load_config(args.config)
    wiki = load_wiki(cfg)
    if args.write:
        write_index(wiki, cfg)
        print(f"wrote {cfg.index_path.relative_to(cfg.root)}")
        return 0
    expected = render_index(wiki, cfg)
    actual = cfg.index_path.read_text(encoding="utf-8") if cfg.index_path.exists() else ""
    if actual.strip() == expected.strip():
        print("index is up to date.")
        return 0
    print("index is STALE — run `proofwright index --write`.", file=sys.stderr)
    return 1


def _cmd_graph(args) -> int:
    cfg = load_config(args.config)
    wiki = load_wiki(cfg)
    graph = build_graph(wiki)
    report = Report()
    graph_checks = {"phantom-hub", "hub-stub", "fragile-bridge"}
    registry = build_registry(cfg)
    for check in registry.enabled(cfg):
        if check.id in graph_checks:
            report.extend(check(wiki, cfg))
    _emit(report, args.format, cfg.root)
    print(
        f"\n{len(wiki.pages)} pages, "
        f"{sum(len(a) for a in graph.adjacency.values())} internal links, "
        f"{len(graph.phantom_targets)} phantom targets.",
        file=sys.stderr,
    )
    return 0


def _cmd_search(args) -> int:
    cfg = load_config(args.config)
    if args.top_n is not None:
        cfg.retrieval.top_n = args.top_n
    wiki = load_wiki(cfg)
    results = search(wiki, cfg, args.query)
    if args.format == "json":
        payload = [
            {
                "slug": r.slug,
                "score": r.score,
                "title": (r.page.frontmatter.get("title") if r.page else None),
                "path": (r.page.path.relative_to(cfg.root).as_posix() if r.page else None),
                "streams": r.streams,
            }
            for r in results
        ]
        print(json.dumps(payload, indent=2))
    elif not results:
        print("no matches.")
    else:
        for r in results:
            streams = ",".join(sorted(r.streams)) or "-"
            print(f"{r.score:.4f}  {r.slug}  [{streams}]")
    return 0


def _emit(report: Report, fmt: str, root: Path) -> None:
    if fmt == "json":
        print(report.to_json())
    else:
        print(report.to_text(root))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in ("check", "lint"):
        return _cmd_check(args)
    if args.command == "index":
        return _cmd_index(args)
    if args.command == "graph":
        return _cmd_graph(args)
    if args.command == "search":
        return _cmd_search(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
