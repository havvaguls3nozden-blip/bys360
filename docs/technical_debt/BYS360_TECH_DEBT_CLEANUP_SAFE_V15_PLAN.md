# BYS360 TECH DEBT CLEANUP SAFE V15

Hedef: `app/services/corporate_information_center.py` içinde yalnızca güvenli `fallback_assignment` ve `return` tipindeki broad exception bloklarına log eklemek.

Güvenlik ilkeleri:
- Tek dosya hedeflenir.
- Her ekleme sonrası hedef dosya compile edilir.
- Compile hatasında ekleme geri alınır.
- Expression, rollback, nested try gibi karmaşık bloklar manuel incelemeye bırakılır.
- Tam proje compile ve mevcut Quality 9 gate çalıştırılır.
