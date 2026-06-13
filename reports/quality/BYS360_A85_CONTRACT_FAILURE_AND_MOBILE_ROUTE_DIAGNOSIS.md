# BYS360 A8.5 Contract Failure ve Mobil Route Teşhis Raporu

Tarih: 2026-06-12T17:48:27

## Özet

- Diagnosis only: True
- Mobil route sayısı: 62
- Exact duplicate METHOD+PATH sayısı: 0
- Path-only duplicate sayısı: 4
- Method-aware OK ama path-only duplicate sayısı: 4
- Pytest return code: 0
- Pytest failure line count: 0
- Pytest error line count: 0
- Classified failure count: 0
- PS1 dosya sayısı: 776
- tests/_archive_a5_obsolete var mı: True
- tests/_archive_a5_obsolete dosya sayısı: 83

## Mükerrer Mobil Route Teşhisi

Exact duplicate METHOD+PATH bulunmadı.

### Aynı path, farklı method kullanan adaylar

#### /api/mobile/kpi/target-management
- methods=['GET'] `app/api/mobile/domains/kpi_target_management.py:68` function=`mobile_kpi_target_management_v2853`
- methods=['POST'] `app/api/mobile/domains/kpi_target_management.py:135` function=`mobile_kpi_target_create_v2853`

#### /api/mobile/support/tickets
- methods=['POST'] `app/api/mobile/domains/support_survey_write.py:37` function=`mobile_support_ticket_create`
- methods=['GET'] `app/api/mobile/support_survey_read_routes.py:10` function=``

#### /api/mobile/performance/tasks/<int:assignment_id>/score-form
- methods=['GET'] `app/api/mobile/performance_routes.py:937` function=`mobile_performance_task_score_form`
- methods=['POST'] `app/api/mobile/performance_routes.py:946` function=`mobile_performance_task_score_submit`

#### /api/mobile/performance/in-period-notes/v2
- methods=['GET'] `app/api/mobile/performance_routes.py:1508` function=`_bys360_legacy_mobile_performance_in_period_notes_v2853`
- methods=['POST'] `app/api/mobile/performance_routes.py:1573` function=`mobile_performance_create_in_period_note_v2853`

Not: Bunlar Flask açısından genelde geçerli olabilir; contract sadece path bazlı duplicate bakıyorsa false-positive üretir.

## Pytest / Contract Hataları

- Komut: `C:\bys360\project\.venv\Scripts\python.exe -m pytest tests --ignore=tests/_archive_a5_obsolete -m not live and not realdb and not slow -q`
- Return code: `0`
- Summary: `{'passed': 12, 'skipped': 734, 'deselected': 34, 'warnings': 10}`

Pytest FAILED/ERROR satırı yakalanmadı. Ayrıntı için JSON içindeki pytest_tail alanına bakılmalı.

## PS1 ve Arşiv Durumu

- PS1 dosya sayısı: 776
- tests/_archive_a5_obsolete mevcut: True
- tests/_archive_a5_obsolete dosya sayısı: 83

## Pytest Son 400 Satır

```text
ssssssss..ssssssssssssssssssssssssssssssssssssssssssssss.....ss.s..sssss [  9%]
ss..ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 19%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 28%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 38%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 48%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 57%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 67%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 77%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 86%]
ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss [ 96%]
ssssssssssssssssssssssssss                                               [100%]
============================== warnings summary ===============================
tests\architecture\test_android_responsive_core_styles_p5b.py:38
  C:\bys360\project\tests\architecture\test_android_responsive_core_styles_p5b.py:38: PytestUnknownMarkWarning: Unknown pytest.mark.mobile - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.mobile

tests\architecture\test_mobile_api_personnel_kpi_communication_response_p3c.py:29
  C:\bys360\project\tests\architecture\test_mobile_api_personnel_kpi_communication_response_p3c.py:29: PytestUnknownMarkWarning: Unknown pytest.mark.mobile - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.mobile

tests\architecture\test_mobile_api_security_suite_p4c.py:43
  C:\bys360\project\tests\architecture\test_mobile_api_security_suite_p4c.py:43: PytestUnknownMarkWarning: Unknown pytest.mark.mobile - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.mobile

tests\architecture\test_mobile_api_security_suite_p4c_v2.py:43
  C:\bys360\project\tests\architecture\test_mobile_api_security_suite_p4c_v2.py:43: PytestUnknownMarkWarning: Unknown pytest.mark.mobile - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.mobile

tests\architecture\test_mobile_auth_dashboard_assistant_response_p3b.py:22
  C:\bys360\project\tests\architecture\test_mobile_auth_dashboard_assistant_response_p3b.py:22: PytestUnknownMarkWarning: Unknown pytest.mark.mobile - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.mobile

tests\mobile\test_mobile_domain_contract_p2a.py:81
  C:\bys360\project\tests\mobile\test_mobile_domain_contract_p2a.py:81: PytestUnknownMarkWarning: Unknown pytest.mark.mobile - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.mobile

tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py::test_mobile_personnel_kpi_communication_response_gate_p3c_v2
tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py::test_mobile_api_request_level_smoke_contract_gate_v3
  C:\bys360\project\app\bootstrap\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-app.log' mode='a' encoding='utf-8'>
    configure_operational_logging(app)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py::test_mobile_personnel_kpi_communication_response_gate_p3c_v2
tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py::test_mobile_api_request_level_smoke_contract_gate_v3
  C:\bys360\project\app\bootstrap\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-ops.log' mode='a' encoding='utf-8'>
    configure_operational_logging(app)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
12 passed, 734 skipped, 34 deselected, 10 warnings in 48.43s

```