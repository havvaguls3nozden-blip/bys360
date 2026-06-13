# BYS360 Quality 10/10 P2 — Tek Dosya Güvenli Patch

Bu paket, önceki geniş kapsamlı P1 patch yaklaşımının yerine **tek dosya, güvenli ve geri dönüşlü** çalışma mantığı getirir.

## Hedef

İlk güvenli hedef dosya:

```text
app/live_scope.py
```

Bu dosyada sadece şu yapı değiştirilir:

```python
except ...:
    pass
```

Yeni yapı:

```python
except ...:
    __import__("logging").getLogger(__name__).exception("...")
```

## Güvenlik Kuralları

- Sadece tek dosya değişir.
- Dosya önce `.quality_backup` altına yedeklenir.
- Patch sonrası `py_compile` yapılır.
- Derleme başarısız olursa dosya otomatik geri alınır.
- Import sırası bozulmasın diye dosyaya yeni `import logging` eklenmez.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P2_LIVE_SCOPE_SAFE_PATCH_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality_10_10_p2_live_scope_safe_patch.ps1 -ProjectRoot "C:\bys360\project" -DryRun

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality_10_10_p2_live_scope_safe_patch.ps1 -ProjectRoot "C:\bys360\project"

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p2_live_scope.ps1 -ProjectRoot "C:\bys360\project"
```
