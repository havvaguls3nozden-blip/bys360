# Faz 9 Rollback Checklist

## Hangi durumda rollback düşünülür?
- Kritik giriş / oturum bozulması
- Veri kaybı veya kalıcı kayıt tutarsızlığı
- Export ve indirme ekranlarında zincirleme hata
- Destek kuyruğunda hızla artan kritik blokaj

## Teknik adımlar
1. Son veritabanı yedeğini doğrula.
2. Problemli release etiketini veya overlay setini tespit et.
3. Gerekirse bakım modunu aç.
4. Uygun geri dönüş paketini uygula.
5. Log ve smoke test sonuçlarını tekrar kontrol et.
6. Yönetim ve pilot kullanıcıları kısa not ile bilgilendir.

## Karar kaydı
Rollback kararı alındığında Faz 9 karar ekranına mutlaka kısa gerekçe işlenmelidir.
