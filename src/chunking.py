from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_text = " ".join(sentences[i:i + self.max_sentences_per_chunk])
            chunk_text = re.sub(r'\s+', ' ', chunk_text).strip()
            if chunk_text:
                chunks.append(chunk_text)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text.strip():
            return []
        if not remaining_separators:
            if len(current_text) <= self.chunk_size:
                return [current_text.strip()]
            return [current_text[i:i + self.chunk_size].strip() for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        rest = remaining_separators[1:]

        if sep == "":
            if len(current_text) <= self.chunk_size:
                return [current_text.strip()]
            return [current_text[i:i + self.chunk_size].strip() for i in range(0, len(current_text), self.chunk_size)]

        parts = current_text.split(sep)

        split_parts: list[str] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(part) > self.chunk_size and rest:
                sub = self._split(part, rest)
                split_parts.extend(sub)
            else:
                split_parts.append(part)

        if not split_parts:
            return []

        merged: list[str] = []
        current = split_parts[0]
        for part in split_parts[1:]:
            combined = current + sep + part
            if len(combined) <= self.chunk_size:
                current = combined
            else:
                merged.append(current)
                current = part
        merged.append(current)

        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_ab = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_ab / (norm_a * norm_b)


class HeadingChunker:
    """
    Split text by markdown headings (## or # lines), treating each section as a chunk.

    Long sections are recursively split with fallback separators.
    When a long section is cut, the heading is re-attached to each child chunk
    so every piece retains its context.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        lines = text.split("\n")
        chunks: list[str] = []
        current_heading = ""
        current_section: list[str] = []

        for line in lines:
            if line.startswith("## ") or line.startswith("# "):
                if current_section:
                    section_text = "\n".join(current_section).strip()
                    if section_text:
                        pieces = self._split_section(current_heading, section_text)
                        chunks.extend(pieces)
                current_heading = line.strip()
                current_section = []
            else:
                current_section.append(line)

        if current_section:
            section_text = "\n".join(current_section).strip()
            if section_text:
                pieces = self._split_section(current_heading, section_text)
                chunks.extend(pieces)

        return chunks

    def _split_section(self, heading: str, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [f"{heading}\n{text}".strip()]
        recursive = RecursiveChunker(chunk_size=self.chunk_size)
        parts = recursive.chunk(text)
        return [f"{heading}\n{part}".strip() for part in parts if part.strip()]


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        result: dict[str, dict] = {}

        fixed = FixedSizeChunker(chunk_size=chunk_size)
        fixed_chunks = fixed.chunk(text)
        result['fixed_size'] = {
            'count': len(fixed_chunks),
            'avg_length': sum(len(c) for c in fixed_chunks) / len(fixed_chunks) if fixed_chunks else 0,
            'chunks': fixed_chunks,
        }

        sentence = SentenceChunker()
        sentence_chunks = sentence.chunk(text)
        result['by_sentences'] = {
            'count': len(sentence_chunks),
            'avg_length': sum(len(c) for c in sentence_chunks) / len(sentence_chunks) if sentence_chunks else 0,
            'chunks': sentence_chunks,
        }

        recursive = RecursiveChunker(chunk_size=chunk_size)
        recursive_chunks = recursive.chunk(text)
        result['recursive'] = {
            'count': len(recursive_chunks),
            'avg_length': sum(len(c) for c in recursive_chunks) / len(recursive_chunks) if recursive_chunks else 0,
            'chunks': recursive_chunks,
        }

        return result
