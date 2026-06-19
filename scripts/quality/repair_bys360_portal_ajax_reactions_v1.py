from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_PORTAL_AJAX_REACTIONS_V1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup(path: Path, backup_root: Path, project_root: Path) -> None:
    if not path.exists():
        return
    try:
        rel = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        rel = Path(path.name)
    target = backup_root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def replace_required(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if old not in text:
        raise RuntimeError(f"Beklenen blok bulunamadı: {label}")
    return text.replace(old, new, 1), True


def patch_routes(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app/portal/routes.py"
    backup(path, backup_root, project_root)
    text = read(path)

    if "reaction_counts," not in text:
        old = """    portal_home_context,\n    portal_instagram_story_items,\n    toggle_reaction,\n    toggle_save,"""
        new = """    portal_home_context,\n    portal_instagram_story_items,\n    reaction_counts,\n    toggle_reaction,\n    toggle_save,\n    user_reaction_for_post,"""
        text, _ = replace_required(text, old, new, "portal_service reaction import")
        changes.append("app/portal/routes.py import güncellendi")
    elif "user_reaction_for_post," not in text:
        text = text.replace("    reaction_counts,\n", "    reaction_counts,\n    user_reaction_for_post,\n", 1)
        changes.append("app/portal/routes.py user_reaction import eklendi")

    if "BYS360_PORTAL_AJAX_REACTIONS_V1_BEGIN" not in text:
        old = """def _portal_has_permission(key: str) -> bool:\n    return portal_permission_allowed(current_user, key)\n# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROUTE_GUARDS_END\n\n\n@main_bp.get(\"/portal\")"""
        new = """def _portal_has_permission(key: str) -> bool:\n    return portal_permission_allowed(current_user, key)\n\n\n# BYS360_PORTAL_AJAX_REACTIONS_V1_BEGIN\ndef _portal_wants_json_response() -> bool:\n    \"\"\"Portal küçük etkileşimlerinde sayfa yenilemeden JSON cevap üretir.\"\"\"\n    requested_with = (request.headers.get(\"X-Requested-With\") or \"\").lower()\n    accept = (request.headers.get(\"Accept\") or \"\").lower()\n    return (\n        requested_with == \"xmlhttprequest\"\n        or \"application/json\" in accept\n        or request.form.get(\"_ajax\") == \"1\"\n    )\n\n\ndef _portal_reaction_payload(post: PortalPost, action: str, message: str) -> dict:\n    counts = reaction_counts(post)\n    return {\n        \"ok\": True,\n        \"post_id\": int(post.id),\n        \"action\": action,\n        \"message\": message,\n        \"reaction_counts\": counts,\n        \"total_reactions\": int(sum(counts.values())),\n        \"user_reaction\": user_reaction_for_post(post, current_user),\n    }\n# BYS360_PORTAL_AJAX_REACTIONS_V1_END\n# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROUTE_GUARDS_END\n\n\n@main_bp.get(\"/portal\")"""
        text, _ = replace_required(text, old, new, "portal ajax helper")
        changes.append("app/portal/routes.py AJAX helper eklendi")

    if "wants_json = _portal_wants_json_response()" not in text:
        old = """@main_bp.post(\"/portal/posts/<int:post_id>/react\")\n@login_required\n@menu_key_required(\"portal_feed\")\ndef portal_post_react(post_id: int):\n    if not _portal_has_permission(\"portal_post_interact\"):\n        return _portal_permission_denied_redirect(\"Bu paylaşımda etkileşim yapma yetkiniz bulunmamaktadır.\")\n    post = PortalPost.query.get_or_404(post_id)\n    if not can_user_view_post(current_user, post):\n        return render_access_denied()\n    action = toggle_reaction(post, current_user, request.form.get(\"reaction_type\", \"like\"))\n    notify_portal_reaction(post, current_user, action=action)\n    db.session.commit()\n    flash(\"Tepkiniz güncellendi.\" if action != \"removed\" else \"Tepkiniz kaldırıldı.\", \"success\")\n    return redirect(request.referrer or url_for(\"main.portal_feed\"))\n"""
        new = """@main_bp.post(\"/portal/posts/<int:post_id>/react\")\n@login_required\n@menu_key_required(\"portal_feed\")\ndef portal_post_react(post_id: int):\n    wants_json = _portal_wants_json_response()\n    if not _portal_has_permission(\"portal_post_interact\"):\n        message = \"Bu paylaşımda etkileşim yapma yetkiniz bulunmamaktadır.\"\n        if wants_json:\n            return jsonify({\"ok\": False, \"message\": message}), 403\n        return _portal_permission_denied_redirect(message)\n    post = PortalPost.query.get_or_404(post_id)\n    if not can_user_view_post(current_user, post):\n        if wants_json:\n            return jsonify({\"ok\": False, \"message\": \"Bu paylaşımı görüntüleme yetkiniz bulunmamaktadır.\"}), 403\n        return render_access_denied()\n    action = toggle_reaction(post, current_user, request.form.get(\"reaction_type\", \"like\"))\n    notify_portal_reaction(post, current_user, action=action)\n    db.session.commit()\n    message = \"Tepkiniz güncellendi.\" if action != \"removed\" else \"Tepkiniz kaldırıldı.\"\n    if wants_json:\n        return jsonify(_portal_reaction_payload(post, action, message))\n    flash(message, \"success\")\n    return redirect(request.referrer or url_for(\"main.portal_feed\"))\n"""
        text, _ = replace_required(text, old, new, "portal_post_react route")
        changes.append("app/portal/routes.py portal_post_react JSON destekli hale getirildi")

    write(path, text)


def patch_post_card(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app/templates/portal/_post_card.html"
    backup(path, backup_root, project_root)
    text = read(path)
    if "data-portal-post-card" not in text:
        old = """<article id=\"post-{{ post.id }}\" class=\"portal-card portal-post-card {{ 'has-social-embed-v3b' if bys360_social.url else '' }} portal-v2c-post-card {{ 'is-pinned' if post.is_pinned else '' }} {{ 'is-instagram' if is_instagram else '' }} {{ 'is-instagram-story' if post.post_type == 'instagram_story' else '' }}\" aria-label=\"Portal paylaşımı\">"""
        new = """<article id=\"post-{{ post.id }}\" class=\"portal-card portal-post-card {{ 'has-social-embed-v3b' if bys360_social.url else '' }} portal-v2c-post-card {{ 'is-pinned' if post.is_pinned else '' }} {{ 'is-instagram' if is_instagram else '' }} {{ 'is-instagram-story' if post.post_type == 'instagram_story' else '' }}\" aria-label=\"Portal paylaşımı\" data-portal-post-card data-portal-post-id=\"{{ post.id }}\">"""
        text, _ = replace_required(text, old, new, "post card article")
        changes.append("_post_card.html paylaşım kartına JS hedef alanı eklendi")
    if "data-portal-reaction-total" not in text:
        old = """<div class=\"portal-post-stats\">\n      <span><i class=\"fa-regular fa-face-smile\"></i> {{ item.total_reactions }} tepki</span>\n      <span><i class=\"fa-regular fa-comment\"></i> {{ item.comments_count }} yorum</span>"""
        new = """<div class=\"portal-post-stats\">\n      <span data-portal-reaction-total><i class=\"fa-regular fa-face-smile\"></i> {{ item.total_reactions }} tepki</span>\n      <span><i class=\"fa-regular fa-comment\"></i> {{ item.comments_count }} yorum</span>"""
        text, _ = replace_required(text, old, new, "reaction total node")
        changes.append("_post_card.html tepki toplamı yenilenebilir hale getirildi")
    if "data-portal-reaction-button" not in text:
        old = """<button class=\"portal-reaction {{ 'active' if item.user_reaction == r.key else '' }}\" type=\"submit\" title=\"{{ r.label }}\">\n            <i class=\"{{ r.icon }}\"></i><span>{{ r.label }}</span>{% if item.reaction_counts.get(r.key) %}<b>{{ item.reaction_counts.get(r.key) }}</b>{% endif %}\n          </button>"""
        new = """<button class=\"portal-reaction {{ 'active' if item.user_reaction == r.key else '' }}\" type=\"submit\" title=\"{{ r.label }}\" data-portal-reaction-button data-reaction-key=\"{{ r.key }}\" data-reaction-label=\"{{ r.label }}\">\n            <i class=\"{{ r.icon }}\"></i><span>{{ r.label }}</span><b data-portal-reaction-count=\"{{ r.key }}\"{% if not item.reaction_counts.get(r.key) %} hidden{% endif %}>{{ item.reaction_counts.get(r.key, 0) }}</b>\n          </button>"""
        text, _ = replace_required(text, old, new, "reaction button")
        changes.append("_post_card.html tepki butonları yenilenebilir hale getirildi")
    write(path, text)


def patch_js(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app/static/js/bys360_portal.js"
    backup(path, backup_root, project_root)
    text = read(path)
    if "updateReactionUi" not in text:
        old = """  document.querySelectorAll('[data-portal-inline-form], [data-portal-quick-action]').forEach(function (form) {\n    form.addEventListener('submit', function () {\n      var btn = form.querySelector('button[type=\"submit\"]');\n      if (btn) btn.disabled = true;\n    });\n  });\n})();"""
        new = """  function portalFetchHeaders() {\n    return {\n      'X-Requested-With': 'XMLHttpRequest',\n      'Accept': 'application/json'\n    };\n  }\n\n  function showPortalInlineMessage(card, message, isError) {\n    if (!card || !message) return;\n    var box = card.querySelector('[data-portal-inline-message]');\n    if (!box) {\n      box = document.createElement('div');\n      box.setAttribute('data-portal-inline-message', '');\n      box.className = 'portal-inline-message';\n      var row = card.querySelector('.portal-reaction-row');\n      if (row && row.parentNode) row.parentNode.insertBefore(box, row.nextSibling);\n      else card.appendChild(box);\n    }\n    box.textContent = message;\n    box.classList.toggle('is-error', !!isError);\n    box.hidden = false;\n    window.clearTimeout(box._portalTimer);\n    box._portalTimer = window.setTimeout(function () { box.hidden = true; }, isError ? 4500 : 2200);\n  }\n\n  function updateReactionUi(card, data) {\n    if (!card || !data || !data.ok) return;\n    var counts = data.reaction_counts || {};\n    card.querySelectorAll('[data-portal-reaction-button]').forEach(function (button) {\n      var key = button.getAttribute('data-reaction-key');\n      var countNode = button.querySelector('[data-portal-reaction-count]');\n      var count = parseInt(counts[key] || 0, 10);\n      button.classList.toggle('active', data.user_reaction === key);\n      button.disabled = false;\n      if (countNode) {\n        countNode.textContent = String(count);\n        countNode.hidden = !count;\n      }\n    });\n    var totalNode = card.querySelector('[data-portal-reaction-total]');\n    if (totalNode) {\n      totalNode.innerHTML = '<i class=\"fa-regular fa-face-smile\"></i> ' + String(data.total_reactions || 0) + ' tepki';\n    }\n  }\n\n  document.querySelectorAll('[data-portal-quick-action]').forEach(function (form) {\n    var reactionButton = form.querySelector('[data-portal-reaction-button]');\n    if (!reactionButton) {\n      form.addEventListener('submit', function () {\n        var btn = form.querySelector('button[type=\"submit\"]');\n        if (btn) btn.disabled = true;\n      });\n      return;\n    }\n\n    form.addEventListener('submit', function (event) {\n      if (!window.fetch || !window.FormData) return;\n      event.preventDefault();\n      var card = form.closest('[data-portal-post-card]') || form.closest('.portal-post-card');\n      var btn = form.querySelector('button[type=\"submit\"]');\n      if (btn) btn.disabled = true;\n      var body = new FormData(form);\n      body.set('_ajax', '1');\n      fetch(form.action, {\n        method: 'POST',\n        body: body,\n        credentials: 'same-origin',\n        headers: portalFetchHeaders()\n      })\n        .then(function (response) {\n          return response.json().then(function (data) {\n            if (!response.ok || !data.ok) throw data;\n            return data;\n          });\n        })\n        .then(function (data) {\n          updateReactionUi(card, data);\n          showPortalInlineMessage(card, data.message || 'Tepkiniz güncellendi.', false);\n        })\n        .catch(function (error) {\n          var message = (error && error.message) || 'Tepki kaydedilemedi. Lütfen tekrar deneyin.';\n          showPortalInlineMessage(card, message, true);\n        })\n        .finally(function () {\n          if (btn) btn.disabled = false;\n        });\n    });\n  });\n\n  document.querySelectorAll('[data-portal-inline-form]').forEach(function (form) {\n    form.addEventListener('submit', function () {\n      var btn = form.querySelector('button[type=\"submit\"]');\n      if (btn) btn.disabled = true;\n    });\n  });\n})();"""
        text, _ = replace_required(text, old, new, "portal quick-action JS")
        changes.append("bys360_portal.js sayfa yenilemesiz tepki akışına geçirildi")
    write(path, text)


def patch_css(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app/static/css/bys360_portal.css"
    backup(path, backup_root, project_root)
    text = read(path)
    marker = "BYS360_PORTAL_AJAX_REACTIONS_V1_BEGIN"
    if marker not in text:
        text += """\n/* BYS360_PORTAL_AJAX_REACTIONS_V1_BEGIN */\n.portal-inline-message{margin:0 18px 10px;border:1px solid rgba(139,0,0,.10);background:rgba(139,0,0,.045);color:#5a3030;border-radius:14px;padding:8px 11px;font-size:.82rem;font-weight:850}.portal-inline-message.is-error{border-color:rgba(185,28,28,.20);background:rgba(185,28,28,.06);color:#7f1d1d}.portal-reaction[disabled]{opacity:.72;cursor:progress}\n/* BYS360_PORTAL_AJAX_REACTIONS_V1_END */\n"""
        changes.append("bys360_portal.css AJAX tepki mesaj stili eklendi")
    write(path, text)


def patch_cache_bust(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    files = [
        "app/templates/portal/feed.html",
        "app/templates/portal/groups.html",
        "app/templates/portal/group_detail.html",
        "app/templates/portal/moderation.html",
        "app/templates/portal/people.html",
        "app/templates/portal/profile.html",
    ]
    for rel in files:
        path = project_root / rel
        if not path.exists():
            continue
        backup(path, backup_root, project_root)
        text = read(path)
        original = text
        text = text.replace("js/bys360_portal.js') }}?v=mobile-portal-light-home-v2-8-81", "js/bys360_portal.js') }}?v=portal-ajax-reactions-v1")
        text = text.replace("js/bys360_portal.js') }}?v=portal-iphone-responsive-v2-11-5", "js/bys360_portal.js') }}?v=portal-ajax-reactions-v1")
        text = text.replace("js/bys360_portal.js') }}?v=portal-iphone-responsive-v2-11", "js/bys360_portal.js') }}?v=portal-ajax-reactions-v1")
        if text != original:
            changes.append(f"{rel} JS cache etiketi güncellendi")
            write(path, text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["all", "repair", "audit"])
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / "backups" / f"portal_ajax_reactions_v1_{stamp}"
    changes: list[str] = []

    if args.mode in {"all", "repair"}:
        patch_routes(project_root, backup_root, changes)
        patch_post_card(project_root, backup_root, changes)
        patch_js(project_root, backup_root, changes)
        patch_css(project_root, backup_root, changes)
        patch_cache_bust(project_root, backup_root, changes)

    result = {
        "package": PACKAGE,
        "mode": args.mode,
        "project_root": str(project_root),
        "backup_root": str(backup_root) if backup_root.exists() else None,
        "changed_count": len(changes),
        "changes": changes,
        "ok": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
