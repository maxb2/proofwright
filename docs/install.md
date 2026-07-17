# Installation

Proofwright requires **Python 3.11+**.

## Install

=== "uv"

    ```sh
    uv add proofwright
    ```

=== "pip"

    ```sh
    pip install proofwright
    ```

This installs two console scripts — `proofwright` and its short alias `pw` — plus the
importable `proofwright` library.

Runtime dependencies are intentionally light: `PyYAML` (frontmatter) and `Jinja2` (index
templating).

## Optional: dense vector retrieval

The `search` command works out of the box with two deterministic streams (BM25 + graph).
An optional third stream adds dense vector similarity via static embeddings — numpy-only,
no torch, and bit-deterministic. Install the extra:

=== "uv"

    ```sh
    uv add 'proofwright[vector]'
    ```

=== "pip"

    ```sh
    pip install 'proofwright[vector]'
    ```

This pulls in `numpy` and `model2vec`. Enable it under `[retrieval.vector]` in
`wiki.toml` — see [Retrieval](retrieval.md) and [Configuration](configuration.md).

## Verify

```sh
pw --help
```

Next: [Getting started](getting-started.md).
