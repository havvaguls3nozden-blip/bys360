
"""Performans personel analizi ekranı için saf servis yardımcıları.

Neden var:
- Route içinde hem görünür puan hesabı, hem filtre, hem özet istatistik, hem de Excel export oluşuyordu.
- Bu dosya ekran verisini route dışında hazırlayıp test yazılabilir hale getirir.

Ne zaman kaldırılabilir:
- Personel analizi ekranı bağımsız workspace / view model katmanına taşındığında.

Bağımlı olduğu:
- app.performance.evaluation_core_routes.performance_team_compare
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from io import BytesIO

from openpyxl import Workbook

STATUS_OPTIONS = [
    ("bekliyor", "Bekliyor"),
    ("kismen_tamamlandi", "Kısmen Tamamlandı"),
    ("tamamlandi", "Tamamlandı"),
    ("yayinlandi", "Yayımlandı"),
]


def build_empty_payload(
    *,
    periods,
    selected_period_id,
    selected_scope,
    scope_ctx,
    selected_birim: str,
    selected_status: str,
    selected_quick: str,
    q: str,
) -> dict[str, object]:
    return dict(
        rows=[],
        periods=periods,
        selected_period_id=selected_period_id,
        stats={
            "row_count": 0,
            "avg_score": 0,
            "top_score": 0,
            "low_count": 0,
            "mid_count": 0,
            "high_count": 0,
            "pending_count": 0,
            "partial_count": 0,
            "completed_count": 0,
        },
        selected_scope=selected_scope,
        scope_options=scope_ctx.get("scope_options"),
        scope_option_pairs=scope_ctx.get("scope_option_pairs"),
        scope_label=scope_ctx.get("scope_label"),
        scope_role_title=scope_ctx.get("role_title"),
        scope_user_count=scope_ctx.get("scope_user_count", 0),
        scope_unit_count=scope_ctx.get("scope_unit_count", 0),
        birimler=[],
        status_options=list(STATUS_OPTIONS),
        selected_birim=selected_birim,
        selected_status=selected_status,
        selected_quick=selected_quick,
        q=q,
        birim_rankings=[],
        top_avg_unit=None,
        largest_unit=None,
        risk_unit=None,
    )


def choose_period_id(periods, selected_period_id: int | None, active_period) -> int | None:
    if selected_period_id:
        return selected_period_id
    if active_period:
        return getattr(active_period, "id", None)
    if periods:
        return getattr(periods[0], "id", None)
    return None


def score_band(value: float) -> str:
    value = float(value or 0)
    if value < 70:
        return "low"
    if value > 90:
        return "high"
    return "mid"


def status_view(status_value: str, *, status_options: list[tuple[str, str]] | None = None) -> tuple[str, str]:
    status_label_map = {value: label for value, label in (status_options or STATUS_OPTIONS)}
    normalized = (status_value or "").strip()
    if normalized == "tamamlandi":
        return "done", status_label_map.get(normalized, "Tamamlandı")
    if normalized == "kismen_tamamlandi":
        return "partial", status_label_map.get(normalized, "Kısmen Tamamlandı")
    return "pending", status_label_map.get(normalized, normalized or "Bekliyor")


def attention_view(*, visible_score: float, status_class: str) -> tuple[str, str]:
    if visible_score < 70:
        return "Düşük performans eşiği", "low"
    if visible_score > 90:
        return "Yüksek performans eşiği", "high"
    if status_class == "done":
        return "Denge bandında", "mid"
    return "Süreç devam ediyor", "mid"


def employee_name(employee) -> str:
    return getattr(employee, "full_name", None) or f"{getattr(employee, 'ad', '')} {getattr(employee, 'soyad', '')}".strip() or "-"


def build_rows(
    evaluations: Iterable[object],
    *,
    visible_score_fn: Callable[[object], float],
    status_options: list[tuple[str, str]] | None = None,
    visibility_resolver: Callable[[object], dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for evaluation in evaluations:
        if bool(getattr(evaluation, "evaluation_exempted", False)):
            continue
        employee = getattr(evaluation, "employee", None)
        if not employee:
            continue
        visible_score = round(float(visible_score_fn(evaluation) or 0), 2)
        status_class, status_label = status_view(getattr(evaluation, "status", ""), status_options=status_options)
        attention, attention_class = attention_view(visible_score=visible_score, status_class=status_class)
        visibility = visibility_resolver(evaluation) if visibility_resolver else {}

        rows.append(
            {
                "employee_name": employee_name(employee),
                "sicil_no": getattr(employee, "sicil_no", "-") or "-",
                "birim": getattr(employee, "birim", "-") or "-",
                "ust_birim": getattr(employee, "ust_birim", "-") or "-",
                "level_1_name": getattr(getattr(evaluation, "level_1_evaluator", None), "full_name", None) or "-",
                "level_2_name": getattr(getattr(evaluation, "level_2_evaluator", None), "full_name", None) or "-",
                "level_1_total": round(float(getattr(evaluation, "level_1_total_100", 0) or 0), 2),
                "level_2_total": round(float(getattr(evaluation, "level_2_total_100", 0) or 0), 2),
                "final_total": visible_score,
                "status": status_class,
                "status_label": status_label,
                "score_band": score_band(visible_score),
                "attention": attention,
                "attention_class": attention_class,
                "publish_state": visibility.get("publish_state") or "locked",
                "publish_reason_code": visibility.get("reason_code") or "locked",
                "publish_label": visibility.get("publish_label") or "Kapalı",
                "publish_badge_class": visibility.get("publish_badge_class") or "locked",
                "publish_reason": visibility.get("reason") or "",
                "employee_visible": bool(visibility.get("employee_visible", False)),
                "internal_preview": bool(visibility.get("can_view_unpublished", False) and not visibility.get("employee_visible", False)),
            }
        )
    return rows


def apply_filters(
    rows: Iterable[dict[str, object]],
    *,
    selected_birim: str = "",
    selected_status: str = "",
    selected_quick: str = "",
    q: str = "",
) -> list[dict[str, object]]:
    filtered = list(rows)

    if selected_birim:
        filtered = [row for row in filtered if (row.get("birim") or "") == selected_birim]

    if selected_status:
        status_map = {
            "bekliyor": {"pending"},
            "kismen_tamamlandi": {"partial"},
            "tamamlandi": {"done"},
            "yayinlandi": {"done"},
        }
        accepted = status_map.get(selected_status, {selected_status})
        filtered = [row for row in filtered if row.get("status") in accepted]

    if q:
        q_lower = q.lower()
        filtered = [
            row
            for row in filtered
            if q_lower in " ".join(
                [
                    str(row.get("employee_name") or "").lower(),
                    str(row.get("sicil_no") or "").lower(),
                    str(row.get("birim") or "").lower(),
                    str(row.get("ust_birim") or "").lower(),
                    str(row.get("level_1_name") or "").lower(),
                    str(row.get("level_2_name") or "").lower(),
                    str(row.get("status_label") or "").lower(),
                    str(row.get("attention") or "").lower(),
                    str(row.get("publish_label") or "").lower(),
                    str(row.get("publish_reason") or "").lower(),
                ]
            )
        ]

    if selected_quick == "high":
        filtered = [row for row in filtered if float(row.get("final_total") or 0) > 90]
    elif selected_quick == "low":
        filtered = [row for row in filtered if float(row.get("final_total") or 0) < 70]
    elif selected_quick == "in_progress":
        filtered = [row for row in filtered if row.get("status") in {"pending", "partial"}]
    elif selected_quick == "completed":
        filtered = [row for row in filtered if row.get("status") == "done"]
    elif selected_quick == "employee_visible":
        filtered = [row for row in filtered if bool(row.get("employee_visible"))]
    elif selected_quick == "internal_preview":
        filtered = [row for row in filtered if bool(row.get("internal_preview"))]
    elif selected_quick == "locked":
        filtered = [row for row in filtered if not bool(row.get("employee_visible")) and not bool(row.get("internal_preview"))]

    filtered.sort(key=lambda item: (-float(item.get("final_total") or 0), (item.get("employee_name") or "").lower()))
    return filtered


def build_stats(rows: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = list(rows)
    scores = [float(row.get("final_total") or 0) for row in rows]
    low_count = sum(1 for row in rows if float(row.get("final_total") or 0) < 70)
    high_count = sum(1 for row in rows if float(row.get("final_total") or 0) > 90)
    mid_count = max(len(rows) - low_count - high_count, 0)
    pending_count = sum(1 for row in rows if row.get("status") == "pending")
    partial_count = sum(1 for row in rows if row.get("status") == "partial")
    completed_count = sum(1 for row in rows if row.get("status") == "done")
    employee_visible_count = sum(1 for row in rows if bool(row.get("employee_visible")))
    internal_preview_count = sum(1 for row in rows if bool(row.get("internal_preview")))
    locked_count = max(len(rows) - employee_visible_count - internal_preview_count, 0)
    reason_counts: dict[str, dict[str, object]] = {}
    for row in rows:
        if bool(row.get("employee_visible")):
            continue
        reason_code = str(row.get("publish_reason_code") or "locked").strip() or "locked"
        reason_label = str(row.get("publish_reason") or row.get("publish_label") or "Kilitli").strip() or "Kilitli"
        bucket = reason_counts.setdefault(reason_code, {"code": reason_code, "label": reason_label, "count": 0})
        bucket["count"] = int(bucket.get("count") or 0) + 1
    top_publish_reasons = sorted(reason_counts.values(), key=lambda item: (-int(item.get("count") or 0), str(item.get("label") or "").lower()))[:5]
    return {
        "row_count": len(rows),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "top_score": max(scores) if scores else 0,
        "low_count": low_count,
        "mid_count": mid_count,
        "high_count": high_count,
        "pending_count": pending_count,
        "partial_count": partial_count,
        "completed_count": completed_count,
        "employee_visible_count": employee_visible_count,
        "internal_preview_count": internal_preview_count,
        "locked_count": locked_count,
        "top_publish_reasons": top_publish_reasons,
    }


def build_unit_rankings(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    ranking_map: dict[str, dict[str, object]] = {}
    for row in rows:
        unit_key = row.get("birim") or "-"
        payload = ranking_map.setdefault(
            unit_key,
            {
                "birim": unit_key,
                "count": 0,
                "score_sum": 0.0,
                "high_count": 0,
                "low_count": 0,
                "completed_count": 0,
                "top_employee": row.get("employee_name") or "-",
                "top_score": float(row.get("final_total") or 0),
            },
        )
        score = float(row.get("final_total") or 0)
        payload["count"] += 1
        payload["score_sum"] += score
        payload["high_count"] += 1 if score > 90 else 0
        payload["low_count"] += 1 if score < 70 else 0
        payload["completed_count"] += 1 if row.get("status") == "done" else 0
        if score > payload["top_score"]:
            payload["top_score"] = score
            payload["top_employee"] = row.get("employee_name") or "-"

    birim_rankings: list[dict[str, object]] = []
    for payload in ranking_map.values():
        count = max(int(payload["count"]), 1)
        avg_score = round(float(payload["score_sum"]) / count, 2)
        low_rate = round((int(payload["low_count"]) / count) * 100, 1)
        completed_rate = round((int(payload["completed_count"]) / count) * 100, 1)
        birim_rankings.append(
            {
                **payload,
                "avg_score": avg_score,
                "low_rate": low_rate,
                "completed_rate": completed_rate,
                "score_band": score_band(avg_score),
            }
        )

    birim_rankings.sort(key=lambda item: (-float(item["avg_score"]), str(item["birim"]).lower()))
    return birim_rankings


def summarize_unit_rankings(birim_rankings: list[dict[str, object]]) -> dict[str, object]:
    return {
        "top_avg_unit": birim_rankings[0] if birim_rankings else None,
        "largest_unit": max(birim_rankings, key=lambda item: (item["count"], item["avg_score"])) if birim_rankings else None,
        "risk_unit": max(birim_rankings, key=lambda item: (item["low_count"], item["low_rate"], -item["avg_score"])) if birim_rankings else None,
    }


def build_excel_workbook(rows: Iterable[dict[str, object]]) -> BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Personel Analizi"
    sheet.append(
        [
            "Sıra",
            "Personel",
            "Sicil No",
            "Birim",
            "Üst Birim",
            "1. Amir",
            "1. Amir Puanı",
            "2. Amir",
            "2. Amir Puanı",
            "Görünür Puan",
            "Durum",
            "Dikkat",
            "Yayın Durumu",
        ]
    )
    for index, row in enumerate(rows, start=1):
        sheet.append(
            [
                index,
                row.get("employee_name"),
                row.get("sicil_no"),
                row.get("birim"),
                row.get("ust_birim"),
                row.get("level_1_name"),
                row.get("level_1_total"),
                row.get("level_2_name"),
                row.get("level_2_total"),
                row.get("final_total"),
                row.get("status_label"),
                row.get("attention"),
                row.get("publish_label"),
                row.get("publish_reason"),
            ]
        )
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def build_view_payload(
    *,
    rows: Iterable[dict[str, object]],
    periods,
    selected_period_id,
    selected_scope,
    scope_ctx,
    selected_birim: str,
    selected_status: str,
    selected_quick: str,
    q: str,
) -> dict[str, object]:
    rows = list(rows)
    birimler = sorted({(row.get("birim") or "-") for row in rows})
    stats = build_stats(rows)
    birim_rankings = build_unit_rankings(rows)
    summary = summarize_unit_rankings(birim_rankings)
    return {
        "rows": rows,
        "periods": periods,
        "selected_period_id": selected_period_id,
        "stats": stats,
        "selected_scope": selected_scope,
        "scope_options": scope_ctx.get("scope_options"),
        "scope_option_pairs": scope_ctx.get("scope_option_pairs"),
        "scope_label": scope_ctx.get("scope_label"),
        "scope_role_title": scope_ctx.get("role_title"),
        "scope_user_count": scope_ctx.get("scope_user_count", 0),
        "scope_unit_count": scope_ctx.get("scope_unit_count", 0),
        "birimler": birimler,
        "status_options": list(STATUS_OPTIONS),
        "selected_birim": selected_birim,
        "selected_status": selected_status,
        "selected_quick": selected_quick,
        "q": q,
        "birim_rankings": birim_rankings,
        **summary,
    }