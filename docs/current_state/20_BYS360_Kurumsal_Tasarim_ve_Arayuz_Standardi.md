Doküman Adı: BYS360 Kurumsal Tasarım ve Arayüz Standardı
Doküman Türü: Kurumsal Arayüz Tasarım Sistemi ve Uygulama Standardı
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## 0. Bu belgenin niteliği — iki katman

Bu belge iki farklı türde içerik barındırır ve bunları **açıkça ayırır**:

1. **KOD DÜZEYİNDE DOĞRULANMIŞ MEVCUT KİMLİK (`CODE_VERIFIED`)** — bugün gerçekten `app/static/`, `app/templates/` içinde var olan, bu oturumda doğrudan okunarak doğrulanan tasarım unsurları.
2. **TASARIM STANDARDI (`DESIGN_STANDARD`)** — bundan sonraki geliştirmenin (Puantaj dahil) uyması **beklenen**, bu belgeyle **kurumsallaştırılan** kural ve bileşen kavramları. Bunlar, aksi açıkça belirtilmedikçe, bugün her ekranda birebir uygulanmış olduğu anlamına **gelmez**.

Bir bileşen adı (ör. `StatCard`, `PageShell`) bu belgede geçiyorsa ve yanında dosya/kod referansı **yoksa**, bu isim **kavramsal bir tasarım standardı adıdır**, mevcut bir dosya/sınıf adı değildir — kod tabanında bu isimlerle birebir eşleşen bileşenler bu oturumda **aranmış ve bulunamamıştır**.

---

## 1. Tasarım ilkeleri

BYS360 arayüzü şu ilkelerle tanımlanır: **resmî, kurumsal, açık, tutarlı, modern, erişilebilir, geliştirici-dışı kullanıcıya uygun.** Pazarlama dili kullanılmaz. "Premium" ifadesi bu standartta bir **arayüz tasarım gereksinimi olarak kullanılmaz** — kod tabanında bazı dosya adlarında ("premium" içeren CSS/JS dosya adları, ör. `ios_pwa_premium.css`, `file_center_premium_v1kb.css`) geçtiği tespit edilmiştir, ancak bu, geliştirme sürecinin iç adlandırma alışkanlığıdır (`CODE_VERIFIED`, dosya adı taraması); bu belge bunu bir tasarım hedefi olarak **benimsemez ve tekrarlamaz**.

---

## 2. Çekirdek görsel kimlik

### 2.1 Ana kurumsal renk

**BYS360 ana koyu kırmızı / bordo kurumsal vurgu rengi: `#8B0000`.**

Bu, bu oturumda **doğrudan kod taramasıyla doğrulanmıştır** (`CODE_VERIFIED`) — icat edilmemiştir:

- `app/static/css/base_logo_refresh.css:2` — `--catab-red:#8B0000;` (adlandırılmış CSS değişkeni)
- `app/static/css/base_logo_refresh.css:224` — `--bys-hero-accent:#8B0000;`
- `app/static/css/analysis_center_ultra.css:1` — `--acu-red:#8B0000;--acu-red-dark:#640000;`
- `app/services/ui/brand_readiness_service.py:31` — kurumun kendi "marka hazırlığı" kontrol servisi, `app/templates/base.html` içinde `'#8B0000' in base_text` ifadesinin doğru olup olmadığını **otomatik olarak** kontrol eder (`sidebar_color_reference`) — yani `#8B0000`'ın sidebar/kimlik rengi olması, kod tabanının **kendisi tarafından da** doğrulanan bir sözleşmedir, yalnızca bu belgenin bir iddiası değildir.
- Onlarca ek CSS dosyasında (`ai_decision_faz9..12_routes` ekranları, `announcement_popup.css`, vb.) tutarlı biçimde tekrarlanır.

**Kullanım ilkeleri:**
- Koyu kırmızı, kurum kimliğini taşıyan omurga/navigasyon unsurları ve birincil eylemler içindir — ekranı **kaplamak** için değildir.
- Ana içerik arka planı açık ve sadedir; kırmızı, sınırlı/vurgulu biçimde kullanılır.
- Kontrast ölçülüdür; okunabilirlik her zaman önceliklidir.
- Metin/arka plan kombinasyonları erişilebilir kontrast oranını korumalıdır (bkz. §14 Erişilebilirlik).

### 2.2 İkincil/durum renkleri

Kod tabanında merkezi, tek bir "durum renk paleti" tanımı (ör. tek bir `--status-success`, `--status-danger` değişken seti) bu oturumda **bulunamamıştır** — birçok CSS dosyası kendi yerel renk değerlerini tanımlar. Bu belge, mevcut olmayan bir tam paleti **icat etmez**; bunun yerine yalnızca **semantik rolleri** tanımlar. Bu rollere karşılık gelen kesin HEX değerleri, kurumsal tasarım gözden geçirmesi sırasında ayrıca kilitlenmelidir:

| Semantik durum | Kullanım alanı |
|---|---|
| Başarılı (success) | Onaylandı, tamamlandı, kaydedildi |
| Uyarı (warning) | Dikkat gerektiren, eksik ama engelleyici olmayan durum |
| Tehlike/Hata (danger/error) | Reddedildi, başarısız, geri alınamaz eylem uyarısı |
| Bilgi (information) | Nötr bilgilendirme |
| Beklemede (pending) | Onay/işlem bekliyor |
| Onaylandı (approved) | Yetkili onayı tamamlanmış |
| Reddedildi/İade (rejected/returned) | Yetkili tarafından reddedilmiş veya iade edilmiş |
| Devre dışı (disabled) | Şu an kullanılamaz/etkileşime kapalı |

### 2.3 Tipografi — ana yazı tipi ailesi

`app/static/css/app.css:17` — `font-family:Segoe UI, Arial, sans-serif;` (`CODE_VERIFIED`). Bu, kod tabanında doğrudan tespit edilen kanonik yazı tipi yığınıdır; bu belge bunu tekrar eder, yeni bir font ailesi icat etmez.

---

## 3. Hilal-yıldız (ay-yıldız) — kurumsal filigran

Kod tabanında **doğrudan doğrulanmıştır** (`CODE_VERIFIED`):

- `app/static/css/app.css` — sabit konumlu, tam ekran bir arka plan katmanı: `background:url("../img/ay_yildiz.png") center center / 620px no-repeat; opacity:.06; pointer-events:none;` — yani görsel baskınlığı **kasıtlı olarak çok düşük** (%6 opaklık) ve **hiçbir fare/dokunma etkileşimini engellemez** (`pointer-events:none`).
- `app/services/ui/brand_readiness_service.py:32` — bu filigranın varlığı (`ay_yildiz` metninin `base.html` içinde geçmesi), kurumun kendi marka-hazırlık kontrol servisinin bir parçası olarak **otomatik denetlenir** (`watermark_reference`).
- Ayrıca `app/templates/base.html`, `login.html`, `forgot_password.html`, `scorecard_pdf.html`, `period_create.html`, `period_edit.html`, `app/services/settings/catalog.py` dosyalarında da referans bulunmaktadır (`CODE_VERIFIED`, dosya listesi).

**Kural (bu belgeyle kurumsallaştırılan standart):**
- Düşük görsel baskınlık korunmalıdır (mevcut %6 opaklık iyi bir referans noktasıdır).
- Formların ve tabloların okunabilirliğini asla bozmamalıdır.
- Dekoratif/kalabalık bir unsura dönüşmemelidir.
- Erişilebilirlik ve kontrast, filigran kullanımına her zaman önceliklidir.

---

## 4. Cam/kart (glass-card) dili — ölçülü modern yaklaşım

`app/static/css/base_logo_refresh.css` içinde `border-radius:16px` (birden fazla yerde tutarlı) ve `backdrop-filter` kullanımı **doğrudan doğrulanmıştır** (`CODE_VERIFIED`) — yani ölçülü bir yuvarlatılmış-köşe + kontrollü saydamlık yaklaşımı kod tabanında zaten mevcuttur.

**Standart:**
- Okunabilirlik her zaman önceliklidir; saydamlık yalnızca uygun olduğunda ve kontrollü biçimde kullanılır.
- Ortak köşe yarıçapı (16px referans alınabilir), ortak boşluk (spacing) ve ortak gölge hiyerarşisi kullanılır.
- Kart başlıkları tutarlı bir hiyerarşi izler.
- Kartlar görsel olarak gürültülü hale gelmemelidir.
- Veri yoğun yönetim ekranları (personel listeleri, rapor tabloları vb.) sade ve tablo-dostu kalmaya devam eder — bu ekranlarda kart dili tabloyu bastırmaz.

---

## 5. Ortak bileşen ailesi (DESIGN_STANDARD — kavramsal)

Aşağıdaki bileşen ailesi, gelecekteki geliştirmenin (Puantaj dahil) yeniden kullanması **beklenen kavramsal isimlerdir**. Bu isimler kod tabanında **birebir dosya/sınıf adı olarak bu oturumda bulunamamıştır** — bu, mevcut bir uygulama envanteri değil, bir standarttır:

`PageShell`, `PageHeader`/`SectionHeader`, `DashboardCard`, `StatCard`, `InfoCard`, `ListCard`, `ApprovalCard`, `TimelineCard`, `StatusBadge`, `FormInput`, `TextArea`, `SelectBox`, `DatePicker`, `ActionButton`, `SecondaryButton`, `DangerAction`, `ModalConfirm`, `EmptyState`, `LoadingState`, `ErrorState`, `AccessDeniedState`, `SuccessFeedback`, `Table`, `FilterBar`, `Pagination`, `Tabs`, `SearchField`, `FileUpload`.

**Mevcut paylaşılan uygulama (`CODE_VERIFIED`, kısmi):** `app/templates/base.html` tüm sayfaların ortak iskeletidir (üst navigasyon, sidebar, filigran, footer — bkz. §3); modül bazlı CSS dosyaları (`app/static/css/*.css`, 100'den fazla dosya) kendi ekranlarına özgü stil tanımlar. Bu, yukarıdaki kavramsal bileşen ailesinin **merkezi, paylaşılan bir bileşen kütüphanesi olarak henüz kod düzeyinde konsolide edilmediği** anlamına gelir — her modül kendi CSS/şablon dosyalarını büyük ölçüde bağımsız tutar. Bu belge, gelecekteki geliştirmenin bu kavramsal aileye **yakınsamasını** standart olarak koyar; mevcut durumu "zaten böyle" diye sunmaz.

---

## 6. Tipografi — hiyerarşi ve okunabilirlik kuralları

- Türkçe karakterler (ı, ğ, ş, ç, ö, ü) her ekranda doğru render edilmelidir.
- Başlık hiyerarşisi net olmalıdır (sayfa başlığı → bölüm başlığı → alt başlık).
- Font boyutu yeterli olmalı; aşırı küçük teknik etiketlerden kaçınılmalıdır.
- Performans karnelerinde ve gelecekteki Puantaj/personel tablolarında okunabilirlik özellikle önceliklidir — yoğun sayısal veri, göz yorgunluğu yaratmayacak biçimde gruplanmalıdır.
- Uzun metinler anlaşılır bölümlere ayrılmalıdır.
- Terminoloji resmî ve kurumsaldır (bkz. §9 Teknik Dil Yasağı).

---

## 7. Boşluk (spacing) ve düzen (layout) ilkeleri

- Sayfa kenar boşlukları tutarlı olmalıdır.
- Kart arası boşluk tutarlı olmalıdır.
- Dikey ritim öngörülebilir olmalıdır.
- Formlar tutarlı biçimde hizalanmalıdır.
- Tablolar taranabilirliğini (scanability) korumalıdır.
- Önemli eylemler öngörülebilir konumlarda olmalıdır.
- Yıkıcı (destructive) eylemler görsel olarak ayrıştırılmalıdır (ör. "Sil" butonu birincil eylemlerden uzak, farklı renkte).
- Mobil düzenler, masaüstünün sıkıştırılmış bir kopyası **olmamalıdır** — mobilin kendi hiyerarşisi ve navigasyonu vardır (bkz. §12).

---

## 8. Form standardı

Tüm formlar şu unsurları tutarlı biçimde içermelidir: etiketler (labels), zorunlu alan işareti, yardım metni, doğrulama (validation) mesaj stili, salt-okunur (read-only) durum, devre dışı (disabled) durum, hata (error) durumu, başarı (success) durumu, tarih/saat girişleri, dosya yükleme, onay (confirmation) akışları.

**Kritik kural:** Doğrulama hataları her zaman **açık, Türkçe, kullanıcı diliyle** yazılmalıdır — teknik/İngilizce hata metni kullanıcıya asla gösterilmez (bkz. §9).

---

## 9. Tablo standardı

Özellikle önemli olduğu alanlar: Personel, Performans, gelecekteki Puantaj, Raporlar, Onay listeleri.

**Kurallar:**
- Başlıklar açık olmalıdır.
- İşlevsel olarak gerekli olduğunda sıralama/filtreleme desteklenmelidir.
- Sütunlar okunamayacak kadar sıkışık olmamalıdır.
- Durum rozetleri (status badge) standartlaştırılmalıdır (bkz. §2.2).
- Satır eylemleri (görüntüle/düzenle/sil vb.) tutarlı bir konumda olmalıdır.
- Yatay taşma (overflow) güvenli biçimde ele alınmalıdır (ör. `overflow-x: auto` — geniş tablo kendi konteynerinde kaydırılır, sayfa geneli yatay kaymaz).
- Mobil uyarlaması tanımlı olmalıdır.
- Excel'e aktarılan (export) biçim, ekran tasarımını **belirlemez** — ekran, Excel'in sütun düzenine mahkûm değildir; ekran kullanıcı deneyimi için, Excel raporlama/arşivleme için optimize edilir.

---

## 10. Teknik dil yasağı — son kullanıcı ekranlarında ham geliştirici terimi kullanılmaz

Son kullanıcı ekranlarında şu türde ham geliştirici/sistem terimleri **gösterilmez**: faz (phase), sync, workflow state, endpoint, exception, traceback, ham JSON, `unauthorized_scope`, iç enum değerleri, veritabanı hatası, API hata payload'u.

Bunların yerine kurumsal Türkçe karşılıkları kullanılır. Örnekler (görev tanımında verilen):

| Teknik/iç terim | Kullanıcıya gösterilen Türkçe karşılık |
|---|---|
| `president_pending` | Başkan Onayı Bekliyor |
| `hr_precheck` | İK/Admin Ön Kontrolünde |
| `loading` | Veriler yükleniyor |
| erişim reddedildi (access denied) | Bu işlem için yetkiniz bulunmamaktadır |
| genel/geri alınabilir hata | Bu işlem şu anda tamamlanamadı. Lütfen tekrar deneyin. |

İç hatalar (stack trace, SQL hatası, ham exception mesajı) kullanıcıya **asla sızdırılmaz**.

**Not (dürüstlük kaydı):** Bu eşleme tablosu, görev tanımında verilen örnekleri birebir kayıt altına alır. Bu belge, mevcut her ekranın bu eşlemeye bugün zaten uyduğunu **iddia etmez** — bu, bundan sonraki geliştirme için bağlayıcı standarttır. Mevcut ekranlarda bu ilkeye aykırı örnekler bulunması durumunda, bu iç teknik defterde (`19_BYS360_Acik_Teknik_Madde_ve_Finalizasyon_Defteri.md`) ayrıca kayıt altına alınmalıdır — bu current-state fazı ekran ekran bir tarama yapmamıştır (`NOT_YET_FINALIZED`).

---

## 11. Hata / boş / yükleniyor / erişim durumları

Her modül şu standart durumları desteklemelidir: `LoadingState`, `EmptyState`, `ErrorState`, `AccessDeniedState`, `SuccessState`.

**Kural:** Hiçbir zaman açıklamasız beyaz/boş bir ekran gösterilmez. Hiçbir zaman ham stack trace gösterilmez. Hiçbir zaman teknik exception mesajı normal kullanıcıya gösterilmez.

---

## 12. Modül tutarlılığı

Aynı tasarım sistemi şu modüllerin **tamamına** uygulanır: Personel Yönetimi, Performans Yönetimi, İletişim, Anketler, Destek, Sistem Ayarları, AI Karar Desteği, Sanal Asistan, Portal, Raporlama/Dashboard, Dosya Merkezi (uygulanabilir olduğu ölçüde), mobil/API'ye yönelik arayüz, gelecekteki Puantaj, gelecekteki genişlemeler.

**Kural:** Hiçbir modül, bağımsız/ilişkisiz bir görsel dil oluşturamaz.

---

## 13. Puantaj tasarım sözleşmesi

Puantaj daha sonra uygulanacaktır. Bu belge, Puantaj'ın **Personel Yönetimi'nin doğal bir uzantısı** olarak görsel davranması gerektiğini şimdiden kayıt altına alır.

Desteklemesi gereken unsurlar: aylık tablo okunabilirliği, gün/durum hücreleri, normal çalışma, vardiyalı çalışma, izin, sağlık raporu, devamsızlık, fazla mesai, telafi izni, onay durumu, ay kilitlendi durumu, düzeltme/yeniden açma durumu, Excel içe aktarma önizlemesi, doğrulama/hata özeti, gerektiğinde istihdam-statüsü göstergeleri.

**Kural:** Bu belge, her devam/mesai türüne şimdiden **keyfi bir renk atamaz**. Nihai semantik renk haritası, Puantaj tasarım ve erişilebilirlik incelemesi sırasında ayrıca kilitlenecektir (bkz. DOC-18 §5).

---

## 14. Masaüstü / duyarlı (responsive) standart

`app/static/css/bys360_responsive_foundation_v11a.css` dosyasının varlığı, duyarlı tasarımın kod tabanında zaten bir temel katman olarak ele alındığını gösterir (`CODE_VERIFIED`, dosya varlığı — içeriği bu oturumda satır satır incelenmemiştir).

**Standart:** Masaüstü, tablet/duyarlı web ve mobil tarayıcı/PWA (uygulanabilir olduğu yerde) aynı ürün kimliğini taşır; duyarlı hiyerarşi ve kullanılabilir navigasyon korunur; tablolar bilinçli biçimde ele alınır (bkz. §9); dokunma hedefleri yeterli büyüklükte olur; yatay düzen çöküşü kullanılamaz ekranlar üretmez.

---

## 15. Native mobil sınırı

Mevcut mobil durum, DOC-16 (Teknik Envanter) belgesinden `CODE_VERIFIED` olarak devralınır: `mobile_flutter/bys360_mobile_native/` altında gerçek bir native Flutter uygulaması mevcuttur (`pubspec.yaml`: sürüm `2.8.87+87`, Flutter/Dart SDK `>=3.2.0 <4.0.0`, bağımlılıklar arasında `go_router`, `provider`, `firebase_core`, `firebase_messaging`, `flutter_secure_storage`, `webview_flutter`). **Bu belge, "Flutter-native V2 tamamlandı" gibi bir iddiada bulunmaz** — mağaza (App Store/Play Store) yayın durumu bu incelemede doğrulanamamıştır (`NOT_YET_FINALIZED`, DOC-16 ile tutarlı).

**Standart:** Gelecekteki native Flutter çalışması şunları yeniden kullanmalıdır: terminoloji, durum anlamları (bkz. §10 eşleme tablosu), görsel hiyerarşi, kurumsal renk kimliği (§2.1), hata dili, yetki mesajlaşması — ancak platforma özgü etkileşim kalıplarını (native jest/navigasyon davranışları) kullanabilir.

---

## 16. Erişilebilirlik

Asgari olarak belgelenir: okunabilir kontrast, uygulanabildiği yerde klavye kullanılabilirliği, net odak (focus) göstergesi, semantik form etiketleri, hata mesajlarının açıklığı, bilginin **yalnızca renkle** kodlanmaması (durum her zaman ayrıca metinle de ifade edilir — bkz. §2.2 semantik durum tablosu), kullanılabilir font boyutlandırma, mobil dokunma alanları, azaltılmış görsel karmaşa.

**Sertifikasyon uyarısı:** Bu belge, resmî bir WCAG sertifikasyonu **iddia etmez**. Repo içinde böyle bir sertifikasyon kanıtı bulunmamıştır.

---

## 17. İkonografi

Tutarlı bir ikon ailesi kullanılır; ikon, anlamın **tek taşıyıcısı değil, tamamlayıcısıdır** (metinle birlikte kullanılır). Yıkıcı/onay ikonları anlamsal olarak net olmalıdır. Dekoratif ikon yığılması yapılmaz. Aynı eylem, tüm modüllerde aynı ikon anlamını taşımalıdır.

---

## 18. Belge/rapor görsel kimliği (Word/PDF)

**Bu bir BELGE ÇIKTI STANDARDIDIR — mevcut üretilen Word/PDF dosyalarının bugün bu standarda uyduğuna dair bir iddia DEĞİLDİR.**

Resmî BYS360 Word/PDF raporları şu ilkelere uymalıdır: resmî kurumsal görünüm, ölçülü BYS360 koyu kırmızı vurgusu (§2.1), sade kapak, tutarlı başlıklar, ölçülü tablo başlığı vurguları, sayfa numaralandırma, belge metadata'sı, sürüm/durum bloğu (bu belge setinin kendi versiyon bloğu formatına benzer biçimde), profesyonel boşluklandırma. Sunum (slayt) gibi görünmemeli, aşırı renkli olmamalı, Başkanlık/kurumsal arşive uygun olmalıdır.

`app/templates/scorecard_pdf.html` dosyasının varlığı (`CODE_VERIFIED`), en azından bir PDF üretim şablonunun bugün mevcut olduğunu gösterir; bu şablonun yukarıdaki tüm ilkelere ne ölçüde uyduğu bu oturumda satır satır değerlendirilmemiştir (`NOT_YET_FINALIZED`).

---

## 19. Tasarım değişikliği yönetişimi

Yeni bir modül veya ekran, aşağıdakileri **bağımsız olarak yeniden tanımlayamaz**: ana kurumsal renk, buton semantiği, durum anlamları, hata dili, düzen hiyerarşisi, kullanıcıya yönelik terminoloji.

Tasarım sistemi değişiklikleri şunları gerektirir: etki incelemesi, etkilenen-modül envanteri, masaüstü/duyarlı inceleme, erişilebilirlik incelemesi, regresyon/arayüz incelemesi.

---

## Ek — Bu belgede tespit edilen, koordinatöre kayıtlı bulgular

1. Ana renk (`#8B0000`), filigran (`ay_yildiz.png`, %6 opaklık), font ailesi (`Segoe UI, Arial, sans-serif`) ve `border-radius`/`backdrop-filter` kullanımı — dördü de doğrudan kod taramasıyla `CODE_VERIFIED` olarak doğrulanmıştır. Kurumun kendi `app/services/ui/brand_readiness_service.py` servisi, ana renk ve filigranın `base.html`'de varlığını **otomatik olarak** denetlemektedir — bu, kurumun bu kimliği zaten bilinçli/resmî bir sözleşme olarak ele aldığının güçlü bir göstergesidir.
2. Ortak bileşen ailesi (§5) ve semantik renk paleti (§2.2) kesin HEX/dosya adı düzeyinde kod tabanında **henüz konsolide edilmemiştir** — bu belge bunları standart olarak koyar, mevcut envanter olarak sunmaz.
3. Mevcut ekranların §10 (teknik dil yasağı) ilkesine ne ölçüde uyduğu bu fazda ekran ekran taranmamıştır — final teslim öncesi ayrı bir tarama önerilir.
4. Word/PDF çıktı standardının (§18) mevcut `scorecard_pdf.html` ile birebir uyumu bu fazda satır satır değerlendirilmemiştir.
