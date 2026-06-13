# BYS360 A8.5E-4 Android Responsive Evidence Patch

Tarih: 2026-06-12T18:26:58

## ?zet

- Candidate reports: `['reports\\architecture\\BYS360_ANDROID_RESPONSIVE_BASELINE_GATE_P5A_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_BASELINE_P5A_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_HARDENING_P5B_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_HARDENING_EVIDENCE_P5B_REPORT.json']`
- Written/updated reports: `['reports\\architecture\\BYS360_ANDROID_RESPONSIVE_BASELINE_GATE_P5A_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_BASELINE_P5A_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_HARDENING_P5B_REPORT.json', 'reports\\architecture\\BYS360_ANDROID_RESPONSIVE_HARDENING_EVIDENCE_P5B_REPORT.json']`
- P5B script return code: 1
- P5B test return code: 1
- OK: False

## P5B Script ??kt?s?

```text
{
  "ok": false,
  "package": "BYS360_CLAUDE_SCORE_UPLIFT_P5B_ANDROID_RESPONSIVE_CORE_STYLES_GATE",
  "android_responsive_core_styles_gate_ok": false,
  "responsive_hardening_ok": false,
  "p5a_baseline_report_ok": false,
  "android_core_css_ok": true,
  "base_template_link_ok": true,
  "core_css_media_query_count": 5,
  "routes_py_lines": 237,
  "total_mobile_route_decorator_count": 24,
  "direct_contract_ok": true,
  "compile_ok": true,
  "app_factory_ok": true,
  "secret_gate_ok": true,
  "secret_gate_finding_count": 0,
  "pytest_ok": true,
  "pytest_mode": "skipped",
  "report": "C:\\bys360\\project\\reports\\architecture\\BYS360_ANDROID_RESPONSIVE_CORE_STYLES_GATE_P5B_REPORT.json"
}


```

## P5B Test ??kt?s?

```text
F                                                                        [100%]
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
=========================== short test summary info ===========================
FAILED tests/architecture/test_android_responsive_core_styles_p5b.py::test_android_responsive_core_styles_gate_p5b
1 failed in 0.14s


```