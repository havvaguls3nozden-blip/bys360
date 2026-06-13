/* BYS360_ANDROID_RESPONSIVE_COMPLETION_V1_JS_BEGIN
   Android/WebView responsive yardımcı: gövde sınıfı, gerçek viewport yüksekliği, tablo etiketleri ve taşma yönetimi.
*/
(function(){
    "use strict";

    var root = document.documentElement;
    var ua = navigator.userAgent || "";
    var isAndroid = /Android/i.test(ua);
    var isWebView = isAndroid && (/(; wv\)|\bwv\b|Version\/\d+\.\d+ Chrome\/)/i.test(ua) || !!window.BYS360Android || !!window.Android);
    var isStandalone = window.matchMedia && window.matchMedia("(display-mode: standalone)").matches;
    var isNarrow = function(){ return window.matchMedia && window.matchMedia("(max-width: 900px)").matches; };

    function activate(){
        if (isAndroid || isWebView || isStandalone || isNarrow()) {
            root.classList.add("bys360-android-responsive-v1");
            if (document.body) document.body.classList.add("bys360-android-responsive-v1");
        }
        if (isWebView) {
            root.classList.add("bys360-android-webview-v1");
            if (document.body) document.body.classList.add("bys360-android-webview-v1");
        }
    }

    function setViewportUnit(){
        var height = window.visualViewport && window.visualViewport.height ? window.visualViewport.height : window.innerHeight;
        var vh = height * 0.01;
        root.style.setProperty("--bys360-android-vh", vh + "px");
    }

    function textOf(node){
        return (node ? (node.textContent || "") : "").replace(/\s+/g, " ").trim();
    }

    function shouldSkipTable(table){
        if (!table || table.dataset.bys360AndroidResponsiveDone === "1") return true;
        var skipSelector = ".calendar, .fc, .fc-view, .fc-scrollgrid, .dataTable, .dt-scroll, .no-mobile-card, [data-no-mobile-card='1']";
        return !!(table.closest && table.closest(skipSelector));
    }

    function wrapTable(table){
        var parent = table.parentElement;
        if (!parent) return;
        var alreadyWrapped = parent.classList && (
            parent.classList.contains("table-responsive") ||
            parent.classList.contains("bys360-responsive-table") ||
            parent.classList.contains("bys360-table-scroll") ||
            parent.classList.contains("android-table-scroll")
        );
        if (alreadyWrapped) return;
        var wrapper = document.createElement("div");
        wrapper.className = "android-table-scroll bys360-android-overflow-managed";
        parent.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    }

    function enhanceTables(){
        if (!isNarrow() && !isAndroid && !isWebView && !isStandalone) return;
        var tables = document.querySelectorAll("table");
        tables.forEach(function(table){
            if (shouldSkipTable(table)) return;
            table.dataset.bys360AndroidResponsiveDone = "1";
            wrapTable(table);

            var headers = Array.prototype.map.call(table.querySelectorAll("thead th"), textOf);
            if (!headers.length) return;
            var rows = table.querySelectorAll("tbody tr");
            if (!rows.length) return;
            if (headers.length > 2 || table.scrollWidth > (window.innerWidth - 24)) {
                table.classList.add("bys360-android-mobile-card-table");
                rows.forEach(function(row){
                    Array.prototype.forEach.call(row.children || [], function(cell, index){
                        if (!cell.getAttribute("data-bys-android-label")) {
                            cell.setAttribute("data-bys-android-label", headers[index] || "Bilgi");
                        }
                    });
                });
            }
        });
    }

    function markOverflow(){
        if (!isNarrow() && !isAndroid && !isWebView && !isStandalone) return;
        var selectors = [
            ".dashboard-grid", ".stats-grid", ".metric-grid", ".kpi-grid", ".ai-grid", ".portal-grid", ".support-grid",
            ".settings-grid", ".performance-grid", ".personnel-grid", ".survey-grid", ".cic-grid", ".report-grid",
            ".toolbar", ".filter-bar", ".action-bar", ".page-actions", ".header-actions", ".form-actions", ".tabbar", ".tabs"
        ];
        document.querySelectorAll(selectors.join(",")).forEach(function(el){
            el.classList.add("bys360-android-overflow-managed");
        });
    }

    function markActuallyWideElements(){
        if (!isNarrow() && !isAndroid && !isWebView && !isStandalone) return;
        var candidates = document.querySelectorAll(".card, .panel, .table-card, .form-card, .section-card, .content-wrap, .page-content, .main-content, .modal-content");
        candidates.forEach(function(el){
            if (!el || !el.scrollWidth || !el.clientWidth) return;
            if (el.scrollWidth > el.clientWidth + 8) {
                el.classList.add("bys360-android-overflow-managed");
            }
        });
    }

    function run(){
        activate();
        setViewportUnit();
        enhanceTables();
        markOverflow();
        markActuallyWideElements();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", run, {once:true});
    } else {
        run();
    }

    var timer;
    function schedule(){
        window.clearTimeout(timer);
        setViewportUnit();
        timer = window.setTimeout(run, 140);
    }

    window.addEventListener("resize", schedule, {passive:true});
    window.addEventListener("orientationchange", function(){ window.setTimeout(run, 280); }, {passive:true});
    if (window.visualViewport) window.visualViewport.addEventListener("resize", setViewportUnit, {passive:true});
})();
/* BYS360_ANDROID_RESPONSIVE_COMPLETION_V1_JS_END */
