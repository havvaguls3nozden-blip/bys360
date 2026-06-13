// BYS360_PERFORMANCE_DASHBOARD_ANALYTICS_JS_OK
(function () {
  "use strict";
  function markReady() {
    var shell = document.querySelector('[data-bys-dashboard="analytics-redesign"]');
    if (!shell) return;
    shell.setAttribute("data-ready", "true");
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", markReady);
  } else {
    markReady();
  }
})();
