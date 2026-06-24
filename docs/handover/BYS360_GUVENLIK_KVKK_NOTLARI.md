# BYS360 Güvenlik ve KVKK Notları

## Kapsam

BYS360 personel, performans, mesajlaşma, anket, geri bildirim, destek ve karar destek verilerini işlediği için kişisel ve kurumsal veri güvenliği esastır.

## Temel kurallar

- Gereksiz kişisel veri toplanmaz.
- Rol bazlı erişim uygulanır.
- Hassas performans verileri yayın/onay tamamlanmadan açılmaz.
- AI karar vermez; insan denetimli özet üretir.
- Kritik işlemler audit log ile izlenir.
- `.env`, DB dump ve loglar release paketine girmez.

## Erişim ilkesi

| Kullanıcı | Görünürlük |
|---|---|
| Personel | Kendi verisi ve kişi detaysız grup özeti |
| Amir | Görevli olduğu personel ve yetki kapsamı |
| Koordinatör/Grup Başkanı | Kendi organizasyon kapsamı |
| Başkan/Admin | Rolüne göre genel görünürlük |

## Olay yönetimi

Gizli bilgi sızdıysa:

1. Paylaşım durdurulur.
2. Sır döndürülür.
3. Etkilenen kullanıcı/servis tespit edilir.
4. Audit log korunur.
5. Kalıcı düzeltme yapılır.
6. Olay raporu yazılır.
