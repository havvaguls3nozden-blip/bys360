# BYS360_MESSAGES_RECOVERY_V1

Message Interactions V1 sonrasında mesaj ekranı beyaz sayfaya düşerse, bu paket son `message_interactions_v1_*` yedeğinden mesaj dosyalarını geri alır.

## Komut

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_MESSAGES_RECOVERY_V1_ROOT_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\recover_bys360_messages_from_interactions_v1.ps1 -ProjectRoot "C:\bys360\project" -RestartWaitress
```

## Not

Veritabanında oluşturulmuş `message_comments` tablosu kalabilir. Dosyalar eski çalışan hale döndüğü için kullanılmaz ve beyaz ekran üretmez.
