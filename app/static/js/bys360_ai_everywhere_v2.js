/* BYS360_AI_EVERYWHERE_V2_WORKING
   Sonradan eklenen ekranlar dahil tüm BYS360 sayfalarına güvenli AI rehber ve asistan yönlendirme katmanı ekler.
   Bu katman karar vermez, puan üretmez, hassas veri göstermez.
*/
(function(){
  'use strict';
  var VERSION = 'BYS360_AI_EVERYWHERE_V2_WORKING';
  var CARD_ID = 'bys360-ai-everywhere-card';
  var COLLAPSE_KEY = 'bys360.aiEverywhere.collapsed.v1';

  function lower(v){ return String(v || '').toLowerCase(); }
  function trim(v){ return String(v || '').replace(/\s+/g,' ').trim(); }
  function escapeHtml(value){
    return String(value == null ? '' : value).replace(/[&<>"']/g, function(ch){
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]);
    });
  }
  function path(){ return lower(window.location.pathname || '/'); }
  function hash(){ return lower(window.location.hash || ''); }
  function pageTitle(){
    var candidates = [
      document.querySelector('[data-page-title]'),
      document.querySelector('.page-title'),
      document.querySelector('h1'),
      document.querySelector('h2'),
      document.querySelector('title')
    ];
    for(var i=0;i<candidates.length;i++){
      if(candidates[i] && trim(candidates[i].textContent)) return trim(candidates[i].textContent).slice(0,90);
    }
    return 'BYS360 ekranı';
  }

  var RULES = [
    {
      id:'performance-category-card',
      test:function(p){return /\/performance\/v2-1-3-personnel-category-card|personel-category-card|personel-kategori/i.test(p);},
      module:'Performans Yönetimi', screen:'Personel Kategori Atama', icon:'fa-tags',
      summary:'Personelin Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel veya Diğer gibi gruplara doğru bağlanmasını destekler. AI desteği, kategori eksikliği ve kapsam etkisi konusunda güvenli kontrol listesi sunar.',
      ai:'Kategori eksikliği, kapsam dışı personel ve grup ortalaması risklerini fark ettirir.',
      action:'Personel kartı, kategori seçimi, import alanı ve rapor filtresini aynı mantıkla kontrol ettirir.',
      guard:'Kişi detayı ve performans puanı göstermez; yalnızca yetkili işlem yolunu anlatır.',
      questions:['Bu ekranda personel kategorisi nasıl atanır?','Kategori eksikse performans görevleri nasıl etkilenir?','Güvenlik personeline özel dönem için önce neyi kontrol etmeliyim?'],
      links:[['Kategori Dönem Kapsamı','/performance/v2-1-5-category-period-scope'],['Performans Yönetimi','/performance/dashboard']]
    },
    {
      id:'performance-category-scope',
      test:function(p){return /\/performance\/v2-1-4-category-scope|category-scope/i.test(p);},
      module:'Performans Yönetimi', screen:'Kategori Kapsam Hazırlığı', icon:'fa-layer-group',
      summary:'Kategori bazlı dönem veya rapor kapsamı oluşturmadan önce hangi personelin kapsama gireceğini anlaşılır hale getirir.',
      ai:'AI ekran rehberi, kapsam dışı kalan personel ve yetkisiz görünürlük risklerine dikkat çeker.',
      action:'Kapsamı oluşturmadan önce kategori, birim, tarih ve yetki sınırını kontrol ettirir.',
      guard:'Personel listesi yetki sınırıyla korunur; başka kullanıcıların puan veya kişi detayı gösterilmez.',
      questions:['Kategori kapsam hazırlığı ne işe yarar?','Kapsam dışı personeli nasıl kontrol ederim?','Bu ekranı dönem kapsamına nasıl bağlarım?'],
      links:[['Kategori Dönem Kapsamı','/performance/v2-1-5-category-period-scope'],['Kategori Dönem Entegrasyonu','/performance/v2-1-6-category-period-integration']]
    },
    {
      id:'performance-category-period',
      test:function(p){return /\/performance\/v2-1-5-category-period-scope|category-period-scope/i.test(p);},
      module:'Performans Yönetimi', screen:'Kategori Dönem Kapsamı', icon:'fa-calendar-check',
      summary:'Belirli kategori veya grup için açılacak performans döneminin gerçek kapsamını yönetir.',
      ai:'Çakışan dönem, boş kategori, eksik amir ve yanlış görev üretimi ihtimallerini kontrol listesine alır.',
      action:'Dönem, kategori ve görev üretimi öncesi hangi kontrolün yapılacağını adım adım anlatır.',
      guard:'Kapsam analizi karar değildir; görev üretimi ve yayın insan/onay süreciyle yürür.',
      questions:['Kategoriye özel dönem nasıl bağlanır?','Aynı tarih aralığında çakışma varsa ne yapmalıyım?','Görev üretmeden önce hangi AI kontrolünü yapayım?'],
      links:[['Kategori Dönem Entegrasyonu','/performance/v2-1-6-category-period-integration'],['Dönemler','/performance/periods']]
    },
    {
      id:'performance-category-integration',
      test:function(p){return /\/performance\/v2-1-6-category-period-integration|category-period-integration/i.test(p);},
      module:'Performans Yönetimi', screen:'Kategori Dönem Entegrasyonu', icon:'fa-link',
      summary:'Kategori kapsam planının gerçek performans dönemi ve görev üretimiyle tutarlı çalışmasını sağlar.',
      ai:'AI rehberi, görev üretimi öncesi eksik amir, sahte görev, kapsam dışı personel ve yayın riski uyarılarını görünür kılar.',
      action:'Kapsam planı → dönem bağlantısı → görev üretimi → yetki/görünürlük kontrol sırasını anlatır.',
      guard:'Otomatik değerlendirme veya puanlama yapmaz; yalnızca entegrasyon kontrol adımlarını açıklar.',
      questions:['Kategori dönem entegrasyonunda hangi sırayla ilerlemeliyim?','Görev üretimi öncesi eksik amir kontrolü nasıl yapılır?','Bu ekrandaki teknik riskleri nasıl sade kontrol ederim?'],
      links:[['Görev Üretimi','/performance/task-management'],['Süreç Takibi','/performance/process-tracking']]
    },
    {
      id:'performance-period-center',
      test:function(p){return /donem-yonetim-merkezi|dönem-yonetim-merkezi|period-management|\/performance\/periods|\/performans\/donem/i.test(p);},
      module:'Performans Yönetimi', screen:'Dönem Yönetimi', icon:'fa-calendar-days',
      summary:'Yıllık, 6 aylık, 3 aylık, aylık veya özel kapsamlı performans dönemlerini yönetir.',
      ai:'Dönem çakışması, kapsam tipi, kategori bağlantısı, görev üretimi ve yayın öncesi kontrol ihtiyacını hatırlatır.',
      action:'Yeni dönem oluşturma, kapsam seçme, aktiflik ve görev üretimi sırasını kullanıcıya adım adım anlatır.',
      guard:'Dönem açma yetkisi rol bazlıdır; asistan yetki dışı dönem açmaz veya veri değiştirmez.',
      questions:['Yeni performans dönemi nasıl açılır?','Sadece Güvenlik personeline özel dönem nasıl oluşturulur?','Dönem açtıktan sonra sıradaki adım ne?'],
      links:[['Dönemler','/performance/periods'],['Kategori Dönem Kapsamı','/performance/v2-1-5-category-period-scope']]
    },
    {
      id:'performance-approvals',
      test:function(p){return /president-approvals|baskan-onay|başkan-onay|personnel-support-publish-approvals|yayin-onay|yayın-onay/i.test(p);},
      module:'Performans Yönetimi', screen:'Onay ve Yayın Kontrolü', icon:'fa-user-check',
      summary:'70 altı sonuç, Başkan/Üst Onay ve Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı gibi kritik aşamaları görünür kılar.',
      ai:'Düşük performans, yayın kilidi, eksik süreç kaydı ve teknik statülerin sade Türkçeye çevrilmesi için dikkat notu üretir.',
      action:'Onay bekleyen kayıtları, karne incelemeyi, süreç geçmişini ve yayın kilidini doğru sırayla kontrol ettirir.',
      guard:'AI onay vermez, ret kararı üretmez ve personele sonucu otomatik açmaz.',
      questions:['70 altı sonuç neden Başkan onayına düşer?','Yayın ön onayı hangi aşamada yapılır?','Karne yayın kilidi nasıl kontrol edilir?'],
      links:[['Başkan Onayları','/performance/president-approvals'],['Yayın Ön Onayı','/performance/personnel-support-publish-approvals']]
    },
    {
      id:'performance-notes-guidance',
      test:function(p){return /interim-notes|donem-ici-not|feedback-aftercare|feedback-meeting-guide|feedback-followup|development|gelisim|gelişim|meeting-development/i.test(p);},
      module:'Performans Yönetimi', screen:'Dönem İçi Not ve Gelişim Rehberi', icon:'fa-seedling',
      summary:'Dönem içi gözlem, gelişim ihtiyacı, görüşme sonrası not ve eylem planı takibi için kullanılır.',
      ai:'Olumlu/olumsuz gözlem, tekrar eden gelişim ihtiyacı ve takip notlarını karar değil rehber bilgi olarak düzenler.',
      action:'Not türü, personel, dönem, açıklama ve takip adımı sırasını anlatır.',
      guard:'Dönem içi not otomatik puan üretmez; nihai değerlendirme insan ve süreç onayıyla oluşur.',
      questions:['Dönem içi not nasıl eklenir?','Gelişim önerisi puanı etkiler mi?','Görüşme sonrası eylem planını nasıl takip ederim?'],
      links:[['Dönem İçi Notlar','/performance/interim-notes'],['Gelişim Rehberi','/performance/meeting-development/faz10']]
    },
    {
      id:'performance-general',
      test:function(p){return /\/performance|\/performans/i.test(p);},
      module:'Performans Yönetimi', screen:'Performans Ekranı', icon:'fa-chart-line',
      summary:'Dönem, kriter, görev, puanlama, karne, onay ve raporlama süreçlerini kurallı ve izlenebilir şekilde destekler.',
      ai:'Düşük/yüksek sonuç, açıklama eksikliği, geciken amir, kapsam ve görünürlük risklerine dikkat çeker.',
      action:'Kullanıcıya gerçek sol menü/sekme/buton adlarıyla işlem sırası anlatır.',
      guard:'Puan belirlemez; amir görüşü veya kişisel performans detayını yetkisiz göstermez.',
      questions:['Bu performans ekranında ne yapabilirim?','Yetkim yoksa hangi ayar kontrol edilmeli?','Karne neden personele görünmüyor?'],
      links:[['Performans Yönetimi','/performance/dashboard'],['AI Karar Destek','/ai/decision-support/faz1/health']]
    },
    {
      id:'personnel',
      test:function(p){return /\/personnel|\/personel|\/admin\/users|organization|leave|delegation|izin|vekalet|vekalet/i.test(p);},
      module:'Personel Yönetimi', screen:'Personel / Organizasyon Ekranı', icon:'fa-users-gear',
      summary:'Personel, sicil, birim, üst birim, yönetici, izin ve vekâlet kayıtlarının diğer modülleri doğru beslemesini sağlar.',
      ai:'Eksik sicil, yönetici bağlantısı, kategori, izin/vekâlet ve performans zinciri risklerini hatırlatır.',
      action:'Personel kaydı, organizasyon bağlantısı, izin ve vekâlet adımlarını sade sıraya koyar.',
      guard:'Kişisel veya hassas personel bilgisini kart üzerinde dökmez; yalnızca yetkili ekrana yönlendirir.',
      questions:['Personel eklerken hangi alanlar zorunlu?','Eksik yönetici performans zincirini nasıl etkiler?','İzinli amir varsa vekâlet nasıl kontrol edilir?'],
      links:[['Personel Listesi','/admin/users'],['Performans Yönetimi','/performance/dashboard']]
    },
    {
      id:'communication',
      test:function(p){return /\/messages|\/surveys|\/support|\/feedback|\/announcements|\/notifications|kurumsal-bilgilendirme|executive-summary|mail-center|\/portal/i.test(p);},
      module:'İletişim ve Anket Yönetimi', screen:'İletişim / Destek / Anket Ekranı', icon:'fa-comments',
      summary:'Mesaj, duyuru, bildirim, anket, geri bildirim, destek talebi ve kurumsal bilgilendirme süreçlerini kayıtlı ve izlenebilir şekilde destekler.',
      ai:'Bekleyen talep, düşük anket katılımı, yoğun destek konusu ve okunmamış kritik bildirimleri karar destek düzeyinde fark ettirir.',
      action:'Kullanıcıyı doğru mesaj, anket, destek veya bilgilendirme ekranına yönlendirir.',
      guard:'Mesaj metni, anket cevabı, destek açıklaması veya ek dosya içeriğini yetkisiz göstermez.',
      questions:['Bu iletişim ekranında sıradaki işlem ne?','Anket katılımı düşükse ne yapmalıyım?','Destek talebi yoğunluğu AI tarafından nasıl özetlenir?'],
      links:[['Yardım Merkezi','/support'],['Anketler','/surveys'],['Bildirimler','/notifications']]
    },
    {
      id:'settings',
      test:function(p){return /\/settings|role-matrix|system-settings|ayar|yetki|captcha|security/i.test(p + hash());},
      module:'Sistem Ayarları ve Yetkilendirme', screen:'Ayar / Yetki Ekranı', icon:'fa-sliders',
      summary:'Rol, kişi, birim, menü görünürlüğü, güvenlik ve modül ayarlarını merkezi kontrol altında tutar.',
      ai:'Yanlış görünürlük, yetkisiz erişim ve modül ayarı uyumsuzluğu risklerini kontrol listesi olarak gösterir.',
      action:'Rol matrisi, kişi bazlı görünürlük, modül ayarı ve sayfa erişim kontrolünü birlikte düşünmenizi sağlar.',
      guard:'Yetkiyi otomatik açmaz; değişiklik yetkili kullanıcı ve audit kayıt mantığıyla yapılır.',
      questions:['Bu menü neden görünmüyor?','Rol matrisi ile kişi bazlı yetki farkı nedir?','AI Karar Destek özetleri kimlere açılmalı?'],
      links:[['Rol Matrisi','/settings/role-matrix'],['Ayarlar','/settings']]
    },
    {
      id:'ai-decision',
      test:function(p){return /\/ai\/decision|\/admin\/ai|ai-decision|ai-center|analysis/i.test(p);},
      module:'AI Karar Destek Merkezi', screen:'AI Karar Destek Ekranı', icon:'fa-brain',
      summary:'BYS360 verilerini özet, dikkat notu, önceliklendirme ve risk farkındalığı çıktısına dönüştürür.',
      ai:'Performans, personel, anket, destek, bildirim ve raporlama verilerini güvenli karar destek notuna çevirir.',
      action:'Üretilen çıktının hangi veri türüne dayandığını ve insan kontrolü gerektirdiğini hatırlatır.',
      guard:'Nihai idari karar vermez; öneri ve özetler insan denetimine açıktır.',
      questions:['AI Karar Destek ile Asistan farkı nedir?','Bu analiz nihai karar sayılır mı?','Hassas veri maskeleme nasıl korunur?'],
      links:[['AI Karar Destek Merkezi','/ai/decision-support/faz1/health'],['Asistan Bilgi Bankası','/ai-agent/knowledge']]
    },
    {
      id:'assistant',
      test:function(p){return /\/ai-agent|assistant-training-bank|asistan/i.test(p);},
      module:'BYS360 Asistanı', screen:'Asistan ve Bilgi Bankası', icon:'fa-robot',
      summary:'Kullanıcıyı doğru ekrana yönlendiren, işlem adımlarını öğreten ve yetki kontrollü özet sunan dijital yardımcı katmandır.',
      ai:'Gerçek ekran adları, güvenli menü haritası ve kurumsal cevap diliyle kullanıcıya rehberlik eder.',
      action:'Bilgi bankası ve ekran rehberlerini güncel tutmayı kolaylaştırır.',
      guard:'İdari karar, performans puanı veya hassas veri üretmez.',
      questions:['Asistan bilgi bankasına ne eklemeliyim?','Asistan hangi verileri gösteremez?','Yeni ekranı asistana nasıl öğretirim?'],
      links:[['Asistan Paneli','/ai-agent/panel'],['Asistan Bilgi Bankası','/ai-agent/knowledge']]
    },
    {
      id:'kpi',
      test:function(p){return /strategic-performance|kpi|hedef|target|goal/i.test(p);},
      module:'KPI ve Hedef Yönetimi', screen:'KPI / Hedef Ekranı', icon:'fa-bullseye',
      summary:'Kurumsal, birim veya personel hedeflerinin dönem, ağırlık, gerçekleşme ve risk seviyesine göre izlenmesini destekler.',
      ai:'Riskli KPI, geciken hedef, düşük gerçekleşme ve hedef-performans bağlantısı konusunda özet/dikkat notu üretir.',
      action:'Hedef dönemi, hedef kartı, gerçekleşen değer ve dashboard kontrol sırasını anlatır.',
      guard:'Hedef sonucunu idari karar gibi yorumlamaz; karar yetkili yöneticiye aittir.',
      questions:['KPI hedef kartı nasıl oluşturulur?','Riskli hedef neye göre görünür?','KPI ile performans bağlantısı nasıl kurulmalı?'],
      links:[['KPI Dashboard','/strategic-performance/dashboard'],['AI KPI Analizi','/strategic-performance/ai-kpi-analysis']]
    },
    {
      id:'dashboard',
      test:function(p){return /\/dashboard|\/home|\/main|\/reports|rapor/i.test(p);},
      module:'Dashboard ve Raporlar', screen:'Dashboard / Rapor Ekranı', icon:'fa-gauge-high',
      summary:'Yönetici görünürlüğü, özet kartları, risk alanları, raporlar ve süreç yoğunluklarını tek bakışta destekler.',
      ai:'Olağan dışı dağılım, geciken süreç, destek yoğunluğu, performans riski ve rapor özetini görünür kılar.',
      action:'Hangi kartın neyi anlattığını ve hangi detay ekrana gidileceğini açıklar.',
      guard:'Rapor özeti yetki sınırına bağlıdır; kişi/hassas detay kart üzerinde açılmaz.',
      questions:['Bu dashboardda hangi karta önce bakmalıyım?','Riskli alanları nasıl yorumlamalıyım?','Raporu AI ile nasıl özetletirim?'],
      links:[['AI Karar Destek','/ai/decision-support/faz1/health']]
    }
  ];

  var DEFAULT_RULE = {
    id:'default', module:'BYS360', screen:'AI Destekli Ekran', icon:'fa-wand-magic-sparkles',
    summary:'Bu ekran BYS360 genel AI rehber katmanına bağlandı. Asistan ekranın amacı, yetki sınırı, güvenli işlem sırası ve ilgili modül bağlantıları konusunda destek verir.',
    ai:'Ekran amacını, olası işlem sırasını ve dikkat edilmesi gereken güvenli sınırı açıklar.',
    action:'Sorunuzu günlük dille yazdığınızda sizi doğru BYS360 ekranına yönlendirir.',
    guard:'İdari karar vermez, performans puanı belirlemez ve hassas veri göstermez.',
    questions:['Bu ekranda ne yapabilirim?','Bu işlem için hangi yetki gerekir?','Sıradaki güvenli kontrol adımı ne?'],
    links:[['BYS360 Asistanı','/ai-agent/panel'],['AI Karar Destek','/ai/decision-support/faz1/health']]
  };

  function getRule(){
    var p = path();
    for(var i=0;i<RULES.length;i++){
      try{ if(RULES[i].test(p)) return RULES[i]; }catch(e){}
    }
    return DEFAULT_RULE;
  }

  function findAssistantRoot(){
    return document.querySelector('#bys360-assistant-module-root, [data-bys360-assistant-module], #bys360-ai-agent-widget-root');
  }

  function openAssistant(question){
    var q = question || 'Bu ekranda ne yapabilirim?';
    try{
      if(window.BYS360AssistantModule && typeof window.BYS360AssistantModule.open === 'function'){
        window.BYS360AssistantModule.open();
      }else{
        var launcher = document.querySelector('#bys360-assistant-module-root .bys360-am-launcher, .bys360-am-launcher, [data-ai-agent-launcher], .bys360-ai-agent-launcher');
        if(launcher){ launcher.click(); }
      }
    }catch(e){}

    var tries = 0;
    function send(){
      tries += 1;
      try{
        var root = findAssistantRoot();
        if(window.BYS360AssistantModule && typeof window.BYS360AssistantModule.open === 'function'){
          window.BYS360AssistantModule.open();
        }
        if(root){
          var chatTab = root.querySelector('[data-view="chat"], [data-agent-tab="chat"]');
          if(chatTab && !chatTab.classList.contains('is-active')) chatTab.click();
        }
        var input = root ? root.querySelector('[data-chat-input], [data-agent-input], textarea, input[type="text"]') : document.querySelector('[data-chat-input], [data-agent-input]');
        var form = root ? root.querySelector('[data-chat-form], [data-agent-form], form') : document.querySelector('[data-chat-form], [data-agent-form]');
        if(input){
          input.value = q;
          input.dispatchEvent(new Event('input',{bubbles:true}));
          input.focus();
          if(form){
            form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
          }
          return true;
        }
      }catch(e){}
      if(tries < 10) window.setTimeout(send, 160);
      return false;
    }
    window.setTimeout(send, 120);
    return true;
  }

  function answerForQuestion(rule, question){
    var q = trim(question || 'Bu ekranda ne yapabilirim?');
    var lowerQ = lower(q);
    var parts = [];
    parts.push('Bu ekran: ' + (rule.screen || pageTitle()) + '.');
    parts.push('Modül: ' + (rule.module || 'BYS360') + '.');
    if(/yetki|kim yapabilir|kimler|izin/.test(lowerQ)){
      parts.push('Bu işlemde önce rol/menü görünürlüğü ve backend erişim yetkisi birlikte kontrol edilmelidir. Yetkiniz yoksa menü görünmeyebilir veya bağlantıyı yazsanız bile veri açılmamalıdır.');
    }else if(/sıradaki|siradaki|ne yap|nasıl|nasil|adım|adim/.test(lowerQ)){
      parts.push(rule.action || DEFAULT_RULE.action);
    }else if(/risk|dikkat|hata|kontrol/.test(lowerQ)){
      parts.push(rule.ai || DEFAULT_RULE.ai);
    }else{
      parts.push(rule.summary || DEFAULT_RULE.summary);
      parts.push(rule.action || DEFAULT_RULE.action);
    }
    parts.push('Güvenli sınır: ' + (rule.guard || DEFAULT_RULE.guard));
    return parts.join(' ');
  }

  function renderInlineAnswer(rule, question, openedAssistant){
    var card = document.getElementById(CARD_ID);
    if(!card) return;
    var box = card.querySelector('[data-ai-everywhere-answer]');
    if(!box) return;
    var links = renderLinks(rule.links || DEFAULT_RULE.links);
    box.hidden = false;
    box.innerHTML = ''+
      '<div class="bys360-ai-everywhere-answer-head"><strong><i class="fa-solid fa-wand-magic-sparkles"></i> Rehber cevabı</strong><span>' + (openedAssistant ? 'Asistan paneline de aktarıldı' : 'Kart içinde çalışıyor') + '</span></div>'+
      '<p><b>Soru:</b> '+ escapeHtml(question || 'Bu ekranda ne yapabilirim?') +'</p>'+
      '<p>'+ escapeHtml(answerForQuestion(rule, question)) +'</p>'+
      links;
  }

  function addTitleBadge(){
    var title = document.querySelector('.page-title, .content-block h1, h1');
    if(!title || title.querySelector('.bys360-ai-screen-supported-badge')) return;
    var badge = document.createElement('span');
    badge.className = 'bys360-ai-screen-supported-badge';
    badge.innerHTML = '<i class="fa-solid fa-sparkles"></i> AI destekli';
    title.appendChild(badge);
  }

  function findMount(){
    return document.querySelector('#contentWrap .content-block') || document.querySelector('#contentWrap') || document.querySelector('main.content-wrap') || document.querySelector('main');
  }

  function shouldSkip(){
    var p = path();
    if(/\/login|\/logout|\/static|\/api\/|\/health|\/favicon/.test(p)) return true;
    if(document.getElementById(CARD_ID)) return true;
    return false;
  }

  function renderLinks(links){
    if(!links || !links.length) return '';
    return '<div class="bys360-ai-everywhere-links">' + links.slice(0,4).map(function(item){
      var title = Array.isArray(item) ? item[0] : item.title;
      var href = Array.isArray(item) ? item[1] : item.href;
      return '<a class="bys360-ai-everywhere-link" href="' + escapeHtml(href || '#') + '"><i class="fa-solid fa-arrow-up-right-from-square"></i>' + escapeHtml(title || 'Ekrana git') + '</a>';
    }).join('') + '</div>';
  }

  /* BYS360_AI_GUIDE_FORCE_COLLAPSED_V3 */
  function ensureAiGuideCollapsedStyleV3(){
    var styleId = 'bys360-ai-guide-force-collapsed-v3';

    if(document.getElementById(styleId)) return;

    var style = document.createElement('style');
    style.id = styleId;

    style.textContent = ''
      + '.bys360-ai-everywhere[data-collapsed="true"]{'
      + 'margin:0 0 .75rem 0!important;'
      + 'min-height:0!important;'
      + '}'

      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-inner{'
      + 'padding:.6rem .85rem!important;'
      + '}'

      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-head{'
      + 'display:flex!important;'
      + 'align-items:center!important;'
      + 'justify-content:space-between!important;'
      + 'gap:.75rem!important;'
      + 'margin:0!important;'
      + '}'

      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-titlebox{'
      + 'min-width:0!important;'
      + 'margin:0!important;'
      + '}'

      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-kicker{'
      + 'display:block!important;'
      + 'margin:0!important;'
      + 'white-space:nowrap!important;'
      + 'overflow:hidden!important;'
      + 'text-overflow:ellipsis!important;'
      + '}'

      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-titlebox h2,'
      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-titlebox p,'
      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-grid,'
      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-questions,'
      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-answer,'
      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-links,'
      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '[data-ai-everywhere-ask]{'
      + 'display:none!important;'
      + '}'

      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '.bys360-ai-everywhere-actions{'
      + 'display:flex!important;'
      + 'margin:0!important;'
      + 'flex:0 0 auto!important;'
      + '}'

      + '.bys360-ai-everywhere[data-collapsed="true"] '
      + '[data-ai-everywhere-toggle]{'
      + 'display:inline-flex!important;'
      + 'margin:0!important;'
      + 'padding:.38rem .7rem!important;'
      + '}';

    document.head.appendChild(style);
  }

  function render(){
    ensureAiGuideCollapsedStyleV3();
    if(shouldSkip()) return;
    var mount = findMount();
    if(!mount) return;
    var rule = getRule();
    var displayTitle = rule.screen || pageTitle();
    var collapsed = true;
    var card = document.createElement('section');
    card.id = CARD_ID;
    card.className = 'bys360-ai-everywhere';
    card.setAttribute('data-bys360-ai-everywhere', VERSION);
    card.setAttribute('data-module', rule.module || 'BYS360');
    card.setAttribute('data-screen-rule', rule.id || 'default');
    card.setAttribute('aria-label','AI destekli ekran rehberi');
    card.setAttribute('data-collapsed','true');
    card.innerHTML = ''+
      '<div class="bys360-ai-everywhere-inner">'+
        '<div class="bys360-ai-everywhere-head">'+
          '<div class="bys360-ai-everywhere-titlebox">'+
            '<span class="bys360-ai-everywhere-kicker"><i class="fa-solid '+ escapeHtml(rule.icon || 'fa-sparkles') +'"></i> AI destekli ekran rehberi · '+ escapeHtml(rule.module || 'BYS360') +'</span>'+
            '<h2>'+ escapeHtml(displayTitle) +'</h2>'+
            '<p>'+ escapeHtml(rule.summary || DEFAULT_RULE.summary) +'</p>'+
          '</div>'+
          '<div class="bys360-ai-everywhere-actions">'+
            '<button type="button" class="bys360-ai-everywhere-btn" data-ai-everywhere-ask="'+ escapeHtml((rule.questions && rule.questions[0]) || 'Bu ekranda ne yapabilirim?') +'"><i class="fa-solid fa-comments"></i> Asistana sor</button>'+
            '<button type="button" class="bys360-ai-everywhere-btn secondary" data-ai-everywhere-toggle><i class="fa-solid fa-chevron-up"></i> '+ (collapsed ? 'Aç' : 'Daralt') +'</button>'+
          '</div>'+
        '</div>'+
        '<div class="bys360-ai-everywhere-grid">'+
          '<article class="bys360-ai-everywhere-card"><strong><i class="fa-solid fa-brain"></i> AI desteği</strong><span>'+ escapeHtml(rule.ai || DEFAULT_RULE.ai) +'</span></article>'+
          '<article class="bys360-ai-everywhere-card"><strong><i class="fa-solid fa-list-check"></i> İşlem rehberi</strong><span>'+ escapeHtml(rule.action || DEFAULT_RULE.action) +'</span></article>'+
          '<article class="bys360-ai-everywhere-card"><strong><i class="fa-solid fa-shield-halved"></i> Güvenli sınır</strong><span>'+ escapeHtml(rule.guard || DEFAULT_RULE.guard) +'</span></article>'+
        '</div>'+
        '<div class="bys360-ai-everywhere-questions">'+
          (rule.questions || DEFAULT_RULE.questions).slice(0,4).map(function(q){return '<button type="button" class="bys360-ai-everywhere-question" data-ai-everywhere-ask="'+ escapeHtml(q) +'">'+ escapeHtml(q) +'</button>';}).join('')+
        '</div>'+ '<div class="bys360-ai-everywhere-answer" data-ai-everywhere-answer hidden></div>' + renderLinks(rule.links || DEFAULT_RULE.links) +
      '</div>';
    var first = mount.firstElementChild;
    mount.insertBefore(card, first || null);
    addTitleBadge();
    document.documentElement.setAttribute('data-bys360-ai-everywhere','v1');
  }

  document.addEventListener('click', function(ev){
    var ask = ev.target && ev.target.closest ? ev.target.closest('[data-ai-everywhere-ask]') : null;
    if(ask){
      ev.preventDefault();
      var question = ask.getAttribute('data-ai-everywhere-ask') || 'Bu ekranda ne yapabilirim?';
      var rule = getRule();
      var opened = openAssistant(question);
      renderInlineAnswer(rule, question, opened);
      return;
    }
    var toggle = ev.target && ev.target.closest ? ev.target.closest('[data-ai-everywhere-toggle]') : null;
    if(toggle){
      ev.preventDefault();
      var card = document.getElementById(CARD_ID);
      if(!card) return;
      var collapsed = card.getAttribute('data-collapsed') === 'true';
      if(collapsed){ card.removeAttribute('data-collapsed'); toggle.setAttribute('aria-expanded','true'); toggle.innerHTML = '<i class="fa-solid fa-chevron-up"></i> Daralt'; }
      else{ card.setAttribute('data-collapsed','true'); toggle.innerHTML = '<i class="fa-solid fa-chevron-down"></i> Aç'; }
    }
  }, true);

  function boot(){
    render();
    window.setTimeout(render, 450);
    window.setTimeout(render, 1200);
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();
  window.addEventListener('pageshow', boot);
  window.BYS360AIEverywhereV2 = {version:VERSION, getRule:getRule, openAssistant:openAssistant, render:render, answerForQuestion:answerForQuestion};
})();
