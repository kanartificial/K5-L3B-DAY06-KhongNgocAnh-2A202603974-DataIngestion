"""Read and normalize source data."""
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from pypdf import PdfReader
from .models import DocumentPage

# Section boundaries derived from the PDF outline of ruotoilaruot.pdf
SECTION_RANGES: list[tuple[int, int, str, str]] = [
    (4, 9, "LOI_NOI_DAU", "Lời nói đầu"),
    (10, 14, "PHAN_1", "Phần Một: Cảm nhận về ruột (Mở đầu)"),
    (15, 28, "PHAN_1", "Việc đi ngoài được thực hiện như thế nào? Và vì sao câu hỏi này quan trọng"),
    (29, 43, "PHAN_1", "Cổng vào ruột"),
    (44, 67, "PHAN_1", "Cấu trúc của ruột"),
    (68, 81, "PHAN_1", "Những gì chúng ta thực sự ăn"),
    (82, 95, "PHAN_1", "Chứng dị ứng và không dung nạp"),
    (96, 103, "PHAN_1", "Một số sự thật về phân"),
    (104, 107, "PHAN_2", "Phần Hai: Hệ thần kinh của ruột (Mở đầu)"),
    (108, 124, "PHAN_2", "Các cơ quan của chúng ta vận chuyển thức ăn như thế nào"),
    (125, 131, "PHAN_2", "Sự trào ngược"),
    (132, 145, "PHAN_2", "Nôn"),
    (146, 163, "PHAN_2", "Táo bón"),
    (164, 193, "PHAN_2", "Não và ruột"),
    (194, 198, "PHAN_3", "Phần Ba: Thế giới của vi sinh vật (Mở đầu)"),
    (199, 206, "PHAN_3", "Tôi là một hệ sinh thái"),
    (207, 215, "PHAN_3", "Hệ miễn dịch và các vi khuẩn của chúng ta"),
    (216, 227, "PHAN_3", "Sự phát triển của hệ vi khuẩn đường ruột"),
    (228, 252, "PHAN_3", "Quần thể sinh vật trong ruột của người trưởng thành"),
    (253, 261, "PHAN_3", "Vai trò của hệ vi khuẩn đường ruột"),
    (262, 274, "PHAN_3", "Vi khuẩn làm cho chúng ta béo như thế nào? Ba giả thuyết"),
    (275, 314, "PHAN_3", "Những kẻ xấu - Các vi khuẩn và ký sinh trùng có hại"),
    (315, 366, "PHAN_3", "Về tính sạch sẽ và các vi khuẩn tốt"),
    (391, 394, "CHU_THICH", "Chú thích"),
]


def get_section_metadata(page_num: int) -> tuple[str | None, str | None]:
    """Return (part_code, section_title) for a 1-indexed page number."""
    for start, end, part, chapter in SECTION_RANGES:
        if start <= page_num <= end:
            return part, chapter
    return None, None


def normalize_text(text: str) -> str:
    """Normalize Unicode (NFC) and whitespace without discarding paragraph structure."""
    if not text:
        return ""
    # Clean null bytes produced by PDF ligature encoding (e.g. ff/fi/fl) and Latin-1 Đ
    text = text.replace("\x00", "")
    text = text.replace("\u00d0", "Đ").replace("\u0110", "Đ")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_pdf(
    path: Path,
    document_id: str,
    source: str,
    log_path: Path | None = None,
) -> list[DocumentPage]:
    """Extract each valid physical page; keep its 1-indexed page number, source, and metadata.

    Detects and logs excluded/empty/non-content pages to `log_path` if provided.
    """
    reader = PdfReader(str(path))
    pages: list[DocumentPage] = []
    skipped_log: list[dict[str, Any]] = []

    for page_idx, pdf_page in enumerate(reader.pages):
        page_num = page_idx + 1
        raw_text = pdf_page.extract_text() or ""
        norm_text = normalize_text(raw_text)
        char_len = len(norm_text)

        # Apply the same exclusion rules documented in manifest.json
        if page_num in (1, 2, 3):
            skipped_log.append({"page": page_num, "chars": char_len, "reason": "front_matter_cover_title_dedication"})
            continue
        if page_num in (10, 104, 194):
            skipped_log.append({"page": page_num, "chars": char_len, "reason": "part_divider_heading_only"})
            continue
        if 367 <= page_num <= 368:
            skipped_log.append({"page": page_num, "chars": char_len, "reason": "acknowledgments"})
            continue
        if 369 <= page_num <= 388:
            skipped_log.append({"page": page_num, "chars": char_len, "reason": "references_bibliography"})
            continue
        if 389 <= page_num <= 390:
            skipped_log.append({"page": page_num, "chars": char_len, "reason": "table_of_contents"})
            continue
        if char_len == 0:
            skipped_log.append({"page": page_num, "chars": 0, "reason": "blank_or_image_only_page"})
            continue

        part, section = get_section_metadata(page_num)
        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=page_num,
                text=norm_text,
                metadata={
                    "page_id": f"{document_id}_p{page_num:03d}",
                    "part": part or "OTHER",
                    "section": section or "Khác",
                    "char_count": char_len,
                },
            )
        )

    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(skipped_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return pages
