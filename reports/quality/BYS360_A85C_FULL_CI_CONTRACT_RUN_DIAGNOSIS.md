# BYS360 A8.5C Full CI Contract Run Te?hisi

Tarih: 2026-06-12T17:55:11

## ?zet

- Return code: 1
- Summary: {'warnings': 28, 'failed': 6, 'passed': 738, 'skipped': 2, 'deselected': 34}
- Passed: 738
- Failed: 6
- Errors: 0
- Skipped: 2
- 700+ passed OK: True
- Clean OK: False

## Komut

```powershell
$env:BYS360_RUN_LEGACY_ARCHITECTURE_TESTS='1'
C:\bys360\project\.venv\Scripts\python.exe -m pytest tests --ignore=tests/_archive_a5_obsolete -m not live and not realdb and not slow -q -ra
```

## S?n?fland?r?lm?? Hatalar

### 1. ::
- Ham sat?r: `FAILED tests/architecture/test_android_responsive_core_styles_p5b.py::test_android_responsive_core_styles_gate_p5b`
- Neden: ``
- Te?his: Genel test/s?zle?me hatas?.
- ?nerilen d?zeltme: ?lgili test dosyas? ve assertion ayr?nt?s? incelenmeli.

### 2. ::
- Ham sat?r: `FAILED tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py::test_mobile_personnel_kpi_communication_response_gate_p3c`
- Neden: ``
- Te?his: Genel test/s?zle?me hatas?.
- ?nerilen d?zeltme: ?lgili test dosyas? ve assertion ayr?nt?s? incelenmeli.

### 3. ::
- Ham sat?r: `FAILED tests/architecture/test_mobile_api_security_suite_p4c.py::test_mobile_security_suite_gate_p4c`
- Neden: ``
- Te?his: Genel test/s?zle?me hatas?.
- ?nerilen d?zeltme: ?lgili test dosyas? ve assertion ayr?nt?s? incelenmeli.

### 4. ::
- Ham sat?r: `FAILED tests/architecture/test_mobile_api_security_suite_p4c_v2.py::test_mobile_security_suite_gate_p4c_v2`
- Neden: ``
- Te?his: Genel test/s?zle?me hatas?.
- ?nerilen d?zeltme: ?lgili test dosyas? ve assertion ayr?nt?s? incelenmeli.

### 5. ::
- Ham sat?r: `FAILED tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py::test_mobile_auth_dashboard_assistant_response_gate_p3b`
- Neden: ``
- Te?his: Genel test/s?zle?me hatas?.
- ?nerilen d?zeltme: ?lgili test dosyas? ve assertion ayr?nt?s? incelenmeli.

### 6. ::
- Ham sat?r: `FAILED tests/mobile/test_mobile_domain_contract_p2a.py::test_mobile_route_contract_count`
- Neden: ``
- Te?his: Mobil route s?zle?mesi g?ncel kodla uyu?muyor.
- ?nerilen d?zeltme: Beklenen route listesi g?ncellenmeli veya ger?ek endpoint eksikli?i giderilmeli.

## Son 500 Sat?r

```text
...F..ss......................................................F......FF. [  9%]
F....................................................................... [ 19%]
.................F...................................................... [ 28%]
........................................................................ [ 38%]
........................................................................ [ 48%]
........................................................................ [ 57%]
........................................................................ [ 67%]
........................................................................ [ 77%]
........................................................................ [ 86%]
........................................................................ [ 96%]
..........................                                               [100%]
================================== FAILURES ===================================
________________ test_android_responsive_core_styles_gate_p5b _________________

    def test_android_responsive_core_styles_gate_p5b() -> None:
        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / "quality" / "bys360_android_responsive_core_styles_gate_p5b.py"
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(root)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
>       assert result.returncode == 0, result.stdout + "\n" + result.stderr
E       AssertionError: {
E           "ok": false,
E           "package": "BYS360_CLAUDE_SCORE_UPLIFT_P5B_ANDROID_RESPONSIVE_CORE_STYLES_GATE",
E           "android_responsive_core_styles_gate_ok": false,
E           "responsive_hardening_ok": false,
E           "p5a_baseline_report_ok": false,
E           "android_core_css_ok": true,
E           "base_template_link_ok": true,
E           "core_css_media_query_count": 5,
E           "routes_py_lines": 237,
E           "total_mobile_route_decorator_count": 24,
E           "direct_contract_ok": true,
E           "compile_ok": true,
E           "app_factory_ok": true,
E           "secret_gate_ok": true,
E           "secret_gate_finding_count": 0,
E           "pytest_ok": true,
E           "pytest_mode": "skipped",
E           "report": "C:\\bys360\\project\\reports\\architecture\\BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json"
E         }
E         
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['C:\\bys360\\project\\.venv\\Scripts\\python.exe', 'C:\\bys360\\project\\scripts\\quality\\bys3...\\\\project\\\\reports\\\\architecture\\\\BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json"\n}\n', stderr='').returncode

tests\architecture\test_android_responsive_core_styles_p5b.py:24: AssertionError
__________ test_mobile_personnel_kpi_communication_response_gate_p3c __________

    def test_mobile_personnel_kpi_communication_response_gate_p3c() -> None:
        root = Path(__file__).resolve().parents[2]
        result = run_checks(
            root,
            compile_all=False,
            app_factory=False,
            secret_gate=False,
            pytest_gate=False,
            write_report=False,
        )
        assert result["direct_contract_ok"] is True
>       assert result["runtime_route_map_ok"] is True
E       assert False is True

tests\architecture\test_mobile_api_personnel_kpi_communication_response_p3c.py:21: AssertionError
------------------------------ Captured log call ------------------------------
WARNING  app:monitoring.py:44 Sentry DSN tanimli degil; hata izleme kapali.
INFO     app:startup.py:46 Startup ozeti | env=testing | db=sqlite | maintenance=off | route_count=6 | schema_errors=0 | core_scope=7 | removed_scope=3
INFO     app.services.performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.
INFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1
INFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.
WARNING  app:monitoring.py:44 Sentry DSN tanimli degil; hata izleme kapali.
INFO     app:startup.py:46 Startup ozeti | env=testing | db=sqlite | maintenance=off | route_count=6 | schema_errors=0 | core_scope=7 | removed_scope=3
INFO     app.services.performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.
INFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1
INFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.
_____________________ test_mobile_security_suite_gate_p4c _____________________

    def test_mobile_security_suite_gate_p4c():
        root = Path(__file__).resolve().parents[2]
        module = _load_gate(root)
    
        class Args:
            compile_all = False
            app_factory = False
            secret_gate = False
            pytest_gate = False
    
        report = module.build_report(root, Args())
>       assert report["ok"], report
E       AssertionError: {'app_factory_ok': True, 'app_factory_smoke': {'ok': True}, 'auth_guard_matrix_ok': False, 'ci_commands': ['python -m ...ality/bys360_mobile_security_suite_gate_p4c.py --root . --compile-all --app-factory --secret-gate --pytest-gate'], ...}
E       assert False

tests\architecture\test_mobile_api_security_suite_p4c.py:31: AssertionError
___________________ test_mobile_security_suite_gate_p4c_v2 ____________________

    def test_mobile_security_suite_gate_p4c_v2():
        root = Path(__file__).resolve().parents[2]
        module = _load_gate(root)
    
        class Args:
            compile_all = False
            app_factory = False
            secret_gate = False
            pytest_gate = False
    
        report = module.build_report(root, Args())
>       assert report["ok"], report
E       AssertionError: {'app_factory_ok': True, 'app_factory_smoke': {'ok': True}, 'auth_guard_matrix_ok': False, 'ci_commands': ['python -m ...ty/bys360_mobile_security_suite_gate_p4c_v2.py --root . --compile-all --app-factory --secret-gate --pytest-gate'], ...}
E       assert False

tests\architecture\test_mobile_api_security_suite_p4c_v2.py:31: AssertionError
___________ test_mobile_auth_dashboard_assistant_response_gate_p3b ____________

    def test_mobile_auth_dashboard_assistant_response_gate_p3b() -> None:
        root = Path(__file__).resolve().parents[2]
        result = run_checks(root, compile_all=True, app_factory=True, secret_gate=False, pytest_gate=False, write_report=False)
        assert result["direct_contract_ok"] is True
>       assert result["runtime_route_map_ok"] is True
E       assert False is True

tests\architecture\test_mobile_auth_dashboard_assistant_response_p3b.py:14: AssertionError
______________________ test_mobile_route_contract_count _______________________

    def test_mobile_route_contract_count():
        route_rules: list[str] = []
        for path in _all_mobile_route_files():
            assert path.exists(), str(path)
            route_rules.extend(_extract_routes(path))
        assert len(route_rules) == EXPECTED_ROUTE_COUNT
>       assert len(route_rules) == len(set(route_rules))
E       AssertionError: assert 24 == 23
E        +  where 24 = len(['/auth/login', '/auth/refresh', '/me', '/dashboard/summary', '/notifications/<int:notification_id>/read', '/notifications/read-all', ...])
E        +  and   23 = len({'/assistant/v2/ask', '/auth/login', '/auth/refresh', '/communication/messages/create-thread', '/communication/messages/threads/<int:thread_id>', '/communication/messages/threads/<int:thread_id>/send', ...})
E        +    where {'/assistant/v2/ask', '/auth/login', '/auth/refresh', '/communication/messages/create-thread', '/communication/messages/threads/<int:thread_id>', '/communication/messages/threads/<int:thread_id>/send', ...} = set(['/auth/login', '/auth/refresh', '/me', '/dashboard/summary', '/notifications/<int:notification_id>/read', '/notifications/read-all', ...])

tests\mobile\test_mobile_domain_contract_p2a.py:68: AssertionError
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
tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py: 1 warning
tests/critical/test_v58_claude_roadmap_smoke.py: 1 warning
tests/critical/test_v59_broad_route_smoke.py: 1 warning
tests/integration/test_feedback_http_behavior.py: 1 warning
tests/test_sp_routes_smoke.py: 1 warning
  C:\bys360\project\app\bootstrap\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-app.log' mode='a' encoding='utf-8'>
    configure_operational_logging(app)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py: 1 warning
tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py: 1 warning
tests/architecture/test_mobile_api_performance_response_p3e.py: 1 warning
tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py: 1 warning
tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py: 1 warning
tests/architecture/test_mobile_api_request_level_smoke_p2c.py: 1 warning
tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py: 1 warning
tests/architecture/test_mobile_api_response_suite_p3f.py: 1 warning
tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v3.py: 1 warning
tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py: 1 warning
tests/critical/test_v58_claude_roadmap_smoke.py: 1 warning
tests/critical/test_v59_broad_route_smoke.py: 1 warning
tests/integration/test_feedback_http_behavior.py: 1 warning
tests/test_sp_routes_smoke.py: 1 warning
  C:\bys360\project\app\bootstrap\startup.py:22: ResourceWarning: unclosed file <_io.TextIOWrapper name='C:\\bys360\\project\\logs\\bys360-ops.log' mode='a' encoding='utf-8'>
    configure_operational_logging(app)
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
SKIPPED [1] tests\architecture\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.
SKIPPED [1] tests\architecture\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.
FAILED tests/architecture/test_android_responsive_core_styles_p5b.py::test_android_responsive_core_styles_gate_p5b
FAILED tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py::test_mobile_personnel_kpi_communication_response_gate_p3c
FAILED tests/architecture/test_mobile_api_security_suite_p4c.py::test_mobile_security_suite_gate_p4c
FAILED tests/architecture/test_mobile_api_security_suite_p4c_v2.py::test_mobile_security_suite_gate_p4c_v2
FAILED tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py::test_mobile_auth_dashboard_assistant_response_gate_p3b
FAILED tests/mobile/test_mobile_domain_contract_p2a.py::test_mobile_route_contract_count
6 failed, 738 passed, 2 skipped, 34 deselected, 28 warnings in 41.25s

```