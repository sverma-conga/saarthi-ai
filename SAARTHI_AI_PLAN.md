# SAARTHI AI — Hackathon Execution Plan

> **Voice-driven AI assistant for Conga CLM** — Browser extension that understands user intent, navigates UI, and executes tasks via natural language/voice commands.

---

## Team

| Developer | IDE | Module Ownership | Status |
|-----------|-----|-----------------|--------|
| **Shivam** | VS Code | Chrome Extension (UI + DOM + Action Executor) | ✅ Complete |
| **Rohit** | PyCharm | Python Backend (FastAPI server + Voice/TTS) | ✅ Complete |
| **Gautam** | PyCharm/VS Code | LLM Orchestrator + RAG Knowledge Engine | ✅ Complete |

---

## Repository Structure

```
saarthi-ai/
│
├── README.md
├── SAARTHI_AI_PLAN.md              ← This file
│
├── contracts/                       ← 🔴 SHARED — DO NOT MODIFY WITHOUT TEAM AGREEMENT
│   └── (request/response schemas defined below)
│
├── extension/                       ← 🔵 SHIVAM ✅ COMPLETE
│   ├── manifest.json               ← MV3, Alt+Shift+S hotkey, all_urls
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.css
│   │   └── popup.js
│   ├── content/
│   │   ├── content.js              ← Panel UI + voice recording + routing
│   │   ├── overlay.js              ← Guide mode highlights + step navigation
│   │   └── content.css
│   ├── background/
│   │   └── service-worker.js       ← Hotkey listener + API proxy (CORS bypass)
│   ├── utils/
│   │   ├── dom-analyzer.js         ← Extract 50 interactive elements
│   │   ├── action-executor.js      ← Execute click/type/select/scroll/wait/navigate
│   │   └── api-client.js           ← Routes calls via background worker + mock fallback
│   └── assets/
│       └── icons/
│
├── backend/                         ← 🟢 ROHIT ✅ COMPLETE
│   ├── Speech-Module/
│   │   ├── main.py                 ← FastAPI app (port 8000)
│   │   ├── config.py               ← Settings (OpenAI key for /pipeline only)
│   │   ├── schemas.py              ← Pydantic models
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── services/
│   │       ├── speech_to_text.py   ← Google SpeechRecognition (free)
│   │       ├── text_to_speech.py   ← gTTS (free)
│   │       └── ai_service.py       ← OpenAI chat (for /pipeline)
│   ├── api/
│   └── voice/
│
├── orchestrator/                    ← 🟡 GAUTAM ✅ COMPLETE
│   ├── __init__.py
│   ├── server.py                   ← FastAPI server (port 8001)
│   ├── agent.py                    ← Main orchestration loop (observe→think→act)
│   ├── config.py                   ← Settings (.env based)
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   ├── intent_classifier.py    ← ACTION/GUIDE/KNOWLEDGE/NAVIGATION/UNKNOWN
│   │   ├── planner.py              ← Business-level step planner
│   │   ├── executor.py             ← Maps step → DOM action (single action)
│   │   ├── recovery.py             ← Error recovery + retry strategies
│   │   └── guide_agent.py          ← Step-by-step guide generation
│   ├── memory/
│   │   └── session_store.py        ← In-memory session state with TTL
│   ├── rag/
│   │   ├── ingest.py               ← Load docs + URLs + sitemaps → vector store
│   │   ├── retriever.py            ← Vector similarity search
│   │   ├── hybrid_search.py        ← BM25 + Vector with RRF fusion
│   │   ├── sources.json            ← Configurable knowledge sources (URLs, files)
│   │   └── vector_store/           ← ChromaDB persistence (gitignored)
│   ├── schemas/
│   │   ├── request.py              ← Pydantic request models
│   │   └── response.py             ← Pydantic response models
│   ├── prompts/
│   │   ├── intent_classifier.md
│   │   ├── planner.md
│   │   ├── executor.md
│   │   ├── recovery.md
│   │   └── guide.md
│   └── knowledge-base/
│       └── docs/                   ← PDF, markdown, transcripts
│
└── tests/
    └── mock_dom_snapshots/
```

---

## Integration Contract (THE MOST CRITICAL PART)

All three modules communicate through ONE API endpoint. This schema is locked.

### Request: Extension → Orchestrator

```json
{
  "session_id": "uuid-string",
  "user_input": "Show today's contracts",
  "mode": "action | guide",
  "context": {
    "url": "https://app.congaclm.com/agreements",
    "page_title": "Agreement List",
    "interactive_elements": [
      {
        "id": "el-1",
        "tag": "button",
        "text": "Filter",
        "selector": "[data-testid='filter-btn']",
        "aria_label": "Open filters",
        "visible": true
      }
    ],
    "visible_text_summary": "Showing 25 agreements. Columns: Name, Status, Created Date, Owner..."
  },
  "previous_actions": [],
  "error_from_last_action": null
}
```

### Response: Orchestrator → Extension

**Action Mode:**
```json
{
  "session_id": "uuid-string",
  "message": "I'll filter agreements to show today's contracts.",
  "mode": "action",
  "actions": [
    {"step": 1, "type": "click", "selector": "[data-testid='filter-btn']", "description": "Open filter panel"},
    {"step": 2, "type": "wait", "duration_ms": 500},
    {"step": 3, "type": "type", "selector": "#date-input", "value": "2025-07-25", "description": "Enter today's date"}
  ],
  "guide_steps": null,
  "done": false,
  "follow_up": "I'll verify the results after the filter is applied."
}
```

**Guide Mode:**
```json
{
  "session_id": "uuid-string",
  "message": "Here's how to create a contract:",
  "mode": "guide",
  "actions": null,
  "guide_steps": [
    {"step": 1, "instruction": "Click the '+ New Agreement' button in the top-right", "highlight_selector": "[data-testid='new-agreement-btn']"},
    {"step": 2, "instruction": "Select the agreement type from the dropdown", "highlight_selector": "#agreement-type-select"}
  ],
  "done": true,
  "follow_up": null
}
```

### Action Vocabulary

| Action Type | Parameters | Description |
|-------------|-----------|-------------|
| `click` | `selector` | Click an element |
| `type` | `selector`, `value` | Type text into input |
| `select` | `selector`, `value` | Select dropdown option |
| `scroll` | `direction`, `amount` | Scroll page/element |
| `wait` | `duration_ms` | Wait before next action |
| `navigate` | `url` | Navigate to URL |

---

## 🔵 SHIVAM — Chrome Extension (✅ COMPLETE)

### What Was Built

A Chrome Manifest V3 extension that:
1. Activates on **`Alt+Shift+S`** (avoids Chrome's built-in Ctrl+Shift+A conflict)
2. Shows a floating panel (shadow DOM isolated) with mic button, text input, mode toggle, response area
3. Records voice via **MediaRecorder API** → sends audio to Rohit's `/speech-to-text`
4. Analyzes current page DOM → extracts up to 50 interactive elements with unique selectors
5. Sends structured request (matching contract) to orchestrator (mock fallback when unavailable)
6. Receives response → executes actions OR shows guide highlights with step navigation
7. Plays TTS response via Rohit's `/text-to-speech`

### Architecture Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Voice capture | MediaRecorder API (not Web Speech API) | Keeps STT in Rohit's domain — collaborative |
| API calls | Routed through background service worker | Bypasses CORS without modifying Rohit's server |
| Orchestrator unavailable | Falls back to local mock responses | Allows full testing without Gautam's backend |
| Panel rendering | Shadow DOM | Avoids CSS conflicts with any host page |
| Selector priority | data-testid > id > aria-label > CSS path | Most reliable for modern web apps |

### File Responsibilities

| File | Purpose |
|------|---------|
| `manifest.json` | MV3 config, permissions, hotkey registration, content script loading |
| `background/service-worker.js` | Hotkey listener + HTTP proxy (all fetch calls route here to bypass CORS) |
| `content/content.js` | Panel UI, voice recording flow, request building, response routing |
| `content/content.css` | Root container positioning |
| `content/overlay.js` | Guide mode: pulsing highlights + tooltip with Prev/Next navigation |
| `utils/api-client.js` | Sends messages to background worker, mock orchestrator fallback |
| `utils/dom-analyzer.js` | Extracts interactive elements with unique selectors |
| `utils/action-executor.js` | Executes click/type/select/scroll/wait/navigate with visual feedback |
| `popup/popup.html` | Extension icon popup (status indicator) |

### How to Load & Test

1. Open `chrome://extensions` → enable Developer Mode
2. Click "Load unpacked" → select the `extension/` folder
3. Navigate to any webpage
4. Press **`Alt+Shift+S`** → panel appears
5. Type a command or click 🎤 to use voice

### Test Scenarios

| Input | Mode | Expected Behavior |
|-------|------|-------------------|
| "Show today's contracts" | Action | Mock returns action plan → executor attempts clicks → reports success/failure |
| "How do I navigate?" | Guide | Mock returns guide steps → tooltips appear with highlights + Prev/Next |
| Voice input via mic | Action | Audio recorded → sent to STT → transcript displayed → mock response + TTS plays |
| Any text (orchestrator down) | Either | Falls back to mock response → still works |

---

## 🟢 ROHIT — Speech Module (✅ COMPLETE)

### What Was Built

A FastAPI server at `http://localhost:8000` providing speech services.

### Endpoints

| Endpoint | Method | Input | Output | Used By Extension? |
|----------|--------|-------|--------|-------------------|
| `/speech-to-text` | POST | Audio file (webm/wav/mp3/ogg/flac) | `{ "transcript": "..." }` | ✅ Yes |
| `/text-to-speech` | POST | `?text=...` query param | Streamed MP3 audio | ✅ Yes |
| `/pipeline` | POST | Audio file | `{ transcript, ai_response, audio_url }` | ❌ Not used |
| `/pipeline/stream` | POST | Audio file | Streamed MP3 | ❌ Not used |

### Tech Stack
- **STT**: Google SpeechRecognition (free, no API key needed)
- **TTS**: gTTS — Google Text-to-Speech (free)
- **AI** (pipeline only): OpenAI GPT-4o (requires API key)
- **Audio conversion**: pydub + ffmpeg

### How to Run

```bash
cd backend/Speech-Module
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --port 8000
```

### Prerequisites
- Python 3.12+
- ffmpeg installed and on PATH (`winget install Gyan.FFmpeg`)

---

## Integration: Shivam ↔ Rohit (✅ VERIFIED)

### Data Flow

```
User clicks 🎤 → MediaRecorder captures webm audio
    ↓
Extension background worker → POST /speech-to-text (audio blob)
    ↓
Rohit's server → Google STT → returns { transcript }
    ↓
Extension displays transcript → builds request with DOM context
    ↓
Sends to orchestrator (mock fallback) → gets response
    ↓
Extension displays AI message
    ↓
Extension background worker → POST /text-to-speech?text=...
    ↓
Rohit's server → gTTS → returns MP3 stream
    ↓
Extension plays audio via <Audio> element
    ↓
Extension executes actions OR shows guide highlights
```

### Verified Test Results (Server Logs)

```
POST /speech-to-text HTTP/1.1  → 200 OK (multiple successful calls)
POST /text-to-speech?text=...  → 200 OK (TTS for all response types)
```

---

## 🟡 GAUTAM — Agentic Orchestrator + RAG Engine (✅ COMPLETE)

### What Was Built

An **agentic AI orchestrator** that operates as an autonomous UI agent — not a chatbot. It follows the **Observe → Think → Act → Observe** loop, returning only the **next single action** per request cycle. This dramatically improves reliability in dynamic enterprise UIs.

### Core Architecture

```
User Request
      ↓
Intent Classifier (ACTION / GUIDE / KNOWLEDGE / NAVIGATION)
      ↓
┌─────────────────────────────────────┐
│ Action Flow → Planner → Executor   │
│ Guide Flow  → Guide Agent          │
│ Knowledge Flow → RAG + LLM         │
└─────────────────────────────────────┘
      ↓
Single Next Action (or guide/answer)
      ↓
Extension Executes
      ↓
Updated DOM sent back
      ↓
Observe Again → Continue Until Done
```

### Agent Components

| Agent | File | Purpose |
|-------|------|---------|
| **Intent Classifier** | `agents/intent_classifier.py` | Categorize user input: ACTION, GUIDE, KNOWLEDGE, NAVIGATION, UNKNOWN |
| **Planner** | `agents/planner.py` | Break goal into business-level steps (no selectors) |
| **Executor** | `agents/executor.py` | Map ONE business step → ONE DOM action with real selector |
| **Recovery** | `agents/recovery.py` | Handle failures: alt selectors, scroll, retry, ask user (max 3 retries) |
| **Guide Agent** | `agents/guide_agent.py` | Generate step-by-step instructions with highlight selectors |
| **Session Memory** | `memory/session_store.py` | Track task state across multiple request/response cycles (TTL: 30 min) |

### RAG Knowledge Engine

| Component | File | Purpose |
|-----------|------|---------|
| **Ingestion** | `rag/ingest.py` | Load local files + web URLs + sitemaps into ChromaDB |
| **Retriever** | `rag/retriever.py` | Vector similarity search |
| **Hybrid Search** | `rag/hybrid_search.py` | BM25 (keyword) + Vector (semantic) with Reciprocal Rank Fusion |
| **Sources Config** | `rag/sources.json` | Configurable knowledge sources |

#### Supported Knowledge Sources

| Source Type | Description | Example |
|-------------|-------------|---------|
| `directory` | Local folder with PDF/MD/TXT files | `knowledge-base/docs/` |
| `url` | Single web page (HTML scraped) | `https://docs.conga.com/clm/overview` |
| `sitemap` | Crawl pages from sitemap XML | `https://docs.conga.com/sitemap.xml` |
| `file` | Single local file | `knowledge-base/docs/guide.pdf` |

#### Adding Knowledge Sources

**Option 1 — Edit `rag/sources.json`:**
```json
{
  "sources": [
    {
      "type": "directory",
      "path": "knowledge-base/docs",
      "enabled": true
    },
    {
      "type": "url",
      "url": "https://docs.conga.com/clm/latest/overview",
      "description": "Conga CLM Overview",
      "enabled": true
    },
    {
      "type": "sitemap",
      "url": "https://docs.conga.com/sitemap.xml",
      "filter_pattern": "/clm/",
      "max_pages": 50,
      "enabled": true
    }
  ]
}
```

**Option 2 — CLI:**
```bash
# Ingest a single URL
python -m rag.ingest --url https://docs.conga.com/clm/overview

# Ingest multiple URLs
python -m rag.ingest --url https://url1.com --url https://url2.com

# Ingest URLs from a file (one per line)
python -m rag.ingest --urls my_urls.txt

# Ingest everything (sources.json + CLI URLs)
python -m rag.ingest --url https://extra-doc.com
```

**Option 3 — Local files:**
Place PDF, Markdown, or TXT files in `orchestrator/knowledge-base/docs/` and run `python -m rag.ingest`.

### Architecture Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Single action per response | Observe→Think→Act loop | Dynamic UIs change after each action — must re-observe |
| Planner ≠ Executor | Separation of concerns | Planner thinks in business terms; Executor maps to DOM |
| Recovery agent | Auto-retry with alternatives | Max 3 retries before asking user — improves demo reliability |
| Hybrid RAG (BM25 + Vector) | RRF fusion | Catches both exact UI labels and semantic meaning |
| Session state in `task_state` | Sent back to client | Survives page refreshes, enables multi-step workflows |
| Intent classification first | Route to specialized flows | KNOWLEDGE queries skip DOM entirely — faster response |

### Updated Response Contract

**Action Mode (single next action):**
```json
{
  "session_id": "uuid-string",
  "message": "Opening filter panel. (step 1/3)",
  "mode": "action",
  "next_action": {
    "type": "click",
    "selector": "[data-testid='filter-btn']",
    "description": "Open filter panel"
  },
  "done": false,
  "task_state": {
    "goal": "Show today's contracts",
    "planned_steps": ["Open filter panel", "Enter today's date", "Apply filter"],
    "completed_steps": [],
    "pending_steps": ["Open filter panel", "Enter today's date", "Apply filter"],
    "retry_count": 0
  }
}
```

**Guide Mode:**
```json
{
  "session_id": "uuid-string",
  "message": "Here's how to create a contract:",
  "mode": "guide",
  "guide_steps": [
    {"step": 1, "instruction": "Click '+ New Agreement' in the top-right", "highlight_selector": "[data-testid='new-agreement-btn']"},
    {"step": 2, "instruction": "Select the agreement type", "highlight_selector": "#agreement-type-select"}
  ],
  "done": true
}
```

**Knowledge Mode:**
```json
{
  "session_id": "uuid-string",
  "message": "Obligation Tracking in Conga CLM allows you to monitor contractual commitments...",
  "mode": "knowledge",
  "done": true
}
```

### File Responsibilities

| File | Purpose |
|------|---------|
| `server.py` | FastAPI app (port 8001), CORS middleware, `/api/process` + `/health` endpoints |
| `agent.py` | Main orchestration — intent classification → routing → plan → execute → recover |
| `config.py` | Pydantic settings (OpenAI key, model, host, port from `.env`) |
| `agents/intent_classifier.py` | LLM-based intent detection with confidence score |
| `agents/planner.py` | Generates business-level step plan using RAG context |
| `agents/executor.py` | Maps one step to one UI action using DOM snapshot |
| `agents/recovery.py` | Failure recovery: alt selectors, scroll, wait, navigate, ask user |
| `agents/guide_agent.py` | Generates highlighted step-by-step guide |
| `memory/session_store.py` | In-memory session store with TTL expiry (30 min) |
| `rag/ingest.py` | Multi-source document ingestion (local + URL + sitemap) |
| `rag/retriever.py` | ChromaDB vector retrieval |
| `rag/hybrid_search.py` | BM25 + Vector search with Reciprocal Rank Fusion |
| `rag/sources.json` | Configurable knowledge source definitions |
| `schemas/request.py` | Pydantic models for incoming requests |
| `schemas/response.py` | Pydantic models for outgoing responses |
| `prompts/*.md` | System prompts for each agent |

### How to Run

```bash
cd orchestrator
pip install -r requirements.txt
copy .env.example .env          # Add your OPENAI_API_KEY
python -m rag.ingest             # Ingest KT docs (once, optional)
python -m uvicorn server:app --port 8001 --reload
```

### Prerequisites
- Python 3.11+
- OpenAI API key (GPT-4o recommended)

### Testing the Orchestrator

```bash
curl -X POST http://localhost:8001/api/process ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\": \"test-1\", \"user_input\": \"Show today contracts\", \"mode\": \"action\", \"context\": {\"url\": \"https://app.congaclm.com/agreements\", \"page_title\": \"Agreements\", \"interactive_elements\": [{\"id\": \"el-1\", \"tag\": \"button\", \"text\": \"Filter\", \"selector\": \"[data-testid=filter-btn]\", \"visible\": true}], \"visible_text_summary\": \"Showing 25 agreements\"}, \"previous_actions\": [], \"error_from_last_action\": null}"
```

---

## Integration Checklist

| # | Task | Who | Status |
|---|------|-----|--------|
| 1 | Start speech module on port 8000 | Rohit | ✅ Done |
| 2 | Start orchestrator on port 8001 | Gautam | ✅ Done — `python -m uvicorn server:app --port 8001` |
| 3 | Extension auto-connects | Shivam | ✅ No code changes — `api-client.js` tries `localhost:8001` first |
| 4 | Verify response schema | All | ✅ Pydantic models enforce exact JSON format |
| 5 | Ingest Conga CLM KT docs | Gautam | 🟡 Add URLs/docs to `rag/sources.json` and run `python -m rag.ingest` |
| 6 | Test on real Conga CLM | All | Extension sends real DOM → orchestrator returns real actions |

**Key point:** The extension automatically falls back to mock when the orchestrator is unavailable. Once Gautam's server is running on port 8001, it will be used immediately — zero code changes needed.

---

## Hackathon Submission

### Transfer to Hackathon Repo

```bash
git remote add hackathon https://github.com/congaengr/ai_hackathon_sparkplugs.git
git push hackathon main
```

### Demo Scenarios (Pick 3 and nail them)

1. **Guide**: "How do I create a contract?" → Highlights UI elements with step-by-step instructions
2. **Action**: "Show today's contracts" → Clicks filter, enters date, applies
3. **Voice**: Full voice flow → Speak command → AI responds with TTS → Executes actions

### Demo Tips
- Pre-load the Conga CLM page before demo
- Have fallback recorded video if live demo fails
- Show Guide Mode first (always works), then Action Mode (impressive)
- Show voice input last (wow factor)

---

## Quick Start Commands

```bash
# Backend — Rohit's Speech Module
cd backend/Speech-Module
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --port 8000

# Orchestrator — Gautam's Agentic AI Engine
cd orchestrator
pip install -r requirements.txt
copy .env.example .env         # Add OPENAI_API_KEY
python -m rag.ingest            # Ingest KT docs + URLs (once)
python -m uvicorn server:app --port 8001 --reload

# Extension — Shivam
# Chrome → chrome://extensions → Developer mode → Load unpacked → select extension/
# Press Alt+Shift+S on any page to activate
```

---

*Last updated: June 3, 2026 | Team: Shivam (✅), Rohit (✅), Gautam (✅)*
