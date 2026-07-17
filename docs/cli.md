# CLI reference

Invoke as `proofwright` or the short alias `pw`. Every subcommand defaults to
`--config wiki.toml` (looked up relative to the current directory).

| Subcommand | Purpose | Key flags |
| --- | --- | --- |
| `check` (alias `lint`) | Run every registered invariant check → report. The zero-LLM pre-flight. | `--format {text,json}`; exits nonzero on `[checks].fail_on` severities |
| `index` | Rebuild or verify the generated table of contents. | `--write` rewrites it; `--check` (default) fails if stale |
| `graph` | Link-graph health: phantom hubs, hub stubs, fragile bridges. | `--format {text,json}` |
| `search "<query>"` | Rank pages (BM25 + graph, RRF). | `--format {text,json}`; `--top-n N` overrides `[retrieval].top_n` |

## Common flags

- `--config PATH` — path to `wiki.toml` (default `./wiki.toml`). Its parent directory is
  the wiki root.
- `--format {text,json}` — report format. `json` is machine-readable and carries stream
  provenance for `search`.

## `check` (alias `lint`)

```sh
pw check                       # run all checks → text report
pw check --format json         # machine-readable findings
```

Runs all registered checks and prints the report. **Exit code** is nonzero when any finding
matches a severity listed in `[checks].fail_on` (default `["error"]`) — so `check` is the CI
gate. `lint` is an exact alias.

## `index`

```sh
pw index --check       # default: fail if the committed index is stale
pw index --write       # regenerate wiki/index.md
```

`--check` and `--write` are mutually exclusive; `--check` is the default. On `--write`,
Proofwright renders the index (flat list, or your `index_template`) and writes it, printing
the path. On `--check`, it compares the rendered index against the committed file and exits
nonzero if they differ.

## `graph`

```sh
pw graph                 # link-graph health report
pw graph --format json
```

Runs the graph-aware checks (`phantom-hub`, `hub-stub`, `fragile-bridge`) and prints a
summary line to stderr: page count, internal link count, and phantom-target count.

## `search`

```sh
pw search "your query"                  # ranked results (BM25 + graph, RRF)
pw search "your query" --format json    # ranked results with stream provenance
pw search "your query" --top-n 20       # override retrieval.top_n
```

Ranks pages by fusing the BM25 and graph-expansion streams with reciprocal rank fusion. Text
output is `score  slug  [streams]`; JSON output adds title, path, and per-result stream
provenance. Tune ranking under `[retrieval]` — see [Retrieval](retrieval.md).
