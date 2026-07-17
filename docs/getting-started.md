# Getting started

This walks through wiring Proofwright into a wiki and running your first check. It assumes
you have [installed](install.md) the package.

## 1. Lay out the wiki

A minimal wiki is three things — sources, pages, and a conventions file:

```text
my-wiki/
├── wiki.toml          # Proofwright config (this file's dir is the wiki root)
├── CLAUDE.md          # conventions the LLM follows when authoring
├── raw/               # immutable sources
│   └── source-a.md
└── wiki/              # LLM-owned pages
    ├── index.md       # generated table of contents
    └── page-a.md
```

The directory holding `wiki.toml` is the **wiki root**; every path in the config resolves
relative to it.

## 2. Add `wiki.toml`

Copy the starter config from the `templates/` directory of the repository and edit to taste.
Every value shown is a default — delete anything you don't override:

```sh
cp templates/wiki.toml.example my-wiki/wiki.toml
```

The full annotated file is on the [Configuration](configuration.md) page.

## 3. Scaffolding templates

The repo's `templates/` directory ships starter assets referenced by the config:

| Template                  | Purpose                                                       |
| ------------------------- | ------------------------------------------------------------- |
| `wiki.toml.example`       | Annotated starter config (all defaults shown).                |
| `CLAUDE.md`               | Conventions/schema the LLM follows when authoring pages.      |
| `page-template.md`        | Skeleton for a wiki page (frontmatter + References section).  |
| `index-template.md`       | Simple flat index template.                                   |
| `index-hierarchical.md`   | Jinja2 template for a nested index (`link_tree`).             |
| `SKILL.md`                | Stub for the semantic (LLM) layer that authors content.       |

## 4. Run your first check

From the wiki root:

```sh
pw check
```

Proofwright loads every page, runs all registered [checks](checks.md), and prints a report.
It exits nonzero when any finding matches a severity in `[checks].fail_on` (default:
`error`) — so `pw check` drops straight into CI as a pre-flight gate.

```sh
pw check --format json     # machine-readable findings
```

## 5. Keep derived artifacts fresh

```sh
pw index --check      # is the committed index stale? (default)
pw index --write      # regenerate it
pw graph              # link-graph health report
```

A `mini-wiki-good` and `mini-wiki-broken` fixture live under `tests/fixtures/` in the
repository — clone them to see a clean run versus a wall of findings.

Next: the full [CLI reference](cli.md).
