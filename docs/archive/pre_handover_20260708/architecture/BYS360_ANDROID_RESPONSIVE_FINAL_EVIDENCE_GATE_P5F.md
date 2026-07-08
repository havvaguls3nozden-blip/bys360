# BYS360 P5F Android Responsive Final Evidence Gate

P5F closes the Android responsive phase by validating the full P5A-P5E chain:

- P5A Android responsive baseline and device matrix
- P5B central Android responsive core CSS
- P5C targeted template responsive layer
- P5D Android responsive release suite
- P5E visual UAT evidence/checklist

The gate is safe. It reads existing reports, checks CSS/link evidence, writes a final handover markdown, compiles the active quality/test files, and optionally runs app factory, secret, and pytest gates.

Expected command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_claude_score_uplift_p5f_android_responsive_final_evidence_gate.ps1 -ProjectRoot "C:\bys360\project" -Mode all -CompileAll -RunAppFactorySmoke -RunSecretGate -RunPytest
```

Expected report:

`reports/architecture/BYS360_ANDROID_RESPONSIVE_FINAL_EVIDENCE_GATE_P5F_REPORT.json`
