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
   * Supports comma-separated fallback selectors.
   */
  function findElement(selector) {
    if (!selector) throw new Error('No selector provided');

    // Try each comma-separated selector
    const selectors = selector.split(',').map((s) => s.trim());
    for (const sel of selectors) {
      try {
        const el = document.querySelector(sel);
        if (el) return el;
      } catch (e) {
        // Invalid selector, try next
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
