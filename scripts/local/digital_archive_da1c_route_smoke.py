from pathlib import Path

from app import create_app
from app.digital_archive.permissions import is_digital_archive_enabled


def main():
    app = create_app()

    rules = sorted(
        (rule.rule, rule.endpoint)
        for rule in app.url_map.iter_rules()
    )

    digital_archive_rules = [
        (rule, endpoint)
        for rule, endpoint in rules
        if "digital-archive" in rule or endpoint.startswith("digital_archive.")
    ]

    if not digital_archive_rules:
        raise SystemExit("DA-1C FAIL: /digital-archive route kaydı bulunamadı.")

    expected_endpoint = "digital_archive.index"
    if not any(endpoint == expected_endpoint for _, endpoint in digital_archive_rules):
        raise SystemExit(f"DA-1C FAIL: {expected_endpoint} endpoint kaydı bulunamadı.")

    if is_digital_archive_enabled(None):
        raise SystemExit("DA-1C FAIL: None ayarında modül kapalı dönmeli.")

    if is_digital_archive_enabled(False):
        raise SystemExit("DA-1C FAIL: False ayarında modül kapalı dönmeli.")

    if not is_digital_archive_enabled("true"):
        raise SystemExit("DA-1C FAIL: true ayarında modül açık dönmeli.")

    print("OK: DA-1C Dijital Arşiv route smoke geçti.")
    print("DIGITAL_ARCHIVE_RULES:")
    for rule, endpoint in digital_archive_rules:
        print(f"- {rule} -> {endpoint}")

    with app.test_client() as client:
        response = client.get("/digital-archive/", follow_redirects=False)
        print(f"UNAUTH_STATUS={response.status_code}")

        if response.status_code not in {302, 401, 403}:
            raise SystemExit(
                "DA-1C FAIL: login olmadan /digital-archive/ erişimi "
                f"302/401/403 beklenirken {response.status_code} döndü."
            )

    print("OK: DA-1C login koruması smoke kontrolünden geçti.")


if __name__ == "__main__":
    main()
