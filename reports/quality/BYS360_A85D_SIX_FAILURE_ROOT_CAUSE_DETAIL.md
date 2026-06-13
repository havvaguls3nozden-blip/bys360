# BYS360 A8.5D 6 Hata K?k Neden Detay Raporu

Tarih: 2026-06-12T17:57:34

## K?k Nedenler

### RC1 ? Android responsive P5B evidence eksik
- Etkilenen testler: `['tests/architecture/test_android_responsive_core_styles_p5b.py']`
- G?zlenen: responsive_hardening_ok=false, p5a_baseline_report_ok=false
- D?zeltme stratejisi: P5A baseline raporu ?retilecek; responsive hardening evidence gate yeniden ko?turulacak.

### RC2 ? Mobil runtime route map contract uyumsuzlu?u
- Etkilenen testler: `['tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py', 'tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py']`
- G?zlenen: direct_contract_ok=true ama runtime_route_map_ok=false
- D?zeltme stratejisi: Runtime route map kontrol?nde beklenen mobil blueprint kay?tlar? ve test app factory kapsam? e?itlenecek.

### RC3 ? Mobil auth guard matrix eksik
- Etkilenen testler: `['tests/architecture/test_mobile_api_security_suite_p4c.py', 'tests/architecture/test_mobile_api_security_suite_p4c_v2.py']`
- G?zlenen: auth_guard_matrix_ok=false
- D?zeltme stratejisi: Mobil route auth/guard matrisi g?ncel route listesine g?re tamamlanacak veya false-positive ise contract g?ncellenecek.

### RC4 ? Mobil route duplicate testi path-only bak?yor
- Etkilenen testler: `['tests/mobile/test_mobile_domain_contract_p2a.py']`
- G?zlenen: 24 route var, path-only unique 23. METHOD+PATH baz?nda duplicate yoksa test false-positive.
- D?zeltme stratejisi: Duplicate assertion METHOD+PATH bazl? yap?lacak.

## Mobil Route Duplicate Detay?

- Route entry count: 62
- Path unique count: 58
- METHOD+PATH unique count: 62
- Path duplicate count: 4
- Exact METHOD+PATH duplicate count: 0

### Path-only duplicate adaylar?

#### /performance/tasks/<int:assignment_id>/score-form
- GET `app/api/mobile/performance_routes.py:937`
- POST `app/api/mobile/performance_routes.py:946`

#### /performance/in-period-notes/v2
- GET `app/api/mobile/performance_routes.py:1508`
- POST `app/api/mobile/performance_routes.py:1573`

#### /support/tickets
- GET `app/api/mobile/support_survey_read_routes.py:10`
- POST `app/api/mobile/domains/support_survey_write.py:37`

#### /kpi/target-management
- GET `app/api/mobile/domains/kpi_target_management.py:68`
- POST `app/api/mobile/domains/kpi_target_management.py:135`

Exact METHOD+PATH duplicate bulunmad?.

## Test Dosyas? Detaylar?

### tests/architecture/test_android_responsive_core_styles_p5b.py
- Var: True
- Script referanslar?: `['scripts/quality/bys360_android_responsive_core_styles_gate_p5b.py']`
- EXPECTED_ROUTE_COUNT: `None`
- Assertionlar:
  - `assert result.returncode == 0, result.stdout + "\n" + result.stderr`
  - `assert data["ok"] is True`
  - `assert data["android_responsive_core_styles_gate_ok"] is True`
  - `assert data["responsive_hardening_ok"] is True`
  - `assert data["p5a_baseline_report_ok"] is True`
  - `assert data["android_core_css_ok"] is True`
  - `assert data["base_template_link_ok"] is True`
  - `assert data["core_css_media_query_count"] >= 5`
  - `assert data["direct_contract_ok"] is True`

### tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py
- Var: True
- Script referanslar?: `[]`
- EXPECTED_ROUTE_COUNT: `None`
- Assertionlar:
  - `assert result["direct_contract_ok"] is True`
  - `assert result["runtime_route_map_ok"] is True`
  - `assert result["response_code_smoke_ok"] is True`
  - `assert result["routes_py_lines"] <= 300`
  - `assert result["total_mobile_route_decorator_count"] == 24`

### tests/architecture/test_mobile_api_security_suite_p4c.py
- Var: True
- Script referanslar?: `['scripts/quality/bys360_mobile_security_suite_gate_p4c.py']`
- EXPECTED_ROUTE_COUNT: `None`
- Assertionlar:
  - `assert spec and spec.loader, f"cannot load {script}"`
  - `assert report["ok"], report`
  - `assert report["p4_security_suite_ok"] is True`
  - `assert report["security_gate_count"] == 2`
  - `assert report["security_gates_passed"] == 2`
  - `assert report["auth_guard_matrix_ok"] is True`
  - `assert report["role_boundary_matrix_ok"] is True`
  - `assert report["total_probe_count"] >= 90`
  - `assert report["direct_contract_ok"] is True`

### tests/architecture/test_mobile_api_security_suite_p4c_v2.py
- Var: True
- Script referanslar?: `['scripts/quality/bys360_mobile_security_suite_gate_p4c_v2.py']`
- EXPECTED_ROUTE_COUNT: `None`
- Assertionlar:
  - `assert spec and spec.loader, f"cannot load {script}"`
  - `assert report["ok"], report`
  - `assert report["p4_security_suite_ok"] is True`
  - `assert report["security_gate_count"] == 2`
  - `assert report["security_gates_passed"] == 2`
  - `assert report["auth_guard_matrix_ok"] is True`
  - `assert report["role_boundary_matrix_ok"] is True`
  - `assert report["total_probe_count"] >= 90`
  - `assert report["direct_contract_ok"] is True`

### tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py
- Var: True
- Script referanslar?: `[]`
- EXPECTED_ROUTE_COUNT: `None`
- Assertionlar:
  - `assert result["direct_contract_ok"] is True`
  - `assert result["runtime_route_map_ok"] is True`
  - `assert result["response_code_smoke_ok"] is True`
  - `assert result["compile_ok"] is True`
  - `assert result["app_factory_ok"] is True`

### tests/mobile/test_mobile_domain_contract_p2a.py
- Var: True
- Script referanslar?: `[]`
- EXPECTED_ROUTE_COUNT: `24`
- Assertionlar:
  - `assert routes_py.exists()`
  - `assert len(routes_py.read_text(encoding="utf-8-sig").splitlines()) <= 300`
  - `assert domain_dir.exists()`
  - `assert (domain_dir / filename).exists(), filename`
  - `assert path.exists(), str(path)`
  - `assert len(route_rules) == EXPECTED_ROUTE_COUNT`
  - `assert len(route_rules) == len(set(route_rules))`
