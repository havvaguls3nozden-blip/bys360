Doküman Adı: BYS360 Açık Teknik Madde ve Finalizasyon Defteri
Doküman Türü: İç / Teknik (Presidency'ye sunulmaz)
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

## Kapsam ve Amaç

Bu belge, BYS360'ın **iç/teknik** açık madde defteridir. Başkanlığa sunulan yönetici belgelerinde (DOC-01, DOC-17) bu maddelerin harf kodları (AA, AJ, AK, AL vb.) veya iç kayıt kimlikleri **kullanılmaz**; yönetici belgelerinde yalnızca kurumsal dille özetlenmiş risk/olgunluk ifadeleri yer alır. Bu belge, devralacak teknik ekip ve coordinator için hazırlanmıştır.

Hiçbir madde "DEFERRED FOREVER" (süresiz ertelendi) olarak işaretlenmez; kapanmamış her madde `SCHEDULED_FOR_POST_PUANTAJ_FINAL_TECHNICAL_CLOSURE` olarak sınıflandırılır — yani Puantaj geliştirmesi ve entegrasyon/güvenlik/devir doğrulamasından **sonra**, final teknik kapanış dalgasında ele alınacaktır (bkz. proje sırası, aşağıda).

---

## Proje Sırası (bağlayıcı referans)

AK kapanışı → **CURRENT-STATE kurumsal dokümantasyonu (bu faz)** → Puantaj geliştirme → Puantaj entegrasyon/güvenlik/devir doğrulama → kalan teknik/LOW/DRIFT/operasyon defteri (AL dahil) → bilinmeyen defekt taraması → final kaynak SHA → uzak CI → FINAL FULL → final dokümantasyon yenileme → kurumsal teslim.

---

## 1. Harf Kodlu Defekt Defteri (A→AL ailesi)

**Kanıt kaynağı:** `git log --oneline` (bu oturumda doğrudan çalıştırıldı) — CODE_VERIFIED.

| Kod | Konu (commit mesajından) | Durum |
|---|---|---|
| N, O | Mobil KPI performans yetkilendirme defektleri | CLOSED (commit `e25baf3`) |
| P | Mobil KPI hedef kapsam defekti | CLOSED (commit `f9cb328`) |
| Q, R | Final teslim defektleri | CLOSED (commit `b023ded`) |
| S, T, U | Performans kapsam / raporlama defektleri | CLOSED (commit `48c2ff5`, `de45e1a`, `d7320ef`) |
| V, W, X | Final teslim defektleri | CLOSED (commit `543e1ee`) |
| Y, Z | Final teslim operasyon defektleri | CLOSED (commit `3681285`) |
| AA–AI | Final teslim defektleri (toplu) | CLOSED (commit `2048926`) |
| AJ | Çapraz veritabanı şema defekti | CLOSED (commit `c3c8083`) |
| AK | Phase7 veritabanı introspeksiyon defekti | CLOSED (commit `873e6d3`, mevcut HEAD) |
| **AL** | **Çapraz veritabanı metadata-sorgu ailesi** | **AÇIK** — bu HEAD'de kapanış commiti bulunamadı. Kullanıcı brifinginde açıkça "AL ve sonraki teknik defter hâlâ mevcuttur" olarak teyit edilmiştir. |

**ID / CATEGORY:** AL / Cross-database metadata-query family
**DESCRIPTION:** AJ (çapraz veritabanı şema) ve AK (Phase7 veritabanı introspeksiyonu) ile aynı ailede, henüz kapatılmamış bir sonraki madde. Bu oturumda AL'nin tam teknik tanımı repository içinde bağımsız olarak bulunamadı (AJ/AK'nin kapanış commit gövdeleri incelenmedi — bu, kapsam dışı bir kaynak kod/geçmiş derin incelemesi gerektirir ve bu faz "NO AL FIX" kuralı gereği buna girmemiştir).
**CURRENT STATUS:** AÇIK / NOT_YET_FINALIZED
**PRODUCTION_IMPACT_KNOWN:** Bilinmiyor — bu inceleme kapsamında değerlendirilmedi.
**FINALIZATION_PHASE:** Puantaj sonrası, "kalan teknik/LOW/DRIFT/operasyon defteri" dalgası.
**CLOSURE_REQUIREMENT:** AJ/AK kapanış commitlerinin (`c3c8083`, `873e6d3`) tam diff'i okunarak AL'nin kapsamının netleştirilmesi; ardından standart remediation + test + CI doğrulama akışı.

---

## 2. Sürüm Kontrollü Teknik Borç Kaydı (`config/quality/bys360_technical_debt_registry.json`)

**Kanıt kaynağı:** CODE_VERIFIED — dosya doğrudan okundu.

Bu, harf kodlu defter ile **ayrı ve tamamlayıcı** bir sistemdir (TD-NNN / TD-CAND-NNN kimlikleri). Registry'nin kendi beyanına göre: **kayıtlı teknik borcun tamamı kapalıdır (14/14, 0 aktif)**, `BYS360-GOV-CEILING-WAIVER-001` kararı kapsamında (onay tarihi 2026-08-23). Örnek kapatılmış maddeler: TD-008 (rol matrisi regresyonu), TD-016/TD-017 (güvenlik testi/CI kapsam boşluğu), TD-032 (PostgreSQL migration zinciri bütünlüğü), TD-034/TD-036 (Scheduled Task installer / rollback script eksikliği), TD-CAND-001/002 (kopya/drift eden yardımcı fonksiyonlar ve assistant role-matrix alt sistemi — bilinçli olarak tek kanonik servise konsolide edildi).

**Önemli metodolojik not (registry'nin kendi ifadesiyle):** Bu repository'nin git geçmişi tek bir "squash" temel commit'e (`d8b50c4`, 2026-06-13) dayanır; bu tarihten önceki bir "P0=0/P1=0/P2=17/P3=21/TOTAL=38" tarihsel defter, **kurumsal karar (BYS360-GOV-LEGACY-001) ile** `HISTORICAL_UNRECONSTRUCTABLE` (tarihsel olarak yeniden inşa edilemez) olarak sınıflandırılmıştır — kaybolmuş değil, resmi olarak "asla kanıtla eşleştirilemedi" statüsünde korunmuştur. Bu, bir gizleme değil, dürüstlük ilkesiyle kayıt altına alınmış bir kurumsal karardır.

**ID / CATEGORY:** TD Registry / Governance note
**DESCRIPTION:** Registry kendi içinde 0 aktif madde bildiriyor; ancak bu current-state fazı bu iddiayı bağımsız olarak yeniden koşmadı (NO COVERAGE CAMPAIGN kısıtı).
**CURRENT STATUS:** Registry beyanına göre KAPALI (0 aktif) — DOCUMENTATION_DERIVED, bu oturumda yeniden doğrulanmadı.
**PRODUCTION_IMPACT_KNOWN:** N/A (registry kapalı beyan ediyor)
**FINALIZATION_PHASE:** Final teknik kapanış dalgasında registry'nin fresh bir gate koşumuyla yeniden teyidi önerilir.
**CLOSURE_REQUIREMENT:** `scripts/quality/bys360_technical_debt_registry_gate.py` çalıştırılarak taze doğrulama.

---

## 3. Brifingde Adı Geçen, Bu Oturumda Bağımsız Olarak Repository İçinde Birebir Bulunamayan Maddeler

Aşağıdaki maddeler bu fazın görev brifinginde açıkça adlandırılmıştır. Bu coordinator taraması, bu isimlerle **birebir eşleşen** bir kayıt/rapor bulamamıştır (repository genelinde `grep` ile arandı). Bu, maddenin var olmadığı anlamına **gelmez** — yalnızca bu oturumun onu tam ifadesiyle mekanik olarak konumlandıramadığı anlamına gelir. "Asla icat etme" kuralı gereği, bu maddeler **silinmez, ancak doğrulanmamış olarak işaretlenir.**

| ID / CATEGORY | Açıklama (brifingden) | Durum | Kanıt |
|---|---|---|---|
| Dashboard LOW | Dashboard modülünde düşük öncelikli bilinen madde | NOT_YET_FINALIZED — repository taramasında birebir bulunamadı | PRODUCTION_HISTORICAL (brifing) |
| M drift risk | Bilinmeyen bir "M" etiketli sürüklenme (drift) riski | NOT_YET_FINALIZED — repository taramasında birebir bulunamadı | PRODUCTION_HISTORICAL (brifing) |
| Mobil fail-open/drift maddeleri | Mobil girişte web'e kıyasla daha gevşek deneme sınırlaması (rate-limit) olduğu, önceki bir kurumsal raporda (`reports/executive/BYS360_Kurumsal_Rapor_Kaynak.md`, §10, eski SHA `ec4e56b` bağlamında) bilinçli kabul edilmiş bir risk olarak anılıyor. `app/services/assistant_role_matrix_v10.py:49` içinde AYRI bir yerde "fail-open olmamasi icin kapali (403) fallback" yorumu bulundu — bu, mobil giriş rate-limit maddesiyle AYNI konu DEĞİLDİR, ayrı ve zaten kapalı-tasarım bir noktadır, karıştırılmamalıdır. | REQUIRES_FINAL_REFRESH — mobil giriş rate-limit maddesi mevcut HEAD'de (`873e6d3`) bağımsız olarak yeniden doğrulanmalı | DOCUMENTATION_DERIVED (eski rapor) + CODE_VERIFIED (ilgisiz, ayrı bir fail-closed noktası) |
| Dosya Merkezi izin (permission) sürüklenmesi | Dosya Merkezi'nin 14 ayrı yetki bayrağı modeli ile ilgili olası tutarsızlık | NOT_YET_FINALIZED — repository taramasında birebir bulunamadı | PRODUCTION_HISTORICAL (brifing) |
| Dosya Merkezi audit/rollback maddeleri | Dosya Merkezi denetim kaydı veya geri alma akışıyla ilgili olası eksik | NOT_YET_FINALIZED — repository taramasında birebir bulunamadı | PRODUCTION_HISTORICAL (brifing) |
| PostgreSQL ROUND uyarısı | PostgreSQL `ROUND()` fonksiyonu ile ilgili bir tip/uyumluluk uyarısı | NOT_YET_FINALIZED — `app` altında `round(` çağrıları 15 dosyada bulundu (ör. `app/services/performance/common.py`, `app/api/mobile/domains/kpi_target_management.py`) ancak spesifik bir "PostgreSQL ROUND uyarısı" kaydı/log'u bu oturumda bulunamadı | CODE_VERIFIED (yalnızca `round(` kullanım yerleri) + PRODUCTION_HISTORICAL (brifing) |
| PT72H / RestartCount / AllowHardTerminate | Scheduled Task sertleştirme maddesi | Bkz. DOC-13 (Agent 2 tarafından script'ler doğrudan okunarak doğrulanacak) | SCRIPT_VERIFIED (Agent 2 raporunda detaylandırılacak) |

**Coordinator notu:** Final teknik kapanış dalgasında bu maddelerin her biri için kurum/geliştirme ekibiyle birlikte kaynak (hangi rapor, hangi tarih, hangi kişi bu maddeyi tanımladı) netleştirilmeli; bu current-state fazı bunu icat etmemiştir.

---

## 4. Operasyonel Gözlem — Genel Kod Sağlığı Bağlamı (bilgi amaçlı, defekt değil)

`reports/quality/BYS360_OPS_AUDIT_CI.md` (2026-08-23 üretim zamanlı, izlenmeyen/committed olmayan bir rapor): 976 Python dosyası, 0 syntax hatası, 2101 adet `except Exception` kullanımı (genel bir hata-yönetimi kalıbı, tek seferde "temizlenmemesi", dosya dosya ve davranış bozmadan ele alınması gerektiği raporun kendi notu), 35 potansiyel secret dosyası / 81 potansiyel secret eşleşmesi (bu current-state fazı bunları doğrulamadı — DOC-05/DOC-09'da Agent 3'ün güncel secret-gate bulgularıyla çapraz okunmalı).

---

## Özet Tablo

| Kategori | Açık madde sayısı (bu oturumda doğrulanan) | Sonraki adım |
|---|---|---|
| Harf kodlu defekt ailesi (A→AL) | 1 (yalnız AL) | Puantaj sonrası final teknik kapanış |
| Sürüm kontrollü TD registry | 0 (registry kendi beyanına göre) — taze doğrulama önerilir | Final teknik kapanış dalgasında `bys360_technical_debt_registry_gate.py` yeniden koşulmalı |
| Brifingde adı geçen, birebir konumlanamayan maddeler | 6 (Dashboard LOW, M drift, mobil fail-open/drift, Dosya Merkezi izin sürüklenmesi, Dosya Merkezi audit/rollback, PostgreSQL ROUND) | Kurum ile kaynak netleştirmesi + final kapanış dalgasında araştırma |
| PT72H/RestartCount/AllowHardTerminate | Agent 2 raporunda detaylandırılacak | DOC-13 |

Bu defter, Puantaj sonrası final teknik kapanış dalgasında güncellenecek, hiçbir maddesi silinmeden yalnızca durumu değiştirilecektir.
