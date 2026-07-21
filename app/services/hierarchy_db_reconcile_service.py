from __future__ import annotations

# --- BYS360 third-manager Excel import compatibility patch ---


THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text

from app.extensions import db

from .hierarchy_rule_engine_service_v2 import HierarchyRuleEngineServiceV2, UserRow


class HierarchyDbReconcileService:
    def __init__(self, report_dir: str | Path | None = None):
        self.report_dir = Path(report_dir or (Path.cwd() / 'reports' / 'faz3_9'))
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.engine = HierarchyRuleEngineServiceV2()

    def preview_and_optionally_apply(self, apply_changes: bool = False) -> dict[str, object]:
        users = self._fetch_users()
        resolved = self.engine.resolve_many(users)
        rows = []
        user_updates = 0
        open_assignment_updates = 0
        locked_assignments = 0
        period_id = self._active_period_id()
        for row in resolved:
            detail = self._diff(row)
            if apply_changes and detail['will_update_user']:
                self._apply_user_chain(row)
                detail['user_updated'] = True
                user_updates += 1
                if period_id:
                    oa, la = self._sync_open_assignments(period_id, row)
                    open_assignment_updates += oa
                    locked_assignments += la
            rows.append({**row, **detail})
        if apply_changes:
            db.session.commit()
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary = {
            'ok': True,
            'apply': apply_changes,
            'input_count': len(users),
            'resolved_count': len(resolved),
            'warning_count': sum(len(r.get('warnings', [])) for r in resolved),
            'info_count': sum(len(r.get('info', [])) for r in resolved),
            'user_updates': user_updates,
            'open_assignment_updates': open_assignment_updates,
            'locked_assignments': locked_assignments,
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'rows': rows,
        }
        json_path = self.report_dir / f'faz3_9_position_apply_{ts}.json'
        csv_path = self.report_dir / f'faz3_9_position_apply_{ts}.csv'
        txt_path = self.report_dir / f'faz3_9_position_apply_{ts}.txt'
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        self._write_csv(csv_path, rows)
        txt_path.write_text(self._build_txt(summary), encoding='utf-8')
        summary.update({'json_path': str(json_path), 'csv_path': str(csv_path), 'txt_path': str(txt_path)})
        return summary

    def _fetch_users(self) -> list[UserRow]:
        cols = self._table_columns('users')
        full_name_expr = "trim(coalesce(ad,'') || ' ' || coalesce(soyad,''))"
        if 'full_name' in cols:
            full_name_expr = f"coalesce(nullif(trim(full_name), ''), {full_name_expr})"
        q = text(f"""
            SELECT id,
                   coalesce(sicil_no,'') AS sicil_no,
                   {full_name_expr} AS full_name,
                   coalesce(role,'personel') AS role,
                   coalesce(unvan,'') AS unvan,
                   coalesce(birim,'') AS birim,
                   coalesce(ust_birim,'') AS ust_birim,
                   coalesce(yonetici_sicil,'') AS yonetici_sicil,
                   coalesce(ikinci_yonetici_sicil,'') AS ikinci_yonetici_sicil,
                   coalesce(ucuncu_yonetici_sicil,'') AS ucuncu_yonetici_sicil,
                   coalesce(is_active,true) AS is_active
            FROM users
            ORDER BY id ASC
        """)
        out = []
        for r in db.session.execute(q).mappings().all():
            if not bool(r['is_active']) or not str(r['sicil_no']).strip():
                continue
            out.append(UserRow(
                id=r['id'],
                sicil_no=str(r['sicil_no']).strip(),
                full_name=str(r['full_name'] or '').strip(),
                role=str(r['role'] or '').strip(),
                unvan=str(r['unvan'] or '').strip(),
                birim=str(r['birim'] or '').strip(),
                ust_birim=str(r['ust_birim'] or '').strip(),
                yonetici_sicil=str(r['yonetici_sicil'] or '').strip(),
                ikinci_yonetici_sicil=str(r['ikinci_yonetici_sicil'] or '').strip(),
                ucuncu_yonetici_sicil=str(r['ucuncu_yonetici_sicil'] or '').strip(),
                is_active=True,
                source='db',
                raw=dict(r),
            ))
        return out

    def _diff(self, row: dict[str, object]) -> dict[str, object]:
        cur1 = str(row.get('yonetici_sicil') or '').strip()
        cur2 = str(row.get('ikinci_yonetici_sicil') or '').strip()
        cur3 = str(row.get('ucuncu_yonetici_sicil') or '').strip()
        tar1 = str(row.get('manager_1_sicil') or '').strip()
        tar2 = str(row.get('manager_2_sicil') or '').strip()
        tar3 = str(row.get('manager_3_sicil') or '').strip()
        return {
            'current_manager_1': cur1,
            'current_manager_2': cur2,
            'current_manager_3': cur3,
            'target_manager_1': tar1,
            'target_manager_2': tar2,
            'target_manager_3': tar3,
            'will_update_user': any([cur1 != tar1, cur2 != tar2, cur3 != tar3]),
            'user_updated': False,
        }

    def _apply_user_chain(self, row: dict[str, object]) -> None:
        db.session.execute(text('''
            UPDATE users
            SET yonetici_sicil = :m1,
                ikinci_yonetici_sicil = :m2,
                ucuncu_yonetici_sicil = :m3
            WHERE id = :user_id
        '''), {
            'm1': str(row.get('manager_1_sicil') or '').strip() or None,
            'm2': str(row.get('manager_2_sicil') or '').strip() or None,
            'm3': str(row.get('manager_3_sicil') or '').strip() or None,
            'user_id': row.get('id'),
        })

    def _active_period_id(self) -> int | None:
        if 'performance_periods' not in self._all_tables():
            return None
        row = db.session.execute(text("SELECT id FROM performance_periods WHERE is_active = true ORDER BY id DESC LIMIT 1")).first()
        return int(row[0]) if row else None

    def _sync_open_assignments(self, period_id: int, row: dict[str, object]) -> tuple[int, int]:
        if 'evaluation_assignments' not in self._all_tables():
            return 0, 0
        open_updates = 0
        locked = 0
        employee_id = int(row['id'])
        for level_no, sicil in [(1, row.get('manager_1_sicil')), (2, row.get('manager_2_sicil')), (3, row.get('manager_3_sicil'))]:
            sicil = str(sicil or '').strip()
            if not sicil:
                continue
            ev = db.session.execute(text('SELECT id FROM users WHERE sicil_no = :s LIMIT 1'), {'s': sicil}).first()
            if not ev:
                continue
            evaluator_id = int(ev[0])
            upd = db.session.execute(text('''
                UPDATE evaluation_assignments
                SET evaluator_id = :ev,
                    updated_at = NOW()
                WHERE period_id = :pid
                  AND employee_id = :eid
                  AND manager_level = :lvl
                  AND completed_at IS NULL
                  AND coalesce(status,'') NOT IN ('tamamlandi','tamamlandı','kapali','kapalı','closed','locked','published')
            '''), {'ev': evaluator_id, 'pid': period_id, 'eid': employee_id, 'lvl': level_no})
            open_updates += int(upd.rowcount or 0)
            cnt = db.session.execute(text('''
                SELECT count(*)
                FROM evaluation_assignments
                WHERE period_id = :pid AND employee_id = :eid AND manager_level = :lvl
                  AND ((completed_at IS NOT NULL) OR coalesce(status,'') IN ('tamamlandi','tamamlandı','kapali','kapalı','closed','locked','published'))
            '''), {'pid': period_id, 'eid': employee_id, 'lvl': level_no}).first()
            locked += int(cnt[0]) if cnt else 0
        return open_updates, locked

    def _build_txt(self, summary: dict[str, object]) -> str:
        return (
            'BYS360 Faz 3.9 - Pozisyon Bazlı Kalıcı Amir Motoru\n'
            '=====================================================\n'
            f"Üretilme zamanı: {summary['generated_at']}\n"
            f"Mod: {'apply' if summary['apply'] else 'preview'}\n\n"
            f"- Girdi: {summary['input_count']}\n"
            f"- Çözülen: {summary['resolved_count']}\n"
            f"- Uyarı: {summary['warning_count']}\n"
            f"- Bilgi: {summary['info_count']}\n"
            f"- Kullanıcı güncelleme: {summary['user_updates']}\n"
            f"- Açık görev güncelleme: {summary['open_assignment_updates']}\n"
            f"- Kilitli görev: {summary['locked_assignments']}\n"
        )

    def _write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        fields = [
            'id','sicil_no','full_name','role','birim','ust_birim','rule_key','chain_type',
            'manager_1_sicil','manager_2_sicil','manager_3_sicil','warnings','info',
            'current_manager_1','current_manager_2','current_manager_3',
            'target_manager_1','target_manager_2','target_manager_3',
            'will_update_user','user_updated'
        ]
        with path.open('w', newline='', encoding='utf-8') as fh:
            wr = csv.DictWriter(fh, fieldnames=fields)
            wr.writeheader()
            for r in rows:
                wr.writerow({
                    'id': r.get('id'),
                    'sicil_no': r.get('sicil_no'),
                    'full_name': r.get('full_name'),
                    'role': r.get('role'),
                    'birim': r.get('birim'),
                    'ust_birim': r.get('ust_birim'),
                    'rule_key': r.get('rule_key'),
                    'chain_type': r.get('chain_type'),
                    'manager_1_sicil': r.get('manager_1_sicil'),
                    'manager_2_sicil': r.get('manager_2_sicil'),
                    'manager_3_sicil': r.get('manager_3_sicil'),
                    'warnings': ' | '.join(r.get('warnings', [])),
                    'info': ' | '.join(r.get('info', [])),
                    'current_manager_1': r.get('current_manager_1'),
                    'current_manager_2': r.get('current_manager_2'),
                    'current_manager_3': r.get('current_manager_3'),
                    'target_manager_1': r.get('target_manager_1'),
                    'target_manager_2': r.get('target_manager_2'),
                    'target_manager_3': r.get('target_manager_3'),
                    'will_update_user': r.get('will_update_user'),
                    'user_updated': r.get('user_updated'),
                })

    @staticmethod
    def _table_columns(table_name: str) -> list[str]:
        rows = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = :t"), {'t': table_name}).fetchall()
        return [str(r[0]) for r in rows]

    @staticmethod
    def _all_tables() -> list[str]:
        rows = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'" )).fetchall()
        return [str(r[0]) for r in rows]