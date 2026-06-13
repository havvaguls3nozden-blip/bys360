# BYS360 P1D Mobil API İletişim ve Asistan Domain Split

Bu overlay, P1C sonrasında `app/api/mobile/routes.py` içinde kalan iletişim V1/V2 ve BYS360 Asistanı mobil endpoint bloklarını ayrı domain modüllerine taşır.

## Hedef

- Mobil API URL/endpoint sözleşmesini korumak.
- `routes.py` dosyasını 1000 satır altına indirmek.
- İletişim/asistan bloklarını `app/api/mobile/domains/` altında ayrıştırmak.
- App factory smoke ve secret gate ile güvenli geçişi doğrulamak.

## Oluşan dosyalar

- `app/api/mobile/domains/communication_v1_write.py`
- `app/api/mobile/domains/communication_v2_write.py`
- `app/api/mobile/domains/assistant_chat.py`

## Not

Bu paket gerçek secret yazmaz. URL sözleşmesi bozulursa işlem başarısız sayılır.
