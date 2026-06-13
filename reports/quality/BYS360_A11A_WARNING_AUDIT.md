# BYS360 A11A Warning Audit

Tarih: 2026-06-12T20:30:26

## Sonuç

- OK: True
- Karar: A11A_WARNING_AUDIT_GREEN
- Pytest returncode: 0
- Extracted warning line count: 2
- Warning item count: 2

## Pytest Özeti

```json
{
  "warnings": 32,
  "passed": 744,
  "skipped": 2,
  "deselected": 34
}
```

## Warning Family Dağılımı

```json
{
  "resource_warning": 2
}
```

## Warning Category Dağılımı

```json
{
  "ResourceWarning": 2
}
```

## En Çok Warning Üreten Dosyalar

```json
{
  "C:\\bys360\\project\\app\\bootstrap\\startup.py": 2
}
```

## Gruplanmış Warning Detayı

```json
{
  "resource_warning": [
    {
      "path": "C:\\bys360\\project\\app\\bootstrap\\startup.py",
      "line_no": 22,
      "category": "ResourceWarning",
      "message": "unclosed file <_io.TextIOWrapper name='C:\\\\bys360\\\\project\\\\logs\\\\bys360-app.log' mode='a' encoding='utf-8'>",
      "family": "resource_warning",
      "fix_strategy": "Açık dosya/socket/session kapatma akışı netleştirilmeli.",
      "raw": "C:\\bys360\\project\\app\\bootstrap\\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\\\bys360\\\\project\\\\logs\\\\bys360-app.log' mode='a' encoding='utf-8'>",
      "context": "tests/test_sp_routes_smoke.py: 1 warning\n  C:\\bys360\\project\\app\\bootstrap\\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\\\bys360\\\\project\\\\logs\\\\bys360-app.log' mode='a' encoding='utf-8'>\n    configure_operational_logging(app)\n  Enable tracemalloc to get traceback where the object was allocated."
    },
    {
      "path": "C:\\bys360\\project\\app\\bootstrap\\startup.py",
      "line_no": 22,
      "category": "ResourceWarning",
      "message": "unclosed file <_io.TextIOWrapper name='C:\\\\bys360\\\\project\\\\logs\\\\bys360-ops.log' mode='a' encoding='utf-8'>",
      "family": "resource_warning",
      "fix_strategy": "Açık dosya/socket/session kapatma akışı netleştirilmeli.",
      "raw": "C:\\bys360\\project\\app\\bootstrap\\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\\\bys360\\\\project\\\\logs\\\\bys360-ops.log' mode='a' encoding='utf-8'>",
      "context": "tests/test_sp_routes_smoke.py: 1 warning\n  C:\\bys360\\project\\app\\bootstrap\\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\\\bys360\\\\project\\\\logs\\\\bys360-ops.log' mode='a' encoding='utf-8'>\n    configure_operational_logging(app)\n  Enable tracemalloc to get traceback where the object was allocated."
    }
  ]
}
```

## Sonraki Adım

A11B: En büyük warning ailesi seçilip güvenli düzeltme uygulanacak. Kod değiştirmeden önce uyarı ailesi netleşti.