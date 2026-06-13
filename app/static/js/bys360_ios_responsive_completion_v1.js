/* BYS360_IOS_RESPONSIVE_COMPLETION_V1_JS_BEGIN
   iOS/PWA responsive yardımcı: gövde sınıfı, gerçek viewport yüksekliği, tablo etiketleri ve scroll wrapper.
*/
(function(){
    "use strict";

    var root = document.documentElement;
    var ua = navigator.userAgent || "";
    var platform = navigator.platform || "";
    var isIOS = /iPad|iPhone|iPod/.test(ua) || (platform === "MacIntel" && navigator.maxTouchPoints > 1);
    var isStandalone = (window.navigator.standalone === true) || window.matchMedia("(display-mode: standalone)").matches;
    var isNarrow = function(){ return window.matchMedia && window.matchMedia("(max-width: 820px)").matches; };

    function activate(){
        if (isIOS || isStandalone || isNarrow()) {
            root.classList.add("bys360-ios-responsive-v1");
            if (document.body) document.body.classList.add("bys360-ios-responsive-v1");
        }
    }

    function setViewportUnit(){
        var vh = (window.visualViewport && window.visualViewport.height ? window.visualViewport.height : window.innerHeight) * 0.01;
        root.style.setProperty("--bys360-vh", vh + "px");
    }

    function textOf(node){
        return (node ? (node.textContent || "") : "").replace(/\s+/g, " ").trim();
    }

    function shouldSkipTable(table){
        if (!table || table.dataset.bys360ResponsiveDone === "1") return true;
        var skipSelector = ".calendar, .fc, .fc-view, .dataTable, .dt-scroll, .no-mobile-card, [data-no-mobile-card='1']";
        return !!(table.closest && table.closest(skipSelector));
    }

    function enhanceTables(){
        if (!isNarrow() && !isIOS && !isStandalone) return;
        var tables = document.querySelectorAll("table");
        tables.forEach(function(table){
            if (shouldSkipTable(table)) return;
            table.dataset.bys360ResponsiveDone = "1";

            var parent = table.parentElement;
            if (parent && !parent.classList.contains("table-responsive") && !parent.classList.contains("bys360-responsive-table") && !parent.classList.contains("bys360-table-scroll")) {
                var wrapper = document.createElement("div");
                wrapper.className = "bys360-responsive-table";
                parent.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }

            var headers = Array.prototype.map.call(table.querySelectorAll("thead th"), textOf);
            if (!headers.length) return;
            var rows = table.querySelectorAll("tbody tr");
            if (!rows.length) return;

            table.classList.add("bys360-mobile-card-table");
            rows.forEach(function(row){
                Array.prototype.forEach.call(row.children || [], function(cell, index){
                    if (!cell.getAttribute("data-bys-label")) {
                        cell.setAttribute("data-bys-label", headers[index] || "Bilgi");
                    }
                });
            });
        });
    }

    function markOverflow(){
        if (!isNarrow() && !isIOS && !isStandalone) return;
        var selectors = [
            ".dashboard-grid", ".stats-grid", ".metric-grid", ".kpi-grid", ".ai-grid", ".portal-grid", ".support-grid",
            ".settings-grid", ".performance-grid", ".personnel-grid", ".survey-grid", ".cic-grid", ".report-grid",
            ".toolbar", ".filter-bar", ".action-bar", ".page-actions", ".header-actions"
        ];
        document.querySelectorAll(selectors.join(",")).forEach(function(el){
            el.classList.add("bys360-ios-responsive-managed");
        });
    }

    function run(){
        activate();
        setViewportUnit();
        enhanceTables();
        markOverflow();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", run, {once:true});
    } else {
        run();
    }

    window.addEventListener("resize", function(){ setViewportUnit(); window.clearTimeout(window.__bys360IosRespTimer); window.__bys360IosRespTimer = window.setTimeout(run, 120); }, {passive:true});
    window.addEventListener("orientationchange", function(){ window.setTimeout(run, 260); }, {passive:true});
    if (window.visualViewport) window.visualViewport.addEventListener("resize", setViewportUnit, {passive:true});
})();
/* BYS360_IOS_RESPONSIVE_COMPLETION_V1_JS_END */
