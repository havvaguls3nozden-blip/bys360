# BYS360 P1D Mobil API İletişim ve Asistan Domain Split Raporu

Üretim zamanı: `2026-06-09T22:31:55`

## Özet

| Alan | Değer |
|---|---:|
| İşlem sonucu | `True` |
| Değişen dosya | 4 |
| routes.py önce | 1410 satır |
| routes.py sonra | 652 satır |
| Mobil route sözleşmesi önce | 24 |
| Mobil route sözleşmesi sonra | 24 |

## Kontroller

| Kontrol | Durum |
|---|---:|
| `p1c_marker_present` | `True` |
| `domain_dir_exists` | `True` |
| `p1d_domain_files_created` | `True` |
| `route_contract_unchanged` | `True` |
| `route_count_unchanged` | `True` |
| `routes_py_reduced` | `True` |
| `routes_py_under_1000_lines` | `True` |
| `compile_ok` | `True` |
| `app_factory_ok` | `True` |
| `secret_gate_ok` | `True` |

## Domain Dosyaları

- `app/api/mobile/domains/assistant_chat.py`
- `app/api/mobile/domains/auth.py`
- `app/api/mobile/domains/communication_v1_write.py`
- `app/api/mobile/domains/communication_v2_write.py`
- `app/api/mobile/domains/dashboard.py`
- `app/api/mobile/domains/notifications.py`
- `app/api/mobile/domains/personnel_read.py`
- `app/api/mobile/domains/support_survey_write.py`

## Not

Bu faz, P1C sonrası kalan iletişim V1/V2 ve BYS360 Asistanı mobil endpoint bloklarını domain modüllerine taşır. URL/endpoint sözleşmesi korunur; canlandırma app factory smoke ve secret gate ile desteklenir.
