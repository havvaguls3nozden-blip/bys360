"""BYS360 model namespace sözleşmesi.

Bu dosya runtime davranışını değiştirmez; model paketinin hangi modüllerden
oluştuğunu ve hangi eski modüllerin yalnızca uyumluluk için tutulduğunu belgelemek
ve kalite kapılarında doğrulamak için kullanılır.
"""
from __future__ import annotations


PUBLIC_MODEL_ENTRYPOINT = "app.models"
LEGACY_SINGLE_FILE_MODEL_PATH = "app/models.py"
MODEL_PACKAGE_PATH = "app/models"

# Canlı omurgada kullanılan model aileleri. Bu liste, model paketinin ana
# sözleşmesini tarif eder; tablo oluşturma veya migration üretme amacı taşımaz.
LIVE_MODEL_MODULES = {
    "performance_archive_models",
    "base",
    "audit_misc_models",
    "core_models",
    "settings_models",
    "org_models",
    "hr_models",
    "performance_models",
    "feedback_models",
    "support_models",
    "communication_models",
    "announcement_popup_models",
    "ai_models",
    "publication_models",
}

# Kaldırılan modüllerin model aileleri fiziksel olarak sökülmüştür.
COMPATIBILITY_MODEL_MODULES: set[str] = set()

# Fazlı iletişim model dosyaları tek seferde taşınmayacak. Önce mevcut davranış
# korunacak, sonra anlamlı isimlendirme fazına bırakılacak.
COMMUNICATION_PHASE_MODEL_MODULES = {
    "communication_family_models",
    "communication_optional_models",
    "communication_phase1_models",
    "communication_phase2_models",
    "communication_phase3_models",
    "communication_phase4_models",
    "communication_phase5_models",
    "communication_required_models",
}

FORBIDDEN_MODEL_NAMESPACE_ARTIFACTS = {
    LEGACY_SINGLE_FILE_MODEL_PATH,
}


def get_model_namespace_manifest() -> dict[str, object]:
    """Kalite kapıları için model namespace sözleşmesini döndürür."""

    return {
        "public_entrypoint": PUBLIC_MODEL_ENTRYPOINT,
        "package_path": MODEL_PACKAGE_PATH,
        "legacy_single_file_path": LEGACY_SINGLE_FILE_MODEL_PATH,
        "live_modules": sorted(LIVE_MODEL_MODULES),
        "compatibility_modules": sorted(COMPATIBILITY_MODEL_MODULES),
        "communication_phase_modules": sorted(COMMUNICATION_PHASE_MODEL_MODULES),
        "forbidden_artifacts": sorted(FORBIDDEN_MODEL_NAMESPACE_ARTIFACTS),
    }
