/* BYS360 Asistani Modulu - Role / Reports / Communication / AI Full Knowledge Base V11
   Canonical extension. Does not restore legacy simple assistants. */
(function(){
  'use strict';
  const VERSION = 'V11_ROLE_REPORT_SUPPORT_AI_KB';
  const MODULE_TITLE = 'BYS360 Asistanı — Kurumsal Rehberlik, Akıllı Yönlendirme ve Yetki Kontrollü Dijital Yardımcı';
  const safeRoute = (label, href) => ({ label, href });
  const ROUTES = {
    moduleRoleMatrix: safeRoute('Sistem Ayarları > Modül Bazlı Rol Matrisi', '/settings/module-role-matrix'),
    performanceRoleMatrix: safeRoute('Sistem Ayarları > Performans Yönetimi Rol Matrisi', '/settings/performance-role-matrix'),
    userPermissions: safeRoute('Sistem Ayarları > Kullanıcı Yetkileri', '/settings/user-permissions'),
    unitProfiles: safeRoute('Sistem Ayarları > Birim Bazlı Menü Profilleri', '/settings/unit-menu-profiles'),
    systemSettings: safeRoute('Sistem Ayarları', '/settings'),
    performanceReports: safeRoute('Performans Yönetimi > Raporlar', '/performance/reports'),
    performanceDashboard: safeRoute('Performans Yönetimi > Yönetici Dashboard', '/performance/dashboard'),
    processTracking: safeRoute('Performans Yönetimi > Süreç Takibi', '/performance/process-tracking'),
    processReports: safeRoute('Performans Yönetimi > Süreç Raporları', '/performance/process-reports'),
    presidentApprovals: safeRoute('Performans Yönetimi > Başkan Onayları', '/performance/president-approvals'),
    support: safeRoute('İletişim ve Anket > Destek Talepleri', '/support'),
    surveys: safeRoute('İletişim ve Anket > Anketler', '/surveys'),
    notifications: safeRoute('Genel > Bildirimler', '/notifications'),
    messages: safeRoute('İletişim ve Anket > Mesajlaşma', '/messages'),
    announcements: safeRoute('İletişim ve Anket > Duyurular', '/announcements'),
    aiDecision: safeRoute('AI Karar Destek Merkezi', '/ai/decision-support')
  };
  const forbiddenPhrases = ['Dönem Yönetimi','end' + 'point yolu','çaylar sıcak','Kış kendini göstermiş','sevimli yorum','tanılama','örnek kayıt','iş planı','süreç eşleşmesi','süreç durumu'];
  const normalize = (s) => (s || '').toLocaleLowerCase('tr-TR')
    .replace(/[ı]/g,'i').replace(/[ğ]/g,'g').replace(/[ü]/g,'u').replace(/[ş]/g,'s').replace(/[ö]/g,'o').replace(/[ç]/g,'c');
  const routeLine = (route) => route ? `Doğru ekran: ${route.label}` : '';
  const answers = [
    {
      id:'role_matrix_overview_v11',
      patterns:['rol matrisi nasıl çalışır','rol matrisi nedir','yetki nasıl çalışır','menü görünürlüğü','menu gorunurlugu','yetkilendirme nasıl çalışır'],
      answer:`Anladım. Bu konu Sistem Ayarları ve Yetkilendirme alanındadır.\n\nBYS360’da rol matrisi, kullanıcıların hangi modülü, sekmeyi ve işlemi görebileceğini belirleyen merkezi kontrol yapısıdır.\n\nDoğru ekranlar:\n- Sistem Ayarları > Modül Bazlı Rol Matrisi\n- Sistem Ayarları > Performans Yönetimi Rol Matrisi\n- Sistem Ayarları > Kullanıcı Yetkileri\n- Sistem Ayarları > Birim Bazlı Menü Profilleri\n\nKim yapabilir?\n- Admin\n- Sistem Yöneticisi\n- Yetki verilmiş ayar/yetki yöneticisi\n\nAdım adım:\n1. Sistem Ayarları bölümüne girin.\n2. İlgili rol matrisi ekranını açın.\n3. Rolü seçin.\n4. Görünmesi gereken modül ve sekmeleri açın.\n5. Görünmemesi gereken alanları kapatın.\n6. Kaydedin.\n7. Kullanıcı bazlı özel yetki varsa ayrıca Kullanıcı Yetkileri alanını kontrol edin.\n8. Birim bazlı farklılık varsa Birim Bazlı Menü Profilleri alanını kontrol edin.\n\nDikkat:\n- Menüde görünmemesi gereken alan kullanıcıya hiç görünmemelidir.\n- Sadece tıklayınca erişim engeli vermek yeterli değildir.\n- Backend route yetkisi de ayrıca korunmalıdır.\n\nKontrol:\n- İlgili kullanıcıyla çıkış/giriş yapıp menünün gerçekten değiştiğini kontrol edin.`
    },
    {
      id:'menu_missing_v11',
      patterns:['menü görünmüyor','menu gorunmuyor','menüm yok','sekme görünmüyor','modül görünmüyor','açtım ama görünmüyor','rol matrisi açtım görünmüyor'],
      answer:`Menü görünmüyorsa yalnızca rol matrisi değil, birkaç katman birlikte kontrol edilmelidir.\n\nKontrol sırası:\n1. Sistem Ayarları > Modül Bazlı Rol Matrisi ekranında ilgili rol için modül açık mı?\n2. Performans alanıysa Sistem Ayarları > Performans Yönetimi Rol Matrisi kontrol edildi mi?\n3. Kullanıcıya kişi bazlı özel menü kapatma uygulanmış mı?\n4. Kullanıcının bağlı olduğu birim için Birim Bazlı Menü Profili farklı mı?\n5. Kullanıcı aktif mi ve doğru role bağlı mı?\n6. Kullanıcı çıkış yapıp tekrar giriş yaptı mı?\n7. Ekran cache nedeniyle eski menüyü gösteriyor olabilir; Ctrl + F5 yapılmalı.\n\nDikkat:\n- Menü kapalıysa kullanıcı sol şeritte o sekmeyi görmemelidir.\n- URL elle yazıldığında da veri göstermemelidir.\n- Beyaz sayfa yerine kurumsal “Bu sayfaya erişim yetkiniz bulunmamaktadır.” ekranı gösterilmelidir.`
    },
    {
      id:'role_difference_v11',
      patterns:['başkan ne görür','baskan ne gorur','admin ne görür','grup başkanı ne görür','koordinatör ne görür','personel ne görür','rol farkları'],
      answer:`BYS360’da görünürlük role, birime, kişiye özel yetkiye ve menü profiline göre belirlenir.\n\nGenel mantık:\n- Başkan / Üst Yönetim: Kurum geneli yönetici görünümü ve yetkili olduğu onay/rapor alanlarını görür.\n- Admin / Sistem Yöneticisi: Sistem ayarları, rol matrisi, kullanıcı ve modül yönetimi dahil geniş yönetim alanlarını görür.\n- Grup Başkanı: Kendi grup/üst birim kapsamındaki personel, performans ve raporları görür.\n- Koordinatör: Kendi çalışma grubu veya koordinasyon kapsamındaki kayıtları görür.\n- Amir / Değerlendirici: Kendisine atanmış değerlendirme görevlerini görür.\n- Personel: Yayınlandıktan sonra kendi karnesini, kendi bildirimlerini, kendi anket/destek işlemlerini ve yetki verilen özetleri görür.\n\nDikkat:\n- Yetki kapsamı dışındaki kişi detayı gösterilmemelidir.\n- Performans puanı, amir görüşü, mesaj içeriği ve anket cevabı hassas kabul edilir.\n- Asistan yalnızca rehberlik eder; yetkiyi aşan veri göstermez.`
    },
    {
      id:'reports_dashboard_v11',
      patterns:['raporlar nerede','dashboard nerede','yönetici dashboard','yonetici dashboard','performans raporları','süreç raporları','riskli personel analizi','başkan onayı bekleyenler','aksatan amirler','dönem tamamlama durumu','birim ortalaması','kategori ortalaması'],
      answer:`Raporlar ve dashboard ekranları, yöneticinin yetki kapsamındaki süreçleri izlemesi için kullanılır.\n\nDoğru ekranlar:\n- Performans Yönetimi > Yönetici Dashboard\n- Performans Yönetimi > Raporlar\n- Performans Yönetimi > Süreç Takibi\n- Performans Yönetimi > Süreç Raporları\n- Performans Yönetimi > Başkan Onayları\n\nRaporlarda takip edilebilecek başlıklar:\n1. Dönem tamamlanma durumu\n2. Eksik değerlendirme görevleri\n3. Aksatan/geciken amirler\n4. Başkan onayı bekleyen düşük performans kayıtları\n5. Yayın kilidi olan karneler\n6. Birim, grup ve kategori ortalamaları\n7. Riskli personel analizi\n8. Düşük/yüksek performans yoğunluğu\n\nDikkat:\n- Başkan/Admin genel görünürlük alabilir.\n- Grup Başkanı ve Koordinatör yalnızca yetki kapsamını görmelidir.\n- Personel kişi detayı içermeyen kendi grup/kategori özetini görebilir.`
    },
    {
      id:'support_ticket_v11',
      patterns:['destek talebi nasıl açılır','destek talebi','yardım talebi','sorun bildireceğim','hata bildireceğim','destek nerede'],
      answer:`Destek talebi, kullanıcıların sistemle ilgili yardım veya sorun bildirimlerini kayıt altına almak için kullanılır.\n\nDoğru ekran: İletişim ve Anket > Destek Talepleri\n\nAdım adım:\n1. Sol şeritten İletişim ve Anket bölümüne girin.\n2. Destek Talepleri ekranını açın.\n3. Yeni Destek Talebi butonuna basın.\n4. Konu başlığını yazın.\n5. Sorunun açıklamasını net şekilde girin.\n6. Gerekirse ekran görüntüsü veya belge ekleyin.\n7. Kaydedin/gönderin.\n8. Talebin durumunu aynı ekrandan takip edin.\n\nDikkat:\n- Beyaz ekran, açılmayan sayfa veya yetki sorunu varsa hangi ekranda olduğu belirtilmelidir.\n- Destek talebi kişisel yazışmada kaybolmaması için sistem içinde kayıt altına alınmalıdır.`
    },
    {
      id:'survey_v11',
      patterns:['anket nasıl cevaplanır','anket nerede','anket dolduracağım','anket oluşturma','anket sonuçları','geri bildirim anket'],
      answer:`Anketler, kurum içi görüş, memnuniyet, geri bildirim ve katılım verilerini toplamak için kullanılır.\n\nDoğru ekran: İletişim ve Anket > Anketler\n\nPersonel için adım adım:\n1. İletişim ve Anket bölümüne girin.\n2. Anketler ekranını açın.\n3. Size atanmış anketi seçin.\n4. Soruları cevaplayın.\n5. Gönder butonuna basın.\n6. Katılım durumunun tamamlandı olarak göründüğünü kontrol edin.\n\nYetkili kullanıcı için:\n1. Yeni anket oluşturulur.\n2. Sorular ve seçenekler girilir.\n3. Hedef kitle seçilir.\n4. Yayınlanır.\n5. Katılım ve sonuçlar yetki sınırına göre izlenir.\n\nDikkat:\n- Anket cevapları yetki ve gizlilik sınırına göre korunmalıdır.\n- Asistan kişisel anket cevabı veya hassas içerik göstermez.`
    },
    {
      id:'notifications_messages_v11',
      patterns:['bildirimler ne anlama gelir','bildirim nerede','duyuru nerede','mesajlaşma','mesaj nerede','duyuru nasıl gönderilir','bildirim nasıl çalışır'],
      answer:`Bildirim, duyuru ve mesajlaşma alanları BYS360’ın kurum içi iletişim katmanıdır.\n\nKullanım alanları:\n- Bildirimler: Sistem olayları, görevler, onaylar ve hatırlatmalar için kullanılır.\n- Duyurular: Kurumsal bilgilendirmelerin hedef kitlelere iletilmesini sağlar.\n- Mesajlaşma: Kullanıcılar arasında kayıtlı kurum içi yazışma yapılmasını sağlar.\n\nAdım adım genel kullanım:\n1. Sol şeritten İletişim ve Anket veya Genel alanını açın.\n2. Bildirimler, Duyurular veya Mesajlaşma ekranına girin.\n3. Size gelen kayıtları okuyun veya yetkiniz varsa yeni kayıt oluşturun.\n4. Gerekli işlem tamamlandıktan sonra durumun güncellendiğini kontrol edin.\n\nDikkat:\n- Mesaj içeriği hassas olabilir; yetkisiz kişiye gösterilmemelidir.\n- Duyuru hedef kitlesi doğru seçilmelidir.\n- Kritik bildirimler süreç takibi açısından kayıt altında kalmalıdır.`
    },
    {
      id:'ai_decision_difference_v11',
      patterns:['ai karar destek nedir','yapay zeka karar destek','ai karar destek merkezi','asistan ile ai karar destek farkı','sen karar destek misin','karar verir misin','puan belirler misin'],
      answer:`BYS360 Asistanı ile AI Karar Destek Merkezi farklı görevler için kullanılır.\n\nBYS360 Asistanı:\n- Kullanıcıyı doğru ekrana yönlendirir.\n- İşlemleri adım adım öğretir.\n- Yetki dahilindeki genel özet ve rehberlik bilgisi verir.\n- Sol şerit, sekme ve süreçleri kullanıcıya anlatır.\n\nAI Karar Destek Merkezi:\n- Verileri özetler.\n- Raporları yorumlanabilir hale getirir.\n- Risk veya dikkat alanlarını görünür kılar.\n- Yöneticiye karar desteği sunar.\n\nKesin sınırlar:\n- AI idari karar vermez.\n- BYS360 Asistanı puan belirlemez.\n- Hassas veri, amir görüşü, mesaj içeriği veya anket cevabı yetkisiz kişiye gösterilmez.\n- Nihai karar yetkili insan/onay makamındadır.`
    },
    {
      id:'what_can_help_v11',
      patterns:['bana hangi konularda yardımcı olursun','neler yapabiliyorsun','hangi konularda yardım edersin','ne işe yararsın','bana nasıl yardım edersin'],
      answer:`BYS360 içinde yetkiniz dahilindeki işlemleri bulmanıza ve doğru sırayla tamamlamanıza yardımcı olurum.\n\nYardımcı olabileceğim başlıklar:\n1. Personel işlemleri\n2. İzin, devamsızlık ve vekâlet süreçleri\n3. Performans Yönetimi\n4. Dönemler, Değerlendirme Kriterleri ve görev üretimi\n5. Başkan Onayları ve 70 altı süreçler\n6. Rol matrisi, menü görünürlüğü ve yetki kontrolleri\n7. Dashboard ve raporlar\n8. Destek talepleri\n9. Anketler, bildirimler, duyurular ve mesajlaşma\n10. AI Karar Destek Merkezi’nin ne işe yaradığı\n11. Bulunduğunuz sayfada ne yapabileceğiniz\n12. Kırık link veya yanlış yönlendirme risklerinde güvenli açıklama\n\nDikkat:\n- İdari karar vermem.\n- Performans puanı belirlemem.\n- Hassas veri göstermem.\n- Yetkiniz dışındaki kayıtlara erişim sağlamam.`
    },
    {
      id:'technical_screen_hygiene_v11',
      patterns:['teknik ifade görünüyor','tanılama yazıyor','faz yazıyor','örnek kayıt yazıyor','json ekranı','beyaz ekran','sayfa açılmıyor','kırık link'],
      answer:`Bu durumda ekran veya yönlendirme canlı kullanıcı deneyimine uygun olmayabilir.\n\nKontrol sırası:\n1. Asistanın verdiği link güvenli menü haritasında var mı?\n2. Sayfa 404, 500, JSON veya beyaz ekran veriyor mu?\n3. Kullanıcının bu sayfaya yetkisi var mı?\n4. Sol menüdeki görünürlük ile backend route yetkisi aynı mı?\n5. Ekranda teknik ifadeler var mı: tanılama, örnek kayıt, test, faz, workflow, sync gibi?\n6. Gerekirse destek talebi açılmalı ve ilgili ekran adı belirtilmelidir.\n\nDikkat:\n- Asistan kırık linki tekrar önermemelidir.\n- Kullanıcıya teknik/geliştirici dili gösterilmemelidir.\n- Canlı ekranda sade Türkçe kurumsal ifade kullanılmalıdır.`
    }
  ];
  function findAnswer(q){ const nq=normalize(q); return answers.find(a=>a.patterns.some(p=>nq.includes(normalize(p)))); }
  function sanitizeText(text){
    let out=String(text||'');
    out=out.replace(/Dönem Yönetimi/g,'Dönemler');
    out=out.replace(new RegExp('end' + 'point yolu','gi'),'bağlantı');
    out=out.replace(/tanılama|örnek kayıt|iş planı/gi,'');
    out=out.replace(/süreç durumu/gi,'süreç durumu');
    out=out.replace(/süreç eşleşmesi/gi,'süreç eşleştirme');
    out=out.replace(/çaylar sıcak|Kış kendini göstermiş|sevimli yorum/gi,'');
    return out.trim();
  }
  function install(){
    window.BYS360_ASSISTANT_ROLE_REPORT_SUPPORT_AI_KB_V11 = { version: VERSION, title: MODULE_TITLE, routes: ROUTES, answers, findAnswer, sanitizeText,
      test(){
        const required=['role_matrix_overview_v11','menu_missing_v11','role_difference_v11','reports_dashboard_v11','support_ticket_v11','survey_v11','notifications_messages_v11','ai_decision_difference_v11','what_can_help_v11','technical_screen_hygiene_v11'];
        const ids=answers.map(a=>a.id); const missing=required.filter(x=>!ids.includes(x));
        const bad=answers.filter(a=>forbiddenPhrases.some(p=>a.answer.includes(p)));
        return {ok: missing.length===0 && bad.length===0, version: VERSION, answer_count: answers.length, missing, forbidden_in_answers: bad.map(a=>a.id)};
      }
    };
    const hookNames=['BYS360AssistantModule','BYS360AsistaniModulu','BYS360Assistant'];
    for (const name of hookNames){
      const obj=window[name];
      if (obj && !obj.__roleReportSupportAiKbV11){
        const originalAsk=obj.ask || obj.handleUserMessage || obj.respond;
        const localResponder=function(message){ const found=findAnswer(message); if(found) return sanitizeText(found.answer); if(typeof originalAsk==='function') return originalAsk.apply(this, arguments); return null; };
        if(!obj.ask) obj.ask=localResponder;
        if(!obj.handleUserMessage) obj.handleUserMessage=localResponder;
        obj.roleReportSupportAiKnowledgeV11=window.BYS360_ASSISTANT_ROLE_REPORT_SUPPORT_AI_KB_V11;
        obj.__roleReportSupportAiKbV11=true;
      }
    }
    document.addEventListener('submit', function(ev){ if (ev && ev.defaultPrevented) return;
      const form=ev.target; if(!form || !form.querySelector) return;
      const input=form.querySelector('input, textarea'); if(!input) return;
      const found=findAnswer(input.value); if(!found) return;
      const root=form.closest('[id*="assistant"], [class*="assistant"], [id*="asistan"], [class*="asistan"]') || document.body;
      setTimeout(()=>{ const area=root.querySelector('[data-bys360-assistant-messages], .bys360-assistant-messages, .assistant-messages, .messages');
        if(area && !area.textContent.includes(found.answer.slice(0,35))){ const div=document.createElement('div'); div.className='bys360-assistant-message bys360-assistant-message-bot bys360-v11-kb-answer'; div.textContent=sanitizeText(found.answer); area.appendChild(div); }
      },50);
    }, true);
    window.dispatchEvent(new CustomEvent('bys360:assistant:role-report-support-ai-kb-v11-ready',{detail:window.BYS360_ASSISTANT_ROLE_REPORT_SUPPORT_AI_KB_V11}));
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', install); else install();
})();
