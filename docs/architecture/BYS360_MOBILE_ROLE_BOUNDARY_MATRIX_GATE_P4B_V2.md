# BYS360 P4B V2 Mobile Role Boundary Matrix Gate

Bu paket, P4B rol/header/token taklidi güvenlik matrisini dinamik Flask route parametreleriyle uyumlu hale getirir.

## Ne düzeltir?

P4B ilk sürümünde runtime route map kontrolü `/api/mobile/performance/tasks/1/score-form` gibi test pathlerini Flask route haritasındaki `/api/mobile/performance/tasks/<int:assignment_id>/score-form` kuralıyla eşleştiremeyebiliyordu. V2 bu kontrolü regex tabanlı hale getirir.

## Ek güvence

- Eski aktif P4B mimari test adını P4B V2 testiyle değiştirir.
- Canlı veriye yazmaz.
- Sahte admin/personel bearer token, rol header taklidi ve malformed token senaryolarında açık 2xx, 404/405 ya da 5xx oluşmadığını denetler.
