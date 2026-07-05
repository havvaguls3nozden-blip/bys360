# Fastfix Notları

Önceki audit scripti toplam/risk sayımı için tüm dosyaları dolaşırken, desen taraması bölümünde excluded klasörlerdeki text dosyalarını da okuyabiliyordu. Bu durum özellikle `.venv` ve build cache nedeniyle çok yavaşlayabiliyordu.

Düzeltme:
- `reason is None` olmayan dosyalarda içerik taraması yapılmaz.
- `.env`, `.git`, `.venv`, log, yerel DB, nested zip ve build cache yine risk sayımında görünür.
- Temiz kaynak adayı dosyalarda pattern/secret taraması devam eder.
