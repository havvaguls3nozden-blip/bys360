# BYS360 A11B ResourceWarning Fix

Tarih: 2026-06-13T08:26:48

## Sonuç

- OK: False
- Karar: A11B_RESOURCE_WARNING_FIX_NOT_GREEN
- Patch status: regex_patch_no_change
- Backup root: `C:\bys360\releases\A11B_RESOURCE_WARNING_FIX_BACKUP_20260613_082526`
- Compileall returncode: 0
- Import returncode: 0
- Pytest returncode: 0
- Strict ResourceWarning returncode: 0
- Warnings after: 32

## Patch Result

```json
{
  "patched": false,
  "status": "regex_patch_no_change",
  "target": "app\\bootstrap\\operational_logging.py",
  "backup": "C:\\bys360\\releases\\A11B_RESOURCE_WARNING_FIX_BACKUP_20260613_082526\\app\\bootstrap\\operational_logging.py"
}
```

## Pytest Summary

```json
{
  "warnings": 32,
  "passed": 744,
  "skipped": 2,
  "deselected": 34
}
```

## Strict ResourceWarning Summary

```json
{
  "warnings": 32,
  "passed": 744,
  "skipped": 2,
  "deselected": 34
}
```

## Strict ResourceWarning Tail

```text
......ss................................................................ [  9%]
........................................................................ [ 19%]
........................................................................ [ 28%]
........................................................................ [ 38%]
........................................................................ [ 48%]
........................................................................ [ 57%]
........................................................................ [ 67%]
........................................................................ [ 77%]
........................................................................ [ 86%]
........................................................................ [ 96%]
..........................                                               [100%]
============================== warnings summary ===============================
tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py: 1 warning
tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py: 1 warning
tests/architecture/test_mobile_api_performance_response_p3e.py: 1 warning
tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py: 1 warning
tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py: 1 warning
tests/architecture/test_mobile_api_request_level_smoke_p2c.py: 1 warning
tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py: 1 warning
tests/architecture/test_mobile_api_response_suite_p3f.py: 1 warning
tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v3.py: 1 warning
tests/architecture/test_mobile_api_security_suite_p4c.py: 1 warning
tests/architecture/test_mobile_api_security_suite_p4c_v2.py: 1 warning
tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py: 1 warning
tests/critical/test_v58_claude_roadmap_smoke.py: 1 warning
tests/critical/test_v59_broad_route_smoke.py: 1 warning
tests/integration/test_feedback_http_behavior.py: 1 warning
tests/test_sp_routes_smoke.py: 1 warning
  C:\bys360\project\.venv\Lib\site-packages\_pytest\unraisableexception.py:67: PytestUnraisableExceptionWarning: Exception ignored in: <_io.FileIO name='C:\\bys360\\project\\logs\\bys360-ops.log' mode='ab' closefd=True>
  
  Traceback (most recent call last):
    File "C:\bys360\project\app\bootstrap\startup.py", line 22, in run_runtime_pipeline
      configure_operational_logging(app)
  ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-ops.log' mode='a' encoding='utf-8'>
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnraisableExceptionWarning(msg))

tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py: 1 warning
tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py: 1 warning
tests/architecture/test_mobile_api_performance_response_p3e.py: 1 warning
tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py: 1 warning
tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py: 1 warning
tests/architecture/test_mobile_api_request_level_smoke_p2c.py: 1 warning
tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py: 1 warning
tests/architecture/test_mobile_api_response_suite_p3f.py: 1 warning
tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v3.py: 1 warning
tests/architecture/test_mobile_api_security_suite_p4c.py: 1 warning
tests/architecture/test_mobile_api_security_suite_p4c_v2.py: 1 warning
tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py: 1 warning
tests/critical/test_v58_claude_roadmap_smoke.py: 1 warning
tests/critical/test_v59_broad_route_smoke.py: 1 warning
tests/integration/test_feedback_http_behavior.py: 1 warning
tests/test_sp_routes_smoke.py: 1 warning
  C:\bys360\project\.venv\Lib\site-packages\_pytest\unraisableexception.py:67: PytestUnraisableExceptionWarning: Exception ignored in: <_io.FileIO name='C:\\bys360\\project\\logs\\bys360-app.log' mode='ab' closefd=True>
  
  Traceback (most recent call last):
    File "C:\bys360\project\app\bootstrap\startup.py", line 22, in run_runtime_pipeline
      configure_operational_logging(app)
  ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-app.log' mode='a' encoding='utf-8'>
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnraisableExceptionWarning(msg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
SKIPPED [1] tests\architecture\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.
SKIPPED [1] tests\architecture\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.
744 passed, 2 skipped, 34 deselected, 32 warnings in 40.61s


```

## Sonraki Adım

A11C: A11B sonrası warning audit tekrar çalıştırılacak ve warning count 0 ise A11 final evidence üretilecek.