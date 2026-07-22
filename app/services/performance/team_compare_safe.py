from typing import Any


def safe_team_compare_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe_rows = []
    for row in rows or []:
        item = {
            "employee_id": row.get("employee_id"),
            "employee_name": row.get("employee_name") or row.get("full_name") or "",
            "score": row.get("score") if row.get("score") is not None else 0,
            "status": row.get("status") or "bekliyor",
            "manager_1_name": row.get("manager_1_name") or "",
            "manager_2_name": row.get("manager_2_name") or "",
            "manager_3_name": row.get("manager_3_name") or "",
            "issues": row.get("issues") or [],
        }
        safe_rows.append(item)
    return safe_rows


def safe_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = safe_team_compare_rows(rows)
    total = len(rows)
    completed = len([r for r in rows if r["status"] in {"tamamlandi", "completed", "yayinlandi", "published"}])
    waiting = total - completed
    low = len([r for r in rows if isinstance(r["score"], (int, float)) and r["score"] < 70])
    high = len([r for r in rows if isinstance(r["score"], (int, float)) and r["score"] >= 90])

    return {
        "total": total,
        "completed": completed,
        "waiting": waiting,
        "low": low,
        "high": high,
        "rows": rows,
    }