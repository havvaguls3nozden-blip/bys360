Doküman Adı: BYS360 Kurumsal Proje ve Yönetici Raporu
Doküman Türü: Kurumsal / Yönetici
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası)
Son Güncelleme: 2026-09-02

---

**Okuyucu kitlesi:** Başkan, Başkan Yardımcısı, Grup Başkanları, üst yönetim. Bu belge teknik ayrıntı içermez; teknik dayanaklar `docs/current_state/` altındaki ilgili belgelerde ayrıca kayıtlıdır.

---

## 1. BYS360 nedir, neden vardır?

BYS360, Başkanlığın personel, performans değerlendirme, kurum içi iletişim, anket, destek ve güvenli dosya paylaşımı gibi günlük yönetim işlerini tek bir web tabanlı sistemde toplayan kurumsal bir yönetim platformudur. Bu işlerin daha önce dağınık araçlarla (ayrı tablolar, e-posta yazışmaları, kağıt onay akışları) yürütülmesi; veri tutarsızlığı, izlenebilirlik kaybı ve gecikmiş onay süreçleri gibi kurumsal riskler doğurur. BYS360, bu işlevleri tek bir kimlik doğrulama ve tek bir rol tabanlı yetkilendirme modeli altında birleştirerek bu riski azaltmayı amaçlar.

## 2. Kurumsal değer

- **Tek kayıt, tek doğruluk kaynağı:** Personel, performans ve iletişim verisi, birbirinden bağımsız dosyalar yerine tek bir veri tabanında, tutarlı biçimde tutulur.
- **İzlenebilir onay süreçleri:** Performans değerlendirmesi gibi çok aşamalı kurumsal süreçler (amir görüşü → üst amir onayı → gerektiğinde Başkanlık onayı) sistematik ve geriye dönük incelenebilir hale gelir.
- **Sınırlı ve denetlenebilir erişim:** Kullanıcılar, kurumun gerçek organizasyon hiyerarşisini yansıtan roller üzerinden, yalnızca görmesi gereken bilgiye erişir; bu erişim kararı hem ekranda hem sistemin arka planında aynı kaynaktan uygulanır — yalnızca ekranda gizlemekle sınırlı değildir.
- **Kurumsal hafıza:** Geçmiş dönem performans kayıtları, personel süreç geçmişi ve iletişim kayıtları arşivlenir ve erişilebilir kalır.

## 3. Kalite Yönetim Sistemi (KYS) ile ilişki

BYS360, kurumun mevcut Kalite Yönetim Sistemi'nin yerine geçen bir belge/prosedür kontrol sistemi **değildir**. Kapsamı, operasyonel insan kaynağı, performans değerlendirme, iç iletişim ve dosya paylaşım süreçlerinin dijitalleştirilmesidir. Bu nedenle BYS360, KYS'nin rakibi değil, onu tamamlayan, örtüşmeyen bir operasyonel yönetim katmanı olarak konumlandırılmalıdır.

## 4. Başlıca modüller

| Alan | Ne yapar |
|---|---|
| Personel Yönetimi | Personel kaydı, izin/devamsızlık takibi, organizasyon hiyerarşisi, vekâlet |
| Performans Yönetimi | Değerlendirme dönemi, kriter/ağırlık, çok aşamalı amir onay zinciri, düşük performans sürecinde Başkanlık onayı, karne/arşiv |
| Kurumsal Portal | Kurum içi paylaşım: duyuru, fotoğraf, video, yorum, moderasyon |
| Dosya Merkezi | Kurum içi güvenli dosya paylaşımı, misafirle kontrollü paylaşım |
| Anketler ve Nabız Yoklaması | Anket oluşturma/atama/sonuç raporlama, periyodik iç geri bildirim |
| İletişim ve Destek | Mesajlaşma, duyuru, destek/yardım talebi takibi |
| Sistem Ayarları / Yetki Matrisi | Rol ve menü yetkilerinin merkezi, canlı yönetimi |
| Yapay Zekâ Destekli Karar Desteği | Özet/öneri üretimi — nihai karar her zaman insan onayına bağlıdır |
| BYS360 Sanal Asistan | Kullanıcıya yetkisi dahilindeki ekranlara güvenli yönlendirme |
| Yönetici Özeti | Üst yönetime otomatik özet raporlama |
| Mobil Uygulama ve Tarayıcı Erişimi | Native mobil uygulama ve tarayıcı üzerinden uygulama benzeri erişim |

Tam modül envanteri, her modülün kapsamı ve mevcut durumu `docs/current_state/12_BYS360_Modul_Envanteri_ve_Fonksiyonel_Kapsam.md` belgesinde ayrıntılı olarak kayıtlıdır.

## 5. Kurumsal görsel kimlik

BYS360, tüm modüllerde tutarlı biçimde uygulanan, kurumun kendi koyu kırmızı/bordo vurgu rengini ve ay-yıldız filigranını taşıyan, resmî ve sade bir kurumsal arayüz standardına sahiptir. Bu standart, kullanıcıya teknik/geliştirici diliyle değil, anlaşılır Türkçe ifadelerle hitap edilmesini de kapsar. Ayrıntı `docs/current_state/20_BYS360_Kurumsal_Tasarim_ve_Arayuz_Standardi.md` belgesindedir.

## 6. Yönetişim ve karar destek modeli

Sistemdeki her erişim kararı, kurumun kendi belirlediği rol ve birim yetkilerine dayanır; bu kurallar merkezi bir yerden yönetilir ve değişiklikleri kendisi de kayıt altına alınır — kim, ne zaman, hangi yetkiyi değiştirdi bilgisi geri alınabilir biçimde saklanır. Yapay zekâ destekli paneller yalnızca özet ve öneri üretir; hiçbir idari karar sistemin kendisi tarafından otomatik olarak verilmez veya uygulanmaz — nihai karar her zaman yetkili bir kişiye aittir. Bu ilke, sistemin tasarımına doğrudan işlenmiştir.

## 6. Mevcut proje olgunluğu

BYS360, kurum bünyesinde canlı olarak kullanılan, sürüm kontrolü altında geliştirilen, geniş bir otomatik test tabanına (binlerce test) sahip bir sistemdir. Veritabanı değişiklikleri tek, tutarlı bir zincirle yönetilir; dağıtım paketleri bütünlük doğrulamalıdır. Sistemin teknik ve operasyonel devir dokümantasyonu ayrı bir belge setinde (`docs/current_state/`, işbu raporun teknik ekleri) hazırlanmıştır.

Bu olgunluk seviyesi, mutlak bir "tamamlandı" ifadesi olarak sunulmamaktadır — bilinen, kayıt altına alınmış açık teknik maddeler bulunmaktadır (bkz. Bölüm 8). Bu, normal bir yazılım yaşam döngüsünün parçasıdır; önemli olan bu maddelerin görünür ve izlenebilir olmasıdır.

## 7. Bu belgenin hazırlandığı aşama

Bu belge seti, **Puantaj öncesi mevcut durum dokümantasyonu** aşamasında hazırlanmıştır. Bu, projenin nihai kapanışı, uzak sunucuda sonuçlanmış (CI) bir doğrulama turu veya nihai üretim kabulü **değildir**. Bu aşamanın amacı, bir sonraki kurumsal geliştirme adımına (Puantaj) geçmeden önce sistemin mevcut durumunu dürüst, kanıta dayalı biçimde kayıt altına almaktır.

## 8. Puantaj — onaylanmış bir sonraki kurumsal geliştirme

Kurumun onayladığı proje sırasına göre, bu dokümantasyon aşamasından sonra **Puantaj (personel devam/mesai takibi)** modülünün geliştirilmesine geçilecektir. Bu modül şu anda **planlanmış ve onaylanmış bir sonraki geliştirme adımıdır**; mevcut sistemde uygulanmış bir özellik değildir. Kapsamı (aylık çizelge, normal/vardiyalı çalışma, resmî tatil, izin türleri, fazla mesai, 4/A ve 4/D istihdam statüleri, HR ve Grup Başkanı onay zinciri gibi kalemler) ayrı bir gereksinim ekinde kayıt altına alınmıştır; bazı noktalar (mevcut çizelge şablonu, vardiya saatleri, mesai ödeme kuralları gibi) kurumun kendisinden netleştirme beklemektedir.

## 9. Final kurumsal kapanıştan önce kalan adımlar

Aşağıdaki adımlar, kurumun onayladığı sıraya göre bu dokümantasyon aşamasından sonra izlenecektir:

1. Puantaj modülünün geliştirilmesi.
2. Puantaj'ın mevcut sistemle entegrasyon, güvenlik ve devir doğrulamasının tamamlanması.
3. Kalan bilinen teknik maddelerin (iç teknik defterde kayıtlı) kapatılması.
4. Bilinmeyen/henüz tespit edilmemiş defektler için son bir tarama.
5. Final kaynak kodu sürümünün kilitlenmesi ve uzak sunucuda (CI) bağımsız doğrulanması.
6. Tam kapsamlı final doğrulama koşumu.
7. Dokümantasyonun bu final duruma göre yenilenmesi.
8. Kurumsal teslim.

Bu sıralama, üst yönetimin daha önce onayladığı sıradır ve bu belge setinin tamamında tutarlı biçimde yansıtılmıştır.

## 10. Sonuç

BYS360, kurumun günlük insan kaynağı, performans ve iç iletişim işlerini dağınık araçlardan tek, denetlenebilir bir sisteme taşıyan, canlı ve kullanılmakta olan bir kurumsal yatırımdır. Mevcut aşamada bu yatırımın durumu dürüstçe belgelenmiş, bir sonraki geliştirme adımı (Puantaj) ve final kurumsal kapanışa giden yol net biçimde tanımlanmıştır.
