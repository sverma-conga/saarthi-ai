// SAARTHI AI — DOM Analyzer
// Extracts interactive elements from the current page for the orchestrator

const DomAnalyzer = (() => {
  const INTERACTIVE_SELECTORS = [
    'button',
    'a[href]',
    'input',
    'select',
    'textarea',
    '[role="button"]',
    '[role="link"]',
    '[role="menuitem"]',
    '[role="tab"]',
    '[onclick]',
    '[data-testid]',
  ].join(', ');

  const MAX_ELEMENTS = 50;

  /**
   * Analyze the DOM and return a snapshot of interactive elements
   * matching the contract schema.
   */
  function analyzeDom() {
    const elements = document.querySelectorAll(INTERACTIVE_SELECTORS);

    return Array.from(elements)
      .filter(isVisible)
      .slice(0, MAX_ELEMENTS)
      .map((el, i) => ({
        id: `el-${i}`,
        tag: el.tagName.toLowerCase(),
        text: getElementText(el),
        selector: getUniqueSelector(el),
        aria_label: el.getAttribute('aria-label') || null,
        placeholder: el.getAttribute('placeholder') || null,
        visible: true,
      }));
  }

  /**
   * Get a summary of visible text on the page (first 500 chars).
   */
  function getVisibleTextSummary() {
    return (document.body.innerText || '').substring(0, 500).trim();
  }

  /**
   * Check if an element is visible in the viewport.
   */
  function isVisible(el) {
    if (el.offsetParent === null && getComputedStyle(el).position !== 'fixed') {
      return false;
    }
    const rect = el.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  /**
   * Extract meaningful text from an element (capped at 50 chars).
   */
  function getElementText(el) {
    const text =
      el.getAttribute('aria-label') ||
      el.getAttribute('title') ||
      el.textContent ||
      el.getAttribute('placeholder') ||
      el.getAttribute('value') ||
      '';
    return text.trim().substring(0, 50);
  }

  /**
   * Generate a unique CSS selector for an element.
   * Priority: data-testid > id > aria-label > CSS path
   */
  function getUniqueSelector(el) {
    // 1. data-testid (most reliable for apps)
    if (el.dataset && el.dataset.testid) {
      return `[data-testid="${el.dataset.testid}"]`;
    }

    // 2. ID (if unique on page)
    if (el.id) {
      return `#${CSS.escape(el.id)}`;
    }

    // 3. aria-label
    const ariaLabel = el.getAttribute('aria-label');
    if (ariaLabel) {
      const selector = `${el.tagName.toLowerCase()}[aria-label="${CSS.escape(ariaLabel)}"]`;
      if (document.querySelectorAll(selector).length === 1) {
        return selector;
      }
    }

    // 4. Fallback: generate CSS path
    return generateCssPath(el);
  }

  /**
   * Generate a CSS selector path from root to element.
   */
  function generateCssPath(el) {
    const parts = [];
    let current = el;

    while (current && current !== document.body && parts.length < 5) {
      let selector = current.tagName.toLowerCase();

      if (current.className && typeof current.className === 'string') {
        const classes = current.className.trim().split(/\s+/).slice(0, 2);
        if (classes.length > 0 && classes[0]) {
          selector += '.' + classes.map(c => CSS.escape(c)).join('.');
        }
      }

      // Add nth-child if needed for uniqueness
      const parent = current.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter(
          (s) => s.tagName === current.tagName
        );
        if (siblings.length > 1) {
          const index = siblings.indexOf(current) + 1;
          selector += `:nth-of-type(${index})`;
        }
      }

      parts.unshift(selector);
      current = current.parentElement;
    }

    return parts.join(' > ');
  }

  return { analyzeDom, getVisibleTextSummary };
})();
