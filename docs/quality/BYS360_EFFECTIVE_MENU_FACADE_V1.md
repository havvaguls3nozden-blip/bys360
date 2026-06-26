# BYS360 Effective Menu Facade V1

Amaç: `app/services/settings/effective_menu.py` dosyasını gerçek facade haline getirmek.

Bu fazda büyük runtime politika blokları `app/services/settings/effective_menu_parts/runtime_policy_context.py` dosyasına taşınır. `effective_menu.py` dış API ve wrapper sırasını korur, fakat 800+ satırlık god-object olmaktan çıkar.

Başarı kriterleri:

- `effective_menu.py` 400 satırın altına iner.
- Yeni `runtime_policy_context.py` 800 satırın altında kalır.
- `build_menu_visibility_map` public API adı korunur.
- Runtime politika blokları import-time sırasını koruyarak uygulanır.
- `exec` / `eval` kullanılmaz.
- Compile kontrolü geçer.
