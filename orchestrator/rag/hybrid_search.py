"""
Hybrid Search — Combines BM25 (keyword) + Vector (semantic) search for better retrieval.

Benefits:
- BM25 catches exact UI labels and product terms
- Vector search captures semantic meaning
- Reciprocal Rank Fusion merges results
"""

import logging
from typing import Optional

from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document

from .retriever import get_vectorstore

logger = logging.getLogger(__name__)


def hybrid_search(query: str, k: int = 3) -> str:
    """Run hybrid BM25 + vector search, fuse results with RRF."""

    vectorstore = get_vectorstore()
    if vectorstore is None:
        return ""

    # --- Vector search ---
    try:
        vector_docs = vectorstore.similarity_search(query, k=k * 2)
    except Exception as e:
        logger.warning("Vector search error: %s", e)
        vector_docs = []

    # --- BM25 keyword search ---
    bm25_docs: list[Document] = []
    try:
        all_docs = vectorstore.similarity_search("", k=200)  # fetch corpus
        if all_docs:
            bm25 = BM25Retriever.from_documents(all_docs, k=k * 2)
            bm25_docs = bm25.invoke(query)
    except Exception as e:
        logger.warning("BM25 search error: %s", e)

    # --- Reciprocal Rank Fusion ---
    fused = _reciprocal_rank_fusion([vector_docs, bm25_docs], k=k)

    if not fused:
        return ""

    return "\n\n---\n\n".join(doc.page_content for doc in fused)


def _reciprocal_rank_fusion(
    result_lists: list[list[Document]], k: int = 3, rrf_k: int = 60
) -> list[Document]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion.

    Score = sum(1 / (rrf_k + rank)) across all lists.
    """
    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    for result_list in result_lists:
        for rank, doc in enumerate(result_list):
            key = doc.page_content[:200]  # deduplicate by content prefix
            if key not in doc_map:
                doc_map[key] = doc
                scores[key] = 0.0
            scores[key] += 1.0 / (rrf_k + rank)

    sorted_keys = sorted(scores, key=scores.get, reverse=True)
    return [doc_map[key] for key in sorted_keys[:k]]
