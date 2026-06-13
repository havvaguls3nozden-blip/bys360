# BYS360 A10R3 Canonical Teknik Borç Evidence Manifest

Tarih: 2026-06-12T20:05:38

## Sonuç

- OK: True
- Karar: A10R3_CANONICAL_EVIDENCE_GREEN
- Source A10R OK: True
- Source A10R2 OK: True
- ZIP: `C:\bys360\releases\BYS360_A10R3_CANONICAL_TECH_DEBT_EVIDENCE_20260612_200538.zip`
- SHA256: `CCC554AABDB390EC9A8EB315A7FDCC5887C7327F398CE71C88E36FC4F5DA3205`
- Evidence file count: 57
- ZIP entry count: 58
- Duplicate ZIP entry count: 0

## Canonical Kural

ZIP SHA256 değeri ZIP dışındaki A10R3 manifestte tutulur. ZIP içine self-referential SHA yazılmaz.

## Final A10 Sayımları

```json
{
  "safe_quarantine_candidate_count": 0,
  "referenced_keep_count": 45,
  "historical_placeholder_keep_count": 7,
  "compat_required_count": 7,
  "compat_apply_candidate_count": 3,
  "compat_keep_allowlist_count": 4,
  "compat_applied_count": 3,
  "compat_failed_count": 0,
  "unclassified_count": 0,
  "non_placeholder_low_risk_count": 0
}
```

## Pytest Özeti

```json
{
  "warnings": 32,
  "passed": 744,
  "skipped": 2,
  "deselected": 34
}
```

## Duplicate Entries

```json
[]
```

## Sonraki Faz

A11_WARNING_ZERO