"""Dijital Arşiv route iskeleti.

DA-1B:
- Blueprint ana uygulama route bootstrap akışına bağlanabilir.
- Modül varsayılan kapalıdır.
- Kullanıcı login olmadan iç modül ekranına erişemez.
- Gerçek belge işlemleri DA-2 sonrasına bırakılmıştır.
"""

from flask import Blueprint, current_app, render_template
from flask_login import login_required

from .permissions import is_digital_archive_enabled

digital_archive_bp = Blueprint(
    "digital_archive",
    __name__,
    url_prefix="/digital-archive",
)


def _digital_archive_config_enabled() -> bool:
    """Config üzerinden geçici modül açık/kapalı durumunu okur.

    DA-1B'de DB ayarı okunmaz. Varsayılan kapalıdır.
    DA-2/DA-3 aşamasında module_settings entegrasyonu eklenecektir.
    """
    value = current_app.config.get("DIGITAL_ARCHIVE_ENABLED", False)
    return is_digital_archive_enabled(value)


@digital_archive_bp.get("/")
@login_required
def index():
    """Dijital Arşiv ana giriş ekranı."""
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    return render_template("digital_archive/disabled.html")
