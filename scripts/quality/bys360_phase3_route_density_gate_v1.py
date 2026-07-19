from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_PHASE3_ROUTE_DENSITY_GATE_V1"
REPORT_JSON_REL = Path("reports/architecture/BYS360_PHASE3_ROUTE_DENSITY_GATE_V1_REPORT.json")
REPORT_MD_REL = Path("reports/architecture/BYS360_PHASE3_ROUTE_DENSITY_GATE_V1_REPORT.md")

ROUTE_DECORATOR_RE = re.compile(
    r"^@\w+(?:_\w+)*\.(?:route|get|post|put|patch|delete)\("
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _is_project_python_file(path: Path) -> bool:
    parts = set(path.parts)
    if "__pycache__" in parts:
        return False
    if ".venv" in parts:
        return False
    if path.name.startswith("."):
        return False
    return path.suffix == ".py"


def _classify_area(rel_path: str) -> str:
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")

    if normalized.startswith("app/api/mobile/"):
        return "mobile_api"
    if normalized.startswith("app/services/"):
        return "service_layer"
    if normalized.startswith("app/institutional/"):
        return "institutional"
    if normalized.startswith("app/performance/"):
        return "performance"
    if normalized.startswith("app/communication/"):
        return "communication"
    if normalized.startswith("app/admin/"):
        return "admin"
    if normalized.startswith("app/portal/"):
        return "portal"
    if normalized.startswith("app/support/"):
        return "support"
    if len(parts) >= 2:
        return parts[1]
    return "app_root"


def _scan_file(root: Path, path: Path) -> dict[str, Any]:
    text = _read_text(path)
    lines = text.splitlines()

    route_decorators = 0
    function_defs = 0
    class_defs = 0
    broad_except = 0

    for line in lines:
        stripped = line.strip()
        if ROUTE_DECORATOR_RE.search(stripped):
            route_decorators += 1
        if stripped.startswith("def ") or stripped.startswith("async def "):
            function_defs += 1
        if stripped.startswith("class "):
            class_defs += 1
        if stripped in {"except Exception:", "except Exception as exc:", "except Exception as e:"}:
            broad_except += 1

    rel_path = str(path.relative_to(root)).replace("\\", "/")

    return {
        "path": rel_path,
        "area": _classify_area(rel_path),
        "lines": len(lines),
        "route_decorators": route_decorators,
        "function_defs": function_defs,
        "class_defs": class_defs,
        "broad_except": broad_except,
        "service_extraction_candidate": bool(route_decorators >= 10 or (route_decorators >= 5 and len(lines) >= 600)),
        "large_file_candidate": bool(len(lines) >= 800),
    }


def _area_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for row in rows:
        area = row["area"]
        item = grouped.setdefault(
            area,
            {
                "area": area,
                "file_count": 0,
                "total_lines": 0,
                "total_route_decorators": 0,
                "large_file_count": 0,
                "service_extraction_candidate_count": 0,
            },
        )
        item["file_count"] += 1
        item["total_lines"] += row["lines"]
        item["total_route_decorators"] += row["route_decorators"]
        item["large_file_count"] += int(bool(row["large_file_candidate"]))
        item["service_extraction_candidate_count"] += int(bool(row["service_extraction_candidate"]))

    return sorted(
        grouped.values(),
        key=lambda item: (item["total_route_decorators"], item["total_lines"]),
        reverse=True,
    )


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# BYS360 Faz 3A Route ve Dosya Yoğunluk Raporu",
        "",
        f"- Paket: `{PACKAGE}`",
        f"- Üretim zamanı: `{result['generated_at']}`",
        f"- Genel durum: `{'PASS' if result['route_density_gate_ok'] else 'FAIL'}`",
        f"- Taranan Python dosyası: `{result['python_file_count']}`",
        f"- Toplam satır: `{result['total_lines']}`",
        f"- Toplam route decorator: `{result['total_route_decorators']}`",
        f"- Servis çıkarımı adayı: `{result['service_extraction_candidate_count']}`",
        f"- Büyük dosya adayı: `{result['large_file_candidate_count']}`",
        "",
        "## En Yoğun Route Dosyaları",
        "",
        "| Sıra | Dosya | Alan | Satır | Route |",
        "|---:|---|---|---:|---:|",
    ]

    for idx, row in enumerate(result["top_by_routes"][:30], start=1):
        lines.append(
            f"| {idx} | `{row['path']}` | {row['area']} | {row['lines']} | {row['route_decorators']} |"
        )

    lines.extend([
        "",
        "## En Büyük Dosyalar",
        "",
        "| Sıra | Dosya | Alan | Satır | Route |",
        "|---:|---|---|---:|---:|",
    ])

    for idx, row in enumerate(result["top_by_lines"][:30], start=1):
        lines.append(
            f"| {idx} | `{row['path']}` | {row['area']} | {row['lines']} | {row['route_decorators']} |"
        )

    lines.extend([
        "",
        "## Alan Özeti",
        "",
        "| Alan | Dosya | Satır | Route | Büyük Dosya | Servis Adayı |",
        "|---|---:|---:|---:|---:|---:|",
    ])

    for row in result["area_summary"]:
        lines.append(
            f"| {row['area']} | {row['file_count']} | {row['total_lines']} | {row['total_route_decorators']} | {row['large_file_count']} | {row['service_extraction_candidate_count']} |"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_checks(root: Path, write_report: bool = True) -> dict[str, Any]:
    app_root = root / "app"

    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    duplicate_paths: list[str] = []

    for path in sorted(app_root.rglob("*.py")):
        if not _is_project_python_file(path):
            continue

        rel = str(path.relative_to(root)).replace("\\", "/")
        if rel in seen:
            duplicate_paths.append(rel)
            continue
        seen.add(rel)

        rows.append(_scan_file(root, path))

    top_by_lines = sorted(rows, key=lambda item: item["lines"], reverse=True)
    top_by_routes = sorted(rows, key=lambda item: (item["route_decorators"], item["lines"]), reverse=True)

    service_candidates = [
        row for row in rows
        if row["service_extraction_candidate"]
    ]

    large_file_candidates = [
        row for row in rows
        if row["large_file_candidate"]
    ]

    result: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "route_density_gate_ok": False,
        "python_file_count": len(rows),
        "duplicate_paths": duplicate_paths,
        "duplicate_path_count": len(duplicate_paths),
        "total_lines": sum(row["lines"] for row in rows),
        "total_route_decorators": sum(row["route_decorators"] for row in rows),
        "service_extraction_candidate_count": len(service_candidates),
        "large_file_candidate_count": len(large_file_candidates),
        "top_by_lines": top_by_lines[:80],
        "top_by_routes": top_by_routes[:80],
        "service_extraction_candidates": service_candidates[:80],
        "large_file_candidates": large_file_candidates[:80],
        "area_summary": _area_summary(rows),
    }

    result["route_density_gate_ok"] = bool(
        result["python_file_count"] > 0
        and result["duplicate_path_count"] == 0
        and result["total_lines"] > 0
        and result["total_route_decorators"] > 0
    )

    if write_report:
        json_report = root / REPORT_JSON_REL
        md_report = root / REPORT_MD_REL
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        _write_markdown(md_report, result)
        result["json_report"] = str(json_report)
        result["markdown_report"] = str(md_report)

    return result


def main() -> int:
    root = Path.cwd()
    result = run_checks(root, write_report=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["route_density_gate_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
