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

  // Element registry: stores direct references to discovered elements
  // so we can find them later even if they're in shadow DOMs
  let _elementRegistry = new Map();

  /**
   * Get an element by its registry ID (for action execution)
   */
  function getElementById(id) {
    return _elementRegistry.get(id) || null;
  }

  /**
   * Analyze the DOM and return a snapshot of interactive elements
   * matching the contract schema.
   */
  function analyzeDom() {
    // Collect elements from main document, shadow DOMs, AND same-origin iframes
    let allElements = [];

    // Recursive function to find elements including inside shadow DOMs
    function collectFromRoot(root) {
      const found = root.querySelectorAll(INTERACTIVE_SELECTORS);
      allElements = allElements.concat(Array.from(found));

      // Traverse shadow roots of ALL elements in this root
      const allEls = root.querySelectorAll('*');
      for (const el of allEls) {
        if (el.shadowRoot) {
          collectFromRoot(el.shadowRoot);
        }
      }
    }

    // 1. Main document (including shadow DOMs)
    collectFromRoot(document);

    // 2. Same-origin iframes
    try {
      const iframes = document.querySelectorAll('iframe');
      for (let idx = 0; idx < iframes.length; idx++) {
        try {
          const iframeDoc = iframes[idx].contentDocument || iframes[idx].contentWindow?.document;
          if (iframeDoc) {
            collectFromRoot(iframeDoc);
          }
        } catch (e) { /* cross-origin */ }
      }
    } catch (e) { /* iframe scan failed */ }

    // Exclude our own panel elements
    allElements = allElements.filter(el => !el.closest?.('#saarthi-root'));

    const results = allElements
      .filter(isVisible)
      .sort(prioritizeElements)
      .slice(0, MAX_ELEMENTS);

    // Clear and rebuild element registry
    _elementRegistry.clear();
    return results.map((el, i) => {
      const id = `el-${i}`;
      _elementRegistry.set(id, el);
      return {
        id,
        tag: el.tagName.toLowerCase(),
        text: getElementText(el),
        selector: getUniqueSelector(el),
        aria_label: el.getAttribute('aria-label') || null,
        placeholder: el.getAttribute('placeholder') || null,
        visible: true,
      };
    });
  }

  /**
   * Sort elements by priority: buttons/nav first, then inputs, then links.
   * Avoids table data links crowding out actionable elements.
   */
  function prioritizeElements(a, b) {
    return getElementPriority(a) - getElementPriority(b);
  }

  function getElementPriority(el) {
    const tag = el.tagName.toLowerCase();
    // Buttons and role=button are highest priority
    if (tag === 'button' || el.getAttribute('role') === 'button') return 1;
    // Input/select/textarea for forms
    if (tag === 'input' || tag === 'select' || tag === 'textarea') return 2;
    // Nav links (in nav, header, or sidebar)
    if (tag === 'a' && el.closest('nav, header, [role="navigation"], aside')) return 3;
    // Regular links
    if (tag === 'a') return 5;
    // Everything else
    return 4;
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
    // For iframe elements, getComputedStyle/offsetParent are still valid within their document
    try {
      if (el.offsetParent === null && getComputedStyle(el).position !== 'fixed') {
        return false;
      }
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    } catch (e) {
      // If visibility check fails (e.g. detached element), assume visible
      return true;
    }
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

  return { analyzeDom, getVisibleTextSummary, getElementById };
})();
