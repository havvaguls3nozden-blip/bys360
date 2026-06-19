from __future__ import annotations

import argparse
import json
import py_compile
import shutil
import subprocess
from pathlib import Path

CHECKS = {
    "model_comment": ("app/models/communication_models.py", "class MessageComment"),
    "model_export": ("app/models/__init__.py", "MessageComment"),
    "schema_comment": ("app/schema_guard_core_maintenances.py", 'table="message_comments"'),
    "reaction_dislike": ("app/services/messages/constants.py", '"👎"'),
    "comment_service": ("app/services/messages/comments.py", "create_message_comment"),
    "serialization_comments": ("app/services/messages/serialization.py", '"comments": _comments_for_message(message)'),
    "route_comment": ("app/communication/messages_routes.py", 'messages_comment_impl'),
    "route_endpoint": ("app/communication/messages_routes.py", '/messages/<int:message_id>/comment'),
    "inbox_ui": ("app/templates/messages_inbox.html", "BYS360_MESSAGE_INTERACTIONS_V1_BLOCK_START"),
    "thread_ui": ("app/templates/messages_thread.html", "BYS360_MESSAGE_INTERACTIONS_V1_BLOCK_START"),
    "js_ajax": ("app/static/js/messages_messenger_mobile.js", "BYS360_MESSAGE_INTERACTIONS_V1_JS"),
    "js_no_reload": ("app/static/js/messages_messenger_mobile.js", "event.preventDefault();"),
    "css_marker": ("app/static/css/messages_messenger_mobile.css", "BYS360_MESSAGE_INTERACTIONS_V1_CSS"),
}

PY_FILES = [
    "app/models/communication_models.py",
    "app/models/__init__.py",
    "app/schema_guard_core_maintenances.py",
    "app/services/messages/constants.py",
    "app/services/messages/comments.py",
    "app/services/messages/serialization.py",
    "app/services/messages/__init__.py",
    "app/communication/messages_routes.py",
]

TEMPLATE_FILES = [
    "app/templates/messages_inbox.html",
    "app/templates/messages_thread.html",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    results: dict[str, object] = {}
    ok = True

    for key, (rel, needle) in CHECKS.items():
        path = root / rel
        passed = path.exists() and needle in path.read_text(encoding="utf-8")
        results[key] = bool(passed)
        ok = ok and bool(passed)

    compile_errors: list[str] = []
    for rel in PY_FILES:
        path = root / rel
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            compile_errors.append(f"{rel}: {exc}")
    results["py_compile_ok"] = not compile_errors
    results["py_compile_errors"] = compile_errors
    ok = ok and not compile_errors

    jinja_errors: list[str] = []
    try:
        from jinja2 import Environment
        env = Environment()
        for rel in TEMPLATE_FILES:
            try:
                env.parse((root / rel).read_text(encoding="utf-8"))
            except Exception as exc:
                jinja_errors.append(f"{rel}: {exc}")
    except Exception as exc:
        jinja_errors.append(f"jinja2 import: {exc}")
    results["jinja_parse_ok"] = not jinja_errors
    results["jinja_errors"] = jinja_errors
    ok = ok and not jinja_errors

    node_path = shutil.which("node")
    node_result = "skipped"
    if node_path:
        proc = subprocess.run([node_path, "--check", str(root / "app/static/js/messages_messenger_mobile.js")], text=True, capture_output=True)
        node_result = "ok" if proc.returncode == 0 else (proc.stderr or proc.stdout)
        ok = ok and proc.returncode == 0
    results["node_check"] = node_result

    payload = {"ok": ok, "checks": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
