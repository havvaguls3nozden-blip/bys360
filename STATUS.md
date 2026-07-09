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
