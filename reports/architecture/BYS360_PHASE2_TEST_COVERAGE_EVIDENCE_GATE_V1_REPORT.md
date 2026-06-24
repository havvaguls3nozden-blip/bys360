# BYS360 Faz 2 Test Kapsamı Kanıt Raporu

- Paket: `BYS360_PHASE2_TEST_COVERAGE_EVIDENCE_GATE_V1`
- Üretim zamanı: `2026-06-24T17:34:18`
- Genel durum: `PASS`
- Git temizliği: `PASS`
- Zorunlu dosyalar: `True`
- Rapor kanıtları: `True`

## Faz 2 Kapanış Özeti

| Faz | Kanıt | Durum |
|---|---|---|
| Faz 2A | pytest invocation guard | PASS |
| Faz 2B | mobile auth smoke gate | PASS |
| Faz 2C | login / me / refresh success flow | PASS |
| Faz 2D-1 | P4A auth guard matrix 28 route + push | PASS |
| Faz 2D-2 | tokenlı personel/admin rol matrisi | PASS |

## Git Log

```text
0647aec test: add phase2 test coverage evidence gate
acfc6ab test: add phase2 mobile role token matrix gate
d41d6c2 test: align mobile auth guard matrix with push routes
6a9369e test: add phase2 mobile auth success flow gate
4f69f65 test: add phase2 mobile auth smoke gate
3430fea test: add phase2 pytest invocation guard
7ada4bd docs: refresh secure release preflight evidence
81151b8 test: align mobile API contract gates with 28 routes
7119f6f docs: add handover runbooks and quality gate entrypoint
```

## Zorunlu Dosya Kontrolleri

| Ad | Yol | Durum | Eksik Token |
|---|---|---|---|
| phase2_pytest_runner | `scripts/windows/run_bys360_tests.ps1` | PASS | `` |
| phase2_pytest_invocation_contract | `tests/quality/test_phase2_pytest_invocation_contract_v1.py` | PASS | `` |
| phase2_auth_smoke_gate | `scripts/quality/bys360_phase2_auth_smoke_gate_v1.py` | PASS | `` |
| phase2_auth_success_flow_gate | `scripts/quality/bys360_phase2_auth_success_flow_gate_v1.py` | PASS | `` |
| phase2_role_token_matrix_gate | `scripts/quality/bys360_phase2_mobile_role_token_matrix_gate_v1.py` | PASS | `` |
| p4a_mobile_auth_guard_matrix | `scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py` | PASS | `` |
| p2b_mobile_behavior_contract | `tests/architecture/test_mobile_api_behavior_smoke_p2b.py` | PASS | `` |

## JSON Rapor Kontrolleri

| Ad | Yol | Durum |
|---|---|---|
| phase2_auth_smoke_report | `reports/architecture/BYS360_PHASE2_AUTH_SMOKE_GATE_V1_REPORT.json` | PASS |
| phase2_auth_success_flow_report | `reports/architecture/BYS360_PHASE2_AUTH_SUCCESS_FLOW_GATE_V1_REPORT.json` | PASS |
| phase2_role_token_matrix_report | `reports/architecture/BYS360_PHASE2_MOBILE_ROLE_TOKEN_MATRIX_GATE_V1_REPORT.json` | PASS |
| p4a_mobile_auth_guard_matrix_report | `reports/architecture/BYS360_MOBILE_AUTH_GUARD_MATRIX_GATE_P4A_REPORT.json` | PASS |
