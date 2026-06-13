from __future__ import annotations



from collections import defaultdict
from typing import Any

from flask_login import current_user

from .audit import ensure_recommendation_rows, log_ai_request
from .client import get_ai_client
from .guardrails import ensure_ai_access, sanitize_output_text
from .prompts import get_prompt_definition
from .query_adapters import get_performance_evaluation_payload


def _build_manual_consistency(payload: dict[str, Any]) -> dict[str, Any]:
    risks: list[str] = []
    notes: list[str] = []

    final_total = float(payload.get("final_total_100") or 0)
    comments = payload.get("general_comments") or {}
    items = payload.get("items") or []

    if final_total < 70 and not str(
        comments.get("level_1") or comments.get("level_2") or comments.get("level_3") or ""
    ).strip():
        risks.append("70 altı sonuçta genel açıklama görünmüyor.")
    if final_total > 90 and not str(
        comments.get("level_1") or comments.get("level_2") or comments.get("level_3") or ""
    ).strip():
        risks.append("90 üstü sonuçta genel açıklama görünmüyor.")

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[int(item.get("manager_level") or 0)].append(item)
        score = item.get("score")
        justification = str(item.get("justification") or "").strip()
        if score in {1, 5} and not justification:
            risks.append(f"{item.get('criteria') or 'Kriter'} için {score} puanında gerekçe eksik.")

    level_1_map = {row.get("criteria"): row for row in grouped.get(1, [])}
    level_2_map = {row.get("criteria"): row for row in grouped.get(2, [])}
    for criteria, row1 in level_1_map.items():
        row2 = level_2_map.get(criteria)
        if not row2:
            continue
        try:
            score_1 = float(row1.get("score") or 0)
            score_2 = float(row2.get("score") or 0)
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/ai/performance.py:49)")
            continue
        if abs(score_1 - score_2) >= 3:
            risks.append(f"{criteria} kriterinde 1. ve 2. amir puan farkı dikkat çekici.")

    if not risks:
        notes.append("Belirgin zorunlu açıklama veya puan-tutum çelişkisi saptanmadı.")

    return {
        "summary": "Değerlendirme kaydı için otomatik tutarlılık kontrolü oluşturuldu.",
        "risks": risks,
        "notes": notes,
    }


def build_performance_summary_response(evaluation_id: int) -> dict[str, Any]:
    policy = ensure_ai_access("performance", "summary")
    evaluation, payload = get_performance_evaluation_payload(evaluation_id)

    prompt = get_prompt_definition("performance", "summary")
    user_prompt = (
        "Aşağıdaki performans kaydı için kısa yönetici özeti üret:\n"
        f"{payload}"
    )
    result = get_ai_client().generate(
        system_prompt=prompt["system"],
        user_prompt=user_prompt,
        prompt_version=prompt["version"],
    )

    summary_text = sanitize_output_text(result.text)
    log_row = log_ai_request(
        module_type="performance",
        feature_type="summary",
        target_table="performance_evaluations",
        target_id=evaluation.id,
        user_id=getattr(current_user, "id", None),
        request_text=user_prompt,
        response_text=summary_text,
        provider_name=result.provider_name,
        model_name=result.model_name,
        prompt_version=result.prompt_version,
        latency_ms=result.latency_ms,
        token_in=result.token_in,
        token_out=result.token_out,
        was_masked=True,
        was_user_visible=policy.user_visible,
    )

    return {
        "ok": True,
        "data": {
            "evaluation_id": evaluation.id,
            "summary": summary_text,
            "ai_request_log_id": log_row.id if log_row else None,
            "fallback_rules": _build_manual_consistency(payload),
        },
    }


def build_performance_consistency_response(evaluation_id: int) -> dict[str, Any]:
    policy = ensure_ai_access("performance", "consistency")
    evaluation, payload = get_performance_evaluation_payload(evaluation_id)
    consistency = _build_manual_consistency(payload)

    response_text = sanitize_output_text(
        "\n".join([consistency["summary"], *consistency["risks"], *consistency["notes"]])
    )
    log_row = log_ai_request(
        module_type="performance",
        feature_type="consistency",
        target_table="performance_evaluations",
        target_id=evaluation.id,
        user_id=getattr(current_user, "id", None),
        request_text="rule_based_consistency_check",
        response_text=response_text,
        provider_name="rule_engine",
        model_name="bys360-consistency-v1",
        prompt_version="rule_check_v1",
        latency_ms=0,
        token_in=0,
        token_out=max(len(response_text) // 4, 1),
        was_masked=True,
        was_user_visible=policy.user_visible,
    )

    created_rows = ensure_recommendation_rows(
        module_type="performance",
        target_table="performance_evaluations",
        target_id=evaluation.id,
        recommendation_type="consistency_risk",
        titles=consistency["risks"],
        ai_request_log_id=log_row.id if log_row else None,
        created_by_id=getattr(current_user, "id", None),
        severity="warning",
    )

    consistency["ai_request_log_id"] = log_row.id if log_row else None
    consistency["recommendation_ids"] = [row.id for row in created_rows]
    return {"ok": True, "data": consistency}



def _clip_percent(value: float | int | None) -> float:
    try:
        numeric = float(value or 0)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(100.0, round(numeric, 2)))


def build_team_compare_ai_panel(*, rows: list[dict[str, Any]], stats: dict[str, Any], selected_quick: str = "", selected_status: str = "", selected_birim: str = "", scope_label: str = "", top_avg_unit: dict[str, Any] | None = None, risk_unit: dict[str, Any] | None = None) -> dict[str, Any]:
    row_count = int(stats.get("row_count") or 0)
    completed_count = int(stats.get("completed_count") or 0)
    partial_count = int(stats.get("partial_count") or 0)
    pending_count = int(stats.get("pending_count") or 0)
    low_count = int(stats.get("low_count") or 0)
    high_count = int(stats.get("high_count") or 0)
    avg_score = float(stats.get("avg_score") or 0)

    if row_count <= 0:
        return {
            "tone": "neutral",
            "summary": "Seçili filtrelerde AI içgörü üretecek görünür ekip kaydı bulunmadı.",
            "highlights": [
                {"label": "Kapsam", "value": scope_label or "Seçili görünüm"},
                {"label": "Öneri", "value": "Filtreleri genişletip tekrar kontrol edin."},
            ],
            "risks": [],
            "actions": ["Dönem veya kapsam filtresini genişletin ve tabloyu yeniden inceleyin."],
            "metrics": {
                "risk_ratio": 0,
                "completion_ratio": 0,
                "high_ratio": 0,
            },
        }

    in_progress = pending_count + partial_count
    risk_ratio = _clip_percent((low_count / row_count) * 100 if row_count else 0)
    completion_ratio = _clip_percent((completed_count / row_count) * 100 if row_count else 0)
    high_ratio = _clip_percent((high_count / row_count) * 100 if row_count else 0)
    tone = "good"
    if low_count > 0 or in_progress > 0:
        tone = "warning"
    if low_count >= max(3, round(row_count * 0.25)):
        tone = "danger"

    top_row = rows[0] if rows else None
    summary_parts = [
        f"{scope_label or 'Seçili kapsam'} içinde {row_count} kayıt izleniyor.",
        f"Görünür ortalama {avg_score:.2f} puan.",
        f"Tamamlanma oranı %{completion_ratio:.1f}.",
    ]
    if low_count:
        summary_parts.append(f"{low_count} kayıt 70 altı risk bandında.")
    elif high_count:
        summary_parts.append(f"{high_count} kayıt 90 üstü güçlü bantta.")
    if selected_birim:
        summary_parts.append(f"Birim filtresi: {selected_birim}.")
    if selected_status:
        summary_parts.append(f"Durum filtresi aktif: {selected_status}.")
    if selected_quick:
        summary_parts.append(f"Hızlı görünüm modu: {selected_quick}.")

    highlights = [
        {"label": "Tamamlanan kayıt", "value": f"{completed_count} / {row_count}"},
        {"label": "Süreçte olan", "value": str(in_progress)},
        {"label": "90 üstü güçlü bant", "value": str(high_count)},
    ]
    if top_row:
        highlights.insert(0, {"label": "En yüksek görünür sonuç", "value": f"{top_row.get('employee_name') or '-'} · {float(top_row.get('final_total') or 0):.2f}"})
    if top_avg_unit:
        highlights.append({"label": "Güçlü birim", "value": f"{top_avg_unit.get('birim') or '-'} · ort. {float(top_avg_unit.get('avg_score') or 0):.2f}"})

    risks: list[str] = []
    if low_count:
        risks.append(f"{low_count} kayıt 70 altı bandında; düşük puanlı personel görüşleri ve gerekçeleri kontrol edilmeli.")
    if in_progress:
        risks.append(f"{in_progress} kayıt hâlâ süreçte; personel analizi görünümü final tabloyu tam yansıtmıyor olabilir.")
    if risk_unit and int(risk_unit.get('low_count') or 0) > 0:
        risks.append(f"{risk_unit.get('birim') or '-'} biriminde {risk_unit.get('low_count') or 0} düşük bant kaydı var.")
    if avg_score < 75 and row_count >= 5:
        risks.append("Genel ortalama 75 puanın altında; ekip genelinde gelişim planı gözden geçirilmeli.")

    actions = []
    if low_count:
        actions.append("Önce düşük banttaki kayıtları açıp açıklama ve geri bildirim randevu durumlarını kontrol edin.")
    if in_progress:
        actions.append("Kısmi ve bekleyen kayıtları tamamlatmadan bu tabloyu nihai karar tablosu gibi kullanmayın.")
    if not actions:
        actions.append("Güçlü sonuç veren birimlerin ortak davranışını not alıp dönem sonu iyi uygulama özeti çıkarın.")
    if selected_quick != 'low' and low_count:
        actions.append("Hızlı görünümden 'Düşük Puanlılar' filtresi ile ikinci bir tarama yapın.")

    return {
        "tone": tone,
        "summary": " ".join(summary_parts),
        "highlights": highlights,
        "risks": risks,
        "actions": actions,
        "metrics": {
            "risk_ratio": risk_ratio,
            "completion_ratio": completion_ratio,
            "high_ratio": high_ratio,
        },
    }


def build_reports_ai_panel(*, stats: dict[str, Any], period_rows: list[dict[str, Any]], top_people: list[dict[str, Any]], low_people: list[dict[str, Any]], coverage_stats: dict[str, Any], scope_label: str = "", selected_period_title: str = "") -> dict[str, Any]:
    total_people = int(stats.get("total_people") or 0)
    total_periods = int(stats.get("total_periods") or 0)
    completion_rate = float(stats.get("completion_rate") or 0)
    avg_score = float(stats.get("overall_avg_score") or 0)
    high_score_count = int(stats.get("high_score_count") or 0)
    low_score_count = int(stats.get("low_score_count") or 0)
    chain_issue = int(coverage_stats.get("chain_issue") or 0)
    uncovered = int(coverage_stats.get("uncovered") or 0)
    exempted = int(coverage_stats.get("exempted") or 0)
    delegated = int(coverage_stats.get("delegated") or 0)

    if total_people <= 0 and not period_rows:
        return {
            "tone": "neutral",
            "summary": "Seçili rapor görünümünde AI içgörü oluşturacak veri bulunmadı.",
            "highlights": [{"label": "Öneri", "value": "Dönem veya kapsam filtresini genişletin."}],
            "risks": [],
            "actions": ["Önce görünüm kapsamını genişletip tekrar deneyin."],
            "metrics": {"completion_rate": 0, "risk_load": 0, "strong_ratio": 0},
        }

    risk_load = low_score_count + chain_issue + uncovered
    strong_ratio = _clip_percent((high_score_count / max(total_people, 1)) * 100)
    tone = "good"
    if completion_rate < 85 or low_score_count > 0 or chain_issue > 0 or uncovered > 0:
        tone = "warning"
    if completion_rate < 70 or risk_load >= max(5, round(total_people * 0.20)):
        tone = "danger"

    best_period = max(period_rows, key=lambda row: float(row.get("avg_score") or 0), default=None)
    weakest_period = max(period_rows, key=lambda row: (int(row.get("low_score_count") or 0), -(float(row.get("avg_score") or 0))), default=None)

    summary_parts = [
        f"{scope_label or 'Seçili rapor alanı'} içinde {total_people} personel ve {total_periods} dönem izleniyor.",
        f"Genel tamamlanma %{completion_rate:.2f}, genel ortalama {avg_score:.2f} puan.",
    ]
    if selected_period_title:
        summary_parts.append(f"Odak dönem: {selected_period_title}.")
    if low_score_count:
        summary_parts.append(f"{low_score_count} düşük bant sonucu yönetici takibi gerektiriyor.")
    if chain_issue or uncovered:
        summary_parts.append(f"Kapsama loglarında {chain_issue + uncovered} kritik zincir/açıkta olay var.")

    highlights = [
        {"label": "90 üstü sonuç", "value": str(high_score_count)},
        {"label": "70 altı sonuç", "value": str(low_score_count)},
        {"label": "Vekâletle kapanan", "value": str(delegated)},
    ]
    if best_period:
        highlights.insert(0, {"label": "En güçlü dönem", "value": f"{best_period.get('title') or '-'} · ort. {float(best_period.get('avg_score') or 0):.2f}"})
    if top_people:
        highlights.append({"label": "Öne çıkan personel", "value": f"{top_people[0].get('name') or '-'} · {float(top_people[0].get('score') or 0):.2f}"})

    risks: list[str] = []
    if completion_rate < 85:
        risks.append("Tamamlanma oranı %85'in altında; rapor final tablo olarak okunmadan önce süreçler tamamlatılmalı.")
    if low_score_count:
        risks.append(f"{low_score_count} düşük puanlı kayıt için gerekçe ve geri bildirim aksiyonu kontrol edilmeli.")
    if weakest_period and int(weakest_period.get('low_score_count') or 0) > 0:
        risks.append(f"{weakest_period.get('title') or '-'} döneminde düşük bant yoğunluğu dikkat çekiyor.")
    if chain_issue:
        risks.append(f"{chain_issue} zincir sorunu logu var; rapor doğruluğu için görev üretim kurgusu da gözden geçirilmeli.")
    if uncovered:
        risks.append(f"{uncovered} açıkta kalan zincir kaydı var; bazı değerlendirmeler görünenden eksik olabilir.")

    actions = []
    if completion_rate < 85:
        actions.append("Önce bekleyen ve kısmi kayıtları kapatıp ardından dönem kartlarını tekrar gözden geçirin.")
    if low_people:
        actions.append("Düşük sonuç listesindeki personeller için açıklama, not karnesi ve geri bildirim taleplerini birlikte kontrol edin.")
    if chain_issue or uncovered:
        actions.append("Kapsama ve muafiyet özeti panelindeki sorunlu birimlerden başlayarak zincir kurgusunu temizleyin.")
    if not actions:
        actions.append("En güçlü dönem ve güçlü personel örneklerini yönetici sunumunda iyi uygulama örneği olarak kullanabilirsiniz.")

    return {
        "tone": tone,
        "summary": " ".join(summary_parts),
        "highlights": highlights,
        "risks": risks,
        "actions": actions,
        "metrics": {
            "completion_rate": _clip_percent(completion_rate),
            "risk_load": risk_load,
            "strong_ratio": strong_ratio,
            "exempted": exempted,
        },
    }