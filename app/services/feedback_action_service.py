from __future__ import annotations


def get_priority_badge(priority: str) -> str:
    normalized = (priority or "medium").strip().lower()
    return {
        "low": "secondary",
        "medium": "warning",
        "high": "danger",
    }.get(normalized, "secondary")


def get_status_badge(status: str) -> str:
    normalized = (status or "open").strip().lower()
    return {
        "open": "secondary",
        "in_progress": "info",
        "resolved": "success",
        "cancelled": "dark",
    }.get(normalized, "secondary")


def summarize_action_backlog(action_rows):
    summary = {"open": 0, "in_progress": 0, "resolved": 0, "cancelled": 0}
    for row in action_rows or []:
        key = (getattr(row, "status", "open") or "open").strip().lower()
        summary[key] = summary.get(key, 0) + 1
    return summary