// SAARTHI AI — Guide Mode Overlay
// Highlights elements and shows step-by-step instructions

const GuideOverlay = (() => {
  let overlayElements = [];
  let currentStep = 0;
  let steps = [];

  /**
   * Show guide overlay with step-by-step highlights.
   */
  function showGuide(guideSteps) {
    clearOverlay();
    steps = guideSteps || [];
    currentStep = 0;

    if (steps.length === 0) return;

    showStep(currentStep);
  }

  function showStep(index) {
    clearOverlay();
    if (index < 0 || index >= steps.length) return;

    currentStep = index;
    const step = steps[index];

    // Try to find and highlight the element
    let targetEl = null;
    if (step.highlight_selector) {
      const selectors = step.highlight_selector.split(',').map((s) => s.trim());
      for (const sel of selectors) {
        try {
          targetEl = document.querySelector(sel);
          if (targetEl) break;
        } catch (e) {}
      }
    }

    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'saarthi-guide-tooltip';
    tooltip.innerHTML = `
      <div class="saarthi-guide-header">
        <span class="saarthi-guide-step">Step ${step.step} of ${steps.length}</span>
        <button class="saarthi-guide-close">&times;</button>
      </div>
      <div class="saarthi-guide-instruction">${escapeHtml(step.instruction)}</div>
      <div class="saarthi-guide-nav">
        ${index > 0 ? '<button class="saarthi-guide-prev">← Prev</button>' : '<span></span>'}
        ${index < steps.length - 1 ? '<button class="saarthi-guide-next">Next →</button>' : '<button class="saarthi-guide-done">✓ Done</button>'}
      </div>
    `;

    // Style the tooltip
    Object.assign(tooltip.style, {
      position: 'fixed',
      zIndex: '2147483646',
      background: '#1e1e2e',
      color: '#cdd6f4',
      border: '1px solid #89b4fa',
      borderRadius: '12px',
      padding: '14px 18px',
      maxWidth: '320px',
      fontSize: '14px',
      fontFamily: "'Segoe UI', sans-serif",
      boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
      animation: 'fadeIn 0.2s ease-out',
    });

    // Position tooltip near target or center of screen
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const rect = targetEl.getBoundingClientRect();

      // Add highlight ring to target
      const highlight = document.createElement('div');
      Object.assign(highlight.style, {
        position: 'fixed',
        top: `${rect.top - 4}px`,
        left: `${rect.left - 4}px`,
        width: `${rect.width + 8}px`,
        height: `${rect.height + 8}px`,
        border: '3px solid #89b4fa',
        borderRadius: '6px',
        zIndex: '2147483645',
        pointerEvents: 'none',
        animation: 'saarthiPulse 1.5s infinite',
        boxShadow: '0 0 12px rgba(137, 180, 250, 0.4)',
      });
      document.body.appendChild(highlight);
      overlayElements.push(highlight);

      // Position tooltip below or above the target
      const tooltipTop = rect.bottom + 12;
      tooltip.style.top = tooltipTop + 'px';
      tooltip.style.left = Math.max(12, rect.left) + 'px';
    } else {
      tooltip.style.top = '50%';
      tooltip.style.left = '50%';
      tooltip.style.transform = 'translate(-50%, -50%)';
    }

    document.body.appendChild(tooltip);
    overlayElements.push(tooltip);

    // Bind navigation events
    const closeBtn = tooltip.querySelector('.saarthi-guide-close');
    const prevBtn = tooltip.querySelector('.saarthi-guide-prev');
    const nextBtn = tooltip.querySelector('.saarthi-guide-next');
    const doneBtn = tooltip.querySelector('.saarthi-guide-done');

    if (closeBtn) closeBtn.addEventListener('click', clearOverlay);
    if (prevBtn) prevBtn.addEventListener('click', () => showStep(currentStep - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => showStep(currentStep + 1));
    if (doneBtn) doneBtn.addEventListener('click', clearOverlay);

    // Inject animation styles if not already present
    injectStyles();
  }

  function clearOverlay() {
    overlayElements.forEach((el) => {
      if (el.parentNode) el.parentNode.removeChild(el);
    });
    overlayElements = [];
  }

  function injectStyles() {
    if (document.getElementById('saarthi-guide-styles')) return;

    const style = document.createElement('style');
    style.id = 'saarthi-guide-styles';
    style.textContent = `
      @keyframes saarthiPulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 12px rgba(137, 180, 250, 0.4); }
        50% { opacity: 0.7; box-shadow: 0 0 20px rgba(137, 180, 250, 0.7); }
      }
      .saarthi-guide-header {
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
      }
      .saarthi-guide-step {
        font-size: 11px; color: #89b4fa; font-weight: 600; text-transform: uppercase;
      }
      .saarthi-guide-close {
        background: none; border: none; color: #6c7086; font-size: 18px; cursor: pointer; padding: 0 4px;
      }
      .saarthi-guide-close:hover { color: #f38ba8; }
      .saarthi-guide-instruction {
        line-height: 1.5; margin-bottom: 12px; color: #cdd6f4;
      }
      .saarthi-guide-nav {
        display: flex; justify-content: space-between; gap: 8px;
      }
      .saarthi-guide-prev, .saarthi-guide-next, .saarthi-guide-done {
        padding: 6px 14px; border-radius: 6px; border: none; cursor: pointer; font-size: 12px; font-weight: 500;
      }
      .saarthi-guide-prev { background: #313244; color: #cdd6f4; }
      .saarthi-guide-next { background: #89b4fa; color: #1e1e2e; }
      .saarthi-guide-done { background: #a6e3a1; color: #1e1e2e; }
      .saarthi-guide-prev:hover { background: #45475a; }
      .saarthi-guide-next:hover { background: #b4d0fb; }
      .saarthi-guide-done:hover { background: #c4edb8; }
    `;
    document.head.appendChild(style);
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  return { showGuide, clearOverlay };
})();
