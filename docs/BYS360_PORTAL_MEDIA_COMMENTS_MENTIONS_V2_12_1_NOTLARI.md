# BYS360 Portal V2.12.1

Bu overlay aşağıdaki portal geliştirmelerini içerir:

- Portal paylaşım medya sınırı 50 MB olarak güncellendi.
- Paylaşıma MP4, WEBM, MOV ve M4V video dosyası ekleme desteği eklendi.
- YouTube/Vimeo bağlantısı desteği korunur.
- Yorumlara cevap verme desteği eklendi.
- Yorum ve cevaplarda `@` ile personel etiketleme öneri listesi eklendi.
- Etiketlenen kullanıcılar ve yorumuna cevap gelen kullanıcılar için sistem içi bildirim üretimi eklendi.
- Yetki/görünürlük sınırı korunur; paylaşımı göremeyecek kullanıcıya etiket bildirimi üretilmez.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_media_comments_mentions_v2_12_1.ps1 -ProjectRoot "C:\bys360\project"
```

Sadece kaynak kontrolü yapılacaksa:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_portal_media_comments_mentions_v2_12_1.ps1 -ProjectRoot "C:\bys360\project"
```
