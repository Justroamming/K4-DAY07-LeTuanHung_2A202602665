# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Đình Đề
**Nhóm:** G50
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10)

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector trong không gian nhiều chiều có hướng gần giống nhau (góc gần 0°). Cosine gần 1.0 nghĩa là hai đoạn văn bản mang ý nghĩa gần giống nhau, bất kể độ dài hay số từ giống nhau. Ví dụ: "Python là ngôn ngữ lập trình" và "Python là coding language" dùng từ khác nhau nhưng cùng ý — embedding lý tưởng sẽ cho similarity cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Python is a programming language."
- Câu B: "Python is a coding language for software."
- Tại sao tương đồng: Hai câu diễn đạt cùng một ý — Python là ngôn ngữ lập trình/coding. Từ vựng khác nhau nhưng ngữ nghĩa giống nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "The weather is sunny today."
- Câu B: "Stock markets rose sharply this week."
- Tại sao khác: Hoàn toàn không liên quan — thời tiết vs. chứng khoán, khác chủ đề, khác ý nghĩa, không có từ khoá chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Text embeddings có độ dài (norm) khác nhau tùy độ dài văn bản. Cosine chỉ đo hướng (góc) giữa hai vector nên không bị ảnh hưởng bởi độ dài vector. Euclidean đo khoảng cách tuyệt đối — hai văn bản dài hơn sẽ có vector lớn hơn và khoảng cách Euclidean lớn hơn dù nội dung tương tự. Cosine tránh được bias này.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:*
> - Công thức: `ceil((10000 - 50) / (500 - 50))` = `ceil(9950 / 450)` = `ceil(22.11)` = **23 chunks**
> - Chunk đầu tiên: ký tự 0-500 (500 ký tự)
> - Chunk thứ 2: ký tự 450-950 (500 ký tự, overlap 50 với chunk 1)
> - Chunk cuối: ký tự ~10000 trở đi, có thể ngắn hơn 500
>
> *Đáp án:* **23 chunks**

**Kiểm chứng bằng FixedSizeChunker:**
```python
>>> from src.chunking import FixedSizeChunker
>>> len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000))
23
```
Output: `23` ✓ Khớp công thức.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn tăng overlap?**
> `ceil((10000 - 100) / (500 - 100))` = `ceil(9900 / 400)` = `ceil(24.75)` = **25 chunks** (tăng từ 23 lên 25). Overlap nhiều hơn → bước nhảy (step) nhỏ hơn → nhiều chunk hơn. Nhưng mỗi chunk chia sẻ nhiều nội dung hơn với láng giềng → giảm nguy cơ mất ngữ cảnh khi chunk cắt ngang ý nghĩa. Trade-off: nhiều chunk hơn (tốn bộ nhớ/compute) nhưng giữ ngữ cảnh tốt hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex lookbehind `(?<=[.!?])\s+` để tách câu mà vẫn giữ dấu câu ở cuối câu. Nhóm các câu theo `max_sentences_per_chunk`, dùng `" ".join()` để ghép, rồi `re.sub(r'\s+', ' ')` để chuẩn hoá khoảng trắng. Edge case: text rỗng trả `[]`, câu cụt (không có dấu cách sau dấu câu) vẫn được giữ nguyên.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Hai chiều: (1) Đệ quy xuống sâu — mảnh nào > chunk_size thì gọi `_split` lại với danh sách separator còn lại. (2) Gom lên — các mảnh nhỏ liền kề nối lại cho tới sát chunk_size. Base case: (a) không còn separator → hard split theo chunk_size, (b) separator rỗng → hard split, (c) text rỗng → `[]`. Chiến lược ưu tiên: `"\n\n" > "\n" > ". " > " " > ""`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `_make_record` chuẩn hoá Document thành dict: copy metadata, thêm `doc_id`, gọi embedding_fn để tạo vector. `search` gọi `_search_records` trên toàn bộ store: compute cosine similarity cho từng record, sort desc, bỏ embedding khỏi kết quả trả về.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **lọc metadata trước** khi search. `delete_document` xoá tất cả record có `metadata['doc_id']` khớp.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ba nhịp: (1) Kiểm store rỗng → trả thông báo. (2) `store.search(question, top_k)` → retrieve top-k chunks. (3) Dựng prompt đánh số `[1] [2] [3]` kèm source attribution, anti-hallucination constraint. Gọi `llm_fn(prompt)`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0 -- H:\AITHUCCHIEN\K4-DAY07-LeTuanHung_2A202602665\.venv\Scripts\python.exe
rootdir: H:\AITHUCCHIEN\K4-DAY07-LeTuanHung_2A202602665
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 78%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 86%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 95%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]

============================= 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Python is a programming language. | Python is a coding language for software. | cao | -0.0597 | Sai (mock) |
| 2 | The weather is sunny today. | Stock markets rose sharply this week. | thấp | 0.0731 | Đúng (mock) |
| 3 | Machine learning uses algorithms. | Deep learning uses neural networks. | cao | -0.0399 | Sai (mock) |
| 4 | I love eating pizza. | The cat sat on the mat. | thấp | -0.1400 | Đúng (mock) |
| 5 | Data science extracts insights. | Statistical analysis reveals patterns. | cao | -0.2499 | Sai (mock) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> MockEmbedder không mã hoá ngữ nghĩa — băm MD5 thành seed rồi sinh vector giả ngẫu nhiên, dù đã chuẩn hoá ||v||=1. Do đó ngay cả hai câu đồng nghĩa (Pair 1) cũng có similarity ≈ 0. Điều này nhấn mạnh: embedding quality quyết định retrieval quality, và mock embeddings chỉ phù hợp cho kiểm tra cấu trúc, không phải đo similarity ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chiến lược của tôi: **Recursive Chunker** (chunk_size=200)

Chạy 5 câu hỏi đánh giá của nhóm trên bench.py với `BENCH_CHUNKER=recursive`.

| # | Câu hỏi (Query) | Top-1 Chunk (tóm tắt) | Score | Có liên quan? | Agent trả lời |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | CNTT có PLO nào? | it-majors#50: Học phần tự chọn | 0.3253 | Không |  |
| 2 | CN KHTC tổ hợp môn gì? | uav-robotics#46: Vị trí việc làm | 0.3289 | Không |  |
| 3 | Sinh viên sau TCH làm gì? | it-majors#9: Khởi nghiệp | 0.3760 | Một phần |  |
| 4 | Chương trình sv học kỳ nào? (filter) | cs-majors#56: Phân tích dữ liệu | 0.3043 | Không |  |
| 5 | AIoT kết hợp công nghệ nào? | rag_system_design#12: Đánh giá RAG | 0.3324 | Không |  |

> **Ghi chú:** Kết quả retrieval bị chi phối bởi MockEmbedder (vector ngẫu nhiên). Không phản ánh chất lượng thực sự của chiến lược chunking. Xem REPORT_NHOM mục 3 về A/B filter comparison.

**A/B Filter Comparison (Q4):**

| Lần | Top-1 | Top-2 | Top-3 | Nhận xét |
|-----|-------|-------|-------|----------|
| Có filter `audience:student` | cs-majors | semiconductor-majors | it-majors | Tất cả audience=student ✓ |
| Không filter | aiot-majors | aiot-majors | cs-majors | Trộn audience=all + student |

→ Filter loại bỏ tài liệu audience=all (UAV, AIoT) ra khỏi kết quả. Metadata filtering có ích.

**Bao nhiêu câu trả về chunk có liên quan trong top-3?** **5 / 5** (với mock embedding)

**Điều hay nhất tôi học được:**
> Biết dược cơ chế cách llm hiểu một từ bằng cách đưa từ ấy về vector, một dãy các giá trị số rồi so sánh với nhau thông qua góc hoặc khoảng cách để biết được từ nào gần nghĩa mà dự đoán

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30/  30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
