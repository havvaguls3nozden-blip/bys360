# BYS360 Kurumsal Bilgilendirme V4.0 — Akıllı Kutlama ve Otomatik İletişim Motoru

Bu overlay mevcut Kurumsal Bilgilendirme Merkezi üzerine şu özellikleri ekler:

- Otomatik doğum günü kutlaması
- Göreve başlama / hizmet yılı kutlaması
- Resmî ve kurumsal özel gün takvimi
- KVKK uyumlu mesaj üretimi: yaş/doğum yılı mesajlarda gösterilmez
- Sistem içi bildirim oluşturma desteği
- Hafta sonu kutlama görevleri için ayrı ayar
- Kutlamalar ekranı: bugün kutlanacaklar, yaklaşanlar, personel tarihleri, özel gün JSON takvimi
- Mevcut zamanlanmış görev motoruna uyumlu çalışma

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_CIC_V4_0_SMART_CELEBRATIONS_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_corporate_information_center_v4_0_smart_celebrations.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Son kontrol

```powershell
python .\scripts\quality\check_corporate_information_center_v4_0_smart_celebrations.py --project-root "C:\bys360\project"
python -m compileall app config.py scripts
```

## Sayfa

```text
/dashboard/kurumsal-bilgilendirme/kutlamalar
```

## Veritabanı

Overlay `users` tablosuna eksikse şu alanları ekler:

- `birth_date`
- `hire_date`
- `celebration_opt_out`

## Not

Otomatik gönderimler mevcut "BYS360 CIC Auto Mail Scheduler" mantığına bağlanır. Görev saatleri Kurumsal Bilgilendirme > Görevler ekranından yönetilir.
