# SAARTHI AI — Test & Demo Instructions

> Complete walkthrough to demonstrate every functional capability of the extension.

---

## Prerequisites

| Requirement | Check |
|------------|-------|
| Chrome browser | Any recent version |
| Python 3.12+ | `python --version` |
| ffmpeg on PATH | `ffmpeg -version` |
| Extension loaded | `chrome://extensions` → Developer Mode → Load unpacked → `extension/` folder |

---

## Step 1: Start the Python Speech Server

### Stop any existing server first

```powershell
# In terminal, find and kill any existing process on port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Start the server

```powershell
cd "c:\Users\sverma\ROC\Saarthi AI\saarthi-ai\backend\Speech-Module"

# Ensure .env exists (no API key needed for STT/TTS)
if (!(Test-Path .env)) { Copy-Item .env.example .env }

# Start the FastAPI server
python -m uvicorn main:app --port 8000
```

### Verify it's running

Open in browser: **http://localhost:8000/docs**  
You should see the FastAPI Swagger UI with `/speech-to-text` and `/text-to-speech` endpoints.

---

## Step 2: Load / Reload the Extension

1. Open `chrome://extensions`
2. Enable **Developer Mode** (top-right toggle)
3. If already loaded: click the **🔄 refresh icon** on the SAARTHI AI card
4. If first time: click **"Load unpacked"** → navigate to `extension/` folder → Select Folder
5. Confirm: you should see "SAARTHI AI" with no errors

---

## Step 3: Open the Test Page

Navigate to **https://www.google.com** (clean Google homepage).

---

## Demo Scenarios

### Demo 1: Panel Open & Close (Hotkey)

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Press `Alt+Shift+S` | SAARTHI AI panel appears (bottom-right) |
| 2 | Observe panel | Shows: title, mode toggle (Action/Guide), response area, mic button, text input |
| 3 | Press `Alt+Shift+S` again | Panel disappears |
| 4 | Press `Alt+Shift+S` once more | Panel reappears (toggle behavior) |

---

### Demo 2: Action Mode — Search with Auto-Submit

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open panel (`Alt+Shift+S`) on google.com | Panel visible, Action mode active (⚡ highlighted) |
| 2 | Type in text input: `search for saarthi ai` | Text appears in input box |
| 3 | Press Enter | Processing starts... |
| 4 | Watch the page | Extension clicks search box → types "saarthi ai" → submits form |
| 5 | Observe status | Shows: `✓ Done — 3 total action(s) in 1 iteration(s)` |
| 6 | Observe page | Google search results for "saarthi ai" are displayed |
| 7 | Listen | TTS speaks: "I'll search for saarthi ai" |

**What this proves:** Text input → DOM analysis → action execution (click + type + submit) → TTS response.

---

### Demo 3: Action Mode — Click a Specific Element

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | On Google search results page, open panel | Panel visible |
| 2 | Type: `click Images` | Processing... |
| 3 | Watch | Extension finds "Images" link → highlights it blue → clicks it |
| 4 | Observe | Page navigates to Google Images tab |
| 5 | Status | `✓ Done — 1 total action(s) in 1 iteration(s)` |

**What this proves:** Natural language → finds matching element by text → clicks it.

---

### Demo 4: Action Mode — Scroll

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to any long page (e.g., Wikipedia article) | Page loaded |
| 2 | Open panel, type: `scroll down` | Processing... |
| 3 | Watch | Page smoothly scrolls down ~400px |
| 4 | Type: `scroll up` | Page scrolls back up |

**What this proves:** Scroll action works without needing a selector.

---

### Demo 5: Guide Mode — Step-by-Step Highlights

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate back to **google.com** | Clean homepage |
| 2 | Open panel (`Alt+Shift+S`) | Panel visible |
| 3 | Click **📖 Guide** button | Guide mode activated (button highlighted) |
| 4 | Type: `how do I use this page?` | Processing... |
| 5 | Observe page | Pulsing blue border appears on the search box |
| 6 | Observe tooltip | Tooltip shows: "Use the search box to find what you need" with Prev/Next/Done buttons |
| 7 | Click **Next** in tooltip | Highlight moves to next element (a link) with new instruction |
| 8 | Click **Next** again | Highlights next element (a button) |
| 9 | Click **Done** | All highlights disappear |

**What this proves:** Guide mode highlights real elements, shows instructions, step navigation works.

---

### Demo 6: Guide Mode Respects Mode Toggle (No Actions Executed)

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Stay in **📖 Guide** mode on google.com | Guide tab selected |
| 2 | Type: `search for hello world` | Processing... |
| 3 | Observe | Highlights appear on search box — does NOT type anything |
| 4 | Confirm | No text was auto-typed, no navigation happened |
| 5 | Switch to **⚡ Action** mode | Action tab now selected |
| 6 | Type: `search for hello world` | Now it actually types and submits |

**What this proves:** Mode toggle correctly gates behavior — Guide only shows, Action only executes.

---

### Demo 7: Voice Input (Full Voice Pipeline)

> **Requires:** microphone access + Speech server running on port 8000

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to **google.com**, open panel | Panel visible, Action mode |
| 2 | Click the **🎤 mic button** | Browser asks for mic permission (first time) → Grant it |
| 3 | Status shows | "🎤 Recording... click mic again to stop" |
| 4 | Speak clearly: **"search for artificial intelligence"** | Mic is recording |
| 5 | Click **🎤 again** to stop recording | Status: "Processing audio..." |
| 6 | Wait 2-3 seconds | Transcript appears: "search for artificial intelligence" |
| 7 | Watch page | Extension types "artificial intelligence" in Google → submits |
| 8 | Listen | TTS plays back the AI response |

**What this proves:** Voice → STT (Rohit's server) → intent processing → action execution → TTS response. Full pipeline.

---

### Demo 8: TTS (Text-to-Speech) Response

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open panel on any page, Action mode | Ready |
| 2 | Type: `hello` | Processing... |
| 3 | Listen to speakers/headphones | AI speaks the response message aloud |
| 4 | Check panel response area | Shows the AI's text response |

**What this proves:** Every response triggers TTS audio playback via Rohit's `/text-to-speech` endpoint.

---

### Demo 9: Error Handling (Element Not Found)

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Open panel on google.com, Action mode | Ready |
| 2 | Type: `click the download button` | Processing... |
| 3 | Observe status | May show `⚠️ Failed at step 1: Element not found: ...` OR clicks first button |
| 4 | Panel still works | Extension doesn't crash, ready for next command |

**What this proves:** Graceful error handling when elements can't be found.

---

### Demo 10: Multi-Turn Loop (done=false)

> **Note:** The mock returns `done: true` for most commands. This is best demonstrated with the real orchestrator. To simulate:

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | On Google results page, Action mode | Ready |
| 2 | Type: `filter results` | Processing... |
| 3 | If a filter/sort button exists | Extension clicks it, status may show "🔄 Iteration 2/10..." |
| 4 | Observe | Loop continues until `done: true` or max 10 iterations |

**What this proves:** Extension loops: execute → re-scan DOM → ask orchestrator again → repeat.

---

## Stopping the Server

```powershell
# Press Ctrl+C in the terminal running uvicorn
# OR force kill:
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Panel doesn't appear | Check `chrome://extensions` for errors; reload extension |
| "Mic error" | Grant microphone permission; check `chrome://settings/content/microphone` |
| STT returns empty/error | Ensure server is running (`http://localhost:8000/docs`) |
| No TTS audio | Check volume; ensure server is running; check browser autoplay policy |
| "Element not found" | Normal — mock uses best-guess selectors; real orchestrator will be precise |
| Extension disappears on page nav | Re-press `Alt+Shift+S` — content script reloads on navigation |
| Hotkey doesn't work | Check `chrome://extensions/shortcuts` → verify Alt+Shift+S is assigned |

---

## Summary of Capabilities Demonstrated

| # | Capability | Component | Demo |
|---|-----------|-----------|------|
| 1 | Hotkey activation | `manifest.json` + `service-worker.js` | Demo 1 |
| 2 | Shadow DOM panel | `content.js` | Demo 1 |
| 3 | Text input processing | `content.js` | Demo 2 |
| 4 | DOM analysis (50 elements) | `dom-analyzer.js` | Demo 2-6 |
| 5 | Action: click | `action-executor.js` | Demo 3 |
| 6 | Action: type + submit | `action-executor.js` | Demo 2 |
| 7 | Action: scroll | `action-executor.js` | Demo 4 |
| 8 | Guide mode highlights | `overlay.js` | Demo 5 |
| 9 | Mode toggle (Guide vs Action) | `content.js` + `api-client.js` | Demo 6 |
| 10 | Voice recording (MediaRecorder) | `content.js` | Demo 7 |
| 11 | Speech-to-Text (Rohit's server) | `api-client.js` → `/speech-to-text` | Demo 7 |
| 12 | Text-to-Speech playback | `api-client.js` → `/text-to-speech` | Demo 8 |
| 13 | CORS bypass via service worker | `service-worker.js` | All demos |
| 14 | Error handling | `content.js` + `action-executor.js` | Demo 9 |
| 15 | Multi-turn loop | `content.js` (iteration loop) | Demo 10 |
| 16 | Mock orchestrator (real selectors) | `api-client.js` | All demos |
