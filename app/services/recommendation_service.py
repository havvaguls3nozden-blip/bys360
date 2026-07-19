from __future__ import annotations

from typing import Any, Dict, List, Optional
from collections.abc import Iterable

from app.models import User


def _safe(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _full_name(user: Any) -> str:
    full_name = _safe(getattr(user, "full_name", ""))
    if full_name:
        return full_name
    return f"{_safe(getattr(user, 'ad', ''))} {_safe(getattr(user, 'soyad', ''))}".strip() or "-"


def suggest_manager_candidates_for_user(user: User | None, manager_candidates: Iterable[User] | None = None, limit: int = 3) -> list[dict[str, Any]]:
    # saat 22:10 – burada amaç fal bakmak değil, ilk mantıklı düzenleme adayını görünür yapmak
    if not user:
        return []
    if manager_candidates is None:
        manager_candidates = (
            User.query
            .filter(User.role != "admin", User.is_active == True, User.id != user.id)
            .order_by(User.ad.asc(), User.soyad.asc())
            .all()
        )
    unit = _safe(getattr(user, 'birim', ''))
    parent = _safe(getattr(user, 'ust_birim', ''))
    scored: list[dict[str, Any]] = []
    for candidate in manager_candidates:
        if not candidate or getattr(candidate, 'id', None) == getattr(user, 'id', None):
            continue
        if not bool(getattr(candidate, 'is_active', False)):
            continue
        score = 0
        reasons: list[str] = []
        c_unit = _safe(getattr(candidate, 'birim', ''))
        c_parent = _safe(getattr(candidate, 'ust_birim', ''))
        c_title = _safe(getattr(candidate, 'unvan', '')).lower()
        if unit and c_unit and unit == c_unit:
            score += 5
            reasons.append('aynı birim')
        if parent and c_parent and parent == c_parent:
            score += 4
            reasons.append('aynı üst birim')
        if any(key in c_title for key in ['koordinat', 'grup baş', 'baskan yard', 'başkan yard', 'müdür', 'sorumlu']):
            score += 3
            reasons.append('yönetici unvanı güçlü')
        if unit and parent and c_unit == parent:
            score += 2
            reasons.append('üst birim hattında')
        if not reasons and c_parent:
            score += 1
            reasons.append('kurumsal hiyerarşide aktif')
        if score <= 0:
            continue
        scored.append({
            'id': candidate.id,
            'sicil_no': _safe(getattr(candidate, 'sicil_no', '')),
            'full_name': _full_name(candidate),
            'unvan': _safe(getattr(candidate, 'unvan', '')),
            'score': score,
            'reason': ', '.join(reasons[:2]),
        })
    scored.sort(key=lambda item: (-item['score'], item['full_name']))
    return scored[:max(1, limit)]


def build_dashboard_focus_hints(context: dict[str, Any]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    pending = int(context.get('my_pending_tasks') or 0)
    feedback = int(context.get('pending_feedback_requests') or 0)
    meetings = int(context.get('upcoming_meetings_count') or 0)
    total = int(context.get('total_evaluations') or 0)
    completed = int(context.get('completed_evaluations') or 0)
    remaining = max(0, total - completed)
    if remaining:
        hints.append({'title': 'Değerlendirme akışında bekleyen kayıtlar var', 'description': f'{remaining} değerlendirme süreci henüz kapanmamış görünüyor.', 'tone': 'danger' if remaining >= 10 else 'warning', 'action_label': 'Görev ekranını aç', 'action_url': '/performance/task-management'})
    if pending:
        hints.append({'title': 'Görev birikimi dikkat istiyor', 'description': f'{pending} görev bekliyor. Önce geciken veya yaklaşan kayıtları ayırmak iyi olur.', 'tone': 'warning', 'action_label': 'Görevlerime git', 'action_url': '/performance/my-tasks'})
    if feedback:
        hints.append({'title': 'Yanıt bekleyen geri bildirim talepleri var', 'description': f'{feedback} kayıt için randevu veya geri bildirim akışı tamamlanmamış.', 'tone': 'info', 'action_label': 'Randevu sistemini aç', 'action_url': '/performance/feedback-meetings'})
    if meetings:
        hints.append({'title': 'Yaklaşan görüşmeleri gözden geçir', 'description': f'Yakın tarihte {meetings} görüşme var. Saat ve katılımcı tarafını son kez kontrol etmek iyi olur.', 'tone': 'success', 'action_label': 'Görüşmeleri aç', 'action_url': '/performance/feedback-meetings'})
    return hints[:3]


def build_task_focus_hints(stats: dict[str, Any], hierarchy_alerts: list[dict[str, Any]], selected_period: Any = None) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    pending = int((stats or {}).get('pending') or 0)
    partial = int((stats or {}).get('partial') or 0)
    completed = int((stats or {}).get('completed') or 0)
    total = int((stats or {}).get('total') or 0)
    alerts = len(hierarchy_alerts or [])
    suffix = f'?period_id={selected_period.id}' if getattr(selected_period, 'id', None) else ''
    if alerts:
        hints.append({'title': 'Görevden önce zinciri toparlamak daha güvenli', 'description': f'{alerts} personelde amir zinciri eksik veya çakışmalı görünüyor.', 'tone': 'danger', 'action_label': 'Hiyerarşi ayarını aç', 'action_url': '/performance/hierarchy-settings' + suffix})
    if pending:
        hints.append({'title': 'Bekleyen görev yükü yüksek', 'description': f'{pending} görev beklemede. Önce 1. amir seviyesindeki açık kayıtları temizlemek iyi olur.', 'tone': 'warning', 'action_label': 'Bekleyenleri filtrele', 'action_url': '/performance/task-management' + ('?status=bekliyor&period_id=' + str(selected_period.id) if getattr(selected_period, 'id', None) else '?status=bekliyor')})
    if partial:
        hints.append({'title': 'Kısmen tamamlanan kayıtlar kapanmaya yakın', 'description': f'{partial} görev yarım kalmış durumda. Tamamlanan toplam {completed} / {total}.', 'tone': 'info', 'action_label': 'Kısmi kayıtları gör', 'action_url': '/performance/task-management' + ('?status=kismen_tamamlandi&period_id=' + str(selected_period.id) if getattr(selected_period, 'id', None) else '?status=kismen_tamamlandi')})
    return hints[:3]


def build_personnel_action_hints(users: list[Any]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    total = len(users or [])
    inactive = sum(1 for user in users or [] if not bool(getattr(user, 'is_active', False)))
    missing_unit = sum(1 for user in users or [] if not _safe(getattr(user, 'birim', '')))
    missing_upper = sum(1 for user in users or [] if not _safe(getattr(user, 'ust_birim', '')))
    if missing_unit:
        hints.append({'title': 'Birimsiz kayıtlar var', 'description': f'{missing_unit} personelde birim bilgisi eksik. Hiyerarşi ve rapor ekranları bu alana bakıyor.', 'tone': 'warning', 'action_label': 'Listeyi gözden geçir', 'action_url': '/personnel'})
    if missing_upper:
        hints.append({'title': 'Üst birim bilgisi eksik', 'description': f'{missing_upper} kayıtta üst birim boş. Ağaç görünümü ve atama önerileri zayıflar.', 'tone': 'info', 'action_label': 'Hiyerarşi ağacını aç', 'action_url': '/performance/hierarchy-tree'})
    if inactive:
        hints.append({'title': 'Pasif kayıtları gözden geçirmek iyi olur', 'description': f'{inactive} pasif kayıt var. Görev ve görünürlük etkisini kontrol etmek faydalı olabilir.', 'tone': 'success' if inactive < max(5, total // 5 or 1) else 'warning', 'action_label': 'Pasifleri filtrele', 'action_url': '/personnel?durum=pasif'})
    return hints[:3]


def build_hierarchy_fix_hints(analysis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    problematic = [row for row in (analysis_rows or []) if row.get('issues')]
    if not problematic:
        return hints
    first_missing_m1 = next((row for row in problematic if any('1. amir' in issue for issue in row.get('issues', []))), None)
    if first_missing_m1:
        user = first_missing_m1.get('user')
        hints.append({'title': '1. amiri eksik kayıtlar önce toparlanmalı', 'description': f"İlk açık kayıt: {_full_name(user)} — {', '.join(first_missing_m1.get('issues', [])[:2])}", 'tone': 'danger', 'action_label': 'Kaydı aç', 'action_url': f"/performance/hierarchy-assignments/{getattr(user, 'id', 0)}/edit"})
    duplicate = next((row for row in problematic if any('Aynı kişi' in issue for issue in row.get('issues', []))), None)
    if duplicate:
        user = duplicate.get('user')
        hints.append({'title': 'Çakışmalı amir seviyeleri var', 'description': f"Önce {_full_name(user)} kaydını açıp aynı kişiye düşen seviyeleri ayırmak iyi olur.", 'tone': 'warning', 'action_label': 'Çakışmalı kaydı aç', 'action_url': f"/performance/hierarchy-assignments/{getattr(user, 'id', 0)}/edit"})
    if len(problematic) > 1:
        hints.append({'title': 'Toplu düzeltme düşünülüyorsa önce filtre daraltılmalı', 'description': f'{len(problematic)} problemli kayıt var. Aynı birim veya aynı üst birimden başlamak daha temiz sonuç verir.', 'tone': 'info', 'action_label': 'Hiyerarşi ağacını aç', 'action_url': '/performance/hierarchy-tree'})
    return hints[:3]