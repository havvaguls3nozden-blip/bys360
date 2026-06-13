BYS360 Performans Faz 2.3 - normalize_weight_inputs export fixi

Hedef hata:
cannot import name 'normalize_weight_inputs' from 'app.services.performance_service'

Bu patch:
- performance_service.py içine normalize_weight_inputs fonksiyonunu geri ekler
- weight inputlarını toplam 100 olacak şekilde normalize eder
- geçersiz/boş değerlerde güncel güvenli default 50/50/0 kullanır

Kurulum:
1) Zip içeriğini proje köküne üstüne kopyalayın.
2) Tekrar:
   deploy\windows\start_waitress_production.bat
