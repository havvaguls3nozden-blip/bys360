(function () {
  function findToggle() {
    return document.querySelector(
      '.bys360-assistant-toggle, .bys360-ai-assistant-toggle, .assistant-toggle, #bys360AssistantToggle, [class*="assistant"][class*="toggle"]'
    );
  }

  function placeLabel() {
    var toggle = findToggle();
    if (!toggle) return;

    var label = document.getElementById('bys360AssistantClosedLabel');
    if (!label) {
      label = document.createElement('div');
      label.id = 'bys360AssistantClosedLabel';
      label.textContent = 'BYS360 Asistanı';
      document.body.appendChild(label);
    }

    var panel = document.querySelector('.bys360-assistant-panel, .assistant-panel, #bys360AssistantPanel');
    var isOpen = panel && panel.offsetParent !== null && panel.getBoundingClientRect().width > 120;

    label.style.display = isOpen ? 'none' : 'block';

    var r = toggle.getBoundingClientRect();
    label.style.position = 'fixed';
    label.style.left = Math.max(8, r.left + (r.width / 2) - 58) + 'px';
    label.style.top = Math.max(8, r.top - 34) + 'px';
    label.style.zIndex = '9999999';
    label.style.background = '#8B0000';
    label.style.color = '#fff';
    label.style.fontSize = '13px';
    label.style.fontWeight = '700';
    label.style.padding = '8px 12px';
    label.style.borderRadius = '999px';
    label.style.boxShadow = '0 8px 22px rgba(0,0,0,.18)';
    label.style.pointerEvents = 'none';
    label.style.whiteSpace = 'nowrap';
  }

  document.addEventListener('DOMContentLoaded', function () {
    placeLabel();
    setInterval(placeLabel, 700);
  });

  window.addEventListener('resize', placeLabel);
  window.addEventListener('scroll', placeLabel, true);
  document.addEventListener('click', function () {
    setTimeout(placeLabel, 200);
  });
})();
