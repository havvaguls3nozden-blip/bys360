from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH"

PHASE3_SERVICE_BLOCK = '''
# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_BEGIN


def _cic_phase3_public_error(message: str) -> str:
    raw = (message or "").strip()
    lowered = raw.lower()
    if not raw:
        return "Gönderim tamamlanamadı. Mail altyapısı ve alıcı bilgileri kontrol edilmelidir."
    if "mail_server" in lowered or "smtp" in lowered or "connection" in lowered or "timeout" in lowered:
        return "Mail sunucusuna ulaşılamadı. Kurumsal mail sunucu ayarları kontrol edilmelidir."
    if "mail_default_sender" in lowered or "sender" in lowered or "from" in lowered:
        return "Gönderici mail adresi tanımlı değil. Mail ayarları kontrol edilmelidir."
    if "password" in lowered or "authentication" in lowered or "login" in lowered:
        return "Mail kullanıcı adı veya şifre doğrulanamadı. Kurumsal mail bilgileri kontrol edilmelidir."
    if "geçersiz" in lowered or "invalid" in lowered or "@" in raw:
        return raw[:220]
    return raw[:220]


def _cic_phase3_task_label(task_key: str) -> str:
    meta = TASK_DEFINITIONS.get(task_key) or {}
    return meta.get("label") or task_key


def _cic_phase3_actor_label(actor_user_id: int | None = None) -> str:
    try:
        if actor_user_id:
            u = User.query.get(actor_user_id)
            return _user_name(u)
    except Exception:
        pass
    return "Sistem"


def _cic_phase3_store_result(task_key: str, result: dict[str, Any], actor_user_id: int | None = None) -> None:
    try:
        set_setting(f"{BASE_KEY}.phase3.last_result", _dumps_json(result), label="Kurumsal bilgilendirme son gönderim özeti", value_type="json", actor_user_id=actor_user_id)
        set_setting(f"{BASE_KEY}.phase3.last_result.{task_key}", _dumps_json(result), label=f"{_cic_phase3_task_label(task_key)} son işlem özeti", value_type="json", actor_user_id=actor_user_id)
    except Exception:
        pass


def _cic_phase3_make_result(*, task_key: str, dry_run: bool, users: list[User], ok_count: int, fail_count: int, skipped_count: int, details: list[dict[str, Any]], started: float, actor_user_id: int | None = None, message: str | None = None) -> dict[str, Any]:
    elapsed = round(time.time() - started, 2)
    task_label = _cic_phase3_task_label(task_key)
    if message:
        public_message = message
    elif dry_run:
        public_message = f"{task_label} kuru çalışma tamamlandı. Gerçek mail gönderilmedi. Alıcı sayısı: {len(users)}."
    elif fail_count:
        public_message = f"{task_label} tamamlandı; {ok_count} başarılı, {fail_count} hatalı kayıt var. Hatalı alıcılar gönderim geçmişinden kontrol edilmelidir."
    else:
        public_message = f"{task_label} başarıyla tamamlandı. {ok_count} alıcıya gönderildi."
    return {
        "version": VERSION,
        "ok": fail_count == 0 and len(users) > 0,
        "task_key": task_key,
        "task_label": task_label,
        "dry_run": bool(dry_run),
        "recipient_count": len(users),
        "success_count": ok_count,
        "fail_count": fail_count,
        "skipped_count": skipped_count,
        "message": public_message,
        "ran_at": _now().strftime("%d.%m.%Y %H:%M:%S"),
        "actor": _cic_phase3_actor_label(actor_user_id),
        "elapsed_seconds": elapsed,
        "details": details[:120],
    }


def send_task(task_key: str, *, dry_run: bool = False, override_users: list[User] | None = None, actor_user_id: int | None = None) -> dict[str, Any]:
    # Faz 3 güvenli gönderim akışı: dry-run, kişi bazlı log ve sade Türkçe sonuç.
    ensure_defaults(actor_user_id=actor_user_id)
    started = time.time()
    if task_key not in TASK_DEFINITIONS:
        result = {
            "version": VERSION,
            "ok": False,
            "task_key": task_key,
            "task_label": task_key,
            "dry_run": bool(dry_run),
            "recipient_count": 0,
            "success_count": 0,
            "fail_count": 1,
            "skipped_count": 0,
            "message": "Bilinmeyen görev seçildi. Görev listesi kontrol edilmelidir.",
            "ran_at": _now().strftime("%d.%m.%Y %H:%M:%S"),
            "actor": _cic_phase3_actor_label(actor_user_id),
            "elapsed_seconds": 0,
            "details": [],
        }
        _cic_phase3_store_result(task_key, result, actor_user_id)
        try:
            db.session.commit()
        except Exception:
            pass
        return result

    cfg = get_config()
    task_cfg = cfg.get("tasks", {}).get(task_key, {})
    task_label = _cic_phase3_task_label(task_key)

    if not task_cfg.get("enabled", False) and not dry_run:
        result = _cic_phase3_make_result(
            task_key=task_key,
            dry_run=dry_run,
            users=[],
            ok_count=0,
            fail_count=1,
            skipped_count=0,
            details=[],
            started=started,
            actor_user_id=actor_user_id,
            message=f"{task_label} pasif durumda. Gerçek gönderim yapılmadı. Görevi aktifleştirip tekrar deneyiniz.",
        )
        _cic_phase3_store_result(task_key, result, actor_user_id)
        db.session.commit()
        return result

    users = list(_recipients_for_task(task_key, override_users) or [])
    unique: list[User] = []
    seen: set[str] = set()
    for u in users:
        key = str(getattr(u, "id", "") or getattr(u, "email", "") or id(u))
        if key in seen:
            continue
        seen.add(key)
        unique.append(u)
    users = unique

    if not users:
        result = _cic_phase3_make_result(
            task_key=task_key,
            dry_run=dry_run,
            users=[],
            ok_count=0,
            fail_count=1,
            skipped_count=0,
            details=[],
            started=started,
            actor_user_id=actor_user_id,
            message=f"{task_label} için alıcı bulunamadı. Alıcı Yönetimi ekranından personel veya yönetici alıcıları seçilmelidir.",
        )
        _cic_phase3_store_result(task_key, result, actor_user_id)
        tasks = cfg.get("tasks", {})
        tasks.setdefault(task_key, {}).update({"last_status": "Alıcı bulunamadı", "last_run_at": _now().strftime("%d.%m.%Y %H:%M")})
        set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)
        set_setting(f"{BASE_KEY}.last_status", f"{task_label}: Alıcı bulunamadı", label="Son kurumsal bilgilendirme durumu", actor_user_id=actor_user_id)
        db.session.commit()
        return result

    tmpl = get_template(task_key)
    ok_count = 0
    fail_count = 0
    skipped_count = 0
    details: list[dict[str, Any]] = []
    mail_type = f"corporate_information_{'dry_run_' if dry_run else ''}{task_key}"

    for user in users:
        user_id = getattr(user, "id", None)
        email = (getattr(user, "email", None) or "").strip()
        name = _user_name(user)
        subject = _render_template_text(tmpl.get("subject", ""), user, task_key).strip()
        body = _render_template_text(tmpl.get("body", ""), user, task_key).strip()

        if not email:
            fail_count += 1
            status_text = "E-posta adresi bulunmadığı için gönderim yapılamadı."
            details.append({"user_id": user_id, "name": name, "email": "", "ok": False, "status": status_text, "subject": subject})
            try:
                if create_mail_log is not None:
                    create_mail_log(mail_type=mail_type, recipient_email=f"user-{user_id or 'unknown'}@no-email.local", subject=subject or task_label, body=body, user_id=user_id, sent_by_id=actor_user_id, is_success=False, error_message=status_text)
            except Exception:
                pass
            continue

        if dry_run:
            ok = True
            raw_msg = "Kuru çalışma: gerçek mail gönderilmedi."
        else:
            if send_email is None:
                ok, raw_msg = False, "Mail gönderim servisi bulunamadı."
            else:
                try:
                    sent_result = send_email(email, subject, body)
                    if isinstance(sent_result, tuple):
                        ok, raw_msg = bool(sent_result[0]), str(sent_result[1] if len(sent_result) > 1 else "")
                    else:
                        ok, raw_msg = bool(sent_result), "Gönderim tamamlandı." if sent_result else "Gönderim tamamlanamadı."
                except Exception as exc:
                    ok, raw_msg = False, str(exc)
        status_text = "Kuru çalışma tamamlandı; mail gönderilmedi." if dry_run else ("Gönderildi." if ok else _cic_phase3_public_error(raw_msg))
        if ok:
            ok_count += 1
        else:
            fail_count += 1
        details.append({"user_id": user_id, "name": name, "email": email, "ok": bool(ok), "status": status_text, "subject": subject})
        try:
            if create_mail_log is not None:
                create_mail_log(mail_type=mail_type, recipient_email=email, subject=subject or task_label, body=body, user_id=user_id, sent_by_id=actor_user_id, is_success=bool(ok), error_message=None if ok else status_text)
        except Exception:
            pass

    result = _cic_phase3_make_result(task_key=task_key, dry_run=dry_run, users=users, ok_count=ok_count, fail_count=fail_count, skipped_count=skipped_count, details=details, started=started, actor_user_id=actor_user_id)
    tasks = cfg.get("tasks", {})
    status = f"{'Kuru çalışma' if dry_run else 'Gönderim'}: {ok_count} başarılı, {fail_count} hatalı, {round(time.time() - started, 2)} sn"
    tasks.setdefault(task_key, {}).update({"last_status": status, "last_run_at": _now().strftime("%d.%m.%Y %H:%M")})
    set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_status", f"{task_label}: {status}", label="Son kurumsal bilgilendirme durumu", actor_user_id=actor_user_id)
    _cic_phase3_store_result(task_key, result, actor_user_id)
    db.session.commit()
    return result


def get_recent_logs(limit: int = 120) -> list[Any]:
    try:
        from app.models import MailLog
        return MailLog.query.filter(MailLog.mail_type.like("corporate_information_%")).order_by(MailLog.sent_at.desc(), MailLog.id.desc()).limit(limit).all()
    except Exception:
        return []


def _cic_phase3_last_result() -> dict[str, Any]:
    value = _loads_json(f"{BASE_KEY}.phase3.last_result", {})
    return value if isinstance(value, dict) else {}


def context(search: str | None = None) -> dict[str, Any]:
    ensure_defaults()
    cfg = get_config()
    rec = get_recipients()
    users = list_users(search=search, limit=800)
    tasks = []
    for key, meta in TASK_DEFINITIONS.items():
        tcfg = cfg["tasks"].get(key, {})
        tasks.append({"key": key, **meta, **tcfg, "subject": get_template(key)["subject"], "body": get_template(key)["body"]})
    phase3_last_result = _cic_phase3_last_result()
    logs = get_recent_logs(120)
    return {
        "version": VERSION,
        "config": cfg,
        "tasks": tasks,
        "task_definitions": TASK_DEFINITIONS,
        "manager_recipients": rec["managers"],
        "staff_recipients": rec["staff"],
        "staff_mode": rec["staff_mode"],
        "users": users,
        "search": search or "",
        "logs": logs,
        "location": cfg["location_name"],
        "phase3_last_result": phase3_last_result,
        "stats": {
            "active_tasks": sum(1 for t in tasks if t.get("enabled")),
            "manager_count": len(rec["managers"]),
            "staff_count": len(rec["staff"]),
            "last_status": get_setting(f"{BASE_KEY}.last_status", "Henüz gönderim yapılmadı"),
            "last_phase3_status": phase3_last_result.get("message") or "Henüz Faz 3 gönderim testi yapılmadı.",
        },
    }

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_END
'''.lstrip()

TEST_TEMPLATE = '''{% extends "corporate_information_center/base.html" %}
{% set active_tab='test' %}
{% block cic_content %}
<!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_TEMPLATE_BEGIN -->
<div class="cic-grid">
  <div class="cic-card span-12">
    <div class="cic-task-head">
      <div>
        <span class="cic-badge ok"><i class="fa-solid fa-shield-check"></i> Faz 3 gönderim akışı aktif</span>
        <h3 style="margin-top:10px">Kuru Çalışma, Alıcı Özeti ve Güvenli Gönderim</h3>
        <p class="cic-muted" style="margin-bottom:0">Gerçek mail göndermeden önce kuru çalışma ile alıcı sayısı, konu ve kişi bazlı durumlar kontrol edilir. Gerçek gönderimde her alıcı için mail log kaydı oluşur.</p>
      </div>
      <a class="cic-btn secondary" href="/dashboard/kurumsal-bilgilendirme/loglar"><i class="fa-solid fa-clock-rotate-left"></i> Geçmişi Aç</a>
    </div>
  </div>

  <form method="post" class="span-5 cic-card" id="cicPhase3TestForm">
    <h3>Gönderim Kontrolü</h3>
    <label>Görev
      <select class="cic-select" name="task_key">
        {% for task in tasks %}<option value="{{ task.key }}">{{ task.label }}</option>{% endfor %}
      </select>
    </label>
    <label class="mt-2 d-block">Hedef
      <select class="cic-select" name="target" id="cicTargetSelect">
        <option value="self">Sadece bana gönder</option>
        <option value="selected">Aşağıda seçtiğim kişilere gönder</option>
      </select>
    </label>
    <label class="cic-task mt-2" style="display:block">
      <input type="checkbox" name="dry_run" value="1" checked id="cicDryRunCheck">
      <strong>Kuru çalışma yap; gerçek mail gönderme</strong><br>
      <small class="cic-muted">Önce bu seçenek açık kalmalı. Sonuç doğruysa gerçek gönderim için işaret kaldırılır.</small>
    </label>
    <div class="cic-help" id="cicRealSendWarning" style="display:none;margin-top:10px;background:#fffaeb;border-color:#fedf89;color:#93370d">
      <strong>Dikkat:</strong> Kuru çalışma kapalı. Bu işlem gerçek e-posta gönderebilir. Alıcı listesini ve mail konusunu kontrol etmeden ilerlemeyin.
    </div>
    <button class="cic-btn mt-3" style="width:100%;justify-content:center"><i class="fa-solid fa-paper-plane"></i> Kontrolü Çalıştır</button>
  </form>

  <div class="cic-card span-7">
    <h3>Son İşlem Özeti</h3>
    {% if phase3_last_result %}
      <div class="cic-grid" style="gap:10px;margin-bottom:12px">
        <div class="span-3 cic-help"><strong>{{ phase3_last_result.recipient_count or 0 }}</strong><br><small>Alıcı</small></div>
        <div class="span-3 cic-help"><strong>{{ phase3_last_result.success_count or 0 }}</strong><br><small>Başarılı</small></div>
        <div class="span-3 cic-help"><strong>{{ phase3_last_result.fail_count or 0 }}</strong><br><small>Hatalı</small></div>
        <div class="span-3 cic-help"><strong>{{ 'Evet' if phase3_last_result.dry_run else 'Hayır' }}</strong><br><small>Kuru Çalışma</small></div>
      </div>
      <p class="{{ 'cic-badge ok' if phase3_last_result.ok else 'cic-badge warn' }}" style="display:inline-flex;margin-bottom:10px">{{ phase3_last_result.message }}</p>
      <p class="cic-muted">Görev: <strong>{{ phase3_last_result.task_label }}</strong> · Tarih: {{ phase3_last_result.ran_at }} · İşlemi yapan: {{ phase3_last_result.actor or '-' }}</p>
      <div style="max-height:360px;overflow:auto">
        <table class="cic-table">
          <thead><tr><th>Alıcı</th><th>E-posta</th><th>Durum</th></tr></thead>
          <tbody>
            {% for item in phase3_last_result.details or [] %}
              <tr>
                <td>{{ item.name or '-' }}</td>
                <td>{{ item.email or '-' }}</td>
                <td>{% if item.ok %}<span class="cic-badge ok">{{ item.status }}</span>{% else %}<span class="cic-badge warn">{{ item.status }}</span>{% endif %}</td>
              </tr>
            {% else %}
              <tr><td colspan="3">Bu işlem için kişi detayı bulunmuyor.</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% else %}
      <div class="cic-help">Henüz Faz 3 kuru çalışma veya gönderim sonucu bulunmuyor. Önce kuru çalışma ile kontrol başlatın.</div>
    {% endif %}
  </div>

  <div class="cic-card span-12">
    <div class="cic-task-head">
      <div>
        <h3>İsteğe Bağlı Test Alıcıları</h3>
        <p class="cic-muted">“Aşağıda seçtiğim kişilere gönder” seçilirse bu listedeki kişiler kullanılır.</p>
      </div>
      <div class="cic-toolbar">
        <input class="cic-input" id="cicPhase3UserSearch" type="search" placeholder="Ad, soyad, e-posta, birim ara...">
        <button type="button" class="cic-btn ghost" data-action="select-visible"><i class="fa-solid fa-check-double"></i> Görünenleri Seç</button>
        <button type="button" class="cic-btn ghost" data-action="clear-selected"><i class="fa-solid fa-eraser"></i> Temizle</button>
      </div>
    </div>
    <div class="cic-grid" style="margin-top:12px">
      {% for user in users %}
      {% set uname = ((user.ad or '') ~ ' ' ~ (user.soyad or ''))|trim or user.full_name_cache or user.email %}
      <label class="cic-person-card span-6" data-phase3-user data-search="{{ (uname ~ ' ' ~ (user.email or '') ~ ' ' ~ (user.birim or '') ~ ' ' ~ (user.unvan or ''))|lower }}">
        <input type="checkbox" name="user_ids" value="{{ user.id }}" form="cicPhase3TestForm">
        <span class="cic-person">
          <span class="cic-avatar">{{ (uname or '?')[:1] }}</span>
          <span><strong>{{ uname }}</strong><br><small class="cic-muted">{{ user.email or 'E-posta yok' }} · {{ user.birim or '-' }} · {{ user.unvan or '-' }}</small></span>
        </span>
      </label>
      {% else %}
      <div class="span-12 cic-help">Listelenecek kullanıcı bulunamadı.</div>
      {% endfor %}
    </div>
  </div>
</div>
<script>
(function(){
  var dry=document.getElementById('cicDryRunCheck');
  var warn=document.getElementById('cicRealSendWarning');
  function syncWarn(){ if(warn) warn.style.display = dry && !dry.checked ? 'block':'none'; }
  if(dry){ dry.addEventListener('change', syncWarn); syncWarn(); }
  var search=document.getElementById('cicPhase3UserSearch');
  var cards=[].slice.call(document.querySelectorAll('[data-phase3-user]'));
  function norm(v){ return (v||'').toString().toLocaleLowerCase('tr-TR'); }
  if(search){ search.addEventListener('input', function(){ var q=norm(search.value); cards.forEach(function(c){ c.style.display = !q || norm(c.getAttribute('data-search')).indexOf(q)>-1 ? '' : 'none'; }); }); }
  document.addEventListener('click', function(e){ var btn=e.target.closest('button[data-action]'); if(!btn) return; var act=btn.getAttribute('data-action'); if(act==='select-visible'){ cards.forEach(function(c){ if(c.style.display==='none') return; var x=c.querySelector('input[type=checkbox]'); if(x) x.checked=true; }); } if(act==='clear-selected'){ cards.forEach(function(c){ var x=c.querySelector('input[type=checkbox]'); if(x) x.checked=false; }); } });
})();
</script>
<!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_TEMPLATE_END -->
{% endblock %}
'''

LOGS_TEMPLATE = '''{% extends "corporate_information_center/base.html" %}
{% set active_tab='logs' %}
{% block cic_content %}
<!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_LOGS_BEGIN -->
<div class="cic-grid">
  <div class="cic-card span-12">
    <div class="cic-task-head">
      <div>
        <h3>Gönderim Geçmişi</h3>
        <p class="cic-muted">Faz 3 kapsamında kuru çalışma ve gerçek gönderim kayıtları kişi bazında izlenir. Hatalar teknik dil yerine kullanıcı dostu açıklamayla gösterilir.</p>
      </div>
      <a class="cic-btn secondary" href="/dashboard/kurumsal-bilgilendirme/test"><i class="fa-solid fa-vial"></i> Test Merkezine Git</a>
    </div>
  </div>
  <div class="cic-card span-12">
    <table class="cic-table">
      <thead><tr><th>Tarih</th><th>Tür</th><th>Alıcı</th><th>Konu</th><th>Sonuç</th></tr></thead>
      <tbody>
        {% for log in logs %}
        <tr>
          <td>{{ log.sent_at.strftime('%d.%m.%Y %H:%M') if log.sent_at else '-' }}</td>
          <td>
            {% if 'dry_run' in (log.mail_type or '') %}<span class="cic-badge warn">Kuru Çalışma</span>{% else %}<span class="cic-badge">Gerçek Gönderim</span>{% endif %}<br>
            <small class="cic-muted">{{ log.mail_type }}</small>
          </td>
          <td>{{ log.recipient_email }}</td>
          <td>{{ log.subject }}</td>
          <td>{% if log.is_success %}<span class="cic-badge ok">Başarılı</span>{% else %}<span class="cic-badge warn">Hatalı</span><br><small>{{ log.error_message or 'Gönderim tamamlanamadı.' }}</small>{% endif %}</td>
        </tr>
        {% else %}
        <tr><td colspan="5">Henüz kurumsal bilgilendirme gönderim kaydı bulunmuyor.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_LOGS_END -->
{% endblock %}
'''


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup(path: Path) -> None:
    if not path.exists():
        return
    bak = path.with_suffix(path.suffix + ".phase3_dispatch.bak")
    if not bak.exists():
        shutil.copy2(path, bak)


def remove_block(text: str) -> str:
    pattern = rf"\n?#\s*{re.escape(VERSION)}_BEGIN.*?#\s*{re.escape(VERSION)}_END\n?"
    return re.sub(pattern, "\n", text, flags=re.DOTALL)


def patch_service(root: Path) -> None:
    path = root / "app" / "services" / "corporate_information_center.py"
    if not path.exists():
        raise FileNotFoundError(f"Kurumsal bilgilendirme service dosyası bulunamadı: {path}")
    text = read_text(path)
    if "def send_task(" not in text or "def context(" not in text:
        raise RuntimeError("Beklenen send_task/context fonksiyonları bulunamadı; dosya yapısı kontrol edilmeli.")
    backup(path)
    text = remove_block(text).rstrip() + "\n\n" + PHASE3_SERVICE_BLOCK + "\n"
    write_text(path, text)


def patch_routes(root: Path) -> None:
    path = root / "app" / "communication" / "corporate_information_center_routes.py"
    if not path.exists():
        return
    text = read_text(path)
    backup(path)
    text = text.replace(
        "flash(f\"{result.get('task_label', 'Görev')} sonucu: {result.get('success_count', 0)} başarılı, {result.get('fail_count', 0)} hatalı.\", \"success\" if result.get(\"ok\") else \"warning\")",
        "flash(result.get('message') or f\"{result.get('task_label', 'Görev')} sonucu: {result.get('success_count', 0)} başarılı, {result.get('fail_count', 0)} hatalı.\", \"success\" if result.get(\"ok\") else \"warning\")",
    )
    text = text.replace(
        "flash(f\"{result.get('task_label', task_key)} çalıştırıldı: {result.get('success_count', 0)} başarılı, {result.get('fail_count', 0)} hatalı.\", \"success\" if result.get(\"ok\") else \"warning\")",
        "flash(result.get('message') or f\"{result.get('task_label', task_key)} çalıştırıldı: {result.get('success_count', 0)} başarılı, {result.get('fail_count', 0)} hatalı.\", \"success\" if result.get(\"ok\") else \"warning\")",
    )
    if VERSION not in text:
        text = text.replace("from __future__ import annotations\n", f"from __future__ import annotations\n# {VERSION}\n", 1)
    write_text(path, text)


def patch_templates(root: Path) -> None:
    base = root / "app" / "templates" / "corporate_information_center"
    test = base / "test.html"
    logs = base / "logs.html"
    if not base.exists():
        raise FileNotFoundError(f"Template klasörü bulunamadı: {base}")
    backup(test)
    backup(logs)
    write_text(test, TEST_TEMPLATE)
    write_text(logs, LOGS_TEMPLATE)


def run_compile(root: Path) -> None:
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if (sys.platform.startswith("win") and py.exists()) else sys.executable
    files = [root / "app" / "services" / "corporate_information_center.py", root / "app" / "communication" / "corporate_information_center_routes.py"]
    result = subprocess.run([python, "-m", "py_compile", *[str(f) for f in files if f.exists()]], cwd=str(root), text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError((result.stdout or "") + (result.stderr or ""))


def gate(root: Path) -> list[str]:
    checks = []
    required = {
        root / "app/services/corporate_information_center.py": [VERSION, "def _cic_phase3_public_error", "def send_task(", "phase3.last_result", "dry_run_"],
        root / "app/templates/corporate_information_center/test.html": [VERSION, "Son İşlem Özeti", "cicDryRunCheck", "Gerçek mail göndermeden"],
        root / "app/templates/corporate_information_center/logs.html": [VERSION, "Kuru Çalışma", "Gerçek Gönderim"],
    }
    for path, needles in required.items():
        if not path.exists():
            checks.append(f"Eksik dosya: {path}")
            continue
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                checks.append(f"{path} içinde eksik ifade: {needle}")
    return checks


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    print("BYS360 Kurumsal Bilgilendirme Merkezi Faz 3 gönderim akışı uygulanıyor...")
    print(f"ProjectRoot={root}")
    patch_service(root)
    patch_routes(root)
    patch_templates(root)
    run_compile(root)
    print(f"{VERSION}_APPLY_OK")
    errors = gate(root)
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 2
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    print("Güncellenen dosyalar:")
    print(" - app/services/corporate_information_center.py")
    print(" - app/communication/corporate_information_center_routes.py")
    print(" - app/templates/corporate_information_center/test.html")
    print(" - app/templates/corporate_information_center/logs.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
