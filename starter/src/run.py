"""Pipeline entry point for Day 06 Data Ingestion & Retrieval Benchmark."""
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .chunking import by_paragraph, fixed_size
from .embeddings import DEFAULT_MODEL_NAME, MyEmbedder
from .evaluation import evaluate_query, summarize
from .ingestion import load_pdf
from .models import Chunk
from .store import ChromaVectorStore


def _compute_chunk_stats(chunks: list[Chunk]) -> dict[str, Any]:
    lengths = sorted(len(c.text) for c in chunks)
    word_counts = [len(c.text.split()) for c in chunks]
    n = len(lengths)
    if n == 0:
        return {}

    def pct(p: float) -> int:
        idx = min(n - 1, max(0, int(round(p * (n - 1)))))
        return lengths[idx]

    return {
        "num_chunks": n,
        "total_chars": sum(lengths),
        "total_words_approx_tokens": sum(word_counts),
        "char_len_min": lengths[0],
        "char_len_p25": pct(0.25),
        "char_len_median": int(statistics.median(lengths)),
        "char_len_mean": round(statistics.mean(lengths), 2),
        "char_len_p75": pct(0.75),
        "char_len_p95": pct(0.95),
        "char_len_max": lengths[-1],
    }


def main() -> None:
    root_dir = Path(__file__).resolve().parents[2]
    pdf_path = root_dir / "ruotoilaruot.pdf"
    questions_path = root_dir / "benchmark" / "questions.json"
    results_dir = root_dir / "results"
    chroma_dir = results_dir / "chroma_db"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("1. Loading and normalizing PDF corpus...")
    t0 = time.perf_counter()
    pages = load_pdf(
        pdf_path,
        document_id="ruot-oi-la-ruot",
        source="ruotoilaruot.pdf",
        log_path=results_dir / "ingestion_skipped_pages.json",
    )
    pdf_load_sec = round(time.perf_counter() - t0, 4)
    if len(pages) < 30:
        raise RuntimeError(f"Corpus has only {len(pages)} valid pages (< 30 minimum)")
    print(f"   Loaded {len(pages)} valid pages in {pdf_load_sec}s.")

    print("2. Building chunks for Strategies A, B, and C...")
    t_chunk_a = time.perf_counter()
    chunks_a: list[Chunk] = []
    for p in pages:
        chunks_a.extend(fixed_size(p, size=500, overlap=50, strategy="A"))
    chunk_time_a = round(time.perf_counter() - t_chunk_a, 4)

    t_chunk_b = time.perf_counter()
    chunks_b: list[Chunk] = []
    for p in pages:
        chunks_b.extend(by_paragraph(p, max_size=600, strategy="B"))
    chunk_time_b = round(time.perf_counter() - t_chunk_b, 4)

    # Strategy C uses the exact same chunking as B, with strategy label C
    chunks_c: list[Chunk] = [
        Chunk(
            chunk_id=c.chunk_id.replace("_B_", "_C_"),
            document_id=c.document_id,
            source=c.source,
            page=c.page,
            text=c.text,
            metadata={**c.metadata, "strategy": "C"},
        )
        for c in chunks_b
    ]

    print(f"   Strategy A chunks: {len(chunks_a)} | Strategy B/C chunks: {len(chunks_b)}")

    print(f"3. Initializing local embedding model ({DEFAULT_MODEL_NAME})...")
    t_model = time.perf_counter()
    embedder = MyEmbedder(DEFAULT_MODEL_NAME, batch_size=64)
    model_init_sec = round(time.perf_counter() - t_model, 4)
    print(f"   Loaded model ({embedder.dimensions} dims) in {model_init_sec}s.")

    print("4. Embedding chunks for Strategy A and Strategy B/C...")
    t_emb_a = time.perf_counter()
    vecs_a = embedder.embed_documents([c.text for c in chunks_a])
    embed_time_a = round(time.perf_counter() - t_emb_a, 4)
    print(f"   Embedded Strategy A ({len(vecs_a)} vectors) in {embed_time_a}s.")

    t_emb_b = time.perf_counter()
    vecs_b = embedder.embed_documents([c.text for c in chunks_b])
    embed_time_b = round(time.perf_counter() - t_emb_b, 4)
    # Strategy C shares identical chunk texts with B, so its vectors are identical
    vecs_c = vecs_b
    print(f"   Embedded Strategy B/C ({len(vecs_b)} vectors) in {embed_time_b}s.")

    print("5. Storing vectors in persistent ChromaDB and verifying idempotent re-ingestion...")
    store = ChromaVectorStore(persist_dir=chroma_dir, dimensions=embedder.dimensions)
    store.create_schema()

    t_up_a = time.perf_counter()
    up_a1 = store.upsert("A", chunks_a, vecs_a)
    upsert_time_a = round(time.perf_counter() - t_up_a, 4)
    # Re-ingest same version to verify no duplication
    up_a2 = store.upsert("A", chunks_a, vecs_a)
    assert up_a1["total_in_collection"] == up_a2["total_in_collection"] == len(chunks_a)

    t_up_b = time.perf_counter()
    up_b1 = store.upsert("B", chunks_b, vecs_b)
    upsert_time_b = round(time.perf_counter() - t_up_b, 4)
    up_b2 = store.upsert("B", chunks_b, vecs_b)
    assert up_b1["total_in_collection"] == up_b2["total_in_collection"] == len(chunks_b)

    t_up_c = time.perf_counter()
    up_c1 = store.upsert("C", chunks_c, vecs_c)
    upsert_time_c = round(time.perf_counter() - t_up_c, 4)
    up_c2 = store.upsert("C", chunks_c, vecs_c)
    assert up_c1["total_in_collection"] == up_c2["total_in_collection"] == len(chunks_c)

    # Test obsolete chunk cleanup when a document changes: insert 1 extra dummy chunk for the same document_id, then re-upsert B
    dummy_chunk = Chunk(
        chunk_id="ruot-oi-la-ruot_B_p999_c00",
        document_id="ruot-oi-la-ruot",
        source="ruotoilaruot.pdf",
        page=999,
        text="Đoạn văn bản cũ từ phiên bản trước sẽ bị xóa khi tài liệu cập nhật.",
        metadata={"page_id": "ruot-oi-la-ruot_p999", "part": "OTHER", "section": "Khác", "chunk_index": 0, "char_len": 67, "strategy": "B"},
    )
    store.get_collection("B").upsert(
        ids=[dummy_chunk.chunk_id],
        documents=[dummy_chunk.text],
        embeddings=[vecs_b[0]],
        metadatas=[{"document_id": "ruot-oi-la-ruot", "source": "ruotoilaruot.pdf", "page": 999, "page_id": "ruot-oi-la-ruot_p999", "part": "OTHER", "section": "Khác", "chunk_index": 0, "char_len": 67, "strategy": "B"}],
    )
    count_with_obsolete = store.count("B")
    cleanup_result = store.upsert("B", chunks_b, vecs_b)
    assert cleanup_result["removed_obsolete"] == 1 and cleanup_result["total_in_collection"] == len(chunks_b)

    ingestion_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "corpus": {
            "document_id": "ruot-oi-la-ruot",
            "source": "ruotoilaruot.pdf",
            "valid_pages": len(pages),
            "pdf_load_time_sec": pdf_load_sec,
        },
        "embedding_model": {
            "provider": "local (sentence-transformers)",
            "model_name": embedder.model_name,
            "dimensions": embedder.dimensions,
            "normalization": "L2 normalized embeddings (cosine similarity)",
            "model_init_time_sec": model_init_sec,
            "cost_usd": 0.0,
        },
        "vector_store": {
            "backend": "ChromaDB PersistentClient",
            "persist_directory": str(chroma_dir.relative_to(root_dir)),
            "distance_metric": "cosine (HNSW approximate nearest neighbor index, hnsw:space=cosine)",
        },
        "strategies": {
            "A": {
                "description": "Fixed-size chunking (size=500 chars, overlap=50 chars), no metadata filter at retrieval",
                "params": {"chunking": "fixed_size", "size": 500, "overlap": 50, "use_metadata_filter": False},
                "chunk_stats": _compute_chunk_stats(chunks_a),
                "timing_sec": {
                    "chunking": chunk_time_a,
                    "embedding": embed_time_a,
                    "upsert": upsert_time_a,
                    "total_ingest": round(pdf_load_sec + chunk_time_a + embed_time_a + upsert_time_a, 4),
                },
                "cost_usd": 0.0,
                "idempotency_check": {
                    "count_after_first_upsert": up_a1["total_in_collection"],
                    "count_after_re_upsert": up_a2["total_in_collection"],
                    "duplicates_created": up_a2["total_in_collection"] - up_a1["total_in_collection"],
                },
            },
            "B": {
                "description": "Paragraph/heading structure-aware chunking (max_size=600 chars), no metadata filter at retrieval",
                "params": {"chunking": "by_paragraph", "max_size": 600, "use_metadata_filter": False},
                "chunk_stats": _compute_chunk_stats(chunks_b),
                "timing_sec": {
                    "chunking": chunk_time_b,
                    "embedding": embed_time_b,
                    "upsert": upsert_time_b,
                    "total_ingest": round(pdf_load_sec + chunk_time_b + embed_time_b + upsert_time_b, 4),
                },
                "cost_usd": 0.0,
                "idempotency_check": {
                    "count_after_first_upsert": up_b1["total_in_collection"],
                    "count_after_re_upsert": up_b2["total_in_collection"],
                    "duplicates_created": up_b2["total_in_collection"] - up_b1["total_in_collection"],
                    "obsolete_chunk_test_before_cleanup": count_with_obsolete,
                    "obsolete_chunks_removed_on_update": cleanup_result["removed_obsolete"],
                    "count_after_cleanup": cleanup_result["total_in_collection"],
                },
            },
            "C": {
                "description": "Same paragraph/heading chunking as B (max_size=600 chars), WITH pre-retrieval metadata filter (part) when question specifies filter",
                "params": {"chunking": "by_paragraph", "max_size": 600, "use_metadata_filter": True, "filter_fields": ["part"]},
                "chunk_stats": _compute_chunk_stats(chunks_c),
                "timing_sec": {
                    "chunking": chunk_time_b,
                    "embedding": embed_time_b,
                    "upsert": upsert_time_c,
                    "total_ingest": round(pdf_load_sec + chunk_time_b + embed_time_b + upsert_time_c, 4),
                },
                "cost_usd": 0.0,
                "idempotency_check": {
                    "count_after_first_upsert": up_c1["total_in_collection"],
                    "count_after_re_upsert": up_c2["total_in_collection"],
                    "duplicates_created": up_c2["total_in_collection"] - up_c1["total_in_collection"],
                },
            },
        },
    }

    (results_dir / "ingestion_stats.json").write_text(
        json.dumps(ingestion_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   Saved ingestion statistics and idempotency check to results/ingestion_stats.json.")

    print("6. Running top-3 retrieval across all 20 benchmark questions for Strategies A, B, and C...")
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    all_traces: list[dict[str, Any]] = []

    for q in questions:
        q_vec = embedder.embed_query(q["question"])
        for strat in ("A", "B", "C"):
            applied_filter = q.get("filter") if (strat == "C" and q.get("filter")) else None
            hits = store.search(strategy=strat, query_vector=q_vec, top_k=3, filters=applied_filter)
            trace = evaluate_query(question=q, hits=hits, strategy=strat, applied_filter=applied_filter)
            all_traces.append(trace)

    summary = summarize(all_traces)
    (results_dir / "retrieval_traces.json").write_text(
        json.dumps(all_traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (results_dir / "retrieval_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   Saved full traces to results/retrieval_traces.json and metrics to results/retrieval_summary.json.")
    for strat in ("A", "B", "C"):
        dev_m = summary[strat]["dev"]
        test_m = summary[strat]["test"]
        print(
            f"   Strategy {strat}: DEV Hit@1={dev_m['hit_at_1_fraction']} ({dev_m['hit_at_1_rate']:.1%}), "
            f"Hit@3={dev_m['evidence_hit_at_3_fraction']} ({dev_m['evidence_hit_at_3_rate']:.1%}) | "
            f"TEST Hit@1={test_m['hit_at_1_fraction']} ({test_m['hit_at_1_rate']:.1%}), "
            f"Hit@3={test_m['evidence_hit_at_3_fraction']} ({test_m['evidence_hit_at_3_rate']:.1%})"
        )


if __name__ == "__main__":
    main()
