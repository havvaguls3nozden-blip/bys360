# BYS360 P5C Android Responsive Targeted Templates Gate

P5C, P5A/P5B sonrası Android/Web responsive çalışmasını hedefli hale getirir.

## Ne yapar?

- `app/static/css/bys360_android_responsive_targeted_p5c.css` dosyasını ekler/günceller.
- `app/templates/base.html` içine P5C responsive CSS bağlantısını ekler.
- P5B raporundaki öncelikli responsive marker olmayan ekranları envantere alır.
- Dashboard, home, evaluation form ve admin AI yüzeylerini merkezi CSS ile güçlendirir.
- Canlı veriye yazmaz.

## Çalıştırma

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_claude_score_uplift_p5c_android_responsive_targeted_templates_gate.ps1 -ProjectRoot "C:\bys360\project" -Mode all -CompileAll -RunAppFactorySmoke -RunSecretGate -RunPytest
```

## Beklenen rapor

`reports/architecture/BYS360_ANDROID_RESPONSIVE_TARGETED_TEMPLATES_GATE_P5C_REPORT.json`

Beklenen anahtarlar:

- `ok: true`
- `android_responsive_targeted_templates_gate_ok: true`
- `targeted_responsive_css_ok: true`
- `base_template_link_ok: true`
- `p5b_core_styles_report_ok: true`
- `target_surface_inventory_ok: true`
