// SAARTHI AI — Content Script
// Injects floating panel with shadow DOM isolation

(function () {
  'use strict';

  let panelVisible = false;
  let container = null;
  let currentAudio = null; // Track current TTS audio for stop functionality

  // Listen for toggle message from background service worker
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.action === 'toggle-panel') {
      panelVisible ? hidePanel() : showPanel();
      panelVisible = !panelVisible;
    }
  });

  function showPanel() {
    if (container) {
      container.style.display = 'block';
      return;
    }

    container = document.createElement('div');
    container.id = 'saarthi-root';

    const shadow = container.attachShadow({ mode: 'open' });
    shadow.innerHTML = `
      <style>${getPanelStyles()}</style>
      <div class="saarthi-panel">
        <div class="panel-header">
          <span class="panel-title">SAARTHI AI</span>
          <div class="header-actions">
            <span class="status-dot"></span>
            <button class="close-btn" title="Close">&times;</button>
          </div>
        </div>

        <div class="mode-toggle">
          <button class="mode-btn active" data-mode="action">⚡ Action</button>
          <button class="mode-btn" data-mode="guide">📖 Guide</button>
        </div>

        <div class="response-area">
          <p class="placeholder-text">Press the mic or type a command...</p>
        </div>

        <div class="input-area">
          <button class="mic-btn" title="Start voice input">🎤</button>
          <input type="text" class="text-input" placeholder="Type a command..." />
          <button class="stop-tts-btn" title="Stop speaking" style="display:none;">⏹</button>
          <button class="send-btn" title="Send">➤</button>
        </div>

        <div class="status-bar">
          <span class="status-text">Ready</span>
        </div>
      </div>
    `;

    document.body.appendChild(container);
    bindPanelEvents(shadow);
  }

  function hidePanel() {
    if (container) {
      container.style.display = 'none';
    }
  }

  function bindPanelEvents(shadow) {
    // Close button
    shadow.querySelector('.close-btn').addEventListener('click', () => {
      hidePanel();
      panelVisible = false;
    });

    // Mode toggle
    const modeBtns = shadow.querySelectorAll('.mode-btn');
    modeBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        modeBtns.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });

    // Send button
    shadow.querySelector('.send-btn').addEventListener('click', () => {
      const input = shadow.querySelector('.text-input');
      const text = input.value.trim();
      if (text) {
        handleUserInput(shadow, text);
        input.value = '';
      }
    });

    // Enter key in input
    shadow.querySelector('.text-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        shadow.querySelector('.send-btn').click();
      }
    });

    // Stop TTS button
    shadow.querySelector('.stop-tts-btn').addEventListener('click', () => {
      stopCurrentAudio(shadow);
    });

    // Mic button — MediaRecorder voice capture
    let mediaRecorder = null;
    let audioChunks = [];
    const micBtn = shadow.querySelector('.mic-btn');

    micBtn.addEventListener('click', async () => {
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        // Stop recording
        mediaRecorder.stop();
        micBtn.classList.remove('recording');
        updateStatus(shadow, 'Processing audio...');
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach((t) => t.stop());
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

          updateStatus(shadow, 'Sending to speech-to-text...');
          try {
            const transcript = await ApiClient.speechToText(audioBlob);
            updateStatus(shadow, `Transcript: "${transcript}"`);
            // Clear input and auto-send the transcript
            shadow.querySelector('.text-input').value = '';
            handleUserInput(shadow, transcript);
          } catch (err) {
            updateStatus(shadow, `STT Error: ${err.message}`);
            showResponse(shadow, `⚠️ Speech-to-text failed: ${err.message}`, 'error');
          }
        };

        mediaRecorder.start();
        micBtn.classList.add('recording');
        updateStatus(shadow, '🎤 Recording... click mic again to stop');
      } catch (err) {
        updateStatus(shadow, `Mic error: ${err.message}`);
      }
    });
  }

  const MAX_ITERATIONS = 10;

  async function handleUserInput(shadow, text) {
    const mode = shadow.querySelector('.mode-btn.active').dataset.mode;
    showResponse(shadow, `<div class="message user-message">${escapeHtml(text)}</div><div class="message ai-message">⏳ Processing...</div>`, 'html');
    updateStatus(shadow, `Sending to AI [${mode} mode]...`);

    const sessionId = crypto.randomUUID();
    let previousActions = [];
    let lastError = null;
    let taskState = null;
    let iteration = 0;
    let done = false;

    try {
      while (!done && iteration < MAX_ITERATIONS) {
        iteration++;

        const request = {
          session_id: sessionId,
          user_input: text,
          mode: mode,
          context: {
            url: window.location.href,
            page_title: document.title,
            interactive_elements: DomAnalyzer.analyzeDom(),
            visible_text_summary: DomAnalyzer.getVisibleTextSummary(),
          },
          previous_actions: previousActions,
          error_from_last_action: lastError,
          task_state: taskState,
        };

        updateStatus(shadow, iteration > 1
          ? `🔄 Iteration ${iteration}/${MAX_ITERATIONS}...`
          : `Sending to AI [${mode} mode]...`);

        const response = await ApiClient.processIntent(request);

        // Persist task_state for next iteration (orchestrator round-trip)
        if (response.task_state) {
          taskState = response.task_state;
        }

        // Display AI message
        showResponse(shadow,
          `<div class="message user-message">${escapeHtml(text)}</div>` +
          `<div class="message ai-message">${escapeHtml(response.message)}</div>`,
          'html'
        );

        // Normalize actions: support both `actions` (batch) and `next_action` (single)
        const actions = response.actions && response.actions.length > 0
          ? response.actions
          : response.next_action
            ? [response.next_action]
            : null;

        // Execute actions, show guide, or handle knowledge response
        if (actions && actions.length > 0) {
          updateStatus(shadow, `⚡ Executing actions (iteration ${iteration})...`);
          const result = await ActionExecutor.executeActions(actions);

          // Track executed actions for next iteration
          previousActions = previousActions.concat(actions.map((a, i) => ({
            ...a,
            executed: i < result.steps_completed,
          })));

          if (result.success) {
            lastError = null;
          } else {
            lastError = `Step ${result.failed_step}: ${result.error}`;
          }
        } else if (response.guide_steps && response.guide_steps.length > 0) {
          updateStatus(shadow, `📖 Guide: ${response.guide_steps.length} steps`);
          GuideOverlay.showGuide(response.guide_steps);
          done = true;
          break;
        } else if (response.mode === 'knowledge') {
          // Knowledge mode: just display the answer, no actions needed
          done = true;
          break;
        }

        // Check if orchestrator says we're done
        done = response.done !== false;

        // If not done, wait briefly for page to settle after actions
        if (!done) {
          await new Promise((r) => setTimeout(r, 800));
        }
      }

      // Final status & TTS — only speak the FINAL response
      if (done) {
        updateStatus(shadow, `✓ Done — ${previousActions.length} total action(s) in ${iteration} iteration(s)`);
      } else {
        updateStatus(shadow, `⚠️ Stopped after ${MAX_ITERATIONS} iterations (${previousActions.length} actions executed)`);
      }

      // Play TTS only once at the end (get the last displayed message)
      const lastAiMsg = shadow.querySelector('.response-area .ai-message');
      if (lastAiMsg) {
        playTTS(shadow, lastAiMsg.textContent);
      }

    } catch (err) {
      showResponse(shadow, `⚠️ Error: ${err.message}`, 'error');
      updateStatus(shadow, `Error: ${err.message}`);
    }
  }

  async function playTTS(shadow, text) {
    try {
      // Stop any currently playing audio first
      stopCurrentAudio(shadow);

      const audioBlob = await ApiClient.textToSpeech(text);
      const audioUrl = URL.createObjectURL(audioBlob);
      currentAudio = new Audio(audioUrl);

      // Show stop button while speaking
      const stopBtn = shadow.querySelector('.stop-tts-btn');
      if (stopBtn) stopBtn.style.display = 'inline-flex';

      currentAudio.play();
      currentAudio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        currentAudio = null;
        if (stopBtn) stopBtn.style.display = 'none';
      };
    } catch (err) {
      // TTS is non-critical — silently fail
      console.warn('SAARTHI TTS failed:', err.message);
    }
  }

  function stopCurrentAudio(shadow) {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
    }
    const stopBtn = shadow.querySelector('.stop-tts-btn');
    if (stopBtn) stopBtn.style.display = 'none';
  }

  function showResponse(shadow, content, type) {
    const responseArea = shadow.querySelector('.response-area');
    if (type === 'html') {
      responseArea.innerHTML = content;
    } else {
      responseArea.innerHTML = `<div class="message ai-message">${escapeHtml(content)}</div>`;
    }
  }

  function updateStatus(shadow, text) {
    shadow.querySelector('.status-text').textContent = text;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function getPanelStyles() {
    return `
      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }

      .saarthi-panel {
        width: 380px;
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        color: #cdd6f4;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 14px;
        overflow: hidden;
        animation: slideUp 0.2s ease-out;
      }

      @keyframes slideUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 16px;
        background: #181825;
        border-bottom: 1px solid #313244;
      }

      .panel-title {
        font-weight: 700;
        font-size: 15px;
        color: #89b4fa;
        letter-spacing: 0.5px;
      }

      .header-actions {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #a6e3a1;
        animation: pulse 2s infinite;
      }

      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
      }

      .close-btn {
        background: none;
        border: none;
        color: #6c7086;
        font-size: 20px;
        cursor: pointer;
        line-height: 1;
        padding: 2px 6px;
        border-radius: 4px;
      }

      .close-btn:hover {
        background: #313244;
        color: #f38ba8;
      }

      .mode-toggle {
        display: flex;
        padding: 10px 16px;
        gap: 8px;
      }

      .mode-btn {
        flex: 1;
        padding: 8px 12px;
        border: 1px solid #313244;
        border-radius: 8px;
        background: #181825;
        color: #6c7086;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.15s;
      }

      .mode-btn:hover {
        border-color: #89b4fa;
        color: #89b4fa;
      }

      .mode-btn.active {
        background: #89b4fa;
        color: #1e1e2e;
        border-color: #89b4fa;
        font-weight: 600;
      }

      .response-area {
        padding: 16px;
        min-height: 120px;
        max-height: 240px;
        overflow-y: auto;
        border-bottom: 1px solid #313244;
      }

      .placeholder-text {
        color: #6c7086;
        font-style: italic;
        text-align: center;
        margin-top: 40px;
      }

      .message {
        padding: 10px 14px;
        border-radius: 10px;
        margin-bottom: 8px;
        line-height: 1.4;
      }

      .user-message {
        background: #313244;
        color: #cdd6f4;
      }

      .ai-message {
        background: #1e3a5f;
        color: #89dceb;
      }

      .input-area {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        gap: 8px;
      }

      .mic-btn, .send-btn {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        font-size: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.15s;
      }

      .mic-btn {
        background: #313244;
        color: #f38ba8;
      }

      .mic-btn:hover {
        background: #f38ba8;
        color: #1e1e2e;
      }

      .mic-btn.recording {
        background: #f38ba8;
        color: #1e1e2e;
        animation: pulse 0.8s infinite;
      }

      .send-btn {
        background: #89b4fa;
        color: #1e1e2e;
      }

      .send-btn:hover {
        background: #b4d0fb;
      }

      .stop-tts-btn {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        font-size: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #f38ba8;
        color: #1e1e2e;
        transition: all 0.15s;
        animation: pulse 0.8s infinite;
      }

      .stop-tts-btn:hover {
        background: #eb6f92;
      }

      .text-input {
        flex: 1;
        padding: 10px 14px;
        border: 1px solid #313244;
        border-radius: 8px;
        background: #181825;
        color: #cdd6f4;
        font-size: 13px;
        outline: none;
        transition: border-color 0.15s;
      }

      .text-input:focus {
        border-color: #89b4fa;
      }

      .text-input::placeholder {
        color: #6c7086;
      }

      .status-bar {
        padding: 8px 16px;
        background: #181825;
        border-top: 1px solid #313244;
      }

      .status-text {
        font-size: 11px;
        color: #6c7086;
      }
    `;
  }
})();
