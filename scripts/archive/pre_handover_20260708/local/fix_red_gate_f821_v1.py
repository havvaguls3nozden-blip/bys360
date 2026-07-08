from pathlib import Path

def read(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")

def write(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")

def ensure_after(path, anchor, insert):
    p = Path(path)
    text = read(p)
    if insert.strip() in text:
        print("OK zaten var:", path)
        return
    if anchor not in text:
        raise SystemExit(f"ANCHOR bulunamadı: {path} :: {anchor}")
    text = text.replace(anchor, anchor + insert, 1)
    write(p, text)
    print("OK eklendi:", path)

# 1) Mobil performans görevleri: _DONE sabiti
ensure_after(
    "app/api/mobile/services/performance_task_helpers.py",
    "logger = logging.getLogger(__name__)\n",
    '\n_DONE = {"tamamlandi", "tamamlandı", "completed", "done", "closed", "kapandi", "kapandı", "yayınlandı", "published"}\n',
)

# 2) CIC misc_context: send_email import/fallback
ensure_after(
    "app/services/cic/misc_context.py",
    "from app.services.cic.config_context import (\n",
    "",
)
misc = read("app/services/cic/misc_context.py")
misc_insert = '''\ntry:\n    from app.services.mail_core import send_email\nexcept Exception:\n    send_email = None  # type: ignore[assignment]\n\n'''
if "from app.services.mail_core import send_email" not in misc:
    marker = "BASE_KEY = \"corporate_information_center\"\n"
    misc = misc.replace(marker, misc_insert + marker, 1)
    write("app/services/cic/misc_context.py", misc)
    print("OK eklendi: app/services/cic/misc_context.py send_email")
else:
    print("OK zaten var: app/services/cic/misc_context.py send_email")

# 3) CIC send_context: create_mail_log import/fallback
send = read("app/services/cic/send_context.py")
send_insert = '''\ntry:\n    from app.services.mail_core import create_mail_log\nexcept Exception:\n    create_mail_log = None  # type: ignore[assignment]\n\n'''
if "from app.services.mail_core import create_mail_log" not in send:
    marker = "from app.services.cic.misc_context import (\n"
    send = send.replace(marker, send_insert + marker, 1)
    write("app/services/cic/send_context.py", send)
    print("OK eklendi: app/services/cic/send_context.py create_mail_log")
else:
    print("OK zaten var: app/services/cic/send_context.py create_mail_log")

# 4) effective_menu: V221/V223 sabitleri
eff = read("app/services/settings/effective_menu.py")
eff_insert = '''\nfrom app.services.settings.effective_menu_parts.bys360_constants import (\n    _BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221,\n    _BYS360_PERIOD_CENTER_MENU_KEY_V221,\n    _BYS360_V223_PERIOD_CENTER_KEY_ROLES,\n)\n'''
if "_BYS360_V223_PERIOD_CENTER_KEY_ROLES" not in eff.split("# BYS360_PERFORMANCE_V2_1_21_PERIOD_CENTER_ROLE_MATRIX_AUTHORITY_BEGIN")[0]:
    marker = "from app.services.settings.effective_menu_parts.core_policy_constants import (\n"
    eff = eff.replace(marker, eff_insert + "\n" + marker, 1)
    write("app/services/settings/effective_menu.py", eff)
    print("OK eklendi: app/services/settings/effective_menu.py constants")
else:
    print("OK zaten var: app/services/settings/effective_menu.py constants")

# 5) RollbackHook / Any eksikleri
for path in [
    "app/services/settings/effective_menu_parts/apply_context.py",
    "app/services/settings/effective_menu_parts/bys360_context.py",
]:
    text = read(path)
    if "RollbackHook = Callable[[], None]" not in text:
        text = text.replace("from app.services.settings_service import build_effective_user_menu_context, get_role_default_menu_keys\n",
                            "from app.services.settings_service import build_effective_user_menu_context, get_role_default_menu_keys\n\nRollbackHook = Callable[[], None]\n", 1)
        write(path, text)
        print("OK eklendi:", path, "RollbackHook")
    else:
        print("OK zaten var:", path, "RollbackHook")

build_path = "app/services/settings/effective_menu_parts/build_context.py"
build = read(build_path)
if "RollbackHook = Callable[[], None]" not in build:
    build = build.replace(
        "from __future__ import annotations\n",
        "from __future__ import annotations\n\nfrom collections.abc import Callable\nfrom typing import Any\n\nRollbackHook = Callable[[], None]\n",
        1,
    )
    write(build_path, build)
    print("OK eklendi:", build_path)
else:
    print("OK zaten var:", build_path)

user_path = "app/services/settings/effective_menu_parts/user_context.py"
user = read(user_path)
if "RollbackHook = Callable[[], None]" not in user:
    user = user.replace(
        "import logging\n",
        "import logging\nfrom collections.abc import Callable\nfrom typing import Any\n\nRollbackHook = Callable[[], None]\n",
        1,
    )
    write(user_path, user)
    print("OK eklendi:", user_path)
else:
    print("OK zaten var:", user_path)

print("OK: F821 local düzeltme tamamlandı.")
