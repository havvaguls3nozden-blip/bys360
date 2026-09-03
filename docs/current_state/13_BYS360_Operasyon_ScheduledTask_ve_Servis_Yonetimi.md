Doküman Adı: BYS360 Operasyon — Scheduled Task ve Servis Yönetimi
Doküman Türü: Operasyon / Windows Çalışma Zamanı
Kurum: Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
Sürüm: Current-State 1.0
Tarih: 2026-09-02
Durum: Puantaj Öncesi Mevcut Durum Dokümanı
Kaynak Kod Referansı: 873e6d3348e644c5384a33a99c517600a3346cfd
Uzak CI Referansı: 7d73ff4d468cad11d78d2339ba770f70b5ec0baf (uzaktan doğrulanmış tarihsel/mevcut kontrol noktası, yerel HEAD değil)
Son Güncelleme: 2026-09-02

---

Kanıt sınıflandırma anahtarı Belge 03 ile aynıdır.

---

## 1. Windows çalışma zamanı modeli — genel bakış

BYS360'ın canlı sunumu, **Waitress WSGI sunucusu**nu bir **Windows Scheduled Task** üzerinden, sistem başlangıcında (`AtStartup`) çalıştıran bir modele dayanır (CODE_VERIFIED — `requirements.txt`: `waitress==3.0.1`; `scripts/windows/install_bys360_live_waitress_80_task_v1.ps1`). Bu, ayrı bir Windows Service (`sc.exe create` ile kaydedilen bir servis) **değildir** — bir Scheduled Task'tir; ayrım operasyonel olarak önemlidir: `Get-Service` ile değil `Get-ScheduledTask` ile sorgulanır, `services.msc` içinde görünmez.

**Düzeltme (peer-review, Agent 1 bulgusu):** Bu bölümün önceki taslağı, Waitress'in önünde **hiçbir** reverse-proxy/servis katmanı olmadığını ima ediyordu — bu, kanıtla **çelişir**. `app/core/reverse_proxy.py` Werkzeug'ün `ProxyFix` ara katmanını (`X-Forwarded-For/Proto/Host/Port/Prefix` başlıklarını okur) devreye sokar; `config.py:655`: `PROXY_FIX_ENABLED`, `APP_ENV` production/staging'de **varsayılan olarak açıktır**. Ayrıca `cutover_bys360_candidate.ps1`, yerel (`127.0.0.1`) sağlık kontrolüne `X-Forwarded-Proto: https` başlığı enjekte eder ve **ayrıca** genel (public) uç noktayı `https://` üzerinden kontrol eder — Waitress'in kendisi yalnızca düz HTTP/80 dinlerken genel uç noktanın HTTPS olması, önünde bir **TLS sonlandırıcı reverse-proxy/yük dengeleyici katmanının bulunduğuna güçlü biçimde işaret eder**. Bu katmanın kimliği/yapılandırması (IIS, nginx, bulut yük dengeleyici vb.) bu repo'nun kapsamı dışındadır ve bu current-state fazında doğrulanamaz — **NOT_YET_FINALIZED**. Doğru ifade: "Waitress tek başına TLS sonlandırmaz; canlıda önünde bir reverse-proxy/TLS katmanı bulunduğuna dair güçlü dolaylı kanıt vardır, ancak bu katmanın kendisi bu repo'nun parçası değildir."

## 2. Görev kimliği

| Alan | Değer | Kanıt |
|---|---|---|
| Görev adı | **`BYS360 Live Waitress 80`** | SCRIPT_VERIFIED — `install_bys360_live_waitress_80_task_v1.ps1:40` (varsayılan `-TaskName`), `cutover_bys360_candidate.ps1:129`, `rollback_bys360_candidate.ps1:144` |
| Çalıştırılabilir | `powershell.exe` (bir PowerShell katmanı üzerinden gerçek Python sürecini başlatır) | CODE_VERIFIED, satır 124, 82-83 |
| Gerçek giriş noktası | `run_server.py` (proje kökünde) — geliştirme-amaçlı giriş noktası **kesinlikle kullanılmaz** | CODE_VERIFIED, satır 58-61 |
| Python yorumlayıcısı | `<ProjectRoot>\.venv\Scripts\python.exe` (varsayılan `C:\bys360\project\.venv\Scripts\python.exe`) | CODE_VERIFIED, satır 37-38 |
| Port | 80 (`$env:APP_PORT` olarak PowerShell katmanında açıkça set edilir) | CODE_VERIFIED, satır 39, 82 |
| Tetikleyici | `AtStartup` (sistem başlangıcı) | CODE_VERIFIED, satır 125 |
| Principal | `SYSTEM`, `LogonType=ServiceAccount`, `RunLevel=Highest` | CODE_VERIFIED, satır 134 |
| Ayarlar | `AllowStartIfOnBatteries`, `DontStopIfGoingOnBatteries`, `StartWhenAvailable` | CODE_VERIFIED, satır 126 |
| Log dosyası | `C:\bys360\logs\bys360_live_waitress_80.log` (append, `*>>`) | CODE_VERIFIED, satır 42, 82 |

## 3. Kurulum/güncelleme modeli — plan/apply, sessiz üzerine yazma yok

`install_bys360_live_waitress_80_task_v1.ps1`, repodaki eski `install_*.ps1` örneklerinden **bilinçli olarak farklı ve daha katı** bir güvenlik sözleşmesi taşır (script başlığı, satır 8-26, CODE_VERIFIED):

1. Varsayılan çalışma modu **yalnızca plan/dry-run**'dır — `-Apply` verilmedikçe `Register-ScheduledTask`/`Set-ScheduledTask`/`Start-ScheduledTask`/`Stop-ScheduledTask`/`Unregister-ScheduledTask`/`schtasks` **hiçbiri çağrılmaz**.
2. `-Apply` verildiğinde, aynı isimde bir görev zaten varsa **sessizce üzerine yazılmaz** — ayrıca `-ConfirmReplace` gerekir (satır 104-114).
3. Hiçbir parola/kimlik bilgisi parametresi yoktur; hiçbir gizli değer log'a/stdout'a yazılmaz.
4. `$ErrorActionPreference = "Stop"`; ön koşullar (`python.exe` ve `run_server.py` varlığı) doğrulanır, eksikse açıklayıcı `throw` ile durulur.

## 4. Başlangıç davranışı ve karakter kodlaması düzeltmesi

`run_server.py`, kendi başlangıcında stdout/stderr'i UTF-8'e yeniden yapılandırır (`_ensure_utf8_stdio`, DOCUMENTATION_DERIVED referans — bu dosyanın kendisi bu belgenin kapsamında satır satır incelenmemiştir, ancak installer script'in yorum satırları bu davranışı doğrudan referans alır). Installer script, PowerShell katmanında **ayrıca**, süreç başlamadan **önce** `$env:PYTHONUTF8='1'` ve `$env:PYTHONIOENCODING='utf-8'` set eder (satır 82, CODE_VERIFIED) — bu ikinci, bağımsız savunma katmanı, Python yorumlayıcısının ilk stdio codec seçimini de kapsar. Gerekçe: Windows Scheduled Task altında yönlendirilmiş (redirected) konsol çıktısı varsayılan olarak sistem ANSI codepage'ini (genellikle cp1252) kullanır ve bu, uygulamanın Türkçe başlangıç mesajlarını encode edemez — bu, **canlı sunucuda gerçekten yaşanmış, kök nedeni doğrulanmış** bir arızadır (`docs/handover/LIVE_INSTALLATION.md` §4, PRODUCTION_HISTORICAL, script yorumlarıyla CODE_VERIFIED tutarlı).

## 5. Yeniden başlatma / hata toleransı davranışı — ve PT72H bilinen açığı

Bu bölüm, görev talimatının özellikle vurguladığı konudur; doğrudan bu HEAD'deki script içeriği taranarak yazılmıştır.

**Grep sonucu (SCRIPT_VERIFIED, negatif):** `scripts/windows/*.ps1` dosyalarının tamamında `PT72H`, `RestartCount`, `RestartInterval`, `AllowHardTerminate`, `ExecutionTimeLimit` desenleri **aranmış, hiçbirine hiçbir dosyada rastlanmamıştır.**

`install_bys360_live_waitress_80_task_v1.ps1:126`'daki tek ayar satırı:

```powershell
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
```

Bu çağrıda `ExecutionTimeLimit`, `RestartCount`, `RestartInterval`, `AllowHardTerminate` parametreleri **belirtilmemiştir**. Windows Task Scheduler'ın `New-ScheduledTaskSettingsSet` cmdlet'i için bilinen platform varsayılanları:

- `ExecutionTimeLimit` varsayılanı **`PT72H`** (72 saat, ISO-8601 süre biçimi) — bu süre sonunda, `AllowHardTerminate` varsayılan olarak `$true` olduğundan, Task Scheduler görevi **zorla sonlandırabilir**, kalıcı bir web sunucusu görevi için istenmeyen bir davranıştır.
- `RestartCount`/`RestartInterval` varsayılanı **ayarlanmamış** (0/yok) — yani görev çökerse (Waitress süreci beklenmedik şekilde sonlanırsa), **otomatik yeniden başlatma yoktur**; görev `AtStartup` tetikleyicisiyle yalnızca bir sonraki sistem yeniden başlatmasında tekrar çalışır.

**Sınıflandırma:** Bu görev talimatının açıkça istediği gibi, bu madde **"zaten düzeltilmiş" olarak değil, AÇIK/BEKLEYEN bir operasyonel sertleştirme maddesi olarak** belgelenir. Bu HEAD'deki hiçbir script (`install_bys360_live_waitress_80_task_v1.ps1`, `cutover_bys360_candidate.ps1`, `rollback_bys360_candidate.ps1`, `prepare_bys360_candidate.ps1`) bu ayarları geçirmez veya sertleştirmez. Pratik sonucu:

- Uygulama süreci çökerse, bir operatör manuel olarak fark edip `Start-ScheduledTask` çalıştırana kadar (ya da sunucu yeniden başlatılana kadar) **canlı servis kapalı kalır**.
- Görev, varsayılan 72 saatlik çalışma süresi sınırına takılıp zorla sonlandırılabilir (teorik risk; Waitress normalde sürekli çalışan bir süreç olduğundan bu limitin gerçekte tetiklenip tetiklenmediği bu incelemede doğrulanamaz — **NOT_YET_FINALIZED**, üretim sunucusunun gerçek çalışma geçmişi operatör beyanı gerektirir).

**Öneri (bu belgenin kapsamı dışında bir uygulama değişikliği, yalnızca operasyonel not):** Bir gelecek sertleştirme dalgasında `New-ScheduledTaskSettingsSet` çağrısına `-ExecutionTimeLimit ([TimeSpan]::Zero)` (sınırsız) veya çok daha uzun bir değer, ve `-RestartCount`/`-RestartInterval` (örn. 3 deneme, 1 dakika arayla) eklenmesi düşünülebilir. Bu, kod değişikliği gerektirdiğinden bu **dokümantasyon-only** current-state fazının kapsamı dışındadır; coordinator'ın açık teknik defterine (KNOWN_OPEN_TECHNICAL_LEDGER_SUMMARY) zaten "PT72H/RestartCount/AllowHardTerminate sertleştirme" olarak işlenmiştir.

## 6. Süreç sahipliği ve DEFECT Z — sahte/eski süreç reddi

Cutover script'i, canlı servisi başlatırken (Faz 15/20) yalnızca "port 80'de bir şey dinliyor" olmasını yeterli **kabul etmez** — bu, geçmişte "DEFECT Z" olarak adlandırılan bir gerçek boşluğun kapatılmasıdır (`cutover_bys360_candidate.ps1` başlığı, satır 66-101, CODE_VERIFIED). Üç bağımsız, hepsi-zorunlu kontrol:

1. **Süreç bağlama** (`Test-ProcessBinding`): port 80'i tutan PID'nin, gerçekten yeni-tanıtılmış `$ProjectRoot` altındaki beklenen venv `python.exe` yoluna çözüldüğü, komut satırının `run_server.py`'yi referans aldığı ve sürecin başlangıç zamanının **bu koşumun kendi `Start-ScheduledTask` çağrısından sonra** olduğu doğrulanır — eski/artık kalmış bir sürecin yanlışlıkla "yeni candidate canlı" olarak kabul edilmesini engeller.
2. **Sürüm kimliği bağlama** (`Test-ReleaseIdentityBinding`, Faz 16a/20): `GET /versionz`'in (loopback'ten) `source_sha`/`migration_head` alanları, bu koşumun tanıtmayı amaçladığı candidate ile **tam eşleşmelidir**.
3. **Hazır olma kapısı** (`Test-ReadinessGate`, Faz 16b/20): `GET /readyz` hem HTTP 200 hem `status=="ready"` döndürmelidir.

Bu üç kontrolden herhangi biri başarısız olursa cutover `SUCCESS` olarak işaretlenmez.

## 7. Sağlık doğrulama

Bkz. Belge 03 §10 (tam tablo). Özet: `/healthz` (her zaman 200/ok), `/readyz` (şema durumuna göre 200/ready ya da 503/degraded), `/versionz` (genel alanlar herkese açık, `source_sha`/`migration_head` yalnızca loopback'e).

## 8. Log konumları

Bkz. Belge 04 §4 (tam tablo) — bu belgede tekrarlanmaz.

## 9. Operasyonel kontroller (görev seviyesinde)

```powershell
Get-ScheduledTask -TaskName "BYS360 Live Waitress 80" | Select-Object TaskName, State, TaskPath
Get-ScheduledTaskInfo -TaskName "BYS360 Live Waitress 80"
Get-NetTCPConnection -LocalPort 80 -State Listen
```

Bu komutlar bu belgenin kapsamında gerçek bir üretim sunucusuna karşı **çalıştırılmamıştır** — yalnızca cmdlet adları ve script'lerin kendi iç kullanımlarına (`cutover_bys360_candidate.ps1`'deki `Get-NetTCPConnection` çağrıları, satır ~825, ~1101) dayanan standart Windows Task Scheduler operasyonlarıdır.

## 10. Diğer zamanlanmış görevler

Ana canlı görevin dışında, repo içinde mail/bildirim/kurumsal-bilgi-merkezi/yönetici-özeti amaçlı çok sayıda ek görev kurulum script'i mevcuttur (bkz. Belge 04 §6, tam liste). Bu belge yalnızca ana canlı servis görevine odaklanır; diğerlerinin canlı sunucuda kurulu olup olmadığı bu current-state fazında doğrulanmamıştır.

## 11. Özet — bilinen açık madde

| Madde | Durum | Kanıt |
|---|---|---|
| PT72H execution time limit sertleştirmesi | **AÇIK** — script'te yok | SCRIPT_VERIFIED (negatif grep, `scripts/windows/*.ps1`) |
| RestartCount/RestartInterval otomatik yeniden başlatma | **AÇIK** — script'te yok | SCRIPT_VERIFIED (negatif grep) |
| AllowHardTerminate açık ayarı | **AÇIK** — script'te yok (platform varsayılanı `$true` geçerli kalıyor) | SCRIPT_VERIFIED (negatif grep) |
| Görev çarpışma koruması (sessiz üzerine yazma yok) | **UYGULANMIŞ** | CODE_VERIFIED, satır 104-114 |
| UTF-8 stdio düzeltmesi | **UYGULANMIŞ** | CODE_VERIFIED, satır 69-83 |
| Süreç/sürüm/hazır-olma üçlü bağlama (DEFECT Z) | **UYGULANMIŞ** (cutover'da) | SCRIPT_VERIFIED, `cutover_bys360_candidate.ps1` |
