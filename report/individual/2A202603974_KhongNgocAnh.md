# Báo cáo cá nhân — Day 6 (`2A202603974` — Khổng Ngọc Anh)

## Dữ liệu và pipeline
- **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:**
  - **Chủ đề & Nguồn:** Y sinh học hệ tiêu hóa và hệ vi sinh vật đường ruột — sách *"Ruột Ơi Là Ruột - Bí Mật Của Một Thế Giới Bị Lãng Quên"* (Giulia Enders, Nguyễn Ngọc Tú dịch, NXB Nhã Nam; bản PDF xuất từ Calibre 8.5.0, `source_id = "ruot-oi-la-ruot"`, đường dẫn cục bộ `ruotoilaruot.pdf`).
  - **Quyền sử dụng & Bảo mật dữ liệu:** Sách có bản quyền thương mại, chỉ dùng bản cá nhân chạy **cục bộ (local)** cho mục đích học tập/thực hành lab. Tuân thủ [GUIDE.md](../../GUIDE.md) và [RULES.md](../../RULES.md): file `ruotoilaruot.pdf` được đưa vào [.gitignore](../../.gitignore) để **không tái phân phối trên Git repo** và **không gửi văn bản lên bất kỳ API bên thứ ba nào** (sử dụng mô hình embedding chạy hoàn toàn trên CPU local). Người chấm có thể đối chiếu toàn bộ cấu trúc trang tại [data/manifest.json](../../data/manifest.json), log trang loại trừ tại [results/ingestion_skipped_pages.json](../../results/ingestion_skipped_pages.json) và trace kết quả tại [results/retrieval_traces.json](../../results/retrieval_traces.json).
  - **Số trang và quy tắc tính trang:** Tổng số trang vật lý là **394 trang** (`1..394`). Quy tắc đếm trang hợp lệ: chỉ tính các trang nội dung chính có văn bản trích xuất được sau chuẩn hóa Unicode NFC; **loại trừ 36 trang** gồm trang bìa/tựa/đề tặng (`1–3`), trang tiêu đề ngăn cách Phần (`10, 104, 194`), trang trống hoặc chỉ có hình minh họa không có chữ (`102, 163, 193, 195, 258, 366`), Lời cảm ơn (`367–368`), Tài liệu tham khảo (`369–388`) và Mục lục (`389–390`). Tổng cộng thu được **358 trang nội dung hợp lệ** (**429.623 ký tự** đã chuẩn hóa, vượt xa mức tối thiểu 30 trang).
- **Chuẩn hóa, lỗi và giới hạn:**
  - Hàm `normalize_text()` trong [starter/src/ingestion.py](../../starter/src/ingestion.py) thực hiện: (1) loại bỏ ký tự null `\x00` sinh ra do lỗi mã hóa ligature (`ff`/`fi`/`fl`) của font PDF ở các từ tiếng Anh (ví dụ trang 374, 386, 392); (2) chuẩn hóa ký tự `Ð` (`\u00d0`/`\u0110` $\rightarrow$ `Đ`); (3) chuẩn hóa Unicode về dạng dựng sẵn **NFC**; (4) gom khoảng trắng ngang liên tiếp và giới hạn tối đa 2 dấu xuống dòng liên tiếp để bảo toàn cấu trúc đoạn.
  - **Log lỗi/trang loại trừ:** Toàn bộ 36 trang bị loại trừ cùng lý do cụ thể (`front_matter_cover_title_dedication`, `part_divider_heading_only`, `blank_or_image_only_page`, `acknowledgments`, `references_bibliography`, `table_of_contents`) được ghi tự động vào [results/ingestion_skipped_pages.json](../../results/ingestion_skipped_pages.json). Không cần OCR vì 358 trang nội dung đều có lớp text số hóa sạch.
- **Embedding model/provider/version/số chiều, vector store/version, metric, lệnh chạy và chi phí:**
  - **Môi trường & Phiên bản thư viện:** Python `3.14.10` (Linux), `pypdf==6.21.4`, `sentence-transformers==6.3.0`, `transformers==5.23.0`, `torch==2.15.0+cpu`, `chromadb==1.5.9`.
  - **Embedding Model:** Local `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (**384 chiều**, chuẩn hóa vector L2 `normalize_embeddings=True`, dùng chung cách mã hóa cho cả document và query trên cả 3 chiến lược A, B, C; không fallback sang mock vector).
  - **Vector Store & Metric:** `ChromaDB PersistentClient` lưu bền vững tại `results/chroma_db/` với 3 collection riêng (`day06_strategy_a`, `day06_strategy_b`, `day06_strategy_c`), sử dụng chỉ mục xấp xỉ HNSW (`approximate nearest neighbor`) với metric **`cosine`** (`hnsw:space="cosine"`).
  - **Kiểm tra nạp lại (Idempotency) & Xử lý tài liệu thay đổi:** Hàm `upsert()` trong [starter/src/store.py](../../starter/src/store.py) sinh `chunk_id` tất định (`ruot-oi-la-ruot_<Strategy>_p<Page>_c<Idx>`), kiểm tra xóa các `chunk_id` cũ không còn tồn tại của cùng `document_id` trước khi `upsert`. Khi chạy nạp lại lần 2 cho cả A (`1,133` chunks), B (`1,058` chunks) và C (`1,058` chunks), số bản ghi giữ nguyên tuyệt đối (`duplicates_created = 0`), và thử nghiệm chèn 1 chunk giả lập phiên bản cũ (`ruot-oi-la-ruot_B_p999_c00`) rồi nạp lại đã tự động dọn sạch (`obsolete_chunks_removed_on_update = 1`, chi tiết tại [results/ingestion_stats.json](../../results/ingestion_stats.json)).
  - **Lệnh chạy tái lập & Chi phí:**
    ```bash
    starter/.venv/bin/python -m starter.src.run
    ```
    Thời điểm chạy: `2026-11-15T12:56:47Z` (`19:56:47+07:00`). Chi phí API: **`$0.00`** (chạy 100% local trên CPU Intel Core i5-8265U).
- **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn:**
  - **Metadata bắt buộc:** `document_id` (`str`: `"ruot-oi-la-ruot"`), `source` (`str`: `"ruotoilaruot.pdf"`), `page` (`int`: số trang vật lý 1-indexed) và `page_id` (`str`: `"ruot-oi-la-ruot_p004"`..).
  - **Trường lọc bổ sung:** `part` (`str`: nhận 1 trong 5 giá trị `LOI_NOI_DAU`, `PHAN_1`, `PHAN_2`, `PHAN_3`, `CHU_THICH`) và `section` (`str`: tên chương trích xuất trực tiếp từ cây Mục lục/Outline gốc của file PDF).
  - **Lý do chọn:** Nhiều khái niệm y sinh (như *táo bón, chất xơ, vi khuẩn, hệ miễn dịch, hormone Cortisone/Insulin*) xuất hiện rải rác ở cả các phần nội dung chính lẫn phần *Chú thích thuật ngữ* cuối sách. Trường `part` cho phép khoanh vùng đúng phần sách người dùng đang tra cứu mà không cần tự đoán giá trị ngoài nguồn.

---

## Cấu hình và benchmark
- **A / B / C (tham số cụ thể, khác biệt duy nhất B–C):**
  - **Chiến lược A (`fixed_size`):** Chia cửa sổ ký tự cố định `size = 500`, `overlap = 50`, gắn đầy đủ metadata nhưng **không lọc metadata** khi truy xuất.
  - **Chiến lược B (`by_paragraph`):** Chia theo cấu trúc đoạn văn / câu hoàn chỉnh với `max_size = 600` ký tự (`overlap = 0`), gắn cùng metadata như A và **không lọc metadata** khi truy xuất (so sánh **A–B** chỉ thay đổi duy nhất thuật toán chia chunk).
  - **Chiến lược C (`by_paragraph` + metadata filter):** Giữ **nguyên hoàn toàn** các chunk và vector của B (`max_size = 600`), chỉ bật thêm bộ lọc `where={"part": ...}` tại thời điểm truy xuất cho các câu hỏi có cung cấp ngữ cảnh `filter` (so sánh **B–C** chỉ thay đổi duy nhất việc áp dụng bộ lọc metadata). Với các câu có `filter = null`, C chạy không lọc giống B.
- **≥20 câu: phân chia ≥15 dev / ≥5 test, câu metadata filter và cách kiểm chứng evidence:**
  - Bộ câu hỏi tại [benchmark/questions.json](../../benchmark/questions.json) gồm **20 câu** được viết và chốt trước khi chạy thử nghiệm: **15 câu `dev` (`q01`–`q15`)** và **5 câu `test` (`q16`–`q20`)**, phủ đủ 4 nhóm: trực tiếp (`6` câu), diễn đạt lại (`4` câu), điều kiện/ngoại lệ (`5` câu) và kiểm tra metadata filter (`5` câu: `q05, q09, q15` ở `dev` và `q18, q20` ở `test`).
  - Tập trang đích của `dev` và `test` hoàn toàn rời nhau ($\text{dev\_pages} \cap \text{test\_pages} = \emptyset$) để tránh rò rỉ dữ liệu. Mọi đoạn `evidence_quote` đều được kiểm chứng tự động bằng script Python là chuỗi con chính xác (`exact substring`) trên văn bản trang `gold_page` sau chuẩn hóa.
- **Tiêu chí chọn chiến lược đã chốt trước khi xem test (ghi tại [benchmark/README.md](../../benchmark/README.md)):**
  1. Ưu tiên cao nhất: **Evidence Hit@3 trên tập `dev`** cao nhất.
  2. Nếu bằng nhau: ưu tiên **Hit@1 trên tập `dev`**, **Chunk Coherence** và **Metadata Filter Compliance** cao hơn.
  3. Nếu vẫn bằng nhau: ưu tiên cấu hình tốn ít tài nguyên hơn (số lượng chunk ít hơn / thời gian xử lý nhanh hơn).

---

## Kết quả

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian | Chi phí |
|---|---|---|---|---:|---:|---:|
| **A (`fixed_size`: 500, overlap 50)** | `dev` | `7/15` (`46.7%`) | `10/15` (`66.7%`) | `1,133` | `105.53s` | `$0.00` |
| **A (`fixed_size`: 500, overlap 50)** | `test` | `2/5` (`40.0%`) | `3/5` (`60.0%`) | `1,133` | `105.53s` | `$0.00` |
| **B (`by_paragraph`: max 600, no filter)** | `dev` | `9/15` (`60.0%`) | `12/15` (`80.0%`) | `1,058` | `100.65s` | `$0.00` |
| **B (`by_paragraph`: max 600, no filter)** | `test` | `3/5` (`60.0%`) | `4/5` (`80.0%`) | `1,058` | `100.65s` | `$0.00` |
| **C (`by_paragraph`: max 600 + filter `part`)** | `dev` | `9/15` (`60.0%`) | `12/15` (`80.0%`) | `1,058` | `100.57s` | `$0.00` |
| **C (`by_paragraph`: max 600 + filter `part`)** | `test` | `3/5` (`60.0%`) | `4/5` (`80.0%`) | `1,058` | `100.57s` | `$0.00` |

| Strategy | Coherence trung bình /2 (`n=10`) | Metadata đủ và đúng (`n/N` trên `test` top-3) | Filter tuân thủ (`n/N` câu `test` / `dev`) | Grounding `0/1/2` (số câu `test`) và trung bình `/2` |
|---|---|---|---|---|
| **A** | **`0.80 / 2.00`** (`n=10`; mức `0`: 2, `1`: 8, `2`: 0) | **`15/15`** (`100.0%`) | `0/2` (`test`) · `1/3` (`dev`) | `0`: 1, `1`: 1, `2`: 3 — **`1.40 / 2.00`** |
| **B** | **`1.30 / 2.00`** (`n=10`; mức `0`: 0, `1`: 7, `2`: 3) | **`15/15`** (`100.0%`) | `1/2` (`test`) · `1/3` (`dev`) | `0`: 1, `1`: 0, `2`: 4 — **`1.60 / 2.00`** |
| **C** | **`1.30 / 2.00`** (`n=10`; mức `0`: 0, `1`: 7, `2`: 3) | **`15/15`** (`100.0%`) | **`2/2` (`test`, `100%`) · `3/3` (`dev`, `100%`)** | `0`: 1, `1`: 0, `2`: 4 — **`1.60 / 2.00`** |

**Đường dẫn trace, nhãn thủ công và cách chọn mẫu:**
- **Trace đầy đủ top-3 (60 lượt truy xuất = 20 câu × 3 chiến lược):** [results/retrieval_traces.json](../../results/retrieval_traces.json) và bảng tổng hợp tự động [results/retrieval_summary.json](../../results/retrieval_summary.json).
- **Nhãn thủ công Chunk Coherence (`n=10` vị trí):** [results/manual_chunk_coherence.csv](../../results/manual_chunk_coherence.csv) (và `.json`) — chọn cố định trước khi xem điểm theo 10 `page_id` hợp lệ đầu tiên đã sắp xếp tăng dần (`p004`–`p009`, `p011`–`p014`), xét chunk đầu tiên (`c00`) của mỗi trang.
- **Nhãn thủ công Metadata Usefulness (`5 câu test × top-3 = 15` bản ghi/chiến lược):** [results/manual_metadata_usefulness.csv](../../results/manual_metadata_usefulness.csv) (và `.json`).
- **Nhãn thủ công Grounding Quality (`5 câu test`/chiến lược):** [results/manual_grounding_quality.csv](../../results/manual_grounding_quality.csv) (và `.json`).
- **Báo cáo phân tích chi tiết 5 khía cạnh:** [results/section4_evaluation_report.md](../../results/section4_evaluation_report.md). Toàn bộ nhãn thủ công do tác giả trực tiếp chấm và kiểm chứng đối chiếu với PDF gốc (không dùng LLM judge).

---

## Phân tích và kết luận
- **So sánh A–B và B–C; 2 ví dụ sai có ID câu và nguồn:**
  - **So sánh A vs. B (Ảnh hưởng của Chunking):** Chia theo đoạn văn (`by_paragraph`, tối đa 600 ký tự) ở B giảm `6.6%` số chunk (`1,133` xuống `1,058`), giảm thời gian tính embedding từ `79.09s` xuống `74.19s`, đồng thời tăng **DEV Hit@1 từ `7/15` lên `9/15`**, **DEV Evidence Hit@3 từ `10/15` lên `12/15`**, **TEST Evidence Hit@3 từ `3/5` lên `4/5`**, **Coherence từ `0.80/2` lên `1.30/2`** và **Grounding từ `1.40/2` lên `1.60/2`**. Nguyên nhân cốt lõi là cửa sổ cố định 500 ký tự của A thường xuyên cắt đôi đoạn bằng chứng.
  - **So sánh B vs. C (Ảnh hưởng của Metadata Filter):** Khi thêm bộ lọc `part` cho các câu có ngữ cảnh giới hạn phạm vi, tỷ lệ tuân thủ filter trong top-3 tăng từ `1/3` (`dev`) và `1/2` (`test`) ở B lên **`3/3` (`100%` `dev`) và `2/2` (`100%` `test`) ở C**. Ở các câu `q09`, `q15` và `q20`, bộ lọc của C loại bỏ hoàn toàn các chunk nhiễu ngoài phạm vi ở Rank 2–3 (ví dụ loại bỏ trang `209` và `354` thuộc `PHAN_3` khi người dùng đang tra cứu mục `CHU_THICH` ở câu `q20`).
  - **Ví dụ lỗi 1 — Lỗi cắt đứt bằng chứng do Fixed-Size Chunking (`q20` trên tập `test` và `q08` trên tập `dev`):**
    - Ở câu **`q20`** (trang nguồn `gold_page = 392`, hỏi về nơi tổng hợp Insulin trong đảo tụy và vai trò duy nhất với Glucose máu), chiến lược A truy xuất đúng trang 392 ở Rank 1 (`ruot-oi-la-ruot_A_p392_c01`, score `0.7756`), nhưng cửa sổ 500 ký tự đã cắt đứt ngay giữa từ `"chuy|ển hóa"` ở đầu mục chú thích `[6] Insulin` (phần mở đầu `"[6] Insulin là một loại hormone từ các tế bào đảo tụy..."` bị đẩy sang cuối chunk `ruot-oi-la-ruot_A_p392_c00`). Hệ quả là `A_p392_c01` mất câu định danh đầu mục và chỉ đạt `40%` mệnh đề bằng chứng (trượt Evidence Hit@3, Grounding chỉ đạt mức `1`). Tương tự ở câu **`q08`** (`dev`, trang `110`), A cắt 4 kỷ lục trong khoang miệng thành 2 chunk `A_p110_c00` (`83.3%` bằng chứng) và `A_p110_c01` (`16.7%` bằng chứng về áp lực 80 kg lên răng hàm), trong khi B và C giữ nguyên vẹn đoạn văn trong `B_p110_c01` và `B_p392_c01` nên đạt Hit@1 và Grounding mức `2`.
  - **Ví dụ lỗi 2 — Lỗi truy xuất sai trang trong cùng một Phần dù đã lọc metadata (`q18` trên tập `test`, nguồn `gold_page = 149`):**
    - Câu **`q18`** hỏi: *"Chất xơ hỗ trợ những người bị táo bón nhẹ hoặc ngắn hạn bằng cách nào khi đi qua đường tiêu hóa?"* với filter `{"part": "PHAN_2"}`. Cả 3 chiến lược A, B, C đều trượt (`Hit@3 = False`, `Grounding = 0`): Chiến lược A trả về `p.147` (định nghĩa táo bón), `p.364` (`PHAN_3`, chất xơ nuôi vi khuẩn) và `p.124`; Chiến lược B và C trả về `ruot-oi-la-ruot_C_p154_c02` (Rank 1, score `0.6631`, bàn về thuốc nhuận tràng khi táo bón), `ruot-oi-la-ruot_C_p147_c00` (Rank 2, score `0.6618`, định nghĩa táo bón tạm thời) và `ruot-oi-la-ruot_C_p154_c01` (Rank 3, score `0.6235`, táo bón nặng). Dù filter `part = PHAN_2` của C đã chặn thành công chunk nhiễu `p.364` từ `PHAN_3`, bản thân `PHAN_2` vẫn có nhiều trang bàn dày đặc về từ khóa *"táo bón"*, khiến mô hình dense embedding `paraphrase-multilingual-MiniLM-L12-v2` chấm điểm các đoạn nói chung về táo bón (`p.147, p.154`) cao hơn đoạn mô tả cơ chế *"chất xơ không được hấp thu ở ruột non, nó đến và gõ vào thành ruột già"* ở trang `149`.
- **Chiến lược chọn, đánh đổi, điều kiện áp dụng:**
  - **Chiến lược được chọn:** **Chiến lược C (`by_paragraph` `max_size=600` + lọc metadata `part` khi có yêu cầu)**.
  - **Đánh đổi (Trade-offs) & Điều kiện áp dụng:** Chiến lược C vừa đạt hiệu năng truy xuất cao nhất (`80%` Evidence Hit@3 trên cả `dev` và `test`), độ mạch lạc chunk tốt hơn (`1.30/2` so với `0.80/2`), giảm số lượng vector lưu trữ (`1,058` so với `1,133`), vừa đảm bảo `100%` tuân thủ phạm vi metadata khi người dùng chỉ định phần sách cần tìm. Đánh đổi cần lưu ý là nếu người dùng hoặc tầng phân loại ngữ cảnh truyền sai giá trị filter `part`, bộ lọc cứng (`hard filter`) sẽ loại mất trang đúng; do đó chỉ áp dụng filter khi ngữ cảnh đầu vào đáng tin cậy.
- **Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí:**
  - **Tập test nhỏ:** Tập `test` chỉ có 5 câu hỏi (`1 câu = 20%`), nên sai số thống kê lớn; kết quả chỉ mang tính minh họa thực nghiệm trên cuốn sách `ruotoilaruot.pdf`, không tuyên bố chiến lược C là tối ưu tổng quát cho mọi tập dữ liệu.
  - **Ranh giới trang vật lý PDF:** Pipeline hiện trích xuất và chia chunk bên trong từng trang vật lý (`DocumentPage`). Khi một câu hoặc một đoạn bằng chứng dài nằm ở cuối trang hoặc vượt quá `max_size = 600` ký tự (như ở câu `q02` trang 16, `q07` trang 98, `q10` trang 180), bằng chứng vẫn bị tách làm hai chunk trên cùng trang đó (`Page Hit@3` của B/C trên `dev` đạt tuyệt đối `15/15`, nhưng `Evidence Hit@3` đơn chunk dừng ở `12/15`).
  - **Thiên lệch người chấm & Công cụ AI hỗ trợ:** Nhãn thủ công do một người (tác giả) chấm. Trong quá trình làm bài, tác giả có sử dụng trợ lý AI (Antigravity) để hỗ trợ viết khung script Python, kiểm tra chuẩn hóa chuỗi và xuất bảng thống kê; toàn bộ câu hỏi, trích dẫn bằng chứng (`evidence_quote`), kết quả chạy thực nghiệm và nhãn chấm thủ công đều được kiểm chứng trực tiếp trên văn bản PDF gốc và log chạy thực tế.
- **Nếu làm lại hoặc mở rộng, cải tiến gì?**
  1. **Ghép văn bản liên trang theo chương (`section`) trước khi chia chunk:** Thay vì chia chunk độc lập từng trang, nối văn bản các trang trong cùng một chương kèm bản đồ vị trí ký tự $\rightarrow$ số trang (`page_span = [p_start, p_end]`) để triệt tiêu hoàn toàn hiện tượng đứt câu ở đầu/cuối trang PDF.
  2. **Thêm overlap 1 câu cho `by_paragraph` hoặc tăng `max_size` lên 800–1.000 ký tự (kèm parent-document / neighboring-chunk expansion):** Giải quyết 3 câu `dev` (`q02, q07, q10`) bị tách đôi bằng chứng dù đã truy xuất trúng trang gold (`Page Hit@3 = 15/15`).
  3. **Kết hợp Hybrid Retrieval (Dense + BM25) và lọc mịn hơn theo `section`:** Giúp các câu hỏi có thuật ngữ đặc thù như *"chất xơ"*, *"van Bauhin"*, *"GLUT5"*, *"nước bọt"* (`q04`, `q18`) tăng hạng chính xác lên Rank 1.
