# BYS360 STATUS.md

## 2026-07-08 â€” Devredilebilirlik TemizliÄŸi ve Kaynak Paket StandardÄ±

### Ã–zet

BYS360 kaynak aÄŸacÄ±nda devredilebilirliÄŸi dÃ¼ÅŸÃ¼ren tek kullanÄ±mlÄ±k script, iÃ§ iÃ§e proje kopyasÄ±, backup/log/instance kalÄ±ntÄ±sÄ± ve eski overlay raporlarÄ±nÄ±n ayrÄ±ÅŸtÄ±rÄ±lmasÄ± baÅŸlatÄ±ldÄ±.

### Kararlar

- Aktif `scripts/` alanÄ±nda yalnÄ±zca CI/test/dokÃ¼man tarafÄ±ndan kullanÄ±lan veya elle onaylanmÄ±ÅŸ scriptler kalacak.
- ReferanssÄ±z `ARCHIVE_CANDIDATE` scriptleri Task Scheduler kontrolÃ¼nden sonra `scripts/archive/pre_handover_YYYYMMDD/` altÄ±na taÅŸÄ±nacak.
- `project/project/`, `backups/`, `logs/`, `instance/*.sqlite*`, `.bak` ve gerÃ§ek `.env` dosyalarÄ± kaynak paketten Ã§Ä±karÄ±lacak.
- README proje tanÄ±tÄ±mÄ± ve hÄ±zlÄ± kurulum dokÃ¼manÄ± olarak yeniden yazÄ±lacak.
- STATUS gÃ¼ncel durumun tek kaynaÄŸÄ± olarak sÃ¼rdÃ¼rÃ¼lecek; her temizlik/geliÅŸtirme turunda yeni rapor yÄ±ÄŸÄ±nÄ± yerine bu dosya gÃ¼ncellenecek.

### SayÄ±sal Durum

- Script envanteri: 365 kayÄ±t
- KEEP: 49
- REVIEW: 27
- ARCHIVE_CANDIDATE: 90
- ALREADY_ARCHIVED: 199

### Sonraki Ä°ÅŸler

1. Task Scheduler raporu ile `ARCHIVE_CANDIDATE` listesini karÅŸÄ±laÅŸtÄ±r.
2. GÃ¼venli olan adaylarÄ± `git mv` ile arÅŸivle.
3. Repo gÃ¼rÃ¼ltÃ¼sÃ¼nÃ¼ temizle.
4. README ve STATUS deÄŸiÅŸikliklerini normal commit olarak iÅŸle.
5. CI ve temel smoke testleri Ã§alÄ±ÅŸtÄ±r.

## 2026-07-08 - Faz 2A SQL Identifier Trace

Kapsam:
- app/routes_president_scorecard_v2.py
- app/services/menu_visibility.py
- app/services/assistant_role_matrix_v10.py
- app/services/executive_mail_center.py
- app/schema_guard_engine.py

Sonuc:
- Kritik dosyalarda dis kullanici girdisine dogrudan bagli SQL identifier kullanimi tespit edilmedi.
- routes_president_scorecard_v2.py icinde tablo ve siralama alanlari sabit aday listeleri ve kolon kontrolu uzerinden geliyor.
- menu_visibility.py icinde tablo secimi candidate table listeleri uzerinden yapiliyor; kullanici/rol degerleri params ile baglaniyor.
- assistant_role_matrix_v10.py icinde request.form yalnizca checkbox gorunurluk degeri icin kullaniliyor; SQL kolonlari role_menu_defaults kolon kontrolu ve sabit aday kolon listeleriyle belirleniyor.
- executive_mail_center.py icinde tablo secimi sabit mail log aday listesi uzerinden yapiliyor.
- schema_guard_engine.py icinde tablo bilgisi ic schema repair/patch tanimlarindan geliyor.

Karar:
- Faz 2A kapsamindaki bes kritik dosyada acil kod degisikligi gerektiren SQL injection bulgusu yok.
- Proje genelinde dinamik SQL kullanimi yaygin oldugu icin genel SQL envanteri Faz 2A disinda ayri teknik borc basligi olarak izlenecek.

Test:
- Faz 2A read-only trace sonrasi git calisma agaci temizdi.

## 2026-07-09 - Faz 2B Login Rate Limit Trace

Kapsam:
- app/security/api_rate_limit.py
- app/security/request_guard.py
- app/auth/routes.py
- app/main_handlers/auth_handlers.py
- app/api/mobile/domains/auth.py
- app/api/mobile/services/auth_service.py

Sonuc:
- Web /login route'u app/auth/routes.py uzerinden app.main_handlers.auth_handlers.login fonksiyonuna baglidir.
- Web login akisi get_auth_throttle_state, record_auth_failure ve clear_auth_failures cagrilariyla IP/kimlik bazli throttle katmanina baglidir.
- Basarisiz girislerde CAPTCHA ve oturum bazli basarisiz giris sayaci da devrededir.
- Mobil /api/mobile/auth/login endpoint'inde ozel auth throttle gorunmedi.
- Mobil login, uygulama seviyesinde flask-limiter ile kurulan genel API rate limit katmani aktif oldugunda varsayilan uygulama limiti altinda kalir.
- app/security/api_rate_limit.py icinde varsayilan limit RATELIMIT_DEFAULT, yoksa 200 per minute olarak tanimlidir.
- App factory onceki smoke ciktisinda BYS360 API rate limit aktif logu gorulmustur.

Karar:
- Faz 2B kapsaminda acil kod degisikligi gerektiren login rate limit acigi tespit edilmedi.
- Web login PASS.
- Mobil login icin ozel throttle bulunmasa da genel API rate limit katmani nedeniyle Faz 2B kabul edilebilir PASS olarak kapatildi.
- Ileride guvenlik sertlestirme fazinda mobil auth login icin web login benzeri IP/kimlik bazli ozel throttle eklenmesi opsiyonel iyilestirme olarak izlenebilir.

Test:
- Faz 2B read-only trace sonrasi git calisma agaci temizdi.

## 2026-07-09 - Faz 2C Dependency Vulnerability Audit

Kapsam:
- pip-audit dependency vulnerability kontrolu
- Sanal ortam paket guvenlik taramasi
- pytest guvenlik guncellemesi dogrulamasi

Bulgular:
- Ilk fallback audit sonucunda pytest 8.4.2 icin PYSEC-2026-1845 acigi goruldu.
- Onerilen fix surumu pytest 9.0.3 olarak raporlandi.
- pytest sanal ortamda 9.0.3 surumune guncellendi.
- requirements.txt icinde pytest satiri bulunmadigi icin proje dependency dosyasinda degisiklik yapilmadi.
- Windows kullanici yolundaki Turkce karakter / kisa yol farki nedeniyle requirements isolated audit ilk denemede saglikli ilerlemedi; TEMP/TMP C:\bys360\tmp olarak ASCII yola alindi.
- Son pip-audit kontrolunde bilinen acik bulunmadi.

Test:
- python -m compileall app: PASS
- PYTHONPATH proje kokune alinarak app ve scripts import kontrolu: PASS
- python -m pytest -q --rootdir C:\bys360\project: 13 passed, 844 skipped
- python -m pip_audit --path .\.venv\Lib\site-packages --progress-spinner off: No known vulnerabilities found
- git calisma agaci temiz.

Karar:
- Faz 2C PASS.
- Kod dosyasi degisikligi yoktur.
- pytest guncellemesi sanal ortam guvenlik sertlestirmesi olarak uygulanmistir.

## 2026-07-09 - Faz 2D Pytest / Coverage / Skip Verification

Kapsam:
- Pytest konfigurasyonu
- Coverage esigi
- Skip nedenleri
- Full pytest calistirma

Bulgular:
- pytest.ini mevcut ve testpaths=tests olarak tanimli.
- pyproject.toml icinde coverage ayari mevcut.
- coverage fail_under = 80 olarak tanimli.
- requirements.txt icinde pytest, pytest-cov veya coverage satiri bulunmadi.
- Sanal ortamda pytest 9.0.3 mevcut.
- Sanal ortamda pytest-cov paketi bulunmadi.
- Sanal ortamda coverage paketi bulunmadi.
- PYTHONPATH proje kokune alindiginda app ve scripts import kontrolu PASS.
- python -m pytest -q --rootdir C:\bys360\project sonucu: 13 passed, 844 skipped.
- Skip nedenlerinin buyuk bolumu eski mimari sozlesme testlerinin arsiv kapsaminda olmasina bagli.
- Eski mimari sozlesme testleri BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 ile ayrica calistirilabilecek sekilde devre disi birakilmis.
- git calisma agaci temiz.

Karar:
- Faz 2D kismi PASS.
- Aktif pytest seti hatasiz geciyor.
- Coverage esigi tanimli fakat pytest-cov/coverage paketi olmadigi icin 80 coverage gate fiilen uygulanmiyor.
- 844 skipped yuksek oldugu icin test guven seviyesi tam PASS olarak degerlendirilemez.
- Coverage gate ve skip politikasinin ayrica sertlestirilmesi teknik borc olarak izlenmelidir.

Sonraki onerilen is:
- pytest-cov ve coverage paketleri kontrollu sekilde dependency dosyasina eklenmeli.
- python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=80 komutu ile gercek coverage gate calistirilmalidir.
- Legacy testlerin ayri kosumda calistirilip calistirilmamasi icin karar verilmelidir.

## 2026-07-09 - Faz 2D Coverage Gate Follow-up

Kapsam:
- pytest-cov ile gercek coverage gate denemesi
- coverage fail_under=80 esiginin uygulanabilirligi

Sonuc:
- pytest-cov ve coverage sanal ortamda kuruldu.
- Coverage komutu calistirildi:
  python -m pytest --rootdir C:\bys360\project --cov=app --cov-report=term-missing --cov-fail-under=80
- Test toplami: 857 item collected.
- Coverage gate sonucu FAIL.
- Toplam coverage: 18%.
- Hedef coverage: 80%.
- Hata: Coverage failure: total of 18 is less than fail-under=80.
- Bu nedenle Faz 2D tam PASS olarak kapatilamaz.

Karar:
- Faz 2D mevcut durumda kismi PASS / coverage FAIL.
- Aktif pytest kosumu calisiyor fakat test kapsami yetersiz.
- requirements.txt degisikligi coverage basarisiz oldugu icin commitlenmedi.
- Coverage artirma isi ayri teknik borc / test sertlestirme fazi olarak ele alinmalidir.

Sonraki onerilen is:
- Coverage hedefi icin once kritik modul bazli test kapsami artirilmali.
- Ilk hedefler: auth, security, performance core services, mobile auth, API rate limit, file/security guard modulleri.
- Tum app icin dogrudan 80 coverage hedefi mevcut test yapisiyla gercekci degildir.

## 2026-07-09 - Faz 2E API Documentation Verification

Kapsam:
- app/api klasoru envanteri
- docs/api/openapi_draft.json kontrolu
- OpenAPI / Swagger / API referans aramasi
- Mobil API route decorator kontrolu

Bulgular:
- docs/api/openapi_draft.json mevcut.
- OpenAPI surumu: 3.0.3.
- OpenAPI basligi: BYS360 API Taslak Envanteri.
- OpenAPI versiyonu: p1a-inventory.
- OpenAPI path sayisi: 820.
- OpenAPI icinde mobile path sayisi: 0.
- app/api/mobile altinda cok sayida aktif mobil API route decorator mevcut.
- Ornek mobil endpointler: /auth/login, /auth/refresh, /me, /dashboard/summary, /personnel/list, /support/tickets, /surveys ve performance endpointleri.
- API dokuman izi vardir fakat mobil API kapsam eslesmesi eksiktir.
- git calisma agaci temiz kalmistir.

Karar:
- Faz 2E kismi PASS.
- OpenAPI taslak dokumani mevcuttur.
- Mobil API endpointleri OpenAPI taslagina dahil edilmedigi icin API dokumantasyon kapsami tam PASS degildir.
- Mobil API OpenAPI coverage eksigi teknik borc olarak izlenmelidir.

Sonraki onerilen is:
- Mobil API endpointleri icin OpenAPI kapsam haritasi cikarilmali.
- En kritik ilk kapsama alinacak endpointler: auth, refresh, me, dashboard, personnel, performance, support, survey.
- API dokumani guncellenmeden once route listesi ile OpenAPI path listesi karsilastirilmalidir.

## 2026-07-09 - Faz 2F Secret Rotation / History Verification

Kapsam:
- Secret/history dokuman adaylari
- .gitignore env/secret/sqlite/instance/backups kurallari
- Git history dosya adi bazli .env izi
- Calisma agacinda takip edilmeyen env/secret/sqlite/db adaylari

Bulgular:
- docs/security/BYS360_SECRET_ROTATION_AND_HISTORY_CLEANUP_RUNBOOK.md mevcut.
- Arsivde secret release, secret sanitizer ve git history cleanup dokumanlari mevcut.
- .gitignore icinde .env, .env.*, sqlite, sqlite3, instance ve backups kurallari mevcut.
- Git history dosya adi bazli .env kontrolunde sadece .env.example ve overlay .env.example gorundu.
- Gercek .env dosyasi git history dosya adi kontrolunde gorunmedi.
- Calisma agacinda takip edilmeyen env/secret/sqlite/db adayi bulunmadi.
- git calisma agaci temiz kaldi.

Karar:
- Faz 2F kismi PASS.
- Repo hijyeni ve dokuman varligi PASS.
- Gercek secret rotation islemi bu dogrulama kapsaminda yapilmadi.
- Secret rotation canli/kurumsal sistemlerde yetki ve onay gerektiren ayri operasyon olarak kalmalidir.
- .gitignore icinde tekrar eden env/secret kurallari zararli degil, fakat ileride repo hijyeni kapsaminda sadelestirilebilir.

Sonraki onerilen is:
- Gercek secret rotation icin kurum yetkilisi/onayi ile DB, Flask secret key, mail, entegrasyon ve token anahtarlari ayri runbook uzerinden yenilenmelidir.
- Rotation yapilmadan once mevcut servis/env envanteri cikarilmalidir.

## 2026-07-09 - Faz 2 Verification Closure Summary

Kapsam:
- Faz 2A SQL identifier trace
- Faz 2B login rate limit trace
- Faz 2C dependency audit
- Faz 2D pytest / coverage verification
- Faz 2E API documentation verification
- Faz 2F secret rotation / history verification

Sonuc:
- Faz 2A PASS: SQL identifier trace tamamlandi.
- Faz 2B PASS: Login rate limit trace tamamlandi.
- Faz 2C PASS: Dependency audit tamamlandi, pip-audit sonucu temiz.
- Faz 2D kismi PASS: Aktif pytest calisiyor fakat coverage 18% ile 80 hedefinin altinda.
- Faz 2E kismi PASS: OpenAPI taslagi mevcut fakat mobil API endpointleri OpenAPI kapsaminda degil.
- Faz 2F kismi PASS: Repo hijyeni ve secret dokumanlari mevcut; gercek secret rotation ayrica yetki/onay gerektirir.
- Faz 2 boyunca calisma agaci temiz tutuldu.
- Kod degisikligi yapilmadi; bulgular STATUS.md icinde kayit altina alindi.

Genel karar:
- Faz 2 verification kapatildi.
- Faz 2 sonucunda kritik bloklayici kod hatasi tespit edilmedi.
- Kalan konular teknik borc olarak izlenmelidir.

Kalan teknik borclar:
- Coverage gate fiilen 80 hedefini karsilamiyor.
- Mobil API OpenAPI dokumantasyonu eksik.
- Gercek secret rotation kurumsal yetki/onay ile ayrica yapilmali.
- .gitignore tekrar eden env/secret kurallari ileride sadeleştirilebilir.

Sonraki onerilen is:
- Faz 3'e gecmeden once teknik borc onceligi secilmeli.
- En mantikli ilk adaylar: coverage artirma, mobil OpenAPI kapsam haritasi veya Phase 3 mimari refactor baslangici.

## 2026-07-09 - Faz 3A Mobile API OpenAPI Coverage Map

Kapsam:
- app/api/mobile altindaki mobil API route decorator envanteri
- docs/api/openapi_draft.json path listesi
- Mobil route ile OpenAPI path karsilastirmasi
- Kod degisikligi yapmadan okuma modu kontrol

Bulgular:
- Phase 2 kapanis tag'i HEAD uzerinde dogrulandi: phase2-verification-closed-20260709.
- docs/api/openapi_draft.json mevcut.
- OpenAPI path sayisi: 820.
- Mobil route decorator sayisi: 72.
- OpenAPI tarafindan kapsanan mobil route sayisi: 11.
- OpenAPI tarafinda eksik mobil route sayisi: 61.
- En buyuk eksik grup: performance, 25 route.
- Diger eksik gruplar: communication 11, kpi 4, support 4, personnel 3, push 3, assistant 2, auth 2, notifications 2.
- Kritik eksik ornekler: /api/mobile/auth/login, /api/mobile/auth/refresh, /api/mobile/me, /api/mobile/dashboard/summary, /api/mobile/personnel/list, /api/mobile/support/tickets ve cok sayida performance endpointi.
- Calisma agaci temiz kaldi.

Karar:
- Faz 3A kismi PASS.
- Mobil API OpenAPI kapsam haritasi cikarildi.
- OpenAPI dokumani var fakat mobil API kapsami yeterli degil.
- Mobil OpenAPI coverage eksigi Faz 3 teknik borcu olarak izlenmelidir.

Sonraki onerilen is:
- Mobil API OpenAPI guncellemesi tek seferde degil, kritik gruplara bolunerek yapilmalidir.
- Ilk sira: auth, me, dashboard, health, personnel, support/survey.
- Ikinci sira: performance endpointleri.
- Ucuncu sira: communication, push, notifications ve kpi endpointleri.

## 2026-07-09 - Faz 3C Mobile OpenAPI Coverage Recheck

Kapsam:
- Faz 3B sonrasi mobil API OpenAPI kapsam tekrar olcumu
- Exact /api/mobile path eslesmesi ile kontrol
- components, security ve bearerAuth varlik kontrolu
- Kod degisikligi yapmadan okuma modu dogrulama

Bulgular:
- OpenAPI path sayisi: 829.
- Mobil route decorator sayisi: 72.
- Exact OpenAPI kapsanan mobil route sayisi: 10.
- Exact OpenAPI eksik mobil route sayisi: 62.
- components mevcut.
- security mevcut.
- bearerAuth security scheme mevcut.
- /api/mobile/support/tickets path'i GET ve POST route'larini birlikte kapsadigi icin 9 path eklemesi 10 route kapsami uretmistir.
- Calisma agaci temiz kaldi.

Eksik grup ozeti:
- performance: 30
- communication: 11
- kpi: 4
- notifications: 4
- personnel: 3
- push: 3
- assistant: 2
- surveys: 2
- ai: 1
- settings: 1
- support: 1

Karar:
- Faz 3C PASS.
- Faz 3B eklemeleri OpenAPI icinde dogrulandi.
- Mobil OpenAPI kapsam borcu devam ediyor.
- En buyuk kalan borc performance endpointleri uzerindedir.

Sonraki onerilen is:
- Faz 3D icin kucuk ve dusuk riskli ikinci mobil OpenAPI paketi eklenmelidir.
- Onerilen Faz 3D kapsam: notifications, surveys, personnel ek endpointleri, support reply, ai/assistant/settings hafif okuma endpointleri.
- Performance endpointleri ayri ve daha buyuk paket olarak sonraya birakilmalidir.

## 2026-07-09 - Faz 3E Mobile OpenAPI Coverage Recheck

Kapsam:
- Faz 3D sonrasi mobil API OpenAPI kapsam tekrar olcumu
- Exact /api/mobile path eslesmesi ile kontrol
- Kalan eksik mobil endpoint gruplarinin belirlenmesi
- Kod degisikligi yapmadan okuma modu dogrulama

Bulgular:
- OpenAPI path sayisi: 847.
- Mobil route decorator sayisi: 72.
- Exact OpenAPI kapsanan mobil route sayisi: 28.
- Exact OpenAPI eksik mobil route sayisi: 44.
- Faz 3D sonrasi kapsanan mobil route sayisi 10'dan 28'e yukseldi.
- Eksik mobil route sayisi 62'den 44'e dustu.
- Kalan eksikler artik 3 ana grupta toplandi: performance, communication, kpi.
- components mevcut.
- security mevcut.
- bearerAuth security scheme mevcut.
- Calisma agaci temiz kaldi.

Kalan eksik grup ozeti:
- performance: 30
- communication: 11
- kpi: 3

Karar:
- Faz 3E PASS.
- Faz 3D eklemeleri OpenAPI kapsaminda dogrulandi.
- Hafif mobil endpointlerin buyuk kismi OpenAPI kapsamına alindi.
- Kalan OpenAPI borcu artik performance, communication ve kpi gruplarina indirgenmistir.

Sonraki onerilen is:
- Faz 3F icin communication ve kpi endpointleri birlikte kapatilabilir.
- Performance endpointleri daha buyuk oldugu icin ayri Faz 3G paketi olarak ele alinmalidir.

## 2026-07-09 - Faz 3G Mobile OpenAPI Coverage Recheck

Kapsam:
- Faz 3F sonrasi mobil API OpenAPI kapsam tekrar olcumu
- Communication ve KPI endpointlerinin OpenAPI kapsaminda dogrulanmasi
- Exact /api/mobile path eslesmesi ile kontrol
- Kod degisikligi yapmadan okuma modu dogrulama

Bulgular:
- OpenAPI path sayisi: 860.
- Mobil route decorator sayisi: 72.
- Exact OpenAPI kapsanan mobil route sayisi: 42.
- Exact OpenAPI eksik mobil route sayisi: 30.
- Kalan eksik grup sadece performance olarak goruldu.
- Communication endpointleri kapsandi.
- KPI endpointleri kapsandi.
- components mevcut.
- security mevcut.
- bearerAuth security scheme mevcut.
- Calisma agaci temiz kaldi.

Kalan eksik grup ozeti:
- performance: 30

Karar:
- Faz 3G PASS.
- Faz 3F eklemeleri OpenAPI kapsaminda dogrulandi.
- Mobil OpenAPI borcu tek gruba indirildi: performance.
- Bir sonraki adimda performance endpointleri ayri paket olarak ele alinmalidir.

Sonraki onerilen is:
- Faz 3H icin performance mobil OpenAPI paketi eklenmelidir.
- Performance paketi buyuk oldugu icin sadece dokumantasyon degisikligi yapilmali, uygulama koduna dokunulmamalidir.

## 2026-07-09 - Faz 3I Final Mobile OpenAPI Coverage

Kapsam:
- Faz 3H sonrasi final mobil API OpenAPI kapsam olcumu
- Exact /api/mobile path eslesmesi ile tum mobil route kontrolu
- OpenAPI core alanlari kontrolu
- Kod degisikligi yapmadan final dogrulama

Bulgular:
- OpenAPI path sayisi: 888.
- Mobil route decorator sayisi: 72.
- Exact OpenAPI kapsanan mobil route sayisi: 72.
- Exact OpenAPI eksik mobil route sayisi: 0.
- Missing routes: NONE.
- components mevcut.
- security mevcut.
- bearerAuth security scheme mevcut.
- Calisma agaci temiz kaldi.

Kapsanan mobil route grup ozeti:
- performance: 30
- communication: 11
- kpi: 4
- notifications: 4
- personnel: 4
- support: 4
- push: 3
- surveys: 3
- assistant: 2
- auth: 2
- ai: 1
- dashboard: 1
- health: 1
- me: 1
- settings: 1

Karar:
- Faz 3I PASS.
- Mobil OpenAPI coverage hedefi 72/72 olarak tamamlandi.
- Mobil OpenAPI dokumantasyon borcu bu faz kapsaminda kapatildi.
- Uygulama koduna dokunulmadan sadece dokumantasyon kapsami tamamlandi.

Sonraki onerilen is:
- Faz 3 final kapanis commit'i yapilmalidir.
- Ardindan branch uzerinde tag alinabilir.

## 2026-07-09 - Faz 4A Test Coverage Baseline

Kapsam:
- Faz 3 final mobil OpenAPI 72/72 kapanisi sonrasi test borcu olcumu
- pytest aktif test durumu kontrolu
- skip reason ozeti kontrolu
- coverage baseline olcumu
- Kod degisikligi yapmadan mevcut test kalitesi tespiti

Bulgular:
- pyproject.toml coverage hedefi fail_under = 80.
- docs/api/openapi_draft.json JSON validasyon PASS.
- python -m compileall app PASS.
- pytest normal run: 13 passed, 844 skipped.
- pytest_exit_code: 0.
- pytest -rs run: 13 passed, 844 skipped.
- pytest_skip_exit_code: 0.
- Skip gerekcesi agirlikli olarak eski mimari sozlesme testlerinin arsiv kapsaminda tutulmasidir.
- coverage total: 18.
- coverage gate sonucu: FAIL.
- coverage fail nedeni: total 18, fail-under 80 altinda.
- Uygulama kodu degistirilmedi.

Karar:
- Faz 4A Kismi PASS.
- Compile ve aktif pytest saglikli.
- Coverage gate FAIL durumu teknik borc olarak teyit edildi.
- En buyuk test borcu 844 skipped test ve dusuk coverage oranidir.
- Coverage hedefi dusurulmemeli; borc test aktivasyonu ve hedefli smoke/unit testlerle kapatilmalidir.

Sonraki onerilen is:
- Faz 4B icin skip mekanizmasi envanteri cikarilmalidir.
- Hangi conftest/marker/env degiskeni ile 844 testin skip edildigi netlestirilmelidir.
- Sonra kucuk bir test grubu kontrollu sekilde aktive edilmelidir.

## 2026-07-09 - Faz 4B Skip Mekanizmasi Envanteri

Kapsam:
- Faz 4A coverage baseline sonrasi skip mekanizmasi envanteri
- pytest/conftest/marker/env etkilerinin incelenmesi
- Normal collection ile legacy env collection karsilastirmasi
- Kod degisikligi yapmadan test borcu kaynaginin netlestirilmesi

Bulgular:
- Aktif branch: phase4-test-coverage-baseline-v1.
- Git durumu temiz.
- Test Python dosyasi sayisi: 158.
- Normal collection: 857 test collected.
- Legacy env collection: 857 test collected.
- normal_collect_exit_code: 0.
- legacy_collect_exit_code: 0.
- BYS360_RUN_LEGACY_ARCHITECTURE_TESTS kullanimi 2 dosyada goruldu.
- pytest.skip kullanimi 4 dosyada goruldu.
- skipif kullanimi gorulmedi.
- pytestmark kullanimi 13 dosyada goruldu.
- Ana skip mekanizmasi tests/architecture/conftest.py icindedir.
- tests/architecture/conftest.py, BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 yoksa legacy mimari testlerine skip marker eklemektedir.
- Collection sayisi degismedigi icin mekanizma test toplamayi engellemiyor; testleri collected halde skip ediyor.
- PowerShell Select-String -Recurse parametresi bu ortamda desteklenmedigi icin ilk arama blogu hata verdi; Python envanter blogu basariyla tamamlandi.
- Uygulama kodu degistirilmedi.

Karar:
- Faz 4B PASS.
- Skip borcunun ana kaynagi netlesti.
- 844 skipped testin ana sebebi collection dislama degil, conftest tabanli skip marker mekanizmasidir.
- Bir sonraki adimda tum legacy testleri birden acmak yerine kucuk ve guvenli bir test paketi secilmelidir.

Sonraki onerilen is:
- Faz 4C icin sadece kucuk bir test grubu BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 ile calistirilmalidir.
- Ilk aday grup mobil API mimari testleridir; Faz 3 OpenAPI calismasiyla dogrudan iliskilidir.

## 2026-07-09 - Faz 4C Mobil API Legacy Test Kontrollu Calistirma

Kapsam:
- Faz 4B sonrasi kucuk mobil API mimari test paketinin kontrollu calistirilmasi
- BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 ile skip edilen testlerin gercek calisma davranisinin olculmesi
- Normal mod skip davranisi ile legacy env acik davranisin karsilastirilmasi
- Kod degisikligi yapmadan test borcu kok nedeninin belirlenmesi

Test seti:
- tests/architecture/test_mobile_api_contract_p2a.py
- tests/architecture/test_mobile_api_behavior_smoke_p2b.py
- tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py
- tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py
- tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py
- tests/architecture/test_mobile_api_performance_response_p3e.py
- tests/architecture/test_mobile_api_response_suite_p3f.py

Bulgular:
- Legacy env acik collection exit code: 0.
- Legacy env acik pytest sonucu: 7 passed, 3 failed.
- faz4c_pytest_exit_code: 1.
- Normal modda ayni test seti sonucu: 7 passed, 3 skipped.
- faz4c_normal_pytest_exit_code: 0.
- docs/api/openapi_draft.json JSON validasyon PASS.
- python -m compileall app PASS.
- Git durumu temiz.
- Basarisiz testler:
  - test_mobile_api_support_survey_notifications_response_p3d.py
  - test_mobile_api_performance_response_p3e.py
  - test_mobile_api_response_suite_p3f.py
- Basarisiz testlerde direct_contract_ok veya p3_suite_ok False donmektedir.
- Ortak hata izi testing/sqlite ortaminda role_menu_defaults ve user_menu_permissions tablolarinin bulunmamasidir.
- menu_profile_access.py guarded exception uretmektedir.
- Normal modda bu testler skip edildigi icin borc daha once gorunmuyordu.

Karar:
- Faz 4C bulgu uretimli PASS.
- Mobil API legacy testleri kontrollu sekilde acilinca gercek test borcu gorunur hale geldi.
- Sorun mobil OpenAPI coverage borcu degil; test ortaminda eksik SQLite/schema/bootstrap bagimliligi gibi gorunmektedir.
- Tum legacy testleri topluca acmak yerine once bu 3 fail kok nedeni izole edilmelidir.
- Uygulama kodu degistirilmedi.

Sonraki onerilen is:
- Faz 4D icin bu 3 testin hangi run_checks sozlesme anahtarinda dustugu ayrintili izole edilmelidir.
- Ardindan test ortaminda gerekli tablo bootstrap'i mi, test beklentisi guncellemesi mi, yoksa guarded fallback iyilestirmesi mi gerektigi karar altina alinmalidir.

## 2026-07-09 - Faz 4D Mobil API Fail Izolasyon

Kapsam:
- Faz 4C sonucunda fail olan 3 mobil API legacy testinin tek tek calistirilmasi
- Ortak kok nedenin ayrintili izole edilmesi
- Kod degisikligi yapmadan test ortami/schema borcunun teyit edilmesi

Tekil test sonuclari:
- test_mobile_api_support_survey_notifications_response_p3d.py: FAIL.
- p3d_exit_code: 1.
- test_mobile_api_performance_response_p3e.py: FAIL.
- p3e_exit_code: 1.
- test_mobile_api_response_suite_p3f.py: FAIL.
- p3f_exit_code: 1.

Bulgular:
- Uc testte de ortak hata izi menu_profile_access.py icindedir.
- testing/sqlite ortaminda role_menu_defaults tablosu yoktur.
- testing/sqlite ortaminda user_menu_permissions tablosu yoktur.
- role_menu_defaults eksikligi get_role_default_menu_keys_handler icinde OperationalError uretmektedir.
- user_menu_permissions eksikligi build_effective_user_menu_context_handler icinde OperationalError uretmektedir.
- Testlerde direct_contract_ok veya p3_suite_ok False donmektedir.
- docs/api/openapi_draft.json JSON validasyon PASS.
- python -m compileall app PASS.
- Git durumu temiz.
- Uygulama kodu degistirilmedi.

Karar:
- Faz 4D bulgu uretimli PASS.
- 3 fail testin kok nedeni farkli endpoint sozlesmeleri degil, ortak testing/sqlite schema/bootstrap eksikligidir.
- Sorun mobil OpenAPI dokumantasyonu degil, legacy testlerin calistigi test veritabani hazirlik katmanidir.
- Bir sonraki adimda once model/tablo adlari ve test bootstrap akisi incelenmelidir.
- Duzeltme test tarafinda schema/bootstrap ekleme ile mi, yoksa servis fallback davranisini sessiz ve tablo-yok uyumlu hale getirme ile mi yapilacak karar altina alinmalidir.

Sonraki onerilen is:
- Faz 4E icin role_menu_defaults ve user_menu_permissions modellerinin nerede tanimlandigi bulunmalidir.
- Test app/db bootstrap akisi incelenmelidir.
- Mumkunse once test bootstrap tarafinda minimal tablo olusturma yaklasimi tercih edilmelidir.

## 2026-07-09 - Faz 4E Model ve Test Bootstrap Envanteri

Kapsam:
- Faz 4D sonrasi role_menu_defaults ve user_menu_permissions tablo/model kaynaklarinin bulunmasi
- Test bootstrap akisi ve db.create_all kullanim noktalarinin incelenmesi
- Kod degisikligi yapmadan duzeltme yonunun netlestirilmesi

Bulgular:
- Aktif branch: phase4-test-coverage-baseline-v1.
- app/models/settings_models.py icinde RoleMenuDefault modeli vardir.
- RoleMenuDefault tablosu: role_menu_defaults.
- app/models/core_models.py icinde UserMenuPermission modeli vardir.
- UserMenuPermission tablosu: user_menu_permissions.
- app.models import sonrasi db.metadata icinde 120 tablo goruldu.
- metadata_has_role_menu_defaults: True.
- metadata_has_user_menu_permissions: True.
- Metadata icindeki ilgili tablolar: role_menu_defaults, unit_menu_profiles, user_menu_permissions.
- tests/conftest.py icinde session scope app fixture vardir.
- tests/conftest.py icinde test sqlite DB yolu hazirlanmakta ve db.create_all() cagrilmaktadir.
- Buna ragmen legacy architecture run_checks akisi bu fixture bootstrap yolunu kullanmadigi icin 3 testte tablolar runtime SQLite DB icinde olusmadan sozlesme kontrolu yapiliyor gibi gorunmektedir.
- docs/api/openapi_draft.json JSON validasyon PASS.
- python -m compileall app PASS.
- Git durumu temiz.
- Uygulama kodu degistirilmedi.

Karar:
- Faz 4E bulgu uretimli PASS.
- Kok neden model tanimi eksikligi degildir.
- Sorun test calisma akisi / SQLite schema bootstrap eksikligi yonundedir.
- Runtime uygulama koduna ilk etapta dokunmak gerekmemektedir.
- En guvenli sonraki adim, legacy architecture run_checks tarafinda veya ilgili test yardimci akisi icinde minimal test DB create_all/bootstrap hazirligi saglamaktir.

Sonraki onerilen is:
- Faz 4F icin 3 fail testi calistiran run_checks kaynaklari bulunmalidir.
- Bu kaynaklarda create_app / test client / SQLite DB hazirligi nerede yapiliyor incelenmelidir.
- Sonra sadece test/architecture yardimci katmaninda minimal bootstrap duzeltmesi uygulanmalidir.

## 2026-07-11 - Faz 4F Mobil Legacy SQLite Bootstrap Denemesi V2

Kapsam:
- P3D/P3E mobil response quality gate dosyalarinda SQLite test schema hazirligi denendi.
- Ilk denemede db.create_all helper eklendi.
- Ikinci denemede file-based SQLite URL kullanimi eklendi.
- Runtime uygulama koduna dokunulmadi.

Degisen dosyalar:
- scripts/quality/bys360_mobile_support_survey_notifications_response_gate_p3d.py
- scripts/quality/bys360_mobile_performance_response_gate_p3e.py
- STATUS.md

Dogrulama sonucu:
- P3D/P3E/P3F hedef 3 test legacy env acikken halen FAIL.
- faz4f_v2_target_3_exit_code: 1.
- Hata izi halen role_menu_defaults ve user_menu_permissions tablolarinin test calisma aninda bulunmadigini gosteriyor.
- Faz 4C mobil API paketi sonraki adimda 7 passed, 3 skipped verdi; bu sonuc legacy env temizlendigi icin hedef 3 testin PASS kaniti sayilmaz.
- Dolayisiyla Faz 4F V2 PASS degildir.

Karar:
- Faz 4F V2 bulgu uretimli FAIL.
- Mevcut duzeltme tek basina yeterli olmadi.
- Sorun artik sadece sqlite memory kaliciligi olmayabilir.
- Bir sonraki adimda _build_app / _ensure_sqlite_test_schema icinde gercek engine URL, metadata tablo varligi ve sqlite_master tablo varligi dogrudan olculmelidir.
- PASS kaniti alinmadan yeni faza gecilmemelidir.

## 2026-07-11 - Faz 4F Mobil Legacy SQLite Bootstrap V3

Kapsam:
- Faz 4F V2 sonrasi helper icindeki import shadow sorunu duzeltildi.
- _ensure_sqlite_test_schema parametresi flask_app olarak netlestirildi.
- import app.models yerine importlib.import_module("app.models") kullanildi.
- Runtime uygulama koduna dokunulmadi.

Kok neden / duzelen kisim:
- import app.models satiri helper icindeki app parametresini module app ile eziyordu.
- Bu nedenle with app.app_context() Flask app yerine app modulu uzerinde calisiyordu.
- V3 ile bu shadow sorunu giderildi.
- P3D/P3E metadata role_menu_defaults ve user_menu_permissions tablolarini gordu.
- P3D/P3E sqlite_master role_menu_defaults ve user_menu_permissions tablolarini gordu.

Dogrulama sonucu:
- SQLite schema/bootstrap kismi PASS.
- P3D/P3E/P3F hedef 3 test legacy env acikken halen FAIL.
- faz4f_v3_target_3_exit_code: 1.
- P3D/P3E direct_contract_ok False donmektedir.
- P3F p3_suite_ok False donmektedir.
- Bu nedenle Faz 4F V3 genel PASS degildir.
- Faz 4C mobil API paketinin 7 passed, 3 skipped sonucu legacy env temizlendigi icin hedef 3 test icin PASS kaniti sayilmaz.

Karar:
- Faz 4F V3 bulgu uretimli PARTIAL.
- Tablo/bootstrap borcu buyuk olcude giderildi.
- Kalan sorun artik tablo yok hatasi degil, direct contract kontrolunun False donmesidir.
- Bir sonraki adimda P3D/P3E direct_contract detaylari ve beklenen/gercek route sozlesmeleri izole edilmelidir.
