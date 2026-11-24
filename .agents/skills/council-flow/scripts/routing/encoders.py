"""Explicit encoder seams for optional local vector routing."""
from __future__ import annotations

from hashlib import sha256
import importlib
import math
from typing import Protocol


class Encoder(Protocol):
    encoder_id: str

    def encode(self, text: str) -> tuple[float, ...]:
        """Encode text into a bounded numeric vector."""


class HashEncoder:
    """Stable dependency-free encoder for deterministic tests and fixtures."""

    encoder_id = "hash-v1"

    def __init__(self, dimension: int) -> None:
        if not isinstance(dimension, int) or isinstance(dimension, bool) or not 1 <= dimension <= 1024:
            raise ValueError("encoder dimension must be an integer between 1 and 1024")
        self.dimension = dimension

    def encode(self, text: str) -> tuple[float, ...]:
        if not isinstance(text, str):
            raise ValueError("encoder input must be text")
        values = []
        counter = 0
        while len(values) < self.dimension:
            digest = sha256(f"{counter}:{text}".encode("utf-8")).digest()
            values.extend((byte / 127.5) - 1.0 for byte in digest)
            counter += 1
        vector = tuple(values[: self.dimension])
        if not any(vector):
            vector = (1.0,) + (0.0,) * (self.dimension - 1)
        return vector


class FastEmbedEncoder:
    """Lazy optional FastEmbed adapter; construction performs no import."""

    def __init__(self, model_name: str) -> None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("FastEmbed model name must be nonempty text")
        self.model_name = model_name
        self.encoder_id = "fastembed-" + model_name
        self._model = None

    def encode(self, text: str) -> tuple[float, ...]:
        if not isinstance(text, str):
            raise ValueError("encoder input must be text")
        if self._model is None:
            try:
                module = importlib.import_module("fastembed")
                text_embedding = module.TextEmbedding
            except (ImportError, AttributeError) as exc:
                raise ImportError("optional FastEmbed dependency is unavailable") from exc
            self._model = text_embedding(model_name=self.model_name)
        vector = tuple(float(value) for value in next(iter(self._model.embed([text]))))
        if not vector or any(not math.isfinite(value) for value in vector):
            raise ValueError("FastEmbed returned an invalid vector")
        return vector
