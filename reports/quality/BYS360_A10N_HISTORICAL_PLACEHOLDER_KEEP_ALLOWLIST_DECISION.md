# BYS360 A10N Historical Placeholder Keep Allowlist Kararı

Tarih: 2026-06-12T19:44:21

## Sonuç

- OK: True
- Karar: A10N_HISTORICAL_PLACEHOLDER_KEEP_ALLOWLIST_GREEN
- A10M OK: True
- Compileall returncode: 0
- Pytest returncode: 0
- A10F safe quarantine candidate count: 0
- A10F cleanup candidate count: 59
- A10I remaining count: 59
- A10K remaining low risk count: 7
- Historical placeholder keep count: 7
- Non-placeholder low risk count: 0

## Refresh Returncodes

```json
{
  "a10a": 0,
  "a10b": 0,
  "a10f": 0,
  "a10i": 0,
  "a10k": 0
}
```

## A10I Karar Dağılımı

```json
{
  "rename_requires_compat_wrapper_and_import_update": 7,
  "keep_referenced_do_not_rename_now": 45,
  "rename_possible_but_runtime_smoke_required": 7
}
```

## A10K Karar Dağılımı

```json
{
  "rename_with_custom_suggestion": 7
}
```

## Historical Placeholder Keep List

```json
[
  {
    "path": "migrations/versions/523a11510d7d_historical_placeholder.py",
    "name": "523a11510d7d_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/523a11510d7d_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/71d0eccf02c0_historical_placeholder.py",
    "name": "71d0eccf02c0_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/71d0eccf02c0_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/b31c7a5d9e2f_historical_placeholder.py",
    "name": "b31c7a5d9e2f_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/b31c7a5d9e2f_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/c32f8a1e4b9d_historical_placeholder.py",
    "name": "c32f8a1e4b9d_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/c32f8a1e4b9d_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/c4a1d9e2f731_historical_placeholder.py",
    "name": "c4a1d9e2f731_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/c4a1d9e2f731_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/d33a9c4e8f10_historical_placeholder.py",
    "name": "d33a9c4e8f10_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/d33a9c4e8f10_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/e8c3f1a9b4d0_historical_placeholder.py",
    "name": "e8c3f1a9b4d0_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/e8c3f1a9b4d0_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  }
]
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

historical_placeholder migration dosyaları Alembic tarihsel uyumluluk dosyasıdır. Placeholder içindeki 'old' harf dizisi false-positive kabul edilerek rename edilmeyecek ve keep allowlist kapsamında korunacaktır.