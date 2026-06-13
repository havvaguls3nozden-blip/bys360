
"""BYS360 Faz 1C hotfix/snippet merge registry.

Bu dosya çalışan iş mantığı üretmek için değil; geçici dosyaların hangi kalıcı
hedefe eritileceğini tek merkezde görünür kılmak için tutulur.
"""
from __future__ import annotations

HOTFIX_MERGE_REGISTRY = [
    {
        "source": "app/education_phase8_button_hotfix.py",
        "target": "app/education_roster_shortcuts.py",
        "family": "education",
        "merge_strategy": "compat_wrapper_keep",
        "risk": "dusuk",
        "note": "Hotfix dosyası zaten uyumluluk sarmalayıcısı; kanonik hedef mevcut.",
    },
    {
        "source": "app/schema_guard_phase7_snippet.py",
        "target": "app/refactor/schema_guard_extension_bundle.py",
        "family": "schema_guard",
        "merge_strategy": "bundle_then_inline",
        "risk": "orta",
        "note": "Faz 7 tablo ve kolon onarımları bundle dosyada toplanmalı.",
    },
    {
        "source": "app/schema_guard_phase8_snippet.py",
        "target": "app/refactor/schema_guard_extension_bundle.py",
        "family": "schema_guard",
        "merge_strategy": "bundle_then_inline",
        "risk": "orta",
        "note": "Faz 8 erişim politikası, export job ve audit log onarımları bundle'a taşınmalı.",
    },
    {
        "source": "app/schema_guard_phase7_approval_hotfix_snippet.py",
        "target": "app/refactor/schema_guard_extension_bundle.py",
        "family": "schema_guard",
        "merge_strategy": "bundle_then_inline",
        "risk": "orta",
        "note": "Approval tablosu onarımı merkezi bundle dosyada tutulmalı.",
    },
    {
        "source": "app/schema_guard_faz81_snippet.py",
        "target": "app/refactor/schema_guard_extension_bundle.py",
        "family": "schema_guard",
        "merge_strategy": "bundle_then_inline",
        "risk": "orta",
        "note": "Faz 8.1 eğitim video stabilizasyon blokları bundle'a alınmalı.",
    },
    {
        "source": "app/services/performance/common_admin_scope_hotfix.py",
        "target": "app/services/performance/common.py",
        "family": "performance",
        "merge_strategy": "inline_function_merge",
        "risk": "dusuk",
        "note": "is_performance_scope_user() ve norm yardımcıları kalıcı common.py içine alınmalı.",
    },
    {
        "source": "app/portal/helpers_import_fix_snippet.py",
        "target": "app/portal/helpers.py",
        "family": "portal",
        "merge_strategy": "import_sync",
        "risk": "dusuk",
        "note": "Helpers import satırları kanonik dosyada eşitlenmeli.",
    },
    {
        "source": "app/portal/portal_story_new_fixed_snippet.py",
        "target": "app/portal/routes.py",
        "family": "portal",
        "merge_strategy": "manual_route_merge",
        "risk": "orta",
        "note": "portal_story_new route gövdesi mevcut routes.py ile karşılaştırılarak eritilmeli.",
    },
    {
        "source": "app/templates/education/_phase8_detail_buttons_snippet.html",
        "target": "app/templates/education/*.html",
        "family": "education_template",
        "merge_strategy": "target_resolution_required",
        "risk": "orta",
        "note": "Önce gerçek detay şablonu bulunmalı, sonra snippet eritilmeli.",
    },
    {
        "source": "app/templates/portal/feed_story_priority_snippet.html",
        "target": "app/templates/portal/feed.html",
        "family": "portal_template",
        "merge_strategy": "preview_then_inline",
        "risk": "orta",
        "note": "Kısa akış öncelik bloğu feed.html veya feed_v2 içinde konumlandırılmalı.",
    },
    {
        "source": "app/templates/portal/feed_profile_card_compact_snippet.html",
        "target": "app/templates/portal/feed.html",
        "family": "portal_template",
        "merge_strategy": "preview_then_inline",
        "risk": "orta",
        "note": "Profil kartı kompakt varyasyonu aktif feed şablonuna göre karara bağlanmalı.",
    },
    {
        "source": "app/templates/portal/feed_profile_card_white_header_snippet.html",
        "target": "app/templates/portal/feed_v2.html",
        "family": "portal_template",
        "merge_strategy": "preview_then_inline",
        "risk": "orta",
        "note": "Beyaz başlıklı profil kartı daha çok feed_v2 tarafına adaydır.",
    },
]