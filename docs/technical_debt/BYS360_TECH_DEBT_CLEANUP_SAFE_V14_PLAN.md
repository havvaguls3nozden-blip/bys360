# SAFE V14 Planı

V13 raporuna göre ilk hedef `app/services/settings/effective_menu.py` dosyasıdır.

V14 yaklaşımı:
1. Hedef dosyadaki `except Exception` bloklarını AST ile tespit eder.
2. Zaten loglanan blokları atlar.
3. Log içermeyen blokların başına aşağıdaki güvenli ifadeleri ekler:

```python
logger = __import__("logging").getLogger(__name__)
logger.exception("BYS360 effective menu isleminde hata yakalandi")
```

4. Her ekleme sonrası hedef dosya compile edilir.
5. Compile hatası oluşursa sadece son ekleme geri alınır.
6. En sonda tam proje compile ve Quality 9 gate çalışır.
