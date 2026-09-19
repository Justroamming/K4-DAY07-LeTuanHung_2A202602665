from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "No documents in the knowledge base. Cannot answer."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "No relevant documents found to answer the question."

        context_lines = []
        for i, result in enumerate(results, start=1):
            source = result.get("metadata", {}).get("source", "unknown")
            content = result["content"]
            context_lines.append(f"[{i}] (source: {source}) {content}")
        context = "\n".join(context_lines)

        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            f"Answer based ONLY on the provided context. "
            f"If the context does not contain the answer, say 'Not found in context.'\n"
        )
        return self.llm_fn(prompt)
