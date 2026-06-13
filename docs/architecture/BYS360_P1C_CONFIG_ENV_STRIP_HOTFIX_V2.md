# BYS360 P1C Config Env Strip HOTFIX V2

Bu paket `config.py` içinde ortam değişkeni yokken import aşamasında patlayan
`os.getenv(...).strip()` kalıplarını güvenli hale getirir.

Örnek dönüşüm:

```python
os.getenv("SENTRY_DSN").strip()
```

```python
(os.getenv("SENTRY_DSN") or "").strip()
```

Gerçek secret değeri yazmaz. Sadece environment değişkeni yoksa app factory smoke'un
çökmesini engeller.
