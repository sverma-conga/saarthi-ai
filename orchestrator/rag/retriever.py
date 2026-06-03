"""
RAG Retriever — Query the vector store for relevant knowledge context.
"""

import os
import logging

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

logger = logging.getLogger(__name__)

PERSIST_DIR = os.path.join(os.path.dirname(__file__), "vector_store")


def get_vectorstore() -> Chroma | None:
    """Load persisted ChromaDB vector store."""
    if not os.path.isdir(PERSIST_DIR) or not os.listdir(PERSIST_DIR):
        logger.info("Vector store not found — RAG disabled")
        return None

    # Skip if only .gitkeep
    files = [f for f in os.listdir(PERSIST_DIR) if f != ".gitkeep"]
    if not files:
        return None

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings,
    )


def retrieve_context(query: str, k: int = 3) -> str:
    """Get relevant KT knowledge for the user's query.

    Returns concatenated document excerpts or a fallback message.
    """
    vectorstore = get_vectorstore()
    if vectorstore is None:
        return ""

    try:
        docs = vectorstore.similarity_search(query, k=k)
    except Exception as e:
        logger.warning("Vector search failed: %s", e)
        return ""

    if not docs:
        return ""

    return "\n\n---\n\n".join(doc.page_content for doc in docs)
