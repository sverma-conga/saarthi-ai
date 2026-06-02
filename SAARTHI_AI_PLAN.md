# SAARTHI AI — Hackathon Execution Plan

> **Voice-driven AI assistant for Conga CLM** — Browser extension that understands user intent, navigates UI, and executes tasks via natural language/voice commands.

---

## Team

| Developer | IDE | Module Ownership |
|-----------|-----|-----------------|
| **Shivam** | VS Code | Chrome Extension (UI + DOM + Action Executor) |
| **Rohit** | PyCharm | Python Backend (FastAPI server + Voice/TTS) |
| **Gautam** | PyCharm/VS Code | LLM Orchestrator + RAG Knowledge Engine |

---

## Repository Structure

```
saarthi-ai/                          ← GitHub repo root
│
├── README.md                        ← Project overview + demo instructions
├── .env.example                     ← Shared env template (API keys)
├── docker-compose.yml               ← One-command backend startup
│
├── contracts/                       ← 🔴 SHARED — DO NOT MODIFY WITHOUT TEAM AGREEMENT
│   ├── request-schema.json          ← Extension → Backend request format
│   ├── response-schema.json         ← Backend → Extension response format
│   └── actions-vocabulary.md        ← Allowed action types and their params
│
├── extension/                       ← 🔵 SHIVAM's territory
│   ├── manifest.json
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.css
│   │   └── popup.js
│   ├── content/
│   │   ├── content.js              ← DOM analyzer + action executor
│   │   ├── overlay.js              ← Guide mode highlights
│   │   └── content.css
│   ├── background/
│   │   └── service-worker.js       ← Hotkey listener, message routing
│   ├── utils/
│   │   ├── dom-analyzer.js         ← Extract interactive elements
│   │   ├── action-executor.js      ← Execute click/type/select/scroll
│   │   └── api-client.js           ← HTTP calls to backend
│   └── assets/
│       └── icons/
│
├── backend/                         ← 🟢 ROHIT's territory (server + voice)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     ← FastAPI app entry point
│   ├── api/
│   │   ├── routes.py               ← /api/process, /api/health
│   │   └── models.py               ← Pydantic request/response models
│   ├── voice/                      ← 🟢 ROHIT
│   │   ├── whisper_client.py       ← Optional Whisper fallback
│   │   └── tts_client.py           ← Text-to-speech if server-side needed
│   └── config.py                   ← Environment variable loading
│
├── orchestrator/                    ← 🟡 GAUTAM's territory
│   ├── __init__.py
│   ├── agent.py                    ← Main orchestration logic (LLM calls)
│   ├── prompts/
│   │   ├── system_prompt.md        ← System prompt for action/guide mode
│   │   ├── action_mode.md
│   │   └── guide_mode.md
│   ├── rag/
│   │   ├── ingest.py              ← Load KT docs → vector store
│   │   ├── retriever.py           ← Query vector store for context
│   │   └── vector_store/          ← ChromaDB persistence (gitignored)
│   └── knowledge-base/
│       ├── README.md              ← How to add new KT docs
│       └── docs/                  ← PDF, markdown, transcripts
│
└── tests/                          ← Integration tests (Phase 2)
    ├── test_api.py
    ├── test_orchestrator.py
    └── mock_dom_snapshots/
```

---

## Integration Contract (THE MOST CRITICAL PART)

All three modules communicate through ONE API endpoint. Agree on this schema **before writing any code**.

### Request: Extension → Backend

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
      },
      {
        "id": "el-2",
        "tag": "input",
        "text": "",
        "selector": "#search-input",
        "placeholder": "Search agreements...",
        "visible": true
      }
    ],
    "visible_text_summary": "Showing 25 agreements. Columns: Name, Status, Created Date, Owner..."
  },
  "previous_actions": [],
  "error_from_last_action": null
}
```

### Response: Backend → Extension

```json
{
  "session_id": "uuid-string",
  "message": "I'll filter agreements to show today's contracts.",
  "mode": "action",
  "actions": [
    {"step": 1, "type": "click", "selector": "[data-testid='filter-btn']", "description": "Open filter panel"},
    {"step": 2, "type": "wait", "duration_ms": 500},
    {"step": 3, "type": "click", "selector": "[data-testid='date-filter']", "description": "Select date filter"},
    {"step": 4, "type": "type", "selector": "#date-input", "value": "2025-07-25", "description": "Enter today's date"},
    {"step": 5, "type": "click", "selector": "[data-testid='apply-filter']", "description": "Apply filter"}
  ],
  "guide_steps": null,
  "done": false,
  "follow_up": "I'll verify the results after the filter is applied. Please wait."
}
```

For **Guide Mode** response:
```json
{
  "session_id": "uuid-string",
  "message": "Here's how to create a contract:",
  "mode": "guide",
  "actions": null,
  "guide_steps": [
    {"step": 1, "instruction": "Click the '+ New Agreement' button in the top-right", "highlight_selector": "[data-testid='new-agreement-btn']"},
    {"step": 2, "instruction": "Select the agreement type from the dropdown", "highlight_selector": "#agreement-type-select"},
    {"step": 3, "instruction": "Fill in the required fields marked with *", "highlight_selector": ".required-field"}
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
| `highlight` | `selector`, `message` | Highlight element (guide mode) |

---

## Developer-Specific Build Guides

---

## 🔵 SHIVAM — Chrome Extension

### What You're Building
A Chrome Manifest V3 extension that:
1. Activates on `Ctrl+Shift+A`
2. Shows a floating panel with mic button + text input + mode toggle
3. Captures voice via Web Speech API → converts to text
4. Analyzes current page DOM → extracts interactive elements
5. Sends request to backend API
6. Receives action plan → executes actions OR highlights elements

### Prerequisites
- Node.js (for optional bundling, not required)
- Chrome browser
- VS Code with "Chrome Extension" snippets extension

### Step-by-Step Build

#### Step 1: Manifest & Shell (1 hour)

Create `extension/manifest.json`:
```json
{
  "manifest_version": 3,
  "name": "SAARTHI AI",
  "version": "1.0.0",
  "description": "Voice-driven AI assistant for Conga CLM",
  "permissions": ["activeTab", "scripting", "storage"],
  "host_permissions": ["https://*.congaclm.com/*", "http://localhost/*"],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": "assets/icons/icon48.png"
  },
  "background": {
    "service_worker": "background/service-worker.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content/content.js"],
      "css": ["content/content.css"]
    }
  ],
  "commands": {
    "activate-saarthi": {
      "suggested_key": { "default": "Ctrl+Shift+A" },
      "description": "Activate SAARTHI AI"
    }
  }
}
```

#### Step 2: Background Service Worker (30 min)

`background/service-worker.js` — Listen for hotkey, inject content script:
```javascript
chrome.commands.onCommand.addListener((command) => {
  if (command === 'activate-saarthi') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'toggle-panel' });
    });
  }
});
```

#### Step 3: Content Script — Floating Panel UI (2 hours)

`content/content.js` — Inject a floating panel into the page:
- Create a shadow DOM container (avoids CSS conflicts with host page)
- Panel has: mic button, text input, send button, mode toggle (Guide/Action), response area
- Listen for `toggle-panel` message from background script

Key structure:
```javascript
// content/content.js
let panelVisible = false;

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'toggle-panel') {
    panelVisible ? hidePanel() : showPanel();
    panelVisible = !panelVisible;
  }
});

function showPanel() {
  const container = document.createElement('div');
  container.id = 'saarthi-root';
  const shadow = container.attachShadow({ mode: 'open' });
  // Build UI inside shadow DOM
  // ... mic button, input, mode toggle, response area
  document.body.appendChild(container);
}
```

#### Step 4: Voice Input via Web Speech API (1 hour)

Inside your panel's mic button handler:
```javascript
function startListening() {
  const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('saarthi-input').value = transcript;
    processUserInput(transcript);
  };
  recognition.start();
}
```

#### Step 5: DOM Analyzer (2 hours)

`utils/dom-analyzer.js` — Extract interactive elements:
```javascript
function analyzeDom() {
  const interactiveSelectors = 'button, a, input, select, textarea, [role="button"], [onclick], [data-testid]';
  const elements = document.querySelectorAll(interactiveSelectors);

  return Array.from(elements)
    .filter(el => el.offsetParent !== null) // visible only
    .slice(0, 50) // limit to 50 elements to avoid token bloat
    .map((el, i) => ({
      id: `el-${i}`,
      tag: el.tagName.toLowerCase(),
      text: (el.textContent || '').trim().substring(0, 50),
      selector: getUniqueSelector(el),
      aria_label: el.getAttribute('aria-label'),
      placeholder: el.getAttribute('placeholder'),
      visible: true
    }));
}

function getUniqueSelector(el) {
  // Priority: data-testid > id > aria-label > CSS path
  if (el.dataset.testid) return `[data-testid="${el.dataset.testid}"]`;
  if (el.id) return `#${el.id}`;
  // Fallback: generate CSS path
  return generateCssPath(el);
}
```

#### Step 6: API Client (1 hour)

`utils/api-client.js`:
```javascript
const BACKEND_URL = 'http://localhost:8000';

async function sendToBackend(userInput, mode) {
  const domSnapshot = analyzeDom();
  const request = {
    session_id: getSessionId(),
    user_input: userInput,
    mode: mode,
    context: {
      url: window.location.href,
      page_title: document.title,
      interactive_elements: domSnapshot,
      visible_text_summary: getVisibleTextSummary()
    },
    previous_actions: getPreviousActions(),
    error_from_last_action: null
  };

  const response = await fetch(`${BACKEND_URL}/api/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  return response.json();
}
```

#### Step 7: Action Executor (2 hours)

`utils/action-executor.js`:
```javascript
async function executeActions(actions) {
  for (const action of actions) {
    try {
      switch (action.type) {
        case 'click':
          document.querySelector(action.selector)?.click();
          break;
        case 'type':
          const input = document.querySelector(action.selector);
          input.value = action.value;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        case 'select':
          const select = document.querySelector(action.selector);
          select.value = action.value;
          select.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        case 'wait':
          await new Promise(r => setTimeout(r, action.duration_ms));
          break;
        case 'scroll':
          window.scrollBy(0, action.amount || 300);
          break;
        case 'navigate':
          window.location.href = action.url;
          break;
      }
      await new Promise(r => setTimeout(r, 300)); // pause between actions
    } catch (err) {
      return { success: false, failed_step: action.step, error: err.message };
    }
  }
  return { success: true };
}
```

#### Step 8: Guide Mode Overlay (1 hour)

`content/overlay.js`:
```javascript
function highlightElement(selector, message) {
  const el = document.querySelector(selector);
  if (!el) return;

  const rect = el.getBoundingClientRect();
  const overlay = document.createElement('div');
  overlay.className = 'saarthi-highlight';
  overlay.style.cssText = `
    position: fixed; top: ${rect.top - 4}px; left: ${rect.left - 4}px;
    width: ${rect.width + 8}px; height: ${rect.height + 8}px;
    border: 3px solid #4CAF50; border-radius: 4px;
    animation: saarthi-pulse 1.5s infinite; z-index: 999999;
    pointer-events: none;
  `;

  if (message) {
    const tooltip = document.createElement('div');
    tooltip.className = 'saarthi-tooltip';
    tooltip.textContent = message;
    overlay.appendChild(tooltip);
  }

  document.body.appendChild(overlay);
}
```

#### Step 9: Text-to-Speech Response (30 min)

```javascript
function speakResponse(text) {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.1;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}
```

#### Step 10: Main Loop Integration (1 hour)

Wire everything together:
```javascript
async function processUserInput(text) {
  const mode = getCurrentMode(); // 'action' or 'guide'
  showLoading();

  const response = await sendToBackend(text, mode);

  // Speak the message
  speakResponse(response.message);
  showMessage(response.message);

  if (response.mode === 'action' && response.actions) {
    const result = await executeActions(response.actions);
    if (!response.done) {
      // Loop: send updated DOM back for next steps
      await new Promise(r => setTimeout(r, 1000));
      await continueSession(response.session_id, result);
    }
  } else if (response.mode === 'guide' && response.guide_steps) {
    showGuideSteps(response.guide_steps);
  }
}
```

### Testing Without Backend
Create a mock that returns hardcoded responses so you can develop the UI independently:
```javascript
// utils/api-client.js — add mock mode
const MOCK_MODE = true; // flip to false when backend is ready

async function sendToBackend(userInput, mode) {
  if (MOCK_MODE) return getMockResponse(userInput, mode);
  // ... real API call
}
```

---

## 🟢 ROHIT — Python Backend (FastAPI + Voice)

### What You're Building
A FastAPI server that:
1. Receives requests from the Chrome extension
2. Passes them to Gautam's orchestrator
3. Returns structured action plans
4. Optionally provides Whisper STT / TTS endpoints as fallback

### Prerequisites
- Python 3.11+
- PyCharm Professional or Community
- pip / poetry for dependency management

### Step-by-Step Build

#### Step 1: Project Setup (30 min)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install fastapi uvicorn pydantic python-dotenv openai-whisper
```

`requirements.txt`:
```
fastapi==0.115.0
uvicorn==0.30.0
pydantic==2.9.0
python-dotenv==1.0.1
openai==1.40.0
httpx==0.27.0
python-multipart==0.0.9
```

#### Step 2: Pydantic Models (1 hour)

`api/models.py` — Mirrors the JSON contract exactly:
```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class Mode(str, Enum):
    action = "action"
    guide = "guide"

class InteractiveElement(BaseModel):
    id: str
    tag: str
    text: str
    selector: str
    aria_label: Optional[str] = None
    placeholder: Optional[str] = None
    visible: bool = True

class PageContext(BaseModel):
    url: str
    page_title: str
    interactive_elements: list[InteractiveElement]
    visible_text_summary: str

class ProcessRequest(BaseModel):
    session_id: str
    user_input: str
    mode: Mode
    context: PageContext
    previous_actions: list[dict] = []
    error_from_last_action: Optional[str] = None

class ActionStep(BaseModel):
    step: int
    type: str  # click, type, select, scroll, wait, navigate, highlight
    selector: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    duration_ms: Optional[int] = None
    direction: Optional[str] = None
    amount: Optional[int] = None
    url: Optional[str] = None
    message: Optional[str] = None

class GuideStep(BaseModel):
    step: int
    instruction: str
    highlight_selector: Optional[str] = None

class ProcessResponse(BaseModel):
    session_id: str
    message: str
    mode: Mode
    actions: Optional[list[ActionStep]] = None
    guide_steps: Optional[list[GuideStep]] = None
    done: bool
    follow_up: Optional[str] = None
```

#### Step 3: FastAPI Routes (1 hour)

`api/routes.py`:
```python
from fastapi import APIRouter, HTTPException
from .models import ProcessRequest, ProcessResponse
import sys
sys.path.append('..')
from orchestrator.agent import process_request

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "service": "saarthi-ai"}

@router.post("/process", response_model=ProcessResponse)
async def process(request: ProcessRequest):
    try:
        result = await process_request(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Step 4: Main App Entry (30 min)

`main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SAARTHI AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

#### Step 5: Mock Orchestrator (for independent testing) (30 min)

Until Gautam's module is ready, create a mock:
```python
# orchestrator/__init__.py
# orchestrator/agent.py

from api.models import ProcessRequest, ProcessResponse, ActionStep, GuideStep, Mode

async def process_request(request: ProcessRequest) -> ProcessResponse:
    """Mock orchestrator — replace with real LLM logic from Gautam"""
    if request.mode == Mode.action:
        return ProcessResponse(
            session_id=request.session_id,
            message=f"I'll help you with: {request.user_input}",
            mode=Mode.action,
            actions=[
                ActionStep(step=1, type="click", selector="button:first-of-type", description="Mock click action")
            ],
            done=True,
            follow_up=None
        )
    else:
        return ProcessResponse(
            session_id=request.session_id,
            message=f"Here's how to: {request.user_input}",
            mode=Mode.guide,
            guide_steps=[
                GuideStep(step=1, instruction="This is a mock guide step", highlight_selector="button:first-of-type")
            ],
            done=True,
            follow_up=None
        )
```

#### Step 6: Whisper Fallback Endpoint (optional, 1.5 hours)

`voice/whisper_client.py`:
```python
import openai
from fastapi import UploadFile

async def transcribe_audio(audio_file: UploadFile) -> str:
    """Use OpenAI Whisper API for accurate transcription"""
    client = openai.AsyncOpenAI()
    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file.file
    )
    return transcript.text
```

Add route in `api/routes.py`:
```python
@router.post("/transcribe")
async def transcribe(audio: UploadFile):
    text = await transcribe_audio(audio)
    return {"text": text}
```

#### Step 7: Dockerfile (30 min)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 8: Integration with Gautam's Orchestrator (Phase 2)

Replace the mock in `api/routes.py`:
```python
from orchestrator.agent import process_request  # Gautam's real implementation
```

### Testing
```bash
# Run server
uvicorn main:app --reload

# Test health
curl http://localhost:8000/api/health

# Test process
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-1","user_input":"show contracts","mode":"action","context":{"url":"http://test.com","page_title":"Test","interactive_elements":[],"visible_text_summary":"test page"}}'
```

---

## 🟡 GAUTAM — LLM Orchestrator + RAG

### What You're Building
The AI brain that:
1. Receives user intent + DOM context
2. Retrieves relevant KT docs via RAG
3. Calls LLM with structured prompt
4. Returns a JSON action plan or guide steps

### Prerequisites
- Python 3.11+
- OpenAI API key (GPT-4o recommended)
- PyCharm or VS Code

### Step-by-Step Build

#### Step 1: Setup (30 min)

```bash
cd orchestrator
pip install langchain langchain-openai langchain-community chromadb tiktoken pypdf
```

Add to `requirements.txt` (shared with backend):
```
langchain==0.3.0
langchain-openai==0.2.0
langchain-community==0.3.0
chromadb==0.5.0
tiktoken==0.7.0
pypdf==4.3.0
```

#### Step 2: Knowledge Ingestion (2 hours)

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
    # Load PDFs
    pdf_loader = DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    # Load markdown/text
    txt_loader = DirectoryLoader(KNOWLEDGE_DIR, glob="**/*.md", loader_cls=TextLoader)

    docs = pdf_loader.load() + txt_loader.load()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_documents(docs)

    # Create vector store
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

#### Step 3: RAG Retriever (1 hour)

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

#### Step 4: System Prompts (1.5 hours)

`prompts/system_prompt.md`:
```markdown
You are SAARTHI AI, an intelligent assistant for Conga CLM (Contract Lifecycle Management).

You help users by either GUIDING them through steps or PERFORMING actions automatically.

## Rules:
1. You MUST respond with valid JSON matching the response schema exactly.
2. You can ONLY use actions from the allowed vocabulary: click, type, select, scroll, wait, navigate, highlight.
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

#### Step 5: Main Orchestrator Agent (3 hours)

`agent.py`:
```python
import json
import os
from openai import AsyncOpenAI
from rag.retriever import retrieve_context

# Import from sibling package (backend models)
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from api.models import ProcessRequest, ProcessResponse, ActionStep, GuideStep, Mode

client = AsyncOpenAI()

SYSTEM_PROMPT = open(
    os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.md")
).read()

async def process_request(request: ProcessRequest) -> ProcessResponse:
    """Main orchestration: RAG + LLM → structured action plan"""

    # 1. Retrieve relevant KT knowledge
    rag_context = retrieve_context(request.user_input)

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

    # 5. Build typed response
    return ProcessResponse(
        session_id=request.session_id,
        message=result.get("message", ""),
        mode=request.mode,
        actions=[ActionStep(**a) for a in result.get("actions", [])] if result.get("actions") else None,
        guide_steps=[GuideStep(**g) for g in result.get("guide_steps", [])] if result.get("guide_steps") else None,
        done=result.get("done", True),
        follow_up=result.get("follow_up")
    )


def build_user_message(request: ProcessRequest, rag_context: str) -> str:
    elements_str = json.dumps(
        [e.model_dump() for e in request.context.interactive_elements],
        indent=2
    )

    error_info = ""
    if request.error_from_last_action:
        error_info = f"\n\n## Error from Last Action:\n{request.error_from_last_action}"

    return f"""## User Request
"{request.user_input}"

## Mode
{request.mode.value}

## Current Page
- URL: {request.context.url}
- Title: {request.context.page_title}
- Visible Content: {request.context.visible_text_summary}

## Interactive Elements on Screen
{elements_str}

## Relevant Knowledge Base Context
{rag_context}
{error_info}

## Previous Actions Taken
{json.dumps(request.previous_actions, indent=2) if request.previous_actions else "None"}

## Instructions
Respond with a JSON object containing: message, actions (for action mode) OR guide_steps (for guide mode), done (boolean), follow_up (string or null).
Each action must use a selector from the Interactive Elements list above.
"""
```

#### Step 6: Test Independently (1 hour)

Create `tests/test_orchestrator.py`:
```python
import asyncio
from orchestrator.agent import process_request
from api.models import ProcessRequest, PageContext, InteractiveElement, Mode

def test_action_mode():
    request = ProcessRequest(
        session_id="test-1",
        user_input="Show today's contracts",
        mode=Mode.action,
        context=PageContext(
            url="https://app.congaclm.com/agreements",
            page_title="Agreements",
            interactive_elements=[
                InteractiveElement(id="el-1", tag="button", text="Filter", selector="[data-testid='filter-btn']"),
                InteractiveElement(id="el-2", tag="input", text="", selector="#date-input", placeholder="Select date"),
            ],
            visible_text_summary="Showing 25 agreements in a table"
        )
    )
    result = asyncio.run(process_request(request))
    print(f"Message: {result.message}")
    print(f"Actions: {result.actions}")
    assert result.actions is not None

if __name__ == "__main__":
    test_action_mode()
```

#### Step 7: Add KT Documents

Place relevant Conga CLM documentation in `orchestrator/knowledge-base/docs/`:
- Process guides (how to create contracts, manage obligations, etc.)
- UI navigation docs
- Video transcripts (manual or auto-generated)
- FAQ documents

Then run: `python -m orchestrator.rag.ingest`

---

## Integration Checklist (Phase 2 — All Together)

| # | Task | Who | Time |
|---|------|-----|------|
| 1 | Rohit starts backend, Shivam's extension connects | Shivam + Rohit | 30 min |
| 2 | Rohit wires Gautam's `process_request` into routes | Rohit + Gautam | 30 min |
| 3 | End-to-end test: text input → action execution | All | 1 hr |
| 4 | End-to-end test: voice input → guide mode | All | 30 min |
| 5 | Fix DOM selector issues on real Conga CLM | Shivam | 1 hr |
| 6 | Tune prompts for Conga CLM specific workflows | Gautam | 1 hr |
| 7 | Add error recovery loop (action fails → retry) | Shivam + Gautam | 30 min |

---

## Recommendations for Success

### 1. Start with the Contract, Not the Code
Print out the JSON schemas. Every developer should have them visible. If you change the contract, notify everyone immediately.

### 2. Use Mock Data from Day 1
- Shivam: Mock backend responses so you can build the full extension without waiting
- Rohit: Mock orchestrator so you can test API flow without LLM
- Gautam: Mock DOM snapshots so you can tune prompts without the extension

### 3. Pick 3 Demo Scenarios and Nail Them
Don't try to handle everything. Pick exactly 3 workflows:
1. **Guide**: "How do I create a contract?" 
2. **Action**: "Show today's contracts" (filter)
3. **Action**: "Create a new agreement named X" (navigation + form fill)

Hard-code fallbacks for these if the general LLM approach fails.

### 4. DOM Selector Strategy (Critical for Reliability)
Priority order for selectors:
1. `data-testid` attributes (most stable)
2. `id` attributes
3. `aria-label` attributes
4. Text content match (fragile but workable)
5. CSS path (last resort)

### 5. Token Budget Management
The DOM snapshot can get huge. Limit to:
- Max 50 interactive elements
- Max 50 chars per element text
- Summarize visible text to ~200 words
- This keeps the LLM call under 4K tokens input

### 6. Session Continuity
For multi-step actions, maintain session state:
- Extension stores `session_id` and `previous_actions`
- After each action batch executes, re-analyze DOM and send back
- LLM sees what changed and decides next steps or declares "done"

### 7. Error Recovery
If an action fails (element not found), don't crash:
- Report error back to backend: `"error_from_last_action": "Element [data-testid='filter-btn'] not found"`
- LLM can suggest alternative selector or ask user for help
- Always have a "I couldn't complete this, here's what I tried" fallback

### 8. Demo Tips
- Pre-load the Conga CLM page before demo
- Have fallback recorded video if live demo fails
- Show Guide Mode first (always works), then Action Mode (impressive)
- Keep 2-3 canned responses for known queries as hardcoded fallbacks

---

## Timeline

| Day | Milestone |
|-----|-----------|
| Day 1 (Hours 0-4) | Phase 0 setup + each dev completes Steps 1-3 of their module |
| Day 1 (Hours 4-8) | Each dev completes remaining steps with mock data |
| Day 2 (Hours 0-3) | Integration: connect all three modules |
| Day 2 (Hours 3-5) | Test on real Conga CLM, fix selectors, tune prompts |
| Day 2 (Hours 5-7) | Polish UI, record backup demo video, prepare presentation |

---

## Quick Start Commands

```bash
# Clone repo
git clone https://github.com/your-team/saarthi-ai.git

# Backend (Rohit)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # Add OPENAI_API_KEY
uvicorn main:app --reload --port 8000

# Orchestrator knowledge ingestion (Gautam)
cd orchestrator
python -m rag.ingest

# Extension (Shivam)
# Chrome → chrome://extensions → Developer mode → Load unpacked → select extension/

# Full stack (docker-compose)
docker-compose up
```

---

## Environment Variables (`.env.example`)

```env
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
BACKEND_PORT=8000
LOG_LEVEL=info
```

---

## Deployment (For Demo Day)

| Option | Effort | Reliability |
|--------|--------|-------------|
| **Local** (all on one laptop) | Low | Medium (wifi dependent for LLM) |
| **Render/Railway** (backend) | Medium | High |
| **Docker Compose** (portable) | Medium | High |

Recommended: Run backend locally for hackathon demo. Deploy to Render only if presenting remotely.

---

*Last updated: July 2025 | Team: Shivam, Rohit, Gautam*
