from __future__ import annotations

import os
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.chunking import (
    FixedSizeChunker,
    HeadingChunker,
    RecursiveChunker,
    SentenceChunker,
)
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

DATA_DIR = Path(__file__).parent / "data"

CHUNK_SIZE = 200

BENCHMARK_QUERIES = [
    {
        "query": "Chương trình ngành Công nghệ thông tin có những chuẩn đầu ra (PLO) nào?",
        "gold": "PLO1-Nhận diện vấn đề và đề xuất giải pháp; PLO2-Giao tiếp hiệu quả; PLO3-Nhận thức trách nhiệm nghề nghiệp; PLO4-Làm việc hiệu quả trong nhóm; PLO5-Thực hiện dự án nghiên cứu và phát triển.",
        "filter": None,
    },
    {
        "query": "Ngành Khoa học máy tính yêu cầu tổ hợp môn xét tuyển nào?",
        "gold": "Toán, Lý, Hóa (A00); Toán, Lý, Anh (A01); Toán, Lý, Tin (X06); Toán, Tin, Anh (X26); hoặc các phương án xét tuyển riêng của Học viện.",
        "filter": None,
    },
    {
        "query": "Sinh viên sau khi tốt nghiệp có thể đảm nhận những vị trí công việc nào?",
        "gold": "Cán bộ kỹ thuật, quản lý, điều hành; lập trình viên, quản trị hệ thống; cán bộ nghiên cứu, giảng dạy; tiếp tục học sau đại học.",
        "filter": None,
    },
    {
        "query": "Chương trình đào tạo dành cho sinh viên bao gồm những học kỳ nào và tín chỉ ra sao?",
        "gold": "Chương trình kéo dài 9 học kỳ, tổng cộng 154 tín chỉ (30 tín chỉ học phần tự chọn, phần còn lại là học phần bắt buộc và thực tập).",
        "filter": {"audience": "student"},
    },
    {
        "query": "Trí tuệ nhân tạo vạn vật (AIoT) kết hợp những công nghệ nào?",
        "gold": "AIoT là sự kết hợp giữa Trí tuệ nhân tạo (AI) và Internet vạn vật (IoT), hướng đến tích hợp khả năng xử lý thông minh trực tiếp vào thiết bị IoT.",
        "filter": None,
    },
]

CHUNKERS = {
    "fixed_size": FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=0),
    "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
    "recursive": RecursiveChunker(chunk_size=CHUNK_SIZE),
    "heading": HeadingChunker(chunk_size=CHUNK_SIZE),
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        raw_fm = match.group(1)
        body = match.group(2).strip()
        frontmatter: dict = {}
        for line in raw_fm.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                frontmatter[key.strip()] = value
        return frontmatter, body
    return {}, text.strip()


def load_documents_from_data(data_dir: Path, chunker_strategy: str = "recursive") -> list[Document]:
    chunker = CHUNKERS[chunker_strategy]
    documents: list[Document] = []

    for md_file in sorted(data_dir.rglob("*.md")):
        frontmatter, body = parse_frontmatter(md_file.read_text(encoding="utf-8"))
        if not body:
            continue

        chunks = chunker.chunk(body)
        if not chunks:
            chunks = [body]

        doc_id_base = frontmatter.get("doc_id", md_file.stem)
        for i, chunk in enumerate(chunks):
            doc_id = f"{doc_id_base}#{i}"
            metadata = {**frontmatter, "doc_id": doc_id_base}
            documents.append(Document(id=doc_id, content=chunk, metadata=metadata))

    return documents


def run_benchmark(store: EmbeddingStore, queries: list[dict]) -> list[dict]:
    results = []
    for q in queries:
        search_results = store.search_with_filter(
            q["query"], top_k=3, metadata_filter=q.get("filter")
        )
        results.append(
            {
                "query": q["query"],
                "filter": q.get("filter"),
                "results": search_results,
            }
        )
    return results


def print_results(results: list[dict]) -> None:
    for r in results:
        print(f"\n{'=' * 80}")
        print(f"Query: {r['query']}")
        if r["filter"]:
            print(f"Filter: {r['filter']}")
        print(f"{'=' * 80}")
        for i, result in enumerate(r["results"], start=1):
            content_preview = result["content"][:200].replace("\n", " ")
            score = result["score"]
            doc_id = result.get("metadata", {}).get("doc_id", "N/A")
            print(f"  [{i}] score={score:.4f} doc_id={doc_id}")
            print(f"      {content_preview}...")


def main() -> None:
    strategy = os.environ.get("BENCH_CHUNKER", "recursive")
    if strategy not in CHUNKERS:
        print(f"Unknown chunker strategy: {strategy}. Available: {list(CHUNKERS.keys())}")
        sys.exit(1)

    print(f"=== Benchmark (chunker: {strategy}) ===")

    documents = load_documents_from_data(DATA_DIR, chunker_strategy=strategy)
    print(f"\nLoaded {len(documents)} chunks from {len(set(d.metadata.get('doc_id', '') for d in documents))} documents")

    store = EmbeddingStore(collection_name="benchmark", embedding_fn=_mock_embed)
    store.add_documents(documents)
    print(f"Stored {store.get_collection_size()} chunks in EmbeddingStore")

    results = run_benchmark(store, BENCHMARK_QUERIES)
    print_results(results)


if __name__ == "__main__":
    main()
