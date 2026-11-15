"""Real local embedding adapter using SentenceTransformers."""
from pathlib import Path
from typing import Protocol
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[1] / ".venv" / "hf_cache"


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """SentenceTransformers local embedder; raises immediately on failure without mock fallback."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, batch_size: int = 64) -> None:
        if not model_name:
            raise ValueError("model_name must not be empty")
        self.model_name = model_name
        self.batch_size = batch_size
        DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        has_local_cache = any(DEFAULT_CACHE_DIR.glob("models--*"))
        self._model = SentenceTransformer(
            model_name,
            device="cpu",
            cache_folder=str(DEFAULT_CACHE_DIR),
            local_files_only=has_local_cache,
        )
        dim = self._model.get_embedding_dimension()
        if not dim or dim <= 0:
            raise RuntimeError(f"Could not determine embedding dimensions for {model_name}")
        self.dimensions: int = int(dim)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vecs = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return [v.tolist() for v in vecs]

    def embed_query(self, question: str) -> list[float]:
        if not question or not question.strip():
            raise ValueError("Query question must not be empty")
        vec = self._model.encode(
            [question.strip()],
            batch_size=1,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]
        return vec.tolist()
