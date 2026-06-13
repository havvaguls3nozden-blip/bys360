# BYS360 P5D Android Responsive Release Suite Gate

P5D, P5A Android responsive baseline, P5B merkezi responsive CSS ve P5C hedefli template responsive katmanını tek release suite altında birleştirir.

## Ne yapar?

- P5A, P5B ve P5C raporlarının varlığını ve başarılı olduğunu kontrol eder.
- Android cihaz matrisi, responsive yüzey taraması, merkezi CSS ve hedefli CSS kanıtını doğrular.
- `base.html` içinde P5B ve P5C CSS bağlantılarının bulunduğunu kontrol eder.
- Mobil route sözleşmesini korur: `routes.py` 300 satır altı, 24 mobil route decorator, domain split korunur.
- Canlı veriye yazmaz.

## Çalıştırma

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_claude_score_uplift_p5d_android_responsive_release_suite_gate.ps1 -ProjectRoot "C:\bys360\project" -Mode all -CompileAll -RunAppFactorySmoke -RunSecretGate -RunPytest
```

## Beklenen rapor

`reports/architecture/BYS360_ANDROID_RESPONSIVE_RELEASE_SUITE_GATE_P5D_REPORT.json`

Beklenen anahtarlar:

- `ok: true`
- `android_responsive_release_suite_gate_ok: true`
- `p5a_baseline_report_ok: true`
- `p5b_core_styles_report_ok: true`
- `p5c_targeted_templates_report_ok: true`
- `responsive_css_evidence_ok: true`
- `base_template_links_ok: true`
- `target_surface_inventory_ok: true`
- `direct_contract_ok: true`
