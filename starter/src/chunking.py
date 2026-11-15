"""Implement fixed-size and structure-aware (paragraph/heading) chunking."""
import re
from .models import Chunk, DocumentPage


def fixed_size(
    page: DocumentPage,
    size: int = 500,
    overlap: int = 50,
    strategy: str = "A",
) -> list[Chunk]:
    """Split page text into overlapping character windows and retain page metadata."""
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")

    text = page.text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    step = size - overlap
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + size, len(text))
        window = text[start:end].strip()
        if window:
            chunk_meta = {
                "document_id": page.document_id,
                "source": page.source,
                "page": page.page,
                "page_id": page.metadata.get("page_id", f"{page.document_id}_p{page.page:03d}"),
                "part": str(page.metadata.get("part", "OTHER")),
                "section": str(page.metadata.get("section", "Khác")),
                "chunk_index": idx,
                "char_len": len(window),
                "strategy": strategy,
            }
            chunks.append(
                Chunk(
                    chunk_id=f"{page.document_id}_{strategy}_p{page.page:03d}_c{idx:02d}",
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=window,
                    metadata=chunk_meta,
                )
            )
            idx += 1
        if end >= len(text):
            break
        start += step

    return chunks


def _split_oversized_block(block: str, max_size: int) -> list[str]:
    """Split a paragraph/block larger than max_size along sentence boundaries when possible."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?…])\s+|\n+", block) if s.strip()]
    if not sentences:
        return []

    parts: list[str] = []
    current = ""
    for sent in sentences:
        if len(sent) > max_size:
            if current:
                parts.append(current)
                current = ""
            for i in range(0, len(sent), max_size):
                piece = sent[i : i + max_size].strip()
                if piece:
                    parts.append(piece)
        elif not current:
            current = sent
        elif len(current) + 1 + len(sent) <= max_size:
            current = f"{current} {sent}"
        else:
            parts.append(current)
            current = sent
    if current:
        parts.append(current)
    return parts


def by_paragraph(
    page: DocumentPage,
    max_size: int = 600,
    strategy: str = "B",
) -> list[Chunk]:
    """Group headings and paragraphs up to max_size, split oversized blocks by sentence, and retain metadata."""
    if max_size <= 0:
        raise ValueError("max_size must be positive")

    text = page.text.strip()
    if not text:
        return []

    # Identify structural blocks: double newlines first; if page has only single newlines, group by sentence/paragraph cues
    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(raw_blocks) == 1 and len(text) > max_size:
        # In Calibre PDF extracts, paragraphs may be separated by single newlines after sentence punctuation or uppercase headings
        raw_blocks = [b.strip() for b in re.split(r"\n(?=[A-ZĐÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ\[\d\"“])", text) if b.strip()]

    units: list[str] = []
    for block in raw_blocks:
        if len(block) <= max_size:
            units.append(block)
        else:
            units.extend(_split_oversized_block(block, max_size))

    grouped_texts: list[str] = []
    current = ""
    for unit in units:
        if not current:
            current = unit
        elif len(current) + 1 + len(unit) <= max_size:
            current = f"{current}\n{unit}"
        else:
            grouped_texts.append(current)
            current = unit
    if current:
        grouped_texts.append(current)

    chunks: list[Chunk] = []
    for idx, chunk_text in enumerate(grouped_texts):
        chunk_meta = {
            "document_id": page.document_id,
            "source": page.source,
            "page": page.page,
            "page_id": page.metadata.get("page_id", f"{page.document_id}_p{page.page:03d}"),
            "part": str(page.metadata.get("part", "OTHER")),
            "section": str(page.metadata.get("section", "Khác")),
            "chunk_index": idx,
            "char_len": len(chunk_text),
            "strategy": strategy,
        }
        chunks.append(
            Chunk(
                chunk_id=f"{page.document_id}_{strategy}_p{page.page:03d}_c{idx:02d}",
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata=chunk_meta,
            )
        )

    return chunks
