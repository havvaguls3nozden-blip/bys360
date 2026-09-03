# BYS360 Current-State — Belgeler Arası Tutarlılık Matrisi

Doküman Adı: BYS360 Belge Tutarlılık Matrisi
Doküman Türü: İç / Teknik (Başkanlığa sunulmaz)
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0 (v2 — dokümantasyon sertleştirme fazı, DOC-20 eklendi + literal peer-review bulguları işlendi)
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf
Son Güncelleme: 2026-09-02

---

## Yöntem

Koordinatör, `docs/current_state/` altındaki tüm belgeleri (19 belge + facts ledger, DOC-20 dahil) tam metin olarak okumuş, aşağıdaki kanonik olguların her belgede tutarlı biçimde ifade edildiğini doğrulamıştır. Bu v2 güncellemesinde, ayrıca **literal peer-review** (Agent 1↔2↔3 çapraz inceleme) yürütülmüştür — bkz. "Peer-review bulguları" bölümü. Bir hücre **UYUMLU** ise, ilgili belge bu olguyu ya doğrudan belirtir ya da hiç değinmez (çelişki yoktur, sessizlik çelişki sayılmaz).

## Bulunan ve düzeltilen çelişkiler

**1. (Coordinator-only review, önceki faz)** DOC-10 §2 ve DOC-16 §4, `postgresql-x64-15` Windows servis-adı kontrolünün `prepare_bys360_candidate.ps1`/`cutover_bys360_candidate.ps1` içinde var olduğunu iddia ediyordu. DOC-03 §3 ise bunu aramış ve bulamamıştı. Koordinatör `grep` ile doğrulamıştır: **DOC-03 doğrudur**, bu kontrol yalnızca eski/tarihsel `deploy_bys360_ec4e56b_production_v*.ps1` script'lerindedir. DOC-10/DOC-16 düzeltilmiştir. **ÇÖZÜLDÜ.**

**2-4. (Literal peer-review, bu faz)** Bkz. aşağıdaki "Peer-review bulguları" bölümü — Agent 3'ün Agent 1'in belgelerinde bulduğu 3 madde (1 FACTUAL_CONTRADICTION, 1 BROKEN_REFERENCE, 1 TERMINOLOGY_DRIFT), tümü DOC-02/DOC-12'de düzeltilmiştir. **ÇÖZÜLDÜ.**

## Ana olgu tablosu

| Olgu | Kanonik değer (FACTS LEDGER) | Doğrulayan/tutarlı belgeler | Sonuç |
|---|---|---|---|
| Application stack | Tek Flask uygulaması, tek omurga (`main_bp`) + modüler route ekleme | DOC-02, DOC-07, DOC-16 | UYUMLU |
| Python sürümü | 3.12 (pin) | DOC-02, DOC-03, DOC-07, DOC-16 | UYUMLU |
| Flask sürümü | 3.1.3 | DOC-02, DOC-07, DOC-16 | UYUMLU |
| PostgreSQL sürümü | 15 (canlı) | DOC-02, DOC-03, DOC-06, DOC-07, DOC-10, DOC-16 | UYUMLU (servis-adı kontrolü ayrımı yukarıda düzeltildi) |
| Waitress/runtime modeli | Waitress 3.0.1 + Windows Scheduled Task | DOC-02, DOC-03, DOC-04, DOC-07, DOC-13, DOC-16 | UYUMLU |
| Scheduled Task adı | "BYS360 Live Waitress 80" | DOC-03, DOC-04, DOC-13, DOC-14, DOC-15, DOC-16 | UYUMLU |
| Live domain | `bys360.canakkaletarihialan.gov.tr` (script varsayılanı, DNS doğrulanmadı) | DOC-03 (tek belirten belge) | UYUMLU (diğerleri değinmiyor, çelişki yok) |
| Health endpoints | `/healthz`, `/readyz`, `/versionz` | DOC-02, DOC-03, DOC-04, DOC-05, DOC-13, DOC-15 | UYUMLU |
| Modül isimleri | DOC-12'deki 20+ modül listesi | DOC-01, DOC-02, DOC-07, DOC-17 (yönetici belgeleri özet düzeyde) | UYUMLU |
| Auth/yetki modeli | Rol aileleri + canlı menü haritası, admin bypass yok (menü katmanında) | DOC-05, DOC-11, DOC-01/17 (özet düzeyde) | UYUMLU |
| Migration modeli | Flask-Migrate/Alembic, tek head `v1a2d3e4f5b6` | DOC-02, DOC-03, DOC-07, DOC-08, DOC-09, DOC-10 | UYUMLU |
| Release modeli | `build_bys360_safe_release.py`, SHA256+gömülü SOURCE_SHA | DOC-02, DOC-03, DOC-05, DOC-07, DOC-14 | UYUMLU |
| Rollback modeli | Alembic downgrade asla otomatik; pre/post-migration ayrımı | DOC-06, DOC-07, DOC-14, DOC-15 | UYUMLU |
| Yerel (local) SHA | `873e6d3348e644c5384a33a99c517600a3346cfd` | Tüm 18 belge (versiyon bloğunda) | UYUMLU |
| Uzak doğrulanmış SHA | `7d73ff4d468cad11d78d2339ba770f70b5ec0baf` | Tüm 18 belge (versiyon bloğunda) | UYUMLU |
| Test sonucu (LOCAL) | TRUE FULL 5684 passed/4 skipped/0 failed/0 errors | DOC-08, DOC-09 (kaynak) | UYUMLU |
| Coverage | %36,5722 (LOCAL), taban %27,62 | DOC-09 (kaynak), diğerleri atıf yapmıyor | UYUMLU |
| Puantaj statüsü | PLANLANAN / ONAYLANAN SONRAKİ GELİŞTİRME, kodda yok | DOC-01, DOC-12 (kaynak), DOC-17, DOC-18 | UYUMLU |
| Finalizasyon statüsü | Current-State 1.0, final değil, final FULL henüz üretilmedi | Tüm 18 belge (versiyon bloğu "Durum" alanı) | UYUMLU |

## Tasarım standardı olguları (DOC-20 — bu fazda eklendi)

| Olgu | Kanonik değer | Doğrulayan/tutarlı belgeler | Sonuç |
|---|---|---|---|
| DESIGN_STANDARD_STATUS | DOC-20 mevcut, Current-State 1.0, temel görsel kimlik unsurları CODE_VERIFIED, ortak bileşen ailesi/palet DESIGN_STANDARD (henüz konsolide değil) | DOC-01, DOC-02, DOC-07, DOC-08, DOC-12, DOC-16, DOC-17, DOC-18, DOC-20 (kaynak) | UYUMLU |
| PRIMARY_INSTITUTIONAL_COLOR | `#8B0000` (CODE_VERIFIED — `base_logo_refresh.css`, `analysis_center_ultra.css`, `brand_readiness_service.py`) | DOC-01, DOC-16, DOC-17, DOC-20 (kaynak) | UYUMLU |
| TECHNICAL_LANGUAGE_POLICY | Son kullanıcı ekranlarında ham geliştirici terimi yok; Türkçe kurumsal karşılık zorunlu; mevcut ekranların uyumu bu fazda taranmadı (NOT_YET_FINALIZED) | DOC-20 (kaynak), DOC-19 (açık madde olarak referanslı) | UYUMLU |
| END_USER_ERROR_LANGUAGE_POLICY | Ham exception/stack trace/API payload kullanıcıya asla gösterilmez; her modülde LoadingState/EmptyState/ErrorState/AccessDeniedState/SuccessState standardı | DOC-20 (kaynak) | UYUMLU |
| PUANTAJ_DESIGN_STATUS | Puantaj, Personel Yönetimi'nin görsel uzantısı olacak; semantik renk haritası henüz kilitlenmedi | DOC-18 §5, DOC-20 §13 | UYUMLU |
| NATIVE_MOBILE_DESIGN_STATUS | Flutter native uygulama mevcut (v2.8.87+87), "V2 tamamlandı" iddiası yok, mağaza yayın durumu NOT_YET_FINALIZED | DOC-16, DOC-20 §15 | UYUMLU |

## Peer-review bulguları (literal çapraz inceleme — bu fazda yürütüldü)

**Yöntem:** Orijinal üç specialist ajan kendi kimlikleriyle (tam bağlamla) devam ettirildi: Agent 1 (mimari/veri/modül — DOC-02/10/12/16'nın yazarı) Agent 2'nin belgelerini (03/04/06/13/14/15) inceledi; Agent 2 (kurulum/operasyon/release — DOC-03/04/06/13/14/15'in yazarı) Agent 3'ün belgelerini (05/07/08/09/11) inceledi; Agent 3 (güvenlik/devir/yönetişim — DOC-05/07/08/09/11'in yazarı) Agent 1'in belgelerini (02/10/12/16) inceledi. Her ajan yalnızca prose okumakla kalmadı, iddiaları doğrudan kod/script üzerinden yeniden doğruladı. Aşağıda **14 bulgu**, tümü koordinatör tarafından **çözüldü** olarak işaretlenmiştir.

| # | Bulgu türü | Dosya / Bölüm | Sorun (özet) | Çözüm |
|---|---|---|---|---|
| 1 | FACTUAL_CONTRADICTION | DOC-12 §3.1 (`app/auth`) | Giriş denemelerinin audit katmanınca izlendiği yanlışlıkla kesin iddia edilmişti; kod kanıtı yok | NOT_YET_FINALIZED'e çevrildi, DOC-05 §8'e atıf eklendi |
| 2 | BROKEN_REFERENCE | DOC-02 §9 madde 3 | Yetkilendirme mimarisi için yanlış atıf ("DOC-13/14") | "DOC-05/11" olarak düzeltildi |
| 3 | TERMINOLOGY_DRIFT | DOC-12 §2 tablo + §6.1 | "63 route dosyası" ifadesi yanıltıcı (59 route + 4 yardımcı dosya) | Sayı ayrıştırılarak netleştirildi |
| 4 | FACTUAL_CONTRADICTION | DOC-05 §8, DOC-11 §8 | `AuditLog`, `FileAuditLog`, `AssignmentAuditLog` — üç ayrı model, tek mekanizma gibi sunulmuştu | Üç mekanizma ayrı ayrı, doğru dosya/satır referanslarıyla yeniden yazıldı |
| 5 | STATUS_MISLABEL | DOC-08 §7 (Redis satırı) | Ledger v2'de CODE_VERIFIED olan Redis-opsiyonel bulgusu hâlâ REQUIRES_FINAL_REFRESH işaretliydi (sıralama artığı) | CODE_VERIFIED'e güncellendi, DOC-02 §6'ya atıf eklendi |
| 6 | UNSUPPORTED_CLAIM / HANDOVER_GAP | DOC-07 §2, DOC-08 §4 | `requirements.lock`/`wheelhouse`'ın eski SHA'ya (`ec4e56b`) ait olduğu açıklık notu olmadan sunulmuştu | Açıklık notu + `requirements.txt`'in iki SHA arasında bayt-bayt aynı olduğu (git diff ile doğrulanmış) mitigasyon notu eklendi |
| 7 | BROKEN_REFERENCE (küçük) | DOC-05 §12 | Sağlık uç noktası satır aralığı (`279-281`) yalnızca `__all__` dışa aktarımını içeriyordu, zayıf atıf | Satır aralığı `72-86,176-202`'ye daraltıldı |
| 8 | TERMINOLOGY_DRIFT (kozmetik) | DOC-07 §3 | "İki katmanlı rollback" ifadesi, DOC-06/14'teki "iki rollback yolu" (migration öncesi/sonrası) ile karıştırılabilir | "İki nesil script" olarak netleştirildi, açıklayıcı not eklendi |
| 9 | FACTUAL_CONTRADICTION | DOC-13 §1, DOC-15 §1 madde 4 | Waitress'in önünde **hiçbir** reverse-proxy olmadığı ima edilmişti; `ProxyFix`/`PROXY_FIX_ENABLED` (prod'da varsayılan açık) ve cutover'ın HTTPS genel kontrolü bunun tersini gösteriyor | İfade yumuşatıldı, TLS-sonlandırıcı katmanın varlığına dair dolaylı kanıt + NOT_YET_FINALIZED (katmanın kimliği bilinmiyor) olarak yeniden yazıldı |
| 10 | BROKEN_REFERENCE | DOC-04 §2 | "Belge 03 §Dizin Yapısı" — böyle bir bölüm yok | Atıf kaldırıldı, dizin yolları doğrudan listelendi + konsolidasyon eksikliği not edildi |
| 11 | BROKEN_REFERENCE | DOC-04 §10 | "Belge 06 §Shadow Rehearsal" — böyle bir bölüm yok | DOC-03 §8 / DOC-14 §4'e yeniden yönlendirildi |
| 12 | TERMINOLOGY_DRIFT | DOC-03 (kanıt anahtarı) | `REQUIRES_INSTITUTIONAL_DECISION` etiketi DOC-04/06'da kullanılıyor ama DOC-03'ün kendi anahtarında tanımlı değildi | DOC-03'ün kanıt sınıflandırma anahtarına resmî olarak eklendi |
| 13 | TERMINOLOGY_DRIFT (kozmetik) | DOC-13 §6 vs DOC-14 §5 | Faz 16a/16b için farklı fonksiyon adları (iç yardımcı vs. üst faz-fonksiyonu) — ikisi de doğru ama açıklanmamış | DOC-14 §5'e açıklayıcı ek cümle eklendi |
| 14 | HANDOVER_GAP | DOC-03 §4, DOC-15 §7 | Redis'in opsiyonel olduğu sorusu "Agent 1'e" ertelenmişti; artık DOC-02 §6'da CODE_VERIFIED olarak yanıtlanmış | Her iki belge güncellendi, doğrudan CODE_VERIFIED sonuca ve DOC-02 §6'ya atıf |

**PEER_REVIEW_FINDING_COUNT = 14, PEER_REVIEW_RESOLVED_COUNT = 14.**

## İkincil olgu tablosu (bu turda ayrıca çapraz kontrol edilen)

| Olgu | Sonuç |
|---|---|
| File Center tablo sayısı (19) | DOC-06, DOC-10, DOC-12 — üç belge bağımsızca aynı sayıyı doğrulamış | UYUMLU |
| Migration dosya sayısı (77) | DOC-07, DOC-09, DOC-10, DOC-16 — tümü 77 | UYUMLU |
| `requirements.lock`/`wheelhouse` eski SHA'ya ait | DOC-03 ("mevcut" bulgusu) + DOC-10/DOC-16 ("eski SHA'ya ait" bulgusu) — **tamamlayıcı**, çelişkili değil: ikisi de doğru, biri varlığı biri güncelliğini ele alıyor | UYUMLU |
| PT72H sertleştirmesi açık | DOC-03, DOC-13, DOC-14, DOC-19 — tümü "açık/bekliyor" | UYUMLU |
| Redis opsiyonel | DOC-02 (kaynak, CODE_VERIFIED); DOC-03/DOC-07/DOC-08/DOC-15 peer-review sırasında CODE_VERIFIED'e güncellendi (bulgu #14, #5) | UYUMLU |
| Üç-SHA belge tutarsızlığı (`873e6d3`/`7d73ff4`/`cb2e57c`) | DOC-07 §13, DOC-08 §8, DOC-09 §3, ledger — dördü de aynı üç SHA'yı tutarlı biçimde raporluyor | UYUMLU |
| PRIMARY_INSTITUTIONAL_COLOR / WATERMARK kanıtı | DOC-16 §11a, DOC-20 §2-3 — aynı dosya:satır referanslarıyla tutarlı | UYUMLU |
| Puantaj grup/soru sayımı (7/22) | DOC-18 §3 (kaynak), ledger, README — üçü de 7 grup/22 soru olarak tutarlı | UYUMLU |

## Sonuç

**CROSS_DOCUMENT_CONSISTENCY_RESULT: PASS.** 1 çelişki önceki fazda (coordinator-only review), 14 bulgu bu fazda (literal peer-review) tespit edilmiş; tümü (15/15) kaynağında düzeltilmiş ve bu matriste kayıt altına alınmıştır.
**DESIGN_CONSISTENCY_RESULT: PASS.** DOC-20 ile diğer belgeler arasında (ana renk, filigran, teknik dil politikası, Puantaj tasarım sözleşmesi, native mobil sınırı) çelişki tespit edilmemiştir.
