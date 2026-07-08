# BYS360 Notification Email V1

Bu overlay, BYS360’da yeni bir sistem içi bildirim oluşturulduğunda bildirimin düştüğü kullanıcının kayıtlı e-posta adresine kısa bir bilgilendirme maili gönderir.

## Ne yapar?

- `Notification` modeli ile oluşturulan yeni bildirimleri merkezi dinleyiciyle yakalar.
- Bildirim commit edildikten sonra ilgili kullanıcının `users.email` adresine mail gönderir.
- Mail içeriğinde hassas detay yerine yalnızca “yeni bildiriminiz var” bilgisi ve bildirim başlığı yer alır.
- Gönderim sonucunu `mail_logs` tablosuna `system_notification_alert` tipiyle yazar.
- SMTP ayarı yoksa ana bildirim sürecini bozmaz; başarısız gönderimi mail loglarına işler.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_NOTIFICATION_EMAIL_V1_ROOT_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_notification_email_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Canlıya aldıktan sonra

Waitress’i yeniden başlatın. Yeni bildirim üretildiğinde mail loglarında `system_notification_alert` kaydı görünmelidir.

## Not

Bu overlay bildirim üretimini değiştirmez; yalnızca bildirim oluştuğunda e-posta bilgilendirme katmanı ekler.
