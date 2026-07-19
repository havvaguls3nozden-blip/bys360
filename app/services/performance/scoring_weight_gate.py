
"""BYS360 Performans Puanlama, Ağırlık ve 3. Amir Modu Kapısı.

Bu modül canlı davranış değiştirmez. Nihai amir kural matrisindeki puanlama,
ağırlıklandırma ve 3. amir mod sözleşmesini kaynak kod üzerinde denetler:

- Kriter puanları 1-5 aralığındadır ve 100'lük ölçeğe çevrilir.
- 1 ve 5 puanlarda açıklama zorunludur; 3 puan tek başına açıklama zorunluluğu üretmez.
- Nihai/ortalama sonuç 70 altı veya 90 üstü ise genel görüş zorunludur.
- 3. amir yorum modunda puana etki etmez; puan modunda ağırlığa dahil olur.
- Aktif ağırlık toplamı her durumda 100 olmalıdır.
- Tek amirli istisnalarda ağırlık 100/0/0 olarak korunur.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from collections.abc import Iterable

SCORING_WEIGHT_GATE_VERSION = "2026-04-20-performance-scoring-weight-gate-faz4"

SCORING_REQUIRED_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/rules.py": (
        "DEFAULT_TWO_MANAGER_WEIGHTS",
        "DEFAULT_THREE_MANAGER_SCORING_WEIGHTS",
        "LEVEL_3_DEFAULT_MODE",
        "LEVEL_3_ALLOWED_MODES",
        'LEVEL_3_DEFAULT_MODE: Final[str] = "comment_only"',
        'LEVEL_3_ALLOWED_MODES: Final[tuple[str, ...]] = ("off", "comment_only", "scoring")',
        "BLIND_REVIEW_ALLOWED",
        "INFO_REASON_LEVEL3_COMMENT_ONLY",
    ),
    "app/services/performance/chain_rule_engine.py": (
        "THREE_MANAGER_COMMENT_WEIGHTS",
        "THREE_MANAGER_SCORING_WEIGHTS",
        "weights_for_chain",
        "level_3_mode == \"scoring\"",
        "return dict(THREE_MANAGER_SCORING_WEIGHTS)",
        "return dict(THREE_MANAGER_COMMENT_WEIGHTS)",
        '"three_manager_comment_only": dict(THREE_MANAGER_COMMENT_WEIGHTS)',
        '"three_manager_scoring": dict(THREE_MANAGER_SCORING_WEIGHTS)',
    ),
    "app/services/performance/common.py": (
        "normalize_weight_inputs",
        "calculate_effective_weights",
        "get_period_level_3_flags",
        "get_base_weight_map",
        "level_3_scoring_enabled",
        "level_3_mode",
        "scoring_enabled",
        "total_after",
        'active_levels = {1: 100.0} if manager_1_id else {}',
        'if manager_3_id and flags["enabled"] and flags["scoring_enabled"]',
    ),
    "app/services/performance/scoring.py": (
        "calculate_preview_total_100",
        "requires_general_comment",
        "validate_score_value",
        "validate_general_comment_requirements",
        "validate_item_comment_requirements",
        "validate_weight_distribution",
        "calculate_level_total_100",
        "calculate_final_total",
        "recalculate_evaluation_totals",
        "score_to_100",
        "score in {1.0, 5.0}",
        "3 puan tek başına yorum zorunluluğu oluşturmaz",
        "evaluation.level_3_total_100 = 0.0",
    ),
    "app/services/performance/criteria.py": (
        "score_to_100",
        "validate_criteria_total",
        "total == 100.0",
    ),
    "app/services/performance/publish_preflight_rules.py": (
        "LOW_SCORE_THRESHOLD = 70.0",
        "HIGH_SCORE_THRESHOLD = 90.0",
        "1 veya 5 verilen kriterlerde açıklama/gerekçe zorunludur",
        "70 altı sonuçlarda ayrıntılı genel görüş zorunludur",
        "90 ve üstü sonuçlarda ayrıntılı genel görüş zorunludur",
        "level_3_comment_required",
    ),
    "app/services/performance/evaluation_form_service.py": (
        "3. amir yorumcu modunda genel görüş zorunludur",
        "1 veya 5 puan için açıklama zorunludur",
        "validate_general_comment_requirements",
    ),
}

SCORING_OPTIONAL_TOKENS: dict[str, tuple[str, ...]] = {
    "app/services/performance/config.py": (
        "calculate_effective_weights",
        "normalize_weight_inputs",
        "get_base_weight_map",
    ),
    "app/templates/performance": (
        "Değerlendirme Kriterleri",
    ),
}

SCORING_FORBIDDEN_PATTERNS: dict[str, tuple[str, ...]] = {
    "app/services/performance/rules.py": (
        r"LEVEL_3_DEFAULT_MODE\s*:[^=]*=\s*[\"']scoring[\"']",
        r"BLIND_REVIEW_ALLOWED\s*:[^=]*=\s*True",
    ),
    "app/services/performance/chain_rule_engine.py": (
        r"THREE_MANAGER_COMMENT_WEIGHTS\s*:[^\n]*3\s*:\s*(?!0\.0|0(?:\.0)?\s*[,}])\d+(?:\.\d+)?",
        r"BLIND_REVIEW_ALLOWED\s*=\s*True",
    ),
    "app/services/performance/scoring.py": (
        r"score\s+in\s+\{\s*1\.0\s*,\s*3\.0\s*,\s*5\.0\s*\}",
        r"score\s+in\s+\{\s*1\s*,\s*3\s*,\s*5\s*\}",
        r"level_total_100\s*<=\s*70",
        r"level_total_100\s*>=\s*90",
    ),
}

SCORING_COMPILE_TARGETS: tuple[str, ...] = (
    "app/services/performance/rule_matrix_final_gate.py",
    "app/services/performance/chain_contract_gate.py",
    "app/services/performance/task_generation_gate.py",
    "app/services/performance/visibility_publication_gate.py",
    "app/services/performance/scoring_weight_gate.py",
    "scripts/check_performance_rule_matrix_final_gate.py",
    "scripts/check_performance_chain_contract_gate.py",
    "scripts/check_performance_task_generation_gate.py",
    "scripts/check_performance_visibility_publication_gate.py",
    "scripts/check_performance_scoring_weight_gate.py",
    "scripts/refactor/bys360_performance_rule_matrix_final_gate_faz4_audit.py",
)


@dataclass
class ScoringWeightFinding:
    code: str
    message: str
    severity: str = "error"


@dataclass
class ScoringWeightReport:
    version: str = SCORING_WEIGHT_GATE_VERSION
    ok: list[str] = field(default_factory=list)
    findings: list[ScoringWeightFinding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for item in self.findings if item.severity == "warning")

    def passed(self) -> bool:
        return self.error_count == 0

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "passed": self.passed(),
            "ok_count": len(self.ok),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "ok": list(self.ok),
            "findings": [item.__dict__.copy() for item in self.findings],
            "contracts": {
                "score_scale": "1-5 -> 100",
                "comment_required_for_scores": [1, 5],
                "general_comment_thresholds": {"below": 70, "above": 90},
                "level_3_modes": ["off", "comment_only", "scoring"],
                "level_3_comment_mode_weight": 0,
                "level_3_scoring_mode_included": True,
                "weight_total": 100,
            },
        }


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _iter_text_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if not path.exists():
        return
    for child in path.rglob("*"):
        if child.is_file() and child.suffix.lower() in {".py", ".html", ".jinja", ".jinja2", ".txt", ".md"}:
            yield child


def _check_required_tokens(root: Path, report: ScoringWeightReport) -> None:
    for rel, tokens in SCORING_REQUIRED_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.findings.append(ScoringWeightFinding("missing_required_file", f"Eksik puanlama/ağırlık dosyası: {rel}"))
            continue
        content = _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"{rel} :: {token}")
            else:
                report.findings.append(ScoringWeightFinding("missing_required_token", f"Eksik puanlama/ağırlık izi: {rel} :: {token}"))

    for rel, tokens in SCORING_OPTIONAL_TOKENS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Opsiyonel puanlama/ağırlık alanı yok/kapsam dışı: {rel}")
            continue
        content = "\n".join(_read(p) for p in _iter_text_files(path)) if path.is_dir() else _read(path)
        for token in tokens:
            if token in content:
                report.ok.append(f"Opsiyonel köprü doğrulandı: {rel} :: {token}")
            else:
                report.ok.append(f"Opsiyonel köprü izi eksik ama canlı kapsamda zorunlu değil: {rel} :: {token}")


def _check_forbidden_patterns(root: Path, report: ScoringWeightReport) -> None:
    for rel, patterns in SCORING_FORBIDDEN_PATTERNS.items():
        path = root / rel
        if not path.exists():
            report.ok.append(f"Yasak puanlama/ağırlık alanı yok veya kapsam dışı: {rel}")
            continue
        for file_path in _iter_text_files(path):
            content = _read(file_path)
            for pattern in patterns:
                flags = re.IGNORECASE | re.MULTILINE
                if "[\\s\\S]" in pattern or "\\s" in pattern:
                    flags |= re.DOTALL
                if re.search(pattern, content, flags=flags):
                    report.findings.append(ScoringWeightFinding("forbidden_scoring_weight_pattern", f"Yasak puanlama/ağırlık izi: {file_path.relative_to(root)} :: {pattern}"))
                else:
                    report.ok.append(f"Yasak puanlama/ağırlık deseni yok: {file_path.relative_to(root)}")


def simulate_score_to_100(score: float, *, score_min: float = 1.0, score_max: float = 5.0) -> float:
    if score <= 0:
        return 0.0
    value = max(score_min, min(score_max, float(score)))
    return round((value / score_max) * 100.0, 2)


def simulate_requires_general_comment(level_total_100: float, raw_scores: tuple[float, ...] = ()) -> bool:
    if level_total_100 < 70 or level_total_100 > 90:
        return True
    return any(float(score) in {1.0, 5.0} for score in raw_scores)


def simulate_normalize_weights(w1: float, w2: float, w3: float, *, level_3_enabled: bool, level_3_scoring_enabled: bool) -> dict[str, float | str | bool]:
    w1 = max(0.0, float(w1 or 0.0))
    w2 = max(0.0, float(w2 or 0.0))
    w3 = max(0.0, float(w3 or 0.0))
    if not level_3_enabled:
        w3 = 0.0
        mode = "off"
    elif level_3_scoring_enabled:
        mode = "scoring"
    else:
        w3 = 0.0
        mode = "comment_only"
    total = w1 + w2 + w3
    if total <= 0:
        if mode == "scoring":
            w1, w2, w3 = 40.0, 40.0, 20.0
        else:
            w1, w2, w3 = 50.0, 50.0, 0.0
        total = 100.0
    result = {
        "evaluator_1_weight": round((w1 / total) * 100.0, 2),
        "evaluator_2_weight": round((w2 / total) * 100.0, 2),
        "evaluator_3_weight": round((w3 / total) * 100.0, 2),
        "level_3_enabled": bool(level_3_enabled),
        "level_3_scoring_enabled": bool(level_3_enabled and level_3_scoring_enabled),
        "level_3_mode": mode,
    }
    total_after = result["evaluator_1_weight"] + result["evaluator_2_weight"] + result["evaluator_3_weight"]  # type: ignore[operator]
    if total_after != 100.0:
        result["evaluator_1_weight"] = round(float(result["evaluator_1_weight"]) + (100.0 - float(total_after)), 2)
    return result


def _check_contract_simulations(report: ScoringWeightReport) -> None:
    expected_scores = {0: 0.0, 1: 20.0, 3: 60.0, 5: 100.0, 9: 100.0}
    for raw, expected in expected_scores.items():
        actual = simulate_score_to_100(float(raw))
        if actual == expected:
            report.ok.append(f"Puan dönüşümü doğru: {raw} -> {actual}")
        else:
            report.findings.append(ScoringWeightFinding("score_conversion_contract", f"Puan dönüşümü beklenmeyen sonuç: {raw} -> {actual}, beklenen {expected}"))

    comment_cases = [
        (69.99, (), True, "70 altı genel görüş"),
        (70.0, (), False, "70 eşik altında değil"),
        (90.0, (), False, "90 eşik üstü değil"),
        (90.01, (), True, "90 üstü genel görüş"),
        (80.0, (1.0,), True, "1 puan açıklama"),
        (80.0, (5.0,), True, "5 puan açıklama"),
        (80.0, (3.0,), False, "3 puan tek başına açıklama değil"),
    ]
    for total, scores, expected, label in comment_cases:
        actual = simulate_requires_general_comment(total, scores)
        if actual is expected:
            report.ok.append(f"Açıklama sözleşmesi doğru: {label}")
        else:
            report.findings.append(ScoringWeightFinding("comment_requirement_contract", f"Açıklama sözleşmesi hatalı: {label} -> {actual}, beklenen {expected}"))

    weight_cases = [
        (50, 50, 20, False, False, "off", 0.0),
        (50, 50, 20, True, False, "comment_only", 0.0),
        (40, 40, 20, True, True, "scoring", 20.0),
        (0, 0, 0, True, True, "scoring", 20.0),
        (0, 0, 0, True, False, "comment_only", 0.0),
    ]
    for w1, w2, w3, enabled, scoring, expected_mode, expected_w3 in weight_cases:
        result = simulate_normalize_weights(w1, w2, w3, level_3_enabled=enabled, level_3_scoring_enabled=scoring)
        total = round(float(result["evaluator_1_weight"]) + float(result["evaluator_2_weight"]) + float(result["evaluator_3_weight"]), 2)
        if total != 100.0:
            report.findings.append(ScoringWeightFinding("weight_total_contract", f"Ağırlık toplamı 100 değil: {result}"))
            continue
        if result["level_3_mode"] != expected_mode:
            report.findings.append(ScoringWeightFinding("level_3_mode_contract", f"3. amir modu hatalı: {result}, beklenen {expected_mode}"))
            continue
        if float(result["evaluator_3_weight"]) != expected_w3:
            report.findings.append(ScoringWeightFinding("level_3_weight_contract", f"3. amir ağırlığı hatalı: {result}, beklenen {expected_w3}"))
            continue
        report.ok.append(f"Ağırlık sözleşmesi doğru: mode={expected_mode}, w3={expected_w3}, total={total}")


def build_scoring_weight_gate_report(project_root: str | Path | None = None) -> ScoringWeightReport:
    root = Path(project_root or Path.cwd()).resolve()
    report = ScoringWeightReport()
    _check_required_tokens(root, report)
    _check_forbidden_patterns(root, report)
    _check_contract_simulations(report)
    return report


def format_scoring_weight_report(report: ScoringWeightReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Performans Puanlama/Ağırlık/3. Amir Modu Kapısı | {status}",
        f"version={report.version}",
        f"OK={len(report.ok)} HATA={report.error_count} UYARI={report.warning_count}",
        "",
        "Sözleşme özeti:",
        "- Puan ölçeği: 1-5 aralığı, 100'lük karşılığa çevrilir.",
        "- Açıklama: 1 ve 5 puanda zorunlu; 3 puan tek başına zorunlu değildir.",
        "- Genel görüş: 70 altı veya 90 üstü nihai/ortalama sonuçta zorunludur.",
        "- 3. amir yorum modunda %0 etkiyle çalışır; puan modunda ağırlığa dahil olur.",
        "- Ağırlık toplamı her aktif senaryoda %100 olmalıdır.",
    ]
    if report.findings:
        lines.append("")
        lines.append("Bulgular:")
        for finding in report.findings:
            lines.append(f"- {finding.severity.upper()} | {finding.code} | {finding.message}")
    return "\n".join(lines)


__all__ = [
    "SCORING_COMPILE_TARGETS",
    "SCORING_REQUIRED_TOKENS",
    "SCORING_WEIGHT_GATE_VERSION",
    "ScoringWeightFinding",
    "ScoringWeightReport",
    "build_scoring_weight_gate_report",
    "format_scoring_weight_report",
    "simulate_normalize_weights",
    "simulate_requires_general_comment",
    "simulate_score_to_100",
]
