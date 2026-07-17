"""Embedding backends for the dense vector stream.

The engine depends only on the :class:`Embedder` protocol — ``encode(texts) -> matrix`` of
L2-normalized rows — so the concrete backend is a swappable config knob. The default is
model2vec (static embeddings: numpy-only, no torch, bit-deterministic). onnx or
sentence-transformers backends can be added here without touching the engine.

All heavy imports (numpy, model2vec) are deferred into function/method bodies so importing this
module never requires the optional ``vector`` extra.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import numpy as np

    from ..config import VectorConfig


@runtime_checkable
class Embedder(Protocol):
    """Turn texts into embedding vectors."""

    def encode(self, texts: list[str]) -> "np.ndarray":
        """Return an ``(len(texts), dim)`` float array of L2-normalized rows."""
        ...


def _normalize(matrix: "np.ndarray") -> "np.ndarray":
    """L2-normalize rows; zero rows are left as zeros (they contribute no similarity)."""
    import numpy as np

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (matrix / norms).astype("float32")


class Model2VecEmbedder:
    """Static-embedding backend backed by a model2vec ``StaticModel``.

    The model (a HuggingFace id or a local directory) is loaded lazily on first ``encode`` so
    construction is cheap and import-safe.
    """

    def __init__(self, model: str) -> None:
        self.model = model
        self._static = None  # loaded on first encode

    def _load(self):
        if self._static is None:
            from model2vec import StaticModel

            self._static = StaticModel.from_pretrained(self.model)
        return self._static

    def encode(self, texts: list[str]) -> "np.ndarray":
        import numpy as np

        if not texts:
            return np.zeros((0, 0), dtype="float32")
        vectors = np.asarray(self._load().encode(texts), dtype="float32")
        return _normalize(vectors)


def load_embedder(vc: "VectorConfig") -> Embedder | None:
    """Build the configured embedder, or ``None`` when the vector stream is disabled.

    Raises a clear error if the stream is enabled but its dependencies or backend are missing.
    """
    if not vc.enabled:
        return None
    if vc.backend == "model2vec":
        try:
            import model2vec  # noqa: F401  (probe the optional dependency)
            import numpy  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "the vector stream is enabled but its dependencies are missing; "
                "install them with: pip install 'proofwright[vector]'"
            ) from exc
        return Model2VecEmbedder(vc.model)
    raise ValueError(f"unknown vector backend: {vc.backend!r}")
