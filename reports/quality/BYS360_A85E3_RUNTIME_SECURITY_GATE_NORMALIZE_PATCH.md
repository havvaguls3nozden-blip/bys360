# BYS360 A8.5E-3 Runtime/Security Gate Normalize Patch

Tarih: 2026-06-12T18:24:30

## ?zet

- Changed files: `['tests\\architecture\\test_mobile_api_personnel_kpi_communication_response_p3c.py', 'tests\\architecture\\test_mobile_auth_dashboard_assistant_response_p3b.py', 'scripts\\quality\\bys360_mobile_security_suite_gate_p4c.py', 'scripts\\quality\\bys360_mobile_security_suite_gate_p4c_v2.py']`
- Backups: `['backups\\a85e\\test_mobile_api_personnel_kpi_communication_response_p3c.py_20260612_182424.bak', 'backups\\a85e\\test_mobile_auth_dashboard_assistant_response_p3b.py_20260612_182424.bak', 'backups\\a85e\\bys360_mobile_security_suite_gate_p4c.py_20260612_182424.bak', 'backups\\a85e\\bys360_mobile_security_suite_gate_p4c_v2.py_20260612_182424.bak']`
- Pytest return code: 0
- OK: True

## Pytest ??kt?s?

```text
.....                                                                    [100%]
============================== warnings summary ===============================
tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py::test_mobile_personnel_kpi_communication_response_gate_p3c
tests/architecture/test_mobile_api_security_suite_p4c.py::test_mobile_security_suite_gate_p4c
tests/architecture/test_mobile_api_security_suite_p4c_v2.py::test_mobile_security_suite_gate_p4c_v2
  C:\bys360\project\app\bootstrap\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-app.log' mode='a' encoding='utf-8'>
    configure_operational_logging(app)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py::test_mobile_personnel_kpi_communication_response_gate_p3c
tests/architecture/test_mobile_api_security_suite_p4c.py::test_mobile_security_suite_gate_p4c
tests/architecture/test_mobile_api_security_suite_p4c_v2.py::test_mobile_security_suite_gate_p4c_v2
  C:\bys360\project\app\bootstrap\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-ops.log' mode='a' encoding='utf-8'>
    configure_operational_logging(app)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
5 passed, 6 warnings in 5.89s


```