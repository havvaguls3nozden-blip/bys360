"""BYS360 Performans Geri Bildirim Görüşmesi Faz 2 rehber veri servisi.

Bu dosya veritabanı bağımlılığı taşımaz. Faz 2'nin amacı; yöneticinin görüşmeye
hazırlanmasını, görüşmeyi 60 dakikalık akışa göre yürütmesini ve geri bildirimi
SBI diliyle somutlaştırmasını sağlamaktır.
"""
from __future__ import annotations

from typing import Any

FLOW_STEPS: list[dict[str, Any]] = [
    {
        "no": "01",
        "time": "0-5 dk",
        "title": "Açılış ve güvenli alan",
        "purpose": "Görüşmenin tonunu kurmak; çalışana bunun yargılama değil birlikte netleşme görüşmesi olduğunu göstermek.",
        "do": [
            "Görüşmenin süresini ve akışını en başta söyleyin.",
            "Önce çalışanın kendi değerlendirmesini dinleyeceğinizi belirtin.",
            "Telefon, ekran ve dış bölünmeleri kapatın.",
        ],
        "avoid": [
            "Vaktim az, hızlı geçelim gibi aceleci girişler.",
            "Çok gerilmene gerek yok diyerek gerginliği büyütmek.",
        ],
        "questions": [
            "Hazırsan önce bu dönemi senin gözünden dinlemek istiyorum.",
            "Bugün görüşmeden çıkarken hangi konuların netleşmiş olmasını istersin?",
        ],
    },
    {
        "no": "02",
        "time": "5-15 dk",
        "title": "Öz değerlendirmeyi dinleme",
        "purpose": "Çalışanın kendi performansını, güçlü taraflarını ve zorlandığı alanları sahiplenmesini sağlamak.",
        "do": [
            "Sözünü kesmeden dinleyin.",
            "İlk yanıt kısa kalırsa birkaç saniye bekleyin.",
            "Anladığınızı göstermek için duyduğunuzu özetleyin.",
        ],
        "avoid": [
            "Hemen düzeltmeye veya savunmaya geçmek.",
            "Çalışanın cümlesini kendi yorumunuzla kapatmak.",
        ],
        "questions": [
            "Bu dönem en çok neyle gurur duyuyorsun?",
            "Sence hangi konuda daha iyi bir sonuç alınabilirdi?",
            "Bir sonraki dönem için kendine ne hedefliyorsun?",
        ],
    },
    {
        "no": "03",
        "time": "15-25 dk",
        "title": "Yönetici değerlendirmesini paylaşma",
        "purpose": "Yönetici puanını ve gözlemini şeffaf, karşılaştırılabilir ve somut örneklerle aktarmak.",
        "do": [
            "Önce aynı fikirde olduğunuz alanları söyleyin.",
            "Farklı düşündüğünüz alanlarda SBI dili kullanın.",
            "Puanı tek başına değil, davranış ve etki ile açıklayın.",
        ],
        "avoid": [
            "Kişiliğe dönük yargılar.",
            "Yıl boyunca hiç konuşulmamış konuyu sürpriz biçimde masaya koymak.",
        ],
        "questions": [
            "Bu kriterde benim gördüğüm tablo şu; senin gözünden eksik bıraktığım bir şey var mı?",
            "Bu farkı kapatmak için hangi destek işe yarar?",
        ],
    },
    {
        "no": "04",
        "time": "25-35 dk",
        "title": "Güçlü yönleri konuşma",
        "purpose": "Çalışanın değer ürettiği davranışları görünür ve tekrar edilebilir hale getirmek.",
        "do": [
            "Güçlü yönü somut olayla ilişkilendirin.",
            "Sadece övmeyin; bu gücün nasıl sürdürüleceğini konuşun.",
            "Çalışanın kendi cümlesini kayda alın.",
        ],
        "avoid": [
            "Genel iltifatla yetinmek.",
            "Yüksek performanslı çalışanı sadece daha çok iş yüküyle ödüllendirmek.",
        ],
        "questions": [
            "Bu dönem sana 'işte bu benim katkım' dedirten an hangisiydi?",
            "Ekibin en çok hangi konuda sana başvuruyor?",
            "Bu gücü bir sonraki dönemde nereye taşımak istersin?",
        ],
    },
    {
        "no": "05",
        "time": "35-50 dk",
        "title": "Gelişim alanlarını konuşma",
        "purpose": "Gelişim ihtiyacını savunma yaratmadan, davranış ve sonuç üzerinden netleştirmek.",
        "do": [
            "En fazla iki ana gelişim alanına odaklanın.",
            "Her alanı örnek davranışla destekleyin.",
            "Çıkış yolu olmayan cümle kurmayın.",
        ],
        "avoid": [
            "Liste halinde çok sayıda eleştiri sıralamak.",
            "Geçmiş hatayı tekrar tekrar büyütmek.",
        ],
        "questions": [
            "Sence hangi tek davranış değişirse en büyük fark oluşur?",
            "Bu alanda senden ne beklediğimi birlikte netleştirelim mi?",
        ],
    },
    {
        "no": "06",
        "time": "50-60 dk",
        "title": "Eylem planı ve kapanış",
        "purpose": "Görüşmeyi somut aksiyon, takip tarihi ve karşılıklı netlikle kapatmak.",
        "do": [
            "En fazla üç SMART aksiyon belirleyin.",
            "Takip tarihini görüşme bitmeden yazın.",
            "Çalışana son söz hakkı verin.",
            "Özet notun BYS360'a işleneceğini söyleyin.",
        ],
        "avoid": [
            "Görüşmeyi 'sonra bakarız' diyerek kapatmak.",
            "Aksiyonun sahibini ve tarihini belirsiz bırakmak.",
        ],
        "questions": [
            "Bugünden sonra ilk somut adımımız ne olsun?",
            "Bu planı hangi tarihte birlikte kontrol edelim?",
            "Eklemek istediğin son bir cümle var mı?",
        ],
    },
]

SCENARIOS: list[dict[str, Any]] = [
    {
        "key": "yuksek-performans",
        "title": "Yüksek performanslı çalışan",
        "situation": "Çalışan dönem boyunca belirgin katkı üretmiş; takdir beklerken yeni hedef de arıyor.",
        "attention": "Övgüyü somut ve kısa tutun; ardından bu gücün nereye taşınacağını konuşun.",
        "openings": [
            "Bu dönem katkın çok görünürdü; bugün bunu kutlayıp bir sonraki adımı birlikte netleştirmek istiyorum.",
            "Güçlü bir dönem geçirdin. Benim için önemli olan, bu gücü sürdürülebilir hale nasıl getireceğimiz.",
            "Bugün sadece iyi yapılanları saymayacağız; seni daha da ileri taşıyacak alanı birlikte arayacağız.",
            "Bu görüşmede güçlü taraflarını somutlaştırıp yeni dönemde hangi sınırı aşabileceğini konuşalım.",
            "Katkını görüyorum; şimdi bu katkının kuruma ve ekibe daha fazla nasıl yayılacağını düşünelim.",
        ],
        "questions": [
            "Bu dönem sana en çok 'benim katkım buydu' dedirten olay hangisiydi?",
            "Ekibin en çok hangi konuda sana başvurdu?",
            "Bu başarının arkasındaki tekrar edilebilir davranış neydi?",
            "Bir sonraki dönem hangi becerini daha görünür kullanmak istersin?",
            "Bu döneme bir başlık versen ne olurdu?",
        ],
    },
    {
        "key": "dusuk-performans",
        "title": "Düşük performanslı çalışan",
        "situation": "Sonuçlar beklentinin altında; çalışanın farkındalığı net olmayabilir.",
        "attention": "Ciddiyeti kaybetmeden yargısız kalın. Önce çalışanın dönemi nasıl yaşadığını dinleyin.",
        "openings": [
            "Bugünkü görüşme kolay olmayabilir; amacım seni sıkıştırmak değil, ne olduğunu birlikte anlamak.",
            "Beklediğimiz noktada olmadığımız alanlar var. Ben anlatmadan önce bu dönemi senin gözünden dinlemek istiyorum.",
            "Bu görüşmeyi bir hüküm anı gibi değil, çıkış yolunu birlikte netleştireceğimiz bir çalışma olarak görelim.",
            "Önce gerçek tabloyu sakin biçimde anlamak istiyorum; sonra somut adımları belirleyeceğiz.",
            "Zorlandığın alanlar olsa da çıkış yolu olmayan bir cümle kurmayacağım; birlikte ilerleme planı çıkaracağız.",
        ],
        "questions": [
            "Bu dönemde seni en çok zorlayan konu neydi?",
            "Kendi performansını önceki dönemle kıyasladığında ne değişti?",
            "Bu dönem yine de başarı saydığın bir şey var mı?",
            "Hangi tek davranış değişirse en büyük fark oluşur?",
            "Bu alanda benden veya kurumdan hangi destek işe yarar?",
        ],
    },
    {
        "key": "toparlanma",
        "title": "Önceki dönem zayıf, bu dönem iyi",
        "situation": "Çalışan toparlanmış; geçmişin gölgesine takılmadan mevcut gelişimi sahiplenmesi gerekir.",
        "attention": "Geçmişi küçümseyici biçimde hatırlatmayın; değişimin nasıl gerçekleştiğini görünür kılın.",
        "openings": [
            "Bu dönem önceki döneme göre belirgin bir toparlanma gördüm; önce senin neyi farklı yaptığını duymak isterim.",
            "Bugün güzel bir dönüşümü konuşacağız. Bunu mümkün kılan davranışları birlikte netleştirelim.",
            "Bu dönemde zeminini güçlendirdiğini düşünüyorum; bunu sen nasıl yaşadın?",
            "Geçmişe takılmadan, bu dönem işe yarayan şeyleri bulalım ve yeni döneme taşıyalım.",
            "Bence burada anlatılacak önemli bir gelişim hikâyesi var; önce senden dinleyelim.",
        ],
        "questions": [
            "Bu dönem en büyük farkı yaratan davranışın neydi?",
            "Zihninde veya çalışma biçiminde ne değişti?",
            "Kimden aldığın hangi geri bildirim etkili oldu?",
            "Bu toparlanmayı sürdürmek için neye ihtiyacın var?",
            "Bu dönüşümü kendi cümlenle nasıl anlatırsın?",
        ],
    },
    {
        "key": "dususe-gecen",
        "title": "Önceki dönem iyi, bu dönem düşüş var",
        "situation": "Önceden güvenilir performans varken bu dönem düşüş oluşmuş olabilir.",
        "attention": "Nedeni bilmeden hüküm vermeyin; önce çalışanın iç ve dış etkenleri anlatmasına alan açın.",
        "openings": [
            "Bu dönem önceki dönemlerden farklı bir tablo gördüm; sebebini birlikte anlamak istiyorum.",
            "Seni tanıdığım performanstan uzaklaştığımız alanlar var. Önce senin ne hissettiğini duymak isterim.",
            "Bugün yargılamak için değil, değişen şeyi doğru anlamak için buradayım.",
            "Bence bu dönem tek kelimeyle açıklanacak kadar basit değil; birlikte parçalara ayıralım.",
            "Geçen dönem güçlü giden bazı şeyleri bu dönem yakalayamadık. Bunun nedenini senin gözünden dinleyelim.",
        ],
        "questions": [
            "Bu düşüşü sen de hissettin mi?",
            "Son altı ayda seni işte veya iş dışında en çok zorlayan şey neydi?",
            "Önceki dönem seni güçlü tutan neydi, bu dönem ne eksildi?",
            "Keşke daha farklı yapsaydım dediğin bir alan var mı?",
            "Yeni döneme geçerken hangi desteği netleştirelim?",
        ],
    },
    {
        "key": "yeni-terfi",
        "title": "Yeni terfi alan çalışan",
        "situation": "Yeni rolde hem heyecan hem ispat baskısı olabilir.",
        "attention": "Tebriği abartıp gelişim alanını görünmez kılmayın; eleştiriyi de terfiyi sorgulatacak sertlikte vermeyin.",
        "openings": [
            "Yeni rolündeki ilk değerlendirmeyi, eski görevden çok yeni zemini anlamak için kullanmak istiyorum.",
            "Bu görüşmenin konusu sadece puan değil; yeni rolde nasıl konumlandığını birlikte görmek.",
            "Terfi sonrası dönemler öğreticidir. Seni zorlayan ve güçlendiren tarafları konuşalım.",
            "Yeni sorumlulukların sende nasıl karşılık bulduğunu önce senden dinlemek isterim.",
            "Bu görüşmeyi yeni rolünün çalışma planını netleştiren bir ara durak gibi ele alalım.",
        ],
        "questions": [
            "Yeni role geçtiğinde ilk baskın duygu neydi?",
            "İlk haftalarda seni en çok zorlayan konu ne oldu?",
            "Bu rolde zaten güçlü olduğun alan hangisi?",
            "Yeni rolün senden hangi yeni davranışı bekliyor?",
            "Bir yıl sonra bu dönemi neyle hatırlamak istersin?",
        ],
    },
    {
        "key": "terfi-bekleyen",
        "title": "Terfi bekleyip alamayan çalışan",
        "situation": "Beklenti karşılanmamış; kırgınlık, hayal kırıklığı veya motivasyon kaybı olabilir.",
        "attention": "Savunmaya geçmeyin. Önce beklentiyi nasıl kurduğunu ve kararı nasıl yaşadığını dinleyin.",
        "openings": [
            "Bu kararın sende bir karşılığı olduğunu biliyorum; önce bunu nasıl yaşadığını dinlemek isterim.",
            "Bugün savunma yapmak için değil, beklentiyi ve gelişim yolunu netleştirmek için buradayız.",
            "Terfi konusunu geçiştirmeden, açık ve saygılı biçimde konuşalım.",
            "Bu görüşmede kararın gerekçesini ve sonraki adımı anlaşılır hale getirmek istiyorum.",
            "Önce senin beklentini nereden kurduğunu anlayalım; sonra yol haritasını konuşalım.",
        ],
        "questions": [
            "Terfi beklentini hangi gözlemlere veya konuşmalara dayandırdın?",
            "Karardan sonra aklında kalan en önemli soru ne oldu?",
            "Bir üst rol için hangi davranışın daha görünür olması gerekir?",
            "Bu konuda sana net ve ölçülebilir hangi hedefi vermeliyiz?",
            "Motivasyonunu korumak için hangi destek anlamlı olur?",
        ],
    },
    {
        "key": "itirazli",
        "title": "Kendi değerlendirmesine itiraz eden çalışan",
        "situation": "Çalışan puanı veya yorumu adil bulmayabilir.",
        "attention": "İtirazı kişisel direnç gibi görmeyin; veri, örnek ve dinleme dengesini koruyun.",
        "openings": [
            "Değerlendirmeyle ilgili farklı düşündüğünü biliyorum; bunu sakin ve somut biçimde konuşalım.",
            "Amacım seni ikna etmek değil, elimizdeki örnekleri birlikte netleştirmek.",
            "İtirazını duymak istiyorum; sonra ben de hangi gözlemlere dayandığımı paylaşacağım.",
            "Bugün fikir ayrılığını kişiselleştirmeden, kriter ve örnek üzerinden ilerleyelim.",
            "Bu görüşmeden çıkarken hangi konularda aynı, hangi konularda farklı düşündüğümüz net olsun.",
        ],
        "questions": [
            "Hangi kriterde farklı düşündüğünü en somut örnekle anlatır mısın?",
            "Sence hangi katkın değerlendirmede yeterince görünmedi?",
            "Benim gözlemimi değiştirebilecek hangi veri veya olay var?",
            "Bu farkı yeni dönemde nasıl ölçülebilir hale getirelim?",
            "Görüşme sonunda hangi netliğe ulaşmak istersin?",
        ],
    },
    {
        "key": "sessiz",
        "title": "Sessiz / kendini küçük gören çalışan",
        "situation": "Çalışan katkısını küçümseyebilir veya görünür olmaktan kaçınabilir.",
        "attention": "Aşırı övgüyle boğmayın; küçük somut örneklerden içgörü çıkarmasına yardım edin.",
        "openings": [
            "Bugün özellikle senin kendi katkını nasıl gördüğünü duymak istiyorum.",
            "Bazı katkıların sessiz ama değerli olduğunu düşünüyorum; birlikte görünür kılalım.",
            "Bu görüşmede büyük cümleler kurmak zorunda değilsin; somut birkaç örnekle ilerleyelim.",
            "Benim gördüğüm bazı güçlü tarafların var; önce senin kendini nasıl gördüğünü dinleyeyim.",
            "Kendini olduğundan küçük anlatma ihtimalin var; bu yüzden örnekler üzerinden gideceğiz.",
        ],
        "questions": [
            "Bu dönem küçük de olsa iyi yaptığını düşündüğün bir iş var mı?",
            "Ekipte insanların sana güvendiği konu ne olabilir?",
            "Sana kolay gelen ama başkalarının zorlandığı bir iş hangisi?",
            "Kendine biraz daha alan açsan hangi katkın görünür olurdu?",
            "Bu dönemi kendi adına hangi cümleyle kapatırsın?",
        ],
    },
    {
        "key": "izinden-donen",
        "title": "Uzun süre izinden dönen çalışan",
        "situation": "İşe dönüş, ritim yakalama ve ekip akışına yeniden girme süreci vardır.",
        "attention": "İzin dönemini sorgulamayın; işe dönüş koşullarını ve destek ihtiyacını konuşun.",
        "openings": [
            "Dönüş sürecini performans kadar uyum ve destek ihtiyacı açısından da konuşmak istiyorum.",
            "Uzun bir aradan sonra ritmi yeniden kurmak zaman alabilir; bu dönemi birlikte değerlendirelim.",
            "Bugün nerede zorlandığını ve hangi destekle daha hızlı toparlanacağını netleştirelim.",
            "İşe dönüşte seni güçlendiren ve yoran tarafları anlamak istiyorum.",
            "Bu görüşmeyi yeni döneme sağlıklı başlangıç planı gibi ele alalım.",
        ],
        "questions": [
            "Döndükten sonra seni en çok zorlayan alan ne oldu?",
            "Hangi süreçlere yeniden alışmak zaman aldı?",
            "Ekipten veya yöneticiden hangi destek işe yaradı?",
            "Yeni dönemde ritmini güçlendirmek için ilk adım ne olsun?",
            "Kendini hangi tarihte daha dengede görmeyi hedefliyorsun?",
        ],
    },
    {
        "key": "zor-donem",
        "title": "Kişisel zor dönem yaşayan çalışan",
        "situation": "Kişisel koşullar performansa yansımış olabilir; mahremiyet ve destek dengesi önemlidir.",
        "attention": "Özel hayata müdahale etmeyin. İşe yansıyan davranış ve destek ihtiyacı üzerinden konuşun.",
        "openings": [
            "Bu dönemin kolay olmadığını hissediyorum; özel alanına girmeden işte neye ihtiyaç duyduğunu konuşalım.",
            "Amacım kişisel konuları sorgulamak değil, iş akışında seni nasıl destekleyeceğimizi netleştirmek.",
            "Bu görüşmede hem beklentileri hem de uygulanabilir desteği dengeli konuşmak istiyorum.",
            "Zor dönemlerde netlik ve destek daha önemli olur; bugün bunu birlikte kuralım.",
            "İstersen sadece işe yansıyan kısmı konuşalım ve sürdürülebilir bir plan çıkaralım.",
        ],
        "questions": [
            "Bu dönem iş akışında seni en çok zorlayan şey ne oldu?",
            "Hangi beklentiyi netleştirirsek yükün azalır?",
            "Kısa vadede hangi destek gerçekçi olur?",
            "Performansını korumak için hangi öncelikleri seçmeliyiz?",
            "Takip görüşmesini hangi aralıkta yapmak iyi olur?",
        ],
    },
    {
        "key": "ekip-surtusme",
        "title": "Ekipte sürtüşme / dedikodu yaşayan çalışan",
        "situation": "Ekip ilişkileri, iletişim tonu veya güven sorunu performansı etkileyebilir.",
        "attention": "Kişileri değil davranışları konuşun. Duyumlarla değil gözlemlenebilir etkilerle ilerleyin.",
        "openings": [
            "Ekip içinde iş akışını etkileyen bazı iletişim başlıkları var; bunu kişiselleştirmeden konuşalım.",
            "Bugün kimin haklı olduğundan çok, çalışma düzenini nasıl güçlendireceğimizi konuşmak istiyorum.",
            "Duyumlarla değil, işe yansıyan davranış ve etki üzerinden ilerleyeceğiz.",
            "Ekip güvenini koruyacak somut adımları birlikte belirleyelim.",
            "Bu görüşmede iletişim dilinin ekibe etkisini sakin biçimde ele alalım.",
        ],
        "questions": [
            "Bu durum işini veya ekip akışını nasıl etkiledi?",
            "Senin kontrolünde olan hangi davranış değişebilir?",
            "Ekipte güveni artıracak ilk somut adım ne olur?",
            "Hangi iletişim kuralını birlikte netleştirmeliyiz?",
            "Bu konuda takip için neyi ölçelim?",
        ],
    },
    {
        "key": "uzaktan-calisan",
        "title": "Uzaktan / sahadan çalışan kişi",
        "situation": "Görünürlük, iletişim sıklığı ve çıktı takibi farklılaşabilir.",
        "attention": "Fiziksel görünürlük yerine çıktı, iletişim netliği ve takip disiplini üzerinden değerlendirin.",
        "openings": [
            "Çalışma düzenin farklı olduğu için performansı çıktı ve iletişim netliği üzerinden konuşmak istiyorum.",
            "Bugün görünürlükten çok, işin takibi ve etkisini birlikte değerlendirelim.",
            "Uzak/saha çalışma düzeninde seni güçlendiren ve zorlayan tarafları anlamak istiyorum.",
            "Bu görüşmede çalışma biçimini değil, sonuç ve koordinasyon kalitesini konuşacağız.",
            "Bir sonraki dönem iletişim ve takip ritmini daha net kurabiliriz.",
        ],
        "questions": [
            "Bu çalışma düzeninde seni en verimli kılan şey ne?",
            "Hangi bilgi akışında kopukluk yaşandı?",
            "Çıktıların görünür olması için nasıl bir takip ritmi iyi olur?",
            "Ekipten beklediğin netlik veya destek ne?",
            "Yeni dönemde hangi iletişim kuralını deneyelim?",
        ],
    },
    {
        "key": "kidemli",
        "title": "Kıdemli / yaşça büyük çalışan",
        "situation": "Deneyim güçlüdür; geri bildirim saygı ve netlik dengesiyle verilmelidir.",
        "attention": "Deneyimi küçümsemeyin; yine de beklentiyi açık ve davranış düzeyinde söyleyin.",
        "openings": [
            "Deneyiminin kuruma katkısını biliyorum; bugün bu katkının yeni beklentilerle nasıl birleşeceğini konuşalım.",
            "Bu görüşmede saygıyı ve açıklığı birlikte koruyarak ilerlemek istiyorum.",
            "Tecrübeni değerli buluyorum; bazı çalışma beklentilerini de netleştirmemiz gerekiyor.",
            "Bugün kişisel değil, işin akışı ve etki alanın üzerinden konuşacağız.",
            "Deneyiminin ekibe daha güçlü aktarılması için hangi adımları atabiliriz, birlikte bakalım.",
        ],
        "questions": [
            "Bu dönem deneyimin en çok nerede katkı sağladı?",
            "Yeni çalışma düzeninde seni zorlayan değişiklik ne?",
            "Ekibe aktarılmasını istediğin en önemli bilgi ne?",
            "Hangi beklenti daha net ifade edilirse süreç kolaylaşır?",
            "Yeni dönemde deneyimini hangi alanda daha görünür kullanırsın?",
        ],
    },
    {
        "key": "istifa-riski",
        "title": "İstifa düşündüğü hissedilen çalışan",
        "situation": "Bağlılık ve motivasyon düşmüş olabilir; doğrudan suçlayıcı dil süreci koparabilir.",
        "attention": "Tahmininizi kesin bilgi gibi sunmayın. Bağlılık, beklenti ve destek başlıklarını açık uçlu konuşun.",
        "openings": [
            "Son dönemde motivasyonunda bir değişim hissediyorum; bunu doğru mu okuyorum, senden duymak isterim.",
            "Bugün sadece performansı değil, burada kalmanı güçlendiren veya zorlaştıran şeyleri de konuşalım.",
            "Bir varsayımla gelmek istemiyorum; işine ve kuruma dair nasıl hissettiğini anlamak istiyorum.",
            "Bu görüşmede beklentilerini ve kurumun senden beklentisini açıkça yan yana koyalım.",
            "Eğer seni yoran veya uzaklaştıran bir şey varsa, bunu güvenli biçimde konuşabiliriz.",
        ],
        "questions": [
            "Son dönemde işine bağlılığını artıran veya azaltan şey ne?",
            "Burada kalmanı güçlendirecek hangi koşul önemli?",
            "Hangi beklentin karşılanmadığında motivasyonun düşüyor?",
            "Yeni dönemde seni yeniden heyecanlandıracak hedef ne olabilir?",
            "Bu konuda birlikte atabileceğimiz gerçekçi adım nedir?",
        ],
    },
    {
        "key": "mesafeli",
        "title": "Yöneticisiyle mesafeli çalışan",
        "situation": "Güven, iletişim veya önceki deneyimler nedeniyle mesafe oluşmuş olabilir.",
        "attention": "Mesafeyi kişisel sorun gibi değil, çalışma ilişkisini iyileştirme konusu olarak ele alın.",
        "openings": [
            "Aramızdaki çalışma iletişimini daha verimli hale getirmek istiyorum; önce senin deneyimini dinleyelim.",
            "Bu görüşmede sadece puanı değil, birlikte çalışma biçimimizi de konuşmak istiyorum.",
            "Benden kaynaklanan bir iletişim engeli varsa bunu duymaya açığım; amacım iş akışını iyileştirmek.",
            "Mesafeyi büyütmeden, beklentilerimizi daha açık hale getirelim.",
            "Bugün karşılıklı güveni ve netliği artıracak somut davranışları belirleyebiliriz.",
        ],
        "questions": [
            "Benimle çalışırken hangi konuda daha fazla netliğe ihtiyaç duyuyorsun?",
            "Hangi iletişim biçimi senin için daha verimli olur?",
            "Benden beklediğin geri bildirim sıklığı nedir?",
            "Birlikte çalışmayı kolaylaştıracak ilk küçük adım ne olabilir?",
            "Bu görüşmeden sonra neyin değişmesini istersin?",
        ],
    },
]

SBI_EXAMPLES: list[dict[str, str]] = [
    {
        "category": "Zamanında katılım",
        "weak": "Sürekli geç kalıyorsun.",
        "situation": "Bu hafta pazartesi ve çarşamba 09.30 ekip toplantılarında",
        "behavior": "toplantıya yaklaşık 20 dakika geç katıldın",
        "impact": "gündemi tekrar etmek zorunda kaldık ve ekip akışı yavaşladı",
        "sentence": "Bu hafta pazartesi ve çarşamba 09.30 ekip toplantılarında toplantıya yaklaşık 20 dakika geç katıldın; bu nedenle gündemi tekrar etmek zorunda kaldık ve ekip akışı yavaşladı.",
    },
    {
        "category": "Rapor teslimi",
        "weak": "Sorumluluk almıyorsun.",
        "situation": "Nisan ayı faaliyet raporunun teslim tarihinde",
        "behavior": "raporu kararlaştırılan tarihten iki gün sonra ilettin",
        "impact": "üst yazı hazırlığı gecikti ve kontrol süremiz daraldı",
        "sentence": "Nisan ayı faaliyet raporunun teslim tarihinde raporu kararlaştırılan tarihten iki gün sonra ilettin; bu nedenle üst yazı hazırlığı gecikti ve kontrol süremiz daraldı.",
    },
    {
        "category": "Ekip desteği",
        "weak": "Çok yardımseversin.",
        "situation": "Yeni başlayan personelin ilk hafta uyum sürecinde",
        "behavior": "iş akışını adım adım anlattın ve örnek dosyaları paylaştın",
        "impact": "personel daha hızlı adapte oldu ve ekip üzerindeki tekrar açıklama yükü azaldı",
        "sentence": "Yeni başlayan personelin ilk hafta uyum sürecinde iş akışını adım adım anlattın ve örnek dosyaları paylaştın; bu sayede personel daha hızlı adapte oldu ve ekip üzerindeki tekrar açıklama yükü azaldı.",
    },
    {
        "category": "Toplantı iletişimi",
        "weak": "Toplantılarda sertsin.",
        "situation": "Salı günkü proje değerlendirme toplantısında",
        "behavior": "itirazını karşı tarafın sözünü bitirmeden ve yüksek sesle dile getirdin",
        "impact": "konu çözümden uzaklaştı ve toplantı gerilimi arttı",
        "sentence": "Salı günkü proje değerlendirme toplantısında itirazını karşı tarafın sözünü bitirmeden ve yüksek sesle dile getirdin; bu nedenle konu çözümden uzaklaştı ve toplantı gerilimi arttı.",
    },
    {
        "category": "Kriz yönetimi",
        "weak": "Krizlerde çok iyisin.",
        "situation": "Ziyaretçi yoğunluğunun arttığı cuma öğleden sonra",
        "behavior": "öncelikleri hızlı ayırıp iki kişiyi yönlendirdin ve bilgi akışını tek noktada topladın",
        "impact": "bekleme süresi azaldı ve ekip panik yaşamadan çalıştı",
        "sentence": "Ziyaretçi yoğunluğunun arttığı cuma öğleden sonra öncelikleri hızlı ayırıp iki kişiyi yönlendirdin ve bilgi akışını tek noktada topladın; bu sayede bekleme süresi azaldı ve ekip panik yaşamadan çalıştı.",
    },
    {
        "category": "Bilgi paylaşımı",
        "weak": "Bizi habersiz bırakıyorsun.",
        "situation": "Görev dağılımı değiştiğinde",
        "behavior": "değişikliği ekibe aynı gün bildirmedin",
        "impact": "iki kişi eski plana göre çalıştı ve iş tekrarlandı",
        "sentence": "Görev dağılımı değiştiğinde değişikliği ekibe aynı gün bildirmedin; bu nedenle iki kişi eski plana göre çalıştı ve iş tekrarlandı.",
    },
    {
        "category": "Süreç iyileştirme",
        "weak": "Çok sistemlisin.",
        "situation": "Arşiv kontrol dosyalarında tekrar eden hataları fark ettiğinde",
        "behavior": "kontrol listesini sadeleştirip herkesin kullanacağı ortak şablona çevirdin",
        "impact": "kontrol süresi kısaldı ve dosya hataları azaldı",
        "sentence": "Arşiv kontrol dosyalarında tekrar eden hataları fark ettiğinde kontrol listesini sadeleştirip herkesin kullanacağı ortak şablona çevirdin; bu sayede kontrol süresi kısaldı ve dosya hataları azaldı.",
    },
    {
        "category": "Takip disiplini",
        "weak": "İşleri takip etmiyorsun.",
        "situation": "Geçen hafta sana iletilen üç açık görevde",
        "behavior": "iki görev için durum güncellemesi paylaşmadın",
        "impact": "işin hangi aşamada olduğunu göremedik ve ek planlama gecikti",
        "sentence": "Geçen hafta sana iletilen üç açık görevde iki görev için durum güncellemesi paylaşmadın; bu nedenle işin hangi aşamada olduğunu göremedik ve ek planlama gecikti.",
    },
    {
        "category": "Vatandaş/ziyaretçi iletişimi",
        "weak": "İletişimin iyi.",
        "situation": "Bilgi almak için gelen ziyaretçi yoğun ve gergin olduğunda",
        "behavior": "önce sakin biçimde dinledin, ardından seçenekleri kısa ve net anlattın",
        "impact": "ziyaretçi sakinleşti ve işlem daha kısa sürede tamamlandı",
        "sentence": "Bilgi almak için gelen ziyaretçi yoğun ve gergin olduğunda önce sakin biçimde dinledin, ardından seçenekleri kısa ve net anlattın; bu sayede ziyaretçi sakinleşti ve işlem daha kısa sürede tamamlandı.",
    },
    {
        "category": "Önceliklendirme",
        "weak": "Önceliklerini bilmiyorsun.",
        "situation": "Aynı gün içinde iki acil talep geldiğinde",
        "behavior": "önceliği netleştirmeden düşük etkili işe başladın",
        "impact": "kritik talep gün sonuna kaldı ve ekip ek mesai yapmak zorunda kaldı",
        "sentence": "Aynı gün içinde iki acil talep geldiğinde önceliği netleştirmeden düşük etkili işe başladın; bu nedenle kritik talep gün sonuna kaldı ve ekip ek mesai yapmak zorunda kaldı.",
    },
]

DISC_TIPS = [
    {"code": "D", "name": "Baskın", "need": "Sonuç ve hız", "tip": "Kısa, net ve sonuç odaklı konuşun; hedef ve etkiyi erken söyleyin."},
    {"code": "I", "name": "Etkileyici", "need": "Takdir ve görünürlük", "tip": "Sıcak başlayın, katkıyı görünür yapın, fikirlerine alan açın."},
    {"code": "S", "name": "Sadık", "need": "Güven ve uyum", "tip": "Yavaş ve destekleyici ilerleyin; ani değişiklik yerine küçük adım önerin."},
    {"code": "C", "name": "Analitik", "need": "Veri ve doğruluk", "tip": "Örnek, kriter ve gerekçe hazırlayın; düşünmesi için zaman tanıyın."},
]

CHECKLISTS = {
    "before": [
        "Görüşme amacı yazıldı.",
        "En az iki güçlü yön somut örnekle hazırlandı.",
        "Gelişim alanı kişilik değil davranış diliyle yazıldı.",
        "SBI örnekleri hazırlandı.",
        "Açılış cümlesi seçildi ve yöneticinin kendi diline uyarlandı.",
    ],
    "during": [
        "Çalışan önce konuştu.",
        "Yönetici puanı örneklerle paylaşıldı.",
        "Güçlü yönler ve gelişim alanları dengeli konuşuldu.",
        "Savunma oluştuğunda örnek ve etkiye geri dönüldü.",
        "Son söz çalışana bırakıldı.",
    ],
    "after": [
        "Görüşme sonrası not BYS360'a işlendi.",
        "En az bir SMART aksiyon oluşturuldu.",
        "Takip tarihi belirlendi.",
        "Özet mail taslağı kontrol edildi.",
        "Aksiyon planı takip listesine alındı.",
    ],
}


def _scenario_map() -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in SCENARIOS}


def get_selected_scenario(key: str | None = None) -> dict[str, Any]:
    data = _scenario_map()
    if key and key in data:
        return data[key]
    return SCENARIOS[0]


def build_guide_context(selected_key: str | None = None) -> dict[str, Any]:
    selected = get_selected_scenario(selected_key)
    return {
        "flow_steps": FLOW_STEPS,
        "scenarios": SCENARIOS,
        "selected_scenario": selected,
        "sbi_examples": SBI_EXAMPLES,
        "disc_tips": DISC_TIPS,
        "checklists": CHECKLISTS,
        "guide_stats": {
            "flow_steps": len(FLOW_STEPS),
            "minutes": 60,
            "scenarios": len(SCENARIOS),
            "opening_sentences": sum(len(s["openings"]) for s in SCENARIOS),
            "sbi_examples": len(SBI_EXAMPLES),
        },
    }
