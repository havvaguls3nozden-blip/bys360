# BYS360 Portal V3B8 — Sosyal Sayfa Kaldırma ve Haber Tarih Sırası

Bu paket iki sadeleştirme yapar:

1. `/portal/social-import` sosyal medya link havuzu sayfası canlı arayüzden kaldırılır.
2. `Basında Tarihi Alan` haber adayları/yayınlanan haberler tarih sırasına göre, en yeni en üstte gösterilir.

## Beklenen Sonuç

- Sol şeritte **Sosyal Medya Gönderisi Ekle** bağlantısı görünmez.
- Portal sekmelerinde **Sosyal Medya Gönderisi** sekmesi görünmez.
- Eski `/portal/social-import` adresi açılırsa `/portal/press-news` sayfasına yönlenir.
- Basında Tarihi Alan sayfasında bulunan haberler tarih sırasına göre listelenir.

## Komut

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v3b8_remove_social_and_news_order.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```
