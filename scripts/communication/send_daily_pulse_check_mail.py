from __future__ import annotations
import argparse
from app import create_app
try:
    from app.services.executive_mail_center import get_selected_recipients
except Exception:
    def get_selected_recipients():
        return []
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--force', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    args=p.parse_args()
    app=create_app()
    with app.app_context():
        recips=get_selected_recipients()
        print({"ok": True, "dry_run": args.dry_run, "type": "daily_pulse_check", "recipient_count": len(recips), "recipients": recips})
        if not args.dry_run:
            # Gerçek mail gönderim fonksiyonu kurumdaki SMTP servis adına göre bağlanır.
            # Şimdilik log/test çıktısı üretir; V1.6 ekranı buradan tetikler.
            pass
if __name__=='__main__':
    main()
