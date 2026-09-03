Doküman Adı: BYS360 Puantaj Geliştirme Gereksinim Eki
Doküman Türü: Gereksinim Notu (Uygulama Belgesi DEĞİLDİR)
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## Önemli Uyarı

**Bu belge bir uygulama/geliştirme dokümanı DEĞİLDİR.** Puantaj modülü bu HEAD'de (`873e6d3`) **henüz uygulanmamıştır** — DOC-12 (Modül Envanteri) ve DOC-02 (Sistem Mimarisi) belgelerinde Puantaj, açıkça **PLANNED / APPROVED NEXT DEVELOPMENT** (planlanmış / onaylı sonraki geliştirme) olarak sınıflandırılmıştır, mevcut olarak uygulanmış bir özellik olarak DEĞİL. Bu belgenin amacı, onaylanmış/talep edilen kapsamı kayıt altına almak ve kurumdan netleştirilmesi gereken girdileri listelemektir — herhangi bir kod, veri modeli veya arayüz tasarımı içermez.

---

## 1. Onaylanmış/Talep Edilen Kapsam (İş Kalemleri)

Aşağıdaki kalemler, bu fazın görev brifinginde Puantaj'ın onaylı/talep edilen kapsamı olarak belirtilmiştir:

1. Aylık puantaj çizelgesi (monthly attendance sheet)
2. Normal çalışma modeli
3. Vardiyalı çalışma modeli
4. Resmî tatiller
5. Resmî tatilde çalışma
6. Yıllık izin
7. Diğer izin türleri
8. Saatlik izin
9. Ücretsiz izin
10. Sağlık raporları
11. Görevlendirme / saha görevi
12. Uzaktan çalışma
13. Eksik çalışma
14. Devamsızlık
15. Fazla mesai (overtime)
16. Telafi izni (compensatory leave)
17. 4/A (SGK'lı) istihdam statüsü
18. 4/D (işçi, TİS kapsamı) istihdam statüsü
19. Ek-28 (mesai/fazla çalışma ödemesi ile ilişkili düzenleme)
20. İstihdam statüsünün personel kategorisinden ayrıştırılması
21. Rapor yükleme
22. İK koordinatörü incelemesi
23. Grup Başkanı nihai onayı
24. Aylık puantaj onayı/kilidi
25. Denetim geçmişi (audit history)
26. Excel içe aktarma önizlemesi (import preview)
27. Excel dışa aktarma (export)
28. Ayrı fazla mesai–izin bakiyesi (overtime/leave balance ayrı takip)
29. Raporlama
30. Yetkilendirme
31. İzin/vekâlet/personel modülleriyle entegrasyon

**Not:** Bu liste, brifingde verilen onaylı kapsamın birebir kaydıdır; bu current-state fazı bu kalemlerin hiçbirini genişletmemiş, yorumlamamış veya teknik tasarıma dökmemiştir.

---

## 2. Mevcut Kod Tabanıyla İlişki (bu fazda yapılan tek doğrulama)

Bu current-state fazı, Puantaj'a ait bir uygulamanın mevcut kod tabanında **hâlihazırda var olup olmadığını** yüzeysel biçimde kontrol etmiştir (derin bir tasarım/kapsam analizi değildir — bu, DOC-12'yi yazan Agent 1'in görevidir). Personel/İK modülünde izin (leave) ve devam (attendance) ile ilgili bazı temel kavramların zaten mevcut olabileceği not edilir (ör. personel izin kayıtları); ancak brifingde tarif edilen kapsamdaki (vardiya modeli, Ek-28, 4/A–4/D ayrımı, aylık kilit/onay zinciri, Excel içe/dışa aktarma önizlemesi gibi) **bütünleşik bir Puantaj modülünün** bu HEAD'de var olduğuna dair bir kanıt bulunmamıştır. Bu tespit DOC-12'de Agent 1 tarafından mekanik olarak (kod okuma yoluyla) teyit edilecek/detaylandırılacaktır; burada yalnızca ön uyarı olarak kayıt altına alınmıştır.

---

## 3. Kurumdan Netleştirilmesi Gereken Girdiler (INSTITUTIONAL_INPUTS_REQUIRED)

**Sayım düzeltmesi (bu güncellemede yapıldı):** Bu belgenin ilk sürümü, kurumdan beklenen netleştirmeleri **10 satırlık düz bir tabloda** listelemişti. Bu sayım, birden fazla ayrı soruyu tek bir satırda birleştirdiği için **yanıltıcıydı** (ör. eski 6. satır "4/A personel için fazla mesai kuralları" tek başına en az 5 ayrı, bağımsız yanıt gerektiren soruyu gizliyordu). Bu bölüm, aşağıda **7 karar grubu** altında toplanan **22 ayrı, tek tek numaralandırılmış soru** olarak yeniden düzenlenmiştir. Hiçbir soru bu güncellemede yanıtlanmamış veya varsayılan bir değerle doldurulmamıştır — yalnızca sayım netleştirilmiştir.

| Grup | Grup Konusu | Soru # | Soru | Durum |
|---|---|---|---|---|
| G1 | Mevcut Excel çizelgesi | 1 | Kurumun bugün fiilen kullandığı puantaj Excel şablonunun kendisi (örnek dosya) | REQUIRES_INSTITUTIONAL_DECISION |
| G1 | Mevcut Excel çizelgesi | 2 | Excel'de kullanılan kısaltma/kod listesi (ör. hangi harf/kod hangi durumu ifade ediyor) | REQUIRES_INSTITUTIONAL_DECISION |
| G2 | Normal/vardiyalı çalışma modeli | 3 | Normal çalışma günü/saati (kurumun standart mesai saatleri) | REQUIRES_INSTITUTIONAL_DECISION |
| G2 | Normal/vardiyalı çalışma modeli | 4 | Vardiya türleri ve saatleri (kaç vardiya, başlangıç/bitiş saatleri) | REQUIRES_INSTITUTIONAL_DECISION |
| G2 | Normal/vardiyalı çalışma modeli | 5 | Vardiya planının sahibi (hangi birim/rol vardiya planını oluşturur/onaylar) | REQUIRES_INSTITUTIONAL_DECISION |
| G3 | Fazla mesai — genel süreç | 6 | Fazla mesai kaydını kimin oluşturacağı (personel mi, amir mi, İK mi) | REQUIRES_INSTITUTIONAL_DECISION |
| G3 | Fazla mesai — genel süreç | 7 | Fazla mesai onay zinciri (kim onaylar, kaç aşama) | REQUIRES_INSTITUTIONAL_DECISION |
| G4 | Ek-28 | 8 | Ek-28 dönüştürme oranı (saat/tutar katsayısı) | REQUIRES_INSTITUTIONAL_DECISION |
| G4 | Ek-28 | 9 | Ek-28 kullanım/geçerlilik süresi ve devir (carry-over) kuralı | REQUIRES_INSTITUTIONAL_DECISION |
| G4 | Ek-28 | 10 | Ek-28'in izin olarak kullanımının onay süreci | REQUIRES_INSTITUTIONAL_DECISION |
| G5 | 4/A (SGK'lı) kuralları | 11 | 4/A personel için mesai karşılığı ödeme/telafi yöntemi | REQUIRES_INSTITUTIONAL_DECISION |
| G5 | 4/A (SGK'lı) kuralları | 12 | 4/A hesaplama kuralı (saatlik/günlük katsayı vb.) | REQUIRES_INSTITUTIONAL_DECISION |
| G5 | 4/A (SGK'lı) kuralları | 13 | 4/A hafta sonu/resmî tatil çalışma kuralı | REQUIRES_INSTITUTIONAL_DECISION |
| G5 | 4/A (SGK'lı) kuralları | 14 | 4/A mesai limitleri, ödeme dönemi ve kullanım süresi | REQUIRES_INSTITUTIONAL_DECISION |
| G5 | 4/A (SGK'lı) kuralları | 15 | 4/A mesai onay makamları | REQUIRES_INSTITUTIONAL_DECISION |
| G6 | 4/D (TİS kapsamı) kuralları | 16 | 4/D normal fazla mesai / TİS hesaplama yöntemi | REQUIRES_INSTITUTIONAL_DECISION |
| G6 | 4/D (TİS kapsamı) kuralları | 17 | 4/D hafta tatili çalışma kuralı | REQUIRES_INSTITUTIONAL_DECISION |
| G6 | 4/D (TİS kapsamı) kuralları | 18 | 4/D ulusal/resmî bayram-tatil çalışma kuralı | REQUIRES_INSTITUTIONAL_DECISION |
| G6 | 4/D (TİS kapsamı) kuralları | 19 | 4/D mesainin izne çevrilme koşulları | REQUIRES_INSTITUTIONAL_DECISION |
| G6 | 4/D (TİS kapsamı) kuralları | 20 | 4/D mesai onay makamları ve limitleri | REQUIRES_INSTITUTIONAL_DECISION |
| G7 | Aylık takvim | 21 | Aylık puantaj hazırlama son tarihi (ayın kaçında hazırlanır) | REQUIRES_INSTITUTIONAL_DECISION |
| G7 | Aylık takvim | 22 | Aylık puantaj nihai onay/kilit tarihi (ayın kaçında kilitlenir) | REQUIRES_INSTITUTIONAL_DECISION |

**PUANTAJ_INSTITUTIONAL_DECISION_GROUP_COUNT = 7**
**PUANTAJ_INDIVIDUAL_UNRESOLVED_QUESTION_COUNT = 22**

**Kural:** Bu tablodaki hiçbir soru bu belgede tahmin edilmemiş veya varsayılan bir değerle doldurulmamıştır. Puantaj geliştirme fazı başlamadan önce bu 22 sorunun (7 grup altında) kurum tarafından yazılı olarak netleştirilmesi önerilir. Gruplama, sorunların konu bütünlüğünü korumak amacıyla yapılmıştır; kurum isterse bir grubun bazı sorularını yanıtlayıp diğerlerini erteleyebilir — grup, tek bir "hep ya da hiç" karar birimi değildir.

---

## 4. Bu Belgenin Kapsam Dışı Bıraktığı Konular

Aşağıdakiler, görev tanımı gereği bu belgenin ve bu fazın kapsamı dışındadır ve burada ele alınmamıştır: veri modeli/tablo tasarımı, API/route tasarımı, ekran/arayüz tasarımı, iş kuralı motoru tasarımı, test planı, migration tasarımı, entegrasyon kodu, zaman/efor tasarımı, zaman/efor tahmini. Bunlar, Puantaj geliştirme fazının kendi kapsamındadır (bkz. proje sırası — DOC-19'daki finalizasyon sırası bölümü).

## 5. Görsel Tasarım Standardıyla İlişki

Puantaj ekranları (aylık çizelge, gün/durum hücreleri, onay/kilit durumları, Excel içe aktarma önizlemesi vb.) uygulanacağı zaman, `docs/current_state/20_BYS360_Kurumsal_Tasarim_ve_Arayuz_Standardi.md` belgesinde tanımlanan kurumsal tasarım standardının **doğal bir uzantısı** olarak, Personel Yönetimi modülüyle aynı görsel dille tasarlanmalıdır. Devam/durum türlerine (normal, izin, rapor, devamsızlık, mesai vb.) atanacak nihai semantik renk haritası, bu belgede önceden belirlenmemiştir — Puantaj tasarım ve erişilebilirlik incelemesi sırasında ayrıca kilitlenecektir (bkz. DOC-20 "Puantaj Tasarım Sözleşmesi" bölümü).
