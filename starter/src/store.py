"""Persistent vector store using ChromaDB with cosine distance and metadata filtering."""
from pathlib import Path
from typing import Any
import chromadb
from .models import Chunk

ALLOWED_FILTER_FIELDS = {"document_id", "source", "page", "page_id", "part", "section", "strategy"}


class ChromaVectorStore:
    """Persistent ChromaDB vector store supporting idempotent upsert, obsolete-chunk cleanup, and metadata filters."""

    def __init__(self, persist_dir: str | Path, dimensions: int) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.dimensions = dimensions
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))

    def _collection_name(self, strategy: str) -> str:
        return f"day06_strategy_{strategy.lower()}"

    def get_collection(self, strategy: str):
        return self.client.get_or_create_collection(
            name=self._collection_name(strategy),
            metadata={"hnsw:space": "cosine", "dimensions": self.dimensions, "strategy": strategy},
        )

    def create_schema(self) -> None:
        """Ensure collections for strategies A, B, and C exist with cosine distance."""
        for strategy in ("A", "B", "C"):
            self.get_collection(strategy)

    def count(self, strategy: str) -> int:
        return self.get_collection(strategy).count()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> dict[str, int]:
        """Validate dimensions, remove obsolete chunks for updated documents, and upsert deterministically."""
        if len(chunks) != len(vectors):
            raise ValueError(f"chunks count ({len(chunks)}) != vectors count ({len(vectors)})")
        if not chunks:
            return {"upserted": 0, "removed_obsolete": 0, "total_in_collection": self.count(strategy)}

        for idx, vec in enumerate(vectors):
            if len(vec) != self.dimensions:
                raise ValueError(f"Vector {idx} dimension {len(vec)} != expected {self.dimensions}")

        collection = self.get_collection(strategy)
        new_ids = [c.chunk_id for c in chunks]
        new_id_set = set(new_ids)
        if len(new_id_set) != len(new_ids):
            raise ValueError("Duplicate chunk_id detected in batch")

        # Identify obsolete chunk IDs belonging to the same document_id(s) that are no longer in the current version
        doc_ids = sorted({c.document_id for c in chunks})
        removed_obsolete = 0
        for doc_id in doc_ids:
            existing = collection.get(where={"document_id": doc_id}, include=[])
            existing_ids = existing.get("ids", []) if existing else []
            obsolete_ids = [eid for eid in existing_ids if eid not in new_id_set]
            if obsolete_ids:
                collection.delete(ids=obsolete_ids)
                removed_obsolete += len(obsolete_ids)

        # Upsert in batches to stay well below SQLite variable limits
        batch_size = 250
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_vecs = vectors[i : i + batch_size]
            collection.upsert(
                ids=[c.chunk_id for c in batch_chunks],
                documents=[c.text for c in batch_chunks],
                embeddings=batch_vecs,
                metadatas=[
                    {
                        "document_id": str(c.document_id),
                        "source": str(c.source),
                        "page": int(c.page),
                        "page_id": str(c.metadata.get("page_id", f"{c.document_id}_p{c.page:03d}")),
                        "part": str(c.metadata.get("part", "OTHER")),
                        "section": str(c.metadata.get("section", "Khác")),
                        "chunk_index": int(c.metadata.get("chunk_index", 0)),
                        "char_len": int(c.metadata.get("char_len", len(c.text))),
                        "strategy": str(strategy),
                    }
                    for c in batch_chunks
                ],
            )

        return {
            "upserted": len(chunks),
            "removed_obsolete": removed_obsolete,
            "total_in_collection": collection.count(),
        }

    def search(
        self,
        strategy: str,
        query_vector: list[float],
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query ChromaDB with cosine distance and optional metadata filter; return top-k hits."""
        if len(query_vector) != self.dimensions:
            raise ValueError(f"Query vector dimension {len(query_vector)} != expected {self.dimensions}")

        where_clause: dict[str, Any] | None = None
        if filters:
            unknown = set(filters.keys()) - ALLOWED_FILTER_FIELDS
            if unknown:
                raise ValueError(f"Unsupported filter fields: {unknown}")
            if len(filters) == 1:
                k, v = next(iter(filters.items()))
                where_clause = {k: v}
            else:
                where_clause = {"$and": [{k: v} for k, v in filters.items()]}

        collection = self.get_collection(strategy)
        res = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]

        hits: list[dict[str, Any]] = []
        for rank, (cid, text, meta, dist) in enumerate(zip(ids, docs, metas, dists), start=1):
            # Chroma cosine distance = 1 - cosine_similarity
            cosine_sim = round(1.0 - float(dist), 6)
            hits.append(
                {
                    "rank": rank,
                    "chunk_id": cid,
                    "text": text,
                    "score": cosine_sim,
                    "cosine_distance": round(float(dist), 6),
                    "metadata": meta,
                }
            )
        return hits


# Keep PgVectorStore alias pointing to ChromaVectorStore so existing imports work seamlessly
PgVectorStore = ChromaVectorStore
