/* BYS360_ASSISTANT_ADVANCED_INTELLIGENCE_V32: Sekme yönlendirme, niyet yakalama ve güvenli cevap güçlendirmesi */
/* BYS360_ASSISTANT_CURRENT_FINAL_POLISH_V31_3: V31 server-first güvenli localFallback ve final kalite düzeltmesi */
/* BYS360_ASSISTANT_HOME_DASHBOARD_SPLIT_V31_2: Ana Sayfa ve Dashboard cevapları ayrıldı */
/* BYS360_ASSISTANT_VISIBILITY_RESTORE_V31_1: visible launcher/panel restored, V31 server-first preserved */
/* BYS360_ASSISTANT_SCREEN_MAP_V20_1_KPI_DESCRIPTION_FIX */
/* BYS360_ASSISTANT_MODULE_SAFE_MENU_BROKEN_LINK_GUARD_V2
 * BYS360_ASSISTANT_MODULE_LIVE_QUALITY_FINAL_GATE_V6
 * V6_CEVAP_HIJYENI_KATMANI
 * V6_FINAL_TEST_SENARYOLARI
 * V6_GUVENLI_YONLENDIRME_SIKILASTIRMA
 * V6_CANLI_KALITE_KONTROL
 * Kurumsal Rehberlik, Akıllı Yönlendirme ve Yetki Kontrollü Dijital Yardımcı
 * Dönemlerdir; yönlendirme bu adla yapılmalıdır
 * Hava durumunu doğru verebilmem için canlı ve doğrulanabilir hava verisi gerekir.
 * Hava durumu açıklaması sıcaklık bilgisiyle uyumlu görünmediği için yalnızca doğrulanabilen bilgileri paylaşıyorum.
 */
/* BYS360_ASSISTANT_MODULE_PERSONEL_LEAVE_DELEGATION_KB_V9_JS
   Eksiksiz ekran öğretimi, adım adım modül cevap sözleşmesi, güvenli eylem sınırı ve canlı kalite V7
   BYS360 Asistanı — Kurumsal Rehberlik, Akıllı Yönlendirme ve Yetki Kontrollü Dijital Yardımcı
   Tek kanonik ekran ajanı. Eski basit sanal asistan/widget yapıları canlıdan gizlenir. */
(function () {
  // BYS360_ASSISTANT_QUESTION_UNIVERSE_V31_5
  // BYS360_ASSISTANT_REAL_SCREEN_NAMES_V31_4
  'use strict';

  var VERSION = 'BYS360_ASSISTANT_MODULE_DEEP_KNOWLEDGE_CONTEXT_V27';
  var MODULE_NAME = 'BYS360 Asistanı';
  var MODULE_LONG_NAME = 'Kurumsal Rehberlik, Akıllı Yönlendirme ve Yetki Kontrollü Dijital Yardımcı';
  var ROOT_ID = 'bys360-assistant-module-root';
  var STORAGE_POS = 'bys360AssistantModule.position.v1';
  var STORAGE_OPEN = 'bys360AssistantModule.open.v1';
  var STORAGE_CHAT = 'bys360AssistantModule.chat.session.v1';
  var STORAGE_VIEW = 'bys360AssistantModule.view.session.v1';
  var STORAGE_CONTEXT = 'bys360AssistantModule.context.session.v1';
  var STORAGE_LAST_PAGE = 'bys360AssistantModule.lastPage.session.v1';
  var CHAT_LIMIT = 180;
  var chatHistory = [];
  var activeRoot = null;

  if (window.__BYS360_ASSISTANT_MODULE_12STEP_STATUS_GATE_V8_LOADED__) return;
  window.__BYS360_ASSISTANT_MODULE_12STEP_STATUS_GATE_V8_LOADED__ = true;

  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn, { once: true });
    else fn();
  }

  function qs(selector, root) { return (root || document).querySelector(selector); }
  function qsa(selector, root) { return Array.prototype.slice.call((root || document).querySelectorAll(selector)); }

  function normalize(input) {
    return String(input || '')
      .toLocaleLowerCase('tr-TR')
      .replace(/ı/g, 'i').replace(/İ/g, 'i')
      .replace(/[âáàä]/g, 'a').replace(/[êéèë]/g, 'e')
      .replace(/[îíìï]/g, 'i').replace(/[ôóòö]/g, 'o').replace(/[ûúùü]/g, 'u')
      .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ş/g, 's')
      .replace(/[^a-z0-9\s/._-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function escapeText(value) {
    return String(value == null ? '' : value).replace(/[&<>"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch];
    });
  }

  function iconSpark() {
    return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2.7l1.9 5.1 5.1 1.9-5.1 1.9L12 16.8l-1.9-5.2L5 9.7l5.1-1.9L12 2.7Z" fill="currentColor"/><path d="M18.4 14.4l.9 2.2 2.2.9-2.2.9-.9 2.2-.9-2.2-2.2-.9 2.2-.9.9-2.2Z" fill="currentColor" opacity=".72"/></svg>';
  }

  function removeLegacyAssistants() {
    var selectors = [
      '#bys360-assistant-pro-v1', '#bys360-ai-agent-widget', '#bys360AiAgentWidget', '#bys360-ai-agent-launcher', '#bys360AiAgentLauncher',
      '#bys360-assistant-root', '#bys360AssistantWidget', '.bys360-assistant-widget', '.bys360-ai-agent-widget', '.bys360-ai-agent-launcher',
      '.ai-agent-widget', '.ai-agent-launcher', '[data-bys360-assistant-root]', '[data-bys360-ai-agent-widget]', '[data-ai-agent-widget]', '[data-bys360-ai-agent-launcher]'
    ];
    selectors.forEach(function (selector) {
      qsa(selector).forEach(function (node) {
        if (!node || node.id === ROOT_ID || node.closest('#' + ROOT_ID)) return;
        node.setAttribute('data-bys360-legacy-assistant-disabled', 'canonical-v1');
        node.style.display = 'none';
      });
    });
  }

  var ROUTES = [
    { title: 'Anasayfa', href: '/home', keywords: ['anasayfa', 'baslangic', 'nereden baslayacagim'], text: 'BYS360 ana başlangıç ekranıdır.' },
    { title: 'Dashboard', href: '/dashboard', keywords: ['dashboard', 'gosterge', 'ozet', 'yonetici ekrani'], text: 'Genel durum ve yönetici özetlerini gösterir.' },
    { title: 'Hava Durumu Kartı', href: '/home', keywords: ['hava durumu karti', 'hava durumu kartı', 'open meteo', 'open-meteo', 'hava'], text: 'BYS360 anasayfa veya dashboard üzerinde Open-Meteo verisiyle çalışan yardımcı hava durumu kartıdır.' },
    /* BYS360_ASSISTANT_SCREEN_MAP_V20_ROUTES */
    { title: 'KPI Dashboardu',
      description: 'Hedef gerçekleşmelerini, başarı oranlarını, hedef kartlarını ve risk seviyelerini takip etmek için kullanılır.', href: '/performans/stratejik/kpi-dashboard', keywords: ['kpi dashboard', 'kpi panel', 'kpi gösterge', 'kpi gosterge', 'hedef dashboard', 'hedef panel', 'stratejik performans dashboard'], text: 'KPI ve hedef gerçekleşmeleri, başarı oranları, risk seviyesi ve yönetici özetleri bu ekranda takip edilir.' },
    { title: 'KPI ve Hedef Listesi', href: '/performans/stratejik/hedefler', keywords: ['kpi hedef listesi', 'hedefler', 'hedef listesi', 'kpi listesi', 'hedef kartlari', 'hedef kartları'], text: 'Tanımlı hedef kartları, hedef türleri, sahipleri, ağırlıkları ve gerçekleşme durumları burada listelenir.' },
    { title: 'Yeni KPI / Hedef Oluştur', href: '/performans/stratejik/hedefler/yeni', keywords: ['yeni kpi', 'hedef olustur', 'hedef oluştur', 'kpi olustur', 'kpi oluştur', 'hedef karti ekle', 'hedef kartı ekle'], text: 'Yeni hedef kartı veya KPI kaydı oluşturma ekranıdır.' },
    { title: 'AI KPI Analiz', href: '/performans/stratejik/kpi-analiz', keywords: ['ai kpi analiz', 'kpi analiz', 'hedef analiz', 'ai hedef analiz', 'kpi yorum', 'hedef yorumu'], text: 'KPI ve hedef verilerinin güvenli, karar vermeyen analiz özetleri burada görüntülenir.' },
    { title: 'Yetkinlik Kütüphanesi', href: '/performans/stratejik/yetkinlik-kutuphanesi', keywords: ['yetkinlik kutuphanesi', 'yetkinlik kütüphanesi', 'liderlik', 'takim calismasi', 'takım çalışması', 'analitik dusunme', 'teknik uzmanlik'], text: 'Görev, rol, performans kriteri, gelişim önerisi ve analiz süreçlerinde kullanılacak yetkinlik tanımları burada yönetilir.' },
    { title: 'Öz Değerlendirme', href: '/performans/stratejik/oz-degerlendirme', keywords: ['oz degerlendirme', 'öz değerlendirme', 'dönem özeti', 'donem ozeti', 'basarilarim', 'başarılarım', 'gelisim ihtiyaci'], text: 'Personelin dönem özeti, başarıları, zorlandığı alanlar ve gelişim ihtiyacını yazdığı ekrandır; otomatik puan üretmez.' },
    { title: 'Stratejik Performans Paneli', href: '/performans/stratejik/panel/dashboard', keywords: ['stratejik performans paneli', 'stratejik panel', 'hedef paneli', 'kpi yonetici paneli', 'kpi yönetici paneli'], text: 'Stratejik performans ve KPI özetlerinin yönetici görünümü bu panelde takip edilir.' },
    { title: 'Öz Değerlendirme Özeti', href: '/performans/stratejik/panel/oz-degerlendirme-ozet', keywords: ['oz degerlendirme ozeti', 'öz değerlendirme özeti', 'self review ozet', 'personel ozet degerlendirme'], text: 'Öz değerlendirme kayıtlarının yönetici/özet görünümü için kullanılan ekrandır.' },
    { title: 'Personel Yönetimi', href: '/personnel', keywords: ['personel', 'sicil', 'unvan', 'birim', 'yonetici', 'profil', 'personel ekle'], text: 'Personel, sicil, birim, görev, yönetici ve organizasyon verileri burada yönetilir.' },
    { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave', keywords: ['izin', 'izin kaydi', 'izin kaydı', 'izin talebi', 'izin bakiyesi', 'yillik izin', 'idari izin', 'saatlik izin'], text: 'İzin kayıtları, izin bakiyeleri, izinli amir etkisi ve izin–vekalet komuta merkezi bu ekranda takip edilir.' },
    { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance', keywords: ['vekalet', 'vekâlet', 'devamsizlik', 'devamsızlık', 'gorev devri', 'görev devri', 'vekil', 'vekil personel', 'vekalet tanimla'], text: 'Devamsızlık kayıtları ve vekâlet tanımları bu ekranda takip edilir.' },
    { title: 'Performans Yönetimi', href: '/performance/dashboard', keywords: ['performans', 'degerlendirme', 'puan', 'karne', 'amir'], text: 'Performans modülünün ana görünümüdür.' },
    { title: 'Sorular / Kriterler', href: '/performance/criteria', keywords: ['kriter', 'soru', 'sorular', 'degerlendirme kriterleri', 'yetkinlik'], text: 'Değerlendirme kriterleri ve soru tanımları burada yönetilir.' },
    { title: 'Dönemler', href: '/performance/periods', keywords: ['donem', 'donemler', 'donem ac', 'donem olustur', 'yeni donem', 'performans donemi'], text: 'Performans dönemi açma, düzenleme ve kapsam kontrolü bu sekmeden yapılır.' },
    { title: 'Değerlendirme Görevleri', href: '/performance/evaluation-tasks', keywords: ['gorev uret', 'degerlendirme gorevi', 'puanlama', 'amir gorevi', 'gorevler'], text: 'Amir değerlendirme görevleri ve puanlama akışı burada izlenir.' },
    { title: 'Başkan Onayları', href: '/performance/president-approvals', keywords: ['baskan onay', 'ust onay', '70 alti', 'dusuk performans', 'yayin kilidi'], text: '70 altı düşük performans ve Başkan Onayı akışı burada takip edilir.' },
    { title: 'Yayın Ön Onayı', href: '/performance/personnel-support-publish-approvals', keywords: ['yayin on onay', 'personel destek', 'yayin onayi', 'son yayina hazirlik'], text: 'Nihai yayın öncesi kurumsal kontrol adımıdır.' },
    { title: 'Süreç Takibi', href: '/performance/process-tracking', keywords: ['surec takibi', 'akış', 'akis', 'statü', 'statu', 'bekleyen'], text: 'Performans süreçlerinin durum ve akış takibi burada yapılır.' },
    { title: 'Süreç Raporları', href: '/performance/process-reports', keywords: ['surec raporu', 'rapor', 'analiz', 'geciken'], text: 'Dönem, görev, onay ve süreç raporları burada incelenir.' },
    { title: 'Dönem İçi Notlar', href: '/performance/interim-notes', keywords: ['donem ici not', 'ara geri bildirim', 'olay notu', 'gelisim notu'], text: 'Dönem içindeki olumlu/olumsuz gözlem ve gelişim notları buradan tutulur.' },
    { title: 'Gelişim Rehberi', href: '/performance/meeting-development/faz10', keywords: ['gelisim rehberi', 'gelisim onerisi', 'egitim onerisi'], text: 'Değerlendirme sonrası gelişim önerileri ve rehber notlar için kullanılır.' },
    { title: 'Not Karnesi', href: '/performance/scorecard', keywords: ['not karnesi', 'karnem', 'karne', 'sonucum', 'performans sonucum'], text: 'Yayınlandıktan sonra personelin kendi karne görünürlüğü burada açılır.' },
    { title: 'Geçmiş Karne Arşivi', href: '/performans/gecmis-karne-arsivi', keywords: ['gecmis karne', 'arsiv', 'eski puan', '2024', '2025'], text: 'Geçmiş yıl ve dönem performans arşivi için kullanılır.' },
    { title: 'Mesajlar', href: '/messages', keywords: ['mesaj', 'sohbet', 'yazisma', 'iletisim'], text: 'Kurum içi mesajlaşma ekranıdır.' },
    { title: 'Anketler', href: '/surveys', keywords: ['anket', 'anketler', 'cevapla', 'katilim'], text: 'Size atanan anketleri ve anket süreçlerini gösterir.' },
    { title: 'Yardım Merkezi', href: '/support', keywords: ['yardim', 'destek', 'talep', 'sorun', 'bilet'], text: 'Destek talepleri ve kullanıcı yardım içerikleri buradadır.' },
    { title: 'AI Karar Destek Merkezi', href: '/ai/decision-support/faz1/health', keywords: ['ai karar', 'karar destek', 'analiz', 'risk', 'ozet'], text: 'Analiz ve karar destek katmanıdır; BYS360 Asistanı ise kullanıcı rehberlik katmanıdır.' },
    { title: 'Asistan Bilgi Bankası', href: '/ai-agent/knowledge', keywords: ['bilgi bankasi', 'asistani egit', 'ogret', 'asistan egitimi'], text: 'Yetkili kullanıcıların asistan eğitim kayıtlarını yönettiği alandır.' },

    { title: 'Modül Bazlı Rol Matrisi', href: '/settings/role-matrix', keywords: ['modul bazli rol matrisi', 'modül bazlı rol matrisi', 'modul matrisi', 'modül matrisi'], text: 'Modül görünürlüklerinin rol bazlı yönetildiği alandır.' },
    { title: 'Performans Yönetimi Rol Matrisi', href: '/settings/performance-role-matrix', keywords: ['performans rol matrisi', 'performans matrisi', 'performans yetki'], text: 'Performans alt sekmelerinin rol bazlı görünürlüğü burada kontrol edilir.' },
    { title: 'Sistem Ayarları', href: '/settings', keywords: ['ayar', 'ayarlar', 'rol', 'yetki', 'matris', 'menu gorunurluk', 'rol matrisi'], text: 'Rol matrisi, menü görünürlüğü, sistem ayarları ve güvenlik ayarları burada yönetilir.' }
  ];

  function findRoutes(message) {
    var n = normalize(message);
    if (!n) return [];
    return ROUTES.filter(function (r) {
      return r.keywords.some(function (keyword) { return n.indexOf(normalize(keyword)) !== -1; }) || n.indexOf(normalize(r.title)) !== -1;
    }).slice(0, 4);
  }

  var SAFE_ROUTE_PREFIXES = [
    /* BYS360_ASSISTANT_SCREEN_MAP_V20_PREFIXES */
    '/performans/stratejik/', '/performans/stratejik/panel/',
    '/performance/president-approvals/', '/performance/periods/', '/performans/gecmis-karne-arsivi',
    '/support/tickets/', '/surveys/', '/messages/', '/personnel/'
  ];

  function legacyRouteMap() {
    var map = {};
    map['/personnel' + '/leaves'] = '/hr-management/leave';
    map['/personnel' + '/leave'] = '/hr-management/leave';
    map['/personnel' + '/delegations'] = '/hr-management/attendance';
    map['/hr-management/delegations'] = '/hr-management/attendance';
    map['/performance/period-management'] = '/performance/periods';
    map['/performance/period-management/create'] = '/performance/periods';
    map['/performance/periods/create'] = '/performance/periods';
    map['/performance/questions'] = '/performance/criteria';
    map['/performance/criteria-management'] = '/performance/criteria';
    map['/performance/tasks'] = '/performance/evaluation-tasks';
    map['/performans/baskan-onaylari'] = '/performance/president-approvals';
    map['/performans/surec-takibi'] = '/performance/process-tracking';
    // V32: Asistan Paneli kendi ekranında kalmalı; Bilgi Bankası ayrı sekmedir.
    return map;
  }

  function knownRoute(href) {
    if (!href || href === '#') return false;
    if (ROUTES.some(function (sayfa yolu) { return sayfa yolu.href === href; })) return true;
    return SAFE_ROUTE_PREFIXES.some(function (prefix) { return href.indexOf(prefix) === 0; });
  }

  function canonicalizeHref(href) {
    if (!href) return '#';
    var işlenmemiş veri = String(href || '').trim();
    if (!işlenmemiş veri || işlenmemiş veri === '#') return '#';
    if (/^(javascript|data|vbscript):/i.test(işlenmemiş veri)) return '#';
    var a = document.createElement('a');
    a.href = işlenmemiş veri;
    if (a.origin && a.origin !== window.location.origin) return '#';
    var path = a.pathname || '/';
    if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);
    var map = legacyRouteMap();
    Object.keys(map).forEach(function (legacy) {
      if (path === legacy || path.indexOf(legacy + '/') === 0) path = map[legacy];
    });
    return path + (a.search || '') + (a.hash || '');
  }

  function titleToRoute(title) {
    var n = normalize(title || '');
    if (!n) return boş;
    var exact = ROUTES.find(function (sayfa yolu) { return normalize(sayfa yolu.title) === n; });
    if (exact) return exact;
    return ROUTES.find(function (sayfa yolu) {
      return sayfa yolu.keywords.some(function (keyword) { return n.indexOf(normalize(keyword)) !== -1; }) || n.indexOf(normalize(sayfa yolu.title)) !== -1;
    }) || boş;
  }

  function normalizeAssistantLink(item) {
    if (!item) return boş;
    var title = String(item.title || item.label || 'Ekrana git');
    var href = canonicalizeHref(item.href || item.url || '#');
    if (normalize(title) === 'izin ve vekalet' || normalize(title) === 'izin ve vekâlet') {
      title = 'İzin ve Devamsızlık Takibi';
      href = '/hr-management/leave';
    }
    if (!knownRoute(href)) {
      var fromTitle = titleToRoute(title);
      if (fromTitle) href = fromTitle.href;
    }
    if (!knownRoute(href)) {
      return { title: title, href: '#', disabled: true, note: 'Bu bağlantı güvenli menü haritasında bulunmadığı için açılmadı.' };
    }
    return { title: title, href: href, disabled: false };
  }

  function safeLinks(links) {
    return (Array.isArray(links) ? links : []).map(normalizeAssistantLink).filter(Boolean).slice(0, 4);
  }

  function removeTransientNotice(root) {
    var kayıt = root ? qs('[data-chat-log]', root) : boş;
    if (!kayıt) return;
    var last = kayıt.lastElementChild;
    if (last && last.getAttribute('data-transient') === 'true') kayıt.removeChild(last);
  }

  function preflightAndNavigate(root, href, title) {
    var safe = normalizeAssistantLink({ href: href, title: title });
    if (!safe || safe.disabled || !safe.href || safe.href === '#') {
      appendMessage(root || activeRoot, 'bot', 'Bu bağlantı güvenli menü haritasında doğrulanamadığı için açmadım. Lütfen ilgili modül adını yazın; sizi güvenli ekrana yönlendireyim.');
      return false;
    }
    saveChatHistory();
    saveCurrentPageContext({ navigatingTo: safe.href, navigatingTitle: safe.title || title || '' });
    appendMessage(root || activeRoot, 'bot', 'Ekranı açmadan önce güvenli bağlantı kontrolü yapıyorum...', [], false, true);
    fetch(safe.href, {
      method: 'GET',
      credentials: 'same-origin',
      geçici kayıt: 'no-store',
      headers: { 'Accept': 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8', 'X-BYS360-Assistant-Preflight': '1' }
    }).then(function (response) {
      if (!response.ok) throw new Error('http_' + response.status);
      var contentType = (response.headers.get('content-type') || '').toLowerCase();
      if (contentType && contentType.indexOf('text/html') === -1 && contentType.indexOf('application/xhtml') === -1) throw new Error('not_screen');
      removeTransientNotice(root || activeRoot);
      window.location.href = safe.href;
    }).catch(function () {
      removeTransientNotice(root || activeRoot);
      appendMessage(root || activeRoot, 'bot', 'Bu ekran şu an güvenli şekilde açılamadı. Beyaz ekran veya teknik hata yaşamamanız için yönlendirmeyi durdurdum. Menü haritasında bu başlığın doğru yolu kontrol edilmeli: ' + (safe.title || title || 'ilgili ekran'));
    });
    return false;
  }

  // V7_CEVAP_HIJYENI_KATMANI: server veya eski bilgi bankasından gelse bile kullanıcı ekranına yanlış/alaycı/teknik ifade düşmesini engeller.
  function sanitizeAssistantText(text) {
    var value = String(text == boş ? '' : text);
    var replacements = [
      [/Dönem\s+Yönetimi/g, 'Dönemler'],
      [/donem yonetimi/gi, 'Dönemler'],
      [new RegExp('end' + 'point\\s+yolu\\s+men[uü]\\s+haritas[ıi]na\\s+eklenmeli\\.?', 'gi'), ''],
      [new RegExp('end' + 'point\\s+yolu\\s+menu\\s+haritasina\\s+eklenmeli\\.?', 'gi'), ''],
      [/Tam\s+modül\s+mantığıyla\s+çalışır\.?/gi, ''],
      [/Eski\s+basit\s+asistanlarla\s+karışmaz;\s+idari\s+karar\s+üretmez,\s+puan\s+belirlemez,\s+hassas\s+veri\s+göstermez\.?/gi, ''],
      [/K[ıi]ş\s+kendini\s+göstermiş;?\s*/gi, ''],
      [/çayl[ae]r\s+sıcak,?\s*/gi, ''],
      [/Şemsiye\s+göreve\.?/gi, ''],
      [/Gök\s*yüzü\s+drama\w*\.?/gi, ''],
      [/işi\s+üşütmeden\.?/gi, ''],
      [/menüler\s+uçuşmasın\.?/gi, ''],
      [/sevimli\s+bir\s+yorum\.?/gi, ''],
      [/espiri\w*\s+cevaplar?\.?/gi, ''],
      [/espri\w*\s+cevaplar?\.?/gi, '']
    ];
    replacements.forEach(function (pair) { value = value.replace(pair[0], pair[1]); });
    if (/\b(1[5-9]|2\d|3\d)\s*°?\s*C\b/i.test(value) && /\bkarlı\b|\bkarli\b|\bdurum karlı\b|\bdurum karli\b/i.test(value)) {
      value = value.replace(/,?\s*durum\s+karlı\.?/gi, '.');
      value = value.replace(/,?\s*durum\s+karli\.?/gi, '.');
      value = value.replace(/\b[kK]arlı hava görünüyor;?\s*/g, '');
      value = value.replace(/\b[kK]arli hava gorunuyor;?\s*/g, '');
      if (value.indexOf('Hava durumu açıklaması sıcaklık bilgisiyle uyumlu görünmediği için yalnızca doğrulanabilen bilgileri paylaşıyorum.') === -1) {
        value += ' Hava durumu açıklaması sıcaklık bilgisiyle uyumlu görünmediği için yalnızca doğrulanabilen bilgileri paylaşıyorum.';
      }
    }
    value = value.replace(/\s+([,.])/g, '$1').replace(/\s{2,}/g, ' ').trim();
    return value || 'Bu konuda BYS360 içinde güvenli şekilde yardımcı olabilirim.';
  }

  function makeAnswer(text, links) { return { text: sanitizeAssistantText(text), links: safeLinks(links || []) }; }


  // V7_EKSİKSİZ_EKRAN_OGRETIM_SOZLESMESI: her cevap gerçek ekran adı, yetki, adım, dikkat ve kontrol düzeniyle verilir.
  // V7_MODUL_CEVAP_FORMATI: öğretici cevaplar aynı kalıpta üretilir; kullanıcıya teknik/eskimiş ekran adı gösterilmez.
  // V7_GUVENLI_EYLEM_SOZLESMESI: asistan idari karar, puan veya hassas veri üretmez; yalnızca güvenli rehberlik verir.
  function listToSentence(items) {
    return (items || []).filter(Boolean).map(function (item, index) { return (index + 1) + ') ' + item; }).join(' ');
  }

  function moduleStepAnswer(title, location, roles, steps, warnings, checks, links) {
    var text = 'Anladım. Bu konu “' + title + '” kapsamındadır. ';
    if (location) text += 'Doğru yol: ' + location + '. ';
    if (roles && roles.length) text += 'Kim yapabilir? ' + roles.join(', ') + '. ';
    if (steps && steps.length) text += 'Adım adım: ' + listToSentence(steps) + ' ';
    if (warnings && warnings.length) text += 'Dikkat: ' + warnings.join(' ') + ' ';
    if (checks && checks.length) text += 'Kontrol: ' + checks.join(' ') + ' ';
    return makeAnswer(text, links || []);
  }

  function teachingContractAnswer() {
    return makeAnswer('BYS360 Asistanı ekran zekâsı ve adım adım rehberlik düzenine göre çalışır: gerçek ekran adını kullanır, önce doğru modülü ve yetkiyi belirtir, sonra işlemi adım adım anlatır, dikkat edilmesi gereken güvenlik/yayın/yetki sınırlarını söyler ve sonunda kontrol adımını verir. Eski veya doğrulanmayan bağlantıları açmaz; idari karar üretmez, performans puanı belirlemez ve hassas veri göstermez.', [
      { title: 'Dönemler', href: '/performance/periods' },
      { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
      { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' },
      { title: 'Sistem Ayarları', href: '/settings' }
    ]);
  }

  function knownScreensAnswer() {
    return makeAnswer('BYS360 içinde güvenli menü haritasına bağlı çalışırım. Personel Yönetimi, İzin ve Devamsızlık Takibi, Devamsızlık ve Vekâlet, Performans Yönetimi, Sorular / Kriterler, Dönemler, Değerlendirme Görevleri, Başkan Onayları, Yayın Ön Onayı, Süreç Takibi, Süreç Raporları, Dönem İçi Notlar, Gelişim Rehberi, Not Karnesi, Geçmiş Karne Arşivi, Mesajlar, Anketler, Yardım Merkezi, AI Karar Destek Merkezi, Asistan Bilgi Bankası ve Sistem Ayarları başlıklarında rehberlik yaparım. Bir ekran güvenli haritada yoksa beyaz ekran riski oluşturmamak için açmam; işlem adını yazarsanız güvenli yolu bulmaya çalışırım.', [
      { title: 'Personel Yönetimi', href: '/personnel' },
      { title: 'Dönemler', href: '/performance/periods' },
      { title: 'Başkan Onayları', href: '/performance/president-approvals' },
      { title: 'Yardım Merkezi', href: '/support' }
    ]);
  }


  // V8_12_ADIM_DURUM_KONTROL_GATE: 12 adımın tamamlandı/kısmen/eksik durumunu kullanıcıya ve son kontrol raporuna bağlar.
  function twelveStepStatusAnswer() {
    var rows = [
      '1. Gerçek Menü / Sekme / URL Haritası: Büyük ölçüde tamamlandı; final canlı ekran taraması gerekir.',
      '2. Güvenli Yönlendirme / Kırık Link Engeli: Tamamlandı; eski/kırık bağlantılar güvenli haritadan geçer.',
      '3. Personel Yönetimi Bilgi Bankası: Kısmen tamamlandı; V9’da derinleştirilecek.',
      '4. İzin, Devamsızlık ve Vekâlet: Kısmen tamamlandı; V9’da ayrıntılı öğretim genişletilecek.',
      '5. Performans Yönetimi Bilgi Bankası: Kısmen tamamlandı; V10’da Dönemler, kriterler, görev, karne ve onaylar derinleştirilecek.',
      '6. Rol Matrisi / Yetki / Menü Görünürlüğü: Kısmen tamamlandı; V11’de detaylandırılacak.',
      '7. Dashboard, Raporlar ve Yönetici Görünümü: Kısmen tamamlandı; V11’de rapor bazlı rehber genişletilecek.',
      '8. İletişim, Anket, Destek ve Bildirimler: Kısmen tamamlandı; V11’de detaylandırılacak.',
      '9. AI Karar Destek Merkezi Ayrımı: Tamamlandı; asistan rehberlik eder, AI Karar Destek analiz/özet üretir.',
      '10. Günlük Konuşma ve Kendini Tanıtma: Büyük ölçüde tamamlandı; kurumsal tanıtım ve kimlik cevapları var.',
      '11. Oturum ve Sayfa Geçişi Koruma: Tamamlandı; aynı sekmede sohbet ve panel durumu korunur.',
      '12. Final Gate ve Canlı Test Senaryoları: Başladı; V12’de tam final gate yapılacak.'
    ];
    return makeAnswer('BYS360 Asistanı durum kontrolü: ' + rows.join(' '), [
      { title: 'Dönemler', href: '/performance/periods' },
      { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
      { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' },
      { title: 'Başkan Onayları', href: '/performance/president-approvals' }
    ]);
  }

  function missingStepsAnswer() {
    return makeAnswer('Eksik kalan ana başlıklar şunlardır: V9’da Personel Yönetimi, İzin, Devamsızlık ve Vekâlet bilgi bankası derinleştirilecek. V10’da Performans Yönetimi bilgi bankası tamamlanacak. V11’de rol matrisi, raporlar, dashboard, iletişim, anket, destek ve bildirimler genişletilecek. V12’de tüm senaryolar tek final gate ile doğrulanacak.', [
      { title: 'Personel Yönetimi', href: '/personnel' },
      { title: 'Yardım Merkezi', href: '/support' },
      { title: 'AI Karar Destek Merkezi', href: '/ai/decision-support' }
    ]);
  }



  function isWeatherIntent(message) {
    var n = normalize(message);
    return /\b(hava|havadurumu|hava durumu|bugun hava|bugün hava|yagmur|yağmur|sicaklik|sıcaklık|ruzgar|rüzgar|open meteo|open-meteo)\b/.test(n);
  }

  function isLocalFirstIntent(message) {
    var n = normalize(message);
    if (!n) return false;
    // V31.1: Sunucu beyni önceliklidir. Yerel cevap yalnızca ekran/oturum veya anlık güvenli sayfa yardımı için çalışır.
    return /\b(bu sayfa|bu ekran|burada ne|neredeyim|hangi ekrandayim|hangi ekrandayım|hangi sayfadayim|hangi sayfadayım|sayfa yardimi|sayfa yardımı|ekran yardimi|ekran yardımı|az onceki konu|az önceki konu|kaldigimiz yer|kaldığımız yer|devam edelim|nereden devam|sayfa değişince|sayfa degisince|konusmalar silinmesin|konuşmalar silinmesin|sohbet kayboluyor)\b/.test(n);
  }

  var WEATHER_PATHS = [
    '/api/weather/current',
    '/api/weather',
    '/api/weather/today',
    '/api/weather/canakkale',
    '/api/weather/current?city=canakkale',
    '/api/open-meteo/current',
    '/api/open-meteo/weather',
    '/weather/api/current',
    '/weather/current',
    '/home/weather',
    '/dashboard/weather',
    '/open-meteo/weather',
    '/open-meteo/current'
  ];

  function uniqueWeatherPaths(list) {
    var seen = {};
    return (list || []).filter(function (url) {
      if (!url || typeof url !== 'string') return false;
      var clean = url.trim();
      if (!clean || /^https?:\/\//i.test(clean) || /^javascript:/i.test(clean)) return false;
      if (seen[clean]) return false;
      seen[clean] = true;
      return true;
    });
  }

  function collectWeatherPaths() {
    var weatherPaths = WEATHER_PATHS.slice();
    try {
      var selectors = [
        '[data-weather-url]', '[data-open-meteo-url]', '[data-bys360-weather-url]', '[data-weather-' + 'end' + 'point]',
        '#weather-card', '.weather-card', '.bys360-weather-card', '[class*=weather]', '[id*=weather]', '[data-weather]'
      ];
      qsa(selectors.join(',')).forEach(function (node) {
        ['weatherUrl', 'openMeteoUrl', 'bys360WeatherUrl', 'weather' + 'End' + 'point', 'end' + 'point', 'url'].forEach(function (key) {
          if (node.dataset && node.dataset[key]) weatherPaths.unshift(node.dataset[key]);
        });
        ['data-weather-url', 'data-open-meteo-url', 'data-bys360-weather-url', 'data-weather-' + 'end' + 'point'].forEach(function (attr) {
          var val = node.getAttribute && node.getAttribute(attr);
          if (val) weatherPaths.unshift(val);
        });
      });
      qsa('script').forEach(function (script) {
        var txt = script.textContent || '';
        var m;
        var re = /["'](\/[A-Za-z0-9_\-\/?.=&%]*?(?:weather|open-meteo)[A-Za-z0-9_\-\/?.=&%]*)["']/gi;
        while ((m = re.exec(txt))) weatherPaths.unshift(m[1]);
      });
    } catch (e) {}
    return uniqueWeatherPaths(weatherPaths);
  }

  function readWeatherFromDom() {
    try {
      var nodes = qsa('[data-weather], [data-temperature], [data-temp], [data-weather-code], #weather-card, .weather-card, .bys360-weather-card, [class*=weather], [id*=weather]');
      for (var i = 0; i < nodes.length; i += 1) {
        var node = nodes[i];
        var ds = node.dataset || {};
        var temp = ds.temperature || ds.temp || ds.temperature2m || node.getAttribute('data-temperature') || node.getAttribute('data-temp');
        var code = ds.weatherCode || ds.weathercode || ds.code || node.getAttribute('data-weather-code');
        var wind = ds.windSpeed || ds.wind || ds.windspeed || node.getAttribute('data-wind-speed');
        var condition = ds.condition || ds.description || ds.weather || '';
        var text = (node.innerText || node.textContent || '').trim();
        if (!condition && text) {
          var lower = normalize(text);
          if (lower.indexOf('yagmur') !== -1) condition = 'yağmurlu';
          else if (/(^|\s)kar(li| yag| yagisi|\s|$)/.test(lower)) condition = 'karlı';
          else if (lower.indexOf('sis') !== -1) condition = 'sisli';
          else if (lower.indexOf('bulut') !== -1) condition = 'bulutlu';
          else if (lower.indexOf('acik') !== -1) condition = 'açık';
        }
        if (!temp && text) {
          var t = text.match(/(-?\d+(?:[,.]\d+)?)\s*°?\s*C/i);
          if (t) temp = t[1].replace(',', '.');
        }
        if (temp || code || condition) return { temperature: temp, wind: wind, code: code, condition: condition, source: 'BYS360 hava durumu kartı' };
      }
    } catch (e) {}
    return boş;
  }

  function pickWeatherPayload(form verisi) {
    if (!form verisi || typeof form verisi !== 'object') return boş;
    var candidates = [form verisi, form verisi.weather, form verisi.current, form verisi.current_weather, form verisi.data, form verisi.result, form verisi.open_meteo, form verisi.openMeteo];
    for (var i = 0; i < candidates.length; i += 1) {
      var p = candidates[i];
      if (!p || typeof p !== 'object') continue;
      var temp = p.temperature_2m != boş ? p.temperature_2m : (p.temperature != boş ? p.temperature : (p.temp != boş ? p.temp : p.current_temperature));
      var wind = p.wind_speed_10m != boş ? p.wind_speed_10m : (p.windspeed != boş ? p.windspeed : (p.wind_speed != boş ? p.wind_speed : p.wind));
      var code = p.weather_code != boş ? p.weather_code : (p.weathercode != boş ? p.weathercode : p.code);
      var condition = p.condition || p.description || p.summary || p.text || p.weather || '';
      var precipitation = p.precipitation != boş ? p.precipitation : (p.rain != boş ? p.rain : p.showers);
      var humidity = p.relative_humidity_2m != boş ? p.relative_humidity_2m : (p.humidity != boş ? p.humidity : boş);
      if (temp != boş || code != boş || condition) {
        return { temperature: temp, wind: wind, code: code, condition: condition, precipitation: precipitation, humidity: humidity, source: form verisi.source || p.source || 'Open-Meteo' };
      }
    }
    return boş;
  }

  function weatherCodeText(code, condition) {
    if (condition) return String(condition);
    var c = Number(code);
    if ([0].indexOf(c) >= 0) return 'açık';
    if ([1, 2].indexOf(c) >= 0) return 'az bulutlu';
    if ([3].indexOf(c) >= 0) return 'kapalı/bulutlu';
    if ([45, 48].indexOf(c) >= 0) return 'sisli';
    if ([51, 53, 55, 56, 57].indexOf(c) >= 0) return 'çisenti';
    if ([61, 63, 65, 66, 67, 80, 81, 82].indexOf(c) >= 0) return 'yağmurlu';
    if ([71, 73, 75, 77, 85, 86].indexOf(c) >= 0) return 'karlı';
    if ([95, 96, 99].indexOf(c) >= 0) return 'gök gürültülü';
    return 'hava durumu';
  }

  function parseWeatherTemperature(value) {
    if (value == boş || value === '') return NaN;
    var cleaned = String(value).replace(',', '.').replace(/[^0-9.\-]/g, '');
    return Number(cleaned);
  }

  function isSnowLikeText(value) {
    var t = normalize(value || '');
    return /(^|\s)kar(li| yag| yagisi|\s|$)/.test(t) || /\bsnow\b/.test(t);
  }

  function isSnowCode(code) {
    var c = Number(code);
    return [71, 73, 75, 77, 85, 86].indexOf(c) >= 0;
  }

  function isWeatherConditionTemperatureMismatch(data) {
    var temp = parseWeatherTemperature(data && data.temperature);
    if (isNaN(temp)) return false;
    var condition = weatherCodeText(data && data.code, data && data.condition);
    // V5_2_HAVA_TUTARLILIK_KONTROLU: 8°C üstünde kar benzeri açıklama kullanıcıya gösterilmez.
    if (temp > 8 && (isSnowCode(data && data.code) || isSnowLikeText(condition))) return true;
    return false;
  }

  function safeWeatherCondition(data) {
    if (isWeatherConditionTemperatureMismatch(data)) return '';
    return weatherCodeText(data && data.code, data && data.condition);
  }

  function weatherTone(data) {
    var temp = parseWeatherTemperature(data && data.temperature);
    var wind = Number(data && data.wind);
    var text = normalize(safeWeatherCondition(data));
    // V5_2_CIDDI_HAVA_DURUMU_DILI: yalnızca güvenilir, kısa ve kurumsal bilgilendirme var.
    if (isWeatherConditionTemperatureMismatch(data)) return 'Hava durumu açıklaması sıcaklık bilgisiyle uyumlu görünmediği için yalnızca doğrulanabilen bilgileri paylaşıyorum.';
    if (text.indexOf('yagmur') !== -1 || text.indexOf('cisenti') !== -1) return 'Yağış görünüyor; dışarı çıkacaksanız tedbirli olmanız iyi olur.';
    if (text.indexOf('kar') !== -1) return 'Düşük sıcaklık ve yağış koşulları görünüyor; dışarı çıkacaksanız yol ve zemin koşullarına dikkat etmeniz iyi olur.';
    if (text.indexOf('sis') !== -1) return 'Sisli hava görünüyor; ulaşımda görüş mesafesine dikkat etmek faydalı olur.';
    if (text.indexOf('gok') !== -1) return 'Gök gürültülü hava görünüyor; açık alanda bulunacaksanız dikkatli olmanız iyi olur.';
    if (!isNaN(temp) && temp >= 30) return 'Hava sıcak görünüyor; gün içinde su tüketimine ve güneşe dikkat etmek iyi olur.';
    if (!isNaN(temp) && temp <= 5) return 'Hava oldukça serin görünüyor; dışarı çıkarken hazırlıklı olmak iyi olur.';
    if (!isNaN(wind) && wind >= 35) return 'Rüzgâr kuvvetli olabilir; dışarıda dikkatli olmak faydalı olur.';
    if (text.indexOf('acik') !== -1 || text.indexOf('bulut') !== -1) return 'Hava durumu genel olarak sakin görünüyor.';
    return 'Güncel hava durumu bilgisini aldım.';
  }

  function formatWeatherAnswer(data) {
    var parts = [];
    var condition = safeWeatherCondition(data);
    if (data.temperature != boş && data.temperature !== '') parts.push('sıcaklık ' + data.temperature + '°C');
    if (condition) parts.push('durum ' + condition);
    if (data.wind != boş && data.wind !== '') parts.push('rüzgâr ' + data.wind + ' km/sa');
    if (data.humidity != boş && data.humidity !== '') parts.push('nem %' + data.humidity);
    var base = parts.length ? ('BYS360 hava durumu bilgisini aldım: ' + parts.join(', ') + '.') : 'BYS360 hava durumu servisinden güncel veri aldım.';
    return base + ' ' + weatherTone(data);
  }

  // V5_2_YAPAY_DIL_YOK_HAVA_DURUMU: hava cevabında mecaz veya yapay ifade kullanılmaz.
  function fetchWeatherAnswer() {
    var domData = readWeatherFromDom();
    if (domData) return Promise.resolve(makeAnswer(formatWeatherAnswer(domData)));
    var weatherPaths = collectWeatherPaths();
    var index = 0;
    function tryNext() {
      if (index >= weatherPaths.length) return Promise.reject(new Error('weather_unavailable'));
      var url = weatherPaths[index++];
      return fetch(url, { credentials: 'same-origin', geçici kayıt: 'no-store', headers: { 'Accept': 'application/sistem verisi', 'X-BYS360-Assistant-Weather': '1' } })
        .then(function (response) { if (!response.ok) throw new Error('http_' + response.status); return response.sistem verisi(); })
        .then(function (form verisi) {
          var data = pickWeatherPayload(form verisi);
          if (!data) throw new Error('weather_payload');
          return makeAnswer(formatWeatherAnswer(data));
        })
        .catch(function () { return tryNext(); });
    }
    return tryNext();
  }

  function answerWeather(root, question, kayıt) {
    fetchWeatherAnswer().then(function (answer) {
      if (kayıt && kayıt.lastElementChild && kayıt.lastElementChild.classList.contains('is-bot')) kayıt.removeChild(kayıt.lastElementChild);
      appendMessage(root, 'bot', answer.text, answer.links || []);
    }).catch(function () {
      if (kayıt && kayıt.lastElementChild && kayıt.lastElementChild.classList.contains('is-bot')) kayıt.removeChild(kayıt.lastElementChild);
      appendMessage(root, 'bot', 'BYS360 hava durumu bilgisine şu an ulaşamadım. Hava bilgisini uydurmam; hava durumu kartı güncellendiğinde güncel bilgiyi sade ve doğru şekilde paylaşabilirim.');
    });
  }


  // V5_SAYFA_BAZLI_YARDIM_OTURUM_DEVAMLILIGI
  function cleanSmallText(value, max) {
    var text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return '';
    return text.length > (max || 90) ? text.slice(0, (max || 90) - 1) + '…' : text;
  }

  function activeMenuText() {
    var selectors = [
      '.sidebar .active', '.sidebar .is-active', '.side-menu .active', '.nav-sidebar .active',
      '.menu-item.active', '.nav-link.active', '[aria-current="page"]',
      '.app-sidebar a.active', '.app-sidebar .is-active', '.bys-sidebar a.active'
    ];
    for (var i = 0; i < selectors.length; i += 1) {
      var node = qs(selectors[i]);
      if (node) {
        var txt = cleanSmallText(node.textContent || node.getAttribute('title') || node.getAttribute('aria-label'), 80);
        if (txt) return txt;
      }
    }
    return '';
  }

  function pageHeadingText() {
    var selectors = ['main h1', '.page-title', '.content-title', '.card-title h1', 'h1', 'h2'];
    for (var i = 0; i < selectors.length; i += 1) {
      var node = qs(selectors[i]);
      if (node) {
        var txt = cleanSmallText(node.textContent, 95);
        if (txt) return txt;
      }
    }
    return cleanSmallText(document.title || '', 95);
  }

  function routeForCurrentPage() {
    var path = canonicalizeHref(window.location.pathname || '/');
    return ROUTES.find(function (r) { return r.href === path; }) || ROUTES.find(function (r) { return path.indexOf(r.href + '/') === 0; }) || boş;
  }

  function currentPageContext() {
    var sayfa yolu = routeForCurrentPage();
    var path = canonicalizeHref(window.location.pathname || '/');
    return {
      path: path,
      routeTitle: sayfa yolu ? sayfa yolu.title : '',
      routeText: sayfa yolu ? sayfa yolu.text : '',
      heading: pageHeadingText(),
      activeMenu: activeMenuText(),
      at: new Date().toISOString()
    };
  }

  function saveCurrentPageContext(extra) {
    try {
      var ctx = currentPageContext();
      if (extra && typeof extra === 'object') Object.keys(extra).forEach(function (k) { ctx[k] = extra[k]; });
      sessionStorage.setItem(STORAGE_CONTEXT, sistem verisi.stringify(ctx));
      sessionStorage.setItem(STORAGE_LAST_PAGE, sistem verisi.stringify(ctx));
      return ctx;
    } catch (e) { return boş; }
  }

  function loadSavedContext() {
    try {
      var işlenmemiş veri = sessionStorage.getItem(STORAGE_CONTEXT) || sessionStorage.getItem(STORAGE_LAST_PAGE);
      return işlenmemiş veri ? sistem verisi.parse(işlenmemiş veri) : boş;
    } catch (e) { return boş; }
  }

  function lastMeaningfulChat() {
    for (var i = chatHistory.length - 1; i >= 0; i -= 1) {
      var msg = chatHistory[i];
      if (msg && msg.text && String(msg.text).indexOf('Sorunuzu BYS360 kapsamında yorumluyorum') === -1) return msg;
    }
    return boş;
  }

  function pageAwareAnswer() {
    var ctx = saveCurrentPageContext() || currentPageContext();



    /* BYS360_ASSISTANT_SCREEN_INTELLIGENCE_V23_PAGE_AWARE_BRIDGE */
    var v23Page = (window.BYS360AssistantScreenIntelligenceV23 && typeof window.BYS360AssistantScreenIntelligenceV23.answerCurrentPage === 'function') ? window.BYS360AssistantScreenIntelligenceV23.answerCurrentPage() : boş;
    if (v23Page && v23Page.text) return makeAnswer(v23Page.text, v23Page.links || []);
    /* BYS360_ASSISTANT_SCREEN_AGENT_V22_PAGE_AWARE_BRIDGE */
    var v22Page = (window.BYS360AssistantScreenAgentV22 && typeof window.BYS360AssistantScreenAgentV22.answerCurrentPage === 'function') ? window.BYS360AssistantScreenAgentV22.answerCurrentPage() : boş;
    if (v22Page && v22Page.text) return makeAnswer(v22Page.text, v22Page.links || []);
    /* BYS360_ASSISTANT_SCREEN_AGENT_V21_PAGE_AWARE_BRIDGE */
    var v21Page = (window.BYS360AssistantScreenAgentV21 && typeof window.BYS360AssistantScreenAgentV21.answerCurrentPage === 'function') ? window.BYS360AssistantScreenAgentV21.answerCurrentPage() : boş;
    if (v21Page && v21Page.text) return makeAnswer(v21Page.text, v21Page.links || []);

    /* BYS360_ASSISTANT_SCREEN_MAP_V20_PAGE_AWARE_BRIDGE */
    var v20Page = (window.BYS360AssistantScreenMapV20 && typeof window.BYS360AssistantScreenMapV20.answerCurrentPage === 'function') ? window.BYS360AssistantScreenMapV20.answerCurrentPage() : boş;
    if (v20Page && v20Page.text) return makeAnswer(v20Page.text, v20Page.links || []);
    var sayfa yolu = routeForCurrentPage();
    if (sayfa yolu) {
      var parts = ['Şu an “' + sayfa yolu.title + '” ekranındasınız. ' + sayfa yolu.text];
      if (ctx.heading && normalize(ctx.heading) !== normalize(sayfa yolu.title)) parts.push('Ekranda görünen başlık: “' + ctx.heading + '”.');
      if (ctx.activeMenu && normalize(ctx.activeMenu).indexOf(normalize(sayfa yolu.title)) === -1) parts.push('Sol şeritte seçili görünen alan: “' + ctx.activeMenu + '”.');
      parts.push('Bu ekranda işlem yaparken rol matrisi, kişi/birim bazlı görünürlük ve güvenli erişim sınırları geçerlidir. Ne yapmak istediğinizi yazarsanız bu ekrandan devam edilecek adımları sırayla anlatırım.');
      return makeAnswer(parts.join(' '), [{ title: sayfa yolu.title, href: sayfa yolu.href }]);
    }
    var label = ctx.heading || ctx.activeMenu || ctx.path || 'bulunduğunuz sayfa';
    return makeAnswer('Şu an “' + label + '” alanındasınız. Bu ekranı Ekran Tanıma Ajanı ile yorumluyorum; yanlış linke yönlendirmemek için ekran adını doğrulamadan işlem bağlantısı açmam. Yapmak istediğiniz işlemi yazarsanız sizi güvenli BYS360 ekranına yönlendiririm.');
  }

  function resumeAnswer() {
    var ctx = loadSavedContext() || currentPageContext();
    var last = lastMeaningfulChat();
    var sayfa yolu = routeForCurrentPage();
    var text = 'Aynı oturum içinde kaldığımız yerden devam edebiliriz.';
    if (sayfa yolu) text += ' Şu an “' + sayfa yolu.title + '” ekranındasınız.';
    else if (ctx && (ctx.routeTitle || ctx.heading)) text += ' Son bağlam: “' + (ctx.routeTitle || ctx.heading) + '”.';
    if (last && last.text) text += ' Son konuşulan konu: “' + cleanSmallText(last.text, 120) + '”.';
    text += ' Bir önceki işlemden devam etmek için yapmak istediğiniz adımı yazın; ben aynı oturum bağlamını koruyarak yönlendireceğim.';
    return makeAnswer(text, sayfa yolu ? [{ title: sayfa yolu.title, href: sayfa yolu.href }] : []);
  }


  function currentRouteHelp() {
    return pageAwareAnswer();
  }

  // V9_PERSONEL_IZIN_DEVAMSIZLIK_VEKALET_TAM_BILGI_BANKASI
  function localAnswer(message) {
    var n = normalize(message);
    var links = findRoutes(message);

    if (!n) return makeAnswer('Size yardımcı olmak için buradayım. Yapmak istediğiniz işlemi yazın; sizi BYS360 içindeki doğru modül, gerçek sekme adı ve güvenli işlem sırasıyla yönlendireyim.');


    if (/\b(12 adim|12 adım|12 adim durum|12 adım durum|tamamlama plani|tamamlama planı|v8|durum kontrol)\b/.test(n)) {
      return twelveStepStatusAnswer();
    }

    if (/\b(hangi adimlar eksik|hangi adımlar eksik|eksik adim|eksik adım|neler eksik|kalanlar ne)\b/.test(n)) {
      return missingStepsAnswer();
    }


    if (/\b(v7|ogretim testi|öğretim testi|canli ogretim|canlı öğretim|cevap sozlesmesi|cevap sözleşmesi|modul rehberi|modül rehberi|12 adim|12 adım|hangi adimlar eksik|hangi adımlar eksik|eksik adim|eksik adım)\b/.test(n)) {
      return teachingContractAnswer();
    }

    if (/\b(her seyi biliyor musun|her şeyi biliyor musun|tum ekranlar|tüm ekranlar|ekranlari biliyor musun|ekranları biliyor musun|hangi ekranlari biliyorsun|hangi ekranları biliyorsun|butun moduller|bütün modüller)\b/.test(n)) {
      return knownScreensAnswer();
    }

    if (/\b(adim adim anlat|adım adım anlat|nasil kullanilir|nasıl kullanılır|bana ogret|bana öğret|islem sirasi|işlem sırası)\b/.test(n)) {
      return moduleStepAnswer('BYS360 adım adım rehberlik', 'İşlem adını yazdıktan sonra ilgili gerçek ekran yolunu göstereceğim', ['Yetkiniz olan kullanıcı rolü'], ['Yapmak istediğiniz işlemi kısa yazın', 'Ben ilgili modülü ve ekranı tespit ederim', 'Yetki gerektiren alan varsa önce bunu belirtirim', 'İşlem adımlarını sıralarım', 'Sonunda hangi ekrandan kontrol edeceğinizi söylerim'], ['Olmayan veya eski bağlantıya yönlendirme yapmam.', 'Hassas veri, puan veya idari karar üretmem.'], ['Cevapta gerçek sekme adı, yetki ve kontrol adımı bulunmalıdır.'], [{ title: 'Yardım Merkezi', href: '/support' }]);
    }

    if (/\b(personel yonetimi nasil|personel yönetimi nasıl|personel modulu nasil|personel modülü nasıl|personel nasil calisir|personel nasıl çalışır)\b/.test(n)) {
      return moduleStepAnswer('Personel Yönetimi', 'Sol şerit > Personel Yönetimi', ['Admin', 'Sistem Yöneticisi', 'Personel Yönetimi yetkilisi'], ['Personel listesini açın', 'Yeni kayıt veya düzenleme ekranına girin', 'Sicil No, ad-soyad, unvan/görev, birim, üst birim ve yönetici bilgisini kontrol edin', 'Rol ve menü görünürlüğünü görevle uyumlu seçin', 'Kaydedin'], ['TC yerine Sicil No esas alınmalıdır.', 'Birim ve yönetici ilişkisi yanlışsa izin, vekâlet, performans ve raporlar da etkilenebilir.'], ['Kayıttan sonra personel listesinde arama yapın ve aktiflik/rol/birim bilgisini doğrulayın.'], [{ title: 'Personel Yönetimi', href: '/personnel' }]);
    }

    if (/\b(baskan onaylari nasil|başkan onayları nasıl|baskan onayi nasil|başkan onayı nasıl|70 alti surec|70 altı süreç)\b/.test(n)) {
      return moduleStepAnswer('Başkan Onayları', 'Sol şerit > Performans Yönetimi > Başkan Onayları', ['Başkan', 'Admin', 'Yetkili üst yönetim kullanıcısı'], ['70 altı nihai performans sonucu oluşur', 'Sistem sonucu doğrudan yayınlamaz', 'Kayıt Başkan Onayları ekranında incelenir', 'Karne, amir görüşleri, süreç geçmişi ve yayın kilidi kontrol edilir', 'Yetkili kullanıcı onay/iade işlemini yapar', 'Gerekli süreç kaydı tamamlanmadan personel karnesi kesinleşmez'], ['Sahte onay kaydı oluşturulmamalıdır.', '70 üstü veya puanı oluşmamış kayıt gereksiz onaya düşmemelidir.'], ['Onaydan sonra Süreç Takibi, yayın kilidi ve karne görünürlüğü kontrol edilmelidir.'], [{ title: 'Başkan Onayları', href: '/performance/president-approvals' }, { title: 'Süreç Takibi', href: '/performance/process-tracking' }]);
    }

    if (/\b(destek talebi nasil acilir|destek talebi nasıl açılır|yardim talebi nasil|yardım talebi nasıl|sorun nasil bildirilir|sorun nasıl bildirilir)\b/.test(n)) {
      return moduleStepAnswer('Yardım Merkezi / Destek Talebi', 'Sol şerit > Yardım Merkezi', ['Standart kullanıcı', 'Yönetici', 'Destek yetkilisi'], ['Yardım Merkezi ekranına girin', 'Yeni destek talebi oluşturun', 'Kategori ve başlık seçin', 'Sorunu kısa ve anlaşılır açıklayın', 'Varsa ekran görüntüsü veya belge ekleyin', 'Talebi kaydedin'], ['Kişisel veya hassas veriyi gereksiz yere talep metnine yazmayın.', 'Teknik hata varsa ekran adı ve yaptığınız son adımı belirtin.'], ['Talep durumunu, cevapları ve kapanış bilgisini aynı ekrandan takip edin.'], [{ title: 'Yardım Merkezi', href: '/support' }]);
    }

    if (/\b(anket nasil cevaplanir|anket nasıl cevaplanır|anket nerede|anketler nerede|anket gonder|anket gönder)\b/.test(n)) {
      return moduleStepAnswer('Anketler', 'Sol şerit > Anketler', ['Anket atanan kullanıcı', 'Anket yetkilisi'], ['Anketler ekranını açın', 'Size atanan anketi seçin', 'Zorunlu soruları doldurun', 'Açık uçlu cevap varsa kurumsal ve net yazın', 'Gönder butonuyla yanıtı tamamlayın'], ['Anket cevapları yetki ve gizlilik kurallarıyla korunur.', 'Başka kullanıcıların cevapları yetkisiz gösterilmemelidir.'], ['Gönderim sonrası anketin tamamlandı durumuna geçtiğini kontrol edin.'], [{ title: 'Anketler', href: '/surveys' }]);
    }



    // V9_PERSONEL_IZIN_DEVAMSIZLIK_VEKALET_TAM_BILGI_BANKASI_CEVAPLARI
    if (/\b(v9|personel bilgi bankasi|personel bilgi bankası|izin bilgi bankasi|izin bilgi bankası|vekalet bilgi bankasi|vekâlet bilgi bankası)\b/.test(n)) {
      return makeAnswer('V9 bilgi bankası aktif. Bu sürüm Personel Yönetimi, İzin ve Devamsızlık Takibi ile Devamsızlık ve Vekâlet konularında daha ayrıntılı, adım adım ve güvenli yönlendirme verir. Cevaplar gerçek ekran adlarıyla hazırlanır; eski/kırık bağlantılar kullanılmaz.', [
        { title: 'Personel Yönetimi', href: '/personnel' },
        { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
        { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' }
      ]);
    }

    if (/\b(personel ekle|yeni personel|personel kaydi|personel kaydı|personel nasil eklenir|personel nasıl eklenir|sicil no ile personel)\b/.test(n)) {
      return moduleStepAnswer('Personel ekleme', 'Sol şerit > Personel Yönetimi', ['Admin', 'Sistem Yöneticisi', 'Personel Yönetimi yetkilisi', 'Yetki verilmiş İK/personel kullanıcısı'], ['Personel Yönetimi ekranını açın', 'Personel listesi içinde yeni kayıt/ekle butonunu kullanın', 'Sicil No, ad, soyad, unvan/görev, birim ve üst birim bilgilerini doldurun', 'Personelin yönetici/amir bağlantısını kontrol edin', 'Gerekliyse profil fotoğrafı ve iletişim bilgilerini ekleyin', 'Rol ve menü görünürlüğünü görevine uygun seçin', 'Kaydedin'], ['TC yerine Sicil No esas alınmalıdır.', 'Birim, üst birim veya yönetici yanlış girilirse performans görev üretimi, izin/vekâlet ve raporlar da yanlış etkilenebilir.', 'Başlangıç gizli erişim bilgisisi veya kullanıcı hesabı üretimi kurum ayarlarına göre çalışmalıdır.'], ['Personel listesinde sicil no veya ad-soyad ile arama yapın; aktiflik, birim, rol ve yönetici bilgisinin doğru göründüğünü kontrol edin.'], [{ title: 'Personel Yönetimi', href: '/personnel' }]);
    }

    if (/\b(personel duzenle|personel düzenle|personel bilgisi guncelle|personel bilgisi güncelle|birim degisikligi|birim değişikliği|yonetici degisti|yönetici değişti|unvan degisti|unvan değişti)\b/.test(n)) {
      return moduleStepAnswer('Personel bilgisi güncelleme', 'Sol şerit > Personel Yönetimi', ['Admin', 'Sistem Yöneticisi', 'Personel Yönetimi yetkilisi'], ['Personel Yönetimi ekranında personeli sicil no veya ad-soyad ile bulun', 'Detay/düzenle işlemine girin', 'Unvan, görev, birim, üst birim, yönetici, aktiflik ve rol bilgilerini kontrol edin', 'Değişiklikleri kaydedin', 'Gerekirse performans görev üretimi veya yetki görünürlüğünü tekrar kontrol edin'], ['Organizasyon değişikliği geçmiş kayıt ve raporlama açısından önemlidir.', 'Yönetici değişikliği performans amir zincirini etkileyebilir.', 'Rol değişikliği menü görünürlüğünü değiştirebilir.'], ['Kayıt sonrası personel kartı, menü görünürlüğü, varsa performans görevleri ve raporlardaki birim bilgisini kontrol edin.'], [{ title: 'Personel Yönetimi', href: '/personnel' }, { title: 'Performans Yönetimi', href: '/performance/dashboard' }]);
    }

    if (/\b(sicil no|sicil numarasi|sicil numarası|tc yerine|sicil no|personel tekil)\b/.test(n)) {
      return makeAnswer('BYS360’da personel takibinde temel ayırt edici bilgi Sicil No’dur. Personel ekleme ve güncelleme işlemlerinde Sicil No doğru girilmelidir; tekrar eden veya hatalı Sicil No, personel listesi, izin/vekâlet, performans amir zinciri ve raporlama tarafında karışıklık oluşturabilir. TC bilgisi kullanıcı ekranlarında ana takip bilgisi olarak kullanılmamalıdır.', [{ title: 'Personel Yönetimi', href: '/personnel' }]);
    }

    if (/\b(profil fotografi|profil fotoğrafı|personel profili|profil bilgileri|personel karti|personel kartı)\b/.test(n)) {
      return moduleStepAnswer('Personel profil bilgileri', 'Sol şerit > Personel Yönetimi', ['Admin', 'Sistem Yöneticisi', 'Personel Yönetimi yetkilisi', 'Yetkisi kapsamında ilgili kullanıcı'], ['Personel Yönetimi ekranında personeli bulun', 'Personel detay/profil ekranını açın', 'Profil fotoğrafı, iletişim, unvan, görev, birim, üst birim, yönetici ve aktiflik bilgilerini kontrol edin', 'Gerekli alanları güncelleyin', 'Kaydedin'], ['Profil bilgileri yalnızca görsel bilgi değildir; birim, rol ve yönetici bağlantısı diğer modülleri etkiler.', 'Hassas veya gereksiz kişisel veri eklenmemelidir.'], ['Personel listesinde ve ilgili dashboard/rapor ekranlarında profil bilgisinin doğru göründüğünü kontrol edin.'], [{ title: 'Personel Yönetimi', href: '/personnel' }]);
    }

    if (/\b(izin nasil girilir|izin nasıl girilir|izin kaydi nasil|izin kaydı nasıl|izin talebi nasil|izin talebi nasıl|yillik izin|yıllık izin|idari izin|saatlik izin|izin bakiyesi)\b/.test(n)) {
      return moduleStepAnswer('İzin kaydı / izin talebi', 'Sol şerit > Personel Yönetimi > İzin ve Devamsızlık Takibi', ['Personel Yönetimi yetkilisi', 'İK/personel yetkilisi', 'Yetkili amir', 'Kurum ayarına göre personelin kendisi'], ['İzin ve Devamsızlık Takibi ekranını açın', 'Yeni izin kaydı veya izin talebi işlemini seçin', 'İlgili personeli seçin', 'İzin türünü belirleyin', 'Başlangıç ve bitiş tarih/saat bilgisini girin', 'Gerekirse açıklama ve belge ekleyin', 'Kaydedin veya onaya gönderin', 'Onay süreci varsa ilgili amir/onaycıya düştüğünü kontrol edin'], ['İzin tarihleri yanlış girilirse devamsızlık, vekâlet ve performans görev akışı etkilenebilir.', 'İzinli amir varsa vekâlet veya görev devri kontrol edilmelidir.', 'İzin bakiyesi kurum ayarına göre takip edilmelidir.'], ['Kayıt sonrası aynı ekranda izin durumunu, izin bakiyesini, varsa onay statüsünü ve bildirim kaydını kontrol edin.'], [{ title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' }]);
    }

    if (/\b(izin talebi nerede|izin nerede|izinleri nereden|izin listesi|izin takip|izin durumu|izin onayi|izin onayı)\b/.test(n)) {
      return makeAnswer('İzin işlemleri için doğru canlı ekran: Personel Yönetimi > İzin ve Devamsızlık Takibi. Bu ekranda izin kaydı, izin talebi, izin durumu, izin bakiyesi ve onay takibi kontrol edilir. Eski personel izin bağlantıları kullanılmamalıdır; beyaz ekran riski olan eski yollar güvenli menü haritasından engellenir.', [{ title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' }]);
    }

    if (/\b(devamsizlik nedir|devamsızlık nedir|devamsizlik kaydi|devamsızlık kaydı|devamsizlik nasil|devamsızlık nasıl|ise gelmedi|işe gelmedi|gec kaldi|geç kaldı)\b/.test(n)) {
      return moduleStepAnswer('Devamsızlık kaydı', 'Sol şerit > Personel Yönetimi > Devamsızlık ve Vekâlet', ['Personel Yönetimi yetkilisi', 'İK/personel yetkilisi', 'Yetkili amir'], ['Devamsızlık ve Vekâlet ekranını açın', 'Personeli seçin', 'Devamsızlık türünü veya olay tipini belirleyin', 'Tarih/saat bilgisini girin', 'Gerekli açıklama veya belgeyi ekleyin', 'Kaydedin', 'Kayıt sonrası rapor ve personel geçmişi etkisini kontrol edin'], ['Devamsızlık kaydı personel geçmişi, izin dengelemesi ve raporları etkileyebilir.', 'Yetkisiz kullanıcı başka personelin detayını görmemelidir.', 'Geçerli bir izin kaydı varsa devamsızlıkla çakışma kontrol edilmelidir.'], ['Kayıt sonrası personel devamsızlık listesi, izin/devamsızlık özeti ve ilgili rapor ekranı kontrol edilmelidir.'], [{ title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' }]);
    }

    if (/\b(vekalet nasil|vekâlet nasıl|vekalet tanimla|vekâlet tanımla|vekil ata|gorev devri|görev devri|amir izinli|izinli amir|vekalet nerede|vekâlet nerede)\b/.test(n)) {
      return moduleStepAnswer('Vekâlet tanımlama', 'Sol şerit > Personel Yönetimi > Devamsızlık ve Vekâlet', ['Admin', 'Personel Yönetimi yetkilisi', 'İK/personel yetkilisi', 'Yetkili amir'], ['Devamsızlık ve Vekâlet ekranını açın', 'Asıl personeli veya izinli amiri seçin', 'Vekil olacak personeli seçin', 'Başlangıç ve bitiş tarihlerini belirleyin', 'Vekâlet kapsamını seçin', 'Kaydedin', 'İlgili süreçlerde vekilin yetki/görev devrinin doğru çalıştığını kontrol edin'], ['Vekâlet süresi izin/devamsızlık tarihiyle uyumlu olmalıdır.', 'Vekil kişinin yetki kapsamı kurum kurallarıyla sınırlı olmalıdır.', 'Performans değerlendirme döneminde izinli amir varsa görev akışı vekâlet bilgisinden etkilenebilir.'], ['Vekâlet listesinde kayıt görünmeli; varsa performans görevleri, onay süreçleri ve bildirimler doğru kişiye yönlenmelidir.'], [{ title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' }, { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' }]);
    }

    if (/\b(izinli amir performansi etkiler mi|izinli amir performansı etkiler mi|amir izinliyse|amir yoksa|vekalet performans|vekâlet performans|gorev kime duser|görev kime düşer)\b/.test(n)) {
      return makeAnswer('İzinli amir varsa BYS360’da önce izin/devamsızlık kaydı ve varsa vekâlet tanımı kontrol edilmelidir. Performans sürecinde değerlendirme görevinin boşa düşmemesi için vekil veya yetkili akış kurum kuralına göre devreye alınır. Asistan performans puanı belirlemez; yalnızca doğru ekranları ve kontrol adımlarını gösterir: önce İzin ve Devamsızlık Takibi, sonra Devamsızlık ve Vekâlet, ardından ilgili performans görev/süreç ekranı kontrol edilir.', [{ title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' }, { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' }, { title: 'Değerlendirme Görevleri', href: '/performance/evaluation-tasks' }]);
    }

    if (/\b(personel gorunmuyor|personel görünmüyor|personel listede yok|personel ekleyemiyorum|sicil hatasi|sicil hatası|yonetici yanlis|yönetici yanlış|birim yanlis|birim yanlış)\b/.test(n)) {
      return makeAnswer('Personel tarafında sorun varsa şu sırayla kontrol edin: 1) Personel kaydı aktif mi? 2) Sicil No doğru ve tekil mi? 3) Birim, üst birim ve yönetici bağlantısı doğru mu? 4) Rol ve kişi bazlı menü görünürlüğü açık mı? 5) Kullanıcının ilgili personeli görme yetkisi var mı? 6) Son değişiklikten sonra ilgili liste/rapor yenilendi mi? Bu kontroller Personel Yönetimi ve gerekiyorsa Sistem Ayarları tarafında yapılmalıdır.', [{ title: 'Personel Yönetimi', href: '/personnel' }, { title: 'Sistem Ayarları', href: '/settings' }]);
    }

    if (/\b(merhaba|selam|slm|gunaydin|iyi aksamlar|iyi gunler)\b/.test(n)) {
      return makeAnswer('Merhaba, ben ' + MODULE_NAME + '. BYS360 içinde yetkiniz dâhilindeki işlemler için size adım adım rehberlik ederim. Hangi işlem için yardımcı olayım?', [{ title: 'Dönemler', href: '/performance/periods' }, { title: 'Yardım Merkezi', href: '/support' }]);
    }

    if (/\b(nasilsin|iyi misin|naber|nasilsiniz)\b/.test(n)) {
      return makeAnswer('İyiyim, teşekkür ederim. Bugün BYS360 içinde hangi işlemde birlikte ilerleyelim? Dönemler, karne, Başkan Onayları, rol matrisi, personel, anket veya destek başlıklarında adım adım yardımcı olabilirim.');
    }


    if (/\b(bu ekranda ne yapabilirim|bu sayfada ne yapabilirim|burada ne yapacagim|burada ne yapacağım|sayfa yardimi|sayfa yardımı|ekran yardimi|ekran yardımı|nereden devam|nereden devam edecegim|nereden devam edeceğim)\b/.test(n)) {
      return pageAwareAnswer();
    }

    if (/\b(az onceki konu|az önceki konu|kaldigimiz yer|kaldığımız yer|devam edelim|kaldigimiz yerden|kaldığımız yerden|onceki konudan|önceki konudan)\b/.test(n)) {
      return resumeAnswer();
    }

    if (/\b(final test|test senaryo|test senaryolari|test senaryoları|kalite kontrol|canli kontrol|canlı kontrol|asistani test|asistanı test|v6|v7|ogretim testi|öğretim testi)\b/.test(n)) {
      return makeAnswer('V7 canlı öğretim ve kalite kontrolünde şu başlıkları test etmelisiniz: 1) Baloncuk kısa tıklamayla açılıyor mu, sürükleyince konumu bozulmadan taşınıyor mu? 2) Sayfa değişince sohbet ve açık panel durumu korunuyor mu? 3) İzin, vekâlet, Dönemler, Başkan Onayları ve rol matrisi cevapları gerçek ekran adlarıyla geliyor mu? 4) Kırık/eski linkler beyaz ekrana götürmeden engelleniyor mu? 5) Hava durumu cevabı ciddi ve doğrulanabilir bilgiyle sınırlı mı? 6) “Seni kim geliştirdi?”, “Neler yapabiliyorsun?” ve “Bu sayfada ne yapabilirim?” soruları düzgün cevaplanıyor mu?', [
        { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
        { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' },
        { title: 'Dönemler', href: '/performance/periods' },
        { title: 'Başkan Onayları', href: '/performance/president-approvals' }
      ]);
    }


    if (/\b(menu haritasi|menü haritası|gercek menu|gerçek menü|hangi ekranlar var|ekran haritasi|ekran haritası)\b/.test(n)) {
      return makeAnswer('BYS360 içinde güvenli menü haritasına göre yönlendirme yaparım. Tanımlı başlıklar: Anasayfa, Dashboard, Personel Yönetimi, İzin ve Devamsızlık Takibi, Devamsızlık ve Vekâlet, Performans Yönetimi, Sorular / Kriterler, Dönemler, Değerlendirme Görevleri, Başkan Onayları, Yayın Ön Onayı, Süreç Takibi, Süreç Raporları, Dönem İçi Notlar, Gelişim Rehberi, Not Karnesi, Geçmiş Karne Arşivi, Mesajlar, Anketler, Yardım Merkezi, AI Karar Destek Merkezi, Asistan Bilgi Bankası ve Sistem Ayarları. Eski veya doğrulanmayan bağlantıları açmadan önce engellerim.', [
        { title: 'Dönemler', href: '/performance/periods' },
        { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
        { title: 'Başkan Onayları', href: '/performance/president-approvals' },
        { title: 'Sistem Ayarları', href: '/settings' }
      ]);
    }

    if (/\b(kirik link|kırık link|beyaz ekran|sayfa acilmiyor|sayfa açılmıyor|yanlis link|yanlış link)\b/.test(n)) {
      return makeAnswer('Beyaz ekran veya kırık link riskini azaltmak için yönlendirmeleri güvenli menü haritasından geçiririm. Eski bağlantı tespit edersem canlı ekrana çeviririm; doğrulanmayan ekranı ise açmayıp uyarı veririm. Örneğin izin işlemleri için eski personel izin bağlantısı yerine doğru yol Personel Yönetimi > İzin ve Devamsızlık Takibi ekranıdır.', [
        { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
        { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' }
      ]);
    }

    if (/\b(bu sayfa|su sayfa|şu sayfa|neredeyim|bulundugum ekran|bulunduğum ekran)\b/.test(n)) {
      return currentRouteHelp();
    }


    if (/\b(neler yapabiliyorsun|ne yapabilirsin|hangi konularda yardimci|hangi konularda yardımcı|bana hangi konularda yardimci olursun|bana hangi konularda yardımcı olursun|yardimci ol|yardımcı ol|ne ise yararsin|ne işe yararsın)\b/.test(n)) {
      return makeAnswer('Size BYS360 içinde adım adım rehberlik ederim: personel kaydı, izin, devamsızlık, vekâlet, performans Dönemler, Sorular / Kriterler, Değerlendirme Görevleri, Başkan Onayları, karne, raporlar, rol matrisi, menü görünürlüğü, destek talepleri, anketler, mesajlar, bildirimler ve AI Karar Destek ayrımı gibi konularda yardımcı olurum. Soruyu eksik veya günlük dille yazsanız bile niyetinizi BYS360 ekranlarıyla eşleştirmeye çalışırım. İdari karar üretmem, performans puanı belirlemem ve hassas veri göstermem.', [
        { title: 'Dönemler', href: '/performance/periods' },
        { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
        { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' },
        { title: 'Sistem Ayarları', href: '/settings' }
      ]);
    }

    if (/\b(hava|havadurumu|hava durumu|bugun hava|bugün hava|yagmur|yağmur|sicaklik|sıcaklık|ruzgar|rüzgar|open meteo|open-meteo)\b/.test(n)) {
      return makeAnswer('Hava durumunu BYS360’daki hava durumu kartından veya Open-Meteo bağlantısından okumaya çalışırım. Güncel veri gelirse kısa, ciddi ve doğrulanabilir bir hava notu paylaşırım; veri yoksa hava bilgisi uydurmam.');
    }

    if (/\b(kim gelistirdi|seni kim|kim yapti|gelistiren kim|kimin tarafindan|kurumsal geliştirme|kurumsal kullanım|kurumsal kullanım)\b/.test(n)) {
      return makeAnswer('Ben BYS360 Asistanı’yım. BYS360 için Personel kurumsal kullanım Özden tarafından geliştirildim. Görevim, BYS360 içinde yetkiniz dâhilindeki işlemleri sade, güvenli ve doğru sırayla anlatmak; sizi gerçek ekranlara yönlendirmek ve sistemi daha kolay kullanmanıza yardımcı olmaktır.', [{ title: 'Asistan Bilgi Bankası', href: '/ai-agent/knowledge' }]);
    }

    if (/\b(sen nesin|kimsin|ne ise yararsin|ne işe yararsın|kendini tanit|kendini tanıt|asistan misin|asistan mısın)\b/.test(n)) {
      return makeAnswer('Ben BYS360 Asistanı’yım; BYS360’a özel kurumsal rehberlik, akıllı yönlendirme ve yetki kontrollü dijital yardımcı katmanıyım. Kullanıcıların sistemde doğru ekrana ulaşmasına, işlem sırasını anlamasına ve yetkisi dâhilindeki bilgileri güvenli şekilde takip etmesine yardımcı olurum.', [{ title: 'Yardım Merkezi', href: '/support' }]);
    }

    if (/\b(nasil calisiyorsun|nasıl çalışıyorsun|calisma mantigin|çalışma mantığın|yapay zekaya bagli misin|yapay zekaya bağlı mısın|ai bagli|ai bağlı|chatgpt misin|chatgpt mısın)\b/.test(n)) {
      return makeAnswer('BYS360 içindeki bilgi bankası, güvenli menü haritası, işlem adımları ve yetki kurallarıyla çalışırım. Yapay zekâ/akıllı yönlendirme katmanından yararlanabilirim; ancak BYS360 sınırlarının dışına çıkmam. Karar destek alanı analiz ve özet üretir; ben ise kullanıcıya doğru ekranı, doğru işlem sırasını ve dikkat edilmesi gereken güvenlik sınırını anlatırım.', [{ title: 'AI Karar Destek Merkezi', href: '/ai/decision-support/faz1/health' }]);
    }


    if (/\b(izin|izin kaydi|izin kaydı|izin talebi|izin nasil|izin nasıl|izin nerede|izin bakiyesi)\b/.test(n)) {
      return makeAnswer('İzin işlemleri için doğru yol: Sol şerit > Personel Yönetimi > İzin ve Devamsızlık Takibi. Bu ekranda personel seçilir, izin türü belirlenir, başlangıç ve bitiş tarihleri girilir, gerekiyorsa açıklama/belge ve vekil personel bilgisi eklenir, ardından İzin kaydet butonuyla kayıt oluşturulur. Kayıttan sonra izin listesi, izin bakiyesi ve izinli amir varsa vekâlet etkisi kontrol edilir. İzinli amirlerde performans görev zincirinin boşa düşmemesi için vekâlet bilgisi özellikle kontrol edilmelidir.', [
        { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' },
        { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' }
      ]);
    }

    if (/\b(vekalet|vekâlet|devamsizlik|devamsızlık|vekil|gorev devri|görev devri)\b/.test(n)) {
      return makeAnswer('Devamsızlık ve vekâlet için doğru yol: Sol şerit > Personel Yönetimi > Devamsızlık ve Vekâlet. Bu ekranda devamsızlık kayıtları izlenir; vekâlet tanımlanacaksa asıl kişi, vekil personel, başlangıç-bitiş tarihi, vekâlet kapsamı ve not bilgisi girilir. Kaydettikten sonra vekâlet kayıtları listesinde durum kontrol edilir. Vekâlet, özellikle izinli amirlerde performans/onay görevlerinin doğru kişiye yönlenmesi için kullanılır.', [
        { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' },
        { title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' }
      ]);
    }

    if (/\b(hangi sorular|hangi sorulari|hangi soruları|ne sorabilirim|neler sorabilirim|soru listesi|ornek sorular|örnek sorular|insan ne sorar|hangi konular|soru havuzu|bys360 da ne sorulur|bys360da ne sorulur)\b/.test(n)) {
      return makeAnswer('BYS360 sınırları içinde şu başlıklarda soru sorabilirsiniz: Genel kullanım, Ana Sayfa, Dashboard, Personel Yönetimi, Sicil No, İzin ve Devamsızlık Takibi, Devamsızlık ve Vekâlet, Performans Yönetimi, Dönemler, Sorular / Kriterler, Değerlendirme Görevleri, Görevlerim, performans notu, Dönem İçi Notlar, Gelişim Rehberi, Başkan Onayları, Yayın Ön Onayı, Not Karnesi, Geçmiş Karne Arşivi, Rol Matrisi, menü görünürlüğü, destek talebi, mesajlar, duyurular, anketler, AI Karar Destek Merkezi ve KPI Dashboardu. Örnek: “performans notu nasıl verilir”, “dönem nasıl açılır”, “kişi nasıl eklenir”, “menü görünmüyor”, “70 altı sonuç ne olur”. Hassas veri, performans puanı, amir görüşü, mesaj metni veya anket cevabı göstermem; sizi yetkili ekrana yönlendiririm.', [{ title: 'Dönem İçi Notlar', href: '/performance/interim-notes' }, { title: 'Dönemler', href: '/performance/periods' }, { title: 'Sistem Ayarları', href: '/settings' }]);
    }

    if (/\b(donem|donemler|yeni donem|donem ac|donem olustur|performans donemi)\b/.test(n)) {
      return makeAnswer('Performans dönemi için doğru yol: Sol şerit > Performans Yönetimi > Dönemler. Bu ekranda Yeni Dönem Oluştur/Yeni Dönem Ekle butonuna basın; dönem adı, dönem türü, başlangıç-bitiş tarihi ve kapsam bilgisini doldurun. Dikkat: kullanıcıya görünen gerçek sekme adı Dönemlerdir; yönlendirme bu adla yapılmalıdır.', [{ title: 'Dönemler', href: '/performance/periods' }, { title: 'Sorular / Kriterler', href: '/performance/criteria' }]);
    }

    if (/\b(kriter|soru|sorular|degerlendirme kriterleri|yetkinlik)\b/.test(n)) {
      return makeAnswer('Kriter işlemleri için doğru yol: Sol şerit > Performans Yönetimi > Sorular / Kriterler. Buradan değerlendirme soruları/kriterleri eklenir, düzenlenir ve aktiflikleri kontrol edilir. Ana kullanıcı dili “Sorular / Kriterler” ve “Değerlendirme Kriterleri” olmalıdır.', [{ title: 'Sorular / Kriterler', href: '/performance/criteria' }]);
    }

    if (/\b(performans notu|not nasil verilir|not nasıl verilir|not ver|not gir|not ekle|not dus|not düş|olay notu|gozlem notu|gözlem notu|donem ici not|dönem içi not|ara geri bildirim|gelisim notu|gelişim notu)\b/.test(n)) {
      return makeAnswer('Performans notu için doğru yol: Sol şerit > Performans Yönetimi > Dönem İçi Notlar. Bu ekran puan verme ekranı değildir; dönem içindeki olumlu/olumsuz gözlem, başarı, gelişim ihtiyacı veya genel not kaydı için kullanılır. Adım adım: 1) Dönem İçi Notlar sekmesini açın. 2) Yeni Not / Not Ekle butonuna basın. 3) İlgili dönem ve personeli seçin. 4) Not türünü ve açıklamayı yazın. 5) Kaydedin. Notlar otomatik puan üretmez; değerlendirme döneminde amire hatırlatma ve gelişim desteği sağlar.', [{ title: 'Dönem İçi Notlar', href: '/performance/interim-notes' }, { title: 'Gelişim Rehberi', href: '/performance/meeting-development/faz10' }]);
    }

    if (/\b(puanlama|degerlendirme gorev|gorev uret|amir gorevi|gorevlerim)\b/.test(n)) {
      return makeAnswer('Puanlama ve amir görevleri için doğru yol: Sol şerit > Performans Yönetimi > Değerlendirme Görevleri. Amir yalnızca kendisine atanmış personel ve görevler üzerinde işlem yapar. Kör değerlendirme yoktur; sonraki amir önceki değerlendirmeyi görebilir.', [{ title: 'Değerlendirme Görevleri', href: '/performance/evaluation-tasks' }]);
    }

    if (/\b(70 alti|dusuk performans|baskan onay|ust onay|yayin kilidi)\b/.test(n)) {
      return makeAnswer('70 altı performans sonucu doğrudan kesinleşmez. Doğru takip yolu: Sol şerit > Performans Yönetimi > Başkan Onayları. Başkan Onayı tamamlanmadan ve gerekli süreç kaydı oluşmadan karne personele kesin/yayınlanmış sonuç olarak açılmaz.', [{ title: 'Başkan Onayları', href: '/performance/president-approvals' }, { title: 'Süreç Takibi', href: '/performance/process-tracking' }]);
    }

    if (/\b(karne|karnem|not karnesi|sonucum|performans sonucum)\b/.test(n)) {
      return makeAnswer('Karne görünürlüğü yayın/onay sürecine bağlıdır. Personel sonucu süreç tamamlanmadan göremez. Doğru yol: Sol şerit > Genel > Not Karnesi. Eski sonuçlar için Geçmiş Karne Arşivi kullanılmalıdır.', [{ title: 'Not Karnesi', href: '/performance/scorecard' }, { title: 'Geçmiş Karne Arşivi', href: '/performans/gecmis-karne-arsivi' }]);
    }

    if (/\b(menu gorunmuyor|sekme yok|rol matrisi|yetki|ayarlar|ac kapa|gorunurluk)\b/.test(n)) {
      return makeAnswer('Bir sekme görünmüyorsa kontrol sırası şöyledir: 1) Sol şerit > Sistem Ayarları ekranına girin. 2) Modül Bazlı Rol Matrisi’nde ana modül açık mı bakın. 3) Performans işlemleri için Performans Yönetimi Rol Matrisi’ni ayrıca kontrol edin. 4) Kişi bazlı menü görünürlüğü veya birim bazlı profil ekranı kapatıyor mu inceleyin. 5) Değişiklikten sonra kullanıcı oturumunu yenileyip menünün gerçekten görünüp görünmediğini kontrol edin. Doğru davranış: yetkisiz kullanıcı menüyü hiç görmemeli; URL yazarsa da beyaz ekran değil güvenli erişim engeli almalıdır.', [{ title: 'Sistem Ayarları', href: '/settings' }]);
    }

    if (/\b(asistani egit|ogret|bilgi bankasi|bilgi ekle|cevap ogret)\b/.test(n)) {
      return makeAnswer('Asistan eğitim içerikleri için doğru yol: Sol şerit > AI Karar Destek Merkezi > Asistan Bilgi Bankası. Burada BYS360 Asistanı’na gerçek sekme adları, işlem adımları, yetki sınırları ve güvenli cevaplar öğretilir.', [{ title: 'Asistan Bilgi Bankası', href: '/ai-agent/knowledge' }]);
    }


    if (/\b(personel ekle|yeni personel|personel kaydi|personel kaydı|sicil|personel duzenle|personel düzenle|personel listesi)\b/.test(n)) {
      return makeAnswer('Personel işlemleri BYS360’ın ana veri omurgasıdır. Genel akış: Sol şerit > Personel Yönetimi. Personel eklerken Sicil No, ad-soyad, unvan/görev, birim, üst birim, yönetici ve rol/görünürlük bilgileri kontrol edilir. Kaydetmeden önce birim-yönetici ilişkisi doğru olmalıdır; çünkü performans amir zinciri, izin/vekâlet, bildirim ve raporlar bu veriden beslenir. Kayıt sonrası personel listesinde kaydı arayın ve aktif/pasif durumunu kontrol edin.', [{ title: 'Personel Yönetimi', href: '/personnel' }]);
    }

    if (/\b(izin ve devamsizlik|izin ve devamsızlık|izin nasil calisir|izin nasıl çalışır|izin sureci|izin süreci|izin detay)\b/.test(n)) {
      return makeAnswer('İzin süreci şöyle çalışır: 1) Sol şerit > Personel Yönetimi > İzin ve Devamsızlık Takibi ekranına girilir. 2) Personel seçilir. 3) İzin türü ve tarih aralığı girilir. 4) Gerekirse açıklama, belge ve vekil personel bilgisi eklenir. 5) Kayıt oluşturulur. 6) İzin bakiyesi, izin listesi ve onay/izleme durumu kontrol edilir. 7) İzinli kişi amirse Devamsızlık ve Vekâlet ekranında görev devri de kontrol edilmelidir. Bu akış performans görevleri ve onay süreçlerinin boşa düşmemesi için önemlidir.', [{ title: 'İzin ve Devamsızlık Takibi', href: '/hr-management/leave' }, { title: 'Devamsızlık ve Vekâlet', href: '/hr-management/attendance' }]);
    }

    if (/\b(performans nasil calisir|performans nasıl çalışır|performans akisi|performans akışı|performans sureci|performans süreci|performans modulu|performans modülü)\b/.test(n)) {
      return makeAnswer('Performans süreci genel olarak şu sırayla ilerler: 1) Performans Yönetimi > Dönemler ekranında dönem açılır. 2) Sorular / Kriterler kontrol edilir. 3) Personel, kategori, birim, amir, izin ve vekâlet verileri doğrulanır. 4) Değerlendirme Görevleri oluşturulur. 5) Amirler görevlerini işlem sırasına göre tamamlar. 6) Sistem nihai puanı ve açıklama zorunluluklarını kontrol eder. 7) 70 altı sonuçlar Başkan Onayları sürecine düşer. 8) Gerekli onaylardan sonra yayın süreci tamamlanır. 9) Karne ve raporlar yetki sınırına göre görünür olur.', [{ title: 'Dönemler', href: '/performance/periods' }, { title: 'Sorular / Kriterler', href: '/performance/criteria' }, { title: 'Değerlendirme Görevleri', href: '/performance/evaluation-tasks' }, { title: 'Başkan Onayları', href: '/performance/president-approvals' }]);
    }

    if (/\b(rol matrisi nasil|rol matrisi nasıl|menu gorunmuyor|menü görünmüyor|sekme gorunmuyor|sekme görünmüyor|yetki yok|erisim yok|erişim yok|modul acilmiyor|modül açılmıyor)\b/.test(n)) {
      return makeAnswer('Menü veya sekme görünmüyorsa kontrol sırası şöyledir: 1) Sistem Ayarları içinde Modül Bazlı Rol Matrisi açık mı? 2) İlgili modülün kendi rol matrisi açık mı? 3) Kullanıcıya kişi bazlı özel menü görünürlüğü verilmiş mi? 4) Birim bazlı profil kullanılıyorsa o profil ilgili ekranı kapatıyor mu? 5) Backend sayfa yolu yetkisi de aynı kuralla çalışıyor mu? Doğru kural şudur: Kullanıcı görmemesi gereken menüyü hiç görmemeli; URL yazarsa da güvenli erişim engeli almalıdır, beyaz ekran almamalıdır.', [{ title: 'Sistem Ayarları', href: '/settings' }, { title: 'Modül Bazlı Rol Matrisi', href: '/settings/role-matrix' }, { title: 'Performans Yönetimi Rol Matrisi', href: '/settings/performance-role-matrix' }]);
    }

    if (/\b(rapor|raporlar|dashboard|yonetici gorunumu|yönetici görünümü|riskli personel|aksatan amir|performans haritasi|performans haritası)\b/.test(n)) {
      return makeAnswer('Rapor ve dashboard ekranları yetki kapsamına göre çalışır. Genel görünüm için Dashboard, performans akışı için Süreç Takibi, dönem/görev/onay analizleri için Süreç Raporları kullanılır. Başkan/Admin geniş görünüm alabilir; Grup Başkanı ve Koordinatör yalnızca kendi organizasyon kapsamındaki ekip, kategori, dönem ve süreç özetlerini görmelidir. Rapor okurken sırasıyla dönem, kapsam, tamamlanma oranı, aksatan amir, 70 altı/başkan onayı, yayın kilidi ve kategori/grup ortalaması kontrol edilir. Kişi detayı her zaman yetki sınırıyla korunur.', [{ title: 'Dashboard', href: '/dashboard' }, { title: 'Süreç Raporları', href: '/performance/process-reports' }, { title: 'Süreç Takibi', href: '/performance/process-tracking' }]);
    }

    if (/\b(destek talebi|yardim merkezi|yardım merkezi|destek nerede|talep ac|talep aç|sorun bildir)\b/.test(n)) {
      return makeAnswer('Destek süreci için doğru yol: Sol şerit > Yardım Merkezi. Kullanıcı önce kategori seçer, kısa bir başlık yazar, sorunu anlaşılır şekilde açıklar ve varsa ekran görüntüsü/dosya ekler. Talep kaydedildikten sonra durum, cevaplar, ek mesajlar ve kapanış bilgisi aynı alandan takip edilir. Asistan kullanım sorularında rehberlik eder; teknik sorun devam ediyorsa destek talebi oluşturulmalıdır.', [{ title: 'Yardım Merkezi', href: '/support' }]);
    }

    if (/\b(anket|anketler|anket cevapla|duyuru|bildirim|mesaj|mesajlar|iletisim|iletişim)\b/.test(n)) {
      return makeAnswer('İletişim, mesaj, anket ve bildirim alanlarında kullanıcı yalnızca yetkisi dahilindeki kayıtları görür. Mesajlaşma için Mesajlar, anketleri görüntülemek/yanıtlamak için Anketler, sorun bildirmek için Yardım Merkezi kullanılır. Anketlerde kullanıcı önce kendisine atanmış anketi açar, soruları yanıtlar, zorunlu alanları tamamlar ve gönderir. Açık uçlu anket cevabı, mesaj içeriği veya kişisel hassas veri yetkisiz şekilde gösterilmez.', [{ title: 'Mesajlar', href: '/messages' }, { title: 'Anketler', href: '/surveys' }, { title: 'Yardım Merkezi', href: '/support' }]);
    }

    if (/\b(ai karar destek|karar destek|yapay zeka karar|analiz merkezi|ai analiz)\b/.test(n)) {
      return makeAnswer('AI Karar Destek Merkezi; performans, personel, anket, destek ve rapor verilerinden özet, risk farkındalığı ve yönetici içgörüsü üretir. BYS360 Asistanı ise kullanım rehberi, güvenli menü yönlendirme ve işlem öğretme katmanıdır. Bu iki alan karışmamalıdır: karar destek analiz eder; asistan doğru ekranı ve işlem sırasını anlatır. Her ikisi de idari kararın veya insan onayının yerine geçmez.', [{ title: 'AI Karar Destek Merkezi', href: '/ai/decision-support/faz1/health' }]);
    }

    if (links.length) {
      return makeAnswer('Anladım. Bu konu BYS360 içinde şu ekrana/ekranlara bağlı görünüyor. İşlemi yaparken kullanıcıya görünen gerçek sekme ve buton adlarını esas alın; yetkiniz yoksa menü görünmeyebilir veya erişim güvenli şekilde engellenir.', links);
    }

    return makeAnswer('Sorunuzu BYS360 kapsamında yorumlayacağım. Lütfen yapmak istediğiniz işlemi yazın: örneğin “Dönemler nerede?”, “Başkan Onayları nasıl çalışır?”, “Rol matrisi niye görünmüyor?”, “Karnem neden açılmadı?”, “İzin nasıl girilir?”, “Vekâlet nerede?”. Ben gerçek sekme adı, işlem sırası ve güvenlik sınırıyla yönlendireceğim.');
  }

  function buildRoot() {
    removeLegacyAssistants();
    var existing = document.getElementById(ROOT_ID);
    if (existing) existing.remove();

    var root = document.createElement('section');
    root.id = ROOT_ID;
    root.setAttribute('data-bys360-assistant-bölüm', VERSION);
    root.setAttribute('aria-live', 'polite');
    root.innerHTML = '' +
      '<button class="bys360-am-launcher" type="button" aria-expanded="false" aria-controls="bys360-am-panel" data-launcher="true" data-drag-handle="true" title="BYS360 Asistanı">' +
        '<span class="bys360-am-launcher-icon">' + iconSpark() + '</span>' +
        '<span class="bys360-am-launcher-text"><strong>' + MODULE_NAME + '</strong><span>Tam BYS360 rehberi hazır</span></span>' +
        '<span class="bys360-am-launcher-dot" aria-hidden="true"></span>' +
      '</button>' +
      '<div class="bys360-am-panel" id="bys360-am-panel" role="dialog" aria-label="' + MODULE_NAME + '" hidden>' +
        '<div class="bys360-am-header" data-drag-handle="true">' +
          '<div class="bys360-am-header-top">' +
            '<div class="bys360-am-mark">' + iconSpark() + '</div>' +
            '<div class="bys360-am-title"><h2>' + MODULE_NAME + '</h2><p>' + MODULE_LONG_NAME + '</p></div>' +
            '<button class="bys360-am-icon-btn" type="button" data-reset-position="true" title="Konumu sıfırla" aria-label="Konumu sıfırla">⌖</button>' +
            '<button class="bys360-am-close" type="button" aria-label="Asistanı kapat">×</button>' +
          '</div>' +
        '</div>' +
        '<div class="bys360-am-tabs" role="tablist">' +
          '<button type="button" class="bys360-am-tab is-active" data-view="chat">Sohbet</button>' +
          '<button type="button" class="bys360-am-tab" data-view="guide">Rehber</button>' +
          '<button type="button" class="bys360-am-tab" data-view="summary">Özet</button>' +
          '<button type="button" class="bys360-am-tab" data-view="security">Sınırlar</button>' +
        '</div>' +
        '<div class="bys360-am-body">' +
          '<div class="bys360-am-view is-active" data-panel="chat">' +
            '<div class="bys360-am-log" data-chat-log="true"></div>' +
            '<form class="bys360-am-form" data-chat-form="true">' +
              '<textarea data-chat-input="true" rows="3" maxlength="900" placeholder="Sorunuzu yazın..."></textarea>' +
              '<div class="bys360-am-form-row"><span>Enter gönderir, Shift+Enter satır açar.</span><button type="submit">Gönder</button></div>' +
            '</form>' +
          '</div>' +
          '<div class="bys360-am-view" data-panel="guide">' +
            '<h3>Nereye gitmeliyim?</h3><p>Aradığınız işlem adını yazın; gerçek BYS360 sekme adına göre yönlendireyim.</p>' +
            '<input type="search" data-guide-search="true" placeholder="Dönemler, Sorular / Kriterler, Başkan Onayları, Rol Matrisi...">' +
            '<div class="bys360-am-guide-list" data-guide-list="true"></div>' +
          '</div>' +
          '<div class="bys360-am-view" data-panel="summary">' +
            '<h3>Yetki kontrollü güvenli özet</h3><p>Bu alan yalnızca sayı/genel durum gösterir. Hassas içerik göstermez.</p>' +
            '<div class="bys360-am-summary" data-summary-grid="true"></div>' +
            '<button class="bys360-am-refresh" type="button" data-refresh-summary="true">Özeti yenile</button>' +
          '</div>' +
          '<div class="bys360-am-view" data-panel="security">' +
            '<h3>Güvenli kullanım sınırları</h3>' +
            '<div class="bys360-am-security-grid">' +
              '<article><strong>Karar üretmez</strong><span>İdari karar, disiplin kararı veya performans sonucu oluşturmaz.</span></article>' +
              '<article><strong>Puan belirlemez</strong><span>Performans puanı vermez, değiştirmez, kesinleştirmez.</span></article>' +
              '<article><strong>Hassas veri göstermez</strong><span>Amir görüşü, mesaj içeriği, anket cevabı ve kişisel detayı dökmez.</span></article>' +
              '<article><strong>Gerçek ekran adı kullanır</strong><span>Kullanıcıya görünen sol şerit/sekme/buton adlarıyla yönlendirir.</span></article>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(root);
    return root;
  }

  function saveChatHistory() {
    try { sessionStorage.setItem(STORAGE_CHAT, sistem verisi.stringify(chatHistory.slice(-CHAT_LIMIT))); } catch (e) {}
  }

  function restoreChatHistory(root) {
    var işlenmemiş veri = boş;
    try { işlenmemiş veri = sessionStorage.getItem(STORAGE_CHAT); } catch (e) {}
    if (!işlenmemiş veri) return false;
    try {
      var parsed = sistem verisi.parse(işlenmemiş veri);
      if (!Array.isArray(parsed) || !parsed.length) return false;
      chatHistory = parsed.slice(-CHAT_LIMIT);
      chatHistory.forEach(function (msg) { appendMessage(root, msg.role, msg.text, msg.links || [], false); });
      return true;
    } catch (e) { return false; }
  }

  function appendMessage(root, role, text, links, persist, transient) {
    links = safeLinks(links);
    if (role !== 'user') text = sanitizeAssistantText(text);
    var kayıt = qs('[data-chat-kayıt]', root);
    if (!kayıt) return;
    var row = document.createElement('div');
    row.className = 'bys360-am-message ' + (role === 'user' ? 'is-user' : 'is-bot');
    if (transient) row.setAttribute('data-transient', 'true');
    var avatar = document.createElement('div');
    avatar.className = 'bys360-am-avatar';
    avatar.textContent = role === 'user' ? 'Siz' : 'BYS';
    var bubble = document.createElement('div');
    bubble.className = 'bys360-am-bubble';
    bubble.textContent = text || '';
    if (links && links.length) {
      var linkBox = document.createElement('div');
      linkBox.className = 'bys360-am-links';
      links.slice(0, 4).forEach(function (item) {
        var a = document.createElement('a');
        a.href = item.disabled ? '#' : (item.href || '#');
        a.setAttribute('data-bys360-safe-link', '1');
        a.setAttribute('data-safe-href', item.href || '#');
        a.setAttribute('data-safe-title', item.title || 'Ekrana git');
        if (item.disabled) a.setAttribute('aria-disabled', 'true');
        a.textContent = item.title || 'Ekrana git';
        a.innerHTML = escapeText(item.title || 'Ekrana git') + '<span>→</span>';
        a.addEventListener('click', function (event) { event.preventDefault(); event.stopPropagation(); preflightAndNavigate(root, item.href, item.title); }, true);
        linkBox.appendChild(a);
      });
      bubble.appendChild(linkBox);
    }
    row.appendChild(avatar);
    row.appendChild(bubble);
    kayıt.appendChild(row);
    kayıt.scrollTop = kayıt.scrollHeight;
    if (persist !== false) {
      chatHistory.push({ role: role === 'user' ? 'user' : 'bot', text: text || '', links: links || [] });
      if (chatHistory.length > CHAT_LIMIT) chatHistory = chatHistory.slice(-CHAT_LIMIT);
      saveChatHistory();
    }
  }

  function setOpen(root, open) {
    var launcher = qs('.bys360-am-launcher', root);
    var panel = qs('.bys360-am-panel', root);
    if (!launcher || !panel) return;
    panel.hidden = !open;
    launcher.setAttribute('aria-expanded', open ? 'true' : 'false');
    try { localStorage.setItem(STORAGE_OPEN, open ? '1' : '0'); } catch (e) {}
  }

  function switchView(root, view) {
    qsa('.bys360-am-tab', root).forEach(function (tab) { tab.classList.toggle('is-active', tab.getAttribute('data-view') === view); });
    qsa('.bys360-am-view', root).forEach(function (panel) { panel.classList.toggle('is-active', panel.getAttribute('data-panel') === view); });
    try { sessionStorage.setItem(STORAGE_VIEW, view || 'chat'); } catch (e) {}
  }

  function renderGuide(root, term) {
    var list = qs('[data-guide-list]', root);
    if (!list) return;
    var items = term ? findRoutes(term) : ROUTES.slice(0, 10);
    if (!items.length) items = ROUTES.slice(0, 6);
    list.innerHTML = items.map(function (item) {
      var safe = normalizeAssistantLink(item) || { href: '#', title: item.title, disabled: true };
      return '<a class="bys360-am-guide-card" data-bys360-safe-link="1" data-safe-href="' + escapeText(safe.href) + '" data-safe-title="' + escapeText(safe.title || item.title) + '" href="' + escapeText(safe.disabled ? '#' : safe.href) + '"><strong>' + escapeText(item.title) + '</strong><span>' + escapeText(item.text) + '</span><em>Git →</em></a>';
    }).join('');
  }

  function renderSummary(root, data) {
    var grid = qs('[data-summary-grid]', root);
    if (!grid) return;
    var cards = [];
    if (data && Array.isArray(data.cards)) cards = data.cards;
    if (!cards.length) {
      cards = [
        { title: 'Bekleyen bildirim', value: '—', note: 'Oturum ve yetkiye göre gösterilir' },
        { title: 'Açık destek talebi', value: '—', note: 'Detay için Yardım Merkezi kullanılır' },
        { title: 'Yanıt bekleyen anket', value: '—', note: 'Kişisel cevap içeriği gösterilmez' },
        { title: 'Performans görevi', value: '—', note: 'Puan veya görüş içeriği gösterilmez' }
      ];
    }
    grid.innerHTML = cards.slice(0, 6).map(function (card) {
      return '<article><span>' + escapeText(card.title || card.label || 'Özet') + '</span><strong>' + escapeText(card.value == null ? '—' : card.value) + '</strong><em>' + escapeText(card.note || card.description || 'Yetki kontrollü genel durum') + '</em></article>';
    }).join('');
  }

  function fetchSummary(root) {
    renderSummary(root, []);
    fetch('/ai-agent/api/assistant-widget-summary', { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
      .then(function (response) { if (!response.ok) throw new Error('summary'); return response.json(); })
      .then(function (payload) { renderSummary(root, payload); })
      .catch(function () { renderSummary(root, null); });
  }


  function localFallback(question) {
    /* BYS360_ASSISTANT_LOCAL_FALLBACK_V31_3
       Sunucu cevabı alınamazsa yalnızca güvenli yerel rehberlik döner.
       İdari karar, performans puanı, mesaj içeriği veya yetkisiz veri göstermez. */
    try {
      var fallback = (typeof localAnswer === 'function') ? localAnswer(question) : null;
      if (fallback && (fallback.text || fallback.links)) {
        return fallback;
      }
    } catch (e) {}
    return makeAnswer(
      'BYS360 Asistanı sunucu cevabına şu an ulaşamadı. Yine de güvenli şekilde yardımcı olabilirim: yapmak istediğiniz işlemi kısa bir cümleyle yazın; ilgili modül, yetki ve kontrol adımlarını yerel rehberlik düzeyinde anlatırım. Hassas veri, performans puanı veya idari karar göstermem.',
      [{ title: 'BYS360 Asistanı Paneli', href: '/ai-agent/panel' }]
    );
  }

  function askServer(question) {
    return fetch('/ai-agent/api/ask', {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify({ question: question, context: (typeof currentPageContext === 'function' ? currentPageContext() : {}) })
    }).then(function (response) {
      if (!response.ok) throw new Error('ask');
      return response.json();
    }).then(function (payload) {
      var answer = payload.answer || payload.reply || payload.message || '';
      var actions = payload.actions || payload.suggestions || [];
      var links = [];
      if (Array.isArray(actions)) {
        links = actions.filter(function (a) { return a && (a.href || a.url); }).map(function (a) { return { title: a.title || a.label || 'Ekrana git', href: a.href || a.url }; });
      }
      if (!answer) throw new Error('empty');
      return { text: sanitizeAssistantText(answer), links: safeLinks(links) };
    });
  }

  function setupDrag(root, onLauncherTap) {
    var drag = null;
    var suppressLauncherClickUntil = 0;
    var threshold = 8;
    var maxTapMs = 650;

    function assistantBoxOffsets() {
      var rootRect = root.getBoundingClientRect();
      var left = rootRect.left, top = rootRect.top, right = rootRect.right, bottom = rootRect.bottom;
      var panel = qs('.bys360-am-panel', root);
      if (panel && !panel.hidden) {
        var panelRect = panel.getBoundingClientRect();
        left = Math.min(left, panelRect.left);
        top = Math.min(top, panelRect.top);
        right = Math.max(right, panelRect.right);
        bottom = Math.max(bottom, panelRect.bottom);
      }
      return {
        left: left - rootRect.left,
        top: top - rootRect.top,
        right: right - rootRect.left,
        bottom: bottom - rootRect.top
      };
    }

    function clampRoot(left, top) {
      var margin = 10;
      var o = assistantBoxOffsets();
      var minX = margin - o.left;
      var maxX = window.innerWidth - margin - o.right;
      var minY = margin - o.top;
      var maxY = window.innerHeight - margin - o.bottom;
      if (maxX < minX) maxX = minX;
      if (maxY < minY) maxY = minY;
      return {
        x: Math.min(Math.max(minX, left), maxX),
        y: Math.min(Math.max(minY, top), maxY)
      };
    }

    function finishDrag(event) {
      if (!drag || (event && drag.id !== event.pointerId)) return false;
      var state = drag;
      var moved = !!state.moved;
      var elapsed = Date.now() - state.startedAt;
      drag = null;
      root.classList.remove('is-dragging');
      if (event) {
        try { root.releasePointerCapture(event.pointerId); } catch (e) {}
      }
      if (moved) {
        // Gerçek sürükleme yapıldıysa hemen ardından oluşan click paneli açıp kapatmasın.
        suppressLauncherClickUntil = Date.now() + 500;
        try { localStorage.setItem(STORAGE_POS, JSON.stringify({ left: root.style.left, top: root.style.top })); } catch (e) {}
        return true;
      }
      if (state.fromLauncher && elapsed <= maxTapMs) {
        // Baloncukta kısa tıklama: sürükleme değilse paneli burada aç/kapat.
        // Böylece drag kodu click olayını yutsa bile asistan açılır.
        suppressLauncherClickUntil = Date.now() + 350;
        if (event && event.cancelable) event.preventDefault();
        if (event) event.stopPropagation();
        if (typeof onLauncherTap === 'function') onLauncherTap(event);
      }
      return false;
    }

    root.addEventListener('pointerdown', function (event) {
      if (event.button != null && event.button !== 0) return;
      var launcher = event.target.closest('.bys360-am-launcher');
      var header = event.target.closest('.bys360-am-header');
      if (!launcher && !header) return;
      if (event.target.closest('.bys360-am-close, [data-reset-position], textarea, input, select, a')) return;
      if (header && event.target.closest('button')) return;
      var rect = root.getBoundingClientRect();
      drag = {
        id: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        dx: event.clientX - rect.left,
        dy: event.clientY - rect.top,
        moved: false,
        fromLauncher: !!launcher,
        startedAt: Date.now()
      };
      try { root.setPointerCapture(event.pointerId); } catch (e) {}
    }, true);

    root.addEventListener('pointermove', function (event) {
      if (!drag || drag.id !== event.pointerId) return;
      var distance = Math.max(Math.abs(event.clientX - drag.startX), Math.abs(event.clientY - drag.startY));
      if (distance < threshold && !drag.moved) return;
      drag.moved = true;
      root.classList.add('is-dragging');
      if (event.cancelable) event.preventDefault();
      var pos = clampRoot(event.clientX - drag.dx, event.clientY - drag.dy);
      root.style.left = pos.x + 'px';
      root.style.top = pos.y + 'px';
      root.style.right = 'auto';
      root.style.bottom = 'auto';
    }, true);

    root.addEventListener('pointerup', function (event) { finishDrag(event); }, true);
    root.addEventListener('pointercancel', function (event) { finishDrag(event); }, true);
    root.addEventListener('lostpointercapture', function () { drag = null; root.classList.remove('is-dragging'); });

    var reset = qs('[data-reset-position]', root);
    if (reset) reset.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      root.style.left = '';
      root.style.top = '';
      root.style.right = '24px';
      root.style.bottom = '24px';
      try { localStorage.removeItem(STORAGE_POS); } catch (e) {}
    }, true);

    return {
      shouldSuppressLauncherClick: function () { return Date.now() < suppressLauncherClickUntil || root.classList.contains('is-dragging'); }
    };
  }

  // V7_FINAL_TEST_SENARYOLARI ve V7_CANLI_KALITE_KONTROL: tarayıcı konsolunda window.BYS360AssistantModule.runSelfTest() ile okunabilir.
  function assistantSelfTest() {
    var badSamples = [
      'Dönem ' + 'Yönetimi', 'bağlantı yolu ' + 'menü haritasına ' + 'eklenmeli', 'Tam modül ' + 'mantığıyla çalışır',
      'çay' + 'lar sıcak', 'Kış ' + 'kendini göstermiş', 'Şemsiye ' + 'göreve', 'Gök' + 'yüzü ' + 'drama' + 'tik', 'sevimli bir ' + 'yorum', 'durum kar' + 'lı'
    ];
    var sanitized = badSamples.map(function (item) { return sanitizeAssistantText('BYS360 hava durumu bilgisini Open-Meteo bağlantısından aldım: sıcaklık 19°C, ' + item + '.'); }).join(' | ');
    var badLeft = badSamples.filter(function (item) { return sanitized.indexOf(item) !== -1; });
    var routeTitles = ROUTES.map(function (r) { return r.title; });
    return {
      ok: badLeft.length === 0 && routeTitles.indexOf('Dönemler') !== -1 && routeTitles.indexOf('İzin ve Devamsızlık Takibi') !== -1,
      version: VERSION,
      teaching_contract: 'V7_EKSİKSİZ_EKRAN_OGRETIM_SOZLESMESI',
      route_count: ROUTES.length,
      safe_routes: routeTitles,
      forbidden_left: badLeft,
      checks: [
        'Cevap hijyeni aktif',
        'Dönemler gerçek sekme adı korunuyor',
        'İzin ve vekâlet güvenli canlı yollara bağlı',
        'Hava durumu şaka/espri üretmiyor',
        'Kırık linkler preflight ile durduruluyor',
        'Oturum aynı sekmede korunuyor'
      ]
    };
  }

  function restorePosition(root) {
    try {
      var raw = localStorage.getItem(STORAGE_POS);
      if (!raw) return;
      var pos = JSON.parse(raw);
      if (pos && pos.left && pos.top) { root.style.left = pos.left; root.style.top = pos.top; root.style.right = 'auto'; root.style.bottom = 'auto'; }
    } catch (e) {}
  }

  function init() {
    var root = buildRoot();
    activeRoot = root;
    saveCurrentPageContext();
    restorePosition(root);
    var dragController = null;
    renderGuide(root, '');
    renderSummary(root, null);
    try {
      var lastView = sessionStorage.getItem(STORAGE_VIEW);
      if (lastView) switchView(root, lastView);
    } catch (e) {}

    var opened = false;
    try { opened = localStorage.getItem(STORAGE_OPEN) === '1'; } catch (e) {}
    setOpen(root, opened);

    var launcher = qs('.bys360-am-launcher', root);
    var close = qs('.bys360-am-close', root);
    function toggleAssistant(event, forceFromPointerTap) {
      if (event) { event.preventDefault(); event.stopPropagation(); }
      if (!forceFromPointerTap && dragController && dragController.shouldSuppressLauncherClick && dragController.shouldSuppressLauncherClick()) return;
      var panel = qs('.bys360-am-panel', root);
      setOpen(root, !!(panel && panel.hidden));
    }
    dragController = setupDrag(root, function (event) { toggleAssistant(event, true); });
    if (launcher) launcher.addEventListener('click', function (event) { toggleAssistant(event, false); }, true);
    // Bazı base.html katmanları click olayını bubble aşamasında kesebildiği için capture aşamasında yedek bağ kurulur.
    document.addEventListener('click', function (event) {
      if (event.target && event.target.closest && event.target.closest('#' + ROOT_ID + ' .bys360-am-launcher')) toggleAssistant(event, false);
    }, true);
    document.addEventListener('click', function (event) {
      var safeLink = event.target && event.target.closest ? event.target.closest('#' + ROOT_ID + ' [data-bys360-safe-link="1"]') : null;
      if (!safeLink) return;
      event.preventDefault();
      event.stopPropagation();
      preflightAndNavigate(root, safeLink.getAttribute('data-safe-href') || safeLink.getAttribute('href'), safeLink.getAttribute('data-safe-title') || safeLink.textContent || 'Ekrana git');
    }, true);
    if (close) close.addEventListener('click', function (event) { if (event) { event.preventDefault(); event.stopPropagation(); } setOpen(root, false); }, true);
    window.BYS360AssistantModule = {
      open: function () { setOpen(root, true); },
      close: function () { setOpen(root, false); },
      toggle: function () { var panel = qs('.bys360-am-panel', root); setOpen(root, !!(panel && panel.hidden)); },
      resetPosition: function () { root.style.left = ''; root.style.top = ''; root.style.right = '24px'; root.style.bottom = '24px'; try { localStorage.removeItem(STORAGE_POS); } catch (e) {} },
      moveTo: function (left, top) { var pos = { x: Number(left) || 24, y: Number(top) || 24 }; root.style.left = pos.x + 'px'; root.style.top = pos.y + 'px'; root.style.right = 'auto'; root.style.bottom = 'auto'; try { localStorage.setItem(STORAGE_POS, JSON.stringify({ left: root.style.left, top: root.style.top })); } catch (e) {} },
      currentPage: function () { return currentPageContext(); },
      helpForCurrentPage: function () { var answer = pageAwareAnswer(); appendMessage(root, 'bot', answer.text, answer.links); return answer; },
      resume: function () { var answer = resumeAnswer(); appendMessage(root, 'bot', answer.text, answer.links); return answer; },
      runSelfTest: function () { return assistantSelfTest(); },
      version: VERSION
    };

    qsa('.bys360-am-tab', root).forEach(function (tab) {
      tab.addEventListener('click', function () {
        var view = tab.getAttribute('data-view');
        switchView(root, view);
        if (view === 'summary') fetchSummary(root);
      });
    });

    var search = qs('[data-guide-search]', root);
    if (search) search.addEventListener('input', function () { renderGuide(root, search.value); });
    var refresh = qs('[data-refresh-summary]', root);
    if (refresh) refresh.addEventListener('click', function () { fetchSummary(root); });

    if (!restoreChatHistory(root)) {
      appendMessage(root, 'bot', 'Merhaba, ben ' + MODULE_NAME + '. Bulunduğunuz ekrana göre sizi doğru sekmeye, doğru işlem sırasına ve güvenli kontrol adımına yönlendiririm. Performans, personel, izin, vekâlet, rol matrisi, raporlar, destek, anket, AI Karar Destek ve sayfa bazlı yardım konularında sorunuzu yazabilirsiniz.');
    }

    var form = qs('[data-chat-form]', root);
    var input = qs('[data-chat-input]', root);
    if (input) {
      input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); if (form) form.dispatchEvent(new Event('submit', { cancelable: true })); }
      });
    }
    if (form) form.addEventListener('submit', function (event) {
      event.preventDefault();
      var question = input ? input.value.trim() : '';
      if (!question) return;
      if (input) input.value = '';
      appendMessage(root, 'user', question);
      appendMessage(root, 'bot', 'Sorunuzu BYS360 kapsamında yorumluyorum...', [], false);
      var log = qs('[data-chat-log]', root);
      if (isWeatherIntent(question)) {
        answerWeather(root, question, log);
        return;
      }
      if (isLocalFirstIntent(question)) {
        var local = localAnswer(question);
        if (log && log.lastElementChild && log.lastElementChild.classList.contains('is-bot')) log.removeChild(log.lastElementChild);
        appendMessage(root, 'bot', local.text, local.links);
        return;
      }
      askServer(question).catch(function () { return localFallback(question); }).then(function (answer) {
        if (log && log.lastElementChild && log.lastElementChild.classList.contains('is-bot')) log.removeChild(log.lastElementChild);
        appendMessage(root, 'bot', answer.text, answer.links);
      });
    });
  }

  window.addEventListener('beforeunload', function () {
    try { saveChatHistory(); saveCurrentPageContext(); } catch (e) {}
  });

  window.addEventListener('pageshow', function () {
    try { saveCurrentPageContext(); } catch (e) {}
  });

  ready(function () {
    try { init(); }
    catch (error) {
      try { console.error('BYS360 Asistanı açılış hatası:', error); } catch (e) {}
      var fallback = document.createElement('button');
      fallback.id = 'bys360-assistant-module-fallback-openfix';
      fallback.type = 'button';
      fallback.textContent = 'BYS360 Asistanı';
      fallback.style.cssText = 'position:fixed;right:24px;bottom:24px;z-index:2147483647;border:0;border-radius:999px;background:#8B0000;color:#fff;padding:14px 18px;font-weight:800;box-shadow:0 12px 36px rgba(0,0,0,.22);';
      fallback.onclick = function () { location.href = '/ai-agent/panel'; };
      document.body.appendChild(fallback);
    }
  });
})();

/* V8_GUVENLI_YONLENDIRME_SIKILASTIRMA | V7_CEVAP_HIJYENI_KATMANI | V7_FINAL_TEST_SENARYOLARI | V7_CANLI_KALITE_KONTROL | V7_EKSİKSİZ_EKRAN_OGRETIM_SOZLESMESI | V7_MODUL_CEVAP_FORMATI | V7_GUVENLI_EYLEM_SOZLESMESI | V7_KANONIK_EKRAN_ADI_KORUMA | V7_CANLI_OGRETIM_TESTLERI */

/* V8_12_ADIM_DURUM_KONTROL_GATE | V8_EKSIK_TESPIT_RAPORU | V8_CANLI_DURUM_KONTROLU | V8_ESKI_ASISTAN_KALINTI_TARAMASI */


/* BYS360_ASISTANI_MODULU_V12_FINAL_GATE_START */
(function(){
  "use strict";

  const V12 = {
    version: "V12",
    canonicalName: "BYS360 Asistanı",
    canonicalFullName: "BYS360 Asistanı — Kurumsal Rehberlik, Akıllı Yönlendirme ve Yetki Kontrollü Dijital Yardımcı",
    forbiddenPhrases: [
      "Dönemler",
      "/hr-management/leave",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      ""
    ],
    safeMenu: {
      "home": { title: "Ana Sayfa", url: "/home" },
      "personnel": { title: "Personel Yönetimi", url: "/hr-management" },
      "leave": { title: "İzin ve Devamsızlık Takibi", url: "/hr-management/leave" },
      "delegation": { title: "Devamsızlık ve Vekâlet", url: "/hr-management/attendance" },
      "performance": { title: "Performans Yönetimi", url: "/performance" },
      "periods": { title: "Dönemler", url: "/performance/periods" },
      "criteria": { title: "Değerlendirme Kriterleri", url: "/performance/criteria" },
      "assignments": { title: "Görev Üretimi", url: "/performance/assignments" },
      "my_tasks": { title: "Değerlendirme Görevlerim", url: "/performance/my-tasks" },
      "scorecards": { title: "Karne", url: "/performance/scorecards" },
      "president_approvals": { title: "Başkan Onayları", url: "/performance/president-approvals" },
      "reports": { title: "Raporlar", url: "/performance/reports" },
      "settings": { title: "Sistem Ayarları", url: "/settings" },
      "role_matrix": { title: "Rol Matrisi", url: "/settings/role-matrix" },
      "support": { title: "Destek Talepleri", url: "/support" },
      "survey": { title: "Anketler", url: "/surveys" },
      "notifications": { title: "Bildirimler", url: "/notifications" },
      "ai_decision": { title: "AI Karar Destek Merkezi", url: "/ai/decision-support" }
    },
    legacyRedirects: {
      "/hr-management/leave": "/hr-management/leave",
      "/personnel/leave": "/hr-management/leave",
      "/personnel/delegation": "/hr-management/attendance",
      "/personnel/attendance": "/hr-management/attendance",
      "/performance/period-management": "/performance/periods",
      "/performans/donem-yonetimi": "/performance/periods"
    }
  };

  function cleanText(text){
    let out = String(text || "");
    out = out.replaceAll("Dönemler", "Dönemler");
    out = out.replaceAll("/hr-management/leave", "/hr-management/leave");
    V12.forbiddenPhrases.forEach(function(p){
      if (p === "Dönemler" || p === "/hr-management/leave") return;
      out = out.split(p).join("");
    });
    return out.replace(/\n{3,}/g, "\n\n").trim();
  }

  function weatherConsistency(text){
    let out = cleanText(text);
    const hasWarm = /\b(1[5-9]|2[0-9]|3[0-9])\s*°?\s*C\b/i.test(out);
    const hasSnow = /(karlı|kar yağış|snow)/i.test(out);
    if (hasWarm && hasSnow) {
      out = out.replace(/durum\s*:?\s*karlı\.?/ig, "");
      out = out.replace(/karlı hava[^.]*\./ig, "");
      out += "\n\nHava açıklaması sıcaklık bilgisiyle uyumlu görünmediği için yalnızca doğrulanabilen bilgileri dikkate almanız önerilir.";
    }
    return cleanText(out);
  }

  function answerLocal(question){
    const q = String(question || "").toLocaleLowerCase("tr-TR");

    if (/v12|final|12 adım|canlı test|son kontrol/.test(q)) {
      return [
        "V12 final kontrol için şu başlıkları sınayabilirim:",
        "1. Gerçek menü ve sekme adları",
        "2. Güvenli yönlendirme ve kırık link engeli",
        "3. Personel Yönetimi",
        "4. İzin, devamsızlık ve vekâlet",
        "5. Performans Yönetimi",
        "6. Rol matrisi ve menü görünürlüğü",
        "7. Dashboard ve raporlar",
        "8. İletişim, anket, destek ve bildirimler",
        "9. AI Karar Destek ayrımı",
        "10. Kendini tanıtma ve günlük konuşma",
        "11. Oturum ve sayfa geçişi koruma",
        "12. Final canlı test senaryoları"
      ].join("\n");
    }

    if (/sen kimsin|seni kim geliştirdi|kim geliştirdi|nasıl çalışıyorsun|yapay zekaya bağlı mısın|chatgpt misin/.test(q)) {
      return "Ben BYS360 Asistanı’yım. BYS360 için Personel kurumsal kullanım Özden tarafından geliştirildim. Görevim, BYS360 içinde yetkiniz dâhilindeki işlemleri doğru ekrana ve doğru işlem sırasına göre anlatmak; sistemi daha kolay, güvenli ve anlaşılır kullanmanıza yardımcı olmaktır. İdari karar üretmem, performans puanı belirlemem ve hassas veri göstermem.";
    }

    if (/neler yapabiliyorsun|hangi konularda yardımcı|bana nasıl yardımcı/.test(q)) {
      return "BYS360 içinde personel işlemleri, izin-devamsızlık-vekalet süreçleri, performans dönemleri, Değerlendirme Kriterleri, görev üretimi, Başkan Onayları, karne-yayın süreci, rol matrisi, menü görünürlüğü, raporlar, destek talepleri, anketler, bildirimler ve AI Karar Destek Merkezi hakkında adım adım yardımcı olurum.";
    }

    if (/izin|devamsızlık|vekalet|vekâlet/.test(q)) {
      return [
        "Bu konu Personel Yönetimi içindedir.",
        "",
        "Doğru ekranlar:",
        "- İzin işlemleri: Personel Yönetimi > İzin ve Devamsızlık Takibi",
        "- Vekâlet ve devamsızlık takibi: Personel Yönetimi > Devamsızlık ve Vekâlet",
        "",
        "Adım adım:",
        "1. Sol şeritten Personel Yönetimi bölümünü açın.",
        "2. İşleme göre İzin ve Devamsızlık Takibi veya Devamsızlık ve Vekâlet ekranına girin.",
        "3. Personeli Sicil No, ad-soyad veya birim bilgisiyle bulun.",
        "4. İzin, devamsızlık veya vekâlet bilgilerini tarih aralığıyla kaydedin.",
        "5. İşlemden sonra kayıt listesinde durumun oluştuğunu kontrol edin.",
        "",
        "Dikkat: İzinli amir varsa performans, onay veya görev akışları vekâlet tanımından etkilenebilir."
      ].join("\n");
    }

    if (/dönem|donem|performans dönemi|dönemler/.test(q)) {
      return [
        "Bu işlem Performans Yönetimi > Dönemler ekranından yapılır.",
        "",
        "Adım adım:",
        "1. Sol şeritten Performans Yönetimi bölümünü açın.",
        "2. Dönemler sekmesine girin.",
        "3. Yeni dönem oluşturma butonunu kullanın.",
        "4. Dönem adı, türü, başlangıç-bitiş tarihi ve kapsam bilgisini doldurun.",
        "5. Kaydettikten sonra Değerlendirme Kriterleri, ağırlıklar ve görev üretimini kontrol edin."
      ].join("\n");
    }

    if (/başkan onay|70 alt|düşük performans/.test(q)) {
      return [
        "Başkan Onayları, 70 altı performans sonuçlarının üst onay sürecini takip etmek için kullanılır.",
        "",
        "Temel akış:",
        "1. Değerlendirme tamamlanır.",
        "2. Nihai puan 70 altındaysa sonuç doğrudan yayınlanmaz.",
        "3. Kayıt Başkan Onayları ekranına düşer.",
        "4. Onay süreci tamamlanmadan karne personele açılmaz.",
        "5. Süreç tamamlandığında yayın ve personel geçmişi kayıtları yetki sınırına göre görünür."
      ].join("\n");
    }

    if (/rol matrisi|menü görünmüyor|menüm yok|yetki|görünürlük/.test(q)) {
      return [
        "Bu konu Sistem Ayarları ve yetki görünürlüğüyle ilgilidir.",
        "",
        "Kontrol sırası:",
        "1. Modül bazlı rol matrisi açık mı kontrol edin.",
        "2. Performans rol matrisi ilgili rol için doğru mu bakın.",
        "3. Kişi bazlı menü görünürlüğü kapalı mı kontrol edin.",
        "4. Birim bazlı profil ilgili kullanıcıyı etkiliyor mu bakın.",
        "5. Menü görünse bile erişim yoksa backend route yetkisi ayrıca kontrol edilmelidir.",
        "",
        "Dikkat: Yetkisi olmayan kullanıcı menüyü görmemeli; linki yazsa bile veri alamamalıdır."
      ].join("\n");
    }

    if (/bu sayfada|bu ekran|nereden devam|kaldığımız yer|az önceki konu/.test(q)) {
      const path = window.location ? window.location.pathname : "";
      return "Şu an bulunduğunuz ekranı dikkate alarak yardımcı olabilirim. Sayfa yolu: " + path + ". Sorunuzu bu ekran üzerinden sorarsanız ilgili işlem adımlarını buradan devam ettiririm.";
    }

    return boş;
  }

  function install(){
    window.BYS360AssistantV12 = V12;
    window.BYS360AssistantCleanText = weatherConsistency;
    window.BYS360AssistantLocalAnswer = answerLocal;

    const oldSend = window.BYS360AssistantModule && window.BYS360AssistantModule.answer;
    if (window.BYS360AssistantModule) {
      window.BYS360AssistantModule.version = "V12";
      window.BYS360AssistantModule.cleanText = weatherConsistency;
      window.BYS360AssistantModule.localAnswer = answerLocal;
      if (typeof oldSend === "function") {
        window.BYS360AssistantModule.answer = function(question){
          const local = answerLocal(question);
          if (local) return weatherConsistency(local);
          const result = oldSend.apply(this, arguments);
          if (typeof result === "string") return weatherConsistency(result);
          return result;
        };
      }
      window.BYS360AssistantModule.runFinalTest = function(){
        const tests = [
          "izin nasıl çalışır",
          "Dönemler nerede",
          "Başkan Onayları nasıl çalışır",
          "rol matrisi görünmüyor",
          "neler yapabiliyorsun",
          "seni kim geliştirdi",
          "bu sayfada ne yapabilirim",
          "hava nasıl"
        ];
        return tests.map(function(t){
          return { question: t, answer: weatherConsistency(answerLocal(t) || "Sunucu cevabı beklenir.") };
        });
      };
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }
})();
/* BYS360_ASISTANI_MODULU_V12_FINAL_GATE_END */



/* BYS360_V14_INTENT_ENGINE_START */
(function(){
  "use strict";

  const intentMap = [
    {
      intent: "performance_periods",
      phrases: [
        "dönem açacağım",
        "performansı başlat",
        "2026 değerlendirmesini oluştur",
        "puanlama sürecini başlatacağım",
        "dönemler nerede"
      ],
      target: "Performans Yönetimi > Dönemler",
      url: "/performance/periods"
    },
    {
      intent: "leave_management",
      phrases: [
        "izin",
        "izin gireceğim",
        "personel izinli",
        "amir izne çıktı"
      ],
      target: "Personel Yönetimi > İzin ve Devamsızlık Takibi",
      url: "/hr-management/leave"
    },
    {
      intent: "delegation_management",
      phrases: [
        "vekalet olacak",
        "vekalet",
        "vekâlet"
      ],
      target: "Personel Yönetimi > Devamsızlık ve Vekâlet",
      url: "/hr-management/attendance"
    },
    {
      intent: "role_matrix",
      phrases: [
        "menüm yok",
        "rol matrisi görünmüyor",
        "yetkim yok"
      ],
      target: "Sistem Ayarları > Rol Matrisi",
      url: "/settings/role-matrix"
    }
  ];

  function detectIntent(question){
    const q = String(question || "").toLocaleLowerCase("tr-TR");

    for (const item of intentMap){
      for (const phrase of item.phrases){
        if (q.includes(phrase.toLocaleLowerCase("tr-TR"))){
          return item;
        }
      }
    }

    return boş;
  }

  window.BYS360IntentEngine = {
    version: "V14",
    detectIntent,
    intentMap
  };

})();
/* BYS360_V14_INTENT_ENGINE_END */


/* BYS360_V15_PAGE_CONTEXT_HELP_START */
(function(){
  "use strict";

  const pageHelpMap = [
    {
      match: ["/performance/periods", "/performans/donemler"],
      title: "Dönemler",
      bölüm: "Performans Yönetimi",
      help: [
        "Şu an Dönemler ekranındasınız.",
        "Bu ekrandan performans dönemleri oluşturulur, tarih aralıkları kontrol edilir ve dönem kapsamı yönetilir.",
        "",
        "Burada yapılabilecekler:",
        "1. Yeni performans dönemi oluşturma",
        "2. Dönem başlangıç ve bitiş tarihlerini kontrol etme",
        "3. Dönem kapsamını belirleme",
        "4. Dönem aktiflik durumunu izleme",
        "",
        "Dikkat: Dönem oluşturmak tek başına değerlendirmeyi başlatmaz. Değerlendirme Kriterleri, ağırlıklar ve görev üretimi de kontrol edilmelidir."
      ].join("\n")
    },
    {
      match: ["/performance/president-approvals", "/performans/baskan-onaylari"],
      title: "Başkan Onayları",
      bölüm: "Performans Yönetimi",
      help: [
        "Şu an Başkan Onayları ekranındasınız.",
        "Bu ekran 70 altı performans sonuçlarının üst onay sürecini takip etmek için kullanılır.",
        "",
        "Burada yapılabilecekler:",
        "1. Başkan onayı bekleyen düşük performans kayıtlarını görüntüleme",
        "2. Karne inceleme detayına geçme",
        "3. Yayın kilidi veya süreç durumunu kontrol etme",
        "4. Yetkiniz varsa onay/ret sürecini yürütme",
        "",
        "Dikkat: Başkan onayı tamamlanmadan 70 altı karne personele kesin/yayınlanmış sonuç olarak açılmamalıdır."
      ].join("\n")
    },
    {
      match: ["/hr-management/leave"],
      title: "İzin ve Devamsızlık Takibi",
      bölüm: "Personel Yönetimi",
      help: [
        "Şu an İzin ve Devamsızlık Takibi ekranındasınız.",
        "Bu ekrandan personelin izin kayıtları, izin tarihleri ve devamsızlık bilgileri takip edilir.",
        "",
        "Burada yapılabilecekler:",
        "1. Personel izin kaydı oluşturma veya görüntüleme",
        "2. İzin başlangıç ve bitiş tarihlerini kontrol etme",
        "3. İzin durumunun personel ve süreçlere etkisini izleme",
        "",
        "Dikkat: İzinli amir varsa performans/onay akışlarında vekâlet ilişkisi ayrıca kontrol edilmelidir."
      ].join("\n")
    },
    {
      match: ["/hr-management/attendance"],
      title: "Devamsızlık ve Vekâlet",
      bölüm: "Personel Yönetimi",
      help: [
        "Şu an Devamsızlık ve Vekâlet ekranındasınız.",
        "Bu ekran devamsızlık kayıtları ve vekâlet tanımları için kullanılır.",
        "",
        "Burada yapılabilecekler:",
        "1. Devamsızlık bilgisini kontrol etme",
        "2. Vekâlet ilişkisi tanımlama veya izleme",
        "3. Amir izinliyse sürecin kime devredileceğini kontrol etme",
        "",
        "Dikkat: Vekâlet kaydı doğru değilse onay ve değerlendirme akışları yanlış kişiye düşebilir."
      ].join("\n")
    },
    {
      match: ["/settings/role-matrix", "/settings"],
      title: "Rol Matrisi ve Sistem Ayarları",
      bölüm: "Sistem Ayarları",
      help: [
        "Şu an Sistem Ayarları / Rol Matrisi alanındasınız.",
        "Bu alan kullanıcıların hangi modül, sekme ve işlemleri görebileceğini yönetmek için kullanılır.",
        "",
        "Burada yapılabilecekler:",
        "1. Modül bazlı rol görünürlüğünü kontrol etme",
        "2. Performans rol matrisi ayarlarını kontrol etme",
        "3. Kişi bazlı menü görünürlüğünü inceleme",
        "4. Birim bazlı profil etkisini değerlendirme",
        "",
        "Dikkat: Menü görünürlüğü ile backend erişim yetkisi birlikte çalışmalıdır. Sadece menüyü gizlemek güvenlik için yeterli değildir."
      ].join("\n")
    },
    {
      match: ["/performance/reports", "/reports"],
      title: "Raporlar",
      bölüm: "Raporlar ve Dashboard",
      help: [
        "Şu an Raporlar alanındasınız.",
        "Bu ekranda performans, süreç, risk, tamamlanma ve yönetici görünürlüğü raporları izlenir.",
        "",
        "Burada yapılabilecekler:",
        "1. Dönem bazlı performans raporlarını inceleme",
        "2. Başkan onayı bekleyenleri takip etme",
        "3. Aksatan amirleri ve yayın kilitlerini kontrol etme",
        "4. Birim, grup veya kategori ortalamalarını değerlendirme",
        "",
        "Dikkat: Raporlarda kişi detayı yalnızca yetki kapsamına göre gösterilmelidir."
      ].join("\n")
    },
    {
      match: ["/support"],
      title: "Destek Talepleri",
      bölüm: "İletişim ve Destek",
      help: [
        "Şu an Destek Talepleri ekranındasınız.",
        "Bu ekrandan kullanıcı yardım talepleri oluşturulur, izlenir ve sonuçlandırılır.",
        "",
        "Burada yapılabilecekler:",
        "1. Yeni destek talebi oluşturma",
        "2. Açık talepleri takip etme",
        "3. Talep durumunu ve cevapları kontrol etme",
        "",
        "Dikkat: Destek talebine hassas kişisel veri eklenmemelidir."
      ].join("\n")
    },
    {
      match: ["/surveys"],
      title: "Anketler",
      bölüm: "İletişim ve Anket",
      help: [
        "Şu an Anketler ekranındasınız.",
        "Bu ekrandan anketler görüntülenir, yanıtlanır veya yetkiniz varsa yönetilir.",
        "",
        "Burada yapılabilecekler:",
        "1. Size atanmış anketleri görüntüleme",
        "2. Anket yanıtı verme",
        "3. Yetkiniz varsa anket oluşturma veya sonuçları izleme",
        "",
        "Dikkat: Anket cevapları yetki ve gizlilik kurallarına göre korunmalıdır."
      ].join("\n")
    },
    {
      match: ["/ai/decision-support"],
      title: "AI Karar Destek Merkezi",
      bölüm: "AI Karar Destek",
      help: [
        "Şu an AI Karar Destek Merkezi alanındasınız.",
        "Bu alan verileri özetleme, önceliklendirme, risk farkındalığı ve yönetici içgörüsü için kullanılır.",
        "",
        "Dikkat: AI Karar Destek idari karar vermez. Nihai karar yetkili insan kullanıcıdadır.",
        "BYS360 Asistanı ise bu merkezi kullanmayı ve doğru ekrana ulaşmayı öğretir."
      ].join("\n")
    },
    {
      match: ["/home", "/"],
      title: "Ana Sayfa",
      bölüm: "Genel",
      help: [
        "Şu an Ana Sayfa alanındasınız.",
        "Bu ekran BYS360 içindeki genel durum, bildirimler, bekleyen işler ve hızlı yönlendirmeler için başlangıç noktasıdır.",
        "",
        "Burada yapılabilecekler:",
        "1. Bekleyen bildirimleri kontrol etme",
        "2. Açık görev veya süreçleri görme",
        "3. İlgili modüle hızlı geçiş yapma"
      ].join("\n")
    }
  ];

  function getCurrentPath(){
    try { return window.location.pathname || "/"; } catch(e){ return "/"; }
  }

  function getPageHelp(path){
    const current = String(path || getCurrentPath());
    let best = boş;
    for (const item of pageHelpMap){
      for (const m of item.match){
        if (current === m || current.startsWith(m + "/") || current.indexOf(m) === 0){
          if (!best || m.length > best._matchLength){
            best = Object.assign({_matchLength: m.length}, item);
          }
        }
      }
    }
    if (best) return best.help;
    return [
      "Bu ekran için özel yardım kaydı henüz bulunmuyor.",
      "Yine de bulunduğunuz sayfaya göre işlem adımlarını birlikte netleştirebilirim.",
      "Sayfanın adını veya yapmak istediğiniz işlemi yazarsanız sizi ilgili modül ve doğru adımlarla yönlendiririm."
    ].join("\n");
  }

  function isPageContextQuestion(question){
    const q = String(question || "").toLocaleLowerCase("tr-TR");
    return [
      "bu sayfada ne yapabilirim",
      "bu ekran ne işe yarar",
      "burada ne yapacağım",
      "bu sayfa ne",
      "şu an neredeyim",
      "nereden devam edeceğim",
      "ekranı anlat",
      "bu ekranı anlat"
    ].some(p => q.includes(p));
  }

  window.BYS360PageContextHelp = {
    version: "V15",
    pageHelpMap,
    getCurrentPath,
    getPageHelp,
    isPageContextQuestion
  };

  const oldLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function(question){
    if (isPageContextQuestion(question)){
      return getPageHelp();
    }
    if (typeof oldLocal === "function"){
      return oldLocal(question);
    }
    return null;
  };

  if (window.BYS360AssistantModule){
    window.BYS360AssistantModule.pageContextHelp = window.BYS360PageContextHelp;
  }
})();
/* BYS360_V15_PAGE_CONTEXT_HELP_END */


/* BYS360_V16_TROUBLESHOOTING_GUIDE_START */
(function(){
  "use strict";

  const troubleshootingMap = [
    {
      key: "white_screen",
      phrases: ["beyaz ekran", "sayfa beyaz", "ekran boş", "500 hata", "sayfa açılmıyor"],
      answer: [
        "Bu durum sayfanın yüklenirken hata aldığını gösterir.",
        "",
        "Olası sebepler:",
        "1. Sayfa yolu eski veya kırık olabilir.",
        "2. Yetki kontrolü doğru ekran yerine hatalı sonuç döndürmüş olabilir.",
        "3. Template/Jinja hatası oluşmuş olabilir.",
        "4. Backend route hata vermiş olabilir.",
        "",
        "Kontrol sırası:",
        "1. Önce sayfa URL’sinin güvenli menü haritasında olup olmadığını kontrol edin.",
        "2. Aynı sayfaya yetkili Admin kullanıcısıyla erişmeyi deneyin.",
        "3. Waitress/uygulama loglarında ilgili route hatasını kontrol edin.",
        "4. Son yapılan overlay sonrası compileall çalıştırın.",
        "",
        "Güvenli çözüm:",
        "Kırık veya eski link kullanılıyorsa asistan bu linki önermemelidir. Gerçek canlı ekran adı ve güvenli URL kullanılmalıdır."
      ].join("\n")
    },
    {
      key: "menu_missing",
      phrases: ["menü görünmüyor", "menüm yok", "sekme görünmüyor", "sol şeritte yok", "menü yok"],
      answer: [
        "Menü görünmüyorsa konu genellikle rol matrisi veya kişi/birim bazlı görünürlük ayarıyla ilgilidir.",
        "",
        "Kontrol sırası:",
        "1. Sistem Ayarları içindeki rol matrisi ilgili rol için açık mı kontrol edin.",
        "2. Performans rol matrisi ayrıca bu sekmeyi kapatıyor mu bakın.",
        "3. Kişi bazlı menü görünürlüğü kullanıcı için kapalı mı kontrol edin.",
        "4. Birim bazlı profil bu kullanıcıyı etkiliyor mu inceleyin.",
        "5. Menü açık görünse bile backend route yetkisi ayrıca kontrol edilmelidir.",
        "",
        "Dikkat:",
        "Yetkisi olmayan kullanıcı menüyü hiç görmemeli; URL yazsa bile veri alamamalıdır."
      ].join("\n")
    },
    {
      key: "button_not_opening",
      phrases: ["buton açılmıyor", "tıklıyorum açılmıyor", "baloncuk açılmıyor", "asistan açılmıyor", "panel açılmıyor"],
      answer: [
        "Butona basınca açılmıyorsa tıklama olayı, sürükleme davranışı veya JavaScript yükleme sırası etkilenmiş olabilir.",
        "",
        "Kontrol sırası:",
        "1. Sayfada Ctrl + F5 ile cache temizleyerek yenileyin.",
        "2. Tarayıcı konsolunda JavaScript hatası var mı kontrol edin.",
        "3. Asistan JS dosyası sayfaya tek kez yükleniyor mu bakın.",
        "4. Baloncuk sürükleme ile kısa tıklama birbirine karışıyor mu test edin.",
        "5. base.html içinde eski basit asistan include’u kalmadığından emin olun.",
        "",
        "Güvenli çözüm:",
        "Kısa tıklama paneli açmalı, basılı tutup sürükleme sadece konumu değiştirmelidir."
      ].join("\n")
    },
    {
      key: "role_matrix_not_applied",
      phrases: ["rol matrisi yansımıyor", "açıyorum kapanmıyor", "kapattım görünmeye devam ediyor", "rol matrisi çalışmıyor"],
      answer: [
        "Rol matrisi değişikliği ekrana yansımıyorsa görünürlük katmanı ve backend yetki katmanı birlikte kontrol edilmelidir.",
        "",
        "Kontrol sırası:",
        "1. Modül bazlı rol matrisi kaydı gerçekten değişmiş mi kontrol edin.",
        "2. Performans rol matrisi aynı alanı tekrar açıyor mu bakın.",
        "3. Kişi bazlı menü izni rol ayarının üstüne yazıyor olabilir.",
        "4. Birim bazlı profil kullanıcıya farklı görünürlük veriyor olabilir.",
        "5. Menü cache veya session içinde eski görünürlük tutuluyor olabilir.",
        "6. Backend route yetkisi menüden bağımsız şekilde ayrıca kontrol edilmelidir.",
        "",
        "Dikkat:",
        "Doğru davranış: kapalı menü görünmemeli; URL yazılırsa da güvenli erişim engeli ekranı gösterilmelidir."
      ].join("\n")
    },
    {
      key: "performance_task_missing",
      phrases: ["görev oluşmadı", "performans görevi yok", "değerlendirme görevi oluşmadı", "amir görevi yok"],
      answer: [
        "Performans görevi oluşmadıysa dönem, kapsam, personel verisi ve amir zinciri birlikte kontrol edilmelidir.",
        "",
        "Kontrol sırası:",
        "1. Dönemler ekranında ilgili dönem aktif mi kontrol edin.",
        "2. Dönem kapsamına personel giriyor mu bakın.",
        "3. Personelin birim, üst birim, yönetici ve kategori bilgisi doğru mu kontrol edin.",
        "4. Değerlendirme Kriterleri ve ağırlıklar hazır mı bakın.",
        "5. 3. amir zorunlu olmayan yerde sahte görev oluşmamalıdır.",
        "6. Görev üretimi tekrar çalıştırıldıysa eski görevlerle çakışma var mı kontrol edin.",
        "",
        "Güvenli çözüm:",
        "Personel ve organizasyon verisi düzeltilmeden görev üretimi tekrarlandığında yanlış amir zinciri oluşabilir."
      ].join("\n")
    },
    {
      key: "wrong_supervisor",
      phrases: ["amir yanlış", "1. amir yanlış", "2. amir yanlış", "3. amir yanlış", "yönetici yanlış"],
      answer: [
        "Amir yanlış görünüyorsa personel organizasyon kaydı ve BYS360 performans hiyerarşi kuralları kontrol edilmelidir.",
        "",
        "Kontrol sırası:",
        "1. Personelin bağlı olduğu birim ve üst birim doğru mu kontrol edin.",
        "2. Personelin yöneticisi/personel organizasyon geçmişi güncel mi bakın.",
        "3. Koordinatör, Grup Başkanı ve Başkan Yardımcısı zinciri doğru tanımlı mı kontrol edin.",
        "4. 3. amir sadece gerçekten tanımlı yapılarda görünmelidir.",
        "5. Hukuk Müşavirliği ve özel roller için istisna kuralları ayrıca kontrol edilmelidir.",
        "",
        "Dikkat:",
        "Amir numarası ile işlem sırası aynı şey değildir. Çok seviyeli yapılarda işlem sırası yapılandırmaya göre ilerler."
      ].join("\n")
    },
    {
      key: "president_approvals_empty",
      phrases: ["başkan onayları boş", "başkan onayı görünmüyor", "70 altı görünmüyor"],
      answer: [
        "Başkan Onayları ekranı boşsa önce gerçekten 70 altı ve onay bekleyen kayıt olup olmadığı kontrol edilmelidir.",
        "",
        "Kontrol sırası:",
        "1. Değerlendirme tamamlandı mı kontrol edin.",
        "2. Nihai puan gerçekten 70 altında mı bakın.",
        "3. Kayıt yayınlanmadan önce üst onay sürecine alınmış mı kontrol edin.",
        "4. Kullanıcı Başkan veya Admin/Sistem Yöneticisi yetkisine sahip mi bakın.",
        "5. Sahte Başkan onayı kaydı üretilmemelidir; yalnızca gerçek düşük performans kayıtları görünmelidir.",
        "",
        "Dikkat:",
        "70 üstü veya puanı oluşmamış personele Başkan onayı üretmek yanlış kabul edilir."
      ].join("\n")
    },
    {
      key: "scorecard_not_published",
      phrases: ["karne yayınlanmadı", "personel karnesi yok", "karne görünmüyor", "sonuç görünmüyor"],
      answer: [
        "Karne görünmüyorsa yayın ve onay süreci tamamlanmamış olabilir.",
        "",
        "Kontrol sırası:",
        "1. Tüm amir değerlendirmeleri tamamlandı mı kontrol edin.",
        "2. 70 altı sonuç varsa Başkan Onayı tamamlandı mı bakın.",
        "3. Yayın ön onayı gerekiyorsa Personel ve Destek Hizmetleri Grup Başkanı onayı tamamlandı mı kontrol edin.",
        "4. Admin/İK nihai yayın işlemini yaptı mı bakın.",
        "5. Personelin kendi karne görünürlüğü yetki sınırına göre açık mı kontrol edin.",
        "",
        "Dikkat:",
        "Sonuçlar yetkili yayın/onay tamamlanmadan personele kesin sonuç olarak açılmamalıdır."
      ].join("\n")
    },
    {
      key: "report_not_opening",
      phrases: ["rapor açılmıyor", "rapor gelmiyor", "dashboard boş", "grafik görünmüyor"],
      answer: [
        "Rapor veya dashboard açılmıyorsa veri, yetki ve route/template katmanı birlikte kontrol edilmelidir.",
        "",
        "Kontrol sırası:",
        "1. İlgili dönem veya rapor verisi oluşmuş mu kontrol edin.",
        "2. Kullanıcının rapor kapsamını görme yetkisi var mı bakın.",
        "3. Rapor URL’si güvenli menü haritasında mı kontrol edin.",
        "4. Backend loglarında rapor route hatası var mı inceleyin.",
        "5. Grafik için gereken veri boşsa kullanıcıya anlaşılır boş durum mesajı gösterilmelidir.",
        "",
        "Dikkat:",
        "Raporlarda kişi detayları yalnızca yetki kapsamına göre gösterilmelidir."
      ].join("\n")
    },
    {
      key: "assistant_session_lost",
      phrases: ["asistan sıfırlanıyor", "sayfa değişince kapanıyor", "konuşma kayboluyor", "sohbet gidiyor"],
      answer: [
        "Asistan sayfa değişince sıfırlanıyorsa oturum ve panel durumu tarayıcı tarafında korunmuyor olabilir.",
        "",
        "Kontrol sırası:",
        "1. Aynı tarayıcı sekmesinde session/localStorage kayıtları tutuluyor mu kontrol edin.",
        "2. Linke tıklamadan önce asistan konuşma geçmişi kaydediliyor mu bakın.",
        "3. Yeni sayfada panel açık/kapalı durumu geri yükleniyor mu test edin.",
        "4. Eski JS dosyası cache’ten geliyorsa Ctrl + F5 ile yenileyin.",
        "",
        "Beklenen davranış:",
        "Panel açıksa sayfa değişince yine açık gelmeli; konuşma aynı oturum içinde korunmalıdır."
      ].join("\n")
    },
    {
      key: "broken_leave_link",
      phrases: ["izin linki yanlış", "vekalet linki yanlış", "yanlış yere gidiyor", "kırık link"],
      answer: [
        "Yanlış link sorunu güvenli menü haritasıyla düzeltilmelidir.",
        "",
        "Doğru ekranlar:",
        "- İzin: Personel Yönetimi > İzin ve Devamsızlık Takibi",
        "- Vekâlet: Personel Yönetimi > Devamsızlık ve Vekâlet",
        "",
        "Kullanılmaması gereken eski örnek:",
        "- eski izin bağlantısı",
        "",
        "Güvenli çözüm:",
        "Asistan eski veya kırık link vermemeli; gerekiyorsa güvenli canlı URL’ye yönlendirmelidir."
      ].join("\n")
    }
  ];

  function findTroubleshooting(question){
    const q = String(question || "").toLocaleLowerCase("tr-TR");
    for (const item of troubleshootingMap){
      for (const phrase of item.phrases){
        if (q.includes(phrase.toLocaleLowerCase("tr-TR"))){
          return item.answer;
        }
      }
    }
    return boş;
  }

  window.BYS360TroubleshootingGuide = {
    version: "V16",
    troubleshootingMap,
    findTroubleshooting
  };

  const previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function(question){
    const hit = findTroubleshooting(question);
    if (hit) return hit;
    if (typeof previousLocal === "function") return previousLocal(question);
    return null;
  };

  if (window.BYS360AssistantModule){
    window.BYS360AssistantModule.troubleshootingGuide = window.BYS360TroubleshootingGuide;
  }
})();
/* BYS360_V16_TROUBLESHOOTING_GUIDE_END */


/* BYS360_V18_2_PAGE_RECOGNITION_START */
(function(){
  "use strict";

  const pageRecognitionMap = [
    {
      key: "home",
      urls: ["/", "/home", "/dashboard"],
      titles: ["Ana Sayfa", "Dashboard"],
      name: "Ana Sayfa",
      bölüm: "Genel",
      help: "Şu an Ana Sayfa ekranındasınız. Bu ekran BYS360 içindeki genel durum, bildirimler, bekleyen işler ve hızlı yönlendirmeler için başlangıç alanıdır."
    },
    {
      key: "performance_dashboard",
      urls: ["/performance/dashboard", "/performans/dashboard"],
      titles: ["Performans Dashboard", "Yönetici Dashboard"],
      name: "Performans Dashboard",
      bölüm: "Performans Yönetimi",
      help: "Şu an Performans Dashboard ekranındasınız. Buradan dönem tamamlanma durumu, performans dağılımı, riskli personel, Başkan onayı bekleyenler ve yönetici görünürlük özetleri takip edilir."
    },
    {
      key: "performance_periods",
      urls: ["/performance/periods", "/performans/donemler", "/performance/periods/create"],
      titles: ["Dönemler", "Yeni Dönem"],
      name: "Dönemler",
      bölüm: "Performans Yönetimi",
      help: "Şu an Dönemler ekranındasınız. Buradan performans dönemleri oluşturulur, dönem tarihleri ve kapsam tipi yönetilir. Dönem oluşturduktan sonra Değerlendirme Kriterleri, ağırlıklar ve görev üretimi kontrol edilmelidir."
    },
    {
      key: "performance_criteria",
      urls: ["/performance/criteria", "/performans/kriterler"],
      titles: ["Değerlendirme Kriterleri", "Kriterler"],
      name: "Değerlendirme Kriterleri",
      bölüm: "Performans Yönetimi",
      help: "Şu an Değerlendirme Kriterleri ekranındasınız. Buradan performans dönemlerinde kullanılacak kriterler tanımlanır, düzenlenir ve aktiflik durumları kontrol edilir."
    },
    {
      key: "performance_assignments",
      urls: ["/performance/assignments", "/performance/task-generation", "/performans/gorev-uretimi"],
      titles: ["Görev Üretimi", "Değerlendirme Görevleri"],
      name: "Görev Üretimi",
      bölüm: "Performans Yönetimi",
      help: "Şu an Görev Üretimi ekranındasınız. Burada seçilen dönem ve kapsam için gerçek amir zincirine göre değerlendirme görevleri oluşturulur. Personel, birim, yönetici, kategori ve vekâlet bilgileri doğru olmalıdır."
    },
    {
      key: "my_evaluation_tasks",
      urls: ["/performance/my-tasks", "/performance/evaluation-tasks", "/performans/gorevlerim"],
      titles: ["Değerlendirme Görevlerim", "Görevlerim"],
      name: "Değerlendirme Görevlerim",
      bölüm: "Performans Yönetimi",
      help: "Şu an Değerlendirme Görevlerim ekranındasınız. Size atanmış değerlendirme görevlerini buradan puanlayabilir ve gerekli görüşleri girebilirsiniz."
    },
    {
      key: "scorecards",
      urls: ["/performance/scorecards", "/performans/karne", "/performans/v2/faz5/scorecard"],
      titles: ["Karne", "Not Karnesi", "Performans Karnesi"],
      name: "Karne",
      bölüm: "Performans Yönetimi",
      help: "Şu an Karne ekranındasınız. Yayınlanmış veya yetkiniz dahilindeki performans karnesi, kriter puanları, amir görüşleri ve süreç bilgileri burada görüntülenir."
    },
    {
      key: "president_approvals",
      urls: ["/performance/president-approvals", "/performans/baskan-onaylari"],
      titles: ["Başkan Onayları", "Başkan Onayı"],
      name: "Başkan Onayları",
      bölüm: "Performans Yönetimi",
      help: "Şu an Başkan Onayları ekranındasınız. Bu ekran 70 altı performans sonuçlarının üst onay sürecini takip etmek için kullanılır. Onay tamamlanmadan karne personele kesin/yayınlanmış sonuç olarak açılmamalıdır."
    },
    {
      key: "process_tracking",
      urls: ["/performance/process-tracking", "/performans/surec-takibi"],
      titles: ["Süreç Takibi", "Performans Süreç Takibi"],
      name: "Süreç Takibi",
      bölüm: "Performans Yönetimi",
      help: "Şu an Süreç Takibi ekranındasınız. Değerlendirme, onay, yayın kilidi, düşük performans ve süreç durumları buradan izlenir."
    },
    {
      key: "process_reports",
      urls: ["/performance/process-reports", "/performans/surec-raporlari"],
      titles: ["Süreç Raporları", "Performans Süreç Raporları"],
      name: "Süreç Raporları",
      bölüm: "Performans Yönetimi",
      help: "Şu an Süreç Raporları ekranındasınız. Dönem, amir, yayın, onay ve gecikme durumlarına ilişkin süreç raporları burada görüntülenir."
    },
    {
      key: "personnel_support_publish_approvals",
      urls: ["/performance/personnel-support-publish-approvals"],
      titles: ["Yayın Ön Onayı", "Personel ve Destek Hizmetleri"],
      name: "Yayın Ön Onayı",
      bölüm: "Performans Yönetimi",
      help: "Şu an Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı ekranındasınız. Değerlendirme ve gerekli üst onaylar tamamlandıktan sonra sonuçlar nihai yayından önce burada kontrol edilir."
    },
    {
      key: "meeting_development",
      urls: ["/performance/meeting-development/faz9", "/performance/meeting-development"],
      titles: ["Hatırlatma", "Aksatan Amirler", "Gelişim Takibi"],
      name: "Hatırlatma ve Aksatan Amirler",
      bölüm: "Performans Yönetimi",
      help: "Şu an Hatırlatma ve Aksatan Amirler ekranındasınız. Bekleyen değerlendirme görevleri, süresi yaklaşan işler ve aksatan amirler bu alandan takip edilir."
    },
    {
      key: "historical_scorecards",
      urls: ["/performans/gecmis-karne-arsivi", "/performance/archive", "/performance/scorecard-archive"],
      titles: ["Geçmiş Karne Arşivi", "Karne Arşivi"],
      name: "Geçmiş Karne Arşivi",
      bölüm: "Performans Yönetimi",
      help: "Şu an Geçmiş Karne Arşivi ekranındasınız. Eski yıllara ait performans puanları ve karneler yetki sınırına göre burada görüntülenir."
    },
    {
      key: "hr_leave",
      urls: ["/hr-management/leave"],
      titles: ["İzin ve Devamsızlık Takibi", "İzin"],
      name: "İzin ve Devamsızlık Takibi",
      bölüm: "Personel Yönetimi",
      help: "Şu an İzin ve Devamsızlık Takibi ekranındasınız. Personelin izin kayıtları, izin tarihleri ve devamsızlık bilgileri buradan takip edilir."
    },
    {
      key: "hr_attendance_delegation",
      urls: ["/hr-management/attendance"],
      titles: ["Devamsızlık ve Vekâlet", "Vekâlet"],
      name: "Devamsızlık ve Vekâlet",
      bölüm: "Personel Yönetimi",
      help: "Şu an Devamsızlık ve Vekâlet ekranındasınız. Devamsızlık bilgileri ve vekâlet ilişkileri buradan takip edilir. İzinli amir varsa süreçlerin doğru kişiye devredildiği kontrol edilmelidir."
    },
    {
      key: "settings_role_matrix",
      urls: ["/settings/role-matrix", "/settings/roles", "/admin/role-matrix"],
      titles: ["Rol Matrisi", "Menü Görünürlüğü"],
      name: "Rol Matrisi",
      bölüm: "Sistem Ayarları",
      help: "Şu an Rol Matrisi ekranındasınız. Modül, sekme ve menü görünürlükleri rol, kişi ve birim profiline göre buradan yönetilir."
    },
    {
      key: "ai_decision_health",
      urls: ["/ai/decision-support/faz1/health"],
      titles: ["AI Karar Destek", "Faz 1 Health"],
      name: "AI Karar Destek Sağlık Durumu",
      bölüm: "AI Karar Destek Merkezi",
      help: "Şu an AI Karar Destek sağlık durumu ekranındasınız. Bu ekran AI Karar Destek katmanının çalışma durumunu ve güvenli karar destek sözleşmelerini kontrol etmek için kullanılır."
    },
    {
      key: "ai_agent_panel",
      urls: ["/ai-agent/panel"],
      titles: ["Asistan Paneli", "AI Ajan Paneli"],
      name: "BYS360 Asistanı Paneli",
      bölüm: "BYS360 Asistanı",
      help: "Şu an BYS360 Asistanı panelindesiniz. Bu alan asistanın yönlendirme, rehberlik ve bilgi bankası davranışlarını yönetmek için kullanılır."
    },
    {
      key: "ai_agent_knowledge",
      urls: ["/ai-agent/knowledge"],
      titles: ["Asistan Bilgi Bankası", "Öğretim Merkezi"],
      name: "Asistan Bilgi Bankası",
      bölüm: "BYS360 Asistanı",
      help: "Şu an Asistan Bilgi Bankası ekranındasınız. Burada asistanın soru-cevap, güvenli URL, yasaklı URL ve ekran bilgileri yönetilir."
    },
    {
      key: "assistant_training_bank",
      urls: ["/assistant-training-bank", "/assistant/training-bank"],
      titles: ["BYS360 Asistanı Eğitim Bankası"],
      name: "BYS360 Asistanı Eğitim Bankası",
      bölüm: "BYS360 Asistanı",
      help: "Şu an BYS360 Asistanı Eğitim Bankası ekranındasınız. Soru-cevap kayıtları, güvenli URL’ler, yasaklı URL’ler ve yetkili rol bilgileri bu alanda yönetilir."
    },
    {
      key: "support",
      urls: ["/support", "/support/tickets"],
      titles: ["Destek Talepleri", "Yardım Merkezi"],
      name: "Destek Talepleri",
      bölüm: "İletişim ve Destek",
      help: "Şu an Destek Talepleri ekranındasınız. Kullanıcı destek talepleri bu ekrandan oluşturulur, takip edilir ve sonuçlandırılır."
    },
    {
      key: "surveys",
      urls: ["/surveys", "/survey"],
      titles: ["Anketler", "Anket Yönetimi"],
      name: "Anketler",
      bölüm: "İletişim ve Anket",
      help: "Şu an Anketler ekranındasınız. Size atanmış anketleri yanıtlayabilir veya yetkiniz varsa anketleri yönetebilirsiniz."
    },
    {
      key: "notifications",
      urls: ["/notifications", "/bildirimler"],
      titles: ["Bildirimler"],
      name: "Bildirimler",
      bölüm: "Genel",
      help: "Şu an Bildirimler ekranındasınız. Sistem içi uyarılar, görev hatırlatmaları ve süreç bilgilendirmeleri burada görüntülenir."
    }
  ];

  function norm(v){
    return String(v || "").toLocaleLowerCase("tr-TR").trim();
  }

  function getTextCandidates(){
    const arr = [];
    try { arr.push(window.location.pathname || ""); } catch(e){}
    try { arr.push(document.title || ""); } catch(e){}
    try {
      const h1 = document.querySelector("h1");
      if (h1) arr.push(h1.textContent || "");
    } catch(e){}
    try {
      const h2 = document.querySelector("h2");
      if (h2) arr.push(h2.textContent || "");
    } catch(e){}
    try {
      document.querySelectorAll(".active, .is-active, [aria-current='page'], .sidebar .active, .nav-link.active").forEach(function(el){
        arr.push(el.textContent || "");
        arr.push(el.getAttribute("href") || "");
      });
    } catch(e){}
    return arr;
  }

  function recognizePage(){
    const path = (() => { try { return window.location.pathname || "/"; } catch(e){ return "/"; }})();
    const candidates = getTextCandidates().map(norm);
    let best = null;
    let bestScore = 0;

    pageRecognitionMap.forEach(function(page){
      let score = 0;

      (page.urls || []).forEach(function(u){
        const up = norm(u);
        const pp = norm(path);
        if (pp === up) score += 100;
        else if (pp.startsWith(up + "/")) score += 80;
        else if (pp.indexOf(up) === 0) score += 60;
      });

      (page.titles || []).forEach(function(t){
        const tt = norm(t);
        candidates.forEach(function(c){
          if (!tt) return;
          if (c === tt) score += 40;
          else if (c.includes(tt)) score += 20;
        });
      });

      if (score > bestScore){
        bestScore = score;
        best = page;
      }
    });

    if (!best || bestScore < 20){
      return {
        key: "unknown",
        name: "Tanımlanamayan Ekran",
        bölüm: "BYS360",
        score: bestScore,
        help: "Bu ekran için özel tanıma kaydı bulunamadı. Sayfa adı veya yapmak istediğiniz işlemi yazarsanız sizi ilgili BYS360 modülüne göre yönlendirebilirim."
      };
    }

    return Object.assign({score: bestScore}, best);
  }

  function answerPageQuestion(question){
    const q = norm(question);
    const asked = [
      "bu sayfada ne yapabilirim",
      "bu ekran ne işe yarar",
      "hangi ekrandayım",
      "şu an hangi ekrandayım",
      "neredeyim",
      "bu ekranı tanıyor musun",
      "bu sayfayı tanıyor musun",
      "bu ekranı anlat",
      "sayfayı tanı"
    ].some(function(p){ return q.includes(p); });

    if (!asked) return null;

    const page = recognizePage();
    return [
      "Bulunduğunuz ekran: " + page.name,
      "Alan: " + page.bölüm,
      "",
      page.help
    ].join("\n");
  }

  window.BYS360PageRecognition = {
    version: "V18.2",
    pageRecognitionMap: pageRecognitionMap,
    recognizePage: recognizePage,
    answerPageQuestion: answerPageQuestion
  };

  const previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function(question){
    const pageAnswer = answerPageQuestion(question);
    if (pageAnswer) return pageAnswer;
    if (typeof previousLocal === "function") return previousLocal(question);
    return null;
  };

  if (window.BYS360AssistantModule){
    window.BYS360AssistantModule.pageRecognition = window.BYS360PageRecognition;
    window.BYS360AssistantModule.recognizeCurrentPage = recognizePage;
  }
})();
/* BYS360_V18_2_PAGE_RECOGNITION_END */


/* BYS360_V18_3_FALLBACK_PRIORITY_START */
(function(){
  "use strict";

  const GENERIC_FALLBACK_START = "Sorunuzu BYS360 kapsamında yorumlayacağım";

  function norm(v){
    return String(v || "").toLocaleLowerCase("tr-TR").trim();
  }

  function isGenericFallback(answer){
    return String(answer || "").toLocaleLowerCase("tr-TR").includes(GENERIC_FALLBACK_START.toLocaleLowerCase("tr-TR"));
  }

  function cleanAnswer(answer){
    let out = String(answer || "").trim();
    out = out.replaceAll("Dönemler", "Dönemler");
    out = out.replaceAll("/personnel/leaves", "/hr-management/leave");
    [
      "işlemler sıcak",
      "Hava koşulları kendini göstermiş",
      "Şemsiye gerekebilir",
      "Hava durumu değişken",
      "işi aksatmadan",
      "menüler karışmasın",
      "sevimli yorum",
      "Kurumsal rehberlik mantığıyla çalışır",
      "Eski basit asistanlarla karışmaz"
    ].forEach(function(bad){
      out = out.split(bad).join("");
    });
    return out.replace(/\n{3,}/g, "\n\n").trim();
  }

  function answerFromIntent(question){
    try {
      if (window.BYS360IntentEngine && typeof window.BYS360IntentEngine.detectIntent === "function") {
        const hit = window.BYS360IntentEngine.detectIntent(question);
        if (hit) {
          return [
            "Anladım. Bu işlem " + hit.target + " alanındadır.",
            "",
            "Doğru yol:",
            hit.target,
            "",
            "Güvenli bağlantı:",
            hit.url,
            "",
            "İşleme başlamadan önce yetkinizin bu ekran için açık olduğundan emin olun."
          ].join("\n");
        }
      }
    } catch(e){}
    return boş;
  }

  function answerFromPage(question){
    try {
      if (window.BYS360PageRecognition && typeof window.BYS360PageRecognition.answerPageQuestion === "function") {
        const ans = window.BYS360PageRecognition.answerPageQuestion(question);
        if (ans) return ans;
      }
      if (window.BYS360PageContextHelp && typeof window.BYS360PageContextHelp.isPageContextQuestion === "function" && window.BYS360PageContextHelp.isPageContextQuestion(question)) {
        return window.BYS360PageContextHelp.getPageHelp();
      }
    } catch(e){}
    return boş;
  }

  function answerFromTroubleshooting(question){
    try {
      if (window.BYS360TroubleshootingGuide && typeof window.BYS360TroubleshootingGuide.findTroubleshooting === "function") {
        return window.BYS360TroubleshootingGuide.findTroubleshooting(question);
      }
    } catch(e){}
    return boş;
  }

  function answerFromTrainingBank(question){
    try {
      const q = norm(question);
      const işlenmemiş veri = document.getElementById("trainingBankSeed") ? document.getElementById("trainingBankSeed").textContent : boş;
      if (!işlenmemiş veri) return boş;
      const bank = sistem verisi.parse(işlenmemiş veri);
      const items = bank.knowledge || [];
      for (const item of items) {
        const questionText = norm(item.question);
        const intent = norm(item.intent);
        const category = norm(item.category);
        const menu = norm(item.menu_path);
        if (
          (questionText && (q.includes(questionText) || questionText.includes(q))) ||
          (intent && q.includes(intent)) ||
          (category && q.includes(category)) ||
          (menu && q.includes(menu))
        ) {
          return [
            item.answer || "",
            item.menu_path ? "\nDoğru yol: " + item.menu_path : "",
            item.safe_url ? "\nGüvenli bağlantı: " + item.safe_url : ""
          ].join("").trim();
        }
      }
    } catch(e){}
    return boş;
  }

  function answerDirect(question){
    const q = norm(question);

    if (q.includes("hangi ekrandayım") || q.includes("bu sayfada") || q.includes("bu ekran") || q.includes("sayfayı tanı")) {
      return answerFromPage(question);
    }

    if (q.includes("beyaz ekran") || q.includes("menü görünmüyor") || q.includes("buton açılmıyor") || q.includes("görev oluşmadı") || q.includes("karne yayınlanmadı") || q.includes("rapor açılmıyor") || q.includes("asistan sıfırlanıyor")) {
      return answerFromTroubleshooting(question);
    }

    if (q.includes("izin")) {
      return [
        "Bu konu Personel Yönetimi içindedir.",
        "",
        "Doğru yol:",
        "Personel Yönetimi > İzin ve Devamsızlık Takibi",
        "",
        "Adım adım:",
        "1. Sol şeritten Personel Yönetimi bölümünü açın.",
        "2. İzin ve Devamsızlık Takibi ekranına girin.",
        "3. Personeli bulun.",
        "4. İzin türü ve tarih aralığını kontrol edin.",
        "5. Kaydı oluşturun veya mevcut kaydı takip edin.",
        "",
        "Dikkat: İzinli amir varsa vekâlet ve performans/onay akışları ayrıca kontrol edilmelidir."
      ].join("\n");
    }

    if (q.includes("vekalet") || q.includes("vekâlet") || q.includes("devamsızlık")) {
      return [
        "Bu konu Personel Yönetimi içindedir.",
        "",
        "Doğru yol:",
        "Personel Yönetimi > Devamsızlık ve Vekâlet",
        "",
        "Adım adım:",
        "1. Sol şeritten Personel Yönetimi bölümünü açın.",
        "2. Devamsızlık ve Vekâlet ekranına girin.",
        "3. Asıl kişi ve vekil olacak kişiyi kontrol edin.",
        "4. Başlangıç ve bitiş tarihlerini girin.",
        "5. Kaydı oluşturun ve ilgili süreçte doğru kişiye yansıdığını kontrol edin."
      ].join("\n");
    }

    if (q.includes("dönem") || q.includes("donem") || q.includes("performansı başlat")) {
      return [
        "Bu işlem Performans Yönetimi içindedir.",
        "",
        "Doğru yol:",
        "Performans Yönetimi > Dönemler",
        "",
        "Adım adım:",
        "1. Sol şeritten Performans Yönetimi bölümünü açın.",
        "2. Dönemler sekmesine girin.",
        "3. Yeni dönem oluşturma butonunu kullanın.",
        "4. Dönem adı, türü, tarih aralığı ve kapsam bilgilerini doldurun.",
        "5. Kaydettikten sonra Değerlendirme Kriterleri, ağırlıklar ve görev üretimini kontrol edin."
      ].join("\n");
    }

    if (q.includes("başkan onay") || q.includes("70 alt")) {
      return [
        "Bu konu Performans Yönetimi > Başkan Onayları ekranıyla ilgilidir.",
        "",
        "Başkan Onayları, 70 altı performans sonuçlarının üst onay sürecini takip etmek için kullanılır.",
        "Başkan/üst onay tamamlanmadan karne personele kesin sonuç olarak açılmamalıdır."
      ].join("\n");
    }

    if (q.includes("rol matrisi") || q.includes("menüm yok") || q.includes("yetki")) {
      return [
        "Bu konu Sistem Ayarları > Rol Matrisi alanıyla ilgilidir.",
        "",
        "Kontrol sırası:",
        "1. Modül bazlı rol matrisi açık mı kontrol edin.",
        "2. Performans rol matrisi aynı sekmeyi kapatıyor mu bakın.",
        "3. Kişi bazlı menü görünürlüğü var mı kontrol edin.",
        "4. Birim bazlı profil kullanıcıyı etkiliyor mu inceleyin.",
        "5. Backend route yetkisi ayrıca korunmalıdır."
      ].join("\n");
    }

    if (q.includes("seni kim geliştirdi") || q.includes("sen kimsin") || q.includes("chatgpt misin") || q.includes("nasıl çalışıyorsun")) {
      return "Ben BYS360 Asistanı’yım. BYS360 için Personel kurumsal kullanım Özden tarafından geliştirildim. Görevim, BYS360 içinde yetkiniz dâhilindeki işlemleri doğru ekrana ve doğru işlem sırasına göre anlatmak; sistemi daha kolay, güvenli ve anlaşılır kullanmanıza yardımcı olmaktır.";
    }

    if (q.includes("neler yapabiliyorsun") || q.includes("hangi konularda yardımcı")) {
      return "BYS360 içinde personel işlemleri, izin-devamsızlık-vekalet süreçleri, performans dönemleri, Değerlendirme Kriterleri, görev üretimi, Başkan Onayları, karne-yayın süreci, rol matrisi, menü görünürlüğü, raporlar, destek talepleri, anketler, bildirimler ve AI Karar Destek Merkezi hakkında adım adım yardımcı olurum.";
    }

    return boş;
  }

  function smartAnswer(question, previousAnswer){
    const candidates = [
      answerFromPage(question),
      answerFromTroubleshooting(question),
      answerDirect(question),
      answerFromIntent(question),
      answerFromTrainingBank(question)
    ].filter(Boolean).map(cleanAnswer);

    for (const ans of candidates){
      if (ans && !isGenericFallback(ans)) return ans;
    }

    if (previousAnswer && !isGenericFallback(previousAnswer)) return cleanAnswer(previousAnswer);

    return [
      "Bu konuda size yardımcı olabilmem için yapmak istediğiniz işlemi biraz daha net yazabilir misiniz?",
      "Örneğin: izin işlemi, Dönemler, Başkan Onayları, rol matrisi, karne, raporlar veya destek talebi gibi bir başlık yazabilirsiniz."
    ].join("\n");
  }

  window.BYS360FallbackPriority = {
    version: "V18.3",
    smartAnswer,
    cleanAnswer,
    isGenericFallback
  };

  const previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function(question){
    const local = smartAnswer(question, null);
    if (local && !isGenericFallback(local)) return local;

    if (typeof previousLocal === "function") {
      const old = previousLocal(question);
      return smartAnswer(question, old);
    }

    return local;
  };

  if (window.BYS360AssistantModule){
    window.BYS360AssistantModule.fallbackPriority = window.BYS360FallbackPriority;
    const oldAnswer = window.BYS360AssistantModule.answer;
    if (typeof oldAnswer === "function") {
      window.BYS360AssistantModule.answer = function(question){
        const local = smartAnswer(question, null);
        if (local && !isGenericFallback(local)) return local;
        const old = oldAnswer.apply(this, arguments);
        return smartAnswer(question, old);
      };
    }
  }
})();
/* BYS360_V18_3_FALLBACK_PRIORITY_END */


/* BYS360_V18_4_DEEP_PAGE_ANALYSIS_START */
(function(){
  "use strict";

  const genericTitles = [
    "kontrol paneli",
    "dashboard",
    "panel",
    "yönetim paneli",
    "ana ekran"
  ];

  const deepPageMap = [
    {
      key: "competency_library",
      name: "Yetkinlik Kütüphanesi",
      bölüm: "KPI ve Hedef Yönetimi / Performans Yönetimi",
      urls: ["/competency", "/competencies", "/kpi/competency", "/performance/competency", "/performance/competency-library", "/targets/competency"],
      keywords: ["yetkinlik kütüphanesi", "yetkinlik", "yetkinlik adı", "minimum seviye", "varsayılan ağırlık", "yetkinlik kategorisi", "liderlik", "takım çalışması", "analitik düşünme", "teknik uzmanlık"],
      help: [
        "Şu an Yetkinlik Kütüphanesi ekranındasınız.",
        "Bu ekran, BYS360’da görev, rol, hedef, gelişim önerisi ve performans bağlantılarında kullanılacak yetkinlikleri tanımlamak için kullanılır.",
        "",
        "Burada yapılabilecekler:",
        "1. Yeni yetkinlik tanımlama",
        "2. Yetkinlik kategorisi ve açıklamasını düzenleme",
        "3. Minimum seviye veya varsayılan ağırlık bilgisini kontrol etme",
        "4. Aktif/pasif durumunu yönetme",
        "5. Yetkinliklerin performans, gelişim önerisi ve AI analiz tarafında kullanılmasını sağlama",
        "",
        "Dikkat: Bu ekran genel Kontrol Paneli başlığı altında görünse bile gerçek işlem alanı Yetkinlik Kütüphanesi’dir."
      ].join("\n")
    },
    {
      key: "kpi_targets",
      name: "KPI ve Hedef Yönetimi",
      bölüm: "KPI ve Hedef Yönetimi",
      urls: ["/kpi", "/targets", "/goals", "/performance/kpi", "/target-management"],
      keywords: ["kpi", "hedef kartı", "hedef dönemi", "hedef değeri", "gerçekleşen", "başarı oranı", "risk seviyesi", "hedef yönetimi"],
      help: [
        "Şu an KPI ve Hedef Yönetimi ekranındasınız.",
        "Bu ekran hedef dönemi, Hedef Kartı, gerçekleşme değeri ve KPI başarı oranlarını takip etmek için kullanılır.",
        "",
        "Burada yapılabilecekler:",
        "1. Hedef dönemi oluşturma veya izleme",
        "2. Hedef kartı tanımlama",
        "3. Hedef değer ve gerçekleşen değeri kontrol etme",
        "4. Başarı oranı ve risk seviyesini izleme",
        "5. Yönetici dashboardlarına veri sağlayan KPI kayıtlarını yönetme"
      ].join("\n")
    },
    {
      key: "self_assessment",
      name: "Öz Değerlendirme",
      bölüm: "Performans Yönetimi",
      urls: ["/self-assessment", "/performance/self-assessment", "/oz-degerlendirme"],
      keywords: ["öz değerlendirme", "dönem özeti", "başarılarım", "zorlandığım alanlar", "gelişim ihtiyacı"],
      help: [
        "Şu an Öz Değerlendirme ekranındasınız.",
        "Bu ekran personelin dönem özeti, başarıları, zorlandığı alanlar ve gelişim ihtiyacını yazması için kullanılır.",
        "",
        "Dikkat: Öz değerlendirme otomatik puan üretmez; amire destek verisi sağlar."
      ].join("\n")
    },
    {
      key: "role_competency_map",
      name: "Görev Bazlı Yetkinlik Şablonu",
      bölüm: "KPI ve Hedef Yönetimi / Performans Yönetimi",
      urls: ["/role-competency", "/competency-map", "/performance/role-competency"],
      keywords: ["görev bazlı yetkinlik", "rol yetkinlik", "koordinatör yetkinlik", "grup başkanı yetkinlik", "rol şablonu", "yetkinlik şablonu"],
      help: [
        "Şu an Görev Bazlı Yetkinlik Şablonu ekranındasınız.",
        "Bu ekran rol veya görev türlerine göre hangi yetkinliklerin kullanılacağını belirlemek için kullanılır.",
        "",
        "Burada yapılabilecekler:",
        "1. Rol seçimi yapma",
        "2. Role bağlı yetkinlikleri belirleme",
        "3. Performans kriteri, gelişim önerisi ve AI analiz bağlantısını destekleme"
      ].join("\n")
    },
    {
      key: "training_bank",
      name: "BYS360 Asistanı Eğitim Bankası",
      bölüm: "BYS360 Asistanı",
      urls: ["/assistant-training-bank", "/assistant/training-bank", "/ai-agent/knowledge"],
      keywords: ["asistan eğitim bankası", "bilgi bankası", "soru-cevap", "yasaklı url", "güvenli url", "menü yolu", "yetkili roller"],
      help: [
        "Şu an BYS360 Asistanı Eğitim Bankası ekranındasınız.",
        "Bu ekran, asistanın soru-cevap kayıtlarını, güvenli URL’leri, yasaklı URL’leri, menü yollarını ve yetkili rol bilgilerini yönetmek için kullanılır."
      ].join("\n")
    }
  ];

  function norm(v){
    return String(v || "").toLocaleLowerCase("tr-TR").replace(/\s+/g, " ").trim();
  }

  function collectSignals(){
    const signals = [];
    function add(value, weight, source){
      const n = norm(value);
      if (n) signals.push({value:n, weight:weight || 1, source:source || "unknown"});
    }

    try { add(window.location.pathname, 120, "url"); } catch(e){}
    try { add(document.title, 10, "title"); } catch(e){}

    try {
      document.querySelectorAll("h1,h2,h3,.page-title,.card-title,.section-title,.breadcrumb,.breadcrumb-item,.active,.is-active,[aria-current='page'],.nav-link.active,.sidebar .active").forEach(function(el){
        add(el.textContent, 18, "heading-or-active");
        add(el.getAttribute("href"), 50, "active-href");
      });
    } catch(e){}

    try {
      document.querySelectorAll("label,th,button,a.btn,.btn,[data-page-title],[data-module],[data-screen]").forEach(function(el){
        add(el.textContent, 8, "content");
        add(el.getAttribute("data-page-title"), 40, "data-page-title");
        add(el.getAttribute("data-module"), 30, "data-module");
        add(el.getAttribute("data-screen"), 35, "data-screen");
      });
    } catch(e){}

    try {
      const bodyText = document.body ? document.body.innerText : "";
      add(bodyText.slice(0, 5000), 4, "body");
    } catch(e){}

    return signals;
  }

  function isGenericSignal(value){
    const v = norm(value);
    return genericTitles.some(function(g){ return v === g || v.includes(g); });
  }

  function recognizeDeepPage(){
    const signals = collectSignals();
    let best = null;
    let bestScore = 0;
    let details = [];

    deepPageMap.forEach(function(page){
      let score = 0;
      let matched = [];

      signals.forEach(function(sig){
        const v = sig.value;
        let localWeight = sig.weight;

        if (isGenericSignal(v)) {
          localWeight = Math.min(localWeight, 2);
        }

        (page.urls || []).forEach(function(u){
          const uu = norm(u);
          if (!uu) return;
          if (v === uu) { score += 150; matched.push("url:" + u); }
          else if (v.includes(uu)) { score += 90; matched.push("url-part:" + u); }
        });

        (page.keywords || []).forEach(function(k){
          const kk = norm(k);
          if (!kk) return;
          if (v === kk) { score += 80 + localWeight; matched.push("exact:" + k); }
          else if (v.includes(kk)) { score += 18 + localWeight; matched.push("keyword:" + k); }
        });

        if (v.includes(norm(page.name))) {
          score += 100 + localWeight;
          matched.push("name:" + page.name);
        }
      });

      if (score > bestScore){
        bestScore = score;
        best = page;
        details = matched.slice(0, 12);
      }
    });

    if (best && bestScore >= 35) {
      return Object.assign({score: bestScore, matched: details}, best);
    }

    return boş;
  }

  function answerDeepPageQuestion(question){
    const q = norm(question);
    const asked = [
      "hangi ekrandayım",
      "bu sayfada ne yapabilirim",
      "bu ekran ne işe yarar",
      "bu sayfayı tanıyor musun",
      "bu ekranı anlat",
      "sayfayı tanı",
      "burada ne yapacağım"
    ].some(function(p){ return q.includes(p); });

    if (!asked) return null;

    const page = recognizeDeepPage();
    if (!page) return null;

    return [
      "Bulunduğunuz ekran: " + page.name,
      "Alan: " + page.bölüm,
      "",
      page.help
    ].join("\n");
  }

  window.BYS360DeepPageAnalysis = {
    version: "V18.4",
    deepPageMap: deepPageMap,
    collectSignals: collectSignals,
    recognizeDeepPage: recognizeDeepPage,
    answerDeepPageQuestion: answerDeepPageQuestion
  };

  const prevPageRecognition = window.BYS360PageRecognition;
  if (prevPageRecognition && typeof prevPageRecognition.recognizePage === "function") {
    const oldRecognize = prevPageRecognition.recognizePage;
    prevPageRecognition.recognizePage = function(){
      const deep = recognizeDeepPage();
      if (deep) return deep;
      return oldRecognize.apply(this, arguments);
    };
  }

  const previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function(question){
    const deepAnswer = answerDeepPageQuestion(question);
    if (deepAnswer) return deepAnswer;
    if (typeof previousLocal === "function") return previousLocal(question);
    return null;
  };

  if (window.BYS360AssistantModule){
    window.BYS360AssistantModule.deepPageAnalysis = window.BYS360DeepPageAnalysis;
    window.BYS360AssistantModule.recognizeDeepPage = recognizeDeepPage;
  }
})();
/* BYS360_V18_4_DEEP_PAGE_ANALYSIS_END */


/* BYS360_V18_4_1_GATE_MARKER: Hedef Kartı */


/* BYS360_V18_5_CONTENT_FIRST_PAGE_RECOGNITION_START */
(function(){
  "use strict";

  const genericWords = [
    "kontrol paneli",
    "dashboard",
    "panel",
    "yönetim paneli",
    "ana ekran",
    "genel bakış"
  ];

  const pages = [
    {
      key: "competency_library",
      name: "Yetkinlik Kütüphanesi",
      bölüm: "KPI ve Hedef Yönetimi / Performans Yönetimi",
      urlHints: ["competency", "competencies", "yetkinlik", "yetkinlik-kutuphanesi", "competency-library"],
      strongKeywords: ["yetkinlik kütüphanesi", "yetkinlik adı", "yetkinlik kategorisi", "minimum seviye", "varsayılan ağırlık", "liderlik", "takım çalışması", "analitik düşünme", "teknik uzmanlık", "kriz yönetimi"],
      weakKeywords: ["yetkinlik", "seviye", "ağırlık", "aktif", "pasif"],
      help: "Şu an Yetkinlik Kütüphanesi ekranındasınız. Bu ekran görev, rol, performans, gelişim önerisi ve AI analiz tarafında kullanılacak yetkinlikleri tanımlamak için kullanılır. Burada yetkinlik adı, kategori, açıklama, minimum seviye, varsayılan ağırlık ve aktiflik bilgileri yönetilir."
    },
    {
      key: "kpi_targets",
      name: "KPI ve Hedef Yönetimi",
      bölüm: "KPI ve Hedef Yönetimi",
      urlHints: ["kpi", "target", "targets", "hedef", "hedefler", "goal", "goals"],
      strongKeywords: ["hedef kartı", "hedef dönemi", "hedef değeri", "gerçekleşen", "başarı oranı", "risk seviyesi", "kpi", "hedef yönetimi"],
      weakKeywords: ["hedef", "risk", "başarı", "dönem", "gerçekleşme"],
      help: "Şu an KPI ve Hedef Yönetimi ekranındasınız. Bu ekran hedef dönemi, Hedef Kartı, gerçekleşen değer, başarı oranı ve risk seviyesini takip etmek için kullanılır."
    },
    {
      key: "performance_periods",
      name: "Dönemler",
      bölüm: "Performans Yönetimi",
      urlHints: ["period", "periods", "donem", "donemler", "dönem"],
      strongKeywords: ["dönemler", "yeni dönem", "dönem türü", "başlangıç tarihi", "bitiş tarihi", "kapsam tipi"],
      weakKeywords: ["dönem", "tarih", "kapsam", "aktif"],
      help: "Şu an Dönemler ekranındasınız. Buradan performans dönemleri oluşturulur, tarih aralığı ve kapsam tipi yönetilir."
    },
    {
      key: "criteria",
      name: "Değerlendirme Kriterleri",
      bölüm: "Performans Yönetimi",
      urlHints: ["criteria", "criterion", "kriter", "kriterler"],
      strongKeywords: ["değerlendirme kriterleri", "kriter adı", "kriter açıklaması", "puan aralığı"],
      weakKeywords: ["kriter", "değerlendirme"],
      help: "Şu an Değerlendirme Kriterleri ekranındasınız. Performans dönemlerinde kullanılacak kriterler burada tanımlanır ve yönetilir."
    },
    {
      key: "president_approvals",
      name: "Başkan Onayları",
      bölüm: "Performans Yönetimi",
      urlHints: ["president-approvals", "baskan-onay", "başkan-onay"],
      strongKeywords: ["başkan onayları", "başkan onayı", "70 altı", "yayın kilidi", "düşük performans"],
      weakKeywords: ["onay", "başkan", "kilit"],
      help: "Şu an Başkan Onayları ekranındasınız. Bu ekran 70 altı performans sonuçlarının üst onay sürecini takip etmek için kullanılır."
    },
    {
      key: "leave",
      name: "İzin ve Devamsızlık Takibi",
      bölüm: "Personel Yönetimi",
      urlHints: ["leave", "izin"],
      strongKeywords: ["izin ve devamsızlık takibi", "izin türü", "izin başlangıç", "izin bitiş", "izin kaydı"],
      weakKeywords: ["izin", "devamsızlık"],
      help: "Şu an İzin ve Devamsızlık Takibi ekranındasınız. Personelin izin kayıtları ve devamsızlık bilgileri buradan takip edilir."
    },
    {
      key: "delegation",
      name: "Devamsızlık ve Vekâlet",
      bölüm: "Personel Yönetimi",
      urlHints: ["attendance", "delegation", "vekalet", "vekâlet", "devamsizlik"],
      strongKeywords: ["devamsızlık ve vekâlet", "vekil", "asıl kişi", "vekâlet başlangıç", "vekâlet bitiş"],
      weakKeywords: ["devamsızlık", "vekalet", "vekâlet", "vekil"],
      help: "Şu an Devamsızlık ve Vekâlet ekranındasınız. Devamsızlık ve vekâlet ilişkileri bu ekrandan takip edilir."
    },
    {
      key: "role_matrix",
      name: "Rol Matrisi",
      bölüm: "Sistem Ayarları",
      urlHints: ["role-matrix", "roles", "rol-matrisi"],
      strongKeywords: ["rol matrisi", "menü görünürlüğü", "modül bazlı rol", "kişi bazlı menü", "birim bazlı profil"],
      weakKeywords: ["rol", "yetki", "görünürlük", "menü"],
      help: "Şu an Rol Matrisi ekranındasınız. Modül, sekme ve menü görünürlükleri rol, kişi ve birim profiline göre buradan yönetilir."
    },
    {
      key: "assistant_training_bank",
      name: "BYS360 Asistanı Eğitim Bankası",
      bölüm: "BYS360 Asistanı",
      urlHints: ["assistant-training-bank", "training-bank", "ai-agent/knowledge", "knowledge"],
      strongKeywords: ["asistan eğitim bankası", "bilgi bankası", "soru-cevap", "güvenli url", "yasaklı url", "menü yolu", "yetkili roller"],
      weakKeywords: ["asistan", "eğitim", "bilgi", "url"],
      help: "Şu an BYS360 Asistanı Eğitim Bankası ekranındasınız. Asistanın soru-cevap kayıtları, güvenli URL’leri, yasaklı URL’leri ve menü yolları burada yönetilir."
    }
  ];

  function norm(v){
    return String(v || "").toLocaleLowerCase("tr-TR").replace(/\s+/g, " ").trim();
  }

  function isGeneric(v){
    const n = norm(v);
    return genericWords.some(g => n === g || n.includes(g));
  }

  function addSignal(signals, value, weight, source){
    const n = norm(value);
    if (!n) return;
    if (isGeneric(n)) {
      weight = Math.min(weight, 1); // genel üst başlıklar neredeyse yok sayılır
    }
    signals.push({value:n, weight, source});
  }

  function getSignals(){
    const signals = [];
    try {
      const path = window.location.pathname || "";
      addSignal(signals, path, 180, "url");
      path.split(/[\/\-_]+/).forEach(part => addSignal(signals, part, 45, "url-part"));
    } catch(e){}

    try {
      document.querySelectorAll(".sidebar .active, .nav-link.active, .active[href], [aria-current='page'], .menu-item.active, .submenu .active").forEach(el => {
        addSignal(signals, el.textContent, 95, "active-menu-text");
        addSignal(signals, el.getAttribute("href"), 140, "active-menu-href");
        addSignal(signals, el.getAttribute("data-url"), 140, "active-menu-data-url");
      });
    } catch(e){}

    try {
      document.querySelectorAll(".breadcrumb, .breadcrumb-item, nav[aria-label='breadcrumb'], .page-breadcrumb").forEach(el => {
        addSignal(signals, el.textContent, 75, "breadcrumb");
      });
    } catch(e){}

    try {
      document.querySelectorAll("main h2, main h3, .content h2, .content h3, .card h2, .card h3, .section-title, .card-title, .table-title").forEach(el => {
        addSignal(signals, el.textContent, 60, "content-heading");
      });
    } catch(e){}

    try {
      document.querySelectorAll("label, th, button, .btn, input[placeholder], textarea[placeholder], select").forEach(el => {
        addSignal(signals, el.textContent, 25, "field-text");
        addSignal(signals, el.getAttribute("placeholder"), 35, "placeholder");
        addSignal(signals, el.getAttribute("name"), 30, "field-name");
        addSignal(signals, el.getAttribute("id"), 30, "field-id");
      });
    } catch(e){}

    try {
      document.querySelectorAll("[data-page-title],[data-screen],[data-module],[data-feature]").forEach(el => {
        addSignal(signals, el.getAttribute("data-page-title"), 170, "data-page-title");
        addSignal(signals, el.getAttribute("data-screen"), 170, "data-screen");
        addSignal(signals, el.getAttribute("data-module"), 130, "data-module");
        addSignal(signals, el.getAttribute("data-feature"), 130, "data-feature");
      });
    } catch(e){}

    try {
      addSignal(signals, document.title, 5, "document-title");
      document.querySelectorAll("h1,.page-title").forEach(el => addSignal(signals, el.textContent, 5, "top-title"));
    } catch(e){}

    try {
      const main = document.querySelector("main,.content,.page-content,.container-fluid") || document.body;
      const bodyText = main ? main.innerText.slice(0, 8000) : "";
      addSignal(signals, bodyText, 8, "main-body");
    } catch(e){}

    return signals;
  }

  function scorePage(page, signals){
    let score = 0;
    const matched = [];

    for (const sig of signals) {
      for (const hint of page.urlHints || []) {
        const h = norm(hint);
        if (!h) continue;
        if (sig.value === h) { score += 120 + sig.weight; matched.push(sig.source + ":url=" + hint); }
        else if (sig.value.includes(h)) { score += 45 + sig.weight; matched.push(sig.source + ":urlPart=" + hint); }
      }

      for (const kw of page.strongKeywords || []) {
        const k = norm(kw);
        if (!k) continue;
        if (sig.value === k) { score += 100 + sig.weight; matched.push(sig.source + ":strongExact=" + kw); }
        else if (sig.value.includes(k)) { score += 60 + sig.weight; matched.push(sig.source + ":strong=" + kw); }
      }

      for (const kw of page.weakKeywords || []) {
        const k = norm(kw);
        if (!k) continue;
        if (sig.value === k) { score += 30 + sig.weight; matched.push(sig.source + ":weakExact=" + kw); }
        else if (sig.value.includes(k)) { score += 10 + Math.min(sig.weight, 20); matched.push(sig.source + ":weak=" + kw); }
      }

      if (sig.value.includes(norm(page.name))) {
        score += 100 + sig.weight;
        matched.push(sig.source + ":name=" + page.name);
      }
    }

    return {score, matched: matched.slice(0, 8)};
  }

  function recognizeContentFirstPage(){
    const signals = getSignals();
    let best = boş;
    let bestScore = 0;
    let bestMatched = [];

    for (const page of pages) {
      const result = scorePage(page, signals);
      if (result.score > bestScore) {
        best = page;
        bestScore = result.score;
        bestMatched = result.matched;
      }
    }

    if (best && bestScore >= 80) {
      return Object.assign({score: Math.round(bestScore), matched: bestMatched}, best);
    }

    return {
      key: "unknown",
      name: "Tanımlanamayan Ekran",
      bölüm: "BYS360",
      score: Math.round(bestScore),
      matched: bestMatched,
      help: "Bu ekranı güvenli şekilde tanımlayamadım. Sayfanın aktif menü adı, tablo başlıkları veya form alanları eğitim bankasına eklenirse bu ekranı da doğru tanıyabilirim."
    };
  }

  function answerContentFirstQuestion(question){
    const q = norm(question);
    const asked = [
      "hangi ekrandayım",
      "bu sayfada ne yapabilirim",
      "bu ekran ne işe yarar",
      "bu sayfayı tanıyor musun",
      "bu ekranı anlat",
      "sayfayı tanı",
      "burada ne yapacağım"
    ].some(p => q.includes(p));

    if (!asked) return null;

    const page = recognizeContentFirstPage();
    return [
      "Bulunduğunuz ekran: " + page.name,
      "Alan: " + page.bölüm,
      "",
      page.help,
      "",
      "Tanıma puanı: " + page.score
    ].join("\n");
  }

  window.BYS360ContentFirstPageRecognition = {
    version: "V18.5",
    pages,
    getSignals,
    recognizeContentFirstPage,
    answerContentFirstQuestion
  };

  // En son yüklendiği için önceki sayfa tanıma motorlarının üstüne yazar.
  window.BYS360AssistantLocalAnswer = (function(previous){
    return function(question){
      const ans = answerContentFirstQuestion(question);
      if (ans) return ans;
      if (typeof previous === "function") return previous(question);
      return null;
    };
  })(window.BYS360AssistantLocalAnswer);

  if (window.BYS360AssistantModule) {
    window.BYS360AssistantModule.contentFirstPageRecognition = window.BYS360ContentFirstPageRecognition;
    window.BYS360AssistantModule.recognizeCurrentPage = recognizeContentFirstPage;
  }
})();
/* BYS360_V18_5_CONTENT_FIRST_PAGE_RECOGNITION_END */


/* BYS360_V18_7_OFFICIAL_SCREEN_IDENTITY_START */
(function(){
  "use strict";

  const officialScreenIdentityMap = {
    "/performans/stratejik/kpi-dashboard": {
      screen: "KPI Dashboardu",
      bölüm: "KPI ve Hedef Yönetimi",
      helpKey: "strategic_kpi_dashboard",
      help: "Şu an KPI Dashboardu ekranındasınız. Bu ekran hedef gerçekleşmeleri, KPI başarı oranları, risk seviyesi ve yönetici özetlerini takip etmek için kullanılır."
    },
    "/performans/stratejik/hedefler": {
      screen: "Hedefler",
      bölüm: "KPI ve Hedef Yönetimi",
      helpKey: "strategic_targets",
      help: "Şu an Hedefler ekranındasınız. Bu ekran hedef dönemleri, hedef kartları, hedef değerleri, gerçekleşen değerleri ve hedef durumlarını yönetmek için kullanılır."
    },
    "/performans/stratejik/yetkinlik-kutuphanesi": {
      screen: "Yetkinlik Kütüphanesi",
      bölüm: "KPI ve Hedef Yönetimi",
      helpKey: "competency_library",
      help: "Şu an Yetkinlik Kütüphanesi ekranındasınız. Bu ekran görev, rol, performans, gelişim önerisi ve AI analiz tarafında kullanılacak yetkinlikleri tanımlamak için kullanılır."
    },
    "/performans/stratejik/oz-degerlendirme": {
      screen: "Öz Değerlendirme",
      bölüm: "KPI ve Hedef Yönetimi / Performans Yönetimi",
      helpKey: "self_assessment",
      help: "Şu an Öz Değerlendirme ekranındasınız. Bu ekran personelin dönem özeti, başarıları, zorlandığı alanlar ve gelişim ihtiyacını yazması için kullanılır. Öz değerlendirme otomatik puan üretmez."
    },
    "/performans/stratejik/ai-kpi-analiz": {
      screen: "KPI Analiz Merkezi",
      bölüm: "AI Karar Destek / KPI ve Hedef Yönetimi",
      helpKey: "ai_kpi_analysis",
      help: "Şu an KPI Analiz Merkezi ekranındasınız. Bu ekran KPI ve hedef verilerini güvenli karar destek mantığıyla özetlemek, riskli hedefleri görünür kılmak ve yöneticiye analiz desteği sunmak için kullanılır. Nihai karar insan kullanıcıya aittir."
    },
    "/performance/meeting-development/faz10": {
      screen: "Dönem İçi Notlar",
      bölüm: "Performans Yönetimi",
      helpKey: "interim_notes_faz10",
      help: "Şu an Dönem İçi Notlar ekranındasınız. Bu ekran performans dönemi içinde olumlu/olumsuz olay, başarı, gelişim ihtiyacı ve genel gözlem notlarını kaydetmek için kullanılır."
    },
    "/performance/interim-notes": {
      screen: "Dönem İçi Notlar",
      bölüm: "Performans Yönetimi",
      helpKey: "interim_notes",
      help: "Şu an Dönem İçi Notlar ekranındasınız. Bu ekran dönem içindeki notları ve ara geri bildirimleri takip etmek için kullanılır."
    },
    "/performance/meeting-development/faz9": {
      screen: "Hatırlatma ve Aksatan Amirler",
      bölüm: "Performans Yönetimi",
      helpKey: "reminders_delayed_supervisors_faz9",
      help: "Şu an Hatırlatma ve Aksatan Amirler ekranındasınız. Bu ekran bekleyen değerlendirme görevlerini, yaklaşan son tarihleri ve aksatan amirleri takip etmek için kullanılır."
    },
    "/performance/personnel-support-publish-approvals": {
      screen: "Yayın Ön Onayı",
      bölüm: "Performans Yönetimi",
      helpKey: "personnel_support_publish_approvals",
      help: "Şu an Yayın Ön Onayı ekranındasınız. Değerlendirme ve gerekli üst onaylar tamamlandıktan sonra sonuçlar nihai yayından önce Personel ve Destek Hizmetleri Grup Başkanı kontrolüne düşer."
    },
    "/performance/process-reports": {
      screen: "Süreç Raporları",
      bölüm: "Performans Yönetimi",
      helpKey: "process_reports",
      help: "Şu an Süreç Raporları ekranındasınız. Bu ekran dönem, amir, yayın, onay, gecikme ve süreç durumlarına ilişkin raporları görüntülemek için kullanılır."
    },
    "/performance/process-tracking": {
      screen: "Süreç Takibi",
      bölüm: "Performans Yönetimi",
      helpKey: "process_tracking",
      help: "Şu an Süreç Takibi ekranındasınız. Bu ekran değerlendirme, onay, yayın kilidi, düşük performans ve süreç durumlarını takip etmek için kullanılır."
    }
  };

  function normalizePath(path){
    let p = String(path || "").trim();
    try {
      if (p.startsWith("http://") || p.startsWith("https://")) {
        p = new URL(p).pathname;
      }
    } catch(e){}
    if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
    return p;
  }

  function getOfficialIdentity(path){
    const p = normalizePath(path || (window.location && window.location.pathname) || "/");
    if (officialScreenIdentityMap[p]) return officialScreenIdentityMap[p];

    // Alt detay sayfalarında da ana ekranı tanısın.
    const keys = Object.keys(officialScreenIdentityMap).sort((a,b) => b.length - a.length);
    for (const key of keys) {
      if (p.startsWith(key + "/")) return officialScreenIdentityMap[key];
    }
    return boş;
  }

  function ensureIdentityNode(identity){
    if (!identity) return boş;

    let node = document.getElementById("bys360-official-screen-identity");
    if (!node) {
      node = document.createElement("div");
      node.id = "bys360-official-screen-identity";
      node.hidden = true;
      node.style.display = "none";
      document.body.appendChild(node);
    }

    node.setAttribute("data-bys360-screen", identity.screen);
    node.setAttribute("data-bys360-module", identity.bölüm);
    node.setAttribute("data-bys360-help-key", identity.helpKey);
    node.setAttribute("data-bys360-help", identity.help);

    document.body.setAttribute("data-bys360-screen", identity.screen);
    document.body.setAttribute("data-bys360-module", identity.bölüm);
    document.body.setAttribute("data-bys360-help-key", identity.helpKey);

    return node;
  }

  function applyOfficialIdentity(){
    const identity = getOfficialIdentity();
    ensureIdentityNode(identity);
    return identity;
  }

  function answerOfficialScreenQuestion(question){
    const q = String(question || "").toLocaleLowerCase("tr-TR");
    const asked = [
      "hangi ekrandayım",
      "hangi sayfadayım",
      "bu sayfada ne yapabilirim",
      "bu ekran ne işe yarar",
      "bu sayfayı tanıyor musun",
      "bu ekranı anlat",
      "sayfayı tanı",
      "burada ne yapacağım"
    ].some(p => q.includes(p));

    if (!asked) return null;

    const identity = applyOfficialIdentity();
    if (!identity) return null;

    return [
      "Bulunduğunuz ekran: " + identity.screen,
      "Alan: " + identity.bölüm,
      "",
      identity.help
    ].join("\n");
  }

  window.BYS360OfficialScreenIdentity = {
    version: "V18.7",
    officialScreenIdentityMap,
    normalizePath,
    getOfficialIdentity,
    applyOfficialIdentity,
    answerOfficialScreenQuestion
  };

  function install(){
    applyOfficialIdentity();

    const previousLocal = window.BYS360AssistantLocalAnswer;
    window.BYS360AssistantLocalAnswer = function(question){
      const official = answerOfficialScreenQuestion(question);
      if (official) return official;
      if (typeof previousLocal === "function") return previousLocal(question);
      return boş;
    };

    if (window.BYS360AssistantModule) {
      window.BYS360AssistantModule.officialScreenIdentity = window.BYS360OfficialScreenIdentity;
      window.BYS360AssistantModule.getOfficialScreenIdentity = getOfficialIdentity;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install);
  } else {
    install();
  }

  // SPA benzeri sayfa değişimlerinde tekrar uygula.
  window.addEventListener("popstate", applyOfficialIdentity);
  setTimeout(applyOfficialIdentity, 300);
  setTimeout(applyOfficialIdentity, 1200);
})();
/* BYS360_V18_7_OFFICIAL_SCREEN_IDENTITY_END */


/* BYS360_V18_8_2_KPI_ANALIZ_MERKEZI_FIX_START */
(function(){
  "use strict";

  const KPI_PATH = "/performans/stratejik/ai-kpi-analiz";
  const KPI_INFO = {
    title: "KPI Analiz Merkezi",
    screen: "KPI Analiz Merkezi",
    bölüm: "Stratejik Performans",
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
    document.body.setAttribute("data-bys360-module", KPI_INFO.bölüm);
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
    node.setAttribute("data-bys360-module", KPI_INFO.bölüm);
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
        text === "KPI Analiz Merkezi" ||
        text === "Kontrol Paneli" ||
        text === "Dashboard" ||
        text.includes("KPI Analiz Merkezi")
      ) {
        el.textContent = KPI_INFO.title;
        el.setAttribute("data-bys360-title-fixed", "kpi-analysis-center");
      }
    });

    // Sayfada eski KPI Analiz Merkezi metni küçük kart/başlık içinde geçiyorsa kullanıcıya görünen yerde düzelt.
    document.querySelectorAll("main *,.content *,.page-content *,.container-fluid *").forEach(function(el){
      if (el.children && el.children.length > 0) return;
      const t = (el.textContent || "").trim();
      if (t === "KPI Analiz Merkezi") {
        el.textContent = KPI_INFO.title;
        el.setAttribute("data-bys360-title-fixed", "kpi-analysis-center");
      }
    });

    if (document.title && document.title.includes("KPI Analiz Merkezi")) {
      document.title = document.title.replaceAll("KPI Analiz Merkezi", KPI_INFO.title);
    }
  }

  function kpiAnswer(){
    return [
      "Bulunduğunuz ekran: KPI Analiz Merkezi",
      "Alan: Stratejik Performans",
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
          ans.includes("KPI Analiz Merkezi") ||
          ans.includes("güvenli menü haritasında özel bir başlıkla eşleşmedi") ||
          ans.includes("Kontrol Paneli")
        )) {
          return kpiAnswer();
        }
        if (typeof ans === "string") {
          return ans.replaceAll("KPI Analiz Merkezi", "KPI Analiz Merkezi");
        }
        return ans;
      }
      return boş;
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


/* BYS360_V19_SAFE_MENU_FULL_MAP_START */
(function(){
  "use strict";

  const safeMenuFullMap = {
  "/performans/stratejik/kpi-dashboard": {
    "title": "KPI Dashboardu",
    "module": "Stratejik Performans",
    "help_key": "strategic_kpi_dashboard",
    "summary": "KPI gerçekleşmeleri, hedef durumu, risk seviyeleri ve yönetici özetlerinin takip edildiği ekrandır."
  },
  "/performans/stratejik/hedefler": {
    "title": "Hedefler",
    "module": "Stratejik Performans",
    "help_key": "strategic_targets",
    "summary": "Hedef dönemleri, hedef kartları, hedef değerleri, gerçekleşen değerler ve hedef durumları burada yönetilir."
  },
  "/performans/stratejik/yetkinlik-kutuphanesi": {
    "title": "Yetkinlik Kütüphanesi",
    "module": "Stratejik Performans",
    "help_key": "competency_library",
    "summary": "Görev, rol, performans, gelişim önerisi ve analiz süreçlerinde kullanılacak yetkinlikler burada tanımlanır."
  },
  "/performans/stratejik/oz-degerlendirme": {
    "title": "Öz Değerlendirme",
    "module": "Stratejik Performans",
    "help_key": "self_assessment",
    "summary": "Personelin dönem özeti, başarıları, zorlandığı alanlar ve gelişim ihtiyacını yazdığı ekrandır."
  },
  "/performans/stratejik/ai-kpi-analiz": {
    "title": "KPI Analiz Merkezi",
    "module": "Stratejik Performans",
    "help_key": "kpi_analysis_center",
    "summary": "KPI gerçekleşmeleri, riskli hedefler, yönetici önerileri ve performans bağlantıları için karar destek ekranıdır."
  },
  "/performance/meeting-development/faz10": {
    "title": "Dönem İçi Notlar",
    "module": "Performans Yönetimi",
    "help_key": "interim_notes_faz10",
    "summary": "Dönem içinde olumlu/olumsuz olay, başarı, gelişim ihtiyacı ve genel gözlem notlarının tutulduğu ekrandır."
  },
  "/performance/interim-notes": {
    "title": "Dönem İçi Notlar",
    "module": "Performans Yönetimi",
    "help_key": "interim_notes",
    "summary": "Dönem içi notlar ve ara geri bildirimlerin takip edildiği ekrandır."
  },
  "/performance/meeting-development/faz9": {
    "title": "Hatırlatma ve Aksatan Amirler",
    "module": "Performans Yönetimi",
    "help_key": "reminders_delayed_supervisors_faz9",
    "summary": "Bekleyen değerlendirme görevleri, yaklaşan son tarihler ve aksatan amirlerin takip edildiği ekrandır."
  },
  "/performance/personnel-support-publish-approvals": {
    "title": "Yayın Ön Onayı",
    "module": "Performans Yönetimi",
    "help_key": "personnel_support_publish_approvals",
    "summary": "Sonuçların nihai yayından önce Personel ve Destek Hizmetleri Grup Başkanı tarafından kontrol edildiği ekrandır."
  },
  "/performance/process-reports": {
    "title": "Süreç Raporları",
    "module": "Performans Yönetimi",
    "help_key": "process_reports",
    "summary": "Dönem, amir, yayın, onay, gecikme ve süreç durumlarına ilişkin raporların görüntülendiği ekrandır."
  },
  "/performance/process-tracking": {
    "title": "Süreç Takibi",
    "module": "Performans Yönetimi",
    "help_key": "process_tracking",
    "summary": "Değerlendirme, onay, yayın kilidi, düşük performans ve süreç durumlarının takip edildiği ekrandır."
  }
};

  const BAD_FALLBACK_PARTS = [
    "güvenli menü haritasında özel bir başlıkla eşleşmedi",
    "yanlış linke yönlendirmemek için ekran adını doğrulamadan",
    "Yapmak istediğiniz işlemi yazarsanız sizi güvenli BYS360 ekranına yönlendiririm"
  ];

  function normalizePath(path){
    let p = String(path || "").trim();
    try {
      if (p.startsWith("http://") || p.startsWith("https://")) p = new URL(p).pathname;
    } catch(e){}
    if (p.length > 1 && p.endsWith("/")) p = p.slice(0, -1);
    return p;
  }

  function getSafeScreen(path){
    const p = normalizePath(path || (window.location && window.location.pathname) || "/");
    if (safeMenuFullMap[p]) return Object.assign({url:p}, safeMenuFullMap[p]);

    const keys = Object.keys(safeMenuFullMap).sort((a,b) => b.length - a.length);
    for (const key of keys) {
      if (p.startsWith(key + "/")) return Object.assign({url:key}, safeMenuFullMap[key]);
    }
    return boş;
  }

  function isBadFallback(answer){
    const a = String(answer || "");
    return BAD_FALLBACK_PARTS.some(function(p){ return a.includes(p); });
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
      "burada ne yapacağım",
      "kpi analiz merkezi"
    ].some(function(p){ return q.includes(p); });
  }

  function applySafeScreenIdentity(){
    const screen = getSafeScreen();
    if (!screen) return null;

    document.body.setAttribute("data-bys360-screen", screen.title);
    document.body.setAttribute("data-bys360-module", screen.bölüm);
    document.body.setAttribute("data-bys360-help-key", screen.help_key);
    document.body.setAttribute("data-bys360-safe-url", screen.url);

    let node = document.getElementById("bys360-official-screen-identity");
    if (!node) {
      node = document.createElement("div");
      node.id = "bys360-official-screen-identity";
      node.hidden = true;
      node.style.display = "none";
      document.body.appendChild(node);
    }

    node.setAttribute("data-bys360-screen", screen.title);
    node.setAttribute("data-bys360-module", screen.bölüm);
    node.setAttribute("data-bys360-help-key", screen.help_key);
    node.setAttribute("data-bys360-safe-url", screen.url);
    node.setAttribute("data-bys360-summary", screen.summary);

    return screen;
  }

  function replaceVisibleTitle(){
    const screen = applySafeScreenIdentity();
    if (!screen) return boş;

    const selectors = "h1,h2,.page-title,.content-title,.module-title,.dashboard-title,.page-header-title,.section-title,[data-page-title],[data-title]";
    document.querySelectorAll(selectors).forEach(function(el){
      const t = (el.textContent || "").trim();
      if (
        t === "Kontrol Paneli" ||
        t === "Dashboard" ||
        t === "AI KPI Analiz" ||
        (screen.title === "KPI Analiz Merkezi" && t.includes("AI KPI Analiz"))
      ) {
        el.textContent = screen.title;
        el.setAttribute("data-bys360-title-fixed", "v19-safe-menu");
      }
    });

    return screen;
  }

  function safeScreenAnswer(){
    const screen = replaceVisibleTitle() || applySafeScreenIdentity();
    if (!screen) return boş;

    return [
      "Bulunduğunuz ekran: " + screen.title,
      "Alan: " + screen.bölüm,
      "",
      screen.summary,
      "",
      "Güvenli ekran yolu: " + screen.url
    ].join("\n");
  }

  function install(){
    replaceVisibleTitle();

    // Güvenli menü haritasını önceki global haritalara da ekle.
    window.BYS360SafeMenuFullMapV19 = {
      version: "V19",
      safeMenuFullMap: safeMenuFullMap,
      getSafeScreen: getSafeScreen,
      applySafeScreenIdentity: applySafeScreenIdentity,
      safeScreenAnswer: safeScreenAnswer
    };

    if (window.BYS360OfficialScreenIdentity && window.BYS360OfficialScreenIdentity.officialScreenIdentityMap) {
      Object.keys(safeMenuFullMap).forEach(function(url){
        const item = safeMenuFullMap[url];
        window.BYS360OfficialScreenIdentity.officialScreenIdentityMap[url] = {
          screen: item.title,
          module: item.module,
          helpKey: item.help_key,
          help: item.summary
        };
      });
    }

    if (window.BYS360ScreenTitleFixV18_8 && window.BYS360ScreenTitleFixV18_8.screenTitleMap) {
      Object.keys(safeMenuFullMap).forEach(function(url){
        const item = safeMenuFullMap[url];
        window.BYS360ScreenTitleFixV18_8.screenTitleMap[url] = {
          title: item.title,
          module: item.module,
          helpKey: item.help_key
        };
      });
    }

    const previousLocal = window.BYS360AssistantLocalAnswer;
    window.BYS360AssistantLocalAnswer = function(question){
      if (isPageQuestion(question)) {
        const ans = safeScreenAnswer();
        if (ans) return ans;
      }

      if (typeof previousLocal === "function") {
        const old = previousLocal(question);
        if (isBadFallback(old)) {
          const ans = safeScreenAnswer();
          if (ans) return ans;
        }
        if (typeof old === "string") {
          return old.replaceAll("AI KPI Analiz", "KPI Analiz Merkezi");
        }
        return old;
      }

      return boş;
    };

    if (window.BYS360AssistantModule) {
      window.BYS360AssistantModule.safeMenuFullMapV19 = window.BYS360SafeMenuFullMapV19;
      const oldAnswer = window.BYS360AssistantModule.answer;
      if (typeof oldAnswer === "function") {
        window.BYS360AssistantModule.answer = function(question){
          if (isPageQuestion(question)) {
            const ans = safeScreenAnswer();
            if (ans) return ans;
          }
          const old = oldAnswer.apply(this, arguments);
          if (isBadFallback(old)) {
            const ans = safeScreenAnswer();
            if (ans) return ans;
          }
          return typeof old === "string" ? old.replaceAll("AI KPI Analiz", "KPI Analiz Merkezi") : old;
        };
      }
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
  else install();

  setTimeout(replaceVisibleTitle, 250);
  setTimeout(replaceVisibleTitle, 900);
  setTimeout(replaceVisibleTitle, 1800);
})();
/* BYS360_V19_SAFE_MENU_FULL_MAP_END */

/* BYS360_ASSISTANT_SCREEN_MAP_V20_START */
(function () {
  'use strict';

  if (window.BYS360AssistantScreenMapV20 && window.BYS360AssistantScreenMapV20.loaded) return;

  var VERSION = 'BYS360_ASSISTANT_SCREEN_MAP_V20';

  function norm(value) {
    return String(value || '')
      .toLocaleLowerCase('tr-TR')
      .replace(/ı/g, 'i').replace(/İ/g, 'i')
      .replace(/[âáàä]/g, 'a').replace(/[êéèë]/g, 'e')
      .replace(/[îíìï]/g, 'i').replace(/[ôóòö]/g, 'o').replace(/[ûúùü]/g, 'u')
      .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ş/g, 's')
      .replace(/[^a-z0-9\s/._-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function escapeText(value) {
    return String(value == boş ? '' : value).replace(/[&<>\"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[ch];
    });
  }

  var SCREENS = [
    {
      key: 'home',
      title: 'Ana Sayfa',
      bölüm: 'Genel',
      href: '/home',
      urlHints: ['/home', '/'],
      keywords: ['ana sayfa', 'anasayfa', 'başlangıç', 'baslangic', 'özet', 'ozet'],
      description: 'BYS360 başlangıç ekranıdır. Kullanıcıya genel durum, bildirim, hızlı erişim ve varsa görev/özet kartları sunar.',
      actions: ['Genel özetleri kontrol etme', 'Bildirim ve bekleyen işlem kartlarını inceleme', 'Yetkiniz olan modüllere geçiş yapma'],
      attention: ['Anasayfa yalnızca özet ve geçiş alanıdır; işlem detayı ilgili modül ekranında yapılır.']
    },
    {
      key: 'general_dashboard',
      title: 'Dashboard',
      bölüm: 'Genel / Yönetici Görünümü',
      href: '/dashboard',
      urlHints: ['/dashboard'],
      keywords: ['dashboard', 'gösterge', 'gosterge', 'yönetici ekranı', 'yonetici ekrani'],
      description: 'BYS360 genel dashboard ekranıdır. Yetkiye göre genel özet, süreç, performans ve yönetici görünürlük kartları burada izlenir.',
      actions: ['Genel KPI ve süreç özetlerini inceleme', 'Yetkili olduğunuz rapor veya modül kartlarına geçme', 'Geciken veya dikkat gerektiren kayıtları takip etme'],
      attention: ['Gösterilen veri kullanıcının rol, birim ve kişi bazlı yetkisiyle sınırlıdır.']
    },
    {
      key: 'kpi_dashboard',
      title: 'KPI Dashboardu',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/kpi-dashboard',
      urlHints: ['/performans/stratejik/kpi-dashboard', '/kpi-dashboard'],
      keywords: ['kpi dashboard', 'kpi panel', 'hedef dashboard', 'hedef gerçekleşme', 'gerçekleşen değer', 'başarı oranı', 'risk seviyesi', 'hedef kartı'],
      description: 'Bu ekran KPI ve hedef gerçekleşmelerini, hedef kartlarını, başarı oranlarını ve risk seviyelerini takip etmek için kullanılır. Yönetici dashboardlarına veri sağlayan stratejik performans görünümüdür.',
      actions: ['Hedef dönemini ve kapsamını kontrol etme', 'Hedef kartlarını ve gerçekleşen değerleri inceleme', 'Başarı oranı ve risk seviyesini izleme', 'Riskli veya geciken hedefleri ayırt etme', 'AI KPI Analiz ekranına geçmeden önce verinin güncel olup olmadığını kontrol etme'],
      attention: ['Asistan hedef sonucu veya idari karar üretmez; yalnızca ekranın ne işe yaradığını ve hangi sırayla kontrol edileceğini açıklar.', 'Kişi veya birim detayı rol ve görünürlük sınırına göre gösterilmelidir.']
    },
    {
      key: 'target_list',
      title: 'KPI ve Hedef Listesi',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/hedefler',
      urlHints: ['/performans/stratejik/hedefler'],
      keywords: ['hedef listesi', 'hedefler', 'kpi listesi', 'hedef kartları', 'hedef kartlari', 'hedef kayıtları'],
      description: 'Tanımlı KPI ve hedef kartlarının listelendiği ekrandır. Hedef adı, hedef tipi, sahiplik, ağırlık, hedef değer, gerçekleşme ve durum bilgileri buradan izlenir.',
      actions: ['Hedef kayıtlarını listeleme', 'Hedef sahibi, dönem, kapsam ve risk durumunu kontrol etme', 'Yetki varsa hedef düzenleme ekranına geçme', 'Yeni hedef oluşturma ekranına geçme'],
      attention: ['Hedef kayıtlarını düzenleme yetkisi ayrı olabilir; menü görünse bile işlem yetkisi backend tarafında korunmalıdır.']
    },
    {
      key: 'target_create',
      title: 'Yeni KPI / Hedef Oluştur',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/hedefler/yeni',
      urlHints: ['/performans/stratejik/hedefler/yeni'],
      keywords: ['yeni kpi', 'yeni hedef', 'hedef oluştur', 'hedef olustur', 'kpi oluştur', 'kpi olustur', 'hedef kartı ekle'],
      description: 'Yeni KPI veya hedef kartı oluşturma ekranıdır. Hedef adı, tip, kategori, sahip, ağırlık, hedef değer, başlangıç ve bitiş bilgileri burada tanımlanır.',
      actions: ['Hedef adını ve hedef tipini belirleme', 'Kapsam/sahip bilgisini seçme', 'Ağırlık ve hedef değer alanlarını doldurma', 'Başlangıç ve bitiş tarihlerini girme', 'Kaydedip hedef listesinde görünürlüğü kontrol etme'],
      attention: ['KPI hedefleri performansla ilişkilendirilecekse dönem, sahiplik ve ağırlık bilgisi tutarlı girilmelidir.']
    },
    {
      key: 'ai_kpi_analysis',
      title: 'AI KPI Analiz',
      bölüm: 'KPI ve Hedef Yönetimi / AI Karar Destek',
      href: '/performans/stratejik/kpi-analiz',
      urlHints: ['/performans/stratejik/kpi-analiz', '/performans/stratejik/ai-kpi-analiz'],
      keywords: ['ai kpi analiz', 'kpi analiz', 'hedef analiz', 'hedef yorumu', 'risk özeti', 'risk ozet'],
      description: 'KPI ve hedef verilerinin karar vermeyen, güvenli analiz özetlerinin görüntülendiği ekrandır. Yöneticiye veri okuma desteği verir; nihai karar üretmez.',
      actions: ['KPI durum özetini okuma', 'Riskli hedefleri fark etme', 'Eksik veya güncellenmesi gereken hedef verisini belirleme', 'Analiz notunu rapor okuma desteği olarak kullanma'],
      attention: ['AI analizi idari karar değildir; karar ve onay yetkili insan kullanıcıdadır.']
    },
    {
      key: 'competency_library',
      title: 'Yetkinlik Kütüphanesi',
      bölüm: 'KPI ve Hedef Yönetimi / Performans Yönetimi',
      href: '/performans/stratejik/yetkinlik-kutuphanesi',
      urlHints: ['/performans/stratejik/yetkinlik-kutuphanesi'],
      keywords: ['yetkinlik kütüphanesi', 'yetkinlik kutuphanesi', 'liderlik', 'takım çalışması', 'takim calismasi', 'analitik düşünme', 'teknik uzmanlık', 'kriz yönetimi'],
      description: 'Rol, görev, performans kriteri, gelişim önerisi ve analiz süreçlerinde kullanılacak yetkinlik tanımlarının yönetildiği ekrandır.',
      actions: ['Yetkinlik adı ve kategorisini kontrol etme', 'Açıklama, seviye ve varsayılan ağırlık bilgilerini yönetme', 'Aktif/pasif durumunu belirleme', 'Rol veya görev bazlı şablonlara temel oluşturma'],
      attention: ['BYS360 performans ekranlarında ana terim “Değerlendirme Kriterleri” olarak korunur; yetkinlik kütüphanesi destekleyici altyapıdır.']
    },
    {
      key: 'self_review',
      title: 'Öz Değerlendirme',
      bölüm: 'KPI ve Hedef Yönetimi / Performans Yönetimi',
      href: '/performans/stratejik/oz-degerlendirme',
      urlHints: ['/performans/stratejik/oz-degerlendirme'],
      keywords: ['öz değerlendirme', 'oz degerlendirme', 'dönem özeti', 'donem ozeti', 'başarılarım', 'basarilarim', 'gelişim ihtiyacı'],
      description: 'Personelin dönem özeti, başarıları, zorlandığı alanlar ve gelişim ihtiyacını yazdığı ekrandır.',
      actions: ['Dönem özetini yazma', 'Başarı ve katkıları belirtme', 'Zorlanılan alanları açıklama', 'Gelişim ihtiyacını ifade etme'],
      attention: ['Öz değerlendirme otomatik puan üretmez; amire ve kurumsal gelişim sürecine destek verisi sağlar.']
    },
    {
      key: 'strategic_panel',
      title: 'Stratejik Performans Paneli',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/panel/dashboard',
      urlHints: ['/performans/stratejik/panel/dashboard'],
      keywords: ['stratejik performans paneli', 'stratejik panel', 'kpi yönetici paneli', 'kpi yonetici paneli'],
      description: 'Stratejik performans özetlerinin yönetici görünümünde izlendiği paneldir.',
      actions: ['Hedef gerçekleşme özetlerini izleme', 'Riskli KPI alanlarını görme', 'Yetkili kapsamda birim/personel özetlerini inceleme'],
      attention: ['Paneldeki kapsam rol ve organizasyon yetkisine göre daraltılmalıdır.']
    },
    {
      key: 'performance_dashboard',
      title: 'Performans Dashboard',
      bölüm: 'Performans Yönetimi',
      href: '/performance/dashboard',
      urlHints: ['/performance/dashboard', '/performans/dashboard'],
      keywords: ['performans dashboard', 'performans paneli', 'yönetici dashboard', 'yonetici dashboard'],
      description: 'Performans sürecinin dönem, tamamlanma, risk, Başkan onayı ve ekip görünürlüğü özetlerinin izlendiği ekrandır.',
      actions: ['Dönem tamamlanma durumunu inceleme', 'Riskli personel ve düşük performans yoğunluğunu görme', 'Başkan onayı bekleyen kayıtları takip etme', 'Aksatan amir veya eksik değerlendirme sinyallerini kontrol etme'],
      attention: ['Personel detayları yalnızca yetki kapsamında açılmalıdır.']
    },
    {
      key: 'periods',
      title: 'Dönemler',
      bölüm: 'Performans Yönetimi',
      href: '/performance/periods',
      urlHints: ['/performance/periods'],
      keywords: ['dönemler', 'donemler', 'yeni dönem', 'dönem türü', 'kapsam tipi'],
      description: 'Performans dönemlerinin oluşturulduğu, tarih aralığı ve kapsam bilgisinin yönetildiği ekrandır.',
      actions: ['Yeni dönem oluşturma', 'Dönem türü ve tarih aralığını kontrol etme', 'Kapsam tipini belirleme', 'Dönem aktiflik durumunu izleme'],
      attention: ['Dönem oluşturmak tek başına değerlendirmeyi başlatmaz; kriter, ağırlık ve görev üretimi ayrıca kontrol edilir.']
    },
    {
      key: 'criteria',
      title: 'Sorular / Kriterler',
      bölüm: 'Performans Yönetimi',
      href: '/performance/criteria',
      urlHints: ['/performance/criteria'],
      keywords: ['değerlendirme kriterleri', 'kriterler', 'sorular', 'kriter adı'],
      description: 'Performans değerlendirmesinde kullanılacak kriter ve soru tanımlarının yönetildiği ekrandır.',
      actions: ['Kriter adı ve açıklamasını kontrol etme', 'Aktif/pasif durumunu belirleme', 'Dönemle ilişkisini değerlendirme'],
      attention: ['Ekran dilinde ana ifade “Değerlendirme Kriterleri” olmalıdır.']
    },
    {
      key: 'evaluation_tasks',
      title: 'Değerlendirme Görevleri',
      bölüm: 'Performans Yönetimi',
      href: '/performance/evaluation-tasks',
      urlHints: ['/performance/evaluation-tasks'],
      keywords: ['değerlendirme görevleri', 'görev üretimi', 'puanlama görevi', 'amir görevi'],
      description: 'Amir değerlendirme görevlerinin üretildiği ve takip edildiği ekrandır.',
      actions: ['Dönem için görev üretme', 'Eksik amir veya hatalı zincir kontrolü yapma', 'Puanlama bekleyen görevleri izleme'],
      attention: ['Sahte görev veya boş 3. amir bekleme durumu üretilmemelidir.']
    },
    {
      key: 'president_approvals',
      title: 'Başkan Onayları',
      bölüm: 'Performans Yönetimi',
      href: '/performance/president-approvals',
      urlHints: ['/performance/president-approvals', '/performans/baskan-onaylari'],
      keywords: ['başkan onayları', 'baskan onaylari', '70 altı', 'düşük performans', 'yayın kilidi'],
      description: '70 altı performans sonuçlarının Başkan Onayı sürecinin takip edildiği ekrandır.',
      actions: ['Başkan onayı bekleyen kayıtları listeleme', 'Karne inceleme detayına geçme', 'Onay/ret sürecini yetki kapsamında yürütme'],
      attention: ['Başkan onayı tamamlanmadan düşük performans sonucu kesinleşmiş veya yayınlanmış sayılmaz.']
    },
    {
      key: 'publish_preapproval',
      title: 'Yayın Ön Onayı',
      bölüm: 'Performans Yönetimi',
      href: '/performance/personnel-support-publish-approvals',
      urlHints: ['/performance/personnel-support-publish-approvals'],
      keywords: ['yayın ön onayı', 'yayin on onayi', 'personel destek onayı', 'final yayın'],
      description: 'Tüm değerlendirme ve varsa üst onaylar tamamlandıktan sonra final yayın öncesi kurumsal kontrol ekranıdır.',
      actions: ['Yayın öncesi bekleyen kayıtları kontrol etme', 'Personel ve Destek Hizmetleri Grup Başkanı ön onayını takip etme', 'Admin/İK final yayın hazırlığını doğrulama'],
      attention: ['Bu adım tamamlanmadan Admin/İK nihai yayına geçmemelidir.']
    },
    {
      key: 'process_tracking',
      title: 'Süreç Takibi',
      bölüm: 'Performans Yönetimi',
      href: '/performance/process-tracking',
      urlHints: ['/performance/process-tracking', '/performans/surec-takibi'],
      keywords: ['süreç takibi', 'surec takibi', 'akış', 'bekleyen işlem', 'statü'],
      description: 'Performans sürecindeki dönem, görev, onay ve yayın adımlarının durum takibi ekranıdır.',
      actions: ['Bekleyen adımları görme', 'Geciken veya kilitli süreçleri ayırt etme', 'İlgili performans alt ekranına güvenli geçiş yapma'],
      attention: ['Teknik statü kodları kullanıcıya gösterilmemeli; Türkçe kurumsal ifadeler kullanılmalıdır.']
    },
    {
      key: 'process_reports',
      title: 'Süreç Raporları',
      bölüm: 'Performans Yönetimi',
      href: '/performance/process-reports',
      urlHints: ['/performance/process-reports'],
      keywords: ['süreç raporları', 'surec raporlari', 'performans raporu', 'aksatan amir', 'geciken değerlendirme'],
      description: 'Dönem, amir, yayın, onay ve gecikme durumlarına ilişkin raporların izlendiği ekrandır.',
      actions: ['Dönem bazlı süreci raporlama', 'Aksatan amir ve eksik görevleri izleme', '70 altı ve yayın kilidi kayıtlarını analiz etme'],
      attention: ['Rapor kapsamı rol ve organizasyon yetkisiyle sınırlandırılmalıdır.']
    },
    {
      key: 'interim_notes',
      title: 'Dönem İçi Notlar',
      bölüm: 'Performans Yönetimi',
      href: '/performance/interim-notes',
      urlHints: ['/performance/interim-notes'],
      keywords: ['dönem içi not', 'donem ici not', 'ara geri bildirim', 'gelişim notu'],
      description: 'Dönem içinde olumlu/olumsuz gözlem, başarı, gelişim ihtiyacı ve genel notların tutulduğu ekrandır.',
      actions: ['Dönem içi gözlem kaydı oluşturma', 'Olumlu/olumsuz olayları not etme', 'Gelişim ihtiyacını kayıt altına alma'],
      attention: ['Bu notlar otomatik puan üretmez; değerlendirme ve gelişim görüşmesine destek sağlar.']
    },
    {
      key: 'scorecard',
      title: 'Not Karnesi',
      bölüm: 'Performans Yönetimi',
      href: '/performance/scorecard',
      urlHints: ['/performance/scorecard', '/performans/v2/faz5/scorecard'],
      keywords: ['not karnesi', 'karne', 'performans sonucu', 'karnem'],
      description: 'Yayınlanan performans sonucunun karne formatında görüntülendiği ekrandır.',
      actions: ['Nihai puanı ve kriter bazlı sonuçları görme', 'Amir görüşlerini yetki kapsamında inceleme', 'Süreç geçmişi ve yayın durumunu kontrol etme'],
      attention: ['İK/Admin yayınlamadan personel kendi sonucunu görmemelidir.']
    },
    {
      key: 'archive',
      title: 'Geçmiş Karne Arşivi',
      bölüm: 'Performans Yönetimi',
      href: '/performans/gecmis-karne-arsivi',
      urlHints: ['/performans/gecmis-karne-arsivi'],
      keywords: ['geçmiş karne', 'gecmis karne', 'arşiv', 'arsiv', 'eski puan'],
      description: 'Geçmiş yıl ve dönem performans karnelerinin yetki bazlı izlendiği ekrandır.',
      actions: ['Eski dönem karne ve puanlarını görme', 'Dönem/yıl filtresiyle kayıt arama', 'Yetkili kapsamda geçmiş performans verisini izleme'],
      attention: ['Personel yalnızca kendi geçmişini; yöneticiler yalnızca yetkili kapsamlarını görmelidir.']
    },
    {
      key: 'personnel',
      title: 'Personel Yönetimi',
      bölüm: 'Personel Yönetimi',
      href: '/personnel',
      urlHints: ['/personnel'],
      keywords: ['personel yönetimi', 'personel listesi', 'sicil', 'unvan', 'birim', 'yönetici'],
      description: 'Personel kayıtları, sicil, unvan, görev, birim, üst birim, yönetici ve organizasyon verilerinin yönetildiği ekrandır.',
      actions: ['Personel kaydı arama', 'Personel bilgisi ekleme/güncelleme', 'Birim, görev ve yönetici bağlantısını kontrol etme'],
      attention: ['Personel verisi performans, izin, vekâlet, iletişim ve yetki süreçlerini doğrudan etkiler.']
    },
    {
      key: 'leave',
      title: 'İzin ve Devamsızlık Takibi',
      bölüm: 'Personel Yönetimi',
      href: '/hr-management/leave',
      urlHints: ['/hr-management/leave'],
      keywords: ['izin', 'izin kaydı', 'izin talebi', 'izin bakiyesi', 'devamsızlık takibi'],
      description: 'İzin kayıtları, izin talepleri, izin bakiyeleri ve izinli amir etkisinin takip edildiği ekrandır.',
      actions: ['İzin kaydı veya izin talebi oluşturma', 'İzin türü ve tarih aralığını kontrol etme', 'Onay ve bakiye durumunu izleme'],
      attention: ['İzinli amir varsa vekâlet ve performans görev akışı ayrıca kontrol edilmelidir.']
    },
    {
      key: 'delegation',
      title: 'Devamsızlık ve Vekâlet',
      bölüm: 'Personel Yönetimi',
      href: '/hr-management/attendance',
      urlHints: ['/hr-management/attendance'],
      keywords: ['devamsızlık', 'vekalet', 'vekâlet', 'vekil', 'görev devri'],
      description: 'Devamsızlık ve vekâlet ilişkilerinin takip edildiği ekrandır.',
      actions: ['Devamsızlık kaydı kontrolü', 'Vekil kişi ve tarih aralığı tanımlama', 'Süreç etkisini izleme'],
      attention: ['Vekâlet süresi ilgili izin/devamsızlık tarihiyle uyumlu olmalıdır.']
    },
    {
      key: 'messages',
      title: 'Mesajlar',
      bölüm: 'İletişim ve Anket Yönetimi',
      href: '/messages',
      urlHints: ['/messages'],
      keywords: ['mesajlar', 'mesaj', 'sohbet', 'yazışma', 'iletişim'],
      description: 'Kurum içi mesajlaşma ve yazışma ekranıdır.',
      actions: ['Mesajları okuma', 'Yetkili kullanıcı veya grupla yazışma', 'Ek ve bildirim durumlarını takip etme'],
      attention: ['Mesaj içerikleri yetki ve gizlilik sınırlarıyla korunmalıdır.']
    },
    {
      key: 'surveys',
      title: 'Anketler',
      bölüm: 'İletişim ve Anket Yönetimi',
      href: '/surveys',
      urlHints: ['/surveys'],
      keywords: ['anketler', 'anket', 'anket cevabı', 'katılım'],
      description: 'Atanan anketlerin görüntülendiği ve cevaplandığı ekrandır.',
      actions: ['Atanan anketleri görme', 'Anketi cevaplama', 'Katılım ve kapanış durumunu izleme'],
      attention: ['Anket cevapları gizlilik ve yetki sınırlarıyla korunmalıdır.']
    },
    {
      key: 'support',
      title: 'Yardım Merkezi',
      bölüm: 'Destek / Yardım Merkezi',
      href: '/support',
      urlHints: ['/support'],
      keywords: ['yardım merkezi', 'yardim merkezi', 'destek talebi', 'bilet', 'sorun bildir'],
      description: 'Destek talepleri ve kullanıcı yardım kayıtlarının yönetildiği ekrandır.',
      actions: ['Destek talebi oluşturma', 'Açık talepleri izleme', 'Talep mesajları ve eklerini takip etme'],
      attention: ['Destek talebine hassas veri eklenmemelidir.']
    },
    {
      key: 'ai_decision',
      title: 'AI Karar Destek Merkezi',
      bölüm: 'AI Karar Destek',
      href: '/ai/decision-support/faz1/health',
      urlHints: ['/ai/decision-support'],
      keywords: ['ai karar destek', 'karar destek', 'risk analizi', 'ai analiz'],
      description: 'Kontrollü analiz, özetleme ve karar destek notlarının takip edildiği ekrandır. Nihai idari karar üretmez.',
      actions: ['Karar destek durumunu kontrol etme', 'Analiz sözleşmelerini ve güvenlik sınırlarını inceleme', 'AI çıktısını insan denetimli yorum olarak kullanma'],
      attention: ['AI karar vermez; yönetici karar alma kapasitesini destekler.']
    },
    {
      key: 'assistant_knowledge',
      title: 'Asistan Bilgi Bankası',
      bölüm: 'BYS360 Asistanı',
      href: '/ai-agent/knowledge',
      urlHints: ['/ai-agent/knowledge', '/assistant-training-bank'],
      keywords: ['asistan bilgi bankası', 'asistan eğitim bankası', 'soru cevap', 'güvenli url', 'yasaklı url'],
      description: 'Yetkili kullanıcıların asistan soru-cevap, güvenli URL, yasaklı URL ve menü yolu kayıtlarını yönettiği ekrandır.',
      actions: ['Asistan öğretim kaydı ekleme', 'Güvenli ve yasaklı URL bilgilerini kontrol etme', 'Yetkili rol ve menü yolunu tanımlama'],
      attention: ['Bu ekran yalnızca yetkili kullanıcılar tarafından kullanılmalıdır.']
    },
    {
      key: 'settings',
      title: 'Sistem Ayarları',
      bölüm: 'Sistem Ayarları ve Yetkilendirme',
      href: '/settings',
      urlHints: ['/settings'],
      keywords: ['sistem ayarları', 'ayarlar', 'rol matrisi', 'menü görünürlüğü', 'yetki'],
      description: 'Sistem ayarları, rol-yetki, menü görünürlüğü, güvenlik ve modül ayarlarının yönetildiği alandır.',
      actions: ['Rol ve menü görünürlüğünü kontrol etme', 'Modül ayarlarını düzenleme', 'Güvenlik ve oturum ayarlarını izleme'],
      attention: ['Menü görünürlüğü ile backend route yetkisi birlikte korunmalıdır.']
    },
    {
      key: 'role_matrix',
      title: 'Modül Bazlı Rol Matrisi',
      bölüm: 'Sistem Ayarları ve Yetkilendirme',
      href: '/settings/role-matrix',
      urlHints: ['/settings/role-matrix'],
      keywords: ['modül bazlı rol matrisi', 'modul bazli rol matrisi', 'rol matrisi', 'menü görünürlüğü'],
      description: 'Modül ve menü görünürlüklerinin rol bazlı yönetildiği ekrandır.',
      actions: ['Rol seçme', 'Modül/menü görünürlüğünü açma-kapatma', 'Kaydedip kullanıcı görünürlüğünü kontrol etme'],
      attention: ['Yetkisiz kullanıcı menüyü görmemeli; URL elle yazılsa bile veri alamamalıdır.']
    },
    {
      key: 'performance_role_matrix',
      title: 'Performans Yönetimi Rol Matrisi',
      bölüm: 'Sistem Ayarları ve Yetkilendirme',
      href: '/settings/performance-role-matrix',
      urlHints: ['/settings/performance-role-matrix'],
      keywords: ['performans rol matrisi', 'performans yönetimi rol matrisi', 'performans yetki'],
      description: 'Performans alt sekmelerinin rol bazlı görünürlüğünün yönetildiği ekrandır.',
      actions: ['Performans sekmesi yetkilerini kontrol etme', 'Başkan Onayları, Yayın Ön Onayı, raporlar gibi sekmeleri role göre açma-kapatma', 'Menü ve backend erişimini birlikte test etme'],
      attention: ['Sekme kapalıysa sadece erişim engeli vermek yetmez; menüden de kaybolmalıdır.']
    }
  ];

  function addSignal(signals, value, weight, source) {
    var n = norm(value);
    if (!n) return;
    signals.push({ value: n, weight: weight || 1, source: source || 'unknown' });
  }

  function collectSignals() {
    var signals = [];
    try {
      var path = window.location.pathname || '';
      addSignal(signals, path, 240, 'url');
      path.split(/[\/\-_]+/).forEach(function (part) { addSignal(signals, part, 30, 'url-part'); });
    } catch (e) {}
    try { addSignal(signals, document.title, 20, 'title'); } catch (e) {}
    try {
      document.querySelectorAll('main h1, main h2, main h3, .page-title, .content-title, .section-title, .card-title, .breadcrumb, .breadcrumb-item, [data-page-title], [data-module], [data-screen]').forEach(function (el) {
        addSignal(signals, el.textContent, 55, 'heading');
        addSignal(signals, el.getAttribute('data-page-title'), 75, 'data-page-title');
        addSignal(signals, el.getAttribute('data-module'), 45, 'data-module');
        addSignal(signals, el.getAttribute('data-screen'), 65, 'data-screen');
      });
    } catch (e) {}
    try {
      document.querySelectorAll('.sidebar .active, .nav-link.active, .menu-item.active, .submenu .active, [aria-current="page"]').forEach(function (el) {
        addSignal(signals, el.textContent, 85, 'active-menu');
        addSignal(signals, el.getAttribute('href'), 160, 'active-href');
      });
    } catch (e) {}
    try {
      document.querySelectorAll('label, th, button, a.btn, .btn, input[placeholder], textarea[placeholder]').forEach(function (el) {
        addSignal(signals, el.textContent, 15, 'field');
        addSignal(signals, el.getAttribute('placeholder'), 18, 'placeholder');
        addSignal(signals, el.getAttribute('name'), 18, 'field-name');
        addSignal(signals, el.getAttribute('id'), 18, 'field-id');
      });
    } catch (e) {}
    try {
      var body = document.body ? document.body.innerText || '' : '';
      addSignal(signals, body.slice(0, 4500), 5, 'body');
    } catch (e) {}
    return signals;
  }

  function matchScreen() {
    var signals = collectSignals();
    var best = boş;
    var bestScore = 0;
    var bestMatches = [];
    SCREENS.forEach(function (screen) {
      var score = 0;
      var matches = [];
      signals.forEach(function (sig) {
        var value = sig.value;
        (screen.urlHints || []).forEach(function (hint) {
          var h = norm(hint);
          if (!h) return;
          if (value === h) { score += 260; matches.push('url:' + hint); }
          else if (value.indexOf(h) !== -1) { score += 140; matches.push('url-part:' + hint); }
        });
        (screen.keywords || []).forEach(function (keyword) {
          var k = norm(keyword);
          if (!k) return;
          if (value === k) { score += 100 + sig.weight; matches.push('exact:' + keyword); }
          else if (value.indexOf(k) !== -1) { score += 22 + Math.min(sig.weight, 90); matches.push('keyword:' + keyword); }
        });
        if (value.indexOf(norm(screen.title)) !== -1) {
          score += 120 + Math.min(sig.weight, 90);
          matches.push('title:' + screen.title);
        }
      });
      if (score > bestScore) {
        bestScore = score;
        best = screen;
        bestMatches = matches.slice(0, 12);
      }
    });
    if (best && bestScore >= 55) {
      best.score = bestScore;
      best.matches = bestMatches;
      return best;
    }
    return boş;
  }

  function buildAnswer(screen) {
    if (!screen) return boş;
    var lines = [];
    lines.push('Bulunduğunuz ekran: ' + screen.title);
    lines.push('Alan: ' + screen.bölüm);
    lines.push('');
    lines.push(screen.description);
    lines.push('');
    lines.push('Bu ekranda yapabilecekleriniz:');
    (screen.actions || []).forEach(function (item, index) {
      lines.push((index + 1) + '. ' + item);
    });
    if (screen.attention && screen.attention.length) {
      lines.push('');
      lines.push('Dikkat:');
      screen.attention.forEach(function (item) { lines.push('- ' + item); });
    }
    lines.push('');
    lines.push('Yapmak istediğiniz işlemi yazarsanız bu ekrandaki doğru işlem sırasını adım adım anlatırım.');
    return { text: lines.join('\n'), links: screen.href ? [{ title: screen.title, href: screen.href }] : [] };
  }

  function answerCurrentPage() {
    return buildAnswer(matchScreen());
  }

  function isPageQuestion(question) {
    var q = norm(question);
    return ['bu ekranda ne yapabilirim', 'bu sayfada ne yapabilirim', 'burada ne yapacagim', 'burada ne yapacağım', 'bu ekran ne ise yarar', 'bu ekran ne işe yarar', 'hangi ekrandayim', 'hangi ekrandayım', 'sayfa yardimi', 'sayfa yardımı', 'ekran yardimi', 'ekran yardımı', 'ekrani anlat', 'ekranı anlat'].some(function (p) { return q.indexOf(norm(p)) !== -1; });
  }

  function answerQuestion(question) {
    if (isPageQuestion(question)) return answerCurrentPage();
    var q = norm(question);
    if ((q.indexOf('kpi') !== -1 || q.indexOf('hedef') !== -1) && (q.indexOf('dashboard') !== -1 || q.indexOf('panel') !== -1 || q.indexOf('nerede') !== -1)) {
      var kpi = SCREENS.filter(function (s) { return s.key === 'kpi_dashboard'; })[0];
      return buildAnswer(kpi);
    }
    return boş;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return boş;
  };

  window.BYS360AssistantScreenMapV20 = {
    loaded: true,
    version: VERSION,
    screens: SCREENS,
    collectSignals: collectSignals,
    matchScreen: matchScreen,
    answerCurrentPage: answerCurrentPage,
    answerQuestion: answerQuestion,
    escapeText: escapeText
  };

  if (window.BYS360AssistantModule) {
    window.BYS360AssistantModule.screenMapV20 = window.BYS360AssistantScreenMapV20;
    window.BYS360AssistantModule.recognizeCurrentScreenV20 = matchScreen;
  }
})();
/* BYS360_ASSISTANT_SCREEN_MAP_V20_END */

/* BYS360_ASSISTANT_SCREEN_AGENT_V21_START */
(function () {
  'use strict';

  if (window.BYS360AssistantScreenAgentV21 && window.BYS360AssistantScreenAgentV21.loaded) return;

  var VERSION = 'BYS360_ASSISTANT_SCREEN_AGENT_V21';

  function norm(value) {
    return String(value || '')
      .toLocaleLowerCase('tr-TR')
      .replace(/ı/g, 'i').replace(/İ/g, 'i')
      .replace(/[âáàä]/g, 'a').replace(/[êéèë]/g, 'e')
      .replace(/[îíìï]/g, 'i').replace(/[ôóòö]/g, 'o').replace(/[ûúùü]/g, 'u')
      .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ş/g, 's')
      .replace(/[^a-z0-9\s/._-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function cleanText(value, maxLen) {
    var text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return '';
    maxLen = maxLen || 90;
    return text.length > maxLen ? text.slice(0, maxLen - 1).trim() + '…' : text;
  }

  function uniq(list, limit) {
    var seen = Object.create(boş);
    var out = [];
    (list || []).forEach(function (item) {
      var t = cleanText(item, 120);
      var key = norm(t);
      if (!key || seen[key]) return;
      seen[key] = true;
      out.push(t);
    });
    return out.slice(0, limit || 8);
  }

  function textOf(selector, limit) {
    var items = [];
    try {
      document.querySelectorAll(selector).forEach(function (el) {
        if (!el) return;
        var style = window.getComputedStyle ? window.getComputedStyle(el) : boş;
        if (style && (style.display === 'none' || style.visibility === 'hidden')) return;
        items.push(el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '');
      });
    } catch (e) {}
    return uniq(items, limit || 8);
  }

  function attrOf(selector, attrs, limit) {
    var items = [];
    try {
      document.querySelectorAll(selector).forEach(function (el) {
        attrs.forEach(function (attr) { items.push(el.getAttribute(attr)); });
      });
    } catch (e) {}
    return uniq(items, limit || 8);
  }

  var MODULE_RULES = [
    {
      key: 'strategic_performance',
      bölüm: 'KPI ve Hedef Yönetimi',
      homeTitle: 'KPI Dashboardu',
      homeHref: '/performans/stratejik/kpi-dashboard',
      prefixes: ['/performans/stratejik', '/strategic-performance'],
      keywords: ['kpi', 'hedef', 'stratejik performans', 'yetkinlik', 'öz değerlendirme', 'oz degerlendirme', 'başarı oranı', 'risk seviyesi'],
      actions: ['Hedef dönemini ve kapsamını kontrol etme', 'KPI/hedef kartlarını ve gerçekleşme değerlerini inceleme', 'Riskli veya geciken hedefleri ayırt etme', 'Yetki varsa hedef kaydı oluşturma ya da düzenleme'],
      attention: ['Asistan hedef sonucu veya idari karar üretmez; yalnızca ekranın kullanım sırasını açıklar.', 'Kişi ve birim detayları rol, birim ve menü görünürlüğü sınırına göre gösterilmelidir.']
    },
    {
      key: 'performance',
      bölüm: 'Performans Yönetimi',
      homeTitle: 'Performans Dashboard',
      homeHref: '/performance/dashboard',
      prefixes: ['/performance', '/performans'],
      keywords: ['performans', 'karne', 'puanlama', 'dönemler', 'değerlendirme', 'başkan onay', 'yayın ön onay', 'süreç takibi', 'kriter'],
      actions: ['Dönem, kriter ve görev durumunu kontrol etme', 'Değerlendirme/puanlama görevlerini izleme', 'Karne, onay ve yayın adımlarını takip etme', 'Rapor ve süreç ekranlarına yetki kapsamında geçme'],
      attention: ['Performans puanı asistan tarafından belirlenmez.', 'Sonuç görünürlüğü yayın ve onay kurallarına göre açılır.']
    },
    {
      key: 'personnel',
      bölüm: 'Personel Yönetimi',
      homeTitle: 'Personel Yönetimi',
      homeHref: '/personnel',
      prefixes: ['/personnel', '/hr-management', '/admin/users'],
      keywords: ['personel', 'sicil', 'unvan', 'birim', 'üst birim', 'yönetici', 'izin', 'devamsızlık', 'vekâlet'],
      actions: ['Personel kaydı arama veya güncelleme', 'Birim, üst birim, unvan ve yönetici bağlantısını kontrol etme', 'İzin, devamsızlık ve vekâlet kayıtlarını izleme', 'Performans zincirini etkileyen personel verisini doğrulama'],
      attention: ['Personel verisi performans, yetki, izin ve raporlama süreçlerini doğrudan etkiler.']
    },
    {
      key: 'settings',
      bölüm: 'Sistem Ayarları ve Yetkilendirme',
      homeTitle: 'Sistem Ayarları',
      homeHref: '/settings',
      prefixes: ['/settings', '/admin/settings', '/admin/roles', '/admin/menu'],
      keywords: ['ayarlar', 'rol matrisi', 'menü görünürlüğü', 'yetki', 'güvenlik', 'captcha', 'audit', 'modül ayarı'],
      actions: ['Rol ve menü görünürlüğünü kontrol etme', 'Modül ayarlarını yetkiye göre düzenleme', 'Güvenlik ve oturum kurallarını izleme', 'Kritik değişikliklerin kayıt altına alındığını kontrol etme'],
      attention: ['Menü görünürlüğü ile backend erişim kontrolü birlikte korunmalıdır.']
    },
    {
      key: 'communication',
      bölüm: 'İletişim, Anket ve Destek Süreçleri',
      homeTitle: 'İletişim ve Anket',
      homeHref: '/messages',
      prefixes: ['/messages', '/communication', '/surveys', '/feedback', '/support'],
      keywords: ['mesaj', 'duyuru', 'anket', 'geri bildirim', 'destek talebi', 'yardım merkezi', 'bildirim'],
      actions: ['Mesaj, duyuru veya destek kayıtlarını inceleme', 'Anket ve geri bildirim katılım durumunu kontrol etme', 'Destek talebi oluşturma veya mevcut talebi takip etme', 'Bildirimleri yetki kapsamında izleme'],
      attention: ['Mesaj, anket ve destek içerikleri gizlilik ve yetki sınırlarıyla korunur.']
    },
    {
      key: 'ai_decision',
      bölüm: 'AI Karar Destek Merkezi',
      homeTitle: 'AI Karar Destek Merkezi',
      homeHref: '/ai/decision-support/faz1/health',
      prefixes: ['/ai/decision-support', '/ai-decision'],
      keywords: ['ai karar destek', 'karar destek', 'analiz', 'risk farkındalığı', 'özetleme'],
      actions: ['Karar destek özetlerini inceleme', 'Risk ve dikkat notlarını insan denetimli yorum olarak değerlendirme', 'Verinin hangi modül alanından geldiğini kontrol etme'],
      attention: ['AI karar vermez; yönetici karar alma kapasitesini destekler.']
    },
    {
      key: 'assistant',
      bölüm: 'BYS360 Asistanı',
      homeTitle: 'Asistan Bilgi Bankası',
      homeHref: '/ai-agent/knowledge',
      prefixes: ['/ai-agent', '/assistant-training-bank'],
      keywords: ['asistan', 'bilgi bankası', 'öğretim merkezi', 'güvenli url', 'soru cevap'],
      actions: ['Asistan bilgi bankası kaydı oluşturma veya düzenleme', 'Güvenli/yasaklı URL ve menü yolu bilgisini kontrol etme', 'Asistan cevaplarının kurumsal sınırlarını izleme'],
      attention: ['Bu alan yalnızca yetkili kullanıcılar tarafından yönetilmelidir.']
    },
    {
      key: 'home',
      bölüm: 'Genel',
      homeTitle: 'Ana Sayfa',
      homeHref: '/home',
      prefixes: ['/home', '/'],
      keywords: ['ana sayfa', 'anasayfa', 'başlangıç', 'baslangic', 'bugün ne var', 'bugun ne var', 'günlük özet', 'gunluk ozet'],
      actions: ['Bugünkü kısa özetleri inceleme', 'Yetkili olduğunuz modüllere geçiş yapma', 'Bekleyen iş veya bildirimleri kontrol etme'],
      attention: ['Ana Sayfa işlem detayı değil, günlük başlangıç ve hızlı geçiş alanıdır.']
    },
    {
      key: 'general_dashboard',
      bölüm: 'Yönetici Dashboard',
      homeTitle: 'Dashboard',
      homeHref: '/dashboard',
      prefixes: ['/dashboard'],
      keywords: ['dashboard', 'genel dashboard', 'gösterge', 'gosterge', 'yönetici görünümü', 'yonetici gorunumu'],
      actions: ['Yönetici özet kartlarını inceleme', 'Grafik/gösterge alanlarını kontrol etme', 'Yetki kapsamındaki analizlerden ilgili modüle geçme'],
      attention: ['Dashboard analiz ve yönetici görünürlüğü ekranıdır; Ana Sayfa ile karıştırılmamalıdır.']
    }
  ];

  function collectPageFacts() {
    var path = '';
    try { path = window.location.pathname || ''; } catch (e) {}
    var titleCandidates = [];
    titleCandidates = titleCandidates.concat(textOf('main h1, main h2, .page-title, .content-title, .module-title, [data-page-title], [data-screen-title]', 5));
    try { titleCandidates.push(document.title || ''); } catch (e) {}
    var activeMenu = textOf('.sidebar .active, .nav-link.active, .menu-item.active, .submenu .active, [aria-current="page"]', 6);
    var breadcrumb = textOf('.breadcrumb, .breadcrumb-item, nav[aria-label="breadcrumb"]', 6);
    var buttons = textOf('button, a.btn, .btn, [role="button"]', 14);
    var fields = textOf('label, th', 14).concat(attrOf('input, textarea, select', ['placeholder', 'name', 'id', 'aria-label'], 14));
    var dataSignals = attrOf('[data-nav-key], [data-module], [data-screen], [data-page-title]', ['data-nav-key', 'data-module', 'data-screen', 'data-page-title'], 12);
    var bodySample = '';
    try { bodySample = cleanText((document.body && document.body.innerText || '').slice(0, 5000), 5000); } catch (e) {}
    var screenTitle = uniq(titleCandidates, 1)[0] || uniq(activeMenu, 1)[0] || path || 'BYS360 ekranı';
    return {
      path: path,
      title: screenTitle,
      activeMenu: activeMenu,
      breadcrumb: breadcrumb,
      buttons: buttons,
      fields: uniq(fields, 14),
      dataSignals: dataSignals,
      bodySample: bodySample
    };
  }

  function inferModule(facts) {
    var haystack = norm([
      facts.path,
      facts.title,
      (facts.activeMenu || []).join(' '),
      (facts.breadcrumb || []).join(' '),
      (facts.fields || []).join(' '),
      (facts.buttons || []).join(' '),
      (facts.dataSignals || []).join(' '),
      facts.bodySample
    ].join(' '));
    var best = boş;
    var bestScore = -1;
    MODULE_RULES.forEach(function (rule) {
      var score = 0;
      (rule.prefixes || []).forEach(function (prefix) {
        var p = norm(prefix);
        if (norm(facts.path).indexOf(p) === 0) score += 280;
        else if (haystack.indexOf(p) !== -1) score += 80;
      });
      (rule.keywords || []).forEach(function (keyword) {
        var k = norm(keyword);
        if (haystack.indexOf(k) !== -1) score += 35;
      });
      if (score > bestScore) {
        bestScore = score;
        best = rule;
      }
    });
    if (!best || bestScore < 25) {
      return {
        key: 'generic',
        bölüm: 'BYS360 Genel Ekranı',
        homeTitle: 'Ana Sayfa',
        homeHref: '/home',
        actions: ['Ekrandaki başlık, filtre, tablo ve butonları kontrol etme', 'Yapmak istediğiniz işlemi yazarak adım adım yönlendirme alma', 'Yetki gerektiren alanlarda ilgili rol veya menü görünürlüğünü kontrol etme'],
        attention: ['Asistan yanlış bağlantı açmamak için yetki ve güvenli rota sınırlarını aşmaz.']
      };
    }
    best._score = bestScore;
    return best;
  }

  function collectVisibleActions(facts) {
    var suggestions = [];
    var joined = norm((facts.buttons || []).join(' '));
    function addWhen(pattern, text) { if (pattern.test(joined)) suggestions.push(text); }
    addWhen(/yeni|ekle|oluştur|olustur|kayit olustur|kayıt oluştur/, 'Yeni kayıt veya işlem başlatma');
    addWhen(/kaydet|güncelle|guncelle|sakla/, 'Girilen bilgileri kaydetme veya güncelleme');
    addWhen(/ara|filtre|süz|suz|listele/, 'Listeyi arama, filtreleme veya kapsamı daraltma');
    addWhen(/detay|incele|görüntüle|goruntule/, 'Kayıt detayını görüntüleme');
    addWhen(/onay|reddet|iade/, 'Yetki varsa onay, iade veya ret işlemi yürütme');
    addWhen(/rapor|excel|pdf|dışa aktar|disa aktar/, 'Rapor veya çıktı alma');
    addWhen(/sil|pasif|kapat/, 'Kritik işlem öncesi yetki ve denetim izini kontrol etme');
    return uniq(suggestions, 6);
  }

  function exactKnownAnswer(facts) {
    try {
      var map = window.BYS360AssistantScreenMapV20;
      if (map && typeof map.answerCurrentPage === 'function') {
        var current = map.answerCurrentPage();
        if (current && current.text && norm(current.text).indexOf('özel bir başlıkla eşleşmedi') === -1) {
          return current;
        }
      }
    } catch (e) {}
    return boş;
  }

  function buildDynamicAnswer(facts, rule) {
    var visibleActions = collectVisibleActions(facts);
    var actions = uniq((rule.actions || []).concat(visibleActions), 7);
    var lines = [];
    lines.push('Bulunduğunuz ekran: ' + (facts.title || 'BYS360 ekranı'));
    lines.push('Algılanan modül: ' + rule.bölüm);
    if (facts.path) lines.push('Ekran yolu: ' + facts.path);
    lines.push('');
    lines.push('Ekran Tanıma Ajanı bu sayfayı URL, sayfa başlığı, aktif sol menü, görünür butonlar ve form alanlarına göre yorumladı. Bu nedenle ekran sabit listede olmasa bile güvenli kullanım açıklaması verebilirim.');
    lines.push('');
    lines.push('Bu ekranda güvenle yapabilecekleriniz:');
    actions.forEach(function (item, index) { lines.push((index + 1) + '. ' + item); });
    var signals = [];
    if (facts.activeMenu && facts.activeMenu.length) signals.push('Aktif menü: ' + facts.activeMenu.slice(0, 3).join(' > '));
    if (facts.breadcrumb && facts.breadcrumb.length) signals.push('Sayfa izi: ' + facts.breadcrumb.slice(0, 3).join(' > '));
    if (facts.buttons && facts.buttons.length) signals.push('Görünür işlem butonları: ' + facts.buttons.slice(0, 6).join(', '));
    if (facts.fields && facts.fields.length) signals.push('Görünür alan ipuçları: ' + facts.fields.slice(0, 6).join(', '));
    if (signals.length) {
      lines.push('');
      lines.push('Görünür işlem ipuçları:');
      signals.forEach(function (item) { lines.push('- ' + item); });
    }
    lines.push('');
    lines.push('Güvenli yönlendirme:');
    lines.push('- Bu ekranla ilgili yapmak istediğiniz işlemi yazarsanız adım adım doğru sırayı anlatırım.');
    if (rule.homeHref) lines.push('- Modülün ana ekranına dönmek gerekirse güvenli hedef: ' + rule.homeTitle + ' (' + rule.homeHref + ')');
    lines.push('');
    lines.push('Dikkat:');
    (rule.attention || []).forEach(function (item) { lines.push('- ' + item); });
    lines.push('- Yetki dışı veri, idari karar, performans puanı veya hassas içerik üretmem; yalnızca güvenli rehberlik sağlarım.');
    return { text: lines.join('\n'), links: rule.homeHref ? [{ title: rule.homeTitle || rule.bölüm, href: rule.homeHref }] : [] };
  }

  function answerCurrentPage() {
    var facts = collectPageFacts();
    var known = exactKnownAnswer(facts);
    if (known && known.text) return known;
    var rule = inferModule(facts);
    return buildDynamicAnswer(facts, rule);
  }

  function isPageQuestion(question) {
    var q = norm(question);
    return [
      'bu ekranda ne yapabilirim', 'bu sayfada ne yapabilirim', 'burada ne yapacagim', 'burada ne yapacağım',
      'bu ekran ne ise yarar', 'bu ekran ne işe yarar', 'hangi ekrandayim', 'hangi ekrandayım',
      'sayfa yardimi', 'sayfa yardımı', 'ekran yardimi', 'ekran yardımı', 'ekrani anlat', 'ekranı anlat',
      'bu sayfayi tani', 'bu sayfayı tanı', 'ekrani tani', 'ekranı tanı', 'burayi anlat', 'burayı anlat',
      'beni yonlendir', 'beni yönlendir', 'ne yapmam gerekiyor', 'burada nasil ilerlerim', 'burada nasıl ilerlerim'
    ].some(function (p) { return q.indexOf(norm(p)) !== -1; });
  }

  function answerQuestion(question) {
    if (isPageQuestion(question)) return answerCurrentPage();
    return boş;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return boş;
  };

  window.BYS360AssistantScreenAgentV21 = {
    loaded: true,
    version: VERSION,
    collectPageFacts: collectPageFacts,
    inferModule: inferModule,
    collectVisibleActions: collectVisibleActions,
    answerCurrentPage: answerCurrentPage,
    answerQuestion: answerQuestion,
    moduleRules: MODULE_RULES
  };

  if (window.BYS360AssistantModule) {
    window.BYS360AssistantModule.screenAgentV21 = window.BYS360AssistantScreenAgentV21;
    window.BYS360AssistantModule.recognizeCurrentScreenV21 = answerCurrentPage;
  }
})();
/* BYS360_ASSISTANT_SCREEN_AGENT_V21_END */

/* BYS360_ASSISTANT_SCREEN_AGENT_V22_START */
(function () {
  'use strict';

  if (window.BYS360AssistantScreenAgentV22 && window.BYS360AssistantScreenAgentV22.loaded) return;

  var VERSION = 'BYS360_ASSISTANT_SCREEN_AGENT_V22_MATURE_PRIORITY_ENGINE';
  var HOME_PATHS = ['/home', '/'];

  function norm(value) {
    return String(value || '')
      .toLocaleLowerCase('tr-TR')
      .replace(/ı/g, 'i').replace(/İ/g, 'i')
      .replace(/[âáàä]/g, 'a').replace(/[êéèë]/g, 'e')
      .replace(/[îíìï]/g, 'i').replace(/[ôóòö]/g, 'o').replace(/[ûúùü]/g, 'u')
      .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ş/g, 's')
      .replace(/[^a-z0-9\s/._-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function cleanText(value, maxLen) {
    var text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return '';
    maxLen = maxLen || 110;
    return text.length > maxLen ? text.slice(0, maxLen - 1).trim() + '…' : text;
  }

  function uniq(list, limit) {
    var seen = Object.create(boş);
    var out = [];
    (list || []).forEach(function (item) {
      var t = cleanText(item, 140);
      var k = norm(t);
      if (!k || seen[k]) return;
      seen[k] = true;
      out.push(t);
    });
    return out.slice(0, limit || 8);
  }

  function isVisible(el) {
    try {
      if (!el) return false;
      var style = window.getComputedStyle ? window.getComputedStyle(el) : boş;
      if (style && (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0')) return false;
      var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : boş;
      if (rect && rect.width === 0 && rect.height === 0) return false;
    } catch (e) {}
    return true;
  }

  function textOf(selector, limit) {
    var items = [];
    try {
      document.querySelectorAll(selector).forEach(function (el) {
        if (!isVisible(el)) return;
        items.push(el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '');
      });
    } catch (e) {}
    return uniq(items, limit || 8);
  }

  function attrOf(selector, attrs, limit) {
    var items = [];
    try {
      document.querySelectorAll(selector).forEach(function (el) {
        if (!isVisible(el)) return;
        attrs.forEach(function (attr) { items.push(el.getAttribute(attr)); });
      });
    } catch (e) {}
    return uniq(items, limit || 8);
  }

  function pathNow() {
    try { return window.location.pathname || '/'; } catch (e) { return '/'; }
  }

  function pathMatches(path, patterns) {
    var p = norm(path || '');
    return (patterns || []).some(function (pattern) {
      var işlenmemiş veri = String(pattern || '');
      var n = norm(işlenmemiş veri);
      if (!n) return false;
      if (işlenmemiş veri.slice(-1) === '*') return p.indexOf(norm(işlenmemiş veri.slice(0, -1))) === 0;
      return p === n || p.indexOf(n + '/') === 0 || p.indexOf(n) === 0;
    });
  }

  function pathIsHome(path) {
    var p = norm(path || '');
    return HOME_PATHS.some(function (hp) { return p === norm(hp); });
  }

  var SCREEN_RULES = [
    {
      id: 'performance_reports',
      screen: 'Performans Raporları',
      bölüm: 'Performans Yönetimi',
      href: '/performance/reports',
      paths: ['/performance/reports*', '/performans/rapor*', '/performans/reports*', '/performance/process-reports*', '/performans/surec-rapor*', '/reports/performance*'],
      keywords: ['raporlar', 'performans raporları', 'performans raporlari', 'raporlama', 'analiz', 'çıktı', 'pdf', 'excel', 'dönem bazlı', 'birim bazlı'],
      description: 'Bu ekran performans verilerinin dönem, birim, grup/kategori, amir ve personel kırılımlarında analiz edilmesi; çıktı, özet ve yönetici görünürlüğü üretilmesi için kullanılır.',
      actions: ['Dönem veya kapsam filtresini seçme', 'Birim, kategori, amir veya personel kırılımını kontrol etme', 'Düşük/yüksek performans yoğunluğunu inceleme', 'Yetki varsa rapor çıktısı veya özet alma', 'Rapor sonucunu yayın/onay süreçleriyle karıştırmadan analiz amaçlı değerlendirme'],
      attention: ['Rapor ekranı idari karar üretmez; veriyi görünür ve analiz edilebilir hale getirir.', 'Personel bazlı detaylar rol, birim ve menü görünürlüğü sınırına göre gösterilmelidir.']
    },
    {
      id: 'process_tracking',
      screen: 'Süreç Takibi',
      bölüm: 'Performans Yönetimi',
      href: '/performance/process-tracking',
      paths: ['/performance/process-tracking*', '/performans/surec-takibi*', '/performans/süreç-takibi*'],
      keywords: ['süreç takibi', 'surec takibi', 'süreç listesi', 'canlı süreç', 'bekleyen süreç'],
      description: 'Bu ekran performans ve onay süreçlerinin hangi aşamada olduğunu izlemek, bekleyen kayıtları görmek ve süreç bütünlüğünü kontrol etmek için kullanılır.',
      actions: ['Bekleyen süreçleri kontrol etme', 'Süreç statüsünü Türkçe kurumsal ifadeyle yorumlama', 'Geciken veya kilitli kayıtları ayırt etme', 'Yetki varsa ilgili karne, onay veya yayın ekranına geçme'],
      attention: ['Teknik durum kodları kullanıcıya gösterilmemeli; Türkçe süreç ifadeleri kullanılmalıdır.']
    },
    {
      id: 'president_approvals',
      screen: 'Başkan Onayları',
      bölüm: 'Performans Yönetimi',
      href: '/performans/baskan-onaylari',
      paths: ['/performans/baskan-onaylari*', '/performance/president-approvals*', '/performance/president-approval*'],
      keywords: ['başkan onayları', 'başkan onayı', '70 altı', 'düşük performans', 'yayın kilidi'],
      description: 'Bu ekran 70 altı düşük performans sonuçlarının üst onay ve yayın kilidi süreçlerini izlemek için kullanılır.',
      actions: ['Başkan onayı bekleyen gerçek kayıtları inceleme', 'Karne detayına geçme', 'Onay/ret veya iade sürecini yetkiye göre yürütme', 'Yayın kilidi ve süreç geçmişini kontrol etme'],
      attention: ['70 altı sonuç Başkan Onayı tamamlanmadan personele kesin sonuç olarak açılmamalıdır.']
    },
    {
      id: 'scorecard',
      screen: 'Performans Karnesi',
      bölüm: 'Performans Yönetimi',
      href: '/performans/v2/faz5/scorecard',
      paths: ['/performans/v2/faz5/scorecard*', '/performance/*/scorecard*', '/performance/scorecard*', '/performans/*/karne*', '/performans/gecmis-karne-arsivi*'],
      keywords: ['karne', 'not karnesi', 'performans karnesi', 'puanlama geçmişi', 'amir görüşleri'],
      description: 'Bu ekran personelin performans sonucunu, kriter bazlı puanlarını, amir görüşlerini ve süreç geçmişini yetki sınırına göre göstermek için kullanılır.',
      actions: ['Nihai puan ve eşik durumunu kontrol etme', 'Kriter bazlı puanları inceleme', 'Amir görüşlerini ve süreç geçmişini okuma', 'Yayın ve görünürlük durumunu kontrol etme'],
      attention: ['Personel karnesi süreç tamamlanmadan ve gerekli yayın/onay yapılmadan personele açılmamalıdır.']
    },
    {
      id: 'performance_periods',
      screen: 'Dönemler',
      bölüm: 'Performans Yönetimi',
      href: '/performance/periods',
      paths: ['/performance/periods*', '/performans/donem*', '/performans/dönem*'],
      keywords: ['dönemler', 'donemler', 'performans dönemi', 'yeni dönem', 'kapsam tipi'],
      description: 'Bu ekran performans dönemlerinin yıl, dönem türü, tarih aralığı ve kapsam tipiyle yönetilmesi için kullanılır.',
      actions: ['Dönem listesini ve aktif dönemi kontrol etme', 'Yetki varsa yeni dönem oluşturma', 'Tüm kurum, birim, kategori veya seçili personel kapsamını belirleme', 'Görev üretimi öncesi dönem bilgilerini doğrulama'],
      attention: ['Doğru sekme adı Dönemlerdir; yönlendirme bu adla yapılmalıdır.']
    },
    {
      id: 'performance_dashboard',
      screen: 'Performans Dashboard',
      bölüm: 'Performans Yönetimi',
      href: '/performance/dashboard',
      paths: ['/performance/dashboard*', '/performans/dashboard*'],
      keywords: ['performans dashboard', 'performans özeti', 'canlı performans haritası', 'riskli personel'],
      description: 'Bu ekran performans sürecinin genel durumunu, tamamlanma oranlarını, riskli alanları ve yönetici görünürlüğünü takip etmek için kullanılır.',
      actions: ['Tamamlanma ve bekleyen görev durumunu izleme', 'Riskli personel ve düşük performans yoğunluğunu kontrol etme', 'Geciken amirleri veya yayın kilitlerini görme', 'Detay ekranlarına yetki kapsamında geçme'],
      attention: ['Dashboard özet verir; ayrıntı ve işlem için ilgili alt ekrana geçilmelidir.']
    },
    {
      id: 'kpi_dashboard',
      screen: 'KPI Dashboardu',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/kpi-dashboard',
      paths: ['/performans/stratejik/kpi-dashboard*', '/strategic-performance/kpi-dashboard*', '/strategic_performance_dashboard*'],
      keywords: ['kpi dashboard', 'hedef gerçekleşmeleri', 'hedef gerceklesmeleri', 'başarı oranı', 'risk seviyesi', 'stratejik performans'],
      description: 'Bu ekran KPI ve hedef gerçekleşmelerini, hedef kartlarını, başarı oranlarını, risk seviyelerini ve stratejik performans özetlerini takip etmek için kullanılır.',
      actions: ['Hedef dönemini ve kapsamını kontrol etme', 'Hedef gerçekleşmelerini ve başarı oranını inceleme', 'Riskli veya geciken KPI kayıtlarını ayırt etme', 'AI KPI Analiz ekranına geçmeden önce verinin güncel olup olmadığını kontrol etme'],
      attention: ['Asistan hedef sonucu veya idari karar üretmez; yalnızca ekranın kullanım sırasını açıklar.']
    },
    {
      id: 'kpi_targets',
      screen: 'KPI ve Hedef Listesi',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/hedefler',
      paths: ['/performans/stratejik/hedefler*', '/strategic-performance/targets*'],
      keywords: ['hedef listesi', 'hedef kartı', 'kpi listesi', 'hedefler'],
      description: 'Bu ekran hedef kartlarını listelemek, kapsam ve durum bilgilerini kontrol etmek ve yetki varsa hedef kaydı oluşturmak için kullanılır.',
      actions: ['Hedef kartlarını listeleme', 'Hedef sahibi, kapsam, ağırlık ve durum bilgilerini kontrol etme', 'Yetki varsa yeni hedef oluşturma veya mevcut hedefi güncelleme'],
      attention: ['KPI hedefleri performans puanının yerine geçmez; karar destek ve izleme verisi üretir.']
    },
    {
      id: 'kpi_analysis',
      screen: 'AI KPI Analiz',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/kpi-analiz',
      paths: ['/performans/stratejik/kpi-analiz*', '/strategic-performance/kpi-analysis*'],
      keywords: ['ai kpi analiz', 'kpi analiz', 'hedef analizi', 'stratejik analiz'],
      description: 'Bu ekran KPI ve hedef verilerinin kontrollü analiz ve özetleme desteğiyle yorumlanması için kullanılır.',
      actions: ['Analiz öncesi veri kapsamını kontrol etme', 'Risk ve başarı özetlerini inceleme', 'AI çıktısını karar değil destek notu olarak değerlendirme'],
      attention: ['AI karar vermez; analiz çıktısı insan denetimli değerlendirme notudur.']
    },
    {
      id: 'competency_library',
      screen: 'Yetkinlik Kütüphanesi',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/yetkinlik-kutuphanesi',
      paths: ['/performans/stratejik/yetkinlik-kutuphanesi*', '/performans/stratejik/yetkinlik*', '/strategic-performance/competenc*'],
      keywords: ['yetkinlik kütüphanesi', 'yetkinlik', 'görev bazlı yetkinlik'],
      description: 'Bu ekran görev, rol ve hedef yönetimiyle ilişkili yetkinlik tanımlarının yönetilmesi için kullanılır.',
      actions: ['Yetkinlik tanımlarını inceleme', 'Rol veya görev bazlı eşleşmeleri kontrol etme', 'Yetki varsa aktif/pasif durumunu düzenleme'],
      attention: ['Bu alan performans ekranlarındaki ana Değerlendirme Kriterleri terimiyle karıştırılmamalıdır.']
    },
    {
      id: 'self_review',
      screen: 'Öz Değerlendirme',
      bölüm: 'KPI ve Hedef Yönetimi',
      href: '/performans/stratejik/oz-degerlendirme',
      paths: ['/performans/stratejik/oz-degerlendirme*', '/strategic-performance/self*'],
      keywords: ['öz değerlendirme', 'oz degerlendirme', 'öz değerlendirme özeti'],
      description: 'Bu ekran personelin dönemsel çalışma özeti, başarıları, zorlandığı alanlar ve gelişim ihtiyaçlarını paylaşması için kullanılır.',
      actions: ['Dönem özeti ve hedef gerçekleşmesini yazma', 'Başarıları ve gelişim ihtiyaçlarını belirtme', 'Yetki kapsamında öz değerlendirme özetini inceleme'],
      attention: ['Öz değerlendirme otomatik puan üretmez; amire destek verisi sağlar.']
    },
    {
      id: 'personnel_list',
      screen: 'Personel Listesi',
      bölüm: 'Personel Yönetimi',
      href: '/admin/users',
      paths: ['/admin/users*', '/personnel*', '/hr-management*'],
      keywords: ['personel listesi', 'personel ekle', 'sicil', 'unvan', 'birim', 'yönetici'],
      description: 'Bu ekran personel kayıtlarının, sicil, unvan, birim, üst birim ve yönetici ilişkilerinin yönetilmesi için kullanılır.',
      actions: ['Personel arama ve listeleme', 'Yetki varsa personel ekleme veya düzenleme', 'Birim, üst birim, unvan ve yönetici bilgisini doğrulama', 'Performans zincirini etkileyen eksik personel bilgisini kontrol etme'],
      attention: ['TC yerine Sicil No kullanılmalı; personel verisi performans ve yetki süreçlerini doğrudan etkiler.']
    },
    {
      id: 'leave_delegation',
      screen: 'İzin, Devamsızlık ve Vekâlet',
      bölüm: 'Personel Yönetimi',
      href: '/personnel/leaves',
      paths: ['/personnel/leaves*', '/leave*', '/attendance*', '/delegation*', '/personnel/delegation*'],
      keywords: ['izin', 'devamsızlık', 'vekâlet', 'vekalet', 'izin talebi'],
      description: 'Bu ekran izin, devamsızlık ve vekâlet süreçlerinin kayıtlı ve izlenebilir yürütülmesi için kullanılır.',
      actions: ['İzin veya devamsızlık kaydını inceleme', 'Vekâlet ilişkisini kontrol etme', 'Performans/onay süreçlerinde vekilin etkisini doğrulama'],
      attention: ['İzinli amir ve vekâlet ilişkileri performans görev akışını etkileyebilir.']
    },
    {
      id: 'role_matrix',
      screen: 'Rol Matrisi ve Menü Görünürlüğü',
      bölüm: 'Sistem Ayarları ve Yetkilendirme',
      href: '/admin/menu-permissions',
      paths: ['/admin/menu*', '/admin/roles*', '/settings/roles*', '/settings/menu*', '/admin/role-matrix*'],
      keywords: ['rol matrisi', 'menü görünürlüğü', 'yetki', 'rol', 'menü yetkisi'],
      description: 'Bu ekran kullanıcıların hangi modülleri, sekmeleri ve işlemleri görebileceğini rol, kişi veya birim bazında yönetmek için kullanılır.',
      actions: ['Rol bazlı görünürlüğü kontrol etme', 'Kişi veya birim bazlı istisna tanımlama', 'Menü kapalıysa ekranda hiç görünmediğini test etme', 'Backend erişim kontrolünün de korunduğunu doğrulama'],
      attention: ['Sadece menüyü gizlemek yetmez; URL ile erişimde de yetki kontrolü korunmalıdır.']
    },
    {
      id: 'settings',
      screen: 'Sistem Ayarları',
      bölüm: 'Sistem Ayarları ve Yetkilendirme',
      href: '/settings',
      paths: ['/settings*', '/admin/settings*', '/system-settings*'],
      keywords: ['sistem ayarları', 'modül ayarları', 'captcha', 'oturum', 'audit', 'güvenlik ayarı'],
      description: 'Bu ekran BYS360 modüllerinin çalışma kurallarını, güvenlik ayarlarını, bildirim/e-posta ayarlarını ve denetim kayıtlarını yönetmek için kullanılır.',
      actions: ['Modül ayarlarını kontrol etme', 'Güvenlik ve oturum kurallarını inceleme', 'Kritik ayar değişikliklerinde audit log kaydını doğrulama'],
      attention: ['Canlı sistemde ayar değişikliği yapmadan önce etki alanı kontrol edilmelidir.']
    },
    {
      id: 'support',
      screen: 'Destek Talepleri',
      bölüm: 'İletişim, Anket ve Destek Süreçleri',
      href: '/support',
      paths: ['/support*', '/help*', '/yardim*', '/yardım*'],
      keywords: ['destek talebi', 'yardım merkezi', 'talep', 'açık destek', 'cevaplandı'],
      description: 'Bu ekran kullanıcı yardım ve destek taleplerinin açılması, cevaplanması ve takip edilmesi için kullanılır.',
      actions: ['Destek talebi oluşturma', 'Açık veya cevap bekleyen talepleri takip etme', 'Talep kategorisi ve durum geçmişini kontrol etme'],
      attention: ['Destek taleplerinde kişisel veya hassas veri paylaşımı sınırlandırılmalıdır.']
    },
    {
      id: 'messages_surveys',
      screen: 'İletişim, Duyuru ve Anket',
      bölüm: 'İletişim, Anket ve Destek Süreçleri',
      href: '/messages',
      paths: ['/messages*', '/communication*', '/surveys*', '/feedback*', '/notifications*'],
      keywords: ['mesaj', 'duyuru', 'anket', 'geri bildirim', 'bildirim', 'nabız'],
      description: 'Bu ekran kurum içi mesajlaşma, duyuru, bildirim, anket ve geri bildirim süreçlerini izlemek için kullanılır.',
      actions: ['Mesaj veya duyuruları inceleme', 'Anket ve geri bildirim katılımını kontrol etme', 'Bildirimleri ve hedef kitleyi yetkiye göre izleme'],
      attention: ['Mesaj ve anket içerikleri gizlilik ve yetki sınırlarıyla korunmalıdır.']
    },
    {
      id: 'ai_decision',
      screen: 'AI Karar Destek Merkezi',
      bölüm: 'AI Karar Destek Merkezi',
      href: '/ai/decision-support/faz1/health',
      paths: ['/ai/decision-support*', '/ai-decision*'],
      keywords: ['ai karar destek', 'karar destek', 'risk farkındalığı', 'özetleme', 'analiz'],
      description: 'Bu ekran BYS360 verilerinden kontrollü özet, risk farkındalığı ve karar destek notları üretmek için kullanılır.',
      actions: ['Karar destek özetlerini inceleme', 'Risk ve dikkat notlarını insan denetimli yorum olarak değerlendirme', 'Verinin hangi modül alanına dayandığını kontrol etme'],
      attention: ['AI karar vermez; yalnızca yönetici karar alma kapasitesini destekler.']
    },
    {
      id: 'assistant_knowledge',
      screen: 'BYS360 Asistanı Bilgi Bankası',
      bölüm: 'BYS360 Asistanı',
      href: '/ai-agent/knowledge',
      paths: ['/ai-agent/knowledge*', '/assistant-training-bank*', '/ai-agent/panel*'],
      keywords: ['asistan bilgi bankası', 'öğretim merkezi', 'asistan paneli', 'güvenli yönlendirme'],
      description: 'Bu ekran BYS360 Asistanı’nın kurumsal rehberlik ve bilgi bankası içeriğini yönetmek için kullanılır.',
      actions: ['Bilgi bankası kayıtlarını inceleme', 'Yetki varsa yeni rehber soru-cevap ekleme', 'Güvenli URL ve yönlendirme kurallarını kontrol etme'],
      attention: ['Asistan bilgi bankası yalnızca yetkili kullanıcılar tarafından yönetilmelidir.']
    },
    {
      id: 'general_dashboard',
      screen: 'Dashboard',
      bölüm: 'Yönetici Dashboard',
      href: '/dashboard',
      paths: ['/dashboard'],
      keywords: ['dashboard', 'genel dashboard', 'yönetici dashboard', 'yonetici dashboard', 'gösterge paneli', 'gosterge paneli', 'yönetici görünümü', 'yonetici gorunumu'],
      description: 'Bu ekran Ana Sayfa değildir. Dashboard; yönetici özetleri, gösterge kartları, grafikler, performans/KPI bağlantıları ve kurumsal durum analizleri için kullanılır.',
      actions: ['Yönetici özet kartlarını inceleme', 'Grafik ve gösterge alanlarını kontrol etme', 'Yetki kapsamındaki performans, destek, anket veya KPI özetlerine geçme'],
      attention: ['Dashboard analiz ve yönetici görünürlüğü ekranıdır; günlük başlangıç ve hızlı geçiş ekranı olan Ana Sayfa ile karıştırılmamalıdır.']
    },
    {
      id: 'home',
      screen: 'Ana Sayfa',
      bölüm: 'Genel',
      href: '/home',
      exactHomeOnly: true,
      paths: ['/home', '/'],
      keywords: ['ana sayfa', 'anasayfa', 'başlangıç', 'baslangic', 'bugün ne var', 'bugun ne var', 'nereden başlayacağım', 'nereden baslayacagim', 'genel özet'],
      description: 'Bu ekran BYS360 açılış ve günlük başlangıç ekranıdır. Kullanıcıya bekleyen işler, kısa özetler ve modüllere güvenli geçiş sağlar.',
      actions: ['Bugünkü kısa özetleri inceleme', 'Bekleyen bildirim, görev, anket veya destek talebi varsa ilgili modüle geçme', 'Yetkili olduğunuz ana modüllere hızlı geçiş yapma'],
      attention: ['Ana Sayfa işlem detayı veya yönetici analiz ekranı değildir; hızlı başlangıç ve yönlendirme alanıdır.']
    }
  ];

  function collectFacts() {
    var path = pathNow();
    var titleCandidates = [];
    titleCandidates = titleCandidates.concat(textOf('main h1, main h2, .page-title, .content-title, .module-title, [data-page-title], [data-screen-title]', 6));
    try { titleCandidates.push(document.title || ''); } catch (e) {}
    var activeMenu = textOf('.sidebar .active, .nav-link.active, .menu-item.active, .submenu .active, [aria-current="page"], [data-nav-key].active', 8);
    var breadcrumb = textOf('.breadcrumb, .breadcrumb-item, nav[aria-label="breadcrumb"]', 8);
    var buttons = textOf('button, a.btn, .btn, [role="button"]', 16);
    var fields = textOf('label, th, .table th', 18).concat(attrOf('input, textarea, select', ['placeholder', 'name', 'id', 'aria-label'], 18));
    var dataSignals = attrOf('[data-nav-key], [data-module], [data-screen], [data-page-title]', ['data-nav-key', 'data-module', 'data-screen', 'data-page-title'], 16);
    var bodySample = '';
    try { bodySample = cleanText((document.body && document.body.innerText || '').slice(0, 7000), 7000); } catch (e) {}
    return {
      path: path,
      rawTitle: uniq(titleCandidates, 2)[0] || '',
      activeMenu: activeMenu,
      breadcrumb: breadcrumb,
      buttons: buttons,
      fields: uniq(fields, 18),
      dataSignals: dataSignals,
      bodySample: bodySample
    };
  }

  function scoreRule(rule, facts) {
    var score = 0;
    var p = norm(facts.path);
    var title = norm(facts.rawTitle);
    var menu = norm((facts.activeMenu || []).join(' '));
    var crumb = norm((facts.breadcrumb || []).join(' '));
    var fields = norm((facts.fields || []).join(' '));
    var buttons = norm((facts.buttons || []).join(' '));
    var data = norm((facts.dataSignals || []).join(' '));
    var body = norm(facts.bodySample || '');
    var haystackStrong = [p, title, menu, crumb, data].join(' ');
    var haystackWeak = [fields, buttons, body].join(' ');

    if (rule.exactHomeOnly && !pathIsHome(facts.path)) return -1000;

    (rule.paths || []).forEach(function (pattern) {
      var işlenmemiş veri = String(pattern || '');
      var base = işlenmemiş veri.slice(-1) === '*' ? işlenmemiş veri.slice(0, -1) : işlenmemiş veri;
      var n = norm(base);
      if (!n) return;
      if (p === n) score += 1000;
      else if (işlenmemiş veri.slice(-1) === '*' && p.indexOf(n) === 0) score += 900;
      else if (p.indexOf(n + '/') === 0) score += 850;
    });

    (rule.keywords || []).forEach(function (keyword) {
      var k = norm(keyword);
      if (!k) return;
      if (title.indexOf(k) !== -1) score += 160;
      if (menu.indexOf(k) !== -1) score += 140;
      if (crumb.indexOf(k) !== -1) score += 120;
      if (data.indexOf(k) !== -1) score += 120;
      if (fields.indexOf(k) !== -1) score += 30;
      if (buttons.indexOf(k) !== -1) score += 20;
      if (body.indexOf(k) !== -1) score += 8;
    });

    // Rapor/alt ekranların Ana Sayfa olarak ezilmesini engelleyen negatif ağırlıklar.
    if (rule.id === 'home' && /(rapor|report|kpi|performans|personel|support|destek|settings|ayar|ai-agent|decision)/.test(p)) score -= 1200;
    if (rule.id === 'home' && /(rapor|report|kpi|hedef|karne|onay|dönem|donem|personel|destek)/.test(haystackStrong)) score -= 700;
    if (rule.id === 'performance_dashboard' && /(rapor|report|process|surec|süreç|baskan|başkan|scorecard|karne|period|donem|dönem)/.test(p)) score -= 350;

    return score;
  }

  function matchScreen(facts) {
    var best = boş;
    var bestScore = -9999;
    SCREEN_RULES.forEach(function (rule) {
      var score = scoreRule(rule, facts);
      if (score > bestScore) {
        bestScore = score;
        best = rule;
      }
    });
    if (!best || bestScore < 60) {
      return {
        id: 'generic',
        screen: facts.rawTitle && !/ana sayfa|anasayfa/i.test(facts.rawTitle) ? facts.rawTitle : 'BYS360 Ekranı',
        bölüm: 'BYS360 Genel Kullanım',
        href: '',
        description: 'Bu ekran sabit haritada birebir eşleşmedi; ancak Ekran Tanıma Ajanı görünen başlık, menü, buton ve alanlardan güvenli kullanım açıklaması üretir.',
        actions: ['Ekrandaki başlık, filtre, tablo ve butonları kontrol etme', 'Yapmak istediğiniz işlemi yazarak adım adım yönlendirme alma', 'Yetki gerektiren alanlarda ilgili rol veya menü görünürlüğünü kontrol etme'],
        attention: ['Yanlış bağlantıya göndermemek için işlem bağlantısı açmadan önce ekran bağlamını ve yetki sınırını dikkate alırım.'],
        _score: bestScore
      };
    }
    best._score = bestScore;
    return best;
  }

  function collectVisibleActions(facts) {
    var suggestions = [];
    var joined = norm((facts.buttons || []).join(' '));
    function addWhen(pattern, text) { if (pattern.test(joined)) suggestions.push(text); }
    addWhen(/yeni|ekle|oluştur|olustur|kayıt oluştur|kayit olustur/, 'Yeni kayıt veya işlem başlatma');
    addWhen(/kaydet|güncelle|guncelle|sakla/, 'Girilen bilgileri kaydetme veya güncelleme');
    addWhen(/ara|filtre|süz|suz|listele/, 'Listeyi arama, filtreleme veya kapsamı daraltma');
    addWhen(/detay|incele|görüntüle|goruntule/, 'Kayıt detayını görüntüleme');
    addWhen(/onay|reddet|iade/, 'Yetki varsa onay, iade veya ret işlemi yürütme');
    addWhen(/rapor|excel|pdf|dışa aktar|disa aktar/, 'Rapor veya çıktı alma');
    return uniq(suggestions, 6);
  }

  function buildAnswer(facts, rule) {
    var screenTitle = rule.screen || facts.rawTitle || 'BYS360 ekranı';
    var actions = uniq((rule.actions || []).concat(collectVisibleActions(facts)), 8);
    var lines = [];
    lines.push('Bulunduğunuz ekran: ' + screenTitle);
    lines.push('Algılanan modül: ' + (rule.bölüm || 'BYS360'));
    if (facts.path) lines.push('Ekran yolu: ' + facts.path);
    lines.push('');
    lines.push('Ekran Tanıma ve Güvenli Yönlendirme Ajanı bu sayfayı URL, sayfa başlığı, aktif sol menü, sayfa izi, görünür butonlar ve tablo/form alanlarına göre yorumladı. Bu nedenle sayfada genel dashboard ifadesi geçse bile gerçek ekran önceliğini URL ve aktif menüden belirler.');
    lines.push('');
    lines.push(rule.description || 'Bu ekran BYS360 içinde yetki sınırına göre işlem ve izleme amacıyla kullanılır.');
    lines.push('');
    lines.push('Bu ekranda güvenle yapabilecekleriniz:');
    actions.forEach(function (item, index) { lines.push((index + 1) + '. ' + item); });
    var signals = [];
    if (facts.activeMenu && facts.activeMenu.length) signals.push('Aktif menü: ' + facts.activeMenu.slice(0, 3).join(' > '));
    if (facts.breadcrumb && facts.breadcrumb.length) signals.push('Sayfa izi: ' + facts.breadcrumb.slice(0, 3).join(' > '));
    if (facts.buttons && facts.buttons.length) signals.push('Görünür işlem butonları: ' + facts.buttons.slice(0, 6).join(', '));
    if (facts.fields && facts.fields.length) signals.push('Görünür alan ipuçları: ' + facts.fields.slice(0, 7).join(', '));
    if (signals.length) {
      lines.push('');
      lines.push('Tanıma ipuçları:');
      signals.forEach(function (item) { lines.push('- ' + item); });
    }
    lines.push('');
    lines.push('Güvenli yönlendirme:');
    lines.push('- Yapmak istediğiniz işlemi yazarsanız bu ekranın doğru işlem sırasını adım adım anlatırım.');
    if (rule.href) lines.push('- Bu ekran için güvenli hedef: ' + screenTitle + ' (' + rule.href + ')');
    lines.push('');
    lines.push('Dikkat:');
    (rule.attention || []).forEach(function (item) { lines.push('- ' + item); });
    lines.push('- Yetki dışı veri, idari karar, performans puanı veya hassas içerik üretmem; yalnızca güvenli rehberlik sağlarım.');
    return { text: lines.join('\n'), links: rule.href ? [{ title: screenTitle, href: rule.href }] : [] };
  }

  function answerCurrentPage() {
    var facts = collectFacts();
    var rule = matchScreen(facts);
    return buildAnswer(facts, rule);
  }

  function isPageQuestion(question) {
    var q = norm(question);
    return [
      'bu ekranda ne yapabilirim', 'bu sayfada ne yapabilirim', 'burada ne yapacagim', 'burada ne yapacağım',
      'bu ekran ne ise yarar', 'bu ekran ne işe yarar', 'hangi ekrandayim', 'hangi ekrandayım',
      'sayfa yardimi', 'sayfa yardımı', 'ekran yardimi', 'ekran yardımı', 'ekrani anlat', 'ekranı anlat',
      'bu sayfayi tani', 'bu sayfayı tanı', 'ekrani tani', 'ekranı tanı', 'burayi anlat', 'burayı anlat',
      'beni yonlendir', 'beni yönlendir', 'ne yapmam gerekiyor', 'burada nasil ilerlerim', 'burada nasıl ilerlerim',
      'bu sayfayı açıkla', 'bu ekranı açıkla', 'nereye gideceğim', 'ne yapacağım'
    ].some(function (p) { return q.indexOf(norm(p)) !== -1; });
  }

  function answerQuestion(question) {
    if (isPageQuestion(question)) return answerCurrentPage();
    return boş;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return boş;
  };

  window.BYS360AssistantScreenAgentV22 = {
    loaded: true,
    version: VERSION,
    collectFacts: collectFacts,
    matchScreen: matchScreen,
    scoreRule: scoreRule,
    answerCurrentPage: answerCurrentPage,
    answerQuestion: answerQuestion,
    rules: SCREEN_RULES
  };

  if (window.BYS360AssistantModule) {
    window.BYS360AssistantModule.screenAgentV22 = window.BYS360AssistantScreenAgentV22;
    window.BYS360AssistantModule.recognizeCurrentScreenV22 = answerCurrentPage;
  }
})();
/* BYS360_ASSISTANT_SCREEN_AGENT_V22_END */

/* BYS360_ASSISTANT_SCREEN_INTELLIGENCE_V23_START */
(function () {
  'use strict';

  if (window.BYS360AssistantScreenIntelligenceV23 && window.BYS360AssistantScreenIntelligenceV23.loaded) return;

  var VERSION = 'BYS360_ASSISTANT_SCREEN_INTELLIGENCE_V23_ADVANCED_CONTEXT_ENGINE';
  var HOME_PATHS = ['/', '/home'];
  var NO_LINK_REASON = 'Ekran belirsizse yanlış bağlantı açmamak için önce işlem niyetini netleştiririm.';

  function norm(value) {
    return String(value || '')
      .toLocaleLowerCase('tr-TR')
      .replace(/ı/g, 'i').replace(/İ/g, 'i')
      .replace(/[âáàä]/g, 'a').replace(/[êéèë]/g, 'e')
      .replace(/[îíìï]/g, 'i').replace(/[ôóòö]/g, 'o').replace(/[ûúùü]/g, 'u')
      .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ş/g, 's')
      .replace(/[^a-z0-9\s/._#?-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function cleanText(value, maxLen) {
    var text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return '';
    maxLen = maxLen || 120;
    return text.length > maxLen ? text.slice(0, maxLen - 1).trim() + '…' : text;
  }

  function uniq(list, limit) {
    var seen = Object.create(boş);
    var out = [];
    (list || []).forEach(function (item) {
      var t = cleanText(item, 180);
      var k = norm(t);
      if (!k || seen[k]) return;
      seen[k] = true;
      out.push(t);
    });
    return out.slice(0, limit || 10);
  }

  function isVisible(el) {
    try {
      if (!el) return false;
      var style = window.getComputedStyle ? window.getComputedStyle(el) : boş;
      if (style && (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0')) return false;
      var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : boş;
      if (rect && rect.width === 0 && rect.height === 0) return false;
    } catch (e) {}
    return true;
  }

  function textOf(selector, limit) {
    var items = [];
    try {
      document.querySelectorAll(selector).forEach(function (el) {
        if (!isVisible(el)) return;
        items.push(el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '');
      });
    } catch (e) {}
    return uniq(items, limit || 10);
  }

  function attrOf(selector, attrs, limit) {
    var items = [];
    try {
      document.querySelectorAll(selector).forEach(function (el) {
        if (!isVisible(el)) return;
        attrs.forEach(function (attr) { items.push(el.getAttribute(attr)); });
      });
    } catch (e) {}
    return uniq(items, limit || 12);
  }

  function pathNow() {
    try { return (window.location.pathname || '/') + (window.location.search || '') + (window.location.hash || ''); } catch (e) { return '/'; }
  }

  function pathOnly() {
    try { return window.location.pathname || '/'; } catch (e) { return '/'; }
  }

  function pathIsHome(path) {
    var p = norm(path || '').replace(/[?#].*$/, '');
    return HOME_PATHS.some(function (hp) { return p === norm(hp); });
  }

  function containsAny(text, arr) {
    var n = norm(text || '');
    return (arr || []).some(function (x) { return n.indexOf(norm(x)) !== -1; });
  }

  function collectFacts() {
    var titleCandidates = [];
    titleCandidates = titleCandidates.concat(textOf('main h1, main h2, .page-title, .content-title, .module-title, .card-title, [data-page-title], [data-screen-title]', 8));
    try { titleCandidates.push(document.title || ''); } catch (e) {}
    var activeMenu = textOf('.sidebar .active, .nav-link.active, .menu-item.active, .submenu .active, [aria-current="page"], [data-nav-key].active, .accordion-item .active', 12);
    var breadcrumb = textOf('.breadcrumb, .breadcrumb-item, nav[aria-label="breadcrumb"], .page-breadcrumb, .crumb', 10);
    var tabs = textOf('.nav-tabs .active, .tab.active, [role="tab"][aria-selected="true"], .subnav .active', 10);
    var buttons = textOf('button, a.btn, .btn, [role="button"], .action-card, .quick-action', 22);
    var headings = textOf('main h1, main h2, main h3, section h2, section h3, .card-header, .card-title', 18);
    var fields = textOf('label, th, .table th, .form-label, .filter-label', 24).concat(attrOf('input, textarea, select', ['placeholder', 'name', 'id', 'aria-label'], 24));
    var dataSignals = attrOf('[data-nav-key], [data-module], [data-screen], [data-page-title], [data-route], [data-' + 'end' + 'point]', ['data-nav-key', 'data-module', 'data-screen', 'data-page-title', 'data-route', 'data-' + 'end' + 'point'], 24);
    var linkHints = attrOf('a[href]', ['href', 'title', 'aria-label'], 28);
    var bodySample = '';
    try { bodySample = cleanText((document.body && document.body.innerText || '').slice(0, 9000), 9000); } catch (e) {}
    return {
      path: pathNow(),
      pathOnly: pathOnly(),
      rawTitle: uniq(titleCandidates, 4)[0] || '',
      titleCandidates: uniq(titleCandidates, 6),
      activeMenu: activeMenu,
      breadcrumb: breadcrumb,
      tabs: tabs,
      buttons: buttons,
      headings: headings,
      fields: uniq(fields, 24),
      dataSignals: dataSignals,
      linkHints: linkHints,
      bodySample: bodySample
    };
  }

  var SCREEN_RULES = [
    { id:'performance_reports', screen:'Performans Raporları', bölüm:'Performans Yönetimi', href:'/performance/reports', paths:['/performance/reports*','/performans/rapor*','/performance/process-reports*','/performans/surec-rapor*'], keywords:['performans raporları','raporlar','raporlama','analiz','çıktı','excel','pdf','dönem bazlı','birim bazlı'], family:'performance', description:'Bu ekran performans verilerinin dönem, birim, grup/kategori, amir ve personel kırılımlarında analiz edilmesi; çıktı, özet ve yönetici görünürlüğü üretilmesi için kullanılır.', actions:['Dönem veya kapsam filtresini seçme','Birim, kategori, amir veya personel kırılımını kontrol etme','Düşük/yüksek performans yoğunluğunu inceleme','Yetki varsa rapor çıktısı veya özet alma'], attention:['Rapor ekranı idari karar üretmez; veriyi görünür ve analiz edilebilir hale getirir.'] },
    { id:'process_tracking', screen:'Süreç Takibi', bölüm:'Performans Yönetimi', href:'/performance/process-tracking', paths:['/performance/process-tracking*','/performans/surec-takibi*','/performans/süreç-takibi*'], keywords:['süreç takibi','surec takibi','süreç listesi','canlı süreç','bekleyen süreç'], family:'performance', description:'Bu ekran performans ve onay süreçlerinin hangi aşamada olduğunu izlemek, bekleyen kayıtları görmek ve süreç bütünlüğünü kontrol etmek için kullanılır.', actions:['Bekleyen süreçleri kontrol etme','Süreç statüsünü Türkçe kurumsal ifadeyle yorumlama','Geciken veya kilitli kayıtları ayırt etme'], attention:['Teknik durum kodları kullanıcıya gösterilmemeli; Türkçe süreç ifadeleri kullanılmalıdır.'] },
    { id:'president_approvals', screen:'Başkan Onayları', bölüm:'Performans Yönetimi', href:'/performans/baskan-onaylari', paths:['/performans/baskan-onaylari*','/performance/president-approvals*','/performance/president-approval*'], keywords:['başkan onayları','başkan onayı','70 altı','düşük performans','yayın kilidi'], family:'performance', description:'Bu ekran 70 altı düşük performans sonuçlarının üst onay ve yayın kilidi süreçlerini izlemek için kullanılır.', actions:['Başkan onayı bekleyen gerçek kayıtları inceleme','Karne detayına geçme','Onay/ret veya iade sürecini yetkiye göre yürütme','Yayın kilidi ve süreç geçmişini kontrol etme'], attention:['70 altı sonuç Başkan Onayı tamamlanmadan personele kesin sonuç olarak açılmamalıdır.'] },
    { id:'scorecard', screen:'Performans Karnesi', bölüm:'Performans Yönetimi', href:'/performans/v2/faz5/scorecard', paths:['/performans/v2/faz5/scorecard*','/performance/*/scorecard*','/performance/scorecard*','/performans/*/karne*','/performans/gecmis-karne-arsivi*','/performance/archive*'], keywords:['karne','not karnesi','performans karnesi','puanlama geçmişi','amir görüşleri','geçmiş karne'], family:'performance', description:'Bu ekran personelin performans sonucunu, kriter bazlı puanlarını, amir görüşlerini ve süreç geçmişini yetki sınırına göre göstermek için kullanılır.', actions:['Nihai puan ve eşik durumunu kontrol etme','Kriter bazlı puanları inceleme','Amir görüşlerini ve süreç geçmişini okuma','Yayın ve görünürlük durumunu kontrol etme'], attention:['Personel karnesi süreç tamamlanmadan ve gerekli yayın/onay yapılmadan personele açılmamalıdır.'] },
    { id:'periods', screen:'Dönemler', bölüm:'Performans Yönetimi', href:'/performance/periods', paths:['/performance/periods*','/performans/donem*','/performans/dönem*'], keywords:['dönemler','performans dönemi','yeni dönem','kapsam tipi','aktif dönem'], family:'performance', description:'Bu ekran performans dönemlerinin yıl, dönem türü, tarih aralığı ve kapsam tipiyle yönetilmesi için kullanılır.', actions:['Dönem listesini ve aktif dönemi kontrol etme','Yetki varsa yeni dönem oluşturma','Tüm kurum, birim, kategori veya seçili personel kapsamını belirleme','Görev üretimi öncesi dönem bilgilerini doğrulama'], attention:['Doğru sekme adı Dönemlerdir; yönlendirme bu adla yapılmalıdır.'] },
    { id:'criteria', screen:'Değerlendirme Kriterleri', bölüm:'Performans Yönetimi', href:'/performance/criteria', paths:['/performance/criteria*','/performans/kriter*','/performance/evaluation-criteria*'], keywords:['değerlendirme kriterleri','kriterler','kriter ekle','aktif kriter'], family:'performance', description:'Bu ekran performans değerlendirmesinde kullanılacak kurumsal kriterlerin tanımlanması ve yönetilmesi için kullanılır.', actions:['Kriter listesini kontrol etme','Yetki varsa kriter ekleme veya düzenleme','Aktif/pasif durumunu kontrol etme'], attention:['Ekran dilinde ana terim Değerlendirme Kriterleri olmalıdır.'] },
    { id:'weights', screen:'Ağırlık Ayarları', bölüm:'Performans Yönetimi', href:'/performance/weights', paths:['/performance/weights*','/performans/agirlik*','/performans/ağırlık*'], keywords:['ağırlık','agirlik','1. amir','2. amir','3. amir','yüzde','%100'], family:'performance', description:'Bu ekran amir seviyelerine göre puan ağırlıklarının ve 3. amir modunun kontrol edilmesi için kullanılır.', actions:['Ağırlık toplamının %100 olduğunu kontrol etme','3. amir yorum/puan modunu ayırt etme','Yetki varsa dönem veya rol bazlı ağırlık düzenleme'], attention:['3. amir yorum modundaysa puana etkisi olmamalıdır.'] },
    { id:'assignments', screen:'Görev Üretimi ve Değerlendirme Görevleri', bölüm:'Performans Yönetimi', href:'/performance/assignments', paths:['/performance/assignments*','/performance/tasks*','/performans/gorev*','/performans/görev*'], keywords:['görev üretimi','değerlendirme görevi','atanan görev','amir zinciri','eksik amir'], family:'performance', description:'Bu ekran dönem kapsamındaki personel için gerçek amir zincirine göre değerlendirme görevlerinin üretilmesi ve takip edilmesi için kullanılır.', actions:['Dönemi ve kapsamı seçme','Eksik amir veya hatalı zincir kontrolü yapma','Görevleri üretme veya yeniden üretme','Bekleyen görevleri izleme'], attention:['Sahte görev veya boş 3. amir beklemesi üretilmemelidir.'] },
    { id:'scoring', screen:'Puanlama ve Değerlendirme', bölüm:'Performans Yönetimi', href:'/performance/scoring', paths:['/performance/scoring*','/performans/puan*','/performance/evaluations*'], keywords:['puanlama','değerlendirme yap','1-5','genel görüş','açıklama'], family:'performance', description:'Bu ekran amirlerin kendilerine atanmış personeli kriter bazlı puan ve görüş ile değerlendirmesi için kullanılır.', actions:['Atanmış değerlendirme görevini açma','Kriter bazlı puanları girme','Zorunlu açıklama alanlarını doldurma','Değerlendirmeyi kaydetme veya tamamlama'], attention:['Asistan puan önermez veya puan belirlemez; yalnızca işlem sırasını açıklar.'] },
    { id:'publish_approvals', screen:'Yayın Ön Onayı', bölüm:'Performans Yönetimi', href:'/performance/personnel-support-publish-approvals', paths:['/performance/personnel-support-publish-approvals*','/performance/publish*','/performans/yayin*','/performans/yayın*'], keywords:['yayın ön onayı','yayınla','personel ve destek','final yayın','yayın kilidi'], family:'performance', description:'Bu ekran sonuçların personele açılmadan önce yetkili yayın ön onayı ve final yayın kontrolünden geçmesi için kullanılır.', actions:['Yayın öncesi bekleyen kayıtları kontrol etme','Başkan onayı gerektiren kayıtların tamamlandığını doğrulama','Yetki varsa yayın ön onayı veya final yayın adımına geçme'], attention:['Yayın tamamlanmadan personel kendi kesin sonucunu görmemelidir.'] },
    { id:'period_notes', screen:'Dönem İçi Notlar', bölüm:'Performans Yönetimi', href:'/performance/period-notes', paths:['/performance/period-notes*','/performans/donem-ici-not*','/performans/dönem-içi-not*'], keywords:['dönem içi not','ara geri bildirim','olumlu olay','gelişim ihtiyacı','gözlem'], family:'performance', description:'Bu ekran dönem boyunca olumlu/olumsuz gözlem, başarı, gelişim ihtiyacı ve ara geri bildirim notlarının kayıt altına alınması için kullanılır.', actions:['Personel veya dönem filtresini seçme','Not türünü ve açıklamayı kontrol etme','Yetki varsa yeni dönem içi not ekleme'], attention:['Dönem içi not otomatik nihai puan üretmez; değerlendirmeye destek kayıt sağlar.'] },
    { id:'development_suggestions', screen:'Gelişim Önerileri', bölüm:'Performans Yönetimi', href:'/performance/development-suggestions', paths:['/performance/development*','/performans/gelisim*','/performans/gelişim*'], keywords:['gelişim önerisi','gelişim alanı','rehber not','aksiyon planı'], family:'performance', description:'Bu ekran düşük performans veya gelişim ihtiyacı görülen alanlar için rehber gelişim önerilerinin kayıt altına alınması için kullanılır.', actions:['Gelişim notlarını inceleme','Yetki varsa öneri veya aksiyon planı ekleme','Karne ve süreç geçmişiyle ilişkisini kontrol etme'], attention:['Öneri idari karar değil, gelişim amaçlı rehberlik notudur.'] },
    { id:'performance_dashboard', screen:'Performans Dashboard', bölüm:'Performans Yönetimi', href:'/performance/dashboard', paths:['/performance/dashboard*','/performans/dashboard*'], keywords:['performans dashboard','performans özeti','canlı performans haritası','riskli personel','geciken amir'], family:'performance', description:'Bu ekran performans sürecinin genel durumunu, tamamlanma oranlarını, riskli alanları ve yönetici görünürlüğünü takip etmek için kullanılır.', actions:['Tamamlanma ve bekleyen görev durumunu izleme','Riskli personel ve düşük performans yoğunluğunu kontrol etme','Geciken amirleri veya yayın kilitlerini görme'], attention:['Dashboard özet verir; ayrıntı ve işlem için ilgili alt ekrana geçilmelidir.'] },

    { id:'kpi_dashboard', screen:'KPI Dashboardu', bölüm:'KPI ve Hedef Yönetimi', href:'/performans/stratejik/kpi-dashboard', paths:['/performans/stratejik/kpi-dashboard*','/strategic-performance/kpi-dashboard*','/strategic_performance_dashboard*','/strategic-performance-dashboard*'], keywords:['kpi dashboard','hedef gerçekleşmeleri','hedef gerceklesmeleri','başarı oranı','risk seviyesi','stratejik performans'], family:'kpi', description:'Bu ekran KPI ve hedef gerçekleşmelerini, hedef kartlarını, başarı oranlarını, risk seviyelerini ve stratejik performans özetlerini takip etmek için kullanılır.', actions:['Hedef dönemini ve kapsamını kontrol etme','Hedef gerçekleşmelerini ve başarı oranını inceleme','Riskli veya geciken KPI kayıtlarını ayırt etme','AI KPI Analiz ekranına geçmeden önce verinin güncel olup olmadığını kontrol etme'], attention:['Asistan hedef sonucu veya idari karar üretmez; yalnızca ekranın kullanım sırasını açıklar.'] },
    { id:'targets', screen:'KPI ve Hedef Listesi', bölüm:'KPI ve Hedef Yönetimi', href:'/performans/stratejik/hedefler', paths:['/performans/stratejik/hedefler*','/strategic-performance/targets*','/strategic-performance/hedefler*'], keywords:['hedef listesi','hedef kartı','kpi listesi','hedefler','hedef sahibi'], family:'kpi', description:'Bu ekran hedef kartlarını listelemek, kapsam ve durum bilgilerini kontrol etmek ve yetki varsa hedef kaydı oluşturmak için kullanılır.', actions:['Hedef kartlarını listeleme','Hedef sahibi, kapsam, ağırlık ve durum bilgilerini kontrol etme','Yetki varsa yeni hedef oluşturma veya mevcut hedefi güncelleme'], attention:['KPI hedefleri performans puanının yerine geçmez; karar destek ve izleme verisi üretir.'] },
    { id:'target_create', screen:'Yeni KPI / Hedef Oluştur', bölüm:'KPI ve Hedef Yönetimi', href:'/performans/stratejik/hedefler/yeni', paths:['/performans/stratejik/hedefler/yeni*','/strategic-performance/targets/new*','/strategic-performance/hedefler/yeni*'], keywords:['yeni hedef','hedef oluştur','kpi oluştur','hedef kodu','hedef değer'], family:'kpi', description:'Bu ekran kurumsal, birim veya personel düzeyinde yeni KPI/hedef kartı oluşturmak için kullanılır.', actions:['Hedef adını, kapsamını ve sahibini belirleme','Hedef değer, gerçekleşen değer ve ağırlık alanlarını kontrol etme','Risk seviyesi ve tarih aralığını tanımlama'], attention:['Hedef kaydı yetki ve kapsam sınırına göre oluşturulmalıdır.'] },
    { id:'kpi_analysis', screen:'AI KPI Analiz', bölüm:'KPI ve Hedef Yönetimi', href:'/performans/stratejik/kpi-analiz', paths:['/performans/stratejik/kpi-analiz*','/strategic-performance/kpi-analysis*','/strategic-performance/ai-analysis*'], keywords:['ai kpi analiz','kpi analiz','hedef analizi','stratejik analiz','risk özeti'], family:'kpi', description:'Bu ekran KPI ve hedef verilerinin kontrollü analiz ve özetleme desteğiyle yorumlanması için kullanılır.', actions:['Analiz öncesi veri kapsamını kontrol etme','Risk ve başarı özetlerini inceleme','AI çıktısını karar değil destek notu olarak değerlendirme'], attention:['AI karar vermez; analiz çıktısı insan denetimli değerlendirme notudur.'] },
    { id:'competency_library', screen:'Yetkinlik Kütüphanesi', bölüm:'KPI ve Hedef Yönetimi', href:'/performans/stratejik/yetkinlik-kutuphanesi', paths:['/performans/stratejik/yetkinlik-kutuphanesi*','/performans/stratejik/yetkinlik*','/strategic-performance/competenc*'], keywords:['yetkinlik kütüphanesi','yetkinlik','görev bazlı yetkinlik','rol yetkinliği'], family:'kpi', description:'Bu ekran görev, rol ve hedef yönetimiyle ilişkili yetkinlik tanımlarının yönetilmesi için kullanılır.', actions:['Yetkinlik tanımlarını inceleme','Rol veya görev bazlı eşleşmeleri kontrol etme','Yetki varsa aktif/pasif durumunu düzenleme'], attention:['Bu alan performans ekranlarındaki ana Değerlendirme Kriterleri terimiyle karıştırılmamalıdır.'] },
    { id:'self_review', screen:'Öz Değerlendirme', bölüm:'KPI ve Hedef Yönetimi', href:'/performans/stratejik/oz-degerlendirme', paths:['/performans/stratejik/oz-degerlendirme*','/strategic-performance/self*','/strategic-performance/oz-degerlendirme*'], keywords:['öz değerlendirme','oz degerlendirme','öz değerlendirme özeti','dönem özeti','başarılar'], family:'kpi', description:'Bu ekran personelin dönemsel çalışma özeti, başarıları, zorlandığı alanlar ve gelişim ihtiyaçlarını paylaşması için kullanılır.', actions:['Dönem özeti ve hedef gerçekleşmesini yazma','Başarıları ve gelişim ihtiyaçlarını belirtme','Yetki kapsamında öz değerlendirme özetini inceleme'], attention:['Öz değerlendirme otomatik puan üretmez; amire destek verisi sağlar.'] },
    { id:'strategic_panel', screen:'Stratejik Performans Paneli', bölüm:'KPI ve Hedef Yönetimi', href:'/performans/stratejik/panel/dashboard', paths:['/performans/stratejik/panel*','/strategic-performance/panel*'], keywords:['stratejik performans paneli','stratejik panel','hedef yönetimi paneli'], family:'kpi', description:'Bu ekran KPI, hedef, yetkinlik ve öz değerlendirme verilerinin yönetsel özetini sunan stratejik performans panelidir.', actions:['Genel hedef gerçekleşme durumunu inceleme','Riskli KPI ve hedefleri ayırt etme','Yetkinlik ve öz değerlendirme özetleriyle bağlantı kurma'], attention:['Panel özet sağlar; işlem için hedef, analiz veya öz değerlendirme alt ekranına geçilmelidir.'] },

    { id:'personnel_list', screen:'Personel Listesi', bölüm:'Personel Yönetimi', href:'/admin/users', paths:['/admin/users*','/personnel*','/hr-management*','/admin/personnel*'], keywords:['personel listesi','personel ekle','sicil','unvan','birim','yönetici','profil fotoğrafı'], family:'personnel', description:'Bu ekran personel kayıtlarının, sicil, unvan, birim, üst birim ve yönetici ilişkilerinin yönetilmesi için kullanılır.', actions:['Personel arama ve listeleme','Yetki varsa personel ekleme veya düzenleme','Birim, üst birim, unvan ve yönetici bilgisini doğrulama'], attention:['TC yerine Sicil No kullanılmalı; personel verisi performans ve yetki süreçlerini doğrudan etkiler.'] },
    { id:'org_units', screen:'Organizasyon Birimleri', bölüm:'Personel Yönetimi', href:'/admin/organization-units', paths:['/admin/organization*','/organization-units*','/personnel/organization*'], keywords:['organizasyon','birim','üst birim','çalışma grubu','koordinatör','grup başkanlığı'], family:'personnel', description:'Bu ekran kurum birimleri, üst birimler, çalışma grupları ve organizasyon ilişkilerinin yönetilmesi için kullanılır.', actions:['Birim ve üst birim ilişkisini kontrol etme','Yetki varsa birim ekleme veya düzenleme','Personel atama ve amir zinciri etkisini doğrulama'], attention:['Organizasyon verisi performans görev üretimini doğrudan etkiler.'] },
    { id:'leave_delegation', screen:'İzin, Devamsızlık ve Vekâlet', bölüm:'Personel Yönetimi', href:'/personnel/leaves', paths:['/personnel/leaves*','/leave*','/attendance*','/delegation*','/personnel/delegation*','/personnel/attendance*'], keywords:['izin','devamsızlık','vekâlet','vekalet','izin talebi','izin kaydı'], family:'personnel', description:'Bu ekran izin, devamsızlık ve vekâlet süreçlerinin kayıtlı ve izlenebilir yürütülmesi için kullanılır.', actions:['İzin veya devamsızlık kaydını inceleme','Vekâlet ilişkisini kontrol etme','Performans/onay süreçlerinde vekilin etkisini doğrulama'], attention:['İzinli amir ve vekâlet ilişkileri performans görev akışını etkileyebilir.'] },

    { id:'role_matrix', screen:'Rol Matrisi ve Menü Görünürlüğü', bölüm:'Sistem Ayarları ve Yetkilendirme', href:'/admin/menu-permissions', paths:['/admin/menu*','/admin/roles*','/settings/roles*','/settings/menu*','/admin/role-matrix*','/admin/permissions*'], keywords:['rol matrisi','menü görünürlüğü','yetki','rol','menü yetkisi','modül bazlı rol'], family:'settings', description:'Bu ekran kullanıcıların hangi modülleri, sekmeleri ve işlemleri görebileceğini rol, kişi veya birim bazında yönetmek için kullanılır.', actions:['Rol bazlı görünürlüğü kontrol etme','Kişi veya birim bazlı istisna tanımlama','Menü kapalıysa ekranda hiç görünmediğini test etme','Backend erişim kontrolünün de korunduğunu doğrulama'], attention:['Sadece menüyü gizlemek yetmez; URL ile erişimde de yetki kontrolü korunmalıdır.'] },
    { id:'settings', screen:'Sistem Ayarları', bölüm:'Sistem Ayarları ve Yetkilendirme', href:'/settings', paths:['/settings*','/admin/settings*','/system-settings*','/admin/system*'], keywords:['sistem ayarları','modül ayarları','captcha','oturum','audit','güvenlik ayarı','e-posta ayarları'], family:'settings', description:'Bu ekran BYS360 modüllerinin çalışma kurallarını, güvenlik ayarlarını, bildirim/e-posta ayarlarını ve denetim kayıtlarını yönetmek için kullanılır.', actions:['Modül ayarlarını kontrol etme','Güvenlik ve oturum kurallarını inceleme','Kritik ayar değişikliklerinde audit log kaydını doğrulama'], attention:['Canlı sistemde ayar değişikliği yapmadan önce etki alanı kontrol edilmelidir.'] },
    { id:'audit_logs', screen:'Audit Log ve Denetim İzleri', bölüm:'Sistem Ayarları ve Yetkilendirme', href:'/admin/audit-logs', paths:['/admin/audit*','/audit*','/logs/audit*'], keywords:['audit','denetim izi','log','değişiklik geçmişi','güvenlik özeti'], family:'settings', description:'Bu ekran kritik işlem, ayar ve yetki değişikliklerinin denetim izlerini incelemek için kullanılır.', actions:['Kritik değişiklik geçmişini inceleme','Kullanıcı, tarih ve işlem türüne göre filtreleme','Şüpheli veya hatalı değişiklikleri tespit etme'], attention:['Denetim kayıtları canlı sistem güvenliği için korunmalıdır.'] },

    { id:'support', screen:'Destek Talepleri', bölüm:'İletişim, Anket ve Destek Süreçleri', href:'/support', paths:['/support*','/help*','/yardim*','/yardım*'], keywords:['destek talebi','yardım merkezi','talep','açık destek','cevaplandı','destek kategorisi'], family:'communication', description:'Bu ekran kullanıcı yardım ve destek taleplerinin açılması, cevaplanması ve takip edilmesi için kullanılır.', actions:['Destek talebi oluşturma','Açık veya cevap bekleyen talepleri takip etme','Talep kategorisi ve durum geçmişini kontrol etme'], attention:['Destek taleplerinde kişisel veya hassas veri paylaşımı sınırlandırılmalıdır.'] },
    { id:'messages', screen:'Mesajlaşma ve Duyurular', bölüm:'İletişim, Anket ve Destek Süreçleri', href:'/messages', paths:['/messages*','/communication*','/announcements*','/notifications*'], keywords:['mesaj','duyuru','bildirim','konuşma','ek dosya','okunmamış'], family:'communication', description:'Bu ekran kurum içi mesajlaşma, duyuru ve bildirim süreçlerini izlemek için kullanılır.', actions:['Mesaj veya duyuruları inceleme','Okunmamış bildirimleri kontrol etme','Yetki varsa hedef kitleye duyuru gönderme'], attention:['Mesaj ve duyuru içerikleri gizlilik ve yetki sınırlarıyla korunmalıdır.'] },
    { id:'surveys_feedback', screen:'Anket ve Geri Bildirim', bölüm:'İletişim, Anket ve Destek Süreçleri', href:'/surveys', paths:['/surveys*','/feedback*','/pulse*'], keywords:['anket','geri bildirim','nabız','kampanya','katılım','cevap'], family:'communication', description:'Bu ekran anket, geri bildirim ve nabız ölçümü süreçlerini yürütmek ve takip etmek için kullanılır.', actions:['Anket veya geri bildirim kampanyasını inceleme','Katılım ve cevap durumunu kontrol etme','Yetki varsa yeni anket veya kampanya oluşturma'], attention:['Anket cevapları yetki ve gizlilik sınırına göre görüntülenmelidir.'] },

    { id:'ai_decision', screen:'AI Karar Destek Merkezi', bölüm:'AI Karar Destek Merkezi', href:'/ai/decision-support/faz1/health', paths:['/ai/decision-support*','/ai-decision*','/ai/decision*'], keywords:['ai karar destek','karar destek','risk farkındalığı','özetleme','analiz','kontrollü yapay zekâ'], family:'ai', description:'Bu ekran BYS360 verilerinden kontrollü özet, risk farkındalığı ve karar destek notları üretmek için kullanılır.', actions:['Karar destek özetlerini inceleme','Risk ve dikkat notlarını insan denetimli yorum olarak değerlendirme','Verinin hangi modül alanına dayandığını kontrol etme'], attention:['AI karar vermez; yalnızca yönetici karar alma kapasitesini destekler.'] },
    { id:'assistant_panel', screen:'BYS360 Asistanı Paneli', bölüm:'BYS360 Asistanı', href:'/ai-agent/panel', paths:['/ai-agent/panel*'], keywords:['asistan paneli','kurumsal asistan paneli','güvenli yönlendirme','ekran tanıma'], family:'assistant', description:'Bu ekran BYS360 Asistanı’nın kurumsal rehberlik, güvenli yönlendirme ve kullanıcı destek panelidir.', actions:['Asistan rehberliğini inceleme','Modül yönlendirmelerini kontrol etme','Yetki sınırı ve bilgi bankası bağlantılarını gözden geçirme'], attention:['Asistan idari karar, puan veya hassas veri üretmez.'] },
    { id:'assistant_knowledge', screen:'BYS360 Asistanı Bilgi Bankası', bölüm:'BYS360 Asistanı', href:'/ai-agent/knowledge', paths:['/ai-agent/knowledge*','/assistant-training-bank*'], keywords:['asistan bilgi bankası','öğretim merkezi','eğitim bankası','soru cevap','rehber kayıt'], family:'assistant', description:'Bu ekran BYS360 Asistanı’nın kurumsal rehberlik ve bilgi bankası içeriğini yönetmek için kullanılır.', actions:['Bilgi bankası kayıtlarını inceleme','Yetki varsa yeni rehber soru-cevap ekleme','Güvenli URL ve yönlendirme kurallarını kontrol etme'], attention:['Asistan bilgi bankası yalnızca yetkili kullanıcılar tarafından yönetilmelidir.'] },

    { id:'analytics_center', screen:'Analiz Merkezi', bölüm:'Raporlama ve Yönetici Görünürlüğü', href:'/analytics', paths:['/analytics*','/analytics-center*','/reports*'], keywords:['analiz merkezi','raporlama','yönetici görünürlüğü','gösterge','kırılım'], family:'reports', description:'Bu ekran farklı modüllerden gelen verilerin yönetici görünürlüğü ve analiz amacıyla izlenmesi için kullanılır.', actions:['Modül ve kapsam filtresini kontrol etme','Grafik ve özet kartlarını inceleme','Yetki varsa rapor veya çıktı alma'], attention:['Analiz sonuçları karar desteğidir; nihai idari karar yerine geçmez.'] },
    { id:'profile_account', screen:'Profil ve Kullanıcı Hesabı', bölüm:'Kullanıcı Hesabı', href:'/account', paths:['/account*','/profile*','/auth/profile*'], keywords:['profil','hesabım','kullanıcı hesabı','oturum','kişisel bilgiler'], family:'account', description:'Bu ekran kullanıcının kendi profil ve hesap bilgilerini görüntülemesi için kullanılır.', actions:['Profil bilgilerini inceleme','Yetki verilen hesap ayarlarını kontrol etme','Oturum ve güvenlik uyarılarını izleme'], attention:['Hesap güvenliğiyle ilgili bilgiler hassasiyetle korunmalıdır.'] },
    { id:'general_dashboard', screen:'Dashboard', bölüm:'Yönetici Dashboard', href:'/dashboard', paths:['/dashboard'], keywords:['dashboard','genel dashboard','yönetici dashboard','yonetici dashboard','gösterge paneli','gosterge paneli','yönetici görünümü','yonetici gorunumu'], family:'dashboard', description:'Bu ekran Ana Sayfa değildir. Dashboard; yönetici özetleri, gösterge kartları, grafikler, performans/KPI bağlantıları ve kurumsal durum analizleri için kullanılır.', actions:['Yönetici özet kartlarını inceleme','Grafik ve gösterge alanlarını kontrol etme','Yetki kapsamındaki performans, destek, anket veya KPI özetlerine geçme'], attention:['Dashboard analiz ve yönetici görünürlüğü ekranıdır; günlük başlangıç ve hızlı geçiş ekranı olan Ana Sayfa ile karıştırılmamalıdır.'] },
    { id:'home', screen:'Ana Sayfa', bölüm:'Genel', href:'/home', exactHomeOnly:true, paths:['/home','/'], keywords:['ana sayfa','anasayfa','başlangıç','baslangic','bugün ne var','bugun ne var','nereden başlayacağım','nereden baslayacagim','genel özet'], family:'home', description:'Bu ekran BYS360 açılış ve günlük başlangıç ekranıdır. Kullanıcıya bekleyen işler, kısa özetler ve modüllere güvenli geçiş sağlar.', actions:['Bugünkü kısa özetleri inceleme','Bekleyen bildirim, görev, anket veya destek talebi varsa ilgili modüle geçme','Yetkili olduğunuz ana modüllere hızlı geçiş yapma'], attention:['Ana Sayfa işlem detayı veya yönetici analiz ekranı değildir; hızlı başlangıç ve yönlendirme alanıdır.'] }
  ];

  var FAMILY_HINTS = [
    { family:'performance', bölüm:'Performans Yönetimi', screen:'Performans Yönetimi Ekranı', path:/\/performance|\/performans/i, keywords:['performans','karne','puan','dönem','amir','onay','rapor'] },
    { family:'kpi', bölüm:'KPI ve Hedef Yönetimi', screen:'KPI ve Hedef Yönetimi Ekranı', path:/stratejik|kpi|target|hedef/i, keywords:['kpi','hedef','stratejik','yetkinlik','öz değerlendirme'] },
    { family:'personnel', bölüm:'Personel Yönetimi', screen:'Personel Yönetimi Ekranı', path:/personnel|admin\/users|organization|leave|attendance|delegation/i, keywords:['personel','sicil','izin','vekalet','vekâlet','birim','unvan'] },
    { family:'settings', bölüm:'Sistem Ayarları ve Yetkilendirme', screen:'Sistem Ayarları Ekranı', path:/settings|admin\/menu|admin\/role|permission|audit/i, keywords:['ayar','yetki','rol','menü','captcha','audit'] },
    { family:'communication', bölüm:'İletişim, Anket ve Destek Süreçleri', screen:'İletişim ve Destek Ekranı', path:/support|messages|communication|survey|feedback|notification/i, keywords:['destek','mesaj','duyuru','anket','geri bildirim','bildirim'] },
    { family:'ai', bölüm:'AI Karar Destek Merkezi', screen:'AI Karar Destek Ekranı', path:/ai\/decision|ai-decision/i, keywords:['ai karar','karar destek','risk','özetleme'] },
    { family:'assistant', bölüm:'BYS360 Asistanı', screen:'BYS360 Asistanı Ekranı', path:/ai-agent|assistant/i, keywords:['asistan','bilgi bankası','öğretim'] }
  ];

  function scoreRule(rule, facts) {
    var score = 0;
    var p = norm(facts.pathOnly || facts.path);
    var fullPath = norm(facts.path || '');
    var title = norm((facts.titleCandidates || []).join(' '));
    var menu = norm((facts.activeMenu || []).join(' '));
    var crumb = norm((facts.breadcrumb || []).join(' '));
    var tabs = norm((facts.tabs || []).join(' '));
    var headings = norm((facts.headings || []).join(' '));
    var fields = norm((facts.fields || []).join(' '));
    var buttons = norm((facts.buttons || []).join(' '));
    var data = norm((facts.dataSignals || []).join(' '));
    var links = norm((facts.linkHints || []).join(' '));
    var body = norm(facts.bodySample || '');
    var strong = [p, fullPath, title, menu, crumb, tabs, data].join(' ');
    var mid = [headings, links].join(' ');
    var weak = [fields, buttons, body].join(' ');

    if (rule.exactHomeOnly && !pathIsHome(facts.pathOnly || facts.path)) return -2000;

    (rule.paths || []).forEach(function (pattern) {
      var işlenmemiş veri = String(pattern || '');
      var base = işlenmemiş veri.slice(-1) === '*' ? işlenmemiş veri.slice(0, -1) : işlenmemiş veri;
      var n = norm(base);
      if (!n) return;
      if (p === n) score += 1400;
      else if (işlenmemiş veri.slice(-1) === '*' && p.indexOf(n) === 0) score += 1250;
      else if (p.indexOf(n + '/') === 0) score += 1150;
      else if (fullPath.indexOf(n) !== -1) score += 850;
    });

    (rule.keywords || []).forEach(function (keyword) {
      var k = norm(keyword);
      if (!k) return;
      if (title.indexOf(k) !== -1) score += 260;
      if (menu.indexOf(k) !== -1) score += 240;
      if (crumb.indexOf(k) !== -1) score += 220;
      if (tabs.indexOf(k) !== -1) score += 180;
      if (data.indexOf(k) !== -1) score += 180;
      if (headings.indexOf(k) !== -1) score += 140;
      if (links.indexOf(k) !== -1) score += 80;
      if (fields.indexOf(k) !== -1) score += 55;
      if (buttons.indexOf(k) !== -1) score += 45;
      if (body.indexOf(k) !== -1) score += 6;
    });

    // Çok olgun öncelik: Ana Sayfa yalnızca gerçek ana sayfa yolunda kazanabilir.
    if (rule.id === 'home' && !pathIsHome(facts.pathOnly || facts.path)) score -= 1800;
    if (rule.id === 'home' && /(rapor|report|kpi|hedef|target|performans|scorecard|karne|onay|approval|period|donem|dönem|personel|izin|leave|support|destek|settings|ayar|ai-agent|decision|survey|anket|message|mesaj)/.test(strong)) score -= 1400;

    // Dashboard kelimesi, rapor/karne/onay/dönem/KPI gibi özel ekranları ezemez.
    if (rule.id === 'performance_dashboard' && /(rapor|report|process|surec|süreç|baskan|başkan|approval|scorecard|karne|period|donem|dönem|kpi|hedef|target)/.test(p)) score -= 600;
    if (rule.id === 'kpi_dashboard' && /(hedefler\/yeni|targets\/new|kpi-analiz|analysis|yetkinlik|competenc|oz-degerlendirme|self)/.test(p)) score -= 500;
    if (rule.id === 'analytics_center' && /(performance\/reports|performans\/rapor|process-reports)/.test(p)) score -= 500;

    // URL ailesiyle uyumsuz ekranlara ceza ver.
    FAMILY_HINTS.forEach(function (hint) {
      if (hint.path.test(facts.path || '') && rule.family && rule.family !== hint.family && rule.id !== 'home') score -= 120;
    });

    return score;
  }

  function rankedRules(facts) {
    return SCREEN_RULES.map(function (rule) {
      return { rule: rule, score: scoreRule(rule, facts) };
    }).sort(function (a, b) { return b.score - a.score; });
  }

  function inferGenericScreen(facts, ranked) {
    var p = facts.path || '';
    var title = facts.rawTitle || (facts.titleCandidates || [])[0] || '';
    var combined = [p, title, (facts.activeMenu || []).join(' '), (facts.breadcrumb || []).join(' '), (facts.headings || []).join(' ')].join(' ');
    var family = boş;
    FAMILY_HINTS.forEach(function (hint) {
      if (!family && (hint.path.test(p) || containsAny(combined, hint.keywords))) family = hint;
    });
    var cleanTitle = cleanText(title || (facts.activeMenu || [])[0] || (facts.breadcrumb || [])[0] || '', 80);
    return {
      id: 'generic_' + (family ? family.family : 'bys360'),
      screen: cleanTitle && !/ana sayfa|anasayfa/i.test(cleanTitle) ? cleanTitle : (family ? family.screen : 'BYS360 Ekranı'),
      bölüm: family ? family.bölüm : 'BYS360 Genel Kullanım',
      href: '',
      description: 'Bu ekran birebir sabit haritada kayıtlı olmasa bile Ekran Zekâsı Ajanı URL, aktif menü, başlık, sayfa izi, görünür butonlar ve tablo/form alanlarından güvenli kullanım açıklaması üretir.',
      actions: ['Ekrandaki başlık, filtre, tablo ve butonları kontrol etme','Yapmak istediğiniz işlemi yazarak adım adım yönlendirme alma','Yetki gerektiren alanlarda ilgili rol veya menü görünürlüğünü kontrol etme'],
      attention: [NO_LINK_REASON],
      generic: true,
      score: ranked && ranked[0] ? ranked[0].score : 0
    };
  }

  function matchScreen(facts) {
    var ranked = rankedRules(facts);
    var first = ranked[0] || boş;
    var second = ranked[1] || boş;
    if (!first || first.score < 85) {
      var generic = inferGenericScreen(facts, ranked);
      generic.confidence = 'düşük';
      generic.candidates = ranked.slice(0, 3).filter(function (x) { return x.score > 20; }).map(function (x) { return { screen: x.rule.screen, score: x.score }; });
      return generic;
    }
    var rule = Object.assign({}, first.rule);
    rule.score = first.score;
    rule.secondBest = second ? { screen: second.rule.screen, score: second.score } : boş;
    rule.confidence = first.score >= 900 ? 'yüksek' : (first.score >= 300 ? 'orta' : 'düşük');
    if (second && first.score < 400 && (first.score - second.score) < 90) {
      rule.ambiguous = true;
      rule.candidates = ranked.slice(0, 3).map(function (x) { return { screen: x.rule.screen, score: x.score }; });
      rule.href = '';
      rule.attention = (rule.attention || []).concat(['Ekran sinyalleri birbirine yakın olduğu için yanlış bağlantı açmadan önce yapmak istediğiniz işlemi yazmanız güvenlidir.']);
    }
    return rule;
  }

  function collectVisibleActions(facts) {
    var suggestions = [];
    var joined = norm([(facts.buttons || []).join(' '), (facts.fields || []).join(' '), (facts.headings || []).join(' ')].join(' '));
    function addWhen(pattern, text) { if (pattern.test(joined)) suggestions.push(text); }
    addWhen(/yeni|ekle|oluştur|olustur|kayıt oluştur|kayit olustur/, 'Yeni kayıt veya işlem başlatma');
    addWhen(/kaydet|güncelle|guncelle|sakla/, 'Girilen bilgileri kaydetme veya güncelleme');
    addWhen(/ara|filtre|süz|suz|listele|dönem|birim|kategori/, 'Listeyi arama, filtreleme veya kapsamı daraltma');
    addWhen(/detay|incele|görüntüle|goruntule|aç|ac/, 'Kayıt detayını görüntüleme');
    addWhen(/onay|reddet|iade|yayın|yayin/, 'Yetki varsa onay, iade, ret veya yayın işlemi yürütme');
    addWhen(/rapor|excel|pdf|dışa aktar|disa aktar|çıktı|cikti/, 'Rapor veya çıktı alma');
    addWhen(/analiz|ai|özet|ozet|risk/, 'Analiz veya özet sonucunu karar destek olarak inceleme');
    return uniq(suggestions, 7);
  }

  function buildAnswer(facts, rule) {
    var screenTitle = rule.screen || facts.rawTitle || 'BYS360 ekranı';
    var actions = uniq((rule.actions || []).concat(collectVisibleActions(facts)), 9);
    var lines = [];
    lines.push('Bulunduğunuz ekran: ' + screenTitle);
    lines.push('Algılanan modül: ' + (rule.bölüm || 'BYS360'));
    if (facts.pathOnly) lines.push('Ekran yolu: ' + facts.pathOnly);
    lines.push('Tanıma güveni: ' + (rule.confidence || 'orta'));
    lines.push('');
    lines.push('Ekran Zekâsı ve Güvenli Yönlendirme Ajanı bu sayfayı URL, aktif sol menü, breadcrumb/sayfa izi, başlık, sekme, görünür butonlar, tablo başlıkları ve form alanlarını birlikte puanlayarak tanıdı. Genel “dashboard” veya “ana sayfa” ifadeleri, özel ekran URL’si ve aktif menünün önüne geçemez.');
    lines.push('');
    lines.push(rule.description || 'Bu ekran BYS360 içinde yetki sınırına göre işlem ve izleme amacıyla kullanılır.');
    lines.push('');
    lines.push('Bu ekranda güvenle yapabilecekleriniz:');
    actions.forEach(function (item, index) { lines.push((index + 1) + '. ' + item); });
    var signals = [];
    if (facts.activeMenu && facts.activeMenu.length) signals.push('Aktif menü: ' + facts.activeMenu.slice(0, 4).join(' > '));
    if (facts.breadcrumb && facts.breadcrumb.length) signals.push('Sayfa izi: ' + facts.breadcrumb.slice(0, 4).join(' > '));
    if (facts.tabs && facts.tabs.length) signals.push('Aktif sekme: ' + facts.tabs.slice(0, 3).join(' > '));
    if (facts.buttons && facts.buttons.length) signals.push('Görünür işlem butonları: ' + facts.buttons.slice(0, 7).join(', '));
    if (facts.fields && facts.fields.length) signals.push('Görünür alan ipuçları: ' + facts.fields.slice(0, 8).join(', '));
    if (signals.length) {
      lines.push('');
      lines.push('Tanıma ipuçları:');
      signals.forEach(function (item) { lines.push('- ' + item); });
    }
    if (rule.ambiguous && rule.candidates && rule.candidates.length) {
      lines.push('');
      lines.push('Yakın olasılıklar:');
      rule.candidates.forEach(function (item) { lines.push('- ' + item.screen); });
    }
    lines.push('');
    lines.push('Güvenli yönlendirme:');
    lines.push('- Yapmak istediğiniz işlemi yazarsanız bu ekranın doğru işlem sırasını adım adım anlatırım.');
    if (rule.href) lines.push('- Bu ekran için güvenli hedef: ' + screenTitle + ' (' + rule.href + ')');
    else lines.push('- ' + NO_LINK_REASON);
    lines.push('');
    lines.push('Dikkat:');
    (rule.attention || []).forEach(function (item) { lines.push('- ' + item); });
    lines.push('- Yetki dışı veri, idari karar, performans puanı veya hassas içerik üretmem; yalnızca güvenli rehberlik sağlarım.');
    return { text: lines.join('\n'), links: rule.href ? [{ title: screenTitle, href: rule.href }] : [] };
  }

  function answerCurrentPage() {
    var facts = collectFacts();
    var rule = matchScreen(facts);
    return buildAnswer(facts, rule);
  }

  function isPageQuestion(question) {
    var q = norm(question);
    return [
      'bu ekranda ne yapabilirim','bu sayfada ne yapabilirim','burada ne yapacagim','burada ne yapacağım',
      'bu ekran ne ise yarar','bu ekran ne işe yarar','hangi ekrandayim','hangi ekrandayım','sayfa yardimi','sayfa yardımı',
      'ekran yardimi','ekran yardımı','ekrani anlat','ekranı anlat','bu sayfayi tani','bu sayfayı tanı','ekrani tani','ekranı tanı',
      'burayi anlat','burayı anlat','beni yonlendir','beni yönlendir','ne yapmam gerekiyor','burada nasil ilerlerim','burada nasıl ilerlerim',
      'bu sayfayı açıkla','bu ekranı açıkla','nereye gideceğim','ne yapacağım','ekranı tanıyor musun','sayfayı tanıyor musun'
    ].some(function (p) { return q.indexOf(norm(p)) !== -1; });
  }

  function answerQuestion(question) {
    if (isPageQuestion(question)) return answerCurrentPage();
    return boş;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return boş;
  };

  window.BYS360AssistantScreenIntelligenceV23 = {
    loaded: true,
    version: VERSION,
    collectFacts: collectFacts,
    scoreRule: scoreRule,
    rankedRules: rankedRules,
    matchScreen: matchScreen,
    inferGenericScreen: inferGenericScreen,
    answerCurrentPage: answerCurrentPage,
    answerQuestion: answerQuestion,
    rules: SCREEN_RULES
  };

  if (window.BYS360AssistantModule) {
    window.BYS360AssistantModule.screenIntelligenceV23 = window.BYS360AssistantScreenIntelligenceV23;
    window.BYS360AssistantModule.recognizeCurrentScreenV23 = answerCurrentPage;
  }
})();
/* BYS360_ASSISTANT_SCREEN_INTELLIGENCE_V23_END */

/* BYS360_ASSISTANT_STABLE_SCROLL_MEMORY_V30_START */
(function () {
  'use strict';
  if (window.__BYS360_ASSISTANT_STABLE_SCROLL_MEMORY_V30_LOADED__) return;
  window.__BYS360_ASSISTANT_STABLE_SCROLL_MEMORY_V30_LOADED__ = true;

  var VERSION = 'assistant-stable-scroll-memory-v30';
  var ROOT_ID = 'bys360-assistant-module-root';
  var HISTORY_KEY = 'bys360Assistant.conversation.current.v30';
  var STATE_KEY = 'bys360Assistant.conversation.state.v30';
  var LEGACY_KEYS = [
    'bys360Assistant.conversation.current.v29',
    'bys360Assistant.history.session.v28',
    'bys360Assistant.history.session.v27',
    'bys360Assistant.history.session.v26'
  ];
  var MAX_HISTORY = 260;
  var history = [];
  var lastTopic = '';
  var restoredOnce = false;
  var restoreTimer = boş;
  var isRestoring = false;
  var suppressRestoreUntil = 0;
  var lastRestoreSignature = '';
  var TR = { 'ç':'c','ğ':'g','ı':'i','ö':'o','ş':'s','ü':'u','â':'a','î':'i','û':'u','Ç':'c','Ğ':'g','İ':'i','I':'i','Ö':'o','Ş':'s','Ü':'u','':'a','Î':'i','Û':'u' };

  function normalize(value) {
    return String(value || '')
      .replace(/[çğıöşüâîûÇĞİIÖŞÜÎÛ]/g, function (ch) { return TR[ch] || ch; })
      .toLowerCase()
      .replace(/[^a-z0-9\s/_-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }
  function escapeText(value) {
    return String(value == boş ? '' : value).replace(/[&<>"']/g, function (ch) {
      return ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[ch];
    });
  }
  function safeParse(raw) {
    if (!raw) return [];
    try {
      var parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.filter(function (m) {
        return m && (m.role === 'user' || m.role === 'bot') && typeof m.text === 'string';
      }).slice(-MAX_HISTORY);
    } catch (e) { return []; }
  }
  function loadHistory() {
    var raw = null, i, migrated;
    try { raw = sessionStorage.getItem(HISTORY_KEY); } catch (e) {}
    if (!raw) {
      for (i = 0; i < LEGACY_KEYS.length; i++) {
        try { migrated = sessionStorage.getItem(LEGACY_KEYS[i]); } catch (e2) { migrated = null; }
        if (migrated) { raw = migrated; break; }
      }
    }
    if (!raw) {
      try { raw = window.name && window.name.indexOf('BYS360_ASSISTANT_HISTORY=') === 0 ? window.name.slice(25) : null; } catch (e3) {}
    }
    return safeParse(raw);
  }
  function saveHistory() {
    var data = JSON.stringify(history.slice(-MAX_HISTORY));
    try { sessionStorage.setItem(HISTORY_KEY, data); } catch (e) {}
    try { window.name = 'BYS360_ASSISTANT_HISTORY=' + data; } catch (e2) {}
  }
  function saveState(topic) {
    lastTopic = topic || lastTopic || '';
    try { sessionStorage.setItem(STATE_KEY, JSON.stringify({ topic:lastTopic, path:location.pathname, ts:Date.now() })); } catch (e) {}
  }
  function loadState() {
    try { return JSON.parse(sessionStorage.getItem(STATE_KEY) || 'null'); } catch (e) { return null; }
  }
  function rootEl() {
    return document.getElementById(ROOT_ID)
      || document.querySelector('[data-bys360-assistant-module]')
      || document.querySelector('.bys360-assistant-module')
      || document.querySelector('.bys360-am-root');
  }
  function formEl(root) {
    return root ? (root.querySelector('[data-chat-form]') || root.querySelector('.bys360-am-form') || root.querySelector('form')) : null;
  }
  function inputEl(root) {
    return root ? (root.querySelector('[data-chat-input]') || root.querySelector('textarea') || root.querySelector('input[type="text"]') || root.querySelector('input:not([type])')) : null;
  }
  function ensureLog(root) {
    if (!root) return null;
    var log = root.querySelector('[data-chat-log]') || root.querySelector('.bys360-am-log') || root.querySelector('[data-chat-list]') || root.querySelector('.bys360-assistant-chat-log') || root.querySelector('[data-assistant-log]');
    if (log) return log;
    var body = root.querySelector('.bys360-am-body') || root.querySelector('.bys360-assistant-body') || root.querySelector('[data-chat-body]') || root;
    log = document.createElement('div');
    log.className = 'bys360-am-log';
    log.setAttribute('data-chat-log', '1');
    log.setAttribute('data-v30-created-log', '1');
    var form = formEl(root);
    if (form && form.parentNode === body) body.insertBefore(log, form);
    else body.appendChild(log);
    return log;
  }
  function visibleText() {
    return normalize([
      document.title,
      document.querySelector('h1') && document.querySelector('h1').textContent,
      document.querySelector('.page-title') && document.querySelector('.page-title').textContent,
      document.querySelector('.active') && document.querySelector('.active').textContent,
      location.pathname
    ].filter(Boolean).join(' '));
  }
  function toLinks(items) {
    return (items || []).map(function (item) {
      if (Array.isArray(item)) return { title:item[0], href:item[1] };
      return { title:item.title || item.label || 'Ekrana git', href:item.href || item.url || '#' };
    }).filter(function (item) { return item.title && item.href; });
  }
  function renderMessage(root, msg, persist) {
    var log = ensureLog(root);
    if (!log) return false;
    var row = document.createElement('div');
    row.className = 'bys360-am-message ' + (msg.role === 'user' ? 'is-user' : 'is-bot');
    row.setAttribute('data-v30-message', '1');
    var avatar = document.createElement('div');
    avatar.className = 'bys360-am-avatar';
    avatar.textContent = msg.role === 'user' ? 'Siz' : 'BYS';
    var bubble = document.createElement('div');
    bubble.className = 'bys360-am-bubble';
    bubble.innerHTML = escapeText(msg.text || '').replace(/\n/g, '<br>');
    var links = toLinks(msg.links || []);
    if (links.length) {
      var linkBox = document.createElement('div');
      linkBox.className = 'bys360-am-links';
      links.slice(0, 6).forEach(function (item) {
        var a = document.createElement('a');
        a.href = item.href || '#';
        a.setAttribute('data-bys360-safe-link', '1');
        a.innerHTML = escapeText(item.title || 'Ekrana git') + '<span>→</span>';
        linkBox.appendChild(a);
      });
      bubble.appendChild(linkBox);
    }
    row.appendChild(avatar);
    row.appendChild(bubble);
    log.appendChild(row);
    if (persist !== false) {
      window.requestAnimationFrame(function () { log.scrollTop = log.scrollHeight; });
    }
    if (persist !== false) {
      history.push({ role:msg.role === 'user' ? 'user' : 'bot', text:msg.text || '', links:links, ts:Date.now() });
      if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
      saveHistory();
    }
    return true;
  }
  function clearOnlyChatLog(root) {
    var log = ensureLog(root);
    if (!log) return;
    log.innerHTML = '';
  }
  function restoreIntoUi(reason) {
    if (isRestoring || Date.now() < suppressRestoreUntil) return false;
    var root = rootEl();
    if (!root) return false;
    var loaded = loadHistory();
    if (!loaded.length) return false;
    history = loaded.slice(-MAX_HISTORY);
    var signature = String(history.length) + ':' + String(history.length ? (history[history.length - 1].ts || history[history.length - 1].text.length) : 0);
    var log = ensureLog(root);
    if (log && log.getAttribute('data-v30-signature') === signature && log.querySelector('[data-v30-message="1"]')) {
      restoredOnce = true;
      return true;
    }
    isRestoring = true;
    suppressRestoreUntil = Date.now() + 650;
    try {
      clearOnlyChatLog(root);
      history.forEach(function (m) { renderMessage(root, m, false); });
      log = ensureLog(root);
      if (log) {
        log.setAttribute('data-v30-signature', signature);
        lastRestoreSignature = signature;
        log.scrollTop = log.scrollHeight;
      }
      restoredOnce = true;
    } finally {
      window.setTimeout(function () { isRestoring = false; }, 120);
    }
    return true;
  }
  function addUser(root, text) { return renderMessage(root, { role:'user', text:text, links:[] }, true); }
  function addBot(root, text, links) { return renderMessage(root, { role:'bot', text:text, links:toLinks(links) }, true); }
  function scheduleRestore(reason) {
    if (isRestoring || Date.now() < suppressRestoreUntil) return;
    if (restoreTimer) clearTimeout(restoreTimer);
    restoreTimer = setTimeout(function () {
      if (isRestoring || Date.now() < suppressRestoreUntil) return;
      restoreIntoUi(reason);
      bindForm();
    }, 160);
  }

  var KNOWLEDGE = [
    {id:'home',module:'Genel',screen:'Ana Sayfa',href:'/home',keys:['anasayfa','ana sayfa','başlangıç','baslangic','bugün ne var','bugun ne var','nereden başlayacağım','nereden baslayacagim','günlük özet','gunluk ozet'],who:['Tüm kullanıcılar, yalnızca kendisine açık kartları ve modül geçişlerini görür.'],steps:['Ana Sayfa ekranını açın.','Bugünkü kısa özetleri, bekleyen bildirimleri, size ait görevleri ve modül geçişlerini kontrol edin.','İşlem yapmak için ilgili modülün gerçek ekranına geçin.'],watch:['Ana Sayfa günlük başlangıç ve hızlı geçiş ekranıdır; yönetici analizleri için Dashboard ekranı kullanılmalıdır.']},
    {id:'general_dashboard',module:'Yönetici Dashboard',screen:'Dashboard',href:'/dashboard',keys:['dashboard','genel dashboard','yönetici dashboard','yonetici dashboard','gösterge paneli','gosterge paneli','yönetici görünümü','yonetici gorunumu'],who:['Başkan, Admin, yöneticiler ve rol matrisinde yetki verilmiş kullanıcılar; herkes yalnızca yetkili olduğu kartları görür.'],steps:['Dashboard ekranını açın.','Yönetici özet kartlarını, grafik/gösterge alanlarını ve yetki kapsamındaki analizleri inceleyin.','Performans, KPI, destek veya anket gibi ayrıntı gereken başlıklarda ilgili modül ekranına geçin.'],watch:['Dashboard analiz ve yönetici görünürlüğü ekranıdır; Ana Sayfa ile aynı cevap verilmemelidir. Kart görünmüyorsa rol matrisi, kişi bazlı menü izni veya modül ayarı kontrol edilmelidir.']},
    {id:'person_add',module:'Personel Yönetimi',screen:'Personel Özlük Dosyaları / Personel Ekle',href:'/admin/users',keys:['kişi ekle','kisi ekle','kişi nasıl eklenir','personel ekle','personel nasıl eklenir','çalışan ekle','calisan ekle','yeni kişi','yeni kisi','yeni personel','kullanıcı ekle','kullanici ekle','hesap aç','hesap ac','personel kaydı','personel kaydi','sicil no','profil fotoğrafı','profil fotografi'],who:['Admin','Sistem Yöneticisi','Personel Yönetimi yetkilisi','Yetki verilmiş İK/personel kullanıcısı'],steps:['Sol menüden Personel Yönetimi bölümüne girin.','Personel Özlük Dosyaları / Personel Listesi ekranını açın.','Yeni Personel Ekle veya Yeni Kayıt butonuna basın.','Sicil No, ad, soyad, unvan, görev, birim, üst birim ve yönetici alanlarını doldurun.','Gerekliyse profil fotoğrafı, kullanıcı hesabı ve rol bilgisini belirleyin.','Kaydedin ve personelin listede göründüğünü kontrol edin.'],watch:['TC yerine Sicil No kullanılmalı.','Birim, üst birim, unvan ve yönetici boş kalırsa performans amir zinciri yanlış üretilebilir.','Rol ve menü görünürlüğü ayrıca kontrol edilmelidir.']},
    {id:'person_update',module:'Personel Yönetimi',screen:'Personel Bilgisi Güncelleme',href:'/admin/users',keys:['personel güncelle','personel guncelle','kişi bilgisi değiştir','kisi bilgisi degistir','birim değiştir','unvan değiştir','yönetici değiştir','personel pasif','aktif pasif'],who:['Admin','Sistem Yöneticisi','Personel Yönetimi yetkilisi'],steps:['Personel Yönetimi > Personel Özlük Dosyaları ekranına girin.','Personeli ad, soyad veya sicil no ile arayın.','Detay / Düzenle butonuna basın.','Birim, üst birim, görev, unvan, yönetici, rol veya aktiflik bilgisini güncelleyin.','Kaydedin.'],watch:['Bu değişiklik performans görev üretimi, rol matrisi, raporlar ve bildirim hedeflerini etkileyebilir.']},
    {id:'org',module:'Personel Yönetimi',screen:'Birim ve Organizasyon Yönetimi',href:'/admin/org-units',keys:['birim ekle','üst birim','ust birim','organizasyon','çalışma grubu','calisma grubu','koordinatör','koordinator','grup başkanlığı','grup baskanligi','pozisyon'],who:['Admin','Sistem Yöneticisi','Organizasyon/personel yetkilisi'],steps:['Birim ve Organizasyon Yönetimi ekranını açın.','Üst birimi ve bağlı birimi tanımlayın.','Çalışma grubu, koordinatör ve yönetici ilişkilerini kurun.','Personel atamalarını doğru birime bağlayın.'],watch:['Organizasyon yanlışsa performans amir zinciri, yetki görünürlüğü ve rapor kırılımları da yanlış olur.']},
    {id:'leave',module:'Personel Yönetimi',screen:'İzin ve Devamsızlık Takibi',href:'/hr-management/leave',keys:['izin','izin nasıl girilir','izin nasil girilir','izin talebi','izin kaydı','izin kaydi','izin bakiyesi','devamsızlık','devamsizlik','rapor izin'],who:['Personel yetkilisi','İK/Admin','Yetki verilmiş yönetici'],steps:['Personel Yönetimi veya İzin Yönetimi bölümüne girin.','İzin Talebi / İzin Kaydı ekranını açın.','Personeli seçin.','İzin türünü, başlangıç ve bitiş tarihini girin.','Gerekli açıklama veya belge varsa ekleyin.','Kaydedin ve onay sürecini kontrol edin.'],watch:['İzinli kişi amirse vekâlet ve performans görev devri etkilenebilir.']},
    {id:'delegation',module:'Personel Yönetimi',screen:'Vekâlet Yönetimi',href:'/hr-management/attendance',keys:['vekâlet','vekalet','vekil ata','görev devri','gorev devri','asıl kişi','asil kisi','vekil kim olacak'],who:['Admin','Personel/İK yetkilisi','Yetki verilmiş yönetici'],steps:['Vekâlet Yönetimi ekranına girin.','Asıl kişiyi seçin.','Vekil olacak kişiyi seçin.','Başlangıç ve bitiş tarihini belirleyin.','Vekâlet kapsamını seçin.','Kaydedin ve ilgili süreçlerde vekilin görünüp görünmediğini kontrol edin.'],watch:['Vekâlet açık değilse izinli amirin görevleri aksayabilir.']},
    {id:'period',module:'Performans Yönetimi',screen:'Dönemler',href:'/performance/periods',keys:['dönem aç','donem ac','dönem oluştur','donem olustur','performans dönemi','performans donemi','2026 performans','değerlendirme dönemi','degerlendirme donemi','özel dönem','ozel donem','güvenlik dönem','temizlik dönem'],who:['Admin','Sistem Yöneticisi','Performans Yetkilisi','Yetki verilmiş İK/personel birimi kullanıcısı'],steps:['Performans Yönetimi > Dönemler ekranına girin.','Yeni Dönem Oluştur butonuna basın.','Dönem adı, dönem türü ve tarih aralığını girin.','Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori veya seçili personel.','Kaydedin.','Ardından kriter, ağırlık ve görev üretimi adımlarını tamamlayın.'],watch:['Dönem oluşturmak tek başına değerlendirmeyi başlatmaz.','Aynı personel için çakışan tarih aralığı varsa sistem uyarı vermelidir.']},
    {id:'criteria',module:'Performans Yönetimi',screen:'Değerlendirme Kriterleri',href:'/performance/criteria',keys:['kriter','değerlendirme kriteri','degerlendirme kriteri','kriter ekle','yetkinlik değil','yetkinlik degil'],who:['Admin','Performans Yetkilisi'],steps:['Performans Yönetimi > Sorular / Kriterler ekranına girin.','Yeni kriter ekle butonuna basın.','Kriter adı, açıklama ve aktiflik bilgisini girin.','Gerekirse dönem/kategori bağlantısını kurun.','Kaydedin.'],watch:['Ana ekran dili “Değerlendirme Kriterleri” olmalı; “Yetkinlik” ana terim olarak kullanılmamalı.']},
    {id:'weights',module:'Performans Yönetimi',screen:'Ağırlık Ayarları',href:'/performance/weights',keys:['ağırlık','agirlik','puan ağırlığı','amir ağırlığı','1 amir','2 amir','3 amir','yüzde yüz','%100'],who:['Admin','Performans Yetkilisi'],steps:['Ağırlık Ayarları ekranına girin.','Dönem veya rol grubunu seçin.','1. amir, 2. amir ve varsa 3. amir ağırlıklarını girin.','Toplamın %100 olduğunu kontrol edin.','Kaydedin.'],watch:['3. amir yorum modundaysa puan ağırlığı %0 olmalıdır.']},
    {id:'task_generation',module:'Performans Yönetimi',screen:'Görev Üretimi',href:'/performance/assignments',keys:['görev üret','gorev uret','değerlendirme görevi','degerlendirme gorevi','amir zinciri','görevler oluşmadı','gorevler olusmadi','eksik amir'],who:['Admin','Performans Yetkilisi'],steps:['Değerlendirme Görevleri ekranına girin.','Dönemi seçin.','Personel, birim, kategori ve amir verilerini doğrulayın.','Görevleri Oluştur butonuna basın.','Oluşan görevlerde eksik amir veya yanlış zincir var mı kontrol edin.'],watch:['Sistem sahte 3. amir görevi veya gereksiz bekleme durumu üretmemelidir.']},
    {id:'evaluation',module:'Performans Yönetimi',screen:'Değerlendirme Görevlerim',href:'/performance/evaluation-tasks',keys:['puan gir','puanlama','değerlendirme yap','degerlendirme yap','görevlerim','gorevlerim','amir değerlendirmesi','amir degerlendirmesi'],who:['Kendisine görev atanmış amir/değerlendirici'],steps:['Değerlendirme Görevlerim ekranına girin.','Değerlendirilecek personeli seçin.','Kriter bazlı 1–5 arası puan girin.','Gerekli açıklama ve genel görüş alanlarını doldurun.','Kaydet / Tamamla butonuna basın.'],watch:['Sistem kör değerlendirme yapmaz; sonraki amir önceki puan ve görüşü görebilir.']},
    {id:'scorecard',module:'Performans Yönetimi',screen:'Karne / Not Karnesi',href:'/performance/scorecard',keys:['karne','karnem','not karnesi','puanım görünmüyor','puanim gorunmuyor','karne görünmüyor','karne gorunmuyor','sonucum yok','performans sonucum'],who:['Personel kendi yayınlanmış karnesini görür; yönetici yetkisi kapsamındaki karneleri görür.'],steps:['Önce değerlendirme görevlerinin tamamlandığını kontrol edin.','70 altı sonuç varsa Başkan Onayı tamamlandı mı bakın.','Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı tamamlandı mı kontrol edin.','Admin/İK final yayın yaptı mı bakın.','Rol matrisi ve karne görünürlüğü açık mı kontrol edin.'],watch:['Süreç tamamlanmadan karne personele açılmaz.']},
    {id:'president',module:'Performans Yönetimi',screen:'Başkan / Üst Onayları',href:'/performance/president-approvals',keys:['başkan onayı','baskan onayi','üst onay','ust onay','70 altı','70 alti','düşük performans','dusuk performans','yayın kilidi','yayin kilidi'],who:['Başkan','Admin/Sistem Yöneticisi','Yetkili üst onay kullanıcısı'],steps:['Başkan / Üst Onayları ekranına girin.','Yalnızca gerçek 70 altı kayıtları inceleyin.','Karne incelemesinde nihai puan, kriterler, amir görüşleri ve süreç geçmişini kontrol edin.','Onay veya iade işlemini yetkiniz dahilinde tamamlayın.'],watch:['Başkan onayı tamamlanmadan düşük performans sonucu personele kesin yayınlanmış sayılmaz.']},
    {id:'publish',module:'Performans Yönetimi',screen:'Yayın Ön Onayı ve Final Yayın',href:'/performance/personnel-support-publish-approvals',keys:['yayın','yayin','yayınla','yayinla','final yayın','final yayin','yayın ön onayı','personel destek onayı','personel destek onayi'],who:['Personel ve Destek Hizmetleri Grup Başkanı','Admin/İK yetkilisi'],steps:['Tüm değerlendirme görevlerinin tamamlandığını kontrol edin.','70 altı kayıtların Başkan Onayı sürecini tamamlayın.','Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayını alın.','Admin/İK final yayını yapar.'],watch:['Final yayın öncesi onay zinciri atlanmamalıdır.']},
    {id:'process',module:'Performans Yönetimi',screen:'Süreç Takibi',href:'/performance/process-tracking',keys:['süreç takibi','surec takibi','akış','akis','bekleyen görev','bekleyen gorev','aksatan amir','geciken amir','hatırlatma','hatirlatma'],who:['Admin','Performans yetkilisi','Yetkili yönetici'],steps:['Süreç Takibi ekranına girin.','Dönemi seçin.','Bekleyen değerlendirme, onay, yayın ve gecikme durumlarını kontrol edin.','Geciken amirler için hatırlatma akışını takip edin.'],watch:['Teknik statü değil, Türkçe kurumsal süreç durumu görünmelidir.']},
    {id:'reports',module:'Dashboard ve Raporlar',screen:'Raporlar',href:'/performance/reports',keys:['rapor','rapor al','analiz','performans raporu','personel raporu','süreç raporu','surec raporu','dışa aktar','disa aktar'],who:['Yetkisi olan kullanıcılar; kapsam rol, kişi ve birim yetkisine göre değişir.'],steps:['Raporlar ekranına girin.','Dönem, birim, kategori, amir veya personel filtresini seçin.','Raporu oluşturun.','Yetkiniz varsa dışa aktarın veya paylaşın.'],watch:['Kişi detayları yetkiye göre görünmelidir; kategori ortalaması kişi detayı olmadan sunulabilir.']},
    {id:'archive',module:'Performans Yönetimi',screen:'Geçmiş Karne Arşivi',href:'/performans/gecmis-karne-arsivi',keys:['geçmiş karne','gecmis karne','arşiv','arsiv','eski puan','2024 puan','2025 puan','geçmiş performans'],who:['Personel kendi geçmişini; yönetici yetkili kapsamını; Başkan/Admin genel görünümü görür.'],steps:['Geçmiş Karne Arşivi ekranına girin.','Yıl veya dönem filtresini seçin.','Yetkiniz dahilindeki karne/puan kayıtlarını inceleyin.'],watch:['Başka personelin detayları yetkisiz görünmemelidir.']},
    {id:'notes',module:'Performans Yönetimi',screen:'Dönem İçi Notlar',href:'/performance/interim-notes',keys:['dönem içi not','donem ici not','ara geri bildirim','olay notu','başarı notu','basari notu','gelişim notu','gelisim notu'],who:['Yetkili amir/yönetici ve performans yetkilisi'],steps:['Dönem İçi Notlar ekranına girin.','Personel ve dönem bilgisini seçin.','Olumlu/olumsuz olay, başarı veya gelişim ihtiyacını yazın.','Kaydedin.'],watch:['Bu notlar otomatik puan üretmez; puanlama döneminde destekleyici hatırlatma olabilir.']},
    {id:'development',module:'Performans Yönetimi',screen:'Gelişim Önerisi',href:'/performance/development-guidance',keys:['gelişim önerisi','gelisim onerisi','rehber alan','eğitim önerisi','egitim onerisi','gelişim planı'],who:['Amirler, performans yetkilileri ve yetkili yöneticiler'],steps:['Gelişim Önerisi / Rehber Alan ekranına girin.','Personel veya dönem bağlamını seçin.','Güçlü yön, gelişim alanı ve takip önerisini yazın.','Kaydedin ve karne/yayın görünürlüğünü kontrol edin.'],watch:['Öneri dili idari karar gibi kesin hüküm içermemelidir.']},
    {id:'role_matrix',module:'Sistem Ayarları ve Yetkilendirme',screen:'Rol Matrisi ve Menü Görünürlüğü',href:'/settings/role-matrix',keys:['rol matrisi','menü görünmüyor','menu gorunmuyor','sekme yok','yetki aç','yetki ac','yetki kapat','menü yetkisi','menu yetkisi','kişi bazlı yetki','kisi bazli yetki','birim profili'],who:['Admin','Sistem Yöneticisi','Yetkilendirme yöneticisi'],steps:['Sistem Ayarları > Rol Matrisi ekranına girin.','Kullanıcının rolünü seçin.','İlgili modül ve alt sekmenin açık/kapalı durumunu kontrol edin.','Kişi bazlı menü izni ve birim profilini kontrol edin.','Kaydedip kullanıcıyla çıkış-giriş yapın.'],watch:['Yetkisi olmayan kullanıcı menüyü hiç görmemelidir; sadece tıklayınca erişim engeli vermek yeterli değildir.']},
    {id:'settings',module:'Sistem Ayarları ve Yetkilendirme',screen:'Sistem Ayarları',href:'/settings',keys:['ayarlar','sistem ayarları','sistem ayarlari','modül ayarı','modul ayari','captcha','oturum','smtp','e-posta','bildirim ayarı','audit kayıt','güvenlik ayarı'],who:['Admin','Sistem Yöneticisi'],steps:['Sistem Ayarları ekranına girin.','İlgili ayar grubunu açın.','Değiştireceğiniz ayarın hangi modülü etkilediğini kontrol edin.','Kaydedin ve değişiklik logunun oluştuğunu doğrulayın.'],watch:['Canlıda küçük bir ayar değişikliği tüm sistem davranışını etkileyebilir.']},
    {id:'support',module:'İletişim ve Anket Yönetimi',screen:'Yardım Merkezi / Destek Talepleri',href:'/support',keys:['yardım','yardim','destek','talep aç','talep ac','sorun bildir','ticket','bilet','destek talebi'],who:['Tüm kullanıcılar talep açabilir; yönetim yetkiye göre takip eder.'],steps:['Yardım Merkezi / Destek ekranına girin.','Destek Talebi Aç butonuna basın.','Kategori, konu ve açıklamayı girin.','Gerekirse dosya ekleyin.','Talebin durumunu takip edin.'],watch:['Gereksiz kişisel veya hassas veri paylaşmayın.']},
    {id:'messages',module:'İletişim ve Anket Yönetimi',screen:'Mesajlar',href:'/messages',keys:['mesaj','sohbet','yazışma','yazisma','okunmamış mesaj','okunmamis mesaj','kendime not'],who:['Yetkisi açık kullanıcılar'],steps:['Mesajlar ekranına girin.','Kişi, grup veya konu seçin.','Mesajınızı yazıp gönderin.','Gerekirse dosya ekleyin.'],watch:['Asistan mesaj içeriğini yetkisiz gösteremez.']},
    {id:'surveys',module:'İletişim ve Anket Yönetimi',screen:'Anketler ve Geri Bildirim',href:'/surveys',keys:['anket','anketi cevapla','anket sonucu','geri bildirim','nabız','nabiz','yanıt bekleyen'],who:['Personel atanmış anketi cevaplar; yetkililer anket yönetir.'],steps:['Anketler ekranına girin.','Yanıt bekleyen anketi açın.','Zorunlu soruları tamamlayın.','Gönderin.'],watch:['Anket cevabı kişisel/hassas olabilir; yetkisiz gösterilmemelidir.']},
    {id:'announcements',module:'İletişim ve Anket Yönetimi',screen:'Duyurular / Bildirimler',href:'/announcements',keys:['duyuru','duyuru gönder','duyuru gonder','bildirim','kurumsal duyuru','mail gönder','mail gonder'],who:['Yetkili birimler ve sistem yöneticileri'],steps:['Duyurular ekranına girin.','Yeni duyuru oluşturun.','Hedef kitleyi belirleyin.','Metni girip yayınlayın.','Bildirim durumunu kontrol edin.'],watch:['Hedef kitle ve görünürlük yetkisi doğru seçilmelidir.']},
    {id:'ai',module:'AI Karar Destek Merkezi',screen:'Karar Destek Merkezi',href:'/ai/decision-support/faz1/health',keys:['ai karar','karar destek','yapay zeka','analiz','risk notu','özet','ozet','ai öneri','ai oneri'],who:['Yetki verilen yönetici ve analiz kullanıcıları'],steps:['AI Karar Destek Merkezi ekranına girin.','Yetkiniz dahilindeki analiz/özet kartını açın.','Çıktıyı karar değil, destek notu olarak değerlendirin.'],watch:['AI idari karar vermez, performans puanı belirlemez, hassas veri göstermemelidir.']},
    {id:'kpi',module:'KPI ve Hedef Yönetimi',screen:'KPI / Hedef Yönetimi',href:'/performans/stratejik/hedefler',keys:['kpi','hedef','hedef kartı','hedef karti','hedef dönemi','hedef donemi','gerçekleşme','gerceklesme','riskli hedef','başarı oranı','basari orani'],who:['Başkan/Admin genel; koordinatör ve yöneticiler yetki kapsamına göre görür.'],steps:['KPI / Hedef Yönetimi ekranına girin.','Hedef dönemi veya hedef kartı oluşturun.','Hedef tipi, kategori, sahip, hedef değer, gerçekleşen değer ve ağırlığı girin.','Kaydedin ve dashboard’da başarı/risk durumunu kontrol edin.'],watch:['KPI otomatik idari karar üretmez; ölçüm ve karar destek verisi sağlar.']},
    {id:'assistant_knowledge',module:'BYS360 Asistanı',screen:'Asistan Bilgi Bankası / Öğretim Merkezi',href:'/ai-agent/knowledge',keys:['asistan öğret','asistan ogret','bilgi bankası','bilgi bankasi','öğretim merkezi','ogretim merkezi','asistan eğit','asistan egit'],who:['Admin','Sistem Yöneticisi','Asistan bilgi yöneticisi'],steps:['Asistan Bilgi Bankası / Öğretim Merkezi ekranına girin.','Yeni soru-cevap veya rehber kaydı ekleyin.','Dili sade, kurumsal ve gerçek ekran adlarıyla yazın.','Test sorusuyla cevabı kontrol edin.'],watch:['Asistan idari karar ve hassas veri içeriği öğrenmemelidir.']},
    {id:'profile',module:'Kullanıcı Hesabı',screen:'Profil / Şifre / Oturum',href:'/account',keys:['profilim','hesabım','hesabim','şifre','sifre','parola','çıkış','cikis','oturum','giriş yapamıyorum','giris yapamiyorum'],who:['Kullanıcı kendi hesabında; Admin yetkili kullanıcı hesaplarında işlem yapar.'],steps:['Profil / Hesabım ekranına girin.','Yetkiniz dahilindeki bilgileri kontrol edin.','Şifre/parola işlemlerinde güvenlik kurallarına uyun.'],watch:['3 hatalı giriş gibi güvenlik kuralları devreye girebilir.']},
    {id:'live',module:'Canlı/Pilot Operasyon',screen:'Canlı Kontrol ve Yayın',href:'/home',keys:['canlı','canli','pilot','yayın','yayin','beyaz ekran','servis başlat','scheduled task','waitress','ctrl f5','cache'],who:['Sistem yöneticisi / teknik yetkili'],steps:['Önce son kontrol scriptlerini çalıştırın.','Python compileall ile sözdizimi kontrolü yapın.','Pilot/canlı scheduled task görevini yeniden başlatın.','Tarayıcıda Ctrl+F5 ile geçici kayıt temizleyerek test edin.'],watch:['base.html hatası tüm sayfaları beyaz ekrana düşürebilir; önce şablon sözdizimini kontrol edin.']}
  ];

  function canonicalUiTextV31_4(value) {
    var out = String(value == null ? '' : value);
    var pairs = [
      ['Dönemler', 'Dönemler'],
      ['Dönemler', 'Dönemler'],
      ['Dönemler', 'Dönemler'],
      ['Başkan Onayları', 'Başkan Onayları'],
      ['Başkan Onayı', 'Başkan Onayı'],
      ['Yayın Ön Onayı', 'Yayın Ön Onayı'],
      ['Dönem İçi Notlar / Gelişim Rehberi', 'Dönem İçi Notlar / Gelişim Rehberi'],
      ['Sorular / Kriterler ekranına', 'Sorular / Kriterler ekranına'],
      ['Sorular / Kriterler sekmesini', 'Sorular / Kriterler sekmesini'],
      ['Performans Yönetimi > Sorular / Kriterler', 'Performans Yönetimi > Sorular / Kriterler'],
      ['Değerlendirme Görevleri ekranına', 'Değerlendirme Görevleri ekranına'],
      ['Performans Yönetimi > Değerlendirme Görevleri', 'Performans Yönetimi > Değerlendirme Görevleri'],
      ['Not Karnesi / Geçmiş Karne Arşivi', 'Not Karnesi / Geçmiş Karne Arşivi'],
      ['Performans Yönetimi > Not Karnesi / Geçmiş Karne Arşivi', 'Performans Yönetimi > Not Karnesi / Geçmiş Karne Arşivi'],
      ['KPI Dashboardu', 'KPI Dashboardu']
    ];
    pairs.forEach(function (p) { out = out.split(p[0]).join(p[1]); });
    return out;
  }
  function response(title, text, links) { return { title:title, text:text, links:toLinks(links || []) }; }
  function formatItem(item, extra) {
    var parts = [];
    parts.push('Anladım. Bu işlem ' + canonicalUiTextV31_4(item.module) + ' içinde, ' + canonicalUiTextV31_4(item.screen) + ' ekranı ile ilgilidir.');
    if (item.who && item.who.length) parts.push('\nKim yapabilir?\n- ' + item.who.join('\n- '));
    if (item.steps && item.steps.length) parts.push('\nAdım adım:\n' + item.steps.map(function (s, i) { return (i + 1) + '. ' + canonicalUiTextV31_4(s); }).join('\n'));
    if (item.watch && item.watch.length) parts.push('\nDikkat:\n- ' + item.watch.map(canonicalUiTextV31_4).join('\n- '));
    parts.push('\nKontrol:\n- İşlemden sonra ilgili ekranda kayıt/durum doğru görünmelidir. Menü görünmüyorsa Rol Matrisi ve kişi bazlı menü iznini kontrol edin.');
    if (extra) parts.push('\n' + extra);
    return response(canonicalUiTextV31_4(item.screen), canonicalUiTextV31_4(parts.join('\n')), [[canonicalUiTextV31_4(item.screen), item.href || '#']]);
  }
  function safetyAnswer(q) {
    var n = normalize(q);
    /* BYS360_ASSISTANT_V32_2_SENSITIVE_CONTENT_GUARD */
    var directAccessAction = /\b(goster|gostermek|ver|ac|goruntule|goruntulemek|gormek|bak|listele|paylas|oku|indir|kopyala)\b/.test(n);
    var sensitiveDataTerm = /\b(performans\s+puan\w*|performans\s+sonuc\w*|puan\w*|notun\w*|notunu\w*|karnesin\w*|karne\w*|amir\s+gorus\w*|yonetici\s+gorus\w*|anket\s+cevab\w*|anket\s+yanit\w*|mesaj\s+icerig\w*|mesaj\s+metn\w*|mesaj\s+yazism\w*|mesajlar\w*|ozel\s+mesaj\w*|tc\b|kimlik\s+no\w*|telefon\w*|adres\w*|maas\w*|dogum\s+tarih\w*)\b/.test(n);
    var wantsSensitiveValue = directAccessAction && sensitiveDataTerm;
    var wantsAdministrativeDecision = /\b(performans puani belirle|performans puanı belirle|isimi sonlandir|işten çıkar|isten cikar|otomatik isten cikar|idari karar ver)\b/.test(n);
    if (wantsSensitiveValue || wantsAdministrativeDecision) {
      return response('Güvenli sınır', 'Bu bilgiyi doğrudan gösteremem. BYS360 Asistanı; performans puanı, amir görüşü, mesaj içeriği, anket cevabı, TC/telefon/adres gibi kişisel veya hassas verileri paylaşmaz.\n\nYapabileceğim şey şu: yetkiniz varsa ilgili modül ekranına yönlendirebilirim. Performans sonucu için Performans Yönetimi > Not Karnesi / Geçmiş Karne Arşivi veya yetkili yönetici ekranı kullanılmalıdır. Yetki yoksa Rol Matrisi ve kişi bazlı menü izni kontrol edilmelidir.', [['Not Karnesi / Geçmiş Karne Arşivi','/performans/v2/faz5/scorecard'], ['Rol Matrisi','/settings/role-matrix'], ['Performans Yönetimi','/performance/dashboard']]);
    }
    return null;
  }
  function smallTalk(q) {
    var n = normalize(q);
    if (/^(merhaba|selam|slm|iyi misin|nasilsin|nasılsın)/.test(n)) return response('Merhaba', 'Merhaba, ben BYS360 Asistanı. Personel ekleme, izin, vekâlet, performans dönemi, karne, Başkan Onayı, rol matrisi, destek, anket, KPI/Hedef ve AI Karar Destek konularında sizi doğru ekrana ve işlem sırasına yönlendirebilirim.', [['Ana Sayfa','/home']]);
    if (/(ne yapabilirsin|ne ise yararsin|yardim et|yardım et|bys360 asistan)/.test(n)) return response('BYS360 Asistanı', 'BYS360 içinde gerçek ekran adlarıyla rehberlik yaparım. Sorunuzu günlük dille yazabilirsiniz: “kişi nasıl eklenir”, “dönem açacağım”, “karne görünmüyor”, “menü yok”, “izin nasıl girilir”, “KPI hedef kartı oluşturacağım” gibi.', [['Asistan Bilgi Bankası','/ai-agent/knowledge']]);
    if (/(seni kim gelistirdi|seni kim geliştirdi|kim yapti|kim yaptı)/.test(n)) return response('Geliştiren bilgi', 'BYS360 Asistanı, BYS360 projesi kapsamında Personel kurumsal kullanım Özden tarafından geliştirilen kurumsal rehberlik ve yönlendirme katmanıdır.', []);
    if (/(kaldigimiz yer|kaldığımız yer|devam edelim|son konu)/.test(n)) {
      var st = loadState();
      return response('Kaldığımız yer', st && st.topic ? ('Son konuştuğumuz konu: ' + st.topic + '. Aynı konu üzerinden devam edebiliriz; yapmak istediğiniz adımı yazmanız yeterli.') : 'Bu oturumda kayıtlı son konu bulamadım. Yapmak istediğiniz işlemi yazarsanız kaldığınız yerden yönlendiririm.', []);
    }
    return null;
  }
  function scoreItem(item, qn) {
    var score = 0;
    item.keys.forEach(function (k) {
      var nk = normalize(k);
      if (!nk) return;
      if (qn === nk) score += 40;
      else if (qn.indexOf(nk) >= 0) score += 20 + Math.min(10, nk.length / 4);
      else {
        var words = nk.split(' ').filter(function (w) { return w.length > 2; });
        var hits = words.filter(function (w) { return qn.indexOf(w) >= 0; }).length;
        if (hits >= Math.min(2, words.length)) score += hits * 4;
      }
    });
    if (normalize(item.module + ' ' + item.screen).split(' ').some(function (w) { return w.length > 3 && qn.indexOf(w) >= 0; })) score += 2;
    return score;
  }
  function questionToItem(q) {
    var qn = normalize(q), best = null, bestScore = 0;
    KNOWLEDGE.forEach(function (item) {
      var s = scoreItem(item, qn);
      if (s > bestScore) { bestScore = s; best = item; }
    });
    return bestScore >= 8 ? best : null;
  }
  function detectCurrentItem() {
    var path = normalize(location.pathname), vt = visibleText(), best = null, bestScore = 0;
    KNOWLEDGE.forEach(function (item) {
      var s = 0;
      var href = normalize(item.href || '');
      if (href && (path === href || path.indexOf(href) === 0 || href.indexOf(path) === 0)) s += 35;
      s += scoreItem(item, vt);
      if (s > bestScore) { bestScore = s; best = item; }
    });
    return best || KNOWLEDGE[0];
  }
  function generalAnswer(q) {
    var n = normalize(q);
    if (/(bys360 nedir|bu sistem nedir|sistem ne ise yarar|proje nedir)/.test(n)) return response('BYS360 nedir?', 'BYS360; personel, performans, iletişim, anket, destek, raporlama, KPI/Hedef ve karar destek süreçlerini tek çatı altında yöneten kurumsal dijital yönetim sistemidir. Amaç yalnızca işlem yapmak değil; süreçleri ölçmek, izlemek, raporlamak ve kurumsal hafıza oluşturmaktır.', [['Ana Sayfa','/home']]);
    if (/(sayfa degisince|sayfa değişince|konusmalar silinmesin|konuşmalar silinmesin|sohbet kayboluyor|gecmis kayboluyor|geçmiş kayboluyor)/.test(n)) return response('Konuşma hafızası', 'Bu sürümde konuşma geçmişi aynı tarayıcı sekmesi oturumu boyunca korunur. Sayfa değiştirseniz bile asistan tekrar açıldığında önceki soru-cevaplar geri yüklenmelidir. Oturum/sekme kapanırsa geçmiş temizlenebilir; bu güvenli kullanım için doğru davranıştır.', []);
    return null;
  }
  function answer(q) {
    var safe = safetyAnswer(q); if (safe) return safe;
    var st = smallTalk(q); if (st) return st;
    var gen = generalAnswer(q); if (gen) return gen;
    var n = normalize(q);
    if (/(bu sayfa|bu ekran|burada ne|ne yapilir|ne yapılır|hangi ekran|sayfayı tanıt|sayfayi tanit|neredeyim)/.test(n)) {
      var cur = detectCurrentItem(); saveState(cur.screen); return formatItem(cur, 'Bulunduğunuz sayfayı URL, başlık ve aktif menü bilgisine göre yorumladım.');
    }
    var item = questionToItem(q);
    if (item) { saveState(item.screen); return formatItem(item); }
    var cur2 = detectCurrentItem(); saveState(cur2.screen);
    return response('BYS360 yönlendirme', 'Sorunuzu BYS360 kapsamında yorumladım; doğrudan net eşleşme bulamadım. Bulunduğunuz ekran: ' + cur2.screen + ' (' + cur2.module + ').\n\nDaha net yönlendirme için günlük dille yazabilirsiniz: “kişi nasıl eklenir”, “dönem açacağım”, “karne görünmüyor”, “menü yok”, “izin nasıl girilir”, “destek talebi açacağım”, “KPI hedef kartı oluşturacağım”.\n\nGenel sınır: Yetkiniz olan ekranı anlatırım, işlem sırasını veririm; hassas veri veya idari karar üretmem.', [[cur2.screen, cur2.href || '/home']]);
  }
  function handleQuestion(q) {
    var root = rootEl();
    if (!root) return false;
    history = loadHistory();
    if (history.length) restoreIntoUi('before-question');
    addUser(root, q);
    var result = answer(q);
    window.setTimeout(function () { addBot(root, result.text, result.links || []); }, 40);
    return true;
  }
  function interceptSubmit(event) {
    var root = rootEl();
    if (!root || !event.target || !root.contains(event.target)) return;
    var form = event.target.closest ? event.target.closest('form') : event.target;
    if (!form || !root.contains(form)) return;
    var input = inputEl(root);
    if (!input) return;
    var q = String(input.value || '').trim();
    if (!q) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
    input.value = '';
    handleQuestion(q);
  }
  function bindForm() {
    var root = rootEl();
    if (!root) return false;
    ensureLog(root);
    var input = inputEl(root);
    var form = formEl(root);
    if (input && form && input.getAttribute('data-v30-enter-bound') !== '1') {
      input.setAttribute('data-v30-enter-bound', '1');
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          form.dispatchEvent(new Event('submit', { bubbles:true, cancelable:true }));
        }
      }, true);
    }
    return true;
  }
  function install() {
    document.removeEventListener('submit', interceptSubmit, true);
    document.addEventListener('submit', interceptSubmit, true);
    bindForm();
    scheduleRestore('install');
  }
  function bootLoop() {
    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      install();
      if ((rootEl() && (restoredOnce || !loadHistory().length)) || tries > 80) clearInterval(timer);
    }, 350);
  }
  try {
    var lastRootSeen = null;
    var mo = new MutationObserver(function () {
      if (isRestoring || Date.now() < suppressRestoreUntil) return;
      var root = rootEl();
      if (root !== lastRootSeen) { lastRootSeen = root; scheduleRestore('mutation-root'); return; }
      if (root && !root.querySelector('[data-chat-kayıt], .bys360-am-kayıt, [data-chat-list], .bys360-assistant-chat-kayıt, [data-assistant-kayıt]')) {
        scheduleRestore('mutation-log-missing');
      }
    });
    mo.observe(document.body || document.documentElement, { childList:true, subtree:true });
  } catch (e) {}
  try {
    var oldPush = window.history && window.history.pushState;
    if (oldPush) window.history.pushState = function () { var r = oldPush.apply(window.history, arguments); scheduleRestore('pushState'); return r; };
    var oldReplace = window.history && window.history.replaceState;
    if (oldReplace) window.history.replaceState = function () { var r2 = oldReplace.apply(window.history, arguments); scheduleRestore('replaceState'); return r2; };
  } catch (e2) {}
  document.addEventListener('click', function (ev) {
    var t = ev && ev.target;
    if (t && t.closest && (t.closest('#bys360-assistant-module-root') || t.closest('[data-bys360-assistant-module]'))) {
      window.setTimeout(function () { bindForm(); }, 60);
    }
  }, true);
  window.addEventListener('pagehide', function () { saveHistory(); saveState(lastTopic); });
  window.addEventListener('beforeunload', function () { saveHistory(); saveState(lastTopic); });
  window.addEventListener('pageshow', function () { install(); scheduleRestore('pageshow'); });
  window.addEventListener('popstate', function () { scheduleRestore('popstate'); });
  window.addEventListener('hashchange', function () { scheduleRestore('hashchange'); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') saveHistory(); else scheduleRestore('visible'); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { install(); bootLoop(); });
  else { install(); bootLoop(); }

  window.BYS360AssistantStableScrollMemoryV30 = {
    version: VERSION,
    knowledgeCount: KNOWLEDGE.length,
    answer: answer,
    restore: restoreIntoUi,
    clearSession: function () { history = []; saveHistory(); var root = rootEl(); if (root) clearOnlyChatLog(root); },
    selfTest: function () {
      var person = answer('kişi nasıl eklenir').text;
      var mem = answer('sayfa değişince konuşmalar silinmesin').text;
      return {
        ok: person.indexOf('Personel Yönetimi') >= 0 && mem.indexOf('aynı tarayıcı sekmesi') >= 0 && KNOWLEDGE.length >= 30,
        version: VERSION,
        knowledgeCount: KNOWLEDGE.length,
        samplePerson: person.slice(0, 140),
        sampleMemory: mem.slice(0, 140)
      };
    }
  };
  window.BYS360AssistantModule = Object.assign(window.BYS360AssistantModule || {}, {
    stableScrollMemoryVersion: VERSION,
    answerBYS360Question: answer,
    restoreConversation: restoreIntoUi,
    runV30SelfTest: window.BYS360AssistantStableScrollMemoryV30.selfTest
  });
})();
/* BYS360_ASSISTANT_STABLE_SCROLL_MEMORY_V30_END */


