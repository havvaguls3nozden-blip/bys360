(function () {
  "use strict";

  const UX_VERSION = "UX1_TOP_BANNER_REMOVE_V1";
  const TECHNICAL_WORDS = [
    "workflow", "phase", "sync", "gate", "endpoint", "json", "debug", "traceback",
    "exception", "unauthorized_scope", "raw error", "stack"
  ];

  const CONTEXTS = [
    {
      key: "performance",
      test: /performans|performance|evaluation|scorecard|karne/i,
      title: "Performans işlemleri",
      summary: "Dönem, görev, puanlama, onay ve karne işlemlerini buradan yönetirsiniz.",
      steps: ["Dönemi seçin", "Eksik görevleri kontrol edin", "Onay/yayın adımını tamamlayın"],
      warning: "70 altı sonuçlar ve yayın işlemleri yetkili onay tamamlanmadan personele açılmamalıdır."
    },
    {
      key: "personnel",
      test: /personel|personnel|hr|izin|vekalet|delegation|leave/i,
      title: "Personel ve organizasyon işlemleri",
      summary: "Personel kaydı, birim, yönetici, izin ve vekâlet bilgilerini buradan yönetirsiniz.",
      steps: ["Personeli bulun", "Bilgiyi kontrol edin", "Değişikliği kaydedin"],
      warning: "Personel, birim ve yönetici bilgisi performans zincirini doğrudan etkiler."
    },
    {
      key: "communication",
      test: /mesaj|message|communication|duyuru|announcement|survey|anket|feedback|geri-bildirim|support|destek/i,
      title: "İletişim ve geri bildirim işlemleri",
      summary: "Mesaj, duyuru, anket, geri bildirim ve destek taleplerini buradan takip edersiniz.",
      steps: ["Kayıtları filtreleyin", "İşlem bekleyeni açın", "Yanıt veya durum güncelleyin"],
      warning: "Kişisel veya hassas içerikleri yalnızca yetkiniz olan kapsamda görüntüleyin."
    },
    {
      key: "settings",
      test: /settings|ayar|yetki|role|menu|admin|authority|permission/i,
      title: "Ayar ve yetki işlemleri",
      summary: "Rol, menü görünürlüğü, modül ayarı ve sistem davranışlarını buradan yönetirsiniz.",
      steps: ["Kullanıcı/rol seçin", "Yetkiyi kontrol edin", "Değişikliği kaydedip test edin"],
      warning: "Yetki değişikliği menü görünürlüğüyle birlikte backend erişimini de etkilemelidir."
    },
    {
      key: "dashboard",
      test: /dashboard|anasayfa|home|rapor|report|executive|özet|summary/i,
      title: "Özet ve rapor ekranı",
      summary: "Bugün dikkat isteyen işlemleri, sayıları ve yönetici özetlerini buradan görürsünüz.",
      steps: ["Özet kartlara bakın", "Riskli veya bekleyen kaydı açın", "Detay rapora geçin"],
      warning: "Özet kartları karar desteği içindir; nihai işlem ilgili modül ekranında yapılmalıdır."
    },
    {
      key: "ai",
      test: /ai|asistan|assistant|karar-destek|decision/i,
      title: "AI ve asistan desteği",
      summary: "Yetkiniz dahilindeki özet, rehberlik ve yönlendirmeleri buradan alırsınız.",
      steps: ["Soruyu kısa yazın", "Önerilen ekrana geçin", "Son kararı insan kontrolüyle verin"],
      warning: "AI karar vermez; yalnızca özet, rehberlik ve karar desteği sağlar."
    }
  ];

  function normalizeText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function getPageText() {
    return [document.title, location.pathname, document.body ? document.body.innerText.slice(0, 3000) : ""].join(" ");
  }

  function resolveContext() {
    const text = getPageText();
    return CONTEXTS.find((item) => item.test.test(text)) || {
      key: "generic",
      title: "Sayfa işlemleri",
      summary: "Bu sayfadaki kayıtları görüntüler, kontrol eder ve yetkiniz dahilindeki işlemleri yaparsınız.",
      steps: ["Özet bilgiyi okuyun", "İşlem bekleyen kaydı açın", "Kaydetmeden önce kontrol edin"],
      warning: "Yetkiniz olmayan işlem veya veri için sistem erişimi sınırlandırmalıdır."
    };
  }

  function findMainContainer() {
    return document.querySelector("main .container-fluid") ||
      document.querySelector("main .container") ||
      document.querySelector("main") ||
      document.querySelector(".content-wrapper") ||
      document.querySelector(".main-content") ||
      document.body;
  }

  function askScreenGuide(context) {
    const prompt = `Bu ekranı sade anlat: ${context.title}. Kullanıcı burada ne yapmalı?`;
    if (window.BYS360AIEverywhereV2 && typeof window.BYS360AIEverywhereV2.ask === "function") {
      window.BYS360AIEverywhereV2.ask(prompt);
      return;
    }
    if (window.BYS360AssistantModule && typeof window.BYS360AssistantModule.open === "function") {
      try {
        window.BYS360AssistantModule.open({ question: prompt, source: "ux1-simple-screen-guide" });
      } catch (err) {
        window.BYS360AssistantModule.open();
      }
    }
  }

  function removeGlobalQuickLogicCard() {
    document.querySelectorAll(".bys360-ux1-quick-logic").forEach((card) => card.remove());
  }

  function renderQuickLogicCard() {
    // UX-1 TOP BANNER REMOVE V1:
    // Global top banner was visually too heavy and its toggle created confusion.
    // Keep the useful UX-1 behavior (long text simplifier + primary action focus),
    // but never inject a full-width "Kısa ekran mantığı" banner at the top.
    removeGlobalQuickLogicCard();
    return null;
  }

  function isExcludedElement(el) {
    if (!el || !el.closest) return true;
    if (el.closest("nav, aside, footer, header, form, table, pre, code, script, style, .modal, .dropdown-menu, .navbar, .sidebar")) return true;
    if (el.closest(".bys360-ux1-quick-logic, .bys360-ai-everywhere-card, .bys360-ai-everywhere-answer")) return true;
    if (el.querySelector("input, select, textarea, button, table, iframe, canvas")) return true;
    return false;
  }

  function hasTechnicalNoise(text) {
    const lower = text.toLowerCase();
    return TECHNICAL_WORDS.some((word) => lower.includes(word));
  }

  function simplifyLongTextBlocks() {
    const candidates = Array.from(document.querySelectorAll([
      "main p",
      "main .alert",
      "main .card-text",
      "main .help-text",
      "main .page-description",
      "main .description",
      ".content-wrapper p",
      ".main-content p"
    ].join(",")));

    const seen = new Set();
    candidates.forEach((el) => {
      if (seen.has(el)) return;
      seen.add(el);
      if (isExcludedElement(el)) return;
      if (el.dataset.ux1Processed === "true") return;
      const text = normalizeText(el.innerText);
      if (text.length < 260 && !hasTechnicalNoise(text)) return;

      el.dataset.ux1Processed = "true";
      el.classList.add("bys360-ux1-long-text", "is-collapsed");
      if (hasTechnicalNoise(text)) el.classList.add("has-technical-noise");

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "bys360-ux1-more";
      btn.textContent = "Detayı göster";
      btn.addEventListener("click", function () {
        const expanded = !el.classList.contains("is-expanded");
        el.classList.toggle("is-expanded", expanded);
        btn.textContent = expanded ? "Detayı gizle" : "Detayı göster";
      });
      el.insertAdjacentElement("afterend", btn);
    });
  }

  function addActionFocusToPrimaryButtons() {
    const labels = ["kaydet", "oluştur", "yayınla", "görev", "onayla", "başlat", "güncelle", "devam"];
    Array.from(document.querySelectorAll("main a, main button")).forEach((el) => {
      if (el.closest(".bys360-ux1-quick-logic")) return;
      const text = normalizeText(el.innerText).toLowerCase();
      if (!text || text.length > 80) return;
      if (labels.some((label) => text.includes(label))) {
        el.classList.add("bys360-ux1-action-focus");
      }
    });
  }

  function init() {
    if (!document.body) return;
    document.documentElement.classList.add("bys360-ux1-enabled");
    removeGlobalQuickLogicCard();
    simplifyLongTextBlocks();
    addActionFocusToPrimaryButtons();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.BYS360UX1SimpleScreenGuide = {
    version: UX_VERSION,
    topBannerEnabled: false,
    removeGlobalQuickLogicCard,
    init,
    resolveContext,
    simplifyLongTextBlocks
  };
})();
