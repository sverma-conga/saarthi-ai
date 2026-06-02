# SAARTHI AI — Hackathon Execution Plan

> **Voice-driven AI assistant for Conga CLM** — Browser extension that understands user intent, navigates UI, and executes tasks via natural language/voice commands.

---

## Team

| Developer | IDE | Module Ownership | Status |
|-----------|-----|-----------------|--------|
| **Shivam** | VS Code | Chrome Extension (UI + DOM + Action Executor) | ✅ Complete |
| **Rohit** | PyCharm | Python Backend (FastAPI server + Voice/TTS) | ✅ Complete |
| **Gautam** | PyCharm/VS Code | LLM Orchestrator + RAG Knowledge Engine | 🟡 Pending |

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
├── orchestrator/                    ← 🟡 GAUTAM — PENDING
│   ├── __init__.py
│   ├── agent.py                    ← Main orchestration logic (LLM calls)
│   ├── prompts/
│   │   ├── system_prompt.md
│   │   ├── action_mode.md
│   │   └── guide_mode.md
│   ├── rag/
│   │   ├── ingest.py              ← Load KT docs → vector store
│   │   ├── retriever.py           ← Query vector store for context
│   │   └── vector_store/          ← ChromaDB persistence (gitignored)
│   └── knowledge-base/
│       ├── README.md
│       └── docs/                  ← PDF, markdown, transcripts
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

## 🟡 GAUTAM — LLM Orchestrator + RAG (PENDING)

### What You're Building

The AI brain that:
1. Receives user intent + DOM context from the extension
2. Retrieves relevant KT docs via RAG
3. Calls LLM with structured prompt
4. Returns a JSON action plan or guide steps

### How Your Code Integrates

The extension's `api-client.js` calls:
```
POST http://localhost:8001/api/process
Content-Type: application/json
Body: { session_id, user_input, mode, context, previous_actions, error_from_last_action }
```

**Your server must:**
1. Listen on port **8001** (or update `ORCHESTRATOR_URL` in `extension/utils/api-client.js`)
2. Accept POST `/api/process` with the request schema above
3. Return JSON matching the response schema above

When your server is running, the extension will automatically use it (falls back to mock if unavailable).

### Prerequisites
- Python 3.11+
- OpenAI API key (GPT-4o recommended)

### Step-by-Step Build

#### Step 1: Setup

```bash
cd orchestrator
pip install langchain langchain-openai langchain-community chromadb tiktoken pypdf fastapi uvicorn
```

#### Step 2: Knowledge Ingestion

`rag/ingest.py`:
```python
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

PERSIST_DIR = os.path.join(os.path.dirname(__file__), "vector_store")
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge-base", "docs")

def ingest_documents():
    """Load KT docs and create vector store"""
    pdf_loader = DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    txt_loader = DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.md", loader_cls=TextLoader)

    docs = pdf_loader.load() + txt_loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )

    print(f"Ingested {len(chunks)} chunks from {len(docs)} documents")
    return vectorstore

if __name__ == "__main__":
    ingest_documents()
```

#### Step 3: RAG Retriever

`rag/retriever.py`:
```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

PERSIST_DIR = os.path.join(os.path.dirname(__file__), "vector_store")

def get_retriever():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )
    return vectorstore.as_retriever(search_kwargs={"k": 3})

def retrieve_context(query: str) -> str:
    """Get relevant KT knowledge for the user's query"""
    retriever = get_retriever()
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant documentation found."
    return "\n\n---\n\n".join([doc.page_content for doc in docs])
```

#### Step 4: System Prompt

`prompts/system_prompt.md`:
```markdown
You are SAARTHI AI, an intelligent assistant for Conga CLM (Contract Lifecycle Management).

You help users by either GUIDING them through steps or PERFORMING actions automatically.

## Rules:
1. You MUST respond with valid JSON matching the response schema exactly.
2. You can ONLY use actions from the allowed vocabulary: click, type, select, scroll, wait, navigate.
3. You MUST use selectors from the provided DOM snapshot. Never invent selectors.
4. If you cannot find the right element, ask the user to clarify or navigate to the correct page.
5. For Guide mode: provide clear step-by-step instructions with highlight selectors.
6. For Action mode: provide executable action steps.
7. Set "done": true only when the task is fully complete.
8. Set "done": false if you need to see the updated DOM after actions execute.
9. Keep messages concise and helpful (spoken aloud to user).

## Available Actions:
- click: { "type": "click", "selector": "...", "description": "..." }
- type: { "type": "type", "selector": "...", "value": "...", "description": "..." }
- select: { "type": "select", "selector": "...", "value": "...", "description": "..." }
- scroll: { "type": "scroll", "direction": "down|up", "amount": 300 }
- wait: { "type": "wait", "duration_ms": 500 }
- navigate: { "type": "navigate", "url": "..." }
```

#### Step 5: Main Orchestrator Agent

`agent.py`:
```python
import json
import os
from openai import AsyncOpenAI
from rag.retriever import retrieve_context

client = AsyncOpenAI()

SYSTEM_PROMPT = open(
    os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.md")
).read()

async def process_request(request: dict) -> dict:
    """Main orchestration: RAG + LLM → structured action plan"""

    # 1. Retrieve relevant KT knowledge
    rag_context = retrieve_context(request["user_input"])

    # 2. Build prompt with DOM context
    user_message = build_user_message(request, rag_context)

    # 3. Call LLM
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    # 4. Parse LLM response
    result = json.loads(response.choices[0].message.content)
    result["session_id"] = request["session_id"]
    return result


def build_user_message(request: dict, rag_context: str) -> str:
    elements_str = json.dumps(request["context"]["interactive_elements"], indent=2)

    error_info = ""
    if request.get("error_from_last_action"):
        error_info = f"\n\n## Error from Last Action:\n{request['error_from_last_action']}"

    return f"""## User Request
"{request['user_input']}"

## Mode
{request['mode']}

## Current Page
- URL: {request['context']['url']}
- Title: {request['context']['page_title']}
- Visible Content: {request['context']['visible_text_summary']}

## Interactive Elements on Screen
{elements_str}

## Relevant Knowledge Base Context
{rag_context}
{error_info}

## Previous Actions Taken
{json.dumps(request.get('previous_actions', []), indent=2)}

## Instructions
Respond with a JSON object containing: message, actions (for action mode) OR guide_steps (for guide mode), done (boolean), follow_up (string or null).
Each action must use a selector from the Interactive Elements list above.
"""
```

#### Step 6: FastAPI Server (Your Entry Point)

Create a FastAPI server that wraps the agent:

```python
# orchestrator/server.py
from fastapi import FastAPI
from agent import process_request

app = FastAPI(title="SAARTHI AI Orchestrator", version="1.0.0")

@app.post("/api/process")
async def process(request: dict):
    result = await process_request(request)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
```

Run with:
```bash
cd orchestrator
python -m uvicorn server:app --port 8001
```

#### Step 7: Add KT Documents

Place Conga CLM documentation in `orchestrator/knowledge-base/docs/`:
- Process guides (how to create contracts, manage obligations)
- UI navigation docs
- Video transcripts
- FAQ documents

Then run: `python -m rag.ingest`

### Testing Your Orchestrator Independently

```bash
curl -X POST http://localhost:8001/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-1",
    "user_input": "Show today contracts",
    "mode": "action",
    "context": {
      "url": "https://app.congaclm.com/agreements",
      "page_title": "Agreements",
      "interactive_elements": [
        {"id": "el-1", "tag": "button", "text": "Filter", "selector": "[data-testid=filter-btn]", "visible": true}
      ],
      "visible_text_summary": "Showing 25 agreements"
    },
    "previous_actions": [],
    "error_from_last_action": null
  }'
```

---

## Integration Checklist (When Gautam Is Ready)

| # | Task | Who | What to do |
|---|------|-----|-----------|
| 1 | Start orchestrator on port 8001 | Gautam | `python -m uvicorn server:app --port 8001` |
| 2 | Extension auto-connects | Shivam | No code changes — `api-client.js` already tries `localhost:8001` first |
| 3 | Verify response schema | All | Ensure orchestrator returns exact JSON format above |
| 4 | Tune selectors | Gautam | Use actual selectors from `interactive_elements` in DOM snapshot |
| 5 | Test on real Conga CLM | All | Extension sends real DOM → orchestrator returns real actions |

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

# Orchestrator — Gautam's AI Engine
cd orchestrator
pip install langchain langchain-openai chromadb tiktoken pypdf fastapi uvicorn
python -m rag.ingest          # Ingest KT docs (once)
python -m uvicorn server:app --port 8001

# Extension — Shivam
# Chrome → chrome://extensions → Developer mode → Load unpacked → select extension/
# Press Alt+Shift+S on any page to activate
```

---

*Last updated: June 3, 2026 | Team: Shivam (✅), Rohit (✅), Gautam (🟡)*
