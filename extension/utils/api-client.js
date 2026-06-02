// SAARTHI AI — API Client
// Routes all HTTP calls through background service worker to bypass CORS

const ApiClient = (() => {
  const SPEECH_BACKEND_URL = 'http://localhost:8000';
  const ORCHESTRATOR_URL = 'http://localhost:8001';

  /**
   * Send a message to background service worker and get response.
   */
  function sendToBackground(message) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else if (response && response.error) {
          reject(new Error(response.error));
        } else {
          resolve(response);
        }
      });
    });
  }

  /**
   * Send recorded audio blob to Rohit's /speech-to-text endpoint.
   * Returns the transcript string.
   */
  async function speechToText(audioBlob) {
    const arrayBuffer = await audioBlob.arrayBuffer();

    const response = await sendToBackground({
      type: 'api-request',
      url: `${SPEECH_BACKEND_URL}/speech-to-text`,
      method: 'POST',
      bodyType: 'formdata',
      body: {
        data: Array.from(new Uint8Array(arrayBuffer)),
        mimeType: audioBlob.type || 'audio/webm',
        filename: 'recording.webm',
      },
    });

    return response.data.transcript;
  }

  /**
   * Send text to Rohit's /text-to-speech endpoint.
   * Returns an audio Blob (MP3).
   */
  async function textToSpeech(text) {
    const response = await sendToBackground({
      type: 'api-request',
      url: `${SPEECH_BACKEND_URL}/text-to-speech?text=${encodeURIComponent(text)}`,
      method: 'POST',
    });

    if (response.type === 'audio') {
      return new Blob([new Uint8Array(response.data)], { type: response.mimeType });
    }
    throw new Error('Unexpected response type from TTS');
  }

  /**
   * Send intent request to the orchestrator (/api/process).
   * Uses mock when orchestrator is unavailable.
   */
  async function processIntent(request) {
    // Try live orchestrator first, fall back to mock
    try {
      const response = await sendToBackground({
        type: 'api-request',
        url: `${ORCHESTRATOR_URL}/api/process`,
        method: 'POST',
        body: request,
      });
      if (response.type === 'json') {
        return response.data;
      }
    } catch (e) {
      // Orchestrator not available — use mock
    }

    return getMockResponse(request);
  }

  /**
   * Mock orchestrator response for testing without Gautam's backend.
   */
  function getMockResponse(request) {
    const input = (request.user_input || '').toLowerCase();
    const sessionId = request.session_id || crypto.randomUUID();

    // Pattern match common commands
    if (input.includes('filter') || input.includes('show') || input.includes('today')) {
      return {
        session_id: sessionId,
        message: "I'll filter the view to show today's items.",
        mode: 'action',
        actions: [
          { step: 1, type: 'click', selector: '[data-testid="filter-btn"], .filter-button, button[title*="Filter"]', description: 'Open filter panel' },
          { step: 2, type: 'wait', duration_ms: 500 },
          { step: 3, type: 'click', selector: '[data-testid="date-filter"], .date-filter', description: 'Select date filter' },
        ],
        guide_steps: null,
        done: false,
        follow_up: "I'll verify the results after the filter is applied.",
      };
    }

    if (input.includes('how') || input.includes('guide') || input.includes('help')) {
      return {
        session_id: sessionId,
        message: "Here's how to navigate this page:",
        mode: 'guide',
        actions: null,
        guide_steps: [
          { step: 1, instruction: 'Look for the navigation menu on the left sidebar', highlight_selector: 'nav, .sidebar, [role="navigation"]' },
          { step: 2, instruction: 'Click on the section you want to explore', highlight_selector: 'nav a, .sidebar a' },
          { step: 3, instruction: 'Use the search bar to find specific items', highlight_selector: 'input[type="search"], .search-input, [placeholder*="Search"]' },
        ],
        done: true,
        follow_up: null,
      };
    }

    if (input.includes('click') || input.includes('press') || input.includes('open')) {
      return {
        session_id: sessionId,
        message: "I'll try to perform that action for you.",
        mode: 'action',
        actions: [
          { step: 1, type: 'click', selector: 'button, a, [role="button"]', description: 'Clicking the target element' },
        ],
        guide_steps: null,
        done: true,
        follow_up: null,
      };
    }

    // Default response
    return {
      session_id: sessionId,
      message: `I understood: "${request.user_input}". The orchestrator will process this once connected.`,
      mode: request.mode || 'action',
      actions: null,
      guide_steps: null,
      done: true,
      follow_up: null,
    };
  }

  return { speechToText, textToSpeech, processIntent };
})();
