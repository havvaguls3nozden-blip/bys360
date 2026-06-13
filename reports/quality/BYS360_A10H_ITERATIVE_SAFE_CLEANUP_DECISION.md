# BYS360 A10H Iterative Safe Cleanup Kararı

Tarih: 2026-06-12T19:18:12

## Sonuç

- OK: True
- Karar: A10H_ITERATIVE_SAFE_CLEANUP_GREEN
- Quarantine root: `C:\bys360\releases\A10H_ITERATIVE_SAFE_CLEANUP_QUARANTINE_20260612_191721`
- Moved total: 91
- Missing total: 0
- Final safe quarantine candidate count: 0
- Final cleanup candidate count: 66
- Final keep or review count: 66
- Compileall returncode: 0
- Pytest returncode: 0

## Rounds

```json
[
  {
    "round": 1,
    "a10a_returncode": 0,
    "a10b_returncode": 0,
    "a10f_returncode": 0,
    "safe_candidate_count_before": 87,
    "moved_count": 87,
    "missing_count": 0,
    "cleanup_candidate_count": 136,
    "keep_or_review_count": 49,
    "by_decision": {
      "runtime_keep_rename_later": 12,
      "safe_quarantine_candidate": 87,
      "referenced_keep_review": 37
    }
  },
  {
    "round": 2,
    "a10a_returncode": 0,
    "a10b_returncode": 0,
    "a10f_returncode": 0,
    "safe_candidate_count_before": 4,
    "moved_count": 4,
    "missing_count": 0,
    "cleanup_candidate_count": 70,
    "keep_or_review_count": 66,
    "by_decision": {
      "runtime_keep_rename_later": 13,
      "referenced_keep_review": 45,
      "safe_quarantine_candidate": 4,
      "runtime_keep_manual_review": 8
    }
  },
  {
    "round": 3,
    "a10a_returncode": 0,
    "a10b_returncode": 0,
    "a10f_returncode": 0,
    "safe_candidate_count_before": 0,
    "moved_count": 0,
    "missing_count": 0,
    "cleanup_candidate_count": 66,
    "keep_or_review_count": 66,
    "by_decision": {
      "runtime_keep_rename_later": 13,
      "referenced_keep_review": 45,
      "runtime_keep_manual_review": 8
    }
  }
]
```

## Final A10F Karar Dağılımı

```json
{
  "runtime_keep_rename_later": 13,
  "referenced_keep_review": 45,
  "runtime_keep_manual_review": 8
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

## Not

Yalnızca A10F safe_quarantine_candidate sınıfı iteratif olarak karantinaya taşındı. Runtime, referanslı ve rename-later dosyalara dokunulmadı.