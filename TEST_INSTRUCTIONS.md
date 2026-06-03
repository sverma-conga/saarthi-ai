# SAARTHI AI — Demo & Test Instructions

> Complete guide to demonstrate SAARTHI AI on Conga CLM with all three components live.

---

## Prerequisites

| Requirement | How to Verify |
|------------|---------------|
| Chrome browser | Any recent version |
| Python 3.12+ | `python --version` |
| ffmpeg on PATH | `ffmpeg -version` |
| GitHub PAT in `.env` | `orchestrator/.env` has `OPENAI_API_KEY=ghp_...` |
| Conga CLM access | Login to https://app.congaclm.com (or demo environment) |

---

## Setup (One-Time)

### 1. Install Dependencies

```powershell
cd backend/Speech-Module
pip install -r requirements.txt

cd ../../orchestrator
pip install -r requirements.txt
pip install playwright
python -m playwright install chromium
```

### 2. Configure Environment

```powershell
cd orchestrator
# Create .env with:
#   OPENAI_API_KEY=ghp_your_github_pat
#   OPENAI_BASE_URL=https://models.inference.ai.azure.com
#   OPENAI_MODEL=gpt-4o
```

### 3. Ingest Knowledge Base (if not done)

```powershell
cd orchestrator
python -m rag.ingest_playwright
# Crawls 50 Conga CLM documentation pages → 134 chunks in ChromaDB
```

### 4. Load Extension

1. Open `chrome://extensions` → enable **Developer Mode**
2. Click **"Load unpacked"** → select the `extension/` folder
3. Verify "SAARTHI AI" appears with no errors

---

## Start All Services

Open two separate terminals:

```powershell
# Terminal 1: Speech Server
cd backend/Speech-Module
python -m uvicorn main:app --port 8000
```

```powershell
# Terminal 2: Orchestrator
cd orchestrator
python -m uvicorn server:app --port 8001
```

### Quick Health Check

```powershell
# Both should return 200:
curl http://localhost:8000/text-to-speech?text=hello -o test.mp3
curl http://localhost:8001/health
```

---

## Demo Flow (Recommended Order)

> **Tip**: Start with Knowledge mode (always works), then Guide mode (visual), then Action mode (impressive), then Voice (wow factor).

---

### Demo 1: Knowledge Mode — "What is Contract AI?"

**Setup**: Navigate to any Conga CLM page. Open panel with `Alt+Shift+S`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Press `Alt+Shift+S` | Panel appears bottom-right |
| 2 | Ensure **⚡ Action** mode is selected | Mode toggle visible |
| 3 | Type: `What is Contract AI in Conga CLM?` | Processing... |
| 4 | Wait 3-5 sec | AI responds with information from RAG |
| 5 | Listen | TTS speaks the answer |

**What this proves**: Natural language → Intent classified as KNOWLEDGE → RAG retrieves from 50 ingested Conga doc pages → GPT-4o synthesizes answer → TTS plays response.

**Expected response** (from RAG): Mentions AI-powered capabilities, Aime Assistant, Search Agent, contract analysis.

---

### Demo 2: Knowledge Mode — "How do I create a contract?"

| Step | Action | Expected |
|------|--------|----------|
| 1 | Type: `How do I create a new contract?` | Processing... |
| 2 | Wait | AI provides step-by-step instructions from documentation |
| 3 | Listen | TTS speaks the answer |

**Expected**: Mentions "Create New Contract", Fill out form, Import documents, Store Executed Contract, Contract Type selection — all from real Conga documentation.

---

### Demo 3: Guide Mode — Step-by-Step Highlights

**Setup**: Navigate to the Conga CLM Contracts list page.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click **📖 Guide** mode button | Guide tab highlighted |
| 2 | Type: `How do I filter contracts?` | Processing... |
| 3 | Watch the page | Pulsing blue highlights appear on relevant UI elements |
| 4 | Read tooltip | Step-by-step instructions with "Next" / "Prev" / "Done" |
| 5 | Click **Next** | Highlight moves to next element |
| 6 | Click **Done** | Highlights disappear |

**What this proves**: Guide mode analyzes real DOM → GPT-4o identifies relevant elements → highlights them with instructions. No actions executed — purely visual guidance.

---

### Demo 4: Action Mode — Click "Create New Contract"

**Setup**: Navigate to Conga CLM Contracts page. Switch to **⚡ Action** mode.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Type: `Click Create New Contract` | Processing... |
| 2 | Watch status | "⚡ Executing actions (iteration 1)..." |
| 3 | Watch page | Extension finds the button → highlights blue → clicks it |
| 4 | Observe result | Contract creation dialog/page opens |
| 5 | Check status | "✓ Done — 1 total action(s) in 1 iteration(s)" |

**What this proves**: Intent → Executor maps natural language to real DOM element → executes click.

---

### Demo 5: Action Mode — Multi-Step Task

**Setup**: On Conga CLM Contracts list page.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Type: `Show me today's contracts` | Processing... |
| 2 | Watch status | "⚡ Executing actions (iteration 1)..." |
| 3 | Watch page | Extension clicks filter/search |
| 4 | Status updates | "🔄 Iteration 2/10..." — re-scans DOM |
| 5 | Watch | Extension enters date or applies filter |
| 6 | Final status | "✓ Done — N total action(s) in M iteration(s)" |

**What this proves**: Full agentic loop — Plan (3-4 steps) → Execute step 1 → Re-observe DOM → Execute step 2 → ... → Done. The `task_state` persists across iterations.

---

### Demo 6: Action Mode — Search

**Setup**: Any Conga CLM page with a search bar.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Type: `Search for NDA agreements` | Processing... |
| 2 | Watch | Extension clicks search box → types "NDA" → submits |
| 3 | Observe | Search results appear |

---

### Demo 7: Voice Input — Full Pipeline

**Setup**: Any Conga CLM page. Mic available. Panel open in Action mode.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click **🎤** mic button | "🎤 Recording... click mic again to stop" |
| 2 | Speak clearly: **"How do I approve a contract?"** | Recording |
| 3 | Click **🎤** again to stop | "Processing audio..." |
| 4 | Wait 2-3 sec | Transcript appears: "how do I approve a contract" |
| 5 | Watch response | AI answers with steps from Conga documentation |
| 6 | Listen | TTS speaks the response |

**What this proves**: Voice → Rohit's STT → transcript → Orchestrator (RAG + GPT-4o) → answer → Rohit's TTS → audio. Full end-to-end voice pipeline.

---

### Demo 8: Voice + Action Execution

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click **🎤**, speak: **"Click on Accounts"** | Recording → stop |
| 2 | Watch | Transcript: "click on accounts" → Extension finds Accounts nav → clicks |
| 3 | Observe | Navigates to Accounts section |

**What this proves**: Voice command → real UI action. No typing needed.

---

### Demo 9: Error Recovery

**Setup**: On a page where the requested element doesn't exist.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Type: `Click the export PDF button` | Processing... |
| 2 | Watch | Orchestrator's recovery agent activates |
| 3 | Observe | May scroll to find it, try alternatives, or report "not found" |
| 4 | Panel still works | Ready for next command |

**What this proves**: Graceful failure handling with auto-recovery (up to 3 retries).

---

### Demo 10: Mode Toggle Safety

| Step | Action | Expected |
|------|--------|----------|
| 1 | Switch to **📖 Guide** mode | Guide tab active |
| 2 | Type: `Click Create New Contract` | Processing... |
| 3 | Observe | Highlights the button but does NOT click it |
| 4 | Switch to **⚡ Action** mode | Action tab active |
| 5 | Type same command | Now it actually clicks the button |

**What this proves**: Guide mode is safe/read-only. Action mode executes.

---

## Fallback Behavior

If either server is down:

| Server Down | Behavior |
|-------------|----------|
| Orchestrator (8001) | Extension uses smart mock — still executes actions using DOM analysis |
| Speech (8000) | Mic button fails gracefully; text input still works |
| Both down | Text input + mock actions still function |

The extension **never crashes**. Mock responses are DOM-aware (uses real selectors from the page).

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Panel doesn't appear | `chrome://extensions` → check for errors → reload extension |
| "Mic error" | Grant permission at `chrome://settings/content/microphone` |
| Orchestrator 500 error | Check `.env` exists in `orchestrator/` with valid `OPENAI_API_KEY` |
| TTS silent | Check volume; check browser autoplay policy (interact with page first) |
| Slow response | GitHub Models rate limit — wait 10 sec and retry |
| "Element not found" | Element may be off-screen or behind a modal; try scrolling first |
| Hotkey doesn't work | `chrome://extensions/shortcuts` → verify Alt+Shift+S is assigned |
| RAG returns generic answers | Run `python -m rag.ingest_playwright` to rebuild vector store |

---

## Architecture Summary for Judges

```
┌─── Chrome Extension ──────────────────────────────────────┐
│  Alt+Shift+S → Shadow DOM Panel                           │
│  Voice (MediaRecorder) ←→ Speech Server (port 8000)       │
│  DOM Analyzer → 50 interactive elements with selectors    │
│  Action Executor → click/type/scroll/navigate/submit      │
│  Agentic Loop → max 10 iterations until done              │
└───────────────────────────┬───────────────────────────────┘
                            │ HTTP (via service worker CORS proxy)
┌───────────────────────────▼───────────────────────────────┐
│  Orchestrator (port 8001) — GPT-4o via GitHub Models      │
│                                                           │
│  Intent Classifier → Planner → Executor → Recovery        │
│       ↕                  ↕                                │
│  RAG Engine          Session Store                        │
│  134 chunks from     (task_state persists                 │
│  Conga CLM docs       across iterations)                  │
└───────────────────────────────────────────────────────────┘

Key: No OpenAI API key needed — uses free GitHub Models (GPT-4o).
     No paid speech APIs — uses free Google STT + gTTS.
```

---

## Demo Tips

1. **Pre-login** to Conga CLM before demo starts
2. **Pre-open** the panel once to warm up (first load takes a moment)
3. **Start with Knowledge** mode — always works, impresses with RAG
4. **Guide mode next** — visual and safe, shows DOM intelligence
5. **Action mode** — the wow moment, AI clicking buttons
6. **Voice last** — full pipeline, biggest impact
7. If live demo fails → explain architecture with the diagram above

---

*Last updated: June 3, 2026*
