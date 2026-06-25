# BYS360 Phase4J Performance Hierarchy Bulk Assign V8 Analysis
- Generated at: 2026-06-25T14:20:53
- Function: performance_hierarchy_bulk_assign
- Lines: 354-400 (47 lines)
- Return count: 2

## Decorators
- `main_bp.route('/performance/hierarchy-settings/bulk-assign', methods=['POST'])`
- `login_required`
- `admin_required`

## Internal function refs
- none

## External refs
- PerformancePeriod
- User
- admin_required
- current_user
- db
- flash
- generate_assignments_for_active_period
- login_required
- main_bp
- redirect
- request
- url_for

## Call names
- all
- commit
- desc
- filter
- filter_by
- first
- flash
- generate_assignments_for_active_period
- get
- order_by
- redirect
- route
- strip
- url_for

## Body items
- Assign 355-355: `ust_birim = (request.form.get('ust_birim') or '').strip()`
- Assign 356-356: `birim = (request.form.get('birim') or '').strip()`
- Assign 357-357: `role = (request.form.get('role') or '').strip()`
- Assign 359-359: `yonetici_sicil = (request.form.get('bulk_yonetici_sicil') or '').strip() or None`
- Assign 360-360: `ikinci_yonetici_sicil = (request.form.get('bulk_ikinci_yonetici_sicil') or '').strip() or None`
- Assign 361-361: `ucuncu_yonetici_sicil = (request.form.get('bulk_ucuncu_yonetici_sicil') or '').strip() or None`
- Assign 362-362: `level_3_enabled = request.form.get('bulk_level_3_enabled') == 'on'`
- Assign 364-364: `query = User.query.filter(User.role != 'admin')`
- If 365-366: `if ust_birim:
    query = query.filter(User.ust_birim == ust_birim)`
- If 367-368: `if birim:
    query = query.filter(User.birim == birim)`
- If 369-370: `if role:
    query = query.filter(User.role == role)`
- Assign 372-372: `users = query.all()`
- If 373-375: `if not users:
    flash('Toplu atama için uygun personel bulunamadı.', 'warning')
    return redirect(url_for('main.performance_hierarchy_settings'))`
- Assign 377-377: `updated_count = 0`
- For 378-386: `for user_obj in users:
    user_obj.yonetici_sicil = yonetici_sicil
    user_obj.ikinci_yonetici_sicil = ikinci_yonetici_sicil
    user_obj.ucuncu_yonetici_sicil = ucuncu_yonetici_sicil if level_3_enabled else None
    updated_count += 1`
- Expr 388-388: `db.session.commit()`
- Assign 390-390: `active_period = PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()`
- Assign 391-391: `assignment_result = None`
- If 392-393: `if active_period:
    assignment_result = generate_assignments_for_active_period(period_id=active_period.id, actor_user_id=current_user.id)`
- Expr 395-395: `flash(f'Toplu hiyerarşi ataması tamamlandı. Güncellenen personel: {updated_count}', 'success')`
- If 396-399: `if assignment_result and assignment_result.get('ok'):
    flash('Aktif dönem görevleri toplu hiyerarşi ataması sonrası yeniden senkronlandı.', 'success')
elif assignment_result and (not assignment_result.get('ok')):
    flash(assignment_result.get('message', 'Aktif dönem görevleri yeniden senkronlanamadı.'), 'warning')`
- Return 400-400: `return redirect(url_for('main.performance_hierarchy_settings'))`

## Recommendation
- performance_hierarchy_bulk_assign kalan en buyuk route adaylarindan biridir.
- internal_function_refs bos ise wrapper/service bolmesi guvenli gorunur.
- Bu route performans hiyerarsisi ile ilgili oldugu icin app/admin/ops_performance_services.py icine alinmasi daha temiz olur.
- Tasima sonrasi compileall, import smoke, duplicate kontrol ve architecture testleri calistirilmelidir.
