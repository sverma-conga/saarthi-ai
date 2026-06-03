# SAARTHI AI — Technical Documentation

> **Voice-driven AI assistant for Conga CLM** — A Chrome extension that understands natural language, navigates enterprise UI, and executes tasks autonomously.

---

## Team & Ownership

| Developer | Module | Stack |
|-----------|--------|-------|
| **Shivam** | Chrome Extension (UI + DOM + Action Executor) | MV3, Shadow DOM, MediaRecorder |
| **Rohit** | Speech Module (STT + TTS) | FastAPI, Google SpeechRecognition, gTTS |
| **Gautam** | Orchestrator + RAG Engine | FastAPI, GPT-4o (GitHub Models), ChromaDB |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Chrome Extension (Alt+Shift+S)                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Voice (Mic) │→ │ STT (port    │→ │ content.js             │ │
│  │ MediaRecorder│  │  8000)       │  │ DOM analysis + routing │ │
│  └─────────────┘  └──────────────┘  └───────────┬────────────┘ │
│                                                   │              │
│  ┌─────────────────────────────────────────────── │ ───────────┐│
│  │ background/service-worker.js (CORS proxy)      ↓            ││
│  └────────────────────────────────────────────────┬────────────┘│
└───────────────────────────────────────────────────│─────────────┘
                                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator (port 8001)                                       │
│                                                                 │
│  Intent Classifier → Planner → Executor → Recovery              │
│         ↕                ↕                                      │
│     RAG Engine      Session Store                               │
│  (ChromaDB + BM25)  (TTL 30min)                                 │
└─────────────────────────────────────────────────────────────────┘
                                                    ↓
                                    { next_action, task_state }
                                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│  Extension executes action → re-observes DOM → sends back       │
│  Loops until done=true (max 10 iterations)                      │
└─────────────────────────────────────────────────────────────────┘
                                                    ↓
                                    TTS (port 8000) → audio playback
```

---

## How It Works (Observe → Think → Act Loop)

1. **User speaks or types** a command ("Show today's contracts")
2. **Extension captures DOM** — extracts 50 interactive elements with unique selectors
3. **Orchestrator classifies intent** → ACTION / GUIDE / KNOWLEDGE
4. **Planner generates steps** (business-level: "Open filter panel", "Enter date", "Apply")
5. **Executor maps step to DOM action** — uses real selectors from the DOM snapshot
6. **Extension executes ONE action** → waits → re-captures DOM
7. **Loop continues** until all steps complete or max 10 iterations
8. **TTS speaks** the final message

---

## API Contracts

### Extension → Orchestrator (POST `localhost:8001/api/process`)

```json
{
  "session_id": "uuid",
  "user_input": "Show today's contracts",
  "mode": "action | guide",
  "context": {
    "url": "https://app.congaclm.com/agreements",
    "page_title": "Agreement List",
    "interactive_elements": [
      { "id": "el-1", "tag": "button", "text": "Filter", "selector": "[data-testid='filter-btn']", "visible": true }
    ],
    "visible_text_summary": "Showing 25 agreements..."
  },
  "previous_actions": [],
  "error_from_last_action": null,
  "task_state": null
}
```

### Orchestrator → Extension

```json
{
  "session_id": "uuid",
  "message": "Opening filter panel. (step 1/3)",
  "mode": "action",
  "next_action": {
    "type": "click",
    "selector": "[data-testid='filter-btn']",
    "description": "Open filter panel"
  },
  "done": false,
  "follow_up": "Waiting for result of: Open filter panel",
  "task_state": {
    "goal": "Show today's contracts",
    "planned_steps": ["Open filter panel", "Enter today's date", "Apply filter"],
    "completed_steps": [],
    "pending_steps": ["Open filter panel", "Enter today's date", "Apply filter"],
    "retry_count": 0
  }
}
```

### Action Types

| Type | Parameters | Description |
|------|-----------|-------------|
| `click` | `selector` | Click an element |
| `type` | `selector`, `value` | Type text into input |
| `select` | `selector`, `value` | Select dropdown option |
| `scroll` | `direction`, `amount` | Scroll page/element |
| `wait` | `duration_ms` | Wait before next action |
| `navigate` | `url` | Navigate to URL |
| `submit` | `selector` | Submit a form |

---

## LLM Configuration

Uses **GitHub Models** (free GPT-4o access via GitHub PAT):

```env
OPENAI_API_KEY=ghp_your_github_personal_access_token
OPENAI_BASE_URL=https://models.inference.ai.azure.com
OPENAI_MODEL=gpt-4o
```

No OpenAI API key required. Any GitHub PAT with default scopes works.

---

## RAG Knowledge Base

**Status**: 50 pages of Conga CLM documentation ingested (134 chunks in ChromaDB).

**Source**: https://documentation.conga.com/en/clm-for-advantage-platform/current/clm-for-users/

**Ingestion**: Uses Playwright (headless Chromium) because the Conga docs site is a JavaScript SPA that requires browser rendering.

```bash
cd orchestrator
python -m rag.ingest_playwright   # Crawls + renders + embeds all pages
```

**Search Strategy**: Hybrid (BM25 keyword + Vector semantic) with Reciprocal Rank Fusion.

**Usage**: RAG context is injected into Planner, Guide Agent, and Knowledge responses automatically.

---

## Running the System

```bash
# 1. Speech Module (Rohit)
cd backend/Speech-Module
python -m uvicorn main:app --port 8000

# 2. Orchestrator (Gautam)
cd orchestrator
python -m uvicorn server:app --port 8001

# 3. Extension (Shivam)
# Chrome → chrome://extensions → Developer mode → Load unpacked → select extension/
# Press Alt+Shift+S on any page
```

**Prerequisites**: Python 3.12, ffmpeg on PATH, Chrome browser.

---

## Integration Design

| Connection | Mechanism | Fallback |
|-----------|-----------|----------|
| Extension → Orchestrator | HTTP via background service worker (CORS bypass) | Mock response engine (DOM-aware) |
| Extension → Speech STT | POST audio blob → JSON transcript | None (mic button disabled) |
| Extension → Speech TTS | POST text → MP3 stream | Silent (non-critical) |
| Orchestrator → LLM | AsyncOpenAI client → GitHub Models | None (500 error) |
| Orchestrator → RAG | ChromaDB + BM25 hybrid search | Empty context (LLM uses general knowledge) |

**Key design principle**: The extension always tries the live orchestrator first. Mock is ONLY a fallback for when the server is unreachable.

---

## File Map

```
extension/
├── manifest.json                ← MV3 config, Alt+Shift+S hotkey
├── background/service-worker.js ← CORS proxy + hotkey listener
├── content/content.js           ← Panel UI, voice, agentic loop (max 10 iterations)
├── content/overlay.js           ← Guide mode highlights + step navigation
├── utils/api-client.js          ← Orchestrator client + mock fallback
├── utils/dom-analyzer.js        ← Extract interactive elements
└── utils/action-executor.js     ← Execute click/type/scroll/wait/navigate/submit

backend/Speech-Module/
├── main.py                      ← FastAPI (port 8000): /speech-to-text, /text-to-speech
└── services/                    ← Google STT (free), gTTS (free)

orchestrator/
├── server.py                    ← FastAPI (port 8001): /api/process, /health
├── agent.py                     ← Main brain: classify → plan → execute → recover
├── config.py                    ← .env settings (API key, base URL, model)
├── agents/
│   ├── intent_classifier.py     ← ACTION / GUIDE / KNOWLEDGE / NAVIGATION
│   ├── planner.py               ← Break goal into business steps (uses RAG)
│   ├── executor.py              ← Map step → DOM action using real selectors
│   ├── recovery.py              ← Error handling: retry, alt selectors, ask user
│   └── guide_agent.py           ← Step-by-step instructions with highlights
├── rag/
│   ├── ingest.py                ← Multi-source ingestion (URL/file/sitemap/crawl)
│   ├── ingest_playwright.py     ← JS-rendered site ingestion (Conga docs)
│   ├── retriever.py             ← Vector similarity search (ChromaDB)
│   ├── hybrid_search.py         ← BM25 + Vector with RRF fusion
│   └── sources.json             ← Knowledge source configuration
├── memory/session_store.py      ← In-memory session state (TTL 30min)
├── schemas/                     ← Pydantic request/response models
└── prompts/                     ← System prompts for each agent
```

---

## Verified Test Results (June 3, 2026)

| Test | Result |
|------|--------|
| Orchestrator `/health` | ✅ 200 OK |
| Speech TTS | ✅ 200 OK, audio/mpeg |
| Orchestrator action mode (real GPT-4o) | ✅ Returns `next_action` + `task_state` |
| Orchestrator knowledge mode (RAG) | ✅ Returns Conga CLM documentation context |
| RAG retrieval ("create a contract") | ✅ Returns real Conga docs (1000+ chars) |
| Extension mock fallback | ✅ DOM-aware responses when server unavailable |

---

*Last verified: June 3, 2026*
