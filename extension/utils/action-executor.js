// SAARTHI AI — Action Executor
// Executes action plans received from the orchestrator on the current page

const ActionExecutor = (() => {
  const STEP_DELAY = 400; // ms between actions

  /**
   * Execute an array of actions sequentially.
   * Returns { success: true } or { success: false, failed_step, error }
   */
  async function executeActions(actions) {
    if (!actions || actions.length === 0) {
      return { success: true, message: 'No actions to execute' };
    }

    for (const action of actions) {
      try {
        await executeStep(action);
        await delay(STEP_DELAY);
      } catch (err) {
        return {
          success: false,
          failed_step: action.step,
          error: err.message,
          description: action.description || '',
        };
      }
    }

    return { success: true, steps_completed: actions.length };
  }

  async function executeStep(action) {
    switch (action.type) {
      case 'click':
        return doClick(action);
      case 'type':
        return doType(action);
      case 'select':
        return doSelect(action);
      case 'scroll':
        return doScroll(action);
      case 'wait':
        return delay(action.duration_ms || 500);
      case 'navigate':
        return doNavigate(action);
      case 'submit':
        return doSubmit(action);
      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }
  }

  function doClick(action) {
    const el = findElement(action.selector);
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    highlightBriefly(el);
    el.click();
  }

  function doType(action) {
    const el = findElement(action.selector);
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    highlightBriefly(el);
    el.focus();
    el.value = action.value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function doSelect(action) {
    const el = findElement(action.selector);
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    highlightBriefly(el);
    el.value = action.value;
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function doSubmit(action) {
    const el = findElement(action.selector);
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    highlightBriefly(el);
    // Try submitting the parent form first
    const form = el.closest('form');
    if (form) {
      form.requestSubmit();
      return;
    }
    // Fallback: dispatch Enter keypress
    const enterEvent = new KeyboardEvent('keydown', {
      key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
    });
    el.dispatchEvent(enterEvent);
  }

  function doScroll(action) {
    const amount = action.amount || 300;
    const direction = action.direction || 'down';
    const y = direction === 'up' ? -amount : amount;
    window.scrollBy({ top: y, behavior: 'smooth' });
  }

  function doNavigate(action) {
    if (!action.url) throw new Error('Navigate action missing url');
    window.location.href = action.url;
  }

  /**
   * Find an element using a selector string.
   * Searches: 1) DomAnalyzer registry, 2) main document, 3) iframes, 4) shadow DOMs, 5) text fallback.
   */
  function findElement(selector) {
    if (!selector) throw new Error('No selector provided');

    // 1. Try DomAnalyzer element registry (works for shadow DOM elements)
    if (selector.startsWith('el-')) {
      const regEl = DomAnalyzer.getElementById(selector);
      if (regEl) return regEl;
    }

    // 2. Try CSS selector in main document
    const selectors = selector.split(',').map((s) => s.trim());
    for (const sel of selectors) {
      try {
        const el = document.querySelector(sel);
        if (el) return el;
      } catch (e) { /* invalid selector */ }
    }

    // 3. Try inside iframes (same-origin)
    const iframes = document.querySelectorAll('iframe');
    for (const iframe of iframes) {
      try {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
        if (iframeDoc) {
          for (const sel of selectors) {
            try {
              const el = iframeDoc.querySelector(sel);
              if (el) return el;
            } catch (e) { /* skip */ }
          }
        }
      } catch (e) { /* cross-origin */ }
    }

    // 4. Deep search shadow DOMs
    function searchShadow(root) {
      for (const sel of selectors) {
        try {
          const el = root.querySelector(sel);
          if (el) return el;
        } catch (e) { /* skip */ }
      }
      const children = root.querySelectorAll('*');
      for (const child of children) {
        if (child.shadowRoot) {
          const found = searchShadow(child.shadowRoot);
          if (found) return found;
        }
      }
      return null;
    }
    const shadowResult = searchShadow(document);
    if (shadowResult) return shadowResult;

    // 5. Text-based fallback (main doc + iframes + shadow DOMs)
    const textHint = selector.replace(/[#.\[\]='"]/g, ' ').trim();
    if (textHint.length > 2) {
      const clickableSelector = 'button, a, [role="button"], input[type="submit"]';

      // Collect all clickable from everywhere
      const allClickable = [];
      function collectClickable(root) {
        allClickable.push(...root.querySelectorAll(clickableSelector));
        const els = root.querySelectorAll('*');
        for (const el of els) {
          if (el.shadowRoot) collectClickable(el.shadowRoot);
        }
      }
      collectClickable(document);
      for (const iframe of iframes) {
        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
          if (iframeDoc) collectClickable(iframeDoc);
        } catch (e) { /* skip */ }
      }

      for (const el of allClickable) {
        const elText = (el.textContent || el.getAttribute('aria-label') || '').trim().toLowerCase();
        if (elText && (elText.includes(textHint.toLowerCase()) || textHint.toLowerCase().includes(elText))) {
          return el;
        }
      }
    }

    throw new Error(`Element not found: ${selector}`);
  }

  /**
   * Briefly highlight an element before acting on it.
   */
  function highlightBriefly(el) {
    const originalOutline = el.style.outline;
    el.style.outline = '3px solid #89b4fa';
    setTimeout(() => {
      el.style.outline = originalOutline;
    }, 600);
  }

  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  return { executeActions };
})();
