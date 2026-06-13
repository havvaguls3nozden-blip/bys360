# İletişim Modülü Faz 1 – Route Sahipliği Overlay

Bu overlay aşağıdaki düzenlemeleri uygular:

- `app/communication/routes.py` artık uyumluluk omurgasıdır.
- `app/communication/surveys_routes.py` gerçek anket route gövdelerini içerir.
- `app/communication/announcements_routes.py` gerçek duyuru route gövdelerini içerir.
- `app/communication/shared.py` ortak zaman/direction/form yardımcılarını taşır.

## Hedef

Davranışı bozmadan route sahipliğini netleştirmek ve `route_registry` uyumluluğunu korumak.

## Not

Bu fazda URL ve endpoint isimleri korunmuştur. Mevcut menü ve template linkleri değişmez.
