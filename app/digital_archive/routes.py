"""Dijital Arşiv route iskeleti.

Bu dosya DA-1A aşamasında pasif modül davranışı sağlar.
Ana uygulamaya kayıt DA-1B aşamasında yapılacaktır.
"""

from flask import Blueprint, render_template

digital_archive_bp = Blueprint(
    "digital_archive",
    __name__,
    url_prefix="/digital-archive",
)


@digital_archive_bp.get("/")
def index():
    """Dijital Arşiv ana giriş ekranı.

    Modül DA-1A aşamasında pasif kabul edilir.
    """
    return render_template("digital_archive/disabled.html")
