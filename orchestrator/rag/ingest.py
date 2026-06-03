"""
RAG Document Ingestion — Load KT docs + web resources into ChromaDB vector store.

Supports:
  - Local files: PDF, Markdown, TXT
  - Web URLs: Any webpage (HTML scraped)
  - Sitemaps: Crawl multiple pages from a sitemap URL
  - Crawl: Recursively follow links from a root documentation page

Configure sources in rag/sources.json or pass URLs directly via CLI.

Usage:
    cd orchestrator
    python -m rag.ingest                                    # Ingest from sources.json
    python -m rag.ingest --url https://example.com/doc      # Ingest a single URL
    python -m rag.ingest --crawl https://docs.example.com/  # Crawl all sub-pages
    python -m rag.ingest --urls urls.txt                    # Ingest URLs from a file
"""

import json
import os
import re
import logging
import argparse
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
    WebBaseLoader,
    SitemapLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

logger = logging.getLogger(__name__)

PERSIST_DIR = os.path.join(os.path.dirname(__file__), "vector_store")
KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "knowledge-base", "docs"
)
SOURCES_FILE = os.path.join(os.path.dirname(__file__), "sources.json")


def _load_sources_config() -> list[dict]:
    """Load source definitions from sources.json."""
    if not os.path.isfile(SOURCES_FILE):
        return []
    with open(SOURCES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return [s for s in data.get("sources", []) if s.get("enabled", True)]


def _load_local_docs() -> list:
    """Load documents from the local knowledge-base/docs directory."""
    if not os.path.isdir(KNOWLEDGE_DIR):
        logger.info("Knowledge directory not found: %s", KNOWLEDGE_DIR)
        return []

    loaders = [
        DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader, silent_errors=True),
        DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.md", loader_cls=TextLoader, silent_errors=True),
        DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.txt", loader_cls=TextLoader, silent_errors=True),
    ]

    docs = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            logger.warning("Local loader error: %s", e)
    return docs


def _load_url_docs(urls: list[str]) -> list:
    """Load documents from web URLs."""
    if not urls:
        return []

    docs = []
    for url in urls:
        try:
            loader = WebBaseLoader(url)
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["source_type"] = "url"
                doc.metadata["source_url"] = url
            docs.extend(loaded)
            print(f"  📄 Loaded URL: {url} ({len(loaded)} pages)")
        except Exception as e:
            logger.warning("URL load error for %s: %s", url, e)
            print(f"  ⚠  Failed to load URL: {url} — {e}")
    return docs


def _load_sitemap_docs(sitemap_url: str, filter_pattern: str = None, max_pages: int = 50) -> list:
    """Load documents from a sitemap URL."""
    try:
        kwargs = {}
        if filter_pattern:
            kwargs["filter_urls"] = [re.compile(filter_pattern)]

        loader = SitemapLoader(sitemap_url, **kwargs)
        docs = loader.load()

        if max_pages and len(docs) > max_pages:
            docs = docs[:max_pages]

        for doc in docs:
            doc.metadata["source_type"] = "sitemap"
            doc.metadata["sitemap_url"] = sitemap_url

        print(f"  🗺️  Loaded sitemap: {sitemap_url} ({len(docs)} pages)")
        return docs
    except Exception as e:
        logger.warning("Sitemap load error for %s: %s", sitemap_url, e)
        print(f"  ⚠  Failed to load sitemap: {sitemap_url} — {e}")
        return []


def _load_single_file(file_path: str) -> list:
    """Load a single file by path."""
    abs_path = os.path.join(os.path.dirname(__file__), "..", file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(abs_path):
        print(f"  ⚠  File not found: {abs_path}")
        return []

    try:
        if abs_path.lower().endswith(".pdf"):
            loader = PyPDFLoader(abs_path)
        else:
            loader = TextLoader(abs_path)
        docs = loader.load()
        print(f"  📄 Loaded file: {file_path} ({len(docs)} pages)")
        return docs
    except Exception as e:
        logger.warning("File load error for %s: %s", file_path, e)
        print(f"  ⚠  Failed to load file: {file_path} — {e}")
        return []


def _discover_links(root_url: str, max_pages: int = 50) -> list[str]:
    """Discover all sub-page links from a root documentation URL.

    Follows links that share the same URL path prefix as root_url.
    """
    parsed_root = urlparse(root_url)
    root_path = parsed_root.path.rstrip("/")
    base_domain = f"{parsed_root.scheme}://{parsed_root.netloc}"

    visited = set()
    to_visit = [root_url]
    discovered = []

    print(f"  🔍 Discovering pages under {root_url} ...")

    while to_visit and len(discovered) < max_pages:
        url = to_visit.pop(0)

        # Normalize
        url = url.split("#")[0].split("?")[0]
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "SAARTHI-AI-Bot/1.0 (Knowledge Ingestion)"
            })
            if resp.status_code != 200:
                continue
            if "text/html" not in resp.headers.get("content-type", ""):
                continue
        except Exception as e:
            logger.debug("Request failed for %s: %s", url, e)
            continue

        discovered.append(url)

        # Parse links
        soup = BeautifulSoup(resp.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(url, href).split("#")[0].split("?")[0]

            # Only follow links within the same path prefix
            parsed = urlparse(full_url)
            if (
                parsed.netloc == parsed_root.netloc
                and parsed.path.startswith(root_path)
                and full_url not in visited
                and len(discovered) + len(to_visit) < max_pages * 2
            ):
                to_visit.append(full_url)

    print(f"  🔍 Discovered {len(discovered)} pages")
    return discovered


def _load_crawl_docs(root_url: str, max_pages: int = 50) -> list:
    """Crawl a documentation site: discover sub-pages, then load them all.

    This is ideal for documentation sites like:
    https://documentation.conga.com/en/clm-for-advantage-platform/current/clm-for-users/
    """
    urls = _discover_links(root_url, max_pages=max_pages)
    if not urls:
        print(f"  ⚠  No pages discovered from {root_url}")
        return []

    docs = []
    for i, url in enumerate(urls):
        try:
            loader = WebBaseLoader(url)
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["source_type"] = "crawl"
                doc.metadata["source_url"] = url
                doc.metadata["root_url"] = root_url
            docs.extend(loaded)
            print(f"  📄 [{i+1}/{len(urls)}] Loaded: {url}")
        except Exception as e:
            logger.warning("Crawl load error for %s: %s", url, e)
            print(f"  ⚠  [{i+1}/{len(urls)}] Failed: {url} — {e}")

    print(f"  🌐 Crawl complete: {len(docs)} pages from {root_url}")
    return docs


def ingest_documents(extra_urls: list[str] = None, crawl_urls: list[str] = None) -> Chroma:
    """Load KT docs from all configured sources and create/update the vector store.

    Args:
        extra_urls: Additional single-page URLs to ingest (from CLI arguments).
        crawl_urls: Documentation root URLs to recursively crawl (from CLI arguments).
    """
    all_docs = []

    # --- 1. Load from sources.json ---
    sources = _load_sources_config()
    print(f"\n📚 Loading from {len(sources)} configured sources...")

    for source in sources:
        source_type = source.get("type", "directory")

        if source_type == "directory":
            docs = _load_local_docs()
            all_docs.extend(docs)
            print(f"  📂 Local docs: {len(docs)} documents")

        elif source_type == "url":
            url = source.get("url")
            if url:
                docs = _load_url_docs([url])
                all_docs.extend(docs)

        elif source_type == "sitemap":
            sitemap_url = source.get("url")
            if sitemap_url:
                docs = _load_sitemap_docs(
                    sitemap_url,
                    filter_pattern=source.get("filter_pattern"),
                    max_pages=source.get("max_pages", 50),
                )
                all_docs.extend(docs)

        elif source_type == "file":
            file_path = source.get("path")
            if file_path:
                docs = _load_single_file(file_path)
                all_docs.extend(docs)

        elif source_type == "crawl":
            crawl_url = source.get("url")
            if crawl_url:
                docs = _load_crawl_docs(
                    crawl_url,
                    max_pages=source.get("max_pages", 50),
                )
                all_docs.extend(docs)

    # --- 2. Load extra URLs from CLI ---
    if extra_urls:
        print(f"\n🔗 Loading {len(extra_urls)} additional URLs...")
        url_docs = _load_url_docs(extra_urls)
        all_docs.extend(url_docs)

    # --- 3. Crawl documentation sites from CLI ---
    if crawl_urls:
        for crawl_url in crawl_urls:
            print(f"\n🌐 Crawling documentation site: {crawl_url}")
            crawl_docs = _load_crawl_docs(crawl_url, max_pages=50)
            all_docs.extend(crawl_docs)

    # --- 4. Check results ---
    if not all_docs:
        print("\n⚠  No documents found from any source.")
        print("   Options:")
        print("   - Place PDF/MD/TXT files in orchestrator/knowledge-base/docs/")
        print("   - Add URL sources to orchestrator/rag/sources.json")
        print("   - Run: python -m rag.ingest --url https://your-doc-url.com")
        return None

    # --- 5. Split into chunks ---
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(all_docs)

    # --- 6. Create vector store ---
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )

    print(f"\n✅ Ingested {len(chunks)} chunks from {len(all_docs)} documents")
    return vectorstore


def _parse_args():
    parser = argparse.ArgumentParser(description="SAARTHI AI — RAG Document Ingestion")
    parser.add_argument(
        "--url", action="append", default=[],
        help="URL to ingest (can be used multiple times)"
    )
    parser.add_argument(
        "--urls", type=str, default=None,
        help="Path to a text file with one URL per line"
    )
    parser.add_argument(
        "--crawl", action="append", default=[],
        help="Root URL to recursively crawl (discovers sub-pages automatically)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=50,
        help="Max pages to crawl per root URL (default: 50)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    extra_urls = list(args.url)

    # Load URLs from file if provided
    if args.urls and os.path.isfile(args.urls):
        with open(args.urls, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    extra_urls.append(line)

    crawl_urls = list(args.crawl)

    ingest_documents(
        extra_urls=extra_urls or None,
        crawl_urls=crawl_urls or None,
    )
