/* BYS360_ANDROID_RESPONSIVE_COMPLETION_V2_JS_BEGIN
   Android/WebView güçlü responsive yardımcı.
   V2: class aktivasyonu, gerçek viewport, geniş eleman baskılama, tablo-kart dönüşümü, AJAX/Morph sonrası yeniden tarama.
*/
(function(){
  "use strict";

  var root = document.documentElement;
  var ua = navigator.userAgent || "";
  var isAndroid = /Android/i.test(ua);
  var isWebView = isAndroid && (/(;\s*wv\)|\bwv\b|Version\/\d+(?:\.\d+)?\s+Chrome\/)/i.test(ua) || !!window.BYS360Android || !!window.Android);
  var isCapacitor = !!(window.Capacitor && (window.Capacitor.isNativePlatform || window.Capacitor.getPlatform));
  var isStandalone = !!(window.matchMedia && window.matchMedia("(display-mode: standalone)").matches);
  var isCoarse = !!(window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
  var isNarrow = function(){ return !!(window.matchMedia && window.matchMedia("(max-width: 1180px)").matches); };

  function activate(){
    if (isAndroid || isWebView || isCapacitor || isStandalone || (isCoarse && isNarrow())) {
      root.classList.add("bys360-android-responsive-v2");
      root.setAttribute("data-bys360-android-responsive", "v2");
      if (isWebView || isCapacitor) root.classList.add("bys360-android-webview-v2");
      if (document.body) {
        document.body.classList.add("bys360-android-responsive-v2");
        document.body.setAttribute("data-bys360-android-responsive", "v2");
      }
    }
  }

  function normalizeViewportMeta(){
    try{
      var meta = document.querySelector('meta[name="viewport"]');
      if (!meta) {
        meta = document.createElement("meta");
        meta.setAttribute("name", "viewport");
        document.head && document.head.prepend(meta);
      }
      var content = meta.getAttribute("content") || "";
      var wanted = "width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content";
      if (!/width\s*=\s*device-width/i.test(content) || !/viewport-fit\s*=\s*cover/i.test(content)) {
        meta.setAttribute("content", wanted);
      }
    }catch(e){}
  }

  function setViewportUnit(){
    var height = (window.visualViewport && window.visualViewport.height) ? window.visualViewport.height : window.innerHeight;
    root.style.setProperty("--bys360-android-v2-vh", (height * 0.01) + "px");
  }

  function textOf(node){
    return (node ? (node.textContent || "") : "").replace(/\s+/g, " ").trim();
  }

  function active(){
    return root.classList.contains("bys360-android-responsive-v2") || isNarrow();
  }

  function skipTable(table){
    if (!table) return true;
    var skipSelector = ".calendar, .fc, .fc-view, .fc-scrollgrid, .flatpickr-calendar, .datepicker, .no-mobile-card, [data-no-mobile-card='1']";
    return !!(table.closest && table.closest(skipSelector));
  }

  function wrapTable(table){
    var parent = table.parentElement;
    if (!parent || parent.classList.contains("bys360-android-v2-table-wrap") || parent.classList.contains("table-responsive")) return;
    var wrapper = document.createElement("div");
    wrapper.className = "bys360-android-v2-table-wrap bys360-android-v2-scroll-x";
    parent.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  }

  function enhanceTables(){
    if (!active()) return;
    var viewport = Math.max(280, window.innerWidth || document.documentElement.clientWidth || 360);
    document.querySelectorAll("table").forEach(function(table){
      if (skipTable(table)) return;
      wrapTable(table);
      var headers = Array.prototype.map.call(table.querySelectorAll("thead th"), textOf);
      var rows = table.querySelectorAll("tbody tr");
      var tooWide = table.scrollWidth > (viewport - 24);
      var manyColumns = headers.length >= 3;
      if ((tooWide || manyColumns) && rows.length) {
        table.classList.add("bys360-android-v2-card-table");
        rows.forEach(function(row){
          Array.prototype.forEach.call(row.children || [], function(cell, index){
            if (!cell.getAttribute("data-bys360-android-v2-label")) {
              cell.setAttribute("data-bys360-android-v2-label", headers[index] || "Bilgi");
            }
          });
        });
      }
      table.dataset.bys360AndroidResponsiveV2 = "1";
    });
  }

  function markContainers(){
    if (!active()) return;
    var selectors = [
      ".app-shell", ".app-main", "#appMain", ".content-wrap", "#contentWrap", ".page-content", ".main-content",
      ".dashboard-grid", ".stats-grid", ".metric-grid", ".kpi-grid", ".ai-grid", ".portal-grid", ".support-grid", ".settings-grid", ".performance-grid", ".personnel-grid", ".survey-grid", ".cic-grid", ".cards-grid", ".summary-grid", ".report-grid", ".quick-actions-grid", ".admin-grid", ".form-grid", ".filter-grid",
      ".toolbar", ".filter-bar", ".action-bar", ".page-actions", ".header-actions", ".form-actions", ".tabbar", ".tabs", ".nav-tabs",
      ".card", ".panel", ".hero", ".hero-card", ".page-hero", ".dashboard-hero", ".info-card", ".stat-card", ".metric-card", ".table-card", ".form-card", ".section-card", ".modal-content"
    ];
    document.querySelectorAll(selectors.join(",")).forEach(function(el){
      el.classList.add("bys360-android-v2-fit");
    });
  }

  function fixWideInlineElements(){
    if (!active()) return;
    var viewport = Math.max(280, window.innerWidth || document.documentElement.clientWidth || 360);
    var candidates = document.querySelectorAll('[style*="width"], [style*="min-width"], .table, .data-table, .datatable, .list-table, .report-table, .chart, .chart-wrap, .apexcharts-canvas, canvas, svg');
    candidates.forEach(function(el){
      if (!el || !el.getBoundingClientRect) return;
      if (el.closest && el.closest(".app-sidebar")) return;
      var rect = el.getBoundingClientRect();
      var sw = el.scrollWidth || rect.width;
      if (sw > viewport + 8 || rect.width > viewport + 8) {
        el.classList.add("bys360-android-v2-fit");
        if (/^(TABLE|THEAD|TBODY|TR|TD|TH)$/i.test(el.tagName)) return;
        try{
          el.style.maxWidth = "100%";
          if (!/CANVAS|SVG/i.test(el.tagName)) el.style.minWidth = "0";
        }catch(e){}
      }
    });
  }

  function closeDuplicateMobileControls(){
    if (!active()) return;
    try{
      var primary = document.getElementById("sidebarToggle") || document.querySelector(".sidebar-toggle");
      var toggles = Array.prototype.slice.call(document.querySelectorAll(".sidebar-toggle, #sidebarToggle, .mobile-menu-toggle, .bys360-mobile-menu-toggle, [data-mobile-menu-toggle]"));
      toggles.forEach(function(btn){
        if (primary && btn !== primary) {
          btn.setAttribute("aria-hidden", "true");
          btn.style.display = "none";
        }
      });
    }catch(e){}
  }

  function run(){
    activate();
    normalizeViewportMeta();
    setViewportUnit();
    markContainers();
    enhanceTables();
    fixWideInlineElements();
    closeDuplicateMobileControls();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run, {once:true});
  else run();
  window.addEventListener("load", function(){ run(); setTimeout(run, 350); setTimeout(run, 1200); }, {once:true});

  var timer;
  function schedule(delay){
    window.clearTimeout(timer);
    setViewportUnit();
    timer = window.setTimeout(run, delay || 120);
  }
  window.addEventListener("resize", function(){ schedule(120); }, {passive:true});
  window.addEventListener("orientationchange", function(){ schedule(320); }, {passive:true});
  if (window.visualViewport) window.visualViewport.addEventListener("resize", function(){ schedule(80); }, {passive:true});

  try{
    var observer = new MutationObserver(function(){ schedule(180); });
    observer.observe(document.documentElement, {childList:true, subtree:true});
  }catch(e){}
})();
/* BYS360_ANDROID_RESPONSIVE_COMPLETION_V2_JS_END */
