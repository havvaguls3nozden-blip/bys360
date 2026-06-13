from app import create_app, db
from app.models import User
from sqlalchemy import or_

app = create_app()

with app.app_context():
    u = User.query.filter(
        or_(
            User.email == "bys360@ktb.gov.tr",
            User.sicil_no == "bys360@ktb.gov.tr"
        )
    ).first()

    if not u:
        raise SystemExit("Kullanici bulunamadi.")

    correct_last_name = "Y\u00f6neticisi"
    correct_display = "Sistem " + correct_last_name

    u.ad = "Sistem"
    u.soyad = correct_last_name
    u.full_name_cache = correct_display
    u.role_label = correct_display

    db.session.commit()

    print("GUNCELLENDI")
    print("ad=", u.ad)
    print("soyad=", u.soyad)
    print("full_name_cache=", u.full_name_cache)
    print("role_label=", u.role_label)
