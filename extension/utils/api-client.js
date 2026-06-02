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
   * Uses real selectors from the DOM context when available.
   */
  function getMockResponse(request) {
    const input = (request.user_input || '').toLowerCase();
    const sessionId = request.session_id || crypto.randomUUID();
    const mode = request.mode || 'action';
    const elements = (request.context && request.context.interactive_elements) || [];

    // Helper: find element by matching text/tag in DOM context
    function findByText(keywords) {
      return elements.find((el) =>
        keywords.some((kw) => (el.text || '').toLowerCase().includes(kw))
      );
    }
    function findByTag(tag) {
      return elements.find((el) => el.tag === tag);
    }
    function findInput() {
      return elements.find((el) =>
        el.tag === 'input' || el.tag === 'textarea' || el.selector?.includes('input')
      );
    }

    // --- GUIDE MODE: always return highlights, never execute actions ---
    if (mode === 'guide') {
      return buildGuideResponse(sessionId, input, elements, findByText, findByTag, findInput);
    }

    // --- ACTION: search/type into search box ---
    if (input.includes('search') || input.includes('type') || input.includes('find')) {
      const searchTerm = input.replace(/search for|search|type|find/gi, '').trim() || 'test query';
      const searchEl = findInput() || findByText(['search']);
      if (searchEl) {
        return {
          session_id: sessionId,
          message: `I'll search for "${searchTerm}".`,
          mode: 'action',
          actions: [
            { step: 1, type: 'click', selector: searchEl.selector, description: 'Click search box' },
            { step: 2, type: 'type', selector: searchEl.selector, value: searchTerm, description: `Type "${searchTerm}"` },
            { step: 3, type: 'submit', selector: searchEl.selector, description: 'Press Enter to submit' },
          ],
          guide_steps: null,
          done: true,
          follow_up: null,
        };
      }
    }

    // --- ACTION: click something by name ---
    if (input.includes('click') || input.includes('press') || input.includes('open') || input.includes('go to')) {
      // Try to find element matching user's words
      const words = input.replace(/click|press|open|go to|the|button|link|on/gi, '').trim().split(/\s+/);
      const matchEl = elements.find((el) =>
        words.some((w) => w.length > 2 && (el.text || '').toLowerCase().includes(w))
      );
      const target = matchEl || findByTag('button') || findByTag('a') || elements[0];
      if (target) {
        return {
          session_id: sessionId,
          message: `Clicking "${target.text || target.tag}".`,
          mode: 'action',
          actions: [
            { step: 1, type: 'click', selector: target.selector, description: `Click ${target.text || target.tag}` },
          ],
          guide_steps: null,
          done: true,
          follow_up: null,
        };
      }
    }

    // --- ACTION: filter/show ---
    if (input.includes('filter') || input.includes('show') || input.includes('today')) {
      const filterBtn = findByText(['filter', 'sort', 'refine']) || findByTag('button');
      const actions = [];
      if (filterBtn) {
        actions.push({ step: 1, type: 'click', selector: filterBtn.selector, description: `Click ${filterBtn.text || 'filter'}` });
        actions.push({ step: 2, type: 'wait', duration_ms: 500 });
      }
      return {
        session_id: sessionId,
        message: "I'll try to filter the view.",
        mode: 'action',
        actions: actions.length > 0 ? actions : null,
        guide_steps: null,
        done: actions.length > 0,
        follow_up: actions.length > 0 ? null : 'No filter element found on this page.',
      };
    }

    // --- GUIDE: how to / help (in action mode, explicit guide keywords) ---
    if (input.includes('how') || input.includes('guide') || input.includes('help')) {
      return buildGuideResponse(sessionId, input, elements, findByText, findByTag, findInput);
    }

    // --- ACTION: scroll ---
    if (input.includes('scroll down') || input.includes('scroll up')) {
      const direction = input.includes('up') ? 'up' : 'down';
      return {
        session_id: sessionId,
        message: `Scrolling ${direction}.`,
        mode: 'action',
        actions: [
          { step: 1, type: 'scroll', direction, amount: 400 },
        ],
        guide_steps: null,
        done: true,
        follow_up: null,
      };
    }

    // --- DEFAULT: use first DOM element ---
    if (elements.length > 0) {
      const first = elements[0];
      return {
        session_id: sessionId,
        message: `I'll interact with the first element I found: "${first.text || first.tag}".`,
        mode: 'action',
        actions: [
          { step: 1, type: 'click', selector: first.selector, description: `Click ${first.text || first.tag}` },
        ],
        guide_steps: null,
        done: true,
        follow_up: null,
      };
    }

    return {
      session_id: sessionId,
      message: `I understood: "${request.user_input}". No interactive elements found to act on.`,
      mode: request.mode || 'action',
      actions: null,
      guide_steps: null,
      done: true,
      follow_up: null,
    };
  }

  /**
   * Build a guide response with highlights based on real DOM elements.
   */
  function buildGuideResponse(sessionId, input, elements, findByText, findByTag, findInput) {
    const steps = [];
    const searchEl = findInput();
    const navEl = findByTag('a') || findByText(['menu', 'home', 'nav']);
    const btnEl = findByTag('button');

    if (searchEl) {
      steps.push({ step: steps.length + 1, instruction: 'Use the search box to find what you need', highlight_selector: searchEl.selector });
    }
    if (navEl) {
      steps.push({ step: steps.length + 1, instruction: `Click "${navEl.text || 'this link'}" to navigate`, highlight_selector: navEl.selector });
    }
    if (btnEl) {
      steps.push({ step: steps.length + 1, instruction: `Click "${btnEl.text || 'this button'}" to take action`, highlight_selector: btnEl.selector });
    }
    if (steps.length === 0) {
      steps.push({ step: 1, instruction: 'No interactive elements detected on this page', highlight_selector: 'body' });
    }

    return {
      session_id: sessionId,
      message: `Here's how to use this page (${steps.length} steps):`,
      mode: 'guide',
      actions: null,
      guide_steps: steps,
      done: true,
      follow_up: null,
    };
  }

  return { speechToText, textToSpeech, processIntent };
})();
