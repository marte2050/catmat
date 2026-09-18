from __future__ import annotations

from collections.abc import Sequence

from fastembed import SparseTextEmbedding, TextEmbedding

from catmat.core.config import settings


class Embedder:
    def __init__(
        self,
        *,
        dense_model: str | None = None,
        sparse_model: str | None = None,
        language: str | None = None,
        threads: int | None = None,
    ) -> None:
        self.dense_model_name = dense_model or settings.embedding_model
        self.sparse_model_name = sparse_model or settings.embedding_sparse_model
        self.language = language or settings.embedding_language
        self._dense = TextEmbedding(model_name=self.dense_model_name, threads=threads)
        self._sparse = SparseTextEmbedding(
            model_name=self.sparse_model_name,
            threads=threads,
            language=self.language,
        )

    def passage_embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._dense.passage_embed(list(texts))]

    def query_embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._dense.query_embed(list(texts))]

    def sparse_embed(self, texts: Sequence[str]):
        return list(self._sparse.embed(list(texts)))
