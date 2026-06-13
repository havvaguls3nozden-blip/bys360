from __future__ import annotations



from app.main_handlers.account_communication_helpers import *  # noqa: F401,F403
from app.main_handlers.account_visibility_helpers import *  # noqa: F401,F403


# BYS360_PERSONNEL_FEATURE_MATRIX_V1_4_HELPER_DEDUP_AND_FULL_SAVE
def _bys360_personnel_feature_matrix_v14_dedupe_items(items):
    seen = set()
    result = []
    for item in items or []:
        key = str((item or {}).get("key") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        clean = dict(item)
        clean["key"] = key
        result.append(clean)
    return result


def _bys360_personnel_feature_matrix_v14_dedupe_grouped_menu(grouped):
    seen = set()
    result = {}
    for group_name, items in (grouped or {}).items():
        clean_items = []
        for item in items or []:
            key = str((item or {}).get("key") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            clean = dict(item)
            clean["key"] = key
            clean_items.append(clean)
        if clean_items:
            result[group_name] = clean_items
    return result


def settings_page():
    grouped_menu_definitions = _bys360_personnel_feature_matrix_v14_dedupe_grouped_menu(get_grouped_menu_definitions())
    flat_menu_items = _bys360_personnel_feature_matrix_v14_dedupe_items(flatten_settings_menu_definitions())
    flat_menu_items = _bys360_personnel_feature_matrix_v14_dedupe_items(extend_flat_menu_items_with_assistant_role_matrix_items(flat_menu_items))
    # BYS360_PERSONNEL_FEATURE_MATRIX_V1_3_DEDUP_HELPER
    # Aynı menu_key birden fazla kaynaktan geldiyse tek satıra indirir.
    # Örnek: ai_agent_panel hem genel menüden hem asistan matrisi ekinden gelirse
    # user_menu_permissions tablosundaki unique constraint hata vermemelidir.
    _seen_menu_keys = set()
    _deduped_flat_menu_items = []
    for _item in flat_menu_items or []:
        _menu_key = str((_item or {}).get("key") or "").strip()
        if not _menu_key or _menu_key in _seen_menu_keys:
            continue
        _seen_menu_keys.add(_menu_key)
        _clean_item = dict(_item)
        _clean_item["key"] = _menu_key
        _deduped_flat_menu_items.append(_clean_item)
    flat_menu_items = _deduped_flat_menu_items
    all_menu_keys = [item["key"] for item in flat_menu_items]
    users = (
        User.query
        .filter(User.role != "admin")
        .order_by(User.ad.asc(), User.soyad.asc())
        .all()
    )
    selected_user_id = request.values.get("user_id", type=int)
    selected_user = db.session.get(User, selected_user_id) if selected_user_id else None
    compare_user_id = request.values.get("compare_user_id", type=int)
    compare_user = db.session.get(User, compare_user_id) if compare_user_id else None
    selected_rule_map = {}
    settings_matrix = None
    settings_presets = {"presets": [], "group_toggles": []}
    bulk_settings_profiles = _build_bulk_settings_profiles(grouped_menu_definitions)
    bulk_target_users = _serialize_bulk_target_users(users)
    role_options = sorted({(user.role or "").strip() for user in users if (user.role or "").strip()})
    birim_options = sorted({(user.birim or "").strip() for user in users if (user.birim or "").strip()})
    bulk_result_summary = _resolve_bulk_result_summary_from_args(request.args, grouped_menu_definitions)
    phase1_seed_summary = ensure_settings_phase1_seeded(updated_by_user_id=getattr(current_user, "id", None))
    if not phase1_seed_summary.get("ok"):
        missing_tables = phase1_seed_summary.get('missing_tables') or []
        if missing_tables:
            flash(
                'Ayarlar altyapısı henüz veritabanına uygulanmamış. Eksik tablolar: ' + ', '.join(missing_tables) + '. Lütfen proje klasöründe flask db upgrade çalıştırın.',
                'warning',
            )
        elif phase1_seed_summary.get('error'):
            flash(f"Ayarlar omurgası hazırlanamadı: {phase1_seed_summary.get('error')}", 'warning')
    communication_role_matrix = _build_communication_role_matrix(_build_communication_policy_items(grouped_menu_definitions, flat_menu_items))
    assistant_role_matrix = _build_assistant_role_matrix()
    settings_role_matrix_groups = _build_settings_role_matrix_groups(grouped_menu_definitions, flat_menu_items)
    foundation_context = build_settings_foundation_context() if phase1_seed_summary.get("ok") else {
        "system_groups": [],
        "module_groups": [],
        "role_defaults_snapshot": [],
        "unit_profiles_snapshot": [],
        "recent_change_logs": [],
        "stats": {"system_total": 0, "module_total": 0, "module_group_total": 0, "role_total": 0, "unit_profile_total": 0, "history_total": 0},
    }

    if request.method == "POST":
        form_action = (request.form.get("form_action") or "save_user_visibility").strip()

        if form_action in {"reset_person_based_role_matrix", "reset_user_kişi bazlı yetkis"}:
            form_action = "reset_user_overrides"

        if form_action in {"save_personnel_feature_matrix_full", "save_personnel_matrix_full"}:
            form_action = "save_user_visibility"

        if form_action == "save_system_foundation":
            try:
                changed = save_system_settings_from_form(request.form, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"Genel sistem ayarları kaydedildi. Güncellenen alan: {changed}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Genel sistem ayarları kaydedilirken hata oluştu: {exc}", "danger")
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id) if keep_user_id else url_for("main.settings_page"))

        if form_action == "save_module_foundation":
            try:
                changed = save_module_settings_from_form(request.form, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"Modül ayar omurgası kaydedildi. Güncellenen alan: {changed}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Modül ayarları kaydedilirken hata oluştu: {exc}", "danger")
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id) if keep_user_id else url_for("main.settings_page"))

        if form_action == "sync_role_defaults":
            seed_result = ensure_settings_phase1_seeded(updated_by_user_id=getattr(current_user, "id", None))
            if seed_result.get("ok"):
                flash("Rol varsayılanı ve ayar omurgası senkronize edildi.", "success")
            else:
                flash(f"Rol varsayılanları senkronize edilirken hata oluştu: {seed_result.get('error')}", "danger")
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id) if keep_user_id else url_for("main.settings_page"))

        if form_action.startswith("save_role_matrix_group__"):
            matrix_key = form_action.replace("save_role_matrix_group__", "", 1).strip()
            changed_total = 0
            try:
                config, policy_items = _get_role_matrix_policy_items_or_raise(matrix_key, grouped_menu_definitions, flat_menu_items)
                scoped_keys = {item["key"] for item in policy_items}
                for role_key, _role_label in COMMUNICATION_POLICY_ROLE_OPTIONS:
                    current_visible = set(get_role_default_menu_keys(role_key))
                    scoped_visible = _collect_role_matrix_visible_keys_from_form(matrix_key, role_key, scoped_keys)
                    merged_visible = (current_visible - scoped_keys) | scoped_visible
                    changed_total += save_role_menu_defaults(role_key, all_menu_keys, merged_visible, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"{config['title']} kaydedildi. İşlenen satır: {changed_total}", "success")
                section_id = config["section_id"]
            except Exception as exc:
                db.session.rollback()
                flash(f"Rol matrisi kaydedilirken hata oluştu: {exc}", "danger")
                section_id = "module-role-matrices"
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id, section=section_id) if keep_user_id else url_for("main.settings_page", section=section_id))

        if form_action.startswith("reset_role_matrix_group__"):
            matrix_key = form_action.replace("reset_role_matrix_group__", "", 1).strip()
            changed_total = 0
            try:
                config, policy_items = _get_role_matrix_policy_items_or_raise(matrix_key, grouped_menu_definitions, flat_menu_items)
                scoped_keys = {item["key"] for item in policy_items}
                for role_key, _role_label in COMMUNICATION_POLICY_ROLE_OPTIONS:
                    current_visible = set(get_role_default_menu_keys(role_key))
                    static_visible = set(get_role_default_menu_keys(role_key, prefer_database=False))
                    if matrix_key == "assistant":
                        static_visible |= get_assistant_role_matrix_recommended_keys(role_key)
                    merged_visible = (current_visible - scoped_keys) | (static_visible & scoped_keys)
                    changed_total += save_role_menu_defaults(role_key, all_menu_keys, merged_visible, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"{config['title']} önerilen rol politikasına döndürüldü. İşlenen satır: {changed_total}", "success")
                section_id = config["section_id"]
            except Exception as exc:
                db.session.rollback()
                flash(f"Rol matrisi sıfırlanırken hata oluştu: {exc}", "danger")
                section_id = "module-role-matrices"
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id, section=section_id) if keep_user_id else url_for("main.settings_page", section=section_id))

        if form_action == "save_communication_role_matrix":
            communication_policy_items = _build_communication_policy_items(grouped_menu_definitions, flat_menu_items)
            communication_keys = {item["key"] for item in communication_policy_items}
            changed_total = 0
            try:
                for role_key, _role_label in COMMUNICATION_POLICY_ROLE_OPTIONS:
                    current_visible = set(get_role_default_menu_keys(role_key))
                    scoped_visible = {
                        item_key
                        for item_key in communication_keys
                        if request.form.get(f"role_policy__{role_key}__{item_key}")
                    }
                    merged_visible = (current_visible - communication_keys) | scoped_visible
                    changed_total += save_role_menu_defaults(role_key, all_menu_keys, merged_visible, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"İletişim ve anket rol matrisi kaydedildi. İşlenen satır: {changed_total}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"İletişim ve anket rol matrisi kaydedilirken hata oluştu: {exc}", "danger")
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id, section="communication-role-policy") if keep_user_id else url_for("main.settings_page", section="communication-role-policy"))

        if form_action == "reset_communication_role_matrix":
            communication_policy_items = _build_communication_policy_items(grouped_menu_definitions, flat_menu_items)
            communication_keys = {item["key"] for item in communication_policy_items}
            changed_total = 0
            try:
                for role_key, _role_label in COMMUNICATION_POLICY_ROLE_OPTIONS:
                    current_visible = set(get_role_default_menu_keys(role_key))
                    static_visible = set(get_role_default_menu_keys(role_key, prefer_database=False))
                    merged_visible = (current_visible - communication_keys) | (static_visible & communication_keys)
                    changed_total += save_role_menu_defaults(role_key, all_menu_keys, merged_visible, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"İletişim ve anket rol matrisi önerilen kurala döndürüldü. İşlenen satır: {changed_total}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Rol matrisi sıfırlanırken hata oluştu: {exc}", "danger")
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id, section="communication-role-policy") if keep_user_id else url_for("main.settings_page", section="communication-role-policy"))


        if form_action == "save_assistant_role_matrix":
            try:
                selected_count = save_assistant_role_matrix_from_form(request.form, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"Sanal Asistan rol matrisi kaydedildi. Açık rol sayısı: {selected_count}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Sanal Asistan rol matrisi kaydedilirken hata oluştu: {exc}", "danger")
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id, section="assistant-role-policy") if keep_user_id else url_for("main.settings_page", section="assistant-role-policy"))

        if form_action == "reset_assistant_role_matrix":
            try:
                selected_count = reset_assistant_role_matrix_defaults(updated_by_user_id=getattr(current_user, "id", None))
                flash(f"Sanal Asistan rol matrisi önerilen politikaya döndürüldü. Açık rol sayısı: {selected_count}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Sanal Asistan rol matrisi sıfırlanırken hata oluştu: {exc}", "danger")
            keep_user_id = request.form.get("keep_user_id", type=int)
            return redirect(url_for("main.settings_page", user_id=keep_user_id, section="assistant-role-policy") if keep_user_id else url_for("main.settings_page", section="assistant-role-policy"))

        if form_action == "rollback_settings_change_entry":
            log_id = request.form.get("change_log_id", type=int)
            keep_user_id = request.form.get("keep_user_id", type=int)
            try:
                result = rollback_settings_change(log_id, actor_user_id=getattr(current_user, "id", None))
                flash(result.get("summary") or "Ayar değişikliği geri alındı.", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Ayar geçmişi geri alınırken hata oluştu: {exc}", "danger")
            return redirect(url_for("main.settings_page", user_id=keep_user_id) if keep_user_id else url_for("main.settings_page"))

        if form_action == "bulk_apply_profile":
            profile_key = (request.form.get("bulk_profile_key") or "").strip()
            scope_type = (request.form.get("bulk_scope_type") or "role").strip()
            scope_role = (request.form.get("bulk_role") or "").strip()
            scope_birim = (request.form.get("bulk_birim") or "").strip()
            keep_user_id = request.form.get("keep_user_id", type=int)

            target_users = [user for user in users if getattr(user, "is_active", True)]
            if scope_type == "role" and scope_role:
                target_users = [user for user in target_users if (user.role or "").strip() == scope_role]
            elif scope_type == "birim" and scope_birim:
                target_users = [user for user in target_users if (user.birim or "").strip() == scope_birim]
            elif scope_type == "role_and_birim":
                if scope_role:
                    target_users = [user for user in target_users if (user.role or "").strip() == scope_role]
                if scope_birim:
                    target_users = [user for user in target_users if (user.birim or "").strip() == scope_birim]

            if not profile_key:
                flash("Toplu uygulama için bir profil seçiniz.", "warning")
                return redirect(url_for("main.settings_page", user_id=keep_user_id) if keep_user_id else url_for("main.settings_page"))
            if not target_users:
                flash("Seçilen kapsamda güncellenecek kullanıcı bulunamadı.", "warning")
                return redirect(url_for("main.settings_page", user_id=keep_user_id) if keep_user_id else url_for("main.settings_page"))

            try:
                for user in target_users:
                    visible_keys = set(_resolve_bulk_profile_keys(profile_key, user, grouped_menu_definitions))
                    _apply_visibility_keys_to_user(user, flat_menu_items, visible_keys)
                db.session.commit()
                bulk_summary = _build_bulk_result_summary(profile_key, scope_type, scope_role, scope_birim, target_users, grouped_menu_definitions)
                flash(f"{len(target_users)} kullanıcı için profil uygulandı.", "success")
                redirect_kwargs = {
                    "last_bulk_profile": bulk_summary["profile_key"],
                    "last_bulk_scope": bulk_summary["scope_type"],
                    "last_bulk_role": bulk_summary["scope_role"],
                    "last_bulk_birim": bulk_summary["scope_birim"],
                    "last_bulk_count": bulk_summary["target_count"],
                    "last_bulk_detail": bulk_summary["scope_detail"],
                    "last_bulk_preview": "||".join([row["name"] for row in bulk_summary["preview_users"]]),
                }
                if keep_user_id:
                    redirect_kwargs["user_id"] = keep_user_id
                return redirect(url_for("main.settings_page", **redirect_kwargs))
            except Exception as exc:
                db.session.rollback()
                flash(f"Toplu profil uygulanırken hata oluştu: {exc}", "danger")
                return redirect(url_for("main.settings_page", user_id=keep_user_id) if keep_user_id else url_for("main.settings_page"))

        if form_action == "export_visibility_template":
            export_user_id = request.form.get("user_id", type=int)
            export_user = db.session.get(User, export_user_id)
            if not export_user:
                flash("Dışa aktarma için kullanıcı seçiniz.", "warning")
                return redirect(url_for("main.settings_page"))
            export_ctx = build_effective_user_menu_context(export_user, flat_menu_items)
            payload = _build_visibility_template_payload(export_user, flat_menu_items, export_ctx)
            buffer = io.BytesIO(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
            safe_name = f"{(getattr(export_user, 'ad', '') + '_' + getattr(export_user, 'soyad', '')).strip('_') or 'kullanici'}"
            safe_name = safe_name.replace(' ', '_')
            return send_file(buffer, mimetype="application/json", as_attachment=True, download_name=f"bys360_yetki_sablonu_{safe_name}.json")

        if form_action == "import_visibility_template":
            import_user_id = request.form.get("user_id", type=int)
            import_user = db.session.get(User, import_user_id)
            if not import_user:
                flash("İçe aktarma için kullanıcı seçiniz.", "warning")
                return redirect(url_for("main.settings_page"))
            raw_payload = (request.form.get("import_template_json") or "").strip()
            upload = request.files.get("import_template_file")
            if not raw_payload and upload and getattr(upload, "filename", ""):
                raw_payload = upload.read().decode("utf-8", errors="ignore").strip()
            if not raw_payload:
                flash("İçe aktarmak için JSON metni veya dosyası seçiniz.", "warning")
                return redirect(url_for("main.settings_page", user_id=import_user.id))
            try:
                payload = json.loads(raw_payload)
                visible_keys = _extract_visible_keys_from_template_payload(payload, flat_menu_items)
                if not visible_keys and not isinstance(payload.get("effective_rule_map"), dict):
                    raise ValueError("Şablonda görünür menü anahtarları bulunamadı.")
                result = save_user_menu_overrides(import_user, flat_menu_items, visible_keys, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"Yetki şablonu içe aktarıldı. Aktif override: {result['override_count']}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Yetki şablonu içe aktarılırken hata oluştu: {exc}", "danger")
            return redirect(url_for("main.settings_page", user_id=import_user.id))

        if form_action == "save_named_archive":
            selected_user_id = request.form.get("user_id", type=int)
            selected_user = db.session.get(User, selected_user_id)
            if not selected_user:
                flash("Şablon arşivi kaydetmek için kullanıcı seçiniz.", "warning")
                return redirect(url_for("main.settings_page"))
            archive_name = (request.form.get("archive_name") or "").strip()
            archive_scope = (request.form.get("archive_scope") or "general").strip()
            archive_description = (request.form.get("archive_description") or "").strip()
            archive_role_target = (request.form.get("archive_role_target") or getattr(selected_user, "role", "") or "").strip()
            archive_birim_target = (request.form.get("archive_birim_target") or getattr(selected_user, "birim", "") or "").strip()
            visible_keys = _collect_form_visible_keys(request.form, flat_menu_items)
            try:
                result = _save_settings_template_archive(
                    archive_name,
                    archive_scope,
                    visible_keys,
                    flat_menu_items,
                    description=archive_description,
                    target_role=archive_role_target,
                    target_birim=archive_birim_target,
                    source_user=selected_user,
                    updated_by_user_id=getattr(current_user, "id", None),
                )
                db.session.commit()
                flash(f"Şablon arşivi kaydedildi: {result['archive_name']} · Açık sekme: {result['visible_count']}", "success")
                archive_redirect_key = result["setting_key"]
            except Exception as exc:
                db.session.rollback()
                archive_redirect_key = (request.form.get('archive_key') or "").strip()
                flash(f"Şablon arşivi kaydedilirken hata oluştu: {exc}", "danger")
            return redirect(url_for("main.settings_page", user_id=selected_user.id, archive_key=archive_redirect_key))

        if form_action == "apply_named_archive":
            selected_user_id = request.form.get("user_id", type=int)
            selected_user = db.session.get(User, selected_user_id)
            archive_key = (request.form.get("archive_key") or "").strip()
            archive = _get_settings_template_archive(archive_key, flat_menu_items)
            if not archive:
                flash("Uygulanacak arşiv seçilemedi.", "warning")
                return redirect(url_for("main.settings_page", user_id=selected_user_id) if selected_user_id else url_for("main.settings_page"))
            apply_mode = (request.form.get("archive_apply_mode") or "user_override").strip()
            target_role = (request.form.get("archive_apply_role") or archive.get("target_role") or getattr(selected_user, "role", "") or "").strip()
            target_birim = (request.form.get("archive_apply_birim") or archive.get("target_birim") or getattr(selected_user, "birim", "") or "").strip()
            visible_keys = set(archive.get("visible_keys") or [])
            try:
                if apply_mode == "role_profile":
                    if not target_role:
                        raise ValueError("Rol profiline uygulamak için rol seçiniz.")
                    changed = save_role_menu_defaults(target_role, all_menu_keys, visible_keys, updated_by_user_id=getattr(current_user, "id", None))
                    flash(f"Arşiv rol profiline uygulandı: {target_role} · İşlenen satır: {changed}", "success")
                elif apply_mode == "unit_profile":
                    if not target_birim:
                        raise ValueError("Birim profiline uygulamak için birim seçiniz.")
                    changed = save_unit_menu_profile(target_birim, all_menu_keys, visible_keys, updated_by_user_id=getattr(current_user, "id", None))
                    flash(f"Arşiv birim profiline uygulandı: {target_birim} · İşlenen satır: {changed}", "success")
                else:
                    if not selected_user:
                        raise ValueError("Personel bazlı rol matrisi için önce personel seçiniz.")
                    result = save_user_menu_overrides(selected_user, flat_menu_items, visible_keys, updated_by_user_id=getattr(current_user, "id", None))
                    flash(f"Arşiv seçili personele uygulandı. Kişiye özel sekme kaydı: {result['override_count']}", "success")
                db.session.commit()
            except Exception as exc:
                db.session.rollback()
                flash(f"Arşiv uygulanırken hata oluştu: {exc}", "danger")
            return redirect(url_for("main.settings_page", user_id=selected_user.id if selected_user else None, archive_key=archive_key) if selected_user else url_for("main.settings_page", archive_key=archive_key))

        if form_action == "delete_named_archive":
            selected_user_id = request.form.get("user_id", type=int)
            archive_key = (request.form.get("archive_key") or "").strip()
            try:
                result = _delete_settings_template_archive(archive_key)
                db.session.commit()
                flash(f"Şablon arşivi silindi: {result['archive_name']}", "success")
            except Exception as exc:
                db.session.rollback()
                flash(f"Şablon arşivi silinirken hata oluştu: {exc}", "danger")
            return redirect(url_for("main.settings_page", user_id=selected_user_id) if selected_user_id else url_for("main.settings_page"))

        selected_user_id = request.form.get("user_id", type=int)
        selected_user = db.session.get(User, selected_user_id)
        if not selected_user:
            flash("Personel seçiniz.", "warning")
            return redirect(url_for("main.settings_page"))

        visible_keys = _collect_form_visible_keys(request.form, flat_menu_items)
        keep_user_id = selected_user.id
        try:
            if form_action == "save_role_profile":
                target_role = (request.form.get("profile_role_target") or selected_user.role or "").strip()
                changed = save_role_menu_defaults(target_role, all_menu_keys, visible_keys, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"{target_role or '-'} rol profili güncellendi. İşlenen satır: {changed}", "success")
            elif form_action == "save_unit_profile":
                target_unit = (request.form.get("profile_unit_target") or selected_user.birim or "").strip()
                changed = save_unit_menu_profile(target_unit, all_menu_keys, visible_keys, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"{target_unit or '-'} birim profili güncellendi. İşlenen satır: {changed}", "success")
            elif form_action == "reset_user_overrides":
                deleted = clear_user_menu_overrides(selected_user.id, updated_by_user_id=getattr(current_user, "id", None))
                flash(f"{selected_user.ad} {selected_user.soyad} için personel bazlı rol matrisi temizlendi. Kaldırılan sekme kaydı: {deleted}", "success")
            else:
                result = save_user_menu_overrides(selected_user, flat_menu_items, visible_keys, updated_by_user_id=getattr(current_user, "id", None))
                flash(
                    f"{selected_user.ad} {selected_user.soyad} için kişi bazlı sekme ayarları kaydedildi. Bu personelin menüsü artık ekrandaki işaretlere göre çalışır. Kaydedilen sekme: {result['override_count']}",
                    "success",
                )
            return redirect(url_for("main.settings_page", user_id=keep_user_id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Ayarlar kaydedilirken hata oluştu: {exc}", "danger")
            return redirect(url_for("main.settings_page", user_id=keep_user_id))

    settings_presets = _build_settings_presets(grouped_menu_definitions, get_role_default_menu_keys(selected_user.role) if selected_user else set())
    selected_profile_resolution = None
    if selected_user:
        selected_profile_resolution = build_effective_user_menu_context(selected_user, flat_menu_items)
        selected_rule_map = dict(selected_profile_resolution["effective_rule_map"])
        defaults = set(selected_profile_resolution["role_default_keys"])
        settings_matrix = _build_settings_matrix(grouped_menu_definitions, selected_rule_map, defaults, selected_user=selected_user, users=users)
    else:
        defaults = set()


    settings_section_links = [
        {"id": "system-foundation", "label": "Genel Sistem", "icon": "fa-solid fa-building-shield"},
        {"id": "system-group-about", "label": "Hakkımızda", "icon": "fa-solid fa-circle-info"},
        {"id": "system-group-kunye", "label": "Sistem Künyesi", "icon": "fa-solid fa-address-card"},
        {"id": "module-foundation", "label": "Modül Ayarları", "icon": "fa-solid fa-sliders"},
        {"id": "general-role-policy", "label": "Genel Rol Matrisi", "icon": "fa-solid fa-layer-group"},
        {"id": "personnel-role-policy", "label": "Personel Rol Matrisi", "icon": "fa-solid fa-users-gear"},
        {"id": "performance-role-policy", "label": "Performans Rol Matrisi", "icon": "fa-solid fa-chart-line"},
        {"id": "communication-role-policy", "label": "İletişim Rol Matrisi", "icon": "fa-solid fa-comments"},
        {"id": "portal-role-policy", "label": "Portal Rol Matrisi", "icon": "fa-solid fa-stream"},
        {"id": "ai-role-policy", "label": "AI Rol Matrisi", "icon": "fa-solid fa-brain"},
        {"id": "settings-security-role-policy", "label": "Ayarlar Rol Matrisi", "icon": "fa-solid fa-shield-halved"},
        {"id": "role-foundation", "label": "Rol Varsayılanları", "icon": "fa-solid fa-user-shield"},
        {"id": "unit-foundation", "label": "Birim Profilleri", "icon": "fa-solid fa-sitemap"},
        {"id": "settings-diagnostics", "label": "Tanılama", "icon": "fa-solid fa-stethoscope"},
        {"id": "settings-history", "label": "Ayar Geçmişi", "icon": "fa-solid fa-clock-rotate-left"},
    ]
    if selected_user:
        settings_section_links.append({"id": "user-overrides", "label": "Personel Bazlı Rol Matrisi", "icon": "fa-solid fa-user-gear"})
        settings_section_links.append({"id": "settings-archives", "label": "Şablon Arşivi", "icon": "fa-solid fa-box-archive"})

    profile_context = build_settings_profile_context(selected_user, flat_menu_items) if phase1_seed_summary.get("ok") else {
        "unit_profiles_snapshot": [],
        "unit_profile_total": 0,
        "selected_user_resolution": None,
    }
    settings_ui_panel_context = build_settings_ui_diagnostics_panel(
        foundation_context=foundation_context,
        profile_context=profile_context,
        selected_user=selected_user,
    )
    user_diff_context = _build_user_visibility_diff(selected_user, compare_user, flat_menu_items) if selected_user and compare_user else None
    settings_archives = _list_settings_template_archives(flat_menu_items) if phase1_seed_summary.get("ok") else []
    selected_archive_key = (request.values.get("archive_key") or "").strip()

    return safe_render(
        "settings.html",
        "<h3>Ayarlar</h3>",
        users=users,
        grouped_menu_definitions=grouped_menu_definitions,
        selected_user=selected_user,
        selected_rule_map=selected_rule_map,
        settings_matrix=settings_matrix,
        role_default_keys=sorted(defaults),
        settings_presets=settings_presets,
        bulk_settings_profiles=bulk_settings_profiles,
        bulk_target_users=bulk_target_users,
        bulk_result_summary=bulk_result_summary,
        role_options=role_options,
        birim_options=birim_options,
        foundation_context=foundation_context,
        communication_role_matrix=communication_role_matrix,
        assistant_role_matrix=assistant_role_matrix,
        settings_role_matrix_groups=settings_role_matrix_groups,
        phase1_seed_summary=phase1_seed_summary,
        profile_context=profile_context,
        settings_section_links=settings_section_links,
        selected_profile_resolution=selected_profile_resolution,
        compare_user=compare_user,
        user_diff_context=user_diff_context,
        settings_archives=settings_archives,
        selected_archive_key=selected_archive_key,
        settings_ui_panel_context=settings_ui_panel_context,
    )

def account():
    return safe_render(
        "account.html",
        "<h3>Hesabım</h3>",
        user=current_user,
        security_questions=SECURITY_QUESTION_CHOICES,
    )




__all__ = [name for name in globals() if not name.startswith("__")]

# BYS360_ASSISTANT_ROLE_MATRIX_V12_FIX_BEGIN
# V12 FIX:
# Son güncellemeden sonra /settings sayfası
# NameError: _build_assistant_role_matrix is not defined
# hatasına düşüyordu. Bu blok, Ayarlar helper dosyasına gereken fonksiyonları
# yerel ve güvenli şekilde ekler. Login/auth/CAPTCHA/config/DB bağlantısına dokunmaz.

ASSISTANT_POLICY_ROLE_OPTIONS = [
    ("admin", "Admin"),
    ("baskan", "Başkan"),
    ("baskan_yardimcisi", "Başkan Yardımcısı"),
    ("grup_baskani", "Grup Başkanı"),
    ("mali_musavir", "Mali Müşavir"),
    ("koordinator", "Koordinatör"),
    ("birim_sorumlusu", "Birim Sorumlusu"),
    ("personel", "Personel"),
    ("kullanici", "Rolsüz/Kullanıcı"),
]

ASSISTANT_DEFAULT_VISIBLE_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
}

ASSISTANT_ROLE_MATRIX_ROWS = [
    {
        "key": "assistant_module",
        "label": "Sanal Asistan Modülü",
        "icon": "fa-solid fa-sparkles",
        "description": "Ana anahtar. Kapalı rolde asistan menüsü, asistan penceresi ve içindeki tüm kısa yollar görünmez.",
    },
]


def _assistant_v12_normalize(value):
    raw = "" if value is None else str(value)
    return raw.strip().lower().replace("ı", "i").replace("İ", "i").replace(" ", "_").replace("-", "_")


def _assistant_v12_get_current_settings():
    try:
        from app.services.assistant_settings_service import get_assistant_settings
        data = get_assistant_settings() or {}
        if isinstance(data, dict):
            return data
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_settings_helpers.py)")
    return {}


def _assistant_visible_roles_from_settings():
    data = _assistant_v12_get_current_settings()
    raw = str(data.get("visible_roles") or "").strip()
    if not raw:
        raw = ",".join(sorted(ASSISTANT_DEFAULT_VISIBLE_ROLES))

    roles = {
        _assistant_v12_normalize(item)
        for item in raw.replace(";", ",").replace("\n", ",").split(",")
        if str(item or "").strip()
    }
    return {role for role in roles if role and role != "__none__"}


def _build_assistant_role_matrix():
    visible_roles = _assistant_visible_roles_from_settings()

    role_rows = []
    item_rows = []

    for role_key, role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
        role_rows.append({
            "role_key": role_key,
            "role_label": role_label,
            "visible_count": 1 if role_key in visible_roles else 0,
            "recommended_count": 1 if role_key in ASSISTANT_DEFAULT_VISIBLE_ROLES else 0,
        })

    for item in ASSISTANT_ROLE_MATRIX_ROWS:
        states = []
        visible_count = 0
        recommended_roles = []

        for role_key, role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
            is_visible = role_key in visible_roles
            is_recommended = role_key in ASSISTANT_DEFAULT_VISIBLE_ROLES

            if is_visible:
                visible_count += 1
            if is_recommended:
                recommended_roles.append(role_label)

            states.append({
                "role_key": role_key,
                "role_label": role_label,
                "is_visible": is_visible,
                "is_recommended": is_recommended,
            })

        item_rows.append({
            "key": item["key"],
            "label": item["label"],
            "icon": item["icon"],
            "description": item["description"],
            "visible_count": visible_count,
            "states": states,
            "recommended_roles": recommended_roles,
        })

    return {
        "roles": role_rows,
        "rows": item_rows,
        "items": item_rows,
        "item_count": len(item_rows),
        "visible_roles": sorted(visible_roles),
    }


def _assistant_v12_set_if_exists(obj, attr, value):
    try:
        if hasattr(obj, attr):
            setattr(obj, attr, value)
            return True
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/main_handlers/account_settings_helpers.py:667")
        return False
    return False


def _assistant_v12_find_module_setting(module_key, setting_key):
    try:
        from app.models import ModuleSetting
        return ModuleSetting.query.filter_by(module_key=module_key, setting_key=setting_key).first()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/main_handlers/account_settings_helpers.py:676")
        return None


def _assistant_v12_create_module_setting():
    try:
        from app.models import ModuleSetting
        return ModuleSetting()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/main_handlers/account_settings_helpers.py:684")
        return None


def _upsert_assistant_module_setting(setting_key, label, value_text, value_type="string", description="", updated_by_user_id=None):
    try:
        from app.extensions import db
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/main_handlers/account_settings_helpers.py:691")
        return None

    row = _assistant_v12_find_module_setting("assistant", setting_key)
    if row is None:
        row = _assistant_v12_create_module_setting()
        if row is None:
            return None
        db.session.add(row)

    _assistant_v12_set_if_exists(row, "module_key", "assistant")
    _assistant_v12_set_if_exists(row, "setting_key", setting_key)
    _assistant_v12_set_if_exists(row, "label", label)
    _assistant_v12_set_if_exists(row, "name", label)
    _assistant_v12_set_if_exists(row, "value_text", str(value_text))
    _assistant_v12_set_if_exists(row, "value", str(value_text))
    _assistant_v12_set_if_exists(row, "setting_value", str(value_text))
    _assistant_v12_set_if_exists(row, "value_type", value_type)
    _assistant_v12_set_if_exists(row, "description", description)
    _assistant_v12_set_if_exists(row, "is_active", True)
    _assistant_v12_set_if_exists(row, "updated_by_user_id", updated_by_user_id)
    return row


def save_assistant_role_matrix_from_form(form, *, updated_by_user_id=None):
    try:
        from app.extensions import db
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/main_handlers/account_settings_helpers.py:718")
        return 0

    selected_roles = []
    for role_key, _role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
        field_name = f"assistant_role_policy__{role_key}__assistant_module"
        if form.get(field_name):
            selected_roles.append(role_key)

    visible_roles_value = ",".join(selected_roles) if selected_roles else "__none__"

    _upsert_assistant_module_setting(
        "enabled",
        "Sanal Asistan Aktif",
        "true",
        "bool",
        "Sanal Asistan genel aktiflik bayrağı. Rol bazlı görünürlük visible_roles ile yönetilir.",
        updated_by_user_id=updated_by_user_id,
    )
    _upsert_assistant_module_setting(
        "visible_roles",
        "Sanal Asistan Görünür Rolleri",
        visible_roles_value,
        "string",
        "Sanal Asistan ana menüsü, penceresi ve tüm kısa yolları hangi rollerde görünecek.",
        updated_by_user_id=updated_by_user_id,
    )
    db.session.commit()
    return len(selected_roles)


def reset_assistant_role_matrix_defaults(*, updated_by_user_id=None):
    try:
        from app.extensions import db
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/main_handlers/account_settings_helpers.py:752")
        return 0

    visible_roles_value = ",".join(sorted(ASSISTANT_DEFAULT_VISIBLE_ROLES))

    _upsert_assistant_module_setting(
        "enabled",
        "Sanal Asistan Aktif",
        "true",
        "bool",
        "Sanal Asistan genel aktiflik bayrağı.",
        updated_by_user_id=updated_by_user_id,
    )
    _upsert_assistant_module_setting(
        "visible_roles",
        "Sanal Asistan Görünür Rolleri",
        visible_roles_value,
        "string",
        "Önerilen rol politikası: yönetici rolleri açık, personel/kullanıcı kapalı.",
        updated_by_user_id=updated_by_user_id,
    )
    db.session.commit()
    return len(ASSISTANT_DEFAULT_VISIBLE_ROLES)
# BYS360_ASSISTANT_ROLE_MATRIX_V12_FIX_END
