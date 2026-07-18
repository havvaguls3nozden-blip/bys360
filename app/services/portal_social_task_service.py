"""BYS360 Portal V3B5 - Sosyal medya otomatik kontrol görev yönetimi.

Bu servis UI üzerinden otomatik kontrolü aç/kapat/şimdi çalıştır işlemlerini yönetir.
Kalıcı zamanlama için Windows Görev Zamanlayıcı kullanılır; kullanıcı PowerShell açmak zorunda kalmaz.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from flask import current_app
except Exception:  # pragma: no cover
    current_app = None

TASK_NAME = "BYS360 Portal Social Auto Import V3B2"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _project_root() -> Path:
    if current_app is not None:
        try:
            return Path(current_app.root_path).resolve().parent
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass
    return Path.cwd().resolve()


def _state_path() -> Path:
    root = _project_root()
    p = root / "instance" / "portal" / "social_auto_task_v3b5_state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _write_state(data: dict[str, Any]) -> None:
    _state_path().write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _read_state() -> dict[str, Any]:
    try:
        return json.loads(_state_path().read_text(encoding="utf-8"))
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return {}


def _run(cmd: list[str], *, timeout: int = 90) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, cwd=str(_project_root()), text=True, capture_output=True, timeout=timeout)
        return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]}
    except Exception as exc:
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": str(exc)}


def _is_windows() -> bool:
    return platform.system().lower().startswith("win") or os.name == "nt"


def get_social_auto_task_status() -> dict[str, Any]:
    """Otomatik sosyal medya kontrol görevinin durumunu döndürür."""
    state = _read_state()
    _project_root()
    base = {
        "ok": True,
        "supported": _is_windows(),
        "task_name": TASK_NAME,
        "enabled": False,
        "state": "Bilinmiyor",
        "last_run_time": None,
        "next_run_time": None,
        "last_task_result": None,
        "last_action": state,
        "message": "Otomatik kontrol durumu henüz alınmadı.",
    }
    if not _is_windows():
        base.update({"ok": False, "message": "Bu ortamda uygulama içi zamanlanmış görev yönetimi desteklenmiyor."})
        return base
    ps = "powershell"
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"$t=Get-ScheduledTask -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue;"
        "if ($null -eq $t) { [PSCustomObject]@{Exists=$false;State='Yok';LastRunTime=$null;NextRunTime=$null;LastTaskResult=$null} | ConvertTo-Json -Compress; exit 0 };"
        f"$i=Get-ScheduledTaskInfo -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue;"
        "$enabled = $t.State -ne 'Disabled';"
        "[PSCustomObject]@{Exists=$true;Enabled=$enabled;State=([string]$t.State);LastRunTime=$i.LastRunTime;NextRunTime=$i.NextRunTime;LastTaskResult=$i.LastTaskResult} | ConvertTo-Json -Compress"
    )
    res = _run([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], timeout=30)
    if not res.get("ok"):
        base.update({"ok": False, "message": "Otomatik görev durumu okunamadı.", "error": res.get("stderr")})
        return base
    try:
        info = json.loads((res.get("stdout") or "{}").strip() or "{}")
    except Exception:
        info = {}
    exists = bool(info.get("Exists"))
    base.update({
        "exists": exists,
        "enabled": bool(info.get("Enabled")) if exists else False,
        "state": info.get("State") or ("Kurulu değil" if not exists else "Bilinmiyor"),
        "last_run_time": str(info.get("LastRunTime") or "") or None,
        "next_run_time": str(info.get("NextRunTime") or "") or None,
        "last_task_result": info.get("LastTaskResult"),
        "message": "Otomatik kontrol açık." if exists and bool(info.get("Enabled")) else "Otomatik kontrol kapalı veya kurulu değil.",
    })
    return base


def install_social_auto_task() -> dict[str, Any]:
    root = _project_root()
    script = root / "scripts" / "windows" / "install_bys360_social_auto_import_v3b2_task.ps1"
    if not script.exists():
        result = {"ok": False, "message": "Otomatik görev kurulum dosyası bulunamadı.", "script": str(script), "generated_at": _now_iso()}
        _write_state(result); return result
    res = _run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-ProjectRoot", str(root), "-Create"], timeout=90)
    result = {"ok": bool(res.get("ok")), "action": "install", "message": "Otomatik kontrol açıldı." if res.get("ok") else "Otomatik kontrol açılamadı.", "result": res, "generated_at": _now_iso()}
    _write_state(result); return result


def remove_social_auto_task() -> dict[str, Any]:
    root = _project_root()
    script = root / "scripts" / "windows" / "install_bys360_social_auto_import_v3b2_task.ps1"
    if not script.exists():
        result = {"ok": False, "message": "Otomatik görev kurulum dosyası bulunamadı.", "script": str(script), "generated_at": _now_iso()}
        _write_state(result); return result
    res = _run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-ProjectRoot", str(root), "-Delete"], timeout=60)
    result = {"ok": bool(res.get("ok")), "action": "remove", "message": "Otomatik kontrol kapatıldı." if res.get("ok") else "Otomatik kontrol kapatılamadı.", "result": res, "generated_at": _now_iso()}
    _write_state(result); return result


def run_social_auto_import_now() -> dict[str, Any]:
    root = _project_root()
    py = root / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path("python")
    script = root / "scripts" / "portal" / "run_bys360_social_media_embed_scan_v3b.py"
    if not script.exists():
        result = {"ok": False, "message": "Sosyal medya kontrol scripti bulunamadı.", "script": str(script), "generated_at": _now_iso()}
        _write_state(result); return result
    res = _run([str(py), str(script), "--project-root", str(root), "--manual", "--auto-discover"], timeout=180)
    result = {"ok": bool(res.get("ok")), "action": "run_now", "message": "Otomatik kontrol şimdi çalıştırıldı." if res.get("ok") else "Otomatik kontrol çalıştırılamadı.", "result": res, "generated_at": _now_iso()}
    _write_state(result); return result
