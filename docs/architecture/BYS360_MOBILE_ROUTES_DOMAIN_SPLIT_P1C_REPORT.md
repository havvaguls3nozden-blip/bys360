# BYS360 P1C Mobil API Domain Split Raporu

Üretim zamanı: `2026-06-09T22:15:34`

## Özet

| Alan | Değer |
|---|---:|
| İşlem sonucu | `True` |
| Değişen dosya | 7 |
| routes.py önce | 1765 satır |
| routes.py sonra | 1410 satır |
| Mobil route sözleşmesi önce | 24 |
| Mobil route sözleşmesi sonra | 24 |

## Kontroller

| Kontrol | Durum |
|---|---:|
| `p1b_marker_present` | `True` |
| `domain_dir_exists` | `True` |
| `domain_files_created` | `True` |
| `route_contract_unchanged` | `True` |
| `route_count_unchanged` | `True` |
| `routes_py_reduced` | `True` |
| `routes_py_under_1500_lines` | `True` |
| `compile_ok` | `True` |

## Domain Dosyaları

- `app/api/mobile/domains/auth.py`
- `app/api/mobile/domains/dashboard.py`
- `app/api/mobile/domains/notifications.py`
- `app/api/mobile/domains/personnel_read.py`
- `app/api/mobile/domains/support_survey_write.py`

## Not

Bu faz, P1B ile küçültülen `app/api/mobile/routes.py` dosyasından düşük riskli ilk endpoint alanlarını domain modüllerine taşır. URL ve endpoint sözleşmesi korunur; route decorator sayısı değişmemelidir.
