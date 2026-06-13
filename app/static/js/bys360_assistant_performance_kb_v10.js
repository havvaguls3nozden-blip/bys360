
/* BYS360 Asistani Modulu - Performance Management Full Knowledge Base V10
   Canonical module extension. Does not restore legacy simple assistants. */
(function(){
  'use strict';
  const VERSION = 'V10_PERFORMANCE_KB';
  const CANONICAL_NAME = 'BYS360 Asistanı';
  const MODULE_TITLE = 'BYS360 Asistanı — Kurumsal Rehberlik, Akıllı Yönlendirme ve Yetki Kontrollü Dijital Yardımcı';

  const safeRoute = (label, href) => ({ label, href });
  const ROUTES = {
    periods: safeRoute('Performans Yönetimi > Dönemler', '/performance/periods'),
    criteria: safeRoute('Performans Yönetimi > Değerlendirme Kriterleri', '/performance/criteria'),
    weights: safeRoute('Performans Yönetimi > Ağırlıklar', '/performance/weights'),
    assignment: safeRoute('Performans Yönetimi > Görev Üretimi', '/performance/assignments'),
    myTasks: safeRoute('Performans Yönetimi > Değerlendirme Görevlerim', '/performance/my-evaluations'),
    scorecard: safeRoute('Performans Yönetimi > Karne', '/performance/scorecards'),
    publish: safeRoute('Performans Yönetimi > Yayın Süreci', '/performance/publish'),
    president: safeRoute('Performans Yönetimi > Başkan Onayları', '/performance/president-approvals'),
    archive: safeRoute('Performans Yönetimi > Geçmiş Karne Arşivi', '/performans/gecmis-karne-arsivi'),
    notes: safeRoute('Performans Yönetimi > Dönem İçi Notlar', '/performance/in-period-notes'),
    development: safeRoute('Performans Yönetimi > Gelişim Önerileri', '/performance/development-suggestions'),
    reports: safeRoute('Performans Yönetimi > Raporlar', '/performance/reports'),
    dashboard: safeRoute('Performans Yönetimi > Yönetici Dashboard', '/performance/dashboard'),
    delays: safeRoute('Performans Yönetimi > Hatırlatma ve Aksatan Amirler', '/performance/meeting-development/faz9')
  };

  const forbiddenPhrases = [
    'Dönem Yönetimi', 'süreç eşleşmesi', 'süreç durumu', 'yetki kapsamı',
    'scorecard_pending', 'president_pending', 'blocked_president_pending'
  ];

  const normalize = (s) => (s || '').toLocaleLowerCase('tr-TR')
    .replace(/[ı]/g,'i').replace(/[ğ]/g,'g').replace(/[ü]/g,'u').replace(/[ş]/g,'s').replace(/[ö]/g,'o').replace(/[ç]/g,'c');

  function routeLine(route){
    return route ? `Doğru ekran: ${route.label}` : '';
  }

  const answers = [
    {
      id: 'performance_overview_v10',
      patterns: ['performans nasıl çalışır','performans yönetimi nasıl çalışır','performans modülü','performans yönetimi nedir','performans süreci'],
      answer: `Anladım. Bu konu Performans Yönetimi içindedir.\n\nPerformans Yönetimi, personelin belirlenen dönem, değerlendirme kriterleri, amir zinciri, puanlama, açıklama, onay ve yayın kurallarına göre değerlendirilmesini sağlar.\n\nDoğru kullanım sırası:\n1. Performans Yönetimi > Dönemler ekranında dönem oluşturulur.\n2. Değerlendirme Kriterleri kontrol edilir.\n3. Ağırlıklar ve 3. amir modu kontrol edilir.\n4. Personel, birim, kategori, izin ve vekâlet bilgileri doğrulanır.\n5. Görev Üretimi ekranında değerlendirme görevleri oluşturulur.\n6. Amirler Değerlendirme Görevlerim alanından puanlama ve görüş girişlerini tamamlar.\n7. Sistem nihai puanı, açıklama zorunluluklarını ve onay ihtiyacını hesaplar.\n8. 70 altı sonuç varsa Başkan Onayları süreci çalışır.\n9. Gerekli onaylar tamamlandıktan sonra yayın süreci yürütülür.\n10. Yayından sonra personel kendi karnesini, yetkili kullanıcılar ise kapsamları dahilindeki raporları görebilir.\n\nDikkat:\n- Kör değerlendirme yapılmaz; sonraki amir önceki değerlendirmeyi görebilir.\n- Personel sonucu yayınlanmadan göremez.\n- Asistan puan belirlemez, yalnızca süreci anlatır.`
    },
    {
      id: 'periods_v10',
      patterns: ['dönemler nerede','donemler nerede','dönem açacağım','donem acacagim','performans dönemi oluştur','yeni dönem oluştur','2026 performans dönemi','güvenlik için dönem','temizlik için dönem'],
      answer: `Anladım. Bu işlem Performans Yönetimi içindedir.\n\n${routeLine(ROUTES.periods)}\n\nKim yapabilir?\n- Admin\n- Sistem Yöneticisi\n- Performans Yetkilisi\n- Yetki verilmiş İK/personel kullanıcısı\n\nAdım adım:\n1. Sol şeritten Performans Yönetimi bölümüne girin.\n2. Dönemler sekmesini açın.\n3. Yeni Dönem Oluştur / Yeni Dönem Ekle butonuna basın.\n4. Dönem adını, dönem türünü, başlangıç ve bitiş tarihini girin.\n5. Kapsam tipini seçin: tüm kurum, birim, üst birim, kategori/grup veya seçili personel.\n6. Kapsama göre ilgili birim, kategori ya da personelleri seçin.\n7. Kaydedin.\n8. Sonra Değerlendirme Kriterleri, Ağırlıklar ve Görev Üretimi adımlarını kontrol edin.\n\nDikkat:\n- Kullanıcıya görünen doğru sekme adı Dönemlerdir.\n- Aynı personel için aynı tarih aralığında çakışan dönem varsa sistem uyarı vermelidir.\n- Dönem oluşturmak tek başına puanlamayı başlatmaz; görev üretimi de yapılmalıdır.`
    },
    {
      id: 'criteria_v10',
      patterns: ['değerlendirme kriterleri','kriter ekleme','performans kriteri','kriter nasıl eklenir','yetkinlik mi kriter mi'],
      answer: `Bu işlem Performans Yönetimi > Değerlendirme Kriterleri alanından yapılır.\n\nKim yapabilir?\n- Admin\n- Sistem Yöneticisi\n- Performans Yetkilisi\n\nAdım adım:\n1. Performans Yönetimi bölümüne girin.\n2. Değerlendirme Kriterleri sekmesini açın.\n3. Yeni Kriter Ekle butonuna basın.\n4. Kriter adını ve açıklamasını girin.\n5. Aktiflik durumunu belirleyin.\n6. Gerekliyse dönem, kategori veya rol bağlantısını seçin.\n7. Kaydedin.\n\nDikkat:\n- BYS360 ekran dilinde ana ifade Değerlendirme Kriterleridir.\n- Kullanıcı ekranlarında ana terim olarak Yetkinlik ifadesi kullanılmamalıdır.\n- Kriter değişiklikleri aktif dönemleri etkileyebileceği için dönem başlamadan kontrol edilmelidir.`
    },
    {
      id: 'weights_v10',
      patterns: ['ağırlık','agirlik','puan ağırlığı','amir ağırlığı','3. amir ağırlık','üçüncü amir ağırlık'],
      answer: `Ağırlık ayarları, amirlerin nihai puana katkısını belirler.\n\nDoğru ekran: Performans Yönetimi > Ağırlıklar\n\nAdım adım:\n1. Performans Yönetimi bölümünden Ağırlıklar alanına girin.\n2. Dönem veya rol/kapsam seçimini yapın.\n3. 1. amir, 2. amir ve varsa 3. amir ağırlıklarını kontrol edin.\n4. Toplam ağırlığın %100 olduğundan emin olun.\n5. Kaydedin.\n\nDikkat:\n- 3. amir yorum modundaysa puana etkisi olmamalıdır.\n- 3. amir puan modundaysa ağırlık toplamı yine %100 kalmalıdır.\n- Yanlış ağırlık nihai puanı etkileyebilir; yayın öncesi mutlaka kontrol edilmelidir.`
    },
    {
      id: 'assignment_v10',
      patterns: ['görev üretimi','gorev uretimi','görevleri oluştur','değerlendirme görevi oluşmadı','amir görevi oluşmadı','görev üret'],
      answer: `Bu işlem Performans Yönetimi > Görev Üretimi alanından yapılır.\n\nAdım adım:\n1. Performans Yönetimi bölümüne girin.\n2. Görev Üretimi ekranını açın.\n3. İlgili dönemi seçin.\n4. Kapsamı kontrol edin: tüm kurum, birim, kategori veya seçili personel.\n5. Personel, birim, üst birim, yönetici, izin ve vekâlet bilgilerinin doğru olduğundan emin olun.\n6. Görevleri Oluştur butonuna basın.\n7. Oluşan görev listesini kontrol edin.\n\nDikkat:\n- Eksik amir varsa önce Personel Yönetimi tarafındaki organizasyon/yönetici bilgisi düzeltilmelidir.\n- 3. amir olmayan kayıtta sahte 3. amir görevi oluşmamalıdır.\n- Hukuk Müşavirliği ve özel roller gibi istisnalar dikkate alınmalıdır.\n- İzinli amir varsa vekâlet ilişkisi süreci etkileyebilir.`
    },
    {
      id: 'evaluation_tasks_v10',
      patterns: ['değerlendirme görevlerim','puanlama nerede','puan gireceğim','amir değerlendirmesi','personeli puanlayacağım','değerlendirme yapacağım'],
      answer: `Puanlama işlemi Performans Yönetimi > Değerlendirme Görevlerim alanından yapılır.\n\nKim yapabilir?\n- Kendisine değerlendirme görevi atanmış amir/değerlendirici\n\nAdım adım:\n1. Performans Yönetimi bölümüne girin.\n2. Değerlendirme Görevlerim sekmesini açın.\n3. Değerlendireceğiniz personeli seçin.\n4. Değerlendirme Kriterleri için 1–5 arası puan girin.\n5. Gerekli açıklamaları ve genel görüşü yazın.\n6. Kaydet veya Tamamla butonuna basın.\n7. Görev durumunun tamamlandı olarak değiştiğini kontrol edin.\n\nDikkat:\n- Sistem kör değerlendirme yapmaz.\n- Sonraki amir, önceki amirin puanını ve görüşünü görebilir.\n- 1 ve 5 puan açıklama zorunluluğu sistem ayarına göre çalışır.\n- 70 altı ve 90 üstü sonuçlarda ayrıntılı genel görüş gerekebilir.`
    },
    {
      id: 'scorecard_v10',
      patterns: ['karne','performans karnesi','karnem nerede','personel karneyi göremiyor','karne görünmüyor','not karnesi'],
      answer: `Karne, değerlendirme sonucu yayınlandıktan sonra görünür hale gelir.\n\nDoğru ekran: Performans Yönetimi > Karne\n\nAdım adım kontrol:\n1. İlgili dönem için tüm değerlendirme görevleri tamamlandı mı kontrol edin.\n2. Açıklama zorunluluğu olan kayıtlar eksiksiz mi bakın.\n3. Nihai puan hesaplandı mı kontrol edin.\n4. 70 altı sonuç varsa Başkan Onayları sürecinin tamamlandığından emin olun.\n5. Gerekli yayın ön onayı tamamlandı mı kontrol edin.\n6. Admin/İK yetkilisi tarafından sonuç yayınlandı mı bakın.\n\nDikkat:\n- Personel kendi sonucunu süreç tamamlanmadan göremez.\n- Yayınlanmamış karne personelde görünmemelidir.\n- Karne ekranında teknik statü değil, Türkçe kurumsal durum ifadeleri görünmelidir.`
    },
    {
      id: 'president_approvals_v10',
      patterns: ['başkan onayları','baskan onaylari','başkan onayı','70 altı','düşük performans','başkan onayına düştü mü','yayın kilidi'],
      answer: `Başkan Onayları, 70 altı performans sonuçlarının doğrudan kesinleşmesini engelleyen üst onay sürecidir.\n\nDoğru ekran: Performans Yönetimi > Başkan Onayları\n\nKim görebilir?\n- Başkan\n- Admin / Sistem Yöneticisi\n- Yetkili performans/İK kullanıcıları, yetki kapsamına göre\n\nAdım adım süreç:\n1. Değerlendirme tamamlanır.\n2. Sistem nihai puanı hesaplar.\n3. Nihai puan 70 altındaysa sonuç doğrudan yayınlanmaz.\n4. Kayıt Başkan Onayları ekranına düşer.\n5. Başkan/üst onay incelemesi yapılır.\n6. Onay/ret veya iade süreci tamamlanır.\n7. Gerekli süreç kaydı oluşmadan karne personele açılmaz.\n\nDikkat:\n- 70 üstü kayda sahte Başkan onayı üretilmemelidir.\n- Başkan onayı bekleyen sonuç yayınlanmış sayılmaz.\n- Sistem otomatik idari işlem yapmazma yapmaz; yalnızca idari süreç akışı üretir.`
    },
    {
      id: 'third_supervisor_v10',
      patterns: ['3. amir','üçüncü amir','ucuncu amir','3 amir','yorum modu','puan modu','3. amir yok'],
      answer: `3. amir her personel için zorunlu değildir. Sadece organizasyon yapısında gerçekten ihtiyaç varsa kullanılır.\n\nÇalışma mantığı:\n1. 3. amir yoksa ekranda boş 3. amir görevi veya gereksiz bekleme statüsü oluşmamalıdır.\n2. 3. amir yorum modundaysa yalnızca görüş yazar; puana etkisi olmaz.\n3. 3. amir puan modundaysa ağırlık hesabına dahil olur.\n4. Çok seviyeli yapılarda işlem sırası genellikle varsa 3. amir, sonra 2. amir, en son 1. amir şeklindedir.\n\nDikkat:\n- 3. amir sütunu olmayan yapılarda ekran kalabalığı yaratmamalıdır.\n- Yorum modunda “puan bekliyor” değil, yorum/görüş bekliyor anlamına gelen ifade kullanılmalıdır.\n- Ağırlık toplamı her durumda %100 olmalıdır.`
    },
    {
      id: 'publish_v10',
      patterns: ['yayın süreci','yayınlama','karne yayınla','sonuç yayınla','personel sonucu görsün','yayın ön onayı'],
      answer: `Yayın süreci, performans sonucunun personele açılmadan önce son kez kontrol edildiği adımdır.\n\nDoğru ekran: Performans Yönetimi > Yayın Süreci\n\nAdım adım:\n1. Dönemdeki tüm değerlendirme görevlerinin tamamlandığını kontrol edin.\n2. Açıklama zorunluluğu olan kayıtları kontrol edin.\n3. 70 altı varsa Başkan Onayları sürecinin tamamlandığından emin olun.\n4. Yayın ön onayı gerekiyorsa Personel ve Destek Hizmetleri Grup Başkanı onayını kontrol edin.\n5. Admin/İK yetkilisi nihai yayını yapar.\n6. Yayından sonra personel kendi karnesini görebilir.\n\nDikkat:\n- Onayları tamamlanmamış karne yayınlanmamalıdır.\n- Yayın öncesi sonuç personel ekranına açılmamalıdır.\n- Yayın işlemi audit/log izleriyle kayıt altına alınmalıdır.`
    },
    {
      id: 'in_period_notes_v10',
      patterns: ['dönem içi not','donem ici not','ara geri bildirim','olumlu olay notu','olumsuz olay notu','performans notu'],
      answer: `Dönem İçi Notlar, performans dönemi boyunca gözlem, başarı, gelişim ihtiyacı veya önemli olayların kayıt altına alınmasını sağlar.\n\nDoğru ekran: Performans Yönetimi > Dönem İçi Notlar\n\nAdım adım:\n1. Performans Yönetimi bölümünden Dönem İçi Notlar alanına girin.\n2. İlgili personeli ve dönemi seçin.\n3. Not türünü belirleyin: olumlu gözlem, gelişim ihtiyacı, olay notu veya genel değerlendirme.\n4. Açıklamayı yazın.\n5. Kaydedin.\n\nDikkat:\n- Bu notlar otomatik puan üretmez.\n- Değerlendirme sırasında amire destek bilgi olarak kullanılabilir.\n- Yetki sınırına göre görünmelidir.`
    },
    {
      id: 'development_v10',
      patterns: ['gelişim önerisi','gelisim onerisi','gelişim rehberi','performans sonrası gelişim','düşük performans gelişim'],
      answer: `Gelişim Önerileri, performans sonucundan sonra personelin gelişim alanlarını daha düzenli takip etmek için kullanılır.\n\nDoğru ekran: Performans Yönetimi > Gelişim Önerileri\n\nAdım adım:\n1. İlgili dönem ve personel seçilir.\n2. Güçlü yönler, gelişim alanları ve önerilen takip adımları yazılır.\n3. Gerekirse eğitim, rehberlik veya görüşme önerisi eklenir.\n4. Kaydedilir ve yetki sınırına göre görüntülenir.\n\nDikkat:\n- Asistan gelişim önerisini idari karar gibi sunmaz.\n- Nihai değerlendirme ve karar yetkili amir/idari birimdedir.\n- Gelişim önerisi puanı otomatik değiştirmez.`
    },
    {
      id: 'archive_v10',
      patterns: ['geçmiş karne','gecmis karne','karne arşivi','puan arşivi','eski yıl puan','2024 puanı','2025 karnesi'],
      answer: `Geçmiş Karne Arşivi, eski dönem performans puanlarının ve karnelerinin yetki sınırına göre görüntülenmesini sağlar.\n\nDoğru ekran: Performans Yönetimi > Geçmiş Karne Arşivi\n\nAdım adım:\n1. Performans Yönetimi bölümünden Geçmiş Karne Arşivi alanına girin.\n2. Yıl, dönem veya personel filtresi kullanın.\n3. Yetkiniz dahilindeki kayıtları inceleyin.\n4. Personel yalnızca kendi geçmişini görmelidir.\n\nDikkat:\n- Eski puanlar manuel veya import ile alınmış olabilir.\n- Yetkisiz kullanıcı başka personelin detaylı karnesini görmemelidir.\n- Arşiv kayıtları kurumsal hafıza için korunur.`
    },
    {
      id: 'reports_v10',
      patterns: ['performans raporları','raporlar nerede','riskli personel analizi','aksatan amir','geciken amir','dönem tamamlama','birim ortalaması','kategori ortalaması','grup ortalaması'],
      answer: `Performans raporları, dönem, birim, kategori, amir ve personel bazlı görünürlük sağlar.\n\nDoğru ekran: Performans Yönetimi > Raporlar\n\nRaporlarda takip edilebilecek başlıklar:\n- Dönem tamamlanma durumu\n- Eksik değerlendirme görevleri\n- Aksatan/geciken amirler\n- Başkan onayı bekleyen düşük performans kayıtları\n- Yayın kilidi olan karneler\n- Birim, grup ve kategori ortalamaları\n- Riskli personel analizi\n- Düşük/yüksek performans yoğunluğu\n\nDikkat:\n- Başkan/Admin genel görünürlük alabilir.\n- Grup Başkanı ve Koordinatör yalnızca yetkili kapsamını görmelidir.\n- Personel kişi detayı içermeyen kendi grup/kategori ortalamasını görebilir.`
    },
    {
      id: 'performance_troubleshooting_v10',
      patterns: ['performans sorun','karne neden yok','görev neden oluşmadı','başkan onayı görünmüyor','puanlama açılmıyor','rapor açılmıyor','performans beyaz ekran'],
      answer: `Performans tarafında sorun varsa şu sırayla kontrol edin:\n\n1. Dönemler ekranında ilgili dönem aktif mi?\n2. Dönemin tarih aralığı ve kapsamı doğru mu?\n3. Değerlendirme Kriterleri aktif mi?\n4. Ağırlıklar toplamı %100 mü?\n5. Personel kaydında birim, üst birim, yönetici ve kategori bilgisi doğru mu?\n6. İzin veya vekâlet kaydı süreci etkiliyor mu?\n7. Görev Üretimi yapılmış mı?\n8. Değerlendirme görevleri tamamlanmış mı?\n9. Açıklama zorunluluğu olan alanlar eksiksiz mi?\n10. 70 altı varsa Başkan Onayları tamamlanmış mı?\n11. Yayın ön onayı ve nihai yayın yapılmış mı?\n12. Kullanıcının rol/menü yetkisi bu ekranı görmeye uygun mu?\n\nDikkat:\n- Beyaz ekran veya açılmayan sayfa varsa kullanıcıyı kırık linke yönlendirmemek gerekir.\n- Asistan yalnızca güvenli menü haritasındaki ekranlara yönlendirmelidir.`
    }
  ];

  function findAnswer(q){
    const nq = normalize(q);
    return answers.find(a => a.patterns.some(p => nq.includes(normalize(p))));
  }

  function sanitizeText(text){
    let out = String(text || '');
    out = out.replace(/Dönem Yönetimi/g, 'Dönemler');
    out = out.replace(/president_pending/g, 'Başkan Onayı Bekliyor');
    out = out.replace(/blocked_president_pending/g, 'Başkan Onayı Yayın Kilidi');
    out = out.replace(/hr_precheck/g, 'İK/Admin Ön Kontrolünde');
    out = out.replace(/süreç durumu/gi, 'süreç durumu');
    out = out.replace(/süreç eşleşmesi/gi, 'süreç eşleştirme');
    out = out.replace(new RegExp('authorized' + '_scope', 'gi'), 'yetki kapsamı');
    return out;
  }

  function install(){
    window.BYS360_ASSISTANT_PERFORMANCE_KB_V10 = {
      version: VERSION,
      title: MODULE_TITLE,
      routes: ROUTES,
      answers,
      findAnswer,
      sanitizeText,
      test(){
        const required = ['periods_v10','criteria_v10','assignment_v10','evaluation_tasks_v10','scorecard_v10','president_approvals_v10','third_supervisor_v10','publish_v10','reports_v10'];
        const ids = answers.map(a=>a.id);
        const missing = required.filter(x=>!ids.includes(x));
        const bad = answers.filter(a => forbiddenPhrases.some(p => a.answer.includes(p)));
        return { ok: missing.length===0 && bad.length===0, version: VERSION, missing, forbidden_in_answers: bad.map(a=>a.id), answer_count: answers.length };
      }
    };

    // Hook existing assistant local responder if present, without replacing canonical module.
    const hookNames = ['BYS360AssistantModule','BYS360AsistaniModulu','BYS360Assistant'];
    for (const name of hookNames){
      const obj = window[name];
      if (obj && !obj.__performanceKbV10){
        const originalAsk = obj.ask || obj.handleUserMessage || obj.respond;
        const localResponder = function(message){
          const found = findAnswer(message);
          if (found) return sanitizeText(found.answer);
          if (typeof originalAsk === 'function') return originalAsk.apply(this, arguments);
          return null;
        };
        if (!obj.ask) obj.ask = localResponder;
        if (!obj.handleUserMessage) obj.handleUserMessage = localResponder;
        obj.performanceKnowledgeV10 = window.BYS360_ASSISTANT_PERFORMANCE_KB_V10;
        obj.__performanceKbV10 = true;
      }
    }

    // Capture submit/click fallback for common widget input areas.
    document.addEventListener('submit', function(ev){ if (ev && ev.defaultPrevented) return;
      const form = ev.target;
      if (!form || !form.querySelector) return;
      const input = form.querySelector('input, textarea');
      if (!input) return;
      const found = findAnswer(input.value);
      if (!found) return;
      const root = form.closest('[id*="assistant"], [class*="assistant"], [id*="asistan"], [class*="asistan"]') || document.body;
      if (root){
        setTimeout(()=>{
          const area = root.querySelector('[data-bys360-assistant-messages], .bys360-assistant-messages, .assistant-messages, .messages');
          if (area && !area.textContent.includes(found.answer.slice(0,40))){
            const div = document.createElement('div');
            div.className = 'bys360-assistant-message bys360-assistant-message-bot bys360-v10-performance-answer';
            div.textContent = sanitizeText(found.answer);
            area.appendChild(div);
          }
        }, 50);
      }
    }, true);

    window.dispatchEvent(new CustomEvent('bys360:assistant:performance-kb-v10-ready', {detail: window.BYS360_ASSISTANT_PERFORMANCE_KB_V10}));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install); else install();
})();
