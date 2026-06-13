# Faz 7 Canlı Öncesi Son Kontrol

## Teknik kontrol
- [ ] `pytest tests/communication -q` temiz geçti
- [ ] `python scripts/communication_preflight.py` temiz geçti
- [ ] communication route dosyaları import hatası vermiyor
- [ ] export endpoint'leri hız sınırlı ve `utf-8-sig`
- [ ] feedback, phase4 ve phase5 template dosyaları eksiksiz

## Güvenlik kontrolü
- [ ] CSRF korumalı POST akışları manuel kontrol edildi
- [ ] Yetkisiz erişimlerde güvenli redirect/uyarı çalışıyor
- [ ] Dosya indirme akışları güvenli dosya çözümleyici kullanıyor
- [ ] Bildirim ve destek ekranlarında kullanıcı kapsamı doğrulandı

## Operasyon kontrolü
- [ ] Varsayılan Faz 5 verileri bootstrap edilebiliyor
- [ ] Sağlık kayıtları üretilebiliyor
- [ ] Audit log kayıtları görünür
- [ ] Kritik export'lar kullanıcıyı bekletmeden tamamlanıyor

## Karar
Bu kontrol listesi temiz ise Faz 8 pilot açılışına geçilebilir.
