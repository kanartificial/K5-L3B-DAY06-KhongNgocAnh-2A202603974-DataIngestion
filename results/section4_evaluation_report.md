# Đánh giá 5 khía cạnh — Section 4 (`ruotoilaruot.pdf`)

Báo cáo chi tiết kết quả thực nghiệm và chấm thủ công theo đúng 5 khía cạnh trong Mục 4 của [GUIDE.md](../GUIDE.md) và [BENCHMARK.md](../BENCHMARK.md).

> **Ghi chú về người chấm và nguy cơ thiên lệch (Bias Disclosure):** Toàn bộ nhãn thủ công (Chunk Coherence, Metadata Usefulness, Grounding Quality) do chính tác giả bài làm thực hiện. Để giảm thiểu thiên lệch xác nhận (*confirmation bias*), 10 vị trí chấm Coherence đã được cố định trước theo thứ tự tăng dần của `page_id` (`p004`–`p014`), tiêu chí chọn chiến lược được đăng ký trước khi đọc tập `test`, và mọi nhãn đều đính kèm trích dẫn văn bản/chunk ID cụ thể để người chấm độc lập có thể đối chiếu. Không sử dụng LLM judge.

---

## Tổng hợp kết quả theo bảng mẫu báo cáo

### Bảng 1: Độ chính xác truy xuất và tài nguyên (Dev vs Test)

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Page Hit@3 (n/N) | Evidence Split Errors | Chunk count | Thời gian ingest | Chi phí |
|---|---|---|---|---|---|---:|---:|---:|
| **A (`fixed_size`: 500, overlap 50)** | `dev` | `7/15` (`46.7%`) | `10/15` (`66.7%`) | `14/15` (`93.3%`) | `4` câu (`q02, q07, q08, q10`) | `1,133` | `105.53s` | `$0.00` |
| **A (`fixed_size`: 500, overlap 50)** | `test` | `2/5` (`40.0%`) | `3/5` (`60.0%`) | `4/5` (`80.0%`) | `1` câu (`q20`) | `1,133` | `105.53s` | `$0.00` |
| **B (`by_paragraph`: max 600, no filter)** | `dev` | `9/15` (`60.0%`) | `12/15` (`80.0%`) | `15/15` (`100.0%`) | `3` câu (`q02, q07, q10`) | `1,058` | `100.65s` | `$0.00` |
| **B (`by_paragraph`: max 600, no filter)** | `test` | `3/5` (`60.0%`) | `4/5` (`80.0%`) | `4/5` (`80.0%`) | `0` câu | `1,058` | `100.65s` | `$0.00` |
| **C (`by_paragraph`: max 600 + filter `part`)** | `dev` | `9/15` (`60.0%`) | `12/15` (`80.0%`) | `15/15` (`100.0%`) | `3` câu (`q02, q07, q10`) | `1,058` | `100.57s` | `$0.00` |
| **C (`by_paragraph`: max 600 + filter `part`)** | `test` | `3/5` (`60.0%`) | `4/5` (`80.0%`) | `4/5` (`80.0%`) | `0` câu | `1,058` | `100.57s` | `$0.00` |

### Bảng 2: Đánh giá thủ công trên các khía cạnh chất lượng

| Strategy | Coherence trung bình /2 (`n=10`) | Metadata đủ và đúng (`n/N` trên `5 test × top-3`) | Filter tuân thủ trên `test` (`n/N`) | Filter tuân thủ trên `dev` (`n/N`) | Grounding `0/1/2` (số câu `test`) và trung bình `/2` |
|---|---|---|---|---|---|
| **A** | **`0.80 / 2.00`** (`0`: 2, `1`: 8, `2`: 0) | **`15/15`** (`100%`) | `0/2` câu (`3/6` bản ghi) | `1/3` câu (`7/9` bản ghi) | `0`: 1, `1`: 1, `2`: 3 — **`1.40 / 2.00`** |
| **B** | **`1.30 / 2.00`** (`0`: 0, `1`: 7, `2`: 3) | **`15/15`** (`100%`) | `1/2` câu (`4/6` bản ghi) | `1/3` câu (`6/9` bản ghi) | `0`: 1, `1`: 0, `2`: 4 — **`1.60 / 2.00`** |
| **C** | **`1.30 / 2.00`** (`0`: 0, `1`: 7, `2`: 3) | **`15/15`** (`100%`) | **`2/2` câu (`6/6` bản ghi, `100%`)** | **`3/3` câu (`9/9` bản ghi, `100%`)** | `0`: 1, `1`: 0, `2`: 4 — **`1.60 / 2.00`** |

---

## 1. Retrieval Accuracy — Hit@1 và Evidence Hit@3

- **Định nghĩa chính:** Một kết quả được tính là hit khi chunk thuộc đúng tài liệu `ruot-oi-la-ruot`, nằm ở `gold_page` (hoặc `alternative_gold_pages`) và chứa đủ bằng chứng trong một chunk đơn lẻ.
- **So sánh kết quả:**
  - **Trên tập `dev` (15 câu):** Chiến lược B và C đạt **Hit@1 = `9/15` (`60.0%`)** và **Evidence Hit@3 = `12/15` (`80.0%`)**, vượt chiến lược A (**Hit@1 = `7/15` (`46.7%`)**, **Evidence Hit@3 = `10/15` (`66.7%`)**).
  - **Trên tập `test` (5 câu):** Chiến lược B và C đạt **Hit@1 = `3/5` (`60.0%`)** và **Evidence Hit@3 = `4/5` (`80.0%`)**, cao hơn chiến lược A (**Hit@1 = `2/5` (`40.0%`)**, **Evidence Hit@3 = `3/5` (`60.0%`)**).
- **Phân tích lỗi bằng chứng bị tách qua nhiều chunk (Multi-chunk Evidence Split):**
  - Ở chiến lược A, mặc dù **Page Hit@3 đạt tới `14/15` trên `dev` và `4/5` trên `test`**, có **4 câu `dev` (`q02, q07, q08, q10`)** và **1 câu `test` (`q20`)** bị tính là trượt Evidence Hit@3 vì cửa sổ 500 ký tự cắt đôi đoạn bằng chứng thành hai chunk liên tiếp (`c00` và `c01`).
  - Cụ thể: ở câu **`q08`** (trang 110, hỏi về 4 kỷ lục trong khoang miệng: cơ nhai, lưỡi, men răng, áp lực 80 kg), chiến lược A cắt đoạn văn tại ký tự 500 nên `ruot-oi-la-ruot_A_p110_c00` chỉ chứa 83.3% mệnh đề và phần áp lực 80 kg rơi sang `ruot-oi-la-ruot_A_p110_c01`. Chiến lược B/C gom trọn đoạn văn vào `ruot-oi-la-ruot_B_p110_c01` nên đạt Hit@1 ngay lập tức.
  - Tương tự ở câu **`q20`** (`test`, trang 392, định nghĩa `[6] Insulin`), chiến lược A cắt đứt từ `"chuy|ển hóa"` ở ranh giới 500 ký tự giữa `A_p392_c00` và `A_p392_c01`, làm `A_p392_c01` mất câu mở đầu định nghĩa mục `[6] Insulin`. Ngược lại, chiến lược B và C giữ nguyên vẹn toàn bộ mục `[6]` trong `B_p392_c01` / `C_p392_c01` (score `0.8282` vs `0.7756` của A).
  - Nếu tính bổ sung chỉ số **Multi-chunk Combined Hit@3** (hợp bằng chứng của các chunk cùng trang gold trong top-3), tỷ lệ của A tăng từ `10/15` lên `12/15` trên `dev`, và của B/C tăng từ `12/15` lên `13/15` trên `dev` (nhờ ghép `c01` và `c00` của câu `q10` trên trang 180).

---

## 2. Chunk Coherence (Chấm thủ công 10 vị trí nguồn cố định)

Chi tiết đầy đủ lưu tại [results/manual_chunk_coherence.json](manual_chunk_coherence.json) và [results/manual_chunk_coherence.csv](manual_chunk_coherence.csv). Mẫu gồm chunk đầu tiên (`c00`) của 10 trang hợp lệ đầu tiên (`p004`–`p009`, `p011`–`p014`).

| Vị trí | Trang (`page_id`) | Điểm A (`/2`) | Lý do chấm A (`fixed_size`) | Điểm B & C (`/2`) | Lý do chấm B & C (`by_paragraph`) |
|---|---|---:|---|---:|---|
| `pos_01` | `p004` | `1` | Cắt cụt đoạn mở đầu ở ký tự 500 ngay trước câu kết về vết loét năm 17 tuổi. | **`2`** | Giữ trọn vẹn đoạn mở đầu Lời nói đầu (585 ký tự), kết thúc đúng dấu chấm hết đoạn. |
| `pos_02` | `p005` | `1` | Cắt lửng giữa cụm từ cuối (`"Rồi tôi cũng lấy lại sự tự chủ và"`). | `1` | Đoạn văn dài >600 ký tự và có xuống dòng PDF nên dư cụm đầu câu kế (`"Tình cờ tôi"`). |
| `pos_03` | `p006` | `1` | Đầu trang nối từ trang 5 và cuối chunk cắt ngang câu mới (`"Đó"`). | `1` | Đầu trang nối từ trang 5 do ngắt trang PDF, nhưng kết thúc trọn đoạn (`"bắt đầu theo học y khoa."`). |
| `pos_04` | `p007` | `1` | Đầu trang thiếu chủ ngữ (`"ấy cảm thấy..."`) và cuối chunk cắt giữa câu (`"Sự ảnh hưởng của đường ruột lên"`). | `1` | Đầu trang thiếu chủ ngữ do ngắt trang PDF, nhưng kết thúc đúng dấu chấm hết đoạn thứ hai (271 ký tự). |
| `pos_05` | `p008` | `0` | Cắt đứt ở cả 2 đầu: mở đầu mất nửa cụm từ (`"đề về Hệ Vi Sinh Vật..."`) và cuối chunk cắt đứt giữa từ (`"mà không h"`). | `1` | Mở đầu nối từ trang 7 nhưng kết thúc trọn vẹn tại `"Đại học Heidelberg."` (356 ký tự). |
| `pos_06` | `p009` | `1` | Đầu trang nối từ trang 8 và cuối chunk cắt lửng (`"trình bày theo một cách thú vị"`). | `1` | Đoạn văn dài >600 ký tự nên cuối chunk bị cắt ở `"có sức quyến"`. |
| `pos_07` | `p011` | `1` | Trang chỉ có 245 ký tự, câu cuối trang kéo sang trang 12 (`"không đơn thuần"`). | `1` | Giống A: lấy trọn 245 ký tự trên trang 11; câu cuối sang trang 12. |
| `pos_08` | `p012` | `1` | Mở đầu nối từ trang 11 và cuối chunk cắt cụt sau động từ `"Não bộ nhận"`. | `1` | Giữ trọn giải thích ẩn dụ cái muỗng/quả tạ nhưng đoạn dài >600 ký tự nên cắt câu cuối (`"và những"`). |
| `pos_09` | `p013` | `0` | Cắt ở cả 2 đầu: mở đầu thiếu chủ ngữ và cuối chunk cắt đứt giữa từ (`"như thế n"`). | **`2`** | Dù cụm đầu nối từ trang 12, toàn bộ ý về hoạt động liên tục 24h của trái tim hoàn chỉnh và dừng đúng hết đoạn (364 ký tự). |
| `pos_10` | `p014` | `1` | Gộp đoạn kết về ống ruột với nửa đoạn mới về tim/não rồi cắt lửng (`"vì nó bơm máu đi"`). | **`2`** | Tách đúng ranh giới đoạn văn (345 ký tự): giữ trọn ý sự hình thành ống ruột và dừng đúng cuối đoạn. |
| **Trung bình** | **10 vị trí** | **`0.80 / 2.00`** | **9/10 chunk bị cắt lửng câu hoặc cắt giữa từ ở ký tự 500.** | **`1.30 / 2.00`** | **6/10 vị trí kết thúc đúng dấu chấm hết đoạn văn, không có chunk nào bị điểm 0.** |

---

## 3. Metadata Usefulness (Kiểm tra thủ công `5 test × top-3 = 15` bản ghi mỗi chiến lược)

Chi tiết từng bản ghi trong số 45 bản ghi (`15 × 3` chiến lược) được lưu tại [results/manual_metadata_usefulness.json](manual_metadata_usefulness.json) và [results/manual_metadata_usefulness.csv](manual_metadata_usefulness.csv).

1. **Độ chính xác và đầy đủ của metadata (`source`, `page`, `part`, `section`):**
   - Cả 3 chiến lược A, B, C đều đạt **`15/15` (`100%`)** bản ghi trên tập `test` có `document_id = "ruot-oi-la-ruot"`, `source = "ruotoilaruot.pdf"`, số trang `page` và nhãn `part`/`section` khớp 100% với trang vật lý trong PDF gốc (không có lỗi lệch trang hay gán sai chương).
2. **Tỷ lệ tuân thủ filter trên các câu có filter (`top-3` tuân thủ hoàn toàn `filter`):**
   - **Tập `test` (`2` câu có filter: `q18` yêu cầu `part = PHAN_2`, `q20` yêu cầu `part = CHU_THICH`):**
     - **Chiến lược A (không lọc):** **`0/2` câu (`0.0%`)** tuân thủ hoàn toàn (`3/6` bản ghi đúng phần). Cụ thể, ở `q18` Rank 2 lấy nhầm `p.364` (`PHAN_3`); ở `q20` Rank 2 và Rank 3 lấy nhầm `p.209` và `p.354` (`PHAN_3`).
     - **Chiến lược B (không lọc):** **`1/2` câu (`50.0%`)** tuân thủ hoàn toàn (`4/6` bản ghi đúng phần). Ở `q18` cả 3 chunk đều thuộc `PHAN_2`, nhưng ở `q20` Rank 2 và Rank 3 vẫn bị kéo sang `p.209` và `p.354` (`PHAN_3` bàn về bệnh tiểu đường và cấy phân) thay vì chỉ tìm trong `CHU_THICH`.
     - **Chiến lược C (có lọc `part`):** **`2/2` câu (`100.0%`)** tuân thủ hoàn toàn (`6/6` bản ghi thuộc đúng `part` yêu cầu). Ở `q20`, cả 3 kết quả top-3 đều nằm trong `CHU_THICH` (`p.392, p.391, p.393`).
   - **Tập `dev` (`3` câu có filter: `q05, q09, q15`):** Chiến lược A và B chỉ đạt **`1/3` (`33.3%`)** câu tuân thủ filter ở cả top-3 (do `q09` và `q15` lẫn các trang thuộc phần khác vào Rank 2–3), trong khi **Chiến lược C đạt `3/3` (`100.0%`)**.
3. **Giá trị thực tế và hạn chế của metadata:**
   - **Trường giúp ích thực sự:**
     - `page` + `section` giúp truy vết tức thì về đúng trang PDF vật lý và tên chương để kiểm chứng bằng chứng.
     - `part` giúp khoanh vùng ngữ cảnh rộng (ví dụ tách riêng bảng thuật ngữ `CHU_THICH` khỏi phần nội dung bàn luận chung ở `PHAN_1..3`), loại bỏ hoàn toàn các chunk nhiễu ngoài phạm vi ở Rank 2–3 của `q09, q15, q20`.
   - **Hạn chế thực tế:**
     - Filter theo `part` là phạm vi cấp Phần lớn (ví dụ `PHAN_2` gồm 84 trang hợp lệ trải dài qua 6 chương). Do đó, trong câu `q18` (hỏi về vai trò của chất xơ với táo bón ở trang 149 thuộc `PHAN_2`), dù filter `part = PHAN_2` đã chặn được chunk nhiễu từ `PHAN_3` (trang 364), bên trong `PHAN_2` vẫn có các đoạn nói về định nghĩa táo bón (trang 147) và thuốc nhuận tràng (trang 154) có điểm cosine cao hơn trang 149, nên chỉ lọc theo `part` không đủ để cứu câu `q18` nếu biểu diễn dense embedding của câu hỏi bị lệch về từ khóa `"táo bón"`.

---

## 4. Grounding Quality (Chấm thủ công 5 câu `test` trên thang 0–2)

Chi tiết lưu tại [results/manual_grounding_quality.json](manual_grounding_quality.json) và [results/manual_grounding_quality.csv](manual_grounding_quality.csv). Lưu ý: chỉ chấm độ đủ của bằng chứng truy xuất trong top-3, **không gọi đây là độ chính xác câu trả lời LLM**.

| Câu hỏi (`test`) | Điểm A | Điểm B | Điểm C | Giải thích chi tiết và đối chiếu nguồn |
|---|---:|---:|---:|---|
| **`q16`** (Diện tích bề mặt ống tiêu hóa gấp bao nhiêu lần diện tích da? — Gold `p.55`) | `2` | `2` | `2` | Cả A, B, C đều truy xuất được `p055_c00` ở Rank 2 (score `0.6542`), chứa nguyên văn câu bằng chứng *"Tổng diện tích bề mặt của ống tiêu hóa lớn gấp khoảng 100 lần so với diện tích da của chúng ta"* kèm tên nguồn và trang 55. |
| **`q17`** (Khi nào người bất dung nạp fructose ăn 1 quả táo/ngày không sao và ngoại lệ nào gây rắc rối? — Gold `p.90`) | `2` | `2` | `2` | Cả A, B, C đều đưa `p090_c00` lên Rank 1 (score `0.8736`), chứa đầy đủ cả mệnh đề chính lẫn điều kiện ngoại lệ (*"trừ phi những thứ khác mà họ ăn được cho thêm fructose, chẳng hạn như xốt cà chua..., chất làm ngọt trong sữa chua ăn bữa sáng và xúp đóng hộp"*). |
| **`q18`** (Chất xơ hỗ trợ người táo bón nhẹ như thế nào khi đi qua đường tiêu hóa? — Gold `p.149`) | `0` | `0` | `0` | Cả 3 chiến lược đều đạt `0`: Top-3 của A (`p.147, p.364, p.124`) và của B/C (`p.154, p.147, p.154`) chỉ bàn về triệu chứng táo bón và thuốc nhuận tràng, hoàn toàn không chứa đoạn bằng chứng ở trang 149 giải thích cơ chế chất xơ không hấp thu ở ruột non mà đến gõ vào thành ruột già. |
| **`q19`** (Chất diệt khuẩn có nên dùng trong sinh hoạt bình thường không và ngoại lệ nào nên dùng? — Gold `p.320`) | `2` | `2` | `2` | Cả A (`A_p320_c00`, score `0.7640`) và B/C (`B_p320_c01` / `C_p320_c01`, score `0.7924`) đều xếp đoạn bằng chứng ở Rank 1, nêu đủ lý do (>95% vi khuẩn vô hại) và 2 ngoại lệ (gia đình có người ốm hoặc chó đi ị lên thảm). |
| **`q20`** (Insulin tổng hợp ở tế bào nào trong đảo tụy và vai trò duy nhất với Glucose máu? — Gold `p.392`) | `1` | **`2`** | **`2`** | **Khác biệt rõ giữa A và B/C:** Ở A (`A_p392_c01`), cửa sổ cố định 500 ký tự cắt mất câu đầu định nghĩa mục `[6] Insulin` (chunk bắt đầu từ giữa từ `"ển hóa các mô mỡ..."`), làm mất định danh đầu mục dù vẫn còn câu về tế bào Beta và Glucose. Ở B và C (`B_p392_c01` / `C_p392_c01`), toàn bộ mục chú thích `[6] Insulin` được giữ trọn vẹn từ đầu đến cuối (điểm `2`). |
| **Phân bố `0 / 1 / 2` & Trung bình `/2`** | `1 / 1 / 3` (**`1.40/2`**) | `1 / 0 / 4` (**`1.60/2`**) | `1 / 0 / 4` (**`1.60/2`**) | **B và C tăng điểm trung bình Grounding từ `1.40/2` lên `1.60/2` nhờ không cắt đứt mục chú thích ở `q20`.** |

---

## 5. Data Strategy Impact (So sánh A–B, B–C và Đánh đổi)

1. **Tác động của chiến lược chia chunk (So sánh A vs B — giữ nguyên không filter):**
   - **Độ chính xác truy xuất:** Chuyển từ `fixed_size` (A: 500 ký tự, overlap 50) sang `by_paragraph` (B: gom đoạn/câu tối đa 600 ký tự) giúp tăng **Hit@1 trên `dev` từ `7/15` (`46.7%`) lên `9/15` (`60.0%`)**, **Evidence Hit@3 trên `dev` từ `10/15` (`66.7%`) lên `12/15` (`80.0%`)**, và trên `test` tăng **Hit@1 từ `2/5` (`40.0%`) lên `3/5` (`60.0%`)**, **Evidence Hit@3 từ `3/5` (`60.0%`) lên `4/5` (`80.0%`)**.
   - **Coherence & Grounding:** Điểm mạch lạc trung bình tăng mạnh từ **`0.80/2.00` lên `1.30/2.00`** (loại bỏ hoàn toàn các chunk điểm `0` bị cắt giữa từ), và điểm Grounding trên `test` tăng từ **`1.40/2.00` lên `1.60/2.00`**.
   - **Tài nguyên tính toán:** Vì không phải nhân bản văn bản ở vùng `overlap=50` và gom gọn theo đoạn, chiến lược B tạo ra **ít hơn 75 chunk** (`1,058` so với `1,133` của A, giảm `6.6%` số chunk và giảm `8.4%` tổng số ký tự từ `468,039` xuống `428,922`), qua đó giảm thời gian chạy embedding trên CPU từ `79.09s` xuống `74.19s`.
2. **Tác động của bộ lọc metadata (So sánh B vs C — giữ nguyên cách chia chunk của B):**
   - **Tính tuân thủ phạm vi (Filter Compliance):** Tăng từ **`1/3` (`33.3%`) lên `3/3` (`100.0%`) trên `dev`** và từ **`1/2` (`50.0%`) lên `2/2` (`100.0%`) trên `test`**. Ở các câu hỏi tra cứu có ngữ cảnh phạm vi (`q09, q15, q20`), bộ lọc `part` loại bỏ hoàn toàn các chunk nhiễu đến từ các phần khác ở Rank 2 và Rank 3.
   - **Tại sao Hit@1 / Hit@3 tổng thể của B và C bằng nhau trên bộ 20 câu hiện tại?** Vì trên 4 câu có filter mà B đã trúng (`q05, q09, q15, q20`), chunk đúng vốn đã có điểm tương đồng ngữ nghĩa cao nhất toàn sách nên nằm ở top-3 ngay cả khi chưa lọc; còn ở câu `q18` (trượt ở cả B và C), các chunk gây nhiễu (`p.154` và `p.147`) lại nằm ngay trong cùng `PHAN_2` với trang gold (`p.149`). Tuy nhiên, C vẫn vượt trội B ở việc đảm bảo 100% kết quả trả về trong top-3 không bị nhiễm nội dung ngoài phạm vi yêu cầu.
3. **Quyết định chọn chiến lược theo tiêu chí đã đăng ký trước:**
   - Theo tiêu chí đã chốt trước khi xem tập `test` (Ưu tiên 1: `DEV Evidence Hit@3`; Ưu tiên 2: `DEV Hit@1` + `Coherence` + `Metadata Usefulness`; Ưu tiên 3: Tài nguyên), **Chiến lược C** được chọn làm cấu hình tốt nhất cho corpus này vì đồng dẫn đầu về `DEV Evidence Hit@3` (`12/15`), `DEV Hit@1` (`9/15`), `Coherence` (`1.30/2`), tốn ít tài nguyên hơn A (`1,058` chunks), và đạt `100%` tuân thủ metadata filter trên cả `dev` lẫn `test`.
4. **Giới hạn và sai số mẫu nhỏ:**
   - Tập `test` chỉ gồm 5 câu hỏi (`1 câu = 20%`), nên mỗi thay đổi 1 câu làm dịch chuyển chỉ số tới 20 điểm phần trăm; kết quả này chỉ minh họa sự khác biệt có kiểm soát trên cuốn sách `ruotoilaruot.pdf` chứ không suy rộng thành kết luận tổng quát cho mọi tập dữ liệu.
   - Việc trích xuất PDF theo từng trang vật lý (`DocumentPage`) khiến những câu văn vắt qua ranh giới hai trang (ví dụ cuối trang 5 sang đầu trang 6) bị tách tự nhiên trước khi đưa vào hàm chunking; ngoài ra các đoạn văn dài quá 600 ký tự vẫn phải cắt nhỏ.
