
/* BYS360_V18_8_CONTROL_PANEL_TITLE_FIX_START */
(function(){
  "use strict";

  const screenTitleMap = {
    "/performans/stratejik/kpi-dashboard": {
      title: "KPI Dashboard",
      module: "KPI ve Hedef Yönetimi",
      helpKey: "strategic_kpi_dashboard"
    },
    "/performans/stratejik/hedefler": {
      title: "Hedefler",
      module: "KPI ve Hedef Yönetimi",
      helpKey: "strategic_targets"
    },
    "/performans/stratejik/yetkinlik-kutuphanesi": {
      title: "Yetkinlik Kütüphanesi",
      module: "KPI ve Hedef Yönetimi",
      helpKey: "competency_library"
    },
    "/performans/stratejik/oz-degerlendirme": {
      title: "Öz Değerlendirme",
      module: "KPI ve Hedef Yönetimi / Performans Yönetimi",
      helpKey: "self_assessment"
    },
    "/performans/stratejik/ai-kpi-analiz": {
      title: "KPI Analiz Merkezi",
      module: "AI Karar Destek / KPI ve Hedef Yönetimi",
      helpKey: "ai_kpi_analysis"
    },
    "/performance/meeting-development/faz10": {
      title: "Dönem İçi Notlar",
      module: "Performans Yönetimi",
      helpKey: "interim_notes_faz10"
    },
    "/performance/interim-notes": {
      title: "Dönem İçi Notlar",
      module: "Performans Yönetimi",
      helpKey: "interim_notes"
    },
    "/performance/meeting-development/faz9": {
      title: "Hatırlatma ve Aksatan Amirler",
      module: "Performans Yönetimi",
      helpKey: "reminders_delayed_supervisors_faz9"
    },
    "/performance/personnel-support-publish-approvals": {
      title: "Yayın Ön Onayı",
      module: "Performans Yönetimi",
      helpKey: "personnel_support_publish_approvals"
    },
    "/performance/process-reports": {
      title: "Süreç Raporları",
      module: "Performans Yönetimi",
      helpKey: "process_reports"
    },
    "/performance/process-tracking": {
      title: "Süreç Takibi",
      module: "Performans Yönetimi",
      helpKey: "process_tracking"
    }
  };

  function normalizePath(path){
    let p = String(path || "").trim();
    try {
      if (p.startsWith("http://") || p.startsWith("https://")) p = new URL(p).pathname;
    } catch(e){}
    if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
    return p;
  }

  function getScreenInfo(){
    const path = normalizePath(window.location && window.location.pathname || "/");
    if (screenTitleMap[path]) return screenTitleMap[path];

    const keys = Object.keys(screenTitleMap).sort((a,b) => b.length - a.length);
    for (const key of keys) {
      if (path.startsWith(key + "/")) return screenTitleMap[key];
    }
    return null;
  }

  function isControlPanelText(text){
    const t = String(text || "").replace(/\s+/g, " ").trim().toLocaleLowerCase("tr-TR");
    return t === "kontrol paneli" || t === "dashboard" || t === "yönetim paneli";
  }

  function ensureIdentity(info){
    if (!info) return;

    document.body.setAttribute("data-bys360-screen", info.title);
    document.body.setAttribute("data-bys360-module", info.module);
    document.body.setAttribute("data-bys360-help-key", info.helpKey);

    let node = document.getElementById("bys360-official-screen-identity");
    if (!node) {
      node = document.createElement("div");
      node.id = "bys360-official-screen-identity";
      node.hidden = true;
      node.style.display = "none";
      document.body.appendChild(node);
    }

    node.setAttribute("data-bys360-screen", info.title);
    node.setAttribute("data-bys360-module", info.module);
    node.setAttribute("data-bys360-help-key", info.helpKey);
  }

  function replaceVisibleTitles(info){
    if (!info) return false;

    let changed = false;
    const selectors = [
      "h1",
      ".page-title",
      ".page-header h1",
      ".page-header-title",
      ".content-header h1",
      ".content-title",
      ".topbar-title",
      ".module-title",
      ".card-header h1",
      ".dashboard-title",
      "[data-page-title]",
      "[data-title]"
    ];

    document.querySelectorAll(selectors.join(",")).forEach(function(el){
      const text = el.textContent || "";
      if (isControlPanelText(text)) {
        el.textContent = info.title;
        el.setAttribute("data-bys360-title-fixed", "true");
        changed = true;
      }
    });

    // Bazı sayfalarda başlık span/div olarak gelebilir; üstteki büyük yazıyı yakalamak için güvenli dar tarama.
    document.querySelectorAll("main div, main span, .content div, .content span, .container-fluid div, .container-fluid span").forEach(function(el){
      if (el.children && el.children.length > 0) return;
      const text = el.textContent || "";
      if (isControlPanelText(text)) {
        const style = window.getComputedStyle ? window.getComputedStyle(el) : null;
        const fontSize = style ? parseFloat(style.fontSize || "0") : 0;
        const weight = style ? parseInt(style.fontWeight || "0", 10) : 0;
        if (fontSize >= 20 || weight >= 600 || el.className.toString().includes("title")) {
          el.textContent = info.title;
          el.setAttribute("data-bys360-title-fixed", "true");
          changed = true;
        }
      }
    });

    if (document.title && isControlPanelText(document.title)) {
      document.title = info.title + " | BYS360";
      changed = true;
    }

    return changed;
  }

  function applyTitleFix(){
    const info = getScreenInfo();
    if (!info) return null;

    ensureIdentity(info);
    replaceVisibleTitles(info);

    window.BYS360CurrentOfficialScreen = info;
    return info;
  }

  function installAssistantHook(){
    const previousLocal = window.BYS360AssistantLocalAnswer;
    window.BYS360AssistantLocalAnswer = function(question){
      const q = String(question || "").toLocaleLowerCase("tr-TR");
      const asksPage = [
        "hangi ekrandayım",
        "hangi sayfadayım",
        "bu sayfada ne yapabilirim",
        "bu ekran ne işe yarar",
        "bu ekranı anlat",
        "bu sayfayı tanıyor musun"
      ].some(function(p){ return q.includes(p); });

      if (asksPage) {
        const info = applyTitleFix();
        if (info) {
          return [
            "Bulunduğunuz ekran: " + info.title,
            "Modül: " + info.module,
            "",
            "Bu sayfa artık genel Kontrol Paneli başlığıyla değil, resmi ekran kimliğiyle tanımlanır."
          ].join("\n");
        }
      }

      if (typeof previousLocal === "function") return previousLocal(question);
      return null;
    };
  }

  function start(){
    applyTitleFix();
    installAssistantHook();

    // Geç yüklenen başlıklar için birkaç kez daha uygula.
    setTimeout(applyTitleFix, 250);
    setTimeout(applyTitleFix, 900);
    setTimeout(applyTitleFix, 1800);

    // İçerik sonradan değişirse yeniden uygula.
    try {
      const observer = new MutationObserver(function(){
        applyTitleFix();
      });
      observer.observe(document.body, {childList:true, subtree:true});
      window.BYS360TitleFixObserver = observer;
    } catch(e){}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }

  window.BYS360ScreenTitleFixV18_8 = {
    version: "V18.8",
    screenTitleMap,
    applyTitleFix,
    getScreenInfo
  };
})();
/* BYS360_V18_8_CONTROL_PANEL_TITLE_FIX_END */


/* BYS360_V18_8_2_KPI_ANALIZ_MERKEZI_FIX_START */
(function(){
  "use strict";

  const KPI_PATH = "/performans/stratejik/ai-kpi-analiz";
  const KPI_INFO = {
    title: "KPI Analiz Merkezi",
    screen: "KPI Analiz Merkezi",
    module: "Stratejik Performans",
    helpKey: "kpi_analysis_center",
    help: "Şu an KPI Analiz Merkezi ekranındasınız. Bu ekran KPI gerçekleşmeleri, riskli hedefler, yönetici önerileri ve performans bağlantıları için karar destek ekranıdır."
  };

  function normPath(v){
    let p = String(v || "").trim();
    try {
      if (p.startsWith("http://") || p.startsWith("https://")) p = new URL(p).pathname;
    } catch(e){}
    if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
    return p;
  }

  function isKpiPage(){
    const path = normPath(window.location && window.location.pathname || "");
    return path === KPI_PATH || path.startsWith(KPI_PATH + "/");
  }

  function isPageQuestion(question){
    const q = String(question || "").toLocaleLowerCase("tr-TR");
    return [
      "hangi ekrandayım",
      "hangi sayfadayım",
      "bu sayfada ne yapabilirim",
      "bu ekran ne işe yarar",
      "bu ekranı anlat",
      "bu sayfayı tanıyor musun",
      "sayfayı tanı",
      "burada ne yapacağım"
    ].some(function(p){ return q.includes(p); });
  }

  function applyKpiIdentity(){
    if (!isKpiPage()) return null;

    document.body.setAttribute("data-bys360-screen", KPI_INFO.screen);
    document.body.setAttribute("data-bys360-module", KPI_INFO.module);
    document.body.setAttribute("data-bys360-help-key", KPI_INFO.helpKey);

    let node = document.getElementById("bys360-official-screen-identity");
    if (!node) {
      node = document.createElement("div");
      node.id = "bys360-official-screen-identity";
      node.hidden = true;
      node.style.display = "none";
      document.body.appendChild(node);
    }
    node.setAttribute("data-bys360-screen", KPI_INFO.screen);
    node.setAttribute("data-bys360-module", KPI_INFO.module);
    node.setAttribute("data-bys360-help-key", KPI_INFO.helpKey);
    node.setAttribute("data-bys360-help", KPI_INFO.help);

    return KPI_INFO;
  }

  function replaceKpiTitle(){
    if (!isKpiPage()) return;

    const selectors = [
      "h1","h2",".page-title",".content-title",".module-title",".dashboard-title",
      ".page-header-title",".section-title","[data-page-title]","[data-title]"
    ];

    document.querySelectorAll(selectors.join(",")).forEach(function(el){
      const text = (el.textContent || "").trim();
      if (
        text === "AI KPI Analiz" ||
        text === "Kontrol Paneli" ||
        text === "Dashboard" ||
        text.includes("AI KPI Analiz")
      ) {
        el.textContent = KPI_INFO.title;
        el.setAttribute("data-bys360-title-fixed", "kpi-analysis-center");
      }
    });

    // Sayfada eski AI KPI Analiz metni küçük kart/başlık içinde geçiyorsa kullanıcıya görünen yerde düzelt.
    document.querySelectorAll("main *,.content *,.page-content *,.container-fluid *").forEach(function(el){
      if (el.children && el.children.length > 0) return;
      const t = (el.textContent || "").trim();
      if (t === "AI KPI Analiz") {
        el.textContent = KPI_INFO.title;
        el.setAttribute("data-bys360-title-fixed", "kpi-analysis-center");
      }
    });

    if (document.title && document.title.includes("AI KPI Analiz")) {
      document.title = document.title.replaceAll("AI KPI Analiz", KPI_INFO.title);
    }
  }

  function kpiAnswer(){
    return [
      "Bulunduğunuz ekran: KPI Analiz Merkezi",
      "Modül: Stratejik Performans",
      "",
      "Bu ekran KPI gerçekleşmeleri, riskli hedefler, yönetici önerileri ve performans bağlantıları için karar destek ekranıdır.",
      "",
      "Burada yapılabilecekler:",
      "1. KPI gerçekleşmelerini inceleme",
      "2. Riskli hedefleri görme",
      "3. Yönetici önerilerini değerlendirme",
      "4. Performans bağlantılarını kontrol etme"
    ].join("\n");
  }

  function install(){
    applyKpiIdentity();
    replaceKpiTitle();

    // V18.7 resmi ekran kimliği haritasına runtime ekle.
    if (window.BYS360OfficialScreenIdentity && window.BYS360OfficialScreenIdentity.officialScreenIdentityMap) {
      window.BYS360OfficialScreenIdentity.officialScreenIdentityMap[KPI_PATH] = {
        screen: KPI_INFO.screen,
        module: KPI_INFO.module,
        helpKey: KPI_INFO.helpKey,
        help: KPI_INFO.help
      };
    }

    // V18.8 title fix haritasına runtime ekle.
    if (window.BYS360ScreenTitleFixV18_8 && window.BYS360ScreenTitleFixV18_8.screenTitleMap) {
      window.BYS360ScreenTitleFixV18_8.screenTitleMap[KPI_PATH] = {
        title: KPI_INFO.title,
        module: KPI_INFO.module,
        helpKey: KPI_INFO.helpKey
      };
    }

    const previousLocal = window.BYS360AssistantLocalAnswer;
    window.BYS360AssistantLocalAnswer = function(question){
      if (isKpiPage() && isPageQuestion(question)) {
        applyKpiIdentity();
        replaceKpiTitle();
        return kpiAnswer();
      }

      const q = String(question || "").toLocaleLowerCase("tr-TR");
      if (q.includes("kpi analiz") || q.includes("kpi analiz merkezi") || q.includes("riskli hedef")) {
        return kpiAnswer();
      }

      if (typeof previousLocal === "function") {
        const ans = previousLocal(question);
        if (isKpiPage() && ans && (
          ans.includes("AI KPI Analiz") ||
          ans.includes("güvenli menü haritasında özel bir başlıkla eşleşmedi") ||
          ans.includes("Kontrol Paneli")
        )) {
          return kpiAnswer();
        }
        if (typeof ans === "string") {
          return ans.replaceAll("AI KPI Analiz", "KPI Analiz Merkezi");
        }
        return ans;
      }
      return null;
    };

    if (window.BYS360AssistantModule) {
      window.BYS360AssistantModule.kpiAnalysisCenterFix = {
        version: "V18.8.2",
        info: KPI_INFO,
        apply: function(){ applyKpiIdentity(); replaceKpiTitle(); }
      };
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }

  setTimeout(function(){ applyKpiIdentity(); replaceKpiTitle(); }, 300);
  setTimeout(function(){ applyKpiIdentity(); replaceKpiTitle(); }, 1200);
})();
/* BYS360_V18_8_2_KPI_ANALIZ_MERKEZI_FIX_END */

