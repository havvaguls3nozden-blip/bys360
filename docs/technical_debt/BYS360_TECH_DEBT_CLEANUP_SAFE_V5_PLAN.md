# SAFE V5 Plan

Amaç: V4 sonrası kalan basit sessiz `except Exception` borcunu küçük ve geri alınabilir yamalarla azaltmak.

Başarı kriterleri:

- `compile_ok: true`
- `quality9_run.returncode: 0`
- `patch_simple_excepts.action_count > 0` veya patch edilebilir kayıt kalmamış olması
- `delta.app_silent_broad_except_count` negatif olmalı
- Backup dizini oluşmalı

Not: `broad_except_count` azalmaz; çünkü bu faz exception tipini değiştirmez. Azalması gereken metrik `app_silent_broad_except_count` ve `patchable_simple_silent_except_count` değerleridir.
