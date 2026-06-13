# BYS360 Quality 9 CI/Test/Threshold/Auth-Session Gate

Bu paket, V1 → V2 delta raporunda görülen üç kalite açığını kapatır:

1. CI içinde `pytest` kurulup çalıştırılmaması.
2. `--max-broad-except 3500` eşiğinin gerçek uygulama kodu sayısına göre fazla gevşek kalması.
3. Auth/session/permission/security hattında sessiz veya kırılgan `except Exception` davranışlarının güvenlik riski oluşturması.

## Uygulanan değişiklikler

- GitHub Actions içine gerçek test adımı eklendi:

```yaml
- name: Run tests
  run: python -m pytest tests/ -m "ci_safe" --tb=short -q
```

- `tests/conftest.py` içine güvenli otomatik `ci_safe` işaretleme eklendi. `live`, `realdb`, `slow`, `legacy_integration` kapsamındaki testler hariç deterministik testler CI tarafından görülür.
- CI broad-except eşiği `3500` yerine `2300` yapıldı.
- Audit kapsamı `app config.py wsgi.py run.py` olarak bağlandı. Böylece backup, script ve teslim klasörü birikimi değil, yaşayan uygulama kodu ölçülür.
- `app/security/*` kritik hatlarında önceki temizlikten kalmış `exc_info=exc` ama `except Exception:` şeklindeki kırılgan bloklar `except Exception as exc:` ile güvenli hale getirildi.
- `app/security/__init__.py` içinde `logger` ilk import fallback bloklarından önce tanımlandı.
- Yeni sözleşme gate eklendi: `scripts/quality/bys360_quality9_ci_gate.py`.

## Kalite 9 hedefleri

| Kontrol | Hedef |
|---|---:|
| App print() | 0 |
| App broad except bütçesi | ≤ 2300 |
| CI pytest | Zorunlu |
| CI marker | `ci_safe` |
| Auth/session/permission/security sessiz except | 0 |
| Undefined `exc_info=exc` paterni | 0 |

## Yerel kontrol komutu

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_ci_tests_threshold_auth_session.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Testleri de yerelde çalıştırmak için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_ci_tests_threshold_auth_session.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunTests
```

## Not

Bu paket sessiz except borcunun tamamını tek hamlede kapatmaz. Öncelik auth/session/permission/security hattındaki kırılganlığı kapatmak ve CI kapısını gerçek kalite denetimi yapar hale getirmektir. Sonraki sprintlerde hedef `2300 → 2200 → 2100 → 2000` şeklinde indirilebilir.
