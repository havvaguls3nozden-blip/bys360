(function () {
  'use strict';

  var isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

  if (!isiOS) return;

  var panelSelectors = [
    '#bys360AssistantPanel',
    '#bys360Assistant',
    '#assistantPanel',
    '#assistantModal',
    '#aiAgentPanel',
    '.bys360-assistant-panel',
    '.bys360-assistant-window',
    '.assistant-panel',
    '.assistant-window',
    '.chatbot-panel',
    '.ai-agent-panel',
    '.sanal-asistan-panel'
  ];

  var inputSelectors = [
    '#assistantInputArea',
    '#bys360AssistantInputArea',
    'input[id*="assistant" i]',
    'textarea[id*="assistant" i]',
    'input[class*="assistant" i]',
    'textarea[class*="assistant" i]',
    '.assistant-input input',
    '.assistant-input textarea',
    '.assistant-composer input',
    '.assistant-composer textarea',
    '.bys360-assistant-input input',
    '.bys360-assistant-input textarea',
    '.bys360-assistant-composer input',
    '.bys360-assistant-composer textarea',
    '.chatbot-input input',
    '.chatbot-input textarea',
    '.ai-agent-input input',
    '.ai-agent-input textarea'
  ];

  function qsa(list) {
    return list.flatMap(function (sel) {
      try { return Array.prototype.slice.call(document.querySelectorAll(sel)); }
      catch (e) { return []; }
    });
  }

  function isVisible(el) {
    if (!el) return false;
    var st = window.getComputedStyle(el);
    var rect = el.getBoundingClientRect();
    return st.display !== 'none' && st.visibility !== 'hidden' && st.opacity !== '0' &&
      rect.width > 10 && rect.height > 10;
  }

  function anyPanelVisible() {
    return qsa(panelSelectors).some(isVisible);
  }

  function markState() {
    var open = anyPanelVisible();
    document.body.classList.toggle('bys360-ios-assistant-open', open);
    if (open) {
      window.setTimeout(function () {
        var inputs = qsa(inputSelectors).filter(isVisible);
        if (inputs.length) {
          var input = inputs[0];
          try { input.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } catch (e) {}
        }
      }, 160);
    }
  }

  document.addEventListener('click', function () {
    window.setTimeout(markState, 80);
    window.setTimeout(markState, 300);
  }, true);

  document.addEventListener('touchend', function () {
    window.setTimeout(markState, 80);
    window.setTimeout(markState, 300);
  }, true);

  window.addEventListener('resize', function () {
    window.setTimeout(markState, 120);
  });

  window.addEventListener('orientationchange', function () {
    window.setTimeout(markState, 350);
  });

  document.addEventListener('focusin', function (e) {
    var t = e.target;
    if (!t) return;
    var s = (t.id || '') + ' ' + (t.className || '');
    if (/assistant|chatbot|ai-agent/i.test(s)) {
      document.body.classList.add('bys360-ios-assistant-open');
      window.setTimeout(function () {
        try { t.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } catch (err) {}
      }, 250);
    }
  }, true);

  var obs = new MutationObserver(function () {
    window.setTimeout(markState, 80);
  });

  function start() {
    try {
      obs.observe(document.body, { attributes: true, childList: true, subtree: true, attributeFilter: ['class', 'style', 'hidden'] });
    } catch (e) {}
    markState();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
/* BYS360 iOS visualViewport gate marker */
(function () {
    if (window.visualViewport) {
        document.documentElement.style.setProperty('--bys360-ios-vh', window.visualViewport.height + 'px');
    }
})();
