# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G50
**Thành viên:** Bùi Đình Đề
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Các ngành đào tạo đại học kỹ thuật tại Học viện Công nghệ Bưu chính Viễn thông (PTIT) và dịch vụ đại học.

**Tại sao nhóm chọn chủ đề này?**
> Các tài liệu về ngành đào tạo có cấu trúc rõ ràng (mục ## Điều, chương trình học kỳ), metadata phong phú (audience, department, category), phù hợp để đánh giá cả truy xuất ngữ nghĩa lẫn lọc metadata. Chủ đề kỹ thuật cũng giúp phân biệt rõ giữa các ngành khi test retrieval quality.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | uav-robotics-majors | https://daotao.ptit.edu.vn/chuong-trinh-dao-tao/chuong-trinh-uav-va-robot-di-dong-tu-hanh/ | 2026-09-19 | ~13KB | audience=all, department=academic-affairs, category=curriculum |
| 2 | space-majors | https://daotao.ptit.edu.vn/chuong-trinh-dao-tao/chuong-trinh-ky-thuat-truyen-thong-hang-khong-vu-tru/ | 2026-09-19 | ~14KB | audience=student, department=academic-affairs, category=curriculum |
| 3 | semiconductor-majors | https://daotao.ptit.edu.vn/chuong-trinh-dao-tao/chuong-trinh-cong-nghe-vi-mach-ban-dan/ | 2026-09-19 | ~14KB | audience=student, department=academic-affairs, category=curriculum |
| 4 | cs-majors | https://daotao.ptit.edu.vn/chuong-trinh-dao-tao/nganh-khoa-hoc-may-tinh/ | 2026-09-19 | ~15KB | audience=student, department=academic-affairs, category=curriculum |
| 5 | it-majors | https://daotao.ptit.edu.vn/chuong-trinh-dao-tao/nganh-cong-nghe-thong-tin/ | 2026-09-19 | ~20KB | audience=student, department=academic-affairs, category=curriculum |
| 6 | aiot-majors | https://daotao.ptit.edu.vn/chuong-trinh-dao-tao/tri-tue-nhan-tao-van-vat-aiot/ | 2026-09-19 | ~10KB | audience=all, department=academic-affairs, category=curriculum |
| 7 | library-services | (đại học) | 2026-08-02 | ~700B | audience=all, department=library, language=vi |
| 8 | course-registration | (đại học) | 2026-08-02 | ~600B | audience=student, department=academic-affairs, language=vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| audience | string | student/all/faculty/staff | Lọc theo đối tượng người dùng, tránh trộn tài liệu dành cho các nhóm khác nhau |
| department | string | academic-affairs/library | Lọc theo phòng ban chịu trách nhiệm |
| category | string | curriculum | Phân loại theo loại tài liệu |
| language | string | vi/en | Lọc theo ngôn ngữ tài liệu |
| source_url | string | URL | Truy vết nguồn gốc tài liệu |
| retrieved_at | date | 2026-09-19 | Đảm bảo thông tin còn cập nhật |
| doc_id | string | cs-majors | Định danh tài liệu gốc cho delete_document |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu (đã bỏ frontmatter):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| cs-majors (~15KB) | FixedSizeChunker (`fixed_size`) | 92 | 198.7 | Không — cắt giữa mục chương trình |
| cs-majors (~15KB) | SentenceChunker (`by_sentences`) | 17 | 780.1 | Một phần — nhiều câu quá dài |
| cs-majors (~15KB) | RecursiveChunker (`recursive`) | 83 | 162.3 | Tốt hơn — ưu tiên cắt theo cấu trúc |
| aiot-majors (~10KB) | FixedSizeChunker (`fixed_size`) | 76 | 199.5 | Không — cắt ngang đoạn |
| aiot-majors (~10KB) | SentenceChunker (`by_sentences`) | 10 | 1109.2 | Kém — sentences quá dài, chunk quá lớn |
| aiot-majors (~10KB) | RecursiveChunker (`recursive`) | 69 | 162.5 | Tốt hơn |
| chunking_experiment_report (~2KB) | FixedSizeChunker (`fixed_size`) | 15 | 198.7 | Trung bình |
| chunking_experiment_report (~2KB) | SentenceChunker (`by_sentences`) | 5 | 453.4 | Tốt — mỗi chunk ~1-2 đoạn |
| chunking_experiment_report (~2KB) | RecursiveChunker (`recursive`) | 16 | 140.8 | Tốt — giữ cấu trúc đoạn văn |

### Chiến lược của từng thành viên

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** Heading + Recursive (tùy chọn)
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản quy định và chương trình đào tạo được biên soạn theo mục (## Mục). HeadingChunker tách mỗi mục thành chunk, đảm bảo mỗi chunk có ngữ cảnh rõ ràng. Nếu mục quá dài, đệ quy hạ xuống recursive.
- **Code snippet:**
```python
from src.chunking import HeadingChunker
chunker = HeadingChunker(chunk_size=200)
chunks = chunker.chunk(text)
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:** Recursive
- **Mô tả & lý do chọn:** RecursiveChunker ưu tiên tách theo ranh giới lớn (đoạn văn, dòng trống) trước, chỉ hạ xuống nhỏ hơn khi cần. Phù hợp với tài liệu kỹ thuật có cấu trúc hỗn hợp. Đảm bảo không tạo chunk vụn.
- **Code snippet:**
```python
from src.chunking import RecursiveChunker
chunker = RecursiveChunker(chunk_size=200)
chunks = chunker.chunk(text)
```

**Thành viên 3 — [Tên]**
- **Loại chiến lược:** FixedSizeChunker
- **Mô tả & lý do chọn:** Fixed-size đơn giản, dự đoán được số lượng chunk. Phù hợp khi cần chunk đều nhau cho embedding model có giới hạn token. Tuy nhiên dễ cắt ngang ý nghĩa.
- **Code snippet:**
```python
from src.chunking import FixedSizeChunker
chunker = FixedSizeChunker(chunk_size=200, overlap=50)
chunks = chunker.chunk(text)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Thành viên 1 | Heading | TBD | Giữ ngữ cảnh theo mục | Ít phù hợp nếu tài liệu không có heading rõ ràng |
| Thành viên 2 | Recursive | TBD | Cân bằng, không chunk vụn | Triển khai phức tạp hơn |
| Thành viên 3 | FixedSize | TBD | Đơn giản, dự đoán được | Cắt ngang ý nghĩa |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Heading + Recursive là lựa chọn tốt nhất cho tài liệu đào tạo vì các mục chương trình (## Điều, học kỳ) đã là đơn vị ngữ nghĩa trọn vẹn do người soạn chia sẵn. Heading chunker giữ ngữ cảnh, recursive fallback xử lý phần dài. FixedSize phù hợp nhất khi cần đơn giản nhưng chất lượng thấp nhất.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Chương trình ngành Công nghệ thông tin có những chuẩn đầu ra (PLO) nào? | PLO1-Nhận diện vấn đề và đề xuất giải pháp IT; PLO2-Giao tiếp hiệu quả; PLO3-Nhận thức trách nhiệm nghề nghiệp; PLO4-Làm việc hiệu quả trong nhóm; PLO5-Thực hiện dự án nghiên cứu và phát triển. | it-majors (Phần Chuẩn đầu ra) |
| 2 | Ngành Khoa học máy tính yêu cầu tổ hợp môn xét tuyển nào? | Toán, Lý, Hóa (A00 – khối A); Toán, Lý, Anh văn (A01 – khối A1); Toán, Lý, Tin (X06); Toán, Tin, Anh (X26); hoặc các phương án xét tuyển riêng của Học viện. | cs-majors (Phần Điều kiện tuyển sinh) |
| 3 | Sinh viên sau khi tốt nghiệp có thể đảm nhận những vị trí công việc nào? | Cán bộ kỹ thuật, quản lý, điều hành trong lĩnh vực CNTT; lập trình viên, quản trị hệ thống; cán bộ nghiên cứu, giảng dạy; tiếp tục học sau đại học. | cs-majors (Phần Cơ hội nghề nghiệp) |
| 4 | Chương trình đào tạo dành cho sinh viên bao gồm những học kỳ nào và tín chỉ ra sao? | 9 học kỳ, tổng tín chỉ theo quy định chương trình, bao gồm học phần bắt buộc, tự chọn và thực tập. | cs-majors/it-majors (Cấu trúc chương trình) |
| 5 | Trí tuệ nhân tạo vạn vật (AIoT) kết hợp những công nghệ nào? | AIoT là sự kết hợp giữa Trí tuệ nhân tạo (AI) và Internet vạn vật (IoT), hướng đến tích hợp khả năng xử lý thông minh trực tiếp vào thiết bị IoT. | aiot-majors (Phần Cơ hội nghề nghiệp/Mô tả) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | Recursive/Heading | TBD | |
| 2 | | Recursive/Heading | TBD | |
| 3 | | Recursive/Heading | TBD | |
| 4 | | Recursive (có filter audience:student) | TBD | Cần lọc metadata để tránh lẫn tài liệu audience=all |
| 5 | | Recursive/Heading | TBD | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, lọc metadata `audience: student` giúp ích cho câu 4. Nếu không lọc, retrieval sẽ lẫn các tài liệu ngành đào tạo audience=all (UAV, AIoT) với các ngành dành riêng cho sinh viên (CS, IT), dẫn đến kết quả kém chính xác hơn. Đây là minh chứng cho tầm quan trọng của metadata filtering trong RAG.

**A/B Comparison — Q4 (Recursive Chunker):**

| Lần | Top-1 | Top-2 | Top-3 | Nhận xét |
|-----|-------|-------|-------|----------|
| Có filter `audience:student` | cs-majors | semiconductor-majors | it-majors | Tất cả audience=student ✓ |
| Không filter | aiot-majors | aiot-majors | cs-majors | Trộn audience=all + student ✗ |

→ Filter loại bỏ tài liệu audience=all ra khỏi kết quả, chỉ giữ tài liệu dành cho sinh viên. Metadata filtering có ích rõ rệt.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Mock embedding làm nhiễu hoàn toàn retrieval**: Với MockEmbedder (MD5 hash → vector ngẫu nhiên), ngay cả hai câu đồng nghĩa cũng có cosine similarity ≈ 0. Kết quả top-3 không phản ánh chất lượng chunking.
> 2. **Metadata filter thay đổi kết quả hoàn toàn**: Câu 4 (chương trình sinh viên) với filter `audience: student` chỉ trả về tài liệu dành cho sinh viên; không filter trả về trộn ngành audience=all (UAV, AIoT).
> 3. **Chunk đúng chủ đề ≠ chunk chứa đáp án**: Top-3 có thể cùng tài liệu vàng nhưng không chunk nào chứa thông tin cần tìm — đây là hạn chế khi đo retrieval chỉ bằng doc_id.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng tài liệu nhưng chiến lược khác nhau cho kết quả count/avg_length rất khác (fixed_size=443, by_sentences=145, recursive=529, heading=524). Tuy nhiên với mock embedding, không chiến lược nào vượt trội rõ ràng về retrieval quality. Trong thực tế (real embedding), recursive/heading sẽ tốt hơn vì giữ ngữ cảnh tốt hơn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Thêm tài liệu chi tiết hơn về quy định tuyển sinh và chương trình đào tạo cho từng ngành. Cân nhắc chia nhỏ theo heading để giữ ngữ cảnh section.

**Phân tích lỗi (Failure Case):**

**Câu hỏi hỏng:** Q1 — "Chương trình ngành Công nghệ thông tin có những chuẩn đầu ra (PLO) nào?"

**Vì sao:** Dùng recursive chunker (chunk_size=200), cả có và không filter. Top-3 trả về: it-majors#50 (học phần tự chọn), uav-robotics#44 (bắt buộc chung), cs-majors#49 (3 tín chỉ). **Không chunk nào chứa thông tin về PLO.** Thông tin PLO CÓ TRONG tài liệu it-majors (section "Chuẩn đầu ra"), nhưng recursive chunker chia section đó thành nhiều chunk con, và chunk chứa PLO cụ thể không lọt top-3. Đây là trường hợp "chunk đúng chủ đề nhưng không chứa đáp án" — cosine đo độ giống chủ đề, không đo mật độ thông tin trả lời được.

**Đề xuất cải thiện:** (1) Tăng chunk_size (ví dụ 500) để section "Chuẩn đầu ra" không bị cắt đôi. (2) Heading chunker sẽ giữ nguyên section lớn — khả năng cao giữ nguyên chunk chứa PLO. (3) Với real embedding, heading chunker sẽ giảm đáng kể failure case này.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
