# BYS360 OpenAPI Başlangıç Notu

Bu dosya OpenAPI/Swagger eksikliğini kapatmak için başlangıç sözleşmesini tanımlar.

## İlk belgelenecek API grupları

- Auth / oturum
- Mobil dashboard
- Bildirimler
- Profil
- Performans dönemleri
- Performans görevleri
- Karne/sonuç özeti
- Destek talepleri
- Anketler
- Asistan rehberlik uçları

## Response standardı

Başarılı cevap:

```json
{
  "ok": true,
  "data": {},
  "message": "İşlem başarıyla tamamlandı."
}
```

Hata cevabı:

```json
{
  "ok": false,
  "error_code": "PERMISSION_DENIED",
  "message": "Bu işlem için yetkiniz bulunmamaktadır."
}
```

## P1 hedefi

`docs/api/openapi_mobile_v1.yaml` dosyası gerçek endpoint envanteriyle oluşturulacak ve mobil uygulama bu sözleşmeye göre test edilecektir.
