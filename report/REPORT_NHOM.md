# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Chủ đề:** Quy chế Đào tạo và Dịch vụ Sinh viên Đại học Bách khoa Hà Nội (HUST)
**Ngày thực hiện:** 2026-09-20

### Danh sách thành viên & Phân công nhiệm vụ

| STT | Họ và tên | Mã sinh viên (MSSV) | Vai trò chính | Nhiệm vụ đảm nhiệm cụ thể |
|:---:|-----------|:-------------------:|:-------------:|---------------------------|
| 1 | **Bùi Đình Đề** *(Trưởng nhóm)* | **2A202602818** | **R1 & R3** (Data & Custom Chunking) | - Chủ trì thu thập, làm sạch và chuẩn hóa 8 văn bản Quy chế ĐHBK Hà Nội.<br>- Thiết kế cấu trúc Metadata Schema (8 trường).<br>- Thiết kế và cài đặt chiến lược chia đoạn nâng cao **`HeadingChunker`** (tự động gắn tiêu đề Điều vào chunk con). |
| 2 | **Lê Tuấn Hưng** | **2A202602665** | **R2 & R3** (Benchmark & Comparison) | - Chủ trì xây dựng 5 câu hỏi đánh giá (Benchmark Queries) & Gold Answers kiểm chứng từ tài liệu.<br>- Thực nghiệm đối chứng hai chiến lược baseline: **`RecursiveChunker`** và **`SentenceChunker`**.<br>- Triển khai kịch bản A/B Testing đánh giá hiệu quả Metadata Pre-filtering. |

> **Thang điểm nhóm: 40 điểm** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình / Bài học nhóm (5). (Chi tiết: `docs/SCORING.md`).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy chế Đào tạo và Dịch vụ Sinh viên Đại học Bách khoa Hà Nội (HUST) — Thư viện, Ký túc xá, Học vụ và Học bổng.

**Tại sao nhóm chọn chủ đề này?**
> Chủ đề bao quát các nhu cầu tra cứu thiết thực và thường xuyên nhất của người học và cán bộ trong trường đại học. Đặc biệt, các quy định có sự phân định ranh giới rõ ràng về quyền lợi, nghĩa vụ và hạn mức giữa các nhóm đối tượng (sinh viên, giảng viên, cán bộ viên chức), tạo điều kiện lý tưởng để chứng minh vai trò then chốt của metadata filtering trong hệ thống RAG thực tế.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy chế đào tạo: Đăng ký tín chỉ và cảnh báo học tập | https://ctt.hust.edu.vn | 2026-09-19 / 5445/QD-DHBK | 2.566 | audience: student, department: academic-affairs, category: regulations |
| 2 | Quy định xét cấp học bổng khuyến khích học tập | https://ctsv.hust.edu.vn | 2026-09-19 / not-stated | 2.327 | audience: student, department: student-affairs, category: scholarship |
- **Cosine similarity đo độ giống về chủ đề (Topical Relevance), không đo mật độ thông tin chứa câu trả lời (Informative Density):** Đoạn mở đầu (#0) và Điều 1 (#1) lặp lại liên tục các từ khóa lớn mang tính khái quát như *"Ký túc xá Bách Khoa"*, *"nội quy"*, *"sinh hoạt nội trú"*, *"phòng ở"*, khiến vector embedding bị kéo lệch điểm số rất cao về phía câu hỏi. Trong khi đó, đoạn Điều 2 chứa câu trả lời cụ thể (*"bếp gas"*, *"bếp từ"*, *"ấm siêu tốc"*) lại là các từ khóa hiếm gặp (low frequency), không đủ sức kéo vector lên Top-3.
   - **Hiện tượng các chunk anh em triệt tiêu lẫn nhau (Intra-document Competition):** Khi chia tài liệu theo heading mà không có overlap ngữ nghĩa, các section trong cùng một văn bản cạnh tranh điểm số khốc liệt. Section nào chứa nhiều từ khóa định danh của văn bản sẽ luôn chiếm ưu thế áp đảo so với section chứa chi tiết kỹ thuật.

3. **Giải pháp đề xuất cải thiện:**
   - **Tìm kiếm lai (Hybrid Search: Dense Vector + Sparse BM25):** Sử dụng BM25 với thuật toán TF-IDF tăng trọng số cho các từ khóa độc nhất như *"nấu ăn"*, *"bếp từ"*, *"ấm siêu tốc"*, giúp đẩy chunk Điều 2 vượt lên Top-1.
   - **Mô hình định tuyến hai giai đoạn (Two-stage Retrieval & Cross-Encoder Reranking):** Giai đoạn 1 dùng Bi-Encoder lấy Top-10; Giai đoạn 2 dùng mô hình Cross-Encoder để chấm điểm trực tiếp cặp `(Query, Chunk)` nhằm đo độ liên quan logic của câu trả lời thay vì đo khoảng cách vector embedding độc lập.
   - **Làm giàu ngữ cảnh (Context Enrichment):** Tự động trích xuất các từ khóa hành động/điều cấm trong section và đưa vào metadata của từng chunk con.

---

### Những bài học và phân tích hay nhất

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Cái bẫy điểm số Naive:** Nếu chỉ chấm theo `doc_id`, hệ thống đạt 10/10 điểm hoàn hảo. Nhưng khi soi vào cấp độ Fact-level, điểm số chỉ đạt 5/10. Sự chênh lệch 5 điểm này chứng minh rằng việc đánh giá RAG bắt buộc phải kiểm tra đến nội dung thông tin thực tế.
> 2. **Kiến trúc Data-Centric quan trọng hơn Model:** Chuẩn hóa Markdown headings và gắn metadata phân loại đối tượng (`audience`) mang lại bước nhảy vọt về chất lượng truy xuất mà không tốn chi phí huấn luyện mô hình.
> 3. **Pre-filtering là khiên chắn chống Hallucination:** Lọc metadata trước khi search giúp triệt tiêu hoàn toàn rủi ro nhầm lẫn giữa các nhóm đối tượng có chung từ vựng trong trường đại học.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một tập dữ liệu 8 file quy chế ĐHBK Hà Nội, việc chọn chiến lược chia đoạn quyết định trực tiếp khả năng sống còn của thông tin: FixedSize xé nát quy định, Sentence gom cụm không kiểm soát được độ dài, còn HeadingChunker bảo tồn tốt nhất ranh giới pháp lý của các Điều khoản.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ: (1) Bổ sung trường metadata `section_type` (preamble, rule, penalty) để có thể lọc bỏ các chunk mở đầu khi câu hỏi mang tính chất tra cứu cụ thể; (2) Triển khai Two-stage Reranking bằng Cross-Encoder; (3) Tăng kích thước cửa sổ trượt (sliding overlap) ở các Điều quy chế dài để thông tin không bị cô lập.


---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |