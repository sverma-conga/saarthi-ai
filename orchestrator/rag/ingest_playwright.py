"""
Playwright-based RAG ingestion for JavaScript-rendered documentation sites.

Uses requests for fast link discovery + Playwright for JS content rendering.

Usage:
    cd orchestrator
    python -m rag.ingest_playwright
"""

import os
import sys
import shutil
import time
from urllib.parse import urljoin, urlparse

import requests as req
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import get_settings
from rag.ingest import _discover_links

PERSIST_DIR = os.path.join(os.path.dirname(__file__), "vector_store")
ROOT_URL = "https://documentation.conga.com/en/clm-for-advantage-platform/current/clm-for-users/"
MAX_PAGES = 50


def discover_links_fast(root_url: str, max_pages: int = MAX_PAGES) -> list[str]:
    """Use requests + BeautifulSoup for fast link discovery (no JS needed for links)."""
    parsed_root = urlparse(root_url)
    root_path = parsed_root.path.rstrip("/")

    visited = set()
    to_visit = [root_url]
    discovered = []

    print(f"🔍 Discovering pages under {root_url} (fast mode)...")

    while to_visit and len(discovered) < max_pages:
        url = to_visit.pop(0)
        url = url.split("#")[0].split("?")[0]
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = req.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            if resp.status_code != 200:
                continue
        except Exception:
            continue

        discovered.append(url)

        soup = BeautifulSoup(resp.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(url, href).split("#")[0].split("?")[0]
            parsed = urlparse(full_url)
            if (
                parsed.netloc == parsed_root.netloc
                and parsed.path.startswith(root_path)
                and full_url not in visited
                and full_url not in to_visit
            ):
                to_visit.append(full_url)

    print(f"✅ Discovered {len(discovered)} pages")
    return discovered


def extract_content(page) -> str:
    """Extract main text content from the rendered page."""
    # Remove noise elements first, then get text from content area
    try:
        text = page.evaluate("""() => {
            // Remove noise
            document.querySelectorAll('nav, header, footer, .cookie-notice, [role="navigation"], .sidebar, .breadcrumb').forEach(el => el.remove());
            
            // Try specific content selectors
            const selectors = ['article', '[role="main"]', 'main', '.topic-content', '.content-body', '#content'];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.trim().length > 200) {
                    return el.innerText.trim();
                }
            }
            // Fallback to body
            return document.body.innerText.trim();
        }""")
        return text if text else ""
    except:
        return ""


def main():
    print("🚀 SAARTHI AI — Playwright-based Documentation Ingestion")
    print(f"   Target: {ROOT_URL}")
    print(f"   Max pages: {MAX_PAGES}")
    print()

    # Clear old vector store
    if os.path.isdir(PERSIST_DIR):
        gitkeep = os.path.join(PERSIST_DIR, ".gitkeep")
        has_gitkeep = os.path.isfile(gitkeep)
        shutil.rmtree(PERSIST_DIR)
        os.makedirs(PERSIST_DIR, exist_ok=True)
        if has_gitkeep:
            open(gitkeep, "w").close()
        print("🗑️  Cleared old vector store")

    # Step 1: Fast link discovery (reuse working function from ingest.py)
    urls = _discover_links(ROOT_URL, MAX_PAGES)
    if not urls:
        print("❌ No URLs discovered. Exiting.")
        return

    # Step 2: Use Playwright to render and extract content
    documents = []
    print(f"\n📄 Extracting content from {len(urls)} pages with Playwright...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for i, url in enumerate(urls):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                # Wait for content to render (SPA needs a moment)
                page.wait_for_timeout(2000)

                content = extract_content(page)
                title = page.title()

                if len(content) < 50 or "unsupported browser" in content.lower():
                    # Try waiting a bit longer
                    page.wait_for_timeout(3000)
                    content = extract_content(page)
                    title = page.title()

                if len(content) < 50 or "unsupported browser" in content.lower():
                    print(f"  ⚠ [{i+1}/{len(urls)}] Skipped (no content): {url}")
                    continue

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": url,
                        "title": title,
                        "source_type": "crawl",
                        "root_url": ROOT_URL,
                    }
                )
                documents.append(doc)
                print(f"  ✅ [{i+1}/{len(urls)}] {title[:50]} ({len(content)} chars)")

            except Exception as e:
                print(f"  ⚠ [{i+1}/{len(urls)}] Error: {url} — {e}")

        browser.close()

    print(f"\n📊 Loaded {len(documents)} documents with real content")

    if not documents:
        print("❌ No documents loaded. Exiting.")
        return

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"✂️  Split into {len(chunks)} chunks")

    # Embed and store
    settings = get_settings()
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
    )

    print("🔄 Embedding chunks into ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )

    print(f"\n✅ Successfully ingested {len(chunks)} chunks from {len(documents)} pages into vector store!")
    print(f"   Vector store location: {PERSIST_DIR}")


if __name__ == "__main__":
    main()
