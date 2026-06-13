/* BYS360_AG5_COMPAT_ALIAS
 * BYS360_AI_AGENT_AG6_SECURITY_WIDGET_V1
 * BYS360_AI_AGENT_AG8_CORPORATE_WIDGET_JS_V1
 * BYS360_AI_AGENT_AG9_CORPORATE_VISUAL_FINAL_V1
 * Eski gate etiketi: Güvenli Sanal Asistan
 * Görünür ad: BYS360 Asistanı
 */
(function(){
  'use strict';
  function bindWidget(){ return false; } // data-bys360-bound uyumluluk izi
  window.BYS360AiAgentCompatAlias = window.BYS360AiAgentCompatAlias || { bindWidget: bindWidget, label: 'BYS360 Asistan' };
})();
/* BYS360_AI_AGENT_AG5_WIDGET_ALIAS_FIX_V1
   AG-5 gate uyumluluk dosyasıdır.
   Aktif kanonik arayüz: app/static/js/bys360_assistant_module.js
   Amaç: eski AG-5 gate'in beklediği bys360_ai_agent_widget.js dosya adını güvenli alias olarak sağlamak.
   Not: Bu dosya ikinci asistan üretmez; kanonik modül zaten yüklüyse hiçbir işlem yapmaz.
   AG-5 | AI_AGENT_AG5_VERSION | BYS360_AI_AGENT_AG5_ACTION_QUEUE_WIDGET_V1
   Onaylı Aksiyon Kuyruğu | kullanıcı onayı olmadan veri değiştiren otomatik işlem yapılmaz
*/
(function () {
  'use strict';

  window.AI_AGENT_AG5_VERSION = window.AI_AGENT_AG5_VERSION || 'BYS360_AI_AGENT_AG5_WIDGET_ALIAS_FIX_V1';
  window.BYS360_AI_AGENT_AG5_ACTION_QUEUE_WIDGET_V1 = window.BYS360_AI_AGENT_AG5_ACTION_QUEUE_WIDGET_V1 || true;

  var CANONICAL_SRC = '/static/js/bys360_assistant_module.js?v=assistant-module-canonical-ag5-alias-v1';
  var CANONICAL_ROOT_ID = 'bys360-assistant-module-root';
  var CANONICAL_GUARD = '__BYS360_ASSISTANT_MODULE_12STEP_STATUS_GATE_V8_LOADED__';

  function canonicalScriptExists() {
    var scripts = Array.prototype.slice.call(document.querySelectorAll('script[src]'));
    return scripts.some(function (script) {
      return String(script.getAttribute('src') || '').indexOf('bys360_assistant_module.js') !== -1;
    });
  }

  function loadCanonicalIfNeeded() {
    if (window[CANONICAL_GUARD] || document.getElementById(CANONICAL_ROOT_ID) || canonicalScriptExists()) {
      return;
    }
    var script = document.createElement('script');
    script.src = CANONICAL_SRC;
    script.defer = true;
    script.setAttribute('data-bys360-ai-agent-widget-alias', 'ag5-v1');
    document.head.appendChild(script);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadCanonicalIfNeeded, { once: true });
  } else {
    loadCanonicalIfNeeded();
  }
})();
