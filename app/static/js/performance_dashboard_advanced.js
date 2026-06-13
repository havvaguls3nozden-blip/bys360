// BYS360_PERFORMANCE_DASHBOARD_ADVANCED_JS_OK
(function () {
  "use strict";

  function loadHeavyPanels() {
    const target = document.querySelector("[data-dashboard-heavy-target]");
    if (!target) return;
    const url = (target.getAttribute("data-url") || "").trim();
    if (!url) {
      target.innerHTML = '<div class="pdash-heavy-placeholder"><p>Ek analiz panelleri için bağlantı tanımlı değil. Ana dashboard kullanılabilir.</p></div>';
      return;
    }
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" }, credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("Ek analiz panelleri yüklenemedi");
        return response.text();
      })
      .then(function (html) {
        const safeHtml = (html || "").trim();
        if (!safeHtml) throw new Error("Ek analiz paneli boş döndü");
        target.innerHTML = safeHtml;
      })
      .catch(function () {
        target.innerHTML = '<div class="pdash-card__head compact"><h2>Ek analiz panelleri</h2><i class="fa-solid fa-layer-group"></i></div><div class="pdash-heavy-placeholder"><p>Ek analiz panelleri güvenli modda açılmadı. Ana dashboard ve hızlı geçişler çalışmaya devam eder.</p></div>';
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadHeavyPanels);
  } else {
    loadHeavyPanels();
  }
})();
