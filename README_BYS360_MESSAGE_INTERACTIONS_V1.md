# BYS360 Message Interactions V1

Bu overlay, İletişim ve Anket Yönetimi > Mesajlar ekranına üç canlı kullanım iyileştirmesi ekler:

1. Mesajlara tepki verme: 👍, 👎, ❤️, 👏, ✅, 👀, 🙏
2. Mesaj gönderiminde sayfa yenilenmeden konuşmaya anında ekleme
3. Mesaj altına yorum yazma

## Kurulum

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_MESSAGE_INTERACTIONS_V1_ROOT_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_message_interactions_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Canlı yeniden başlatma

```powershell
cd C:\bys360\project
.\.venv\Scripts\Activate.ps1

Stop-ScheduledTask -TaskName "BYS360 Live Waitress 80" -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"
```

## Kontrol

- Mesajlar ekranında bir konuşma açın.
- Mesaj yazıp gönderin: sayfa yenilenmeden mesaj altta görünmelidir.
- Mesaj altında 👍 veya 👎 seçin: tepki sayısı anında görünmelidir.
- Yorum butonuna basıp yorum yazın: yorum mesaj altında anında görünmelidir.

## Geri alma

Uygulama öncesi dosyalar şu klasöre yedeklenir:

`backups/message_interactions_v1_<tarih_saat>/...`

Bu klasörden ilgili dosyalar proje köküne geri kopyalanarak önceki hale dönülebilir.
