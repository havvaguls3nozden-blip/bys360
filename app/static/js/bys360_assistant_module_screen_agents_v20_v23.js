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
    return String(value == null ? '' : value).replace(/[&<>\"]/g, function (ch) {
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
      attention: ['Sahte görev veya null 3. amir bekleme durumu üretilmemelidir.']
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
    var best = null;
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
    return null;
  }

  function buildAnswer(screen) {
    if (!screen) return null;
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
    return null;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return null;
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
    var seen = Object.create(null);
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
        var style = window.getComputedStyle ? window.getComputedStyle(el) : null;
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
    var best = null;
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
    return null;
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
    return null;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return null;
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
    var seen = Object.create(null);
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
      var style = window.getComputedStyle ? window.getComputedStyle(el) : null;
      if (style && (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0')) return false;
      var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : null;
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
      var rawData = String(pattern || '');
      var n = norm(rawData);
      if (!n) return false;
      if (rawData.slice(-1) === '*') return p.indexOf(norm(rawData.slice(0, -1))) === 0;
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
      var rawData = String(pattern || '');
      var base = rawData.slice(-1) === '*' ? rawData.slice(0, -1) : rawData;
      var n = norm(base);
      if (!n) return;
      if (p === n) score += 1000;
      else if (rawData.slice(-1) === '*' && p.indexOf(n) === 0) score += 900;
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
    var best = null;
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
    return null;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return null;
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
    var seen = Object.create(null);
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
      var style = window.getComputedStyle ? window.getComputedStyle(el) : null;
      if (style && (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0')) return false;
      var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : null;
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
    { id:'assignments', screen:'Görev Üretimi ve Değerlendirme Görevleri', bölüm:'Performans Yönetimi', href:'/performance/assignments', paths:['/performance/assignments*','/performance/tasks*','/performans/gorev*','/performans/görev*'], keywords:['görev üretimi','değerlendirme görevi','atanan görev','amir zinciri','eksik amir'], family:'performance', description:'Bu ekran dönem kapsamındaki personel için gerçek amir zincirine göre değerlendirme görevlerinin üretilmesi ve takip edilmesi için kullanılır.', actions:['Dönemi ve kapsamı seçme','Eksik amir veya hatalı zincir kontrolü yapma','Görevleri üretme veya yeniden üretme','Bekleyen görevleri izleme'], attention:['Sahte görev veya null 3. amir beklemesi üretilmemelidir.'] },
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
      var rawData = String(pattern || '');
      var base = rawData.slice(-1) === '*' ? rawData.slice(0, -1) : rawData;
      var n = norm(base);
      if (!n) return;
      if (p === n) score += 1400;
      else if (rawData.slice(-1) === '*' && p.indexOf(n) === 0) score += 1250;
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

    // Çok olgun öncelik: Ana Sayfa yalnızca gerçek ana routenda kazanabilir.
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
    var family = null;
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
    var first = ranked[0] || null;
    var second = ranked[1] || null;
    if (!first || first.score < 85) {
      var generic = inferGenericScreen(facts, ranked);
      generic.confidence = 'düşük';
      generic.candidates = ranked.slice(0, 3).filter(function (x) { return x.score > 20; }).map(function (x) { return { screen: x.rule.screen, score: x.score }; });
      return generic;
    }
    var rule = Object.assign({}, first.rule);
    rule.score = first.score;
    rule.secondBest = second ? { screen: second.rule.screen, score: second.score } : null;
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
    return null;
  }

  var previousLocal = window.BYS360AssistantLocalAnswer;
  window.BYS360AssistantLocalAnswer = function (question) {
    var answer = answerQuestion(question);
    if (answer && answer.text) return answer.text;
    if (typeof previousLocal === 'function') return previousLocal(question);
    return null;
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
