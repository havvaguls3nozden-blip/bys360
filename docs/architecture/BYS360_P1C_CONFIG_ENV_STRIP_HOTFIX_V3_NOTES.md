# BYS360 P1C Config Env Strip HOTFIX V3

Bu paket P1C domain split sonrasında app factory smoke sırasında görülen `os.getenv(...).strip()` import hatalarını güvenli hale getirir.

- Gerçek secret üretmez veya kaynak koda yazmaz.
- Sadece no-default `os.getenv("VAR").strip()` kalıbını `(os.getenv("VAR") or "").strip()` biçimine çevirir.
- `os.getenv("VAR", "default").strip()` satırlarını güvenli kabul eder ve hata saymaz.
- Secret gate JSON çıktısını robust şekilde parse eder.
- App factory smoke için geçici subprocess env değerleri kullanır; bu değerler dosyaya yazılmaz.
