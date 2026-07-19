from __future__ import annotations

# Bu dosya app.services.ai.dashboard_panels dış public API'sini bozmadan ayrıştırılmıştır.


from app.services.ai.dashboard_panel_common import (
    Any,
    Iterable,
    _get,
    _to_int,
    _tone_from_counts,
    _badge_from_tone,
    _has_real_hierarchy_warning,
    _is_hierarchy_missing_exempt,
    _has_first_manager_binding,
    _has_level_3_binding,
)

def build_personnel_profile_chain_ai_panel(profile: Any | None) -> dict[str, Any]:
    profile = profile or {}
    manager_cards = [_get(profile, key) for key in ('manager_1', 'manager_2', 'manager_3')]
    manager_count = sum(1 for item in manager_cards if item)
    missing_count = 3 - manager_count
    hierarchy_state = str(_get(profile, 'hierarchy_state') or 'Belirsiz')
    is_active = bool(_get(profile, 'is_active'))
    org_path = str(_get(profile, 'org_path') or '-')
    path_depth = len([part for part in org_path.split('>') if str(part).strip()]) if org_path != '-' else 0
    seen_sicils: dict[str, int] = {}
    for mgr in manager_cards:
        sicil = str(_get(mgr, 'sicil_no') or '').strip()
        if sicil:
            seen_sicils[sicil] = seen_sicils.get(sicil, 0) + 1
    duplicate_managers = sum(1 for count in seen_sicils.values() if count > 1)
    critical = 1 if not _get(profile, 'manager_1') else 0
    warning = (1 if not _get(profile, 'manager_2') else 0) + duplicate_managers
    tone = _tone_from_counts(critical=critical, warning=warning)

    if critical:
        headline = 'Zincirin ilk halkasında eksik tanım var'
        summary = 'AI özeti, bu profil için en az 1. amir kaydının tamamlanması gerektiğini; aksi halde görev ve değerlendirme akışında boşluk oluşacağını söylüyor.'
    elif warning:
        headline = 'Profil çalışır durumda ama zincirde açıklıklar var'
        summary = 'AI özeti, temel amir akışının çözüldüğünü ancak üst seviye ya da opsiyonel amir bilgilerinin gözden geçirilmesinin veri kalitesini artıracağını gösteriyor.'
    else:
        headline = 'Profilin hiyerarşi görünümü dengeli'
        summary = 'AI özeti, personel profilinde rol, birim ve amir zincirinin birlikte okunabildiğini; profilin görev üretimi için daha güvenli bir görünüme yaklaştığını gösteriyor.'

    bullets = [
        f"Hiyerarşi durumu: {hierarchy_state}.",
        f"Tanımlı amir sayısı {manager_count}; eksik halka sayısı {missing_count if missing_count > 0 else 0}.",
        f"Organizasyon yolu: {org_path}.",
        f"Hesap durumu: {'Aktif' if is_active else 'Pasif'} kullanıcı.",
    ]

    spotlight = []
    for idx, key in enumerate(('manager_1', 'manager_2', 'manager_3'), start=1):
        mgr = _get(profile, key)
        if not mgr:
            continue
        mgr_name = _get(mgr, 'full_name') or f"{_get(mgr, 'ad', '')} {_get(mgr, 'soyad', '')}".strip() or '-'
        spotlight.append({'label': f'{idx}. Amir', 'value': str(mgr_name)})

    recommendations = []
    if not _get(profile, 'manager_1'):
        recommendations.append('Önce 1. amir alanını tamamlayın; görev üretimi ve performans akışı burada kırılır.')
    if _get(profile, 'manager_1') and not _get(profile, 'manager_2'):
        recommendations.append('2. amir eksikse profil yine açılır; ancak rapor ve kıyas tarafında zincir kalitesi düşer.')
    if duplicate_managers:
        recommendations.append('Aynı sicilin birden fazla amir halkasında görünmesi olası zincir çakışmasına işaret eder; kişi bazlı atamayı kontrol edin.')
    if path_depth <= 1 and org_path != '-':
        recommendations.append('Organizasyon yolu çok kısa görünüyor; üst birim bağı ya da organizasyon birimi ataması ayrıca kontrol edilmeli.')
    if not recommendations:
        recommendations.append('Zincir görünümü dengeli; bir sonraki adım profil ile organizasyon birimi atamasının aynı terminolojiyi koruduğunu doğrulamaktır.')

    risk_rows = []
    if not _get(profile, 'manager_1'):
        risk_rows.append({'label': '1. amir', 'value': 'Eksik', 'tone': 'critical'})
    if not _get(profile, 'manager_2'):
        risk_rows.append({'label': '2. amir', 'value': 'Eksik', 'tone': 'watch'})
    if not _get(profile, 'manager_3'):
        risk_rows.append({'label': '3. amir', 'value': 'Boş / opsiyonel', 'tone': 'calm'})
    if duplicate_managers:
        risk_rows.append({'label': 'Aynı amir tekrarı', 'value': duplicate_managers, 'tone': 'watch'})

    actions = [
        {'label': 'Tanımlı amir', 'value': manager_count, 'tone': 'calm' if manager_count >= 2 else 'watch'},
        {'label': 'Eksik halka', 'value': max(missing_count, 0), 'tone': 'critical' if critical else ('watch' if warning else 'calm')},
        {'label': 'Yol derinliği', 'value': path_depth, 'tone': 'watch' if path_depth <= 1 else 'calm'},
        {'label': 'Tekrarlı amir', 'value': duplicate_managers, 'tone': 'watch' if duplicate_managers else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight[:3],
        'recommendations': recommendations[:4],
        'risk_rows': risk_rows[:4],
    }


def build_admin_user_form_ai_panel(*, form_data: dict[str, Any] | None = None, manager_candidates: Iterable[Any] | None = None, mode: str = 'create', user_obj: Any | None = None) -> dict[str, Any]:
    form_data = form_data or {}
    role = str(form_data.get('role') or _get(user_obj, 'role') or 'personel').strip()
    birim = str(form_data.get('birim') or _get(user_obj, 'birim') or '').strip()
    ust_birim = str(form_data.get('ust_birim') or _get(user_obj, 'ust_birim') or '').strip()
    unvan = str(form_data.get('unvan') or _get(user_obj, 'unvan') or '').strip()
    sicil_no = str(form_data.get('sicil_no') or _get(user_obj, 'sicil_no') or '').strip()
    managers = [
        str(form_data.get('yonetici_sicil') or _get(user_obj, 'yonetici_sicil') or '').strip(),
        str(form_data.get('ikinci_yonetici_sicil') or _get(user_obj, 'ikinci_yonetici_sicil') or '').strip(),
        str(form_data.get('ucuncu_yonetici_sicil') or _get(user_obj, 'ucuncu_yonetici_sicil') or '').strip(),
    ]
    selected_count = sum(1 for item in managers if item)
    duplicate_count = len([item for item in set(managers) if item and managers.count(item) > 1])
    self_ref = 1 if sicil_no and sicil_no in [m for m in managers if m] else 0
    required_missing = sum(1 for value in [unvan, birim, ust_birim] if not value)
    manager_pool = len(list(manager_candidates or []))
    tone = _tone_from_counts(critical=required_missing + self_ref + duplicate_count, warning=max(0, 1 if selected_count == 0 else 0))

    if required_missing or self_ref or duplicate_count:
        headline = 'Form gönderilmeden önce zorunlu eşleşmeler gözden geçirilmeli'
        summary = 'AI özeti, rol, birim ve amir alanlarında eksik ya da çakışan seçimler olduğunda kayıt sonrasında zincir ve görev üretimi tarafının etkilenebileceğini hatırlatıyor.'
    elif selected_count == 0:
        headline = 'Kayıt açılabilir; amir alanları tamamlanırsa daha güçlü olur'
        summary = 'AI özeti, temel alanların dolu göründüğünü ancak amir alanları boş bırakıldığında hiyerarşi tarafında ek düzenleme ihtiyacı doğabileceğini gösteriyor.'
    else:
        headline = 'Form görünümü kurumsal eşleşme için dengeli'
        summary = 'AI özeti, rol, unvan, birim ve amir alanlarının birlikte okunabildiğini; kayıt sonrasında organizasyon ve performans akışlarının daha az müdahale isteyeceğini gösteriyor.'

    bullets = [
        f"Mod: {'Yeni kayıt' if mode == 'create' else 'Düzenleme'}; seçili rol: {role or '-'}.",
        f"Birim: {birim or '-'} | Üst birim: {ust_birim or '-'}.",
        f"Seçili amir sayısı {selected_count}; yönetici havuzu {manager_pool} kayıt içeriyor.",
        f"Zorunlu form riski {required_missing + self_ref + duplicate_count} başlıkta toplanıyor.",
    ]

    spotlight = []
    if unvan:
        spotlight.append({'label': 'Unvan', 'value': unvan})
    if birim:
        spotlight.append({'label': 'Birim', 'value': birim})
    if ust_birim:
        spotlight.append({'label': 'Üst birim', 'value': ust_birim})

    actions = [
        {'label': 'Eksik alan', 'value': required_missing, 'tone': 'critical' if required_missing else 'calm'},
        {'label': 'Seçili amir', 'value': selected_count, 'tone': 'watch' if selected_count == 0 else 'calm'},
        {'label': 'Mükerrer amir', 'value': duplicate_count, 'tone': 'critical' if duplicate_count else 'calm'},
        {'label': 'Kendine atama', 'value': self_ref, 'tone': 'critical' if self_ref else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight[:3],
    }


def build_excel_fix_preview_ai_panel(*, errors: Iterable[str] | None = None, normalized_headers: Iterable[str] | None = None, autofix_enabled: bool = False, applied_fixes: dict[str, Any] | None = None) -> dict[str, Any]:
    errors = [str(item) for item in (errors or []) if str(item).strip()]
    headers = [str(item).strip() for item in (normalized_headers or []) if str(item).strip()]
    applied_fixes = applied_fixes or {}
    missing_required = sum(1 for item in errors if 'zorunlu alan eksik' in item.lower())
    unit_errors = sum(1 for item in errors if 'birim' in item.lower())
    manager_errors = sum(1 for item in errors if 'amir' in item.lower() or 'yonetici' in item.lower() or 'yönetici' in item.lower())
    row_count = len(errors)
    tone = _tone_from_counts(critical=missing_required + unit_errors, warning=manager_errors + row_count)

    if errors:
        headline = 'İçe aktarma sonrası düzeltme ön izlemi hazır'
        summary = 'AI özeti, hata satırlarını sınıflandırarak önce başlık uyumu ve zorunlu alan eksiklerinin kapatılmasını; ardından birim ve amir zincirinin temizlenmesini öneriyor.'
    elif headers:
        headline = 'Başlık seti okunabildi; içe aktarma ön izlemi dengeli'
        summary = 'AI özeti, mevcut başlıkların sisteme yakın göründüğünü; yükleme öncesi birkaç örnek satır kontrolüyle daha güvenli sonuç alınabileceğini söylüyor.'
    else:
        headline = 'Excel şablonu yüklenmeye hazır'
        summary = 'AI özeti, önce başlık uyumunun kontrol edilmesini; özellikle sicil, e-posta, birim ve amir sütunlarının temiz tutulmasını öneriyor.'

    suggestions = []
    if missing_required:
        suggestions.append(f'Öncelik 1: {missing_required} satırda zorunlu alan eksikliği var; sicil, ad, soyad, e-posta, unvan ve birim alanlarını tamamlayın.')
    if unit_errors:
        suggestions.append(f'Öncelik 2: {unit_errors} satırda birim/üst birim eşleşmesi sorunlu; aynı yazım standardını kullanın.')
    if manager_errors:
        suggestions.append(f'Öncelik 3: {manager_errors} satırda amir zinciri alanları kontrol edilmeli; sicil bazlı değerleri sadeleştirin.')
    if not suggestions:
        suggestions.append('Şablon yüklenmeden önce ilk 5 satırı örnek kontrol ederek sicil, birim ve amir sütunlarını doğrulayın.')

    alias_count = _to_int(applied_fixes.get('header_alias_count'))
    whitespace_count = _to_int(applied_fixes.get('whitespace_trim_count'))
    inferred_role_count = _to_int(applied_fixes.get('inferred_role_count'))
    default_active_count = _to_int(applied_fixes.get('default_active_count'))
    autofix_preview = []
    if alias_count:
        autofix_preview.append({'label': 'Başlık eşleştirme', 'value': alias_count, 'reason': 'Eş anlamlı başlıklar sistem başlıklarına dönüştürüldü.'})
    if whitespace_count:
        autofix_preview.append({'label': 'Metin temizliği', 'value': whitespace_count, 'reason': 'Birden fazla boşluk ve kenar boşlukları sadeleştirildi.'})
    if inferred_role_count:
        autofix_preview.append({'label': 'Rol çıkarımı', 'value': inferred_role_count, 'reason': 'Boş rol alanlarında unvan/birim üzerinden rol önerisi uygulandı.'})
    if default_active_count:
        autofix_preview.append({'label': 'Varsayılan aktif', 'value': default_active_count, 'reason': 'Boş aktiflik alanları sistem varsayılanı ile aktif kabul edildi.'})

    actions = [
        {'label': 'Hata satırı', 'value': row_count, 'tone': 'critical' if row_count else 'calm'},
        {'label': 'Eksik alan', 'value': missing_required, 'tone': 'critical' if missing_required else 'calm'},
        {'label': 'Birim sorunu', 'value': unit_errors, 'tone': 'watch' if unit_errors else 'calm'},
        {'label': 'Amir sorunu', 'value': manager_errors, 'tone': 'watch' if manager_errors else 'calm'},
    ]
    spotlight = []
    if headers:
        spotlight.append({'label': 'İlk başlıklar', 'value': ', '.join(headers[:6])})
    if autofix_enabled:
        spotlight.append({'label': 'AI otomatik düzeltme', 'value': 'Açık'})
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': suggestions[:4],
        'actions': actions,
        'spotlight': spotlight[:2],
        'autofix_enabled': autofix_enabled,
        'autofix_preview': autofix_preview[:4],
    }


def build_personnel_list_ai_panel(stats: Any | None = None, user_rows: Iterable[Any] | None = None) -> dict[str, Any]:
    stats = stats or {}
    rows = list(user_rows or [])
    total_count = _to_int(_get(stats, "total_count"))
    filtered_count = _to_int(_get(stats, "filtered_count"))
    active_count = _to_int(_get(stats, "active_count"))
    passive_count = _to_int(_get(stats, "passive_count"))
    unit_count = _to_int(_get(stats, "unit_count"))

    missing_email = 0
    missing_sicil = 0
    missing_unit = 0
    role_gaps = 0
    passive_visible = 0
    seen_sicil: dict[str, int] = {}
    for row in rows:
        email = (_get(row, 'email', '') or '').strip()
        sicil = (_get(row, 'sicil_no', '') or '').strip()
        unit = (_get(row, 'birim', '') or '').strip()
        role_text = (_get(row, 'role_text', '') or '').strip()
        if not email or email == '-':
            missing_email += 1
        if not sicil or sicil == '-':
            missing_sicil += 1
        if not unit or unit == '-':
            missing_unit += 1
        if not role_text or role_text == '-':
            role_gaps += 1
        if not bool(_get(row, 'is_active', False)):
            passive_visible += 1
        if sicil and sicil != '-':
            seen_sicil[sicil] = seen_sicil.get(sicil, 0) + 1
    duplicate_sicil = sum(1 for count in seen_sicil.values() if count > 1)

    critical = missing_sicil + missing_unit + duplicate_sicil
    warning = missing_email + passive_visible + role_gaps
    tone = _tone_from_counts(critical=critical, warning=warning)

    if critical > 0:
        headline = 'Personel havuzunda veri bütünlüğü önce çekirdek alanlardan toparlanmalı'
        summary = 'AI özeti, filtrelenen görünümde önce sicil, birim ve mükerrer kayıt risklerinin kapatılmasını öneriyor.'
    elif warning > 0:
        headline = 'Personel görünümü çalışıyor; bakım ihtiyacı daha çok iletişim ve görünürlükte'
        summary = 'AI özeti, ana omurganın ayakta olduğunu; fakat e-posta, pasif kayıt ve rol etiketlerinin düzenli izlenmesi gerektiğini gösteriyor.'
    else:
        headline = 'Personel listesi veri kalitesi açısından dengeli görünüyor'
        summary = 'AI özeti, görünür kayıtların temel özlük alanlarında belirgin açık bırakmadığını ve toplu işlemler için sağlıklı zeminin korunduğunu söylüyor.'

    bullets = [
        f'Filtrede {filtered_count} kayıt, toplam havuzda {total_count} personel görünüyor.',
        f'Aktif {active_count} ve pasif {passive_count} kayıt birlikte izlendiğinde görünür pasif yük {passive_visible} satır olarak öne çıkıyor.',
        f'E-posta eksik {missing_email}, sicil eksik {missing_sicil}, birim eksik {missing_unit}, rol etiketi boş {role_gaps} kayıt var.',
    ]
    if duplicate_sicil:
        bullets.append(f'Mükerrer sicil riski taşıyan {duplicate_sicil} görünür kayıt kümesi dikkat istiyor.')
    else:
        bullets.append(f'{unit_count} bağlı birim içinde görünür mükerrer sicil riski tespit edilmedi.')

    actions = [
        {'label': 'Sicil eksiği', 'value': missing_sicil, 'tone': 'critical' if missing_sicil else 'calm'},
        {'label': 'Birim eksiği', 'value': missing_unit, 'tone': 'critical' if missing_unit else 'calm'},
        {'label': 'E-posta eksiği', 'value': missing_email, 'tone': 'watch' if missing_email else 'calm'},
        {'label': 'Pasif görünür', 'value': passive_visible, 'tone': 'watch' if passive_visible else 'calm'},
    ]
    spotlight = [
        {'label': 'Mükerrer sicil kümesi', 'value': duplicate_sicil},
        {'label': 'Bağlı birim', 'value': unit_count},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_admin_users_risk_ai_panel(users: Iterable[Any] | None = None, manager_candidates: Iterable[Any] | None = None) -> dict[str, Any]:
    rows = list(users or [])
    manager_sicils = {(_get(item, 'sicil_no', '') or '').strip() for item in list(manager_candidates or []) if (_get(item, 'sicil_no', '') or '').strip()}

    risk_rows: list[dict[str, Any]] = []
    no_manager = 0
    broken_manager_ref = 0
    missing_role = 0
    missing_unit = 0
    passive_count = 0
    for user in rows:
        score = 0
        reasons: list[str] = []
        manager_1 = (getattr(user, 'yonetici_sicil', None) or '').strip()
        role_text = (getattr(user, 'role', None) or getattr(user, 'role_label', None) or '').strip()
        birim = (getattr(user, 'birim', None) or '').strip()
        ust_birim = (getattr(user, 'ust_birim', None) or '').strip()
        email = (getattr(user, 'email', None) or '').strip()
        if not manager_1:
            no_manager += 1
            score += 3
            reasons.append('1. amir eksik')
        elif manager_sicils and manager_1 not in manager_sicils:
            broken_manager_ref += 1
            score += 3
            reasons.append('amir sicili bulunamadı')
        if not birim or not ust_birim:
            missing_unit += 1
            score += 2
            reasons.append('birim zinciri eksik')
        if not role_text:
            missing_role += 1
            score += 2
            reasons.append('rol boş')
        if not email:
            score += 1
            reasons.append('e-posta boş')
        if not bool(getattr(user, 'is_active', False)):
            passive_count += 1
            score += 1
            reasons.append('pasif kayıt')
        if score:
            risk_rows.append({
                'name': (getattr(user, 'full_name', None) or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}".strip() or '-'),
                'sicil_no': getattr(user, 'sicil_no', None) or '-',
                'score': score,
                'reasons': ', '.join(reasons[:3]),
            })

    risk_rows.sort(key=lambda item: (-_to_int(item['score']), str(item['name']).lower()))
    top_rows = risk_rows[:5]
    critical = no_manager + broken_manager_ref
    warning = missing_unit + missing_role + passive_count
    tone = _tone_from_counts(critical=critical, warning=warning)

    if critical > 0:
        headline = 'Özlük listesinde amir zinciri ve bağlılık riski taşıyan kayıtlar öne çıkıyor'
        summary = 'AI özeti, özellikle amiri eksik veya tanımsız amire bakan personellerin önce temizlenmesini öneriyor.'
    elif warning > 0:
        headline = 'Liste büyük ölçüde dengeli; kalan riskler rol ve birim etiketlerinde yoğunlaşıyor'
        summary = 'AI özeti, kullanıcı yönetim merkezinde kritik kopukluk azalsa da rol, birim ve pasif kayıt bakımının sürmesi gerektiğini söylüyor.'
    else:
        headline = 'Özlük listesi risk görünümü sakin'
        summary = 'AI özeti, filtrelenen listede belirgin amir, rol veya birim baskısı oluşmadığını gösteriyor.'

    bullets = [
        f'Amiri eksik {no_manager}, amir sicili tanımsız {broken_manager_ref} kayıt bulunuyor.',
        f'Birim zinciri eksik {missing_unit}, rol boş {missing_role}, pasif kayıt {passive_count} durumda.',
        f'İlk risk sırası kullanıcı yönetim tablosunda en yüksek {len(top_rows)} kayıt üzerinden okunmalı.',
    ]
    actions = [
        {'label': 'Amiri eksik', 'value': no_manager, 'tone': 'critical' if no_manager else 'calm'},
        {'label': 'Tanımsız amir', 'value': broken_manager_ref, 'tone': 'critical' if broken_manager_ref else 'calm'},
        {'label': 'Rol boş', 'value': missing_role, 'tone': 'watch' if missing_role else 'calm'},
        {'label': 'Pasif kayıt', 'value': passive_count, 'tone': 'watch' if passive_count else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'risk_rows': top_rows,
    }


def build_import_health_priority_ai_panel(stats: Any | None = None, duplicate_units: Iterable[Any] | None = None, unbound_users: Iterable[Any] | None = None, mismatched_users: Iterable[Any] | None = None, incomplete_manager_chain: Iterable[Any] | None = None, empty_workgroups: Iterable[Any] | None = None) -> dict[str, Any]:
    stats = stats or {}
    duplicate_count = _to_int(_get(stats, 'duplicate_units'))
    unbound_count = _to_int(_get(stats, 'unbound_users'))
    mismatched_count = _to_int(_get(stats, 'mismatched_users'))
    chain_count = _to_int(_get(stats, 'incomplete_manager_chain'))
    empty_count = _to_int(_get(stats, 'empty_workgroups'))

    priorities: list[dict[str, Any]] = []
    def add_priority(label: str, value: int, reason: str, tone: str) -> None:
        if value:
            priorities.append({'label': label, 'value': value, 'reason': reason, 'tone': tone})

    add_priority('Eksik amir zinciri', chain_count, 'Görev üretimi ve değerlendirme akışı önce bu kayıtları hisseder.', 'critical' if chain_count else 'calm')
    add_priority('Bağsız personel', unbound_count, 'Birim ağacına düşmeyen kayıtlar rol ve rapor görünümünü bozar.', 'critical' if unbound_count else 'calm')
    add_priority('Yanlış bağlı personel', mismatched_count, 'Profil ile bağlı birim uyuşmadığında üst akışlar yanlış raporlanır.', 'watch')
    add_priority('Mükerrer birim', duplicate_count, 'Aynı isimli birimler zincir ve import eşleşmesini şaşırtır.', 'watch')
    add_priority('Boş çalışma grubu', empty_count, 'Yapıda duran ama kullanılmayan gruplar gereksiz gürültü üretir.', 'calm' if empty_count else 'calm')
    priorities.sort(key=lambda item: (-_to_int(item['value']), 0 if item['tone'] == 'critical' else 1))

    critical = chain_count + unbound_count
    warning = mismatched_count + duplicate_count + empty_count
    tone = _tone_from_counts(critical=critical, warning=warning)

    if critical > 0:
        headline = 'İçe aktarım sağlık raporunda önce zincir ve bağ sorunları çözülmeli'
        summary = 'AI özeti, personel kayıtlarının görev üretimini ve görünürlük akışını bozacak başlıkları öncelik sırasına koydu.'
    elif warning > 0:
        headline = 'Sağlık raporu büyük ölçüde dengeli; kalan iş daha çok yapısal temizlikte'
        summary = 'AI özeti, kritik kopukluk azalsa da birim tekrarları ve boş yapılar için bakım penceresi açılmasını öneriyor.'
    else:
        headline = 'İçe aktarım sağlık raporu temiz görünüyor'
        summary = 'AI özeti, ana veri yapısında belirgin bir kopukluk kalmadığını ve raporun bakım moduna geçtiğini söylüyor.'

    bullets = [
        f'Eksik amir zinciri {chain_count}, bağsız personel {unbound_count}, yanlış bağlı personel {mismatched_count} kayıt seviyesinde izlendi.',
        f'Mükerrer birim {duplicate_count} ve boş çalışma grubu {empty_count} yapısal bakım kalemi olarak öne çıkıyor.',
        f'Önerilen çözüm sırası ilk {min(len(priorities), 3)} başlıkta görev üretimini en çok etkileyen alanları öne taşıyor.',
    ]
    actions = [
        {'label': 'Zincir eksiği', 'value': chain_count, 'tone': 'critical' if chain_count else 'calm'},
        {'label': 'Bağsız personel', 'value': unbound_count, 'tone': 'critical' if unbound_count else 'calm'},
        {'label': 'Yanlış bağlı', 'value': mismatched_count, 'tone': 'watch' if mismatched_count else 'calm'},
        {'label': 'Mükerrer birim', 'value': duplicate_count, 'tone': 'watch' if duplicate_count else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'priorities': priorities[:5],
    }


def build_org_unit_detail_ai_panel(*, unit_obj: Any | None = None, parent_options: Iterable[Any] | None = None) -> dict[str, Any]:
    unit_obj = unit_obj or {}
    unit_name = str(_get(unit_obj, 'name') or 'Yeni kayıt')
    unit_type = str(_get(unit_obj, 'unit_type') or 'diger')
    parent_name = _get(_get(unit_obj, 'parent'), 'name') or 'Ana kayıt'
    is_active = bool(_get(unit_obj, 'is_active', True))
    child_count = 0
    children = _get(unit_obj, 'children')
    if children is not None:
        try:
            child_count = len(list(children))
        except Exception:
            child_count = _to_int(_get(children, 'count', 0))
    linked_users = 0
    users_rel = _get(unit_obj, 'users')
    if users_rel is not None:
        try:
            linked_users = users_rel.count() if hasattr(users_rel, 'count') else len(list(users_rel))
        except Exception:
            linked_users = 0
    parent_pool = len(list(parent_options or []))
    code_present = 1 if _get(unit_obj, 'unit_code') else 0
    warning = (1 if not code_present else 0) + (1 if linked_users == 0 and child_count == 0 and _get(unit_obj, 'id') else 0)
    tone = _tone_from_counts(critical=0, warning=warning)

    if _get(unit_obj, 'id'):
        headline = 'Birim kartı düzenleme öncesi bağlı kayıtlarla birlikte okunuyor'
        summary = 'AI özeti, birim adının tek başına değil; üst bağ, bağlı personel ve alt kırılımlarla birlikte değerlendirilmesini öneriyor.'
    else:
        headline = 'Yeni birim kaydı için bağ kararı belirleyici olacak'
        summary = 'AI özeti, yeni kayıt açılırken üst birim, tür ve kod kombinasyonunun organizasyon ağacında çakışma yaratmayacak şekilde seçilmesini öneriyor.'

    bullets = [
        f'Birim adı: {unit_name}; tür: {unit_type}.',
        f'Üst bağ: {parent_name}; seçilebilir üst birim havuzu {parent_pool} kayıt içeriyor.',
        f'Bağlı personel {linked_users}, alt birim {child_count} kayıt ile izleniyor.',
        f"Durum: {'Aktif' if is_active else 'Pasif'}; kod alanı {'tanımlı' if code_present else 'boş'} durumda.",
    ]
    recommendations = []
    if not code_present:
        recommendations.append('Aynı isimli birimlerin ayrışması için kod alanını doldurmanız önerilir.')
    if linked_users == 0 and child_count == 0 and _get(unit_obj, 'id'):
        recommendations.append('Bu birim aktif ama bağlı personel veya alt kırılım taşımıyor; görünürlük ve kullanım amacı tekrar kontrol edilmeli.')
    if parent_name == 'Ana kayıt' and unit_type in {'calisma_grubu', 'koordinatorluk', 'diger'}:
        recommendations.append('Bu tür kayıtlar çoğu senaryoda üst birime bağlanır; ana kayıt bırakılıyorsa kurumsal gerekçe net olmalı.')
    if not recommendations:
        recommendations.append('Kayıt görünümü dengeli; sonraki adım personel atamaları ile birim bağının terminolojik olarak uyumlu kaldığını doğrulamaktır.')

    actions = [
        {'label': 'Bağlı personel', 'value': linked_users, 'tone': 'calm' if linked_users else 'watch'},
        {'label': 'Alt birim', 'value': child_count, 'tone': 'calm'},
        {'label': 'Kod', 'value': 'Var' if code_present else 'Yok', 'tone': 'watch' if not code_present else 'calm'},
        {'label': 'Durum', 'value': 'Aktif' if is_active else 'Pasif', 'tone': 'calm' if is_active else 'watch'},
    ]
    spotlight = [
        {'label': 'Üst bağ', 'value': str(parent_name)},
        {'label': 'Havuz', 'value': parent_pool},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
        'recommendations': recommendations[:4],
    }


def build_personnel_density_ai_panel(stats: Any | None = None, user_rows: Iterable[Any] | None = None) -> dict[str, Any]:
    stats = stats or {}
    rows = list(user_rows or [])
    unit_map: dict[str, int] = {}
    role_map: dict[str, int] = {}
    for row in rows:
        unit_name = str(_get(row, 'birim') or '-').strip() or '-'
        role_name = str(_get(row, 'role_text') or '-').strip() or '-'
        unit_map[unit_name] = unit_map.get(unit_name, 0) + 1
        role_map[role_name] = role_map.get(role_name, 0) + 1

    total = max(_to_int(_get(stats, 'filtered_count', len(rows))), len(rows), 1)
    top_units = sorted(unit_map.items(), key=lambda item: (-item[1], item[0].lower()))[:6]
    top_roles = sorted(role_map.items(), key=lambda item: (-item[1], item[0].lower()))[:6]
    unit_density = [
        {
            'label': label,
            'value': count,
            'share': round((count / total) * 100, 1),
            'tone': 'critical' if count / total >= 0.35 else 'watch' if count / total >= 0.2 else 'calm',
        }
        for label, count in top_units
    ]
    role_density = [
        {
            'label': label,
            'value': count,
            'share': round((count / total) * 100, 1),
            'tone': 'critical' if count / total >= 0.45 else 'watch' if count / total >= 0.25 else 'calm',
        }
        for label, count in top_roles
    ]
    critical = sum(1 for item in unit_density if item['tone'] == 'critical') + sum(1 for item in role_density if item['tone'] == 'critical')
    warning = sum(1 for item in unit_density if item['tone'] == 'watch') + sum(1 for item in role_density if item['tone'] == 'watch')
    tone = _tone_from_counts(critical=critical, warning=warning)

    if critical:
        headline = 'Personel dağılımında yoğun kümeler var'
        summary = 'AI özeti, bazı birim ve rol gruplarının filtrede belirgin biçimde yığıldığını; toplu işlem ve veri kalite kontrolünün önce bu kümelerde yapılmasının daha verimli olacağını gösteriyor.'
    elif warning:
        headline = 'Yoğunluk görünümü dengeli ama izlenmesi gereken kümeler var'
        summary = 'AI özeti, dağılımın genel olarak yaygın olduğunu; yine de orta yoğunluktaki birim ve rol kümelerinin toplu aksiyonlarda öncelikli okunmasının fayda sağlayacağını söylüyor.'
    else:
        headline = 'Personel dağılımı geniş bir alana yayılmış görünüyor'
        summary = 'AI özeti, görünür personel havuzunun tek bir birim ya da rol etrafında aşırı toplanmadığını; filtrelerin dengeli bir örneklem verdiğini gösteriyor.'

    bullets = [
        f'Filtrede {total} kayıt üzerinden yoğunluk hesaplandı.',
        f'En yoğun birim payı %{unit_density[0]["share"]:.1f} seviyesinde.' if unit_density else 'Görünür birim verisi bulunmuyor.',
        f'En yoğun rol payı %{role_density[0]["share"]:.1f} seviyesinde.' if role_density else 'Görünür rol verisi bulunmuyor.',
        'Toplu güncelleme, uyarı taraması ve import sonrası kontrol için önce yoğun kümeleri kullanmanız önerilir.',
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'unit_density': unit_density,
        'role_density': role_density,
        'actions': [
            {'label': 'Yoğun birim', 'value': unit_density[0]['label'] if unit_density else '-', 'tone': unit_density[0]['tone'] if unit_density else 'calm'},
            {'label': 'Yoğun rol', 'value': role_density[0]['label'] if role_density else '-', 'tone': role_density[0]['tone'] if role_density else 'calm'},
            {'label': 'Birim kümesi', 'value': len(unit_density), 'tone': 'calm'},
            {'label': 'Rol kümesi', 'value': len(role_density), 'tone': 'calm'},
        ],
    }


def build_import_health_simulation_ai_panel(*, stats: Any | None = None, simulation: Any | None = None) -> dict[str, Any]:
    stats = stats or {}
    simulation = simulation or {}
    bindable = _to_int(_get(simulation, 'bindable_users'))
    syncable = _to_int(_get(simulation, 'syncable_users'))
    chain_review = _to_int(_get(simulation, 'chain_review_users'))
    duplicate_review = _to_int(_get(simulation, 'duplicate_review_units'))
    total_effect = bindable + syncable
    tone = _tone_from_counts(critical=chain_review + duplicate_review, warning=0 if total_effect else 1)

    if total_effect:
        headline = 'Tek tık simülasyon, otomatik uygulanabilir kayıtları ayırdı'
        summary = 'AI özeti, sağlık raporundaki sorunların hangilerinin güvenli ön düzenleme ile işaretlenebileceğini; hangilerinin ise yönetici incelemesi istediğini ayrı gösteriyor.'
    else:
        headline = 'Simülasyon çalıştı; otomatik uygulanabilir etki düşük görünüyor'
        summary = 'AI özeti, mevcut görünümde sorunların daha çok yapısal ve karar gerektiren tipte olduğunu; otomatik önerilerin çoğunun yalnızca önceliklendirme amacı taşıdığını gösteriyor.'

    bullets = [
        f'{bindable} bağsız personel için birim eşleme adayı üretildi.',
        f'{syncable} yanlış bağlı kayıt için profil → bağlı birim senkronu önerildi.',
        f'{chain_review} kayıt eksik amir zinciri nedeniyle manuel incelemeye bırakıldı.',
        f'{duplicate_review} mükerrer/benzer birim satırı otomatik birleştirme yerine doğrulama listesine alındı.',
    ]
    actions = [
        {'label': 'Otomatik aday', 'value': total_effect, 'tone': 'calm' if total_effect else 'watch'},
        {'label': 'Manuel zincir', 'value': chain_review, 'tone': 'critical' if chain_review else 'calm'},
        {'label': 'Birim doğrulama', 'value': duplicate_review, 'tone': 'watch' if duplicate_review else 'calm'},
    ]
    preview_rows = [
        {'label': 'Birim eşleme adayı', 'value': bindable, 'note': 'Birim ve üst birim metni dolu olan ama ağaç bağı eksik personeller.'},
        {'label': 'Profil-birim senkronu', 'value': syncable, 'note': 'Profildeki birim bilgisi ile bağlı organizasyon birimi farklı olan kayıtlar.'},
        {'label': 'Zincir incelemesi', 'value': chain_review, 'note': '1/2/3. amir alanlarından en az biri eksik ya da tutarsız görünen kayıtlar.'},
        {'label': 'Mükerrer birim doğrulaması', 'value': duplicate_review, 'note': 'Aynı ad ve ebeveynle tekrar eden birim satırları; otomatik birleştirilmez, sadece listeye alınır.'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets,
        'actions': actions,
        'preview_rows': preview_rows,
    }


def build_hierarchy_tree_ai_panel(*, grouped_tree: Any | None = None, users: Iterable[Any] | None = None, q: str | None = None, birim: str | None = None, scope_label: str | None = None, total_user_count: int | None = None) -> dict[str, Any]:
    tree_rows = list(grouped_tree or [])
    user_rows = list(users or [])
    filtered_count = len(user_rows)
    total_count = _to_int(total_user_count, filtered_count)
    unit_count = len(tree_rows)
    hidden_count = max(total_count - filtered_count, 0)
    tone = _tone_from_counts(critical=1 if filtered_count == 0 and total_count > 0 else 0, warning=1 if hidden_count > 0 else 0)

    filters = []
    if q:
        filters.append(f"arama: {q}")
    if birim:
        filters.append(f"birim: {birim}")
    filter_text = ", ".join(filters) if filters else "genel görünüm"
    scope_text = scope_label or "Seçili kapsam"

    if filtered_count == 0 and total_count > 0:
        headline = "Ağaç görünümünde sonuç bulunamadı"
        summary = "AI özeti, mevcut filtrelerle görünür düğüm kalmadığını; arama ve birim filtresinin gevşetilmesini öneriyor."
    elif hidden_count > 0:
        headline = "Hiyerarşi ağacı filtreli görünümde izleniyor"
        summary = "AI özeti, görünür personel sayısının toplam kapsamın altında kaldığını; daraltılmış görünümle çalışıldığını gösteriyor."
    else:
        headline = "Hiyerarşi ağacı dengeli görünüyor"
        summary = "AI özeti, seçili kapsamda ağaç görünümünün okunabilir olduğunu; dağılımın doğrudan incelenebileceğini gösteriyor."

    bullets = [
        f"{scope_text} içinde toplam {total_count} personelin {filtered_count} kadarı bu görünümde listeleniyor.",
        f"Ağaçta {unit_count} birim/düğüm grubu var; aktif filtre görünümü: {filter_text}.",
        f"Filtre dışında kalan kayıt sayısı {hidden_count}; kapsam dar ise üst birim veya arama filtresi gözden geçirilebilir.",
    ]
    actions = [
        {"label": "Görünen kişi", "value": filtered_count, "tone": "calm"},
        {"label": "Toplam kapsam", "value": total_count, "tone": "calm"},
        {"label": "Birim düğümü", "value": unit_count, "tone": "watch" if unit_count > 20 else "calm"},
        {"label": "Filtre dışı", "value": hidden_count, "tone": "watch" if hidden_count else "calm"},
    ]
    spotlight = [
        {"label": "Kapsam", "value": scope_text},
        {"label": "Filtre", "value": filter_text},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "spotlight": spotlight,
    }


def build_hierarchy_bulk_edit_ai_panel(*, analysis_rows: Iterable[Any] | None = None, period: Any | None = None, scope_label: str | None = None) -> dict[str, Any]:
    rows = list(analysis_rows or [])
    total_count = len(rows)
    missing_count = 0
    warning_count = 0
    level3_count = 0
    for row in rows:
        if _has_real_hierarchy_warning(row):
            warning_count += 1
        if _has_level_3_binding(row):
            level3_count += 1
        if not _is_hierarchy_missing_exempt(row) and not _has_first_manager_binding(row):
            missing_count += 1
    tone = _tone_from_counts(critical=missing_count, warning=warning_count)
    period_title = _get(period, 'title', 'Seçili dönem')
    scope_text = scope_label or 'Seçili kapsam'

    if missing_count:
        headline = f"{period_title} için toplu düzenleme öncesi boşluklar var"
        summary = "AI özeti, toplu hiyerarşi düzenlemesinde önce 1. amiri eksik kayıtların ayrıştırılmasını öneriyor."
    elif warning_count:
        headline = f"{period_title} için toplu düzenleme dikkat istiyor"
        summary = "AI özeti, eksik zincir olmasa da uyarı taşıyan kayıtların toplu güncellemeden önce gözden geçirilmesini öneriyor."
    else:
        headline = f"{period_title} için toplu düzenleme görünümü dengeli"
        summary = "AI özeti, seçili kapsamda toplu güncellemenin düşük riskli bir görünüm sunduğunu gösteriyor."

    bullets = [
        f"{scope_text} içinde toplu düzenleme aday sayısı {total_count}.",
        f"1. amiri eksik kayıt {missing_count}, uyarılı kayıt {warning_count}.",
        f"3. amirli akış sayısı {level3_count}; toplu güncellemede bu grup ayrıca izlenmeli.",
    ]
    actions = [
        {"label": "Toplam aday", "value": total_count, "tone": "calm"},
        {"label": "1. amir eksik", "value": missing_count, "tone": "critical" if missing_count else "calm"},
        {"label": "Uyarılı kayıt", "value": warning_count, "tone": "watch" if warning_count else "calm"},
        {"label": "3. amirli", "value": level3_count, "tone": "watch" if level3_count else "calm"},
    ]
    detail_cards = [
        {
            "title": "Öncelikli temizlik",
            "subtitle": "Toplu düzenleme öncesi ilk müdahale kümesi",
            "tone": "critical" if missing_count else "calm",
            "meta": [
                {"label": "Eksik 1. amir", "value": missing_count},
                {"label": "Uyarılı kayıt", "value": warning_count},
            ],
        },
        {
            "title": "Kapsam görünümü",
            "subtitle": scope_text,
            "tone": "watch" if level3_count else "calm",
            "meta": [
                {"label": "Toplam", "value": total_count},
                {"label": "3. amirli", "value": level3_count},
            ],
        },
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "detail_cards": detail_cards,
    }


def build_hierarchy_assignment_person_ai_panel(user_obj: Any | None, manager_candidates: Iterable[Any] | None = None) -> dict[str, Any]:
    user_obj = user_obj or {}
    manager_candidates = list(manager_candidates or [])
    user_name = _get(user_obj, 'full_name') or f"{_get(user_obj, 'ad', '')} {_get(user_obj, 'soyad', '')}".strip() or 'Personel'
    birim = _get(user_obj, 'birim') or _get(_get(user_obj, 'organization_unit'), 'name') or '-'
    first_manager = _get(user_obj, 'yonetici_sicil') or _get(user_obj, 'manager_1') or _get(_get(user_obj, 'manager_1_obj'), 'sicil_no')
    second_manager = _get(user_obj, 'ikinci_yonetici_sicil') or _get(user_obj, 'manager_2') or _get(_get(user_obj, 'manager_2_obj'), 'sicil_no')
    third_manager = _get(user_obj, 'ucuncu_yonetici_sicil') or _get(user_obj, 'manager_3') or _get(_get(user_obj, 'manager_3_obj'), 'sicil_no')
    assigned_count = sum(1 for value in (first_manager, second_manager) if value) + (1 if third_manager else 0)
    missing_count = (0 if first_manager else 1) + (0 if second_manager else 1)
    candidate_count = len(manager_candidates)
    tone = _tone_from_counts(critical=1 if not first_manager else 0, warning=(1 if not second_manager else 0))

    if not first_manager:
        headline = f"{user_name} için 1. amir bilgisi tamamlanmalı"
        summary = "AI özeti, kişi bazlı atamada önce 1. amir alanının doldurulmasını; ardından üst zincirin netleştirilmesini öneriyor."
    elif missing_count > 0:
        headline = f"{user_name} için zincir kısmen tamamlanmış"
        summary = "AI özeti, temel zincirin çalıştığını ancak üst halkalarda eksik alanlar bulunduğunu gösteriyor."
    else:
        headline = f"{user_name} için kişi bazlı atama görünümü dengeli"
        summary = "AI özeti, kişi bazlı amir atamasında temel halkaların doldurulduğunu ve formun kontrol amaçlı kullanılabileceğini gösteriyor."

    bullets = [
        f"Personel: {user_name} / Birim: {birim}.",
        f"Tanımlı amir sayısı {assigned_count}; eksik halka {missing_count if missing_count > 0 else 0}.",
        f"Seçilebilir yönetici havuzu {candidate_count} kişi.",
    ]
    actions = [
        {"label": "1. amir", "value": 'Var' if first_manager else 'Eksik', "tone": "critical" if not first_manager else "calm"},
        {"label": "2. amir", "value": 'Var' if second_manager else 'Eksik', "tone": "watch" if not second_manager else "calm"},
        {"label": "3. amir", "value": 'Var' if third_manager else 'Opsiyonel', "tone": "calm" if third_manager else "watch"},
        {"label": "Aday havuz", "value": candidate_count, "tone": "calm"},
    ]
    detail_cards = [
        {
            "title": "Zincir durumu",
            "subtitle": "Kişi bazlı atama görünümü",
            "tone": "critical" if not first_manager else ("watch" if missing_count > 0 else "calm"),
            "meta": [
                {"label": "1. amir", "value": first_manager or '-'},
                {"label": "2. amir", "value": second_manager or '-'},
                {"label": "3. amir", "value": third_manager or '-'},
            ],
        },
        {
            "title": "Form rehberi",
            "subtitle": "Kayıt öncesi hızlı kontrol",
            "tone": "watch" if candidate_count < 3 else "calm",
            "meta": [
                {"label": "Aday sayısı", "value": candidate_count},
                {"label": "Birim", "value": birim},
            ],
        },
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "detail_cards": detail_cards,
    }


def build_org_units_risk_map_ai_panel(*, rows: Iterable[Any] | None = None, stats: Any | None = None) -> dict[str, Any]:
    row_list = list(rows or [])
    stats = stats or {}
    risk_map: list[dict[str, Any]] = []
    critical = 0
    warning = 0
    for row in row_list:
        unit = _get(row, 'unit') if isinstance(row, dict) else None
        if unit is None and isinstance(row, (list, tuple)) and row:
            unit = row[0]
        unit_name = str(_get(unit, 'name') or _get(row, 'parent_name') or '-').strip() or '-'
        personnel_count = _to_int(_get(row, 'personnel_count'))
        child_count = _to_int(_get(row, 'child_count'))
        is_active = bool(_get(unit, 'is_active', True))
        code_present = 1 if str(_get(unit, 'unit_code') or _get(unit, 'code') or '').strip() else 0
        score = 0
        reasons = []
        if is_active and personnel_count == 0 and child_count == 0:
            score += 3
            reasons.append('bağlı kayıt yok')
        if is_active and child_count == 0 and personnel_count <= 1:
            score += 1
            reasons.append('dar kapsama')
        if not code_present:
            score += 1
            reasons.append('kod boş')
        if not is_active:
            score += 1
            reasons.append('pasif')
        if score:
            if score >= 3:
                critical += 1
            else:
                warning += 1
            risk_map.append({
                'label': unit_name,
                'value': score,
                'detail': ', '.join(reasons[:3]) or 'izleme',
                'tone': 'critical' if score >= 3 else 'watch',
            })
    risk_map.sort(key=lambda item: (-_to_int(item['value']), str(item['label']).lower()))
    tone = _tone_from_counts(critical=critical, warning=warning)
    if critical:
        headline = 'Birim bazlı risk yoğunluğu bazı kayıtlarda kümeleniyor'
        summary = 'AI özeti, aktif görünüp personel veya alt kırılım taşımayan birimlerin organizasyon ağacında önce ele alınmasını öneriyor.'
    elif warning:
        headline = 'Organizasyon listesi genel olarak dengeli; düşük yoğunluklu bakım başlıkları var'
        summary = 'AI özeti, risk yoğunluğunun daha çok kod boşluğu ve dar kapsama gösteren birimlerde toplandığını söylüyor.'
    else:
        headline = 'Organizasyon listesi risk yoğunluğu sakin'
        summary = 'AI özeti, filtrelenen birim listesinde belirgin yapısal baskı görülmediğini gösteriyor.'
    bullets = [
        f'Toplam {len(row_list)} kayıt içinde kritik yoğunluk taşıyan {critical}, izleme gerektiren {warning} birim var.',
        'Aktif ama ilişkisiz duran birimler önce görünürlük ve hiyerarşi bakımını etkiler.',
        f'İlk {min(len(risk_map), 5)} kayıt, birim bazlı risk haritası olarak üstte tutuldu.',
    ]
    actions = [
        {'label': 'Kritik yoğunluk', 'value': critical, 'tone': 'critical' if critical else 'calm'},
        {'label': 'İzleme listesi', 'value': warning, 'tone': 'watch' if warning else 'calm'},
        {'label': 'Toplam kayıt', 'value': _to_int(_get(stats, 'filtered_count', len(row_list))), 'tone': 'calm'},
        {'label': 'Aktif birim', 'value': _to_int(_get(stats, 'active_count')), 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'risk_map': risk_map[:6],
    }


def build_assignment_recommendation_center_ai_panel(
    *,
    summary: dict[str, Any] | None = None,
    recommendation_rows: Iterable[Any] | None = None,
    action_plan_rows: Iterable[Any] | None = None,
    pressure_rows: Iterable[Any] | None = None,
    period: Any | None = None,
    scope_label: str | None = None,
) -> dict[str, Any]:
    summary = summary or {}
    recommendation_rows = list(recommendation_rows or [])
    action_plan_rows = list(action_plan_rows or [])
    pressure_rows = list(pressure_rows or [])
    uncovered = _to_int(_get(summary, "uncovered"))
    chain_issue = _to_int(_get(summary, "chain_issue"))
    delegated = _to_int(_get(summary, "delegated"))
    exempted = _to_int(_get(summary, "exempted"))
    tone = _tone_from_counts(critical=uncovered + chain_issue, warning=delegated + exempted)

    period_title = _get(period, "title", "Seçili dönem")
    if uncovered or chain_issue:
        headline = f"{period_title} için önce kritik atama açıkları kapatılmalı"
        summary_text = (
            "AI öneri merkezi, önce açıkta kalan görevleri ve amir zinciri kırıklarını, "
            "ardından kalıcılaşan vekâlet baskısını ele almanızı öneriyor."
        )
    elif delegated or exempted:
        headline = f"{period_title} için vekâlet ve muafiyet baskısı izlenmeli"
        summary_text = (
            "AI öneri merkezi, seçili kapsamda kritik açık azalsa da vekâletli ve muaf "
            "akışların aynı birimlerde kümelendiğini gösteriyor."
        )
    else:
        headline = f"{period_title} için öneri merkezi dengeli görünüyor"
        summary_text = (
            "AI öneri merkezi, seçili kapsamda acil bir kırmızı bayrak görmüyor. "
            "Yine de ilk aksiyon planı bakım akışı için hazır tutuluyor."
        )

    bullets = [
        f"Seçili kapsam: {scope_label or 'Genel görünüm'}; {len(recommendation_rows)} öneri ve {len(action_plan_rows)} aksiyon satırı hazırlandı.",
        f"Kritik açıkta {uncovered}, zincir sorunu {chain_issue}, vekâletli {delegated}, muaf {exempted} kayıt okunuyor.",
    ]
    if pressure_rows:
        top = pressure_rows[0]
        bullets.append(
            f"En yüksek baskı {top.get('unit_name') or top.get('label') or '-'} biriminde ve risk skoru "
            f"{top.get('risk_score') or top.get('score') or 0}."
        )
    bullets.append("Aksiyon planı tablosu indirilebilir; filtre kısayolları ilgili denetim görünümüne tek tıkla taşır.")

    actions = [
        {"label": "Kritik öneri", "value": len([r for r in recommendation_rows if r.get("tone") == "critical"]), "tone": "critical" if uncovered or chain_issue else "calm"},
        {"label": "İzleme önerisi", "value": len([r for r in recommendation_rows if r.get("tone") == "watch"]), "tone": "watch" if delegated or exempted else "calm"},
        {"label": "Aksiyon planı", "value": len(action_plan_rows), "tone": "watch" if action_plan_rows else "calm"},
        {"label": "Baskı birimi", "value": len(pressure_rows), "tone": "watch" if pressure_rows else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary_text,
        "bullets": bullets[:4],
        "actions": actions,
    }


def build_assignment_delegation_pressure_ai_panel(
    *,
    pressure_rows: Iterable[Any] | None = None,
    shortcut_rows: Iterable[Any] | None = None,
    scope_label: str | None = None,
) -> dict[str, Any]:
    pressure_rows = list(pressure_rows or [])
    shortcut_rows = list(shortcut_rows or [])
    critical = sum(1 for row in pressure_rows if (row.get("tone") == "critical"))
    warning = sum(1 for row in pressure_rows if (row.get("tone") == "watch"))
    tone = _tone_from_counts(critical=critical, warning=warning)

    if critical:
        headline = "Kalıcı görev devri baskısı bazı birimlerde yükseliyor"
        summary = (
            "AI özeti, aynı birimlerde tekrarlayan vekâlet ve zincir açıklarının "
            "kalıcı operasyon baskısına dönüştüğünü işaret ediyor."
        )
    elif warning:
        headline = "Görev devri baskısı izlenmeli"
        summary = "AI özeti, bazı birimlerde tekrar eden vekâlet yoğunluğunun bakım ve planlama istediğini söylüyor."
    else:
        headline = "Görev devri baskısı dengeli"
        summary = "AI özeti, seçili kapsamda belirgin kümelenen görev devri baskısı görmüyor."

    bullets = [f"Seçili kapsam: {scope_label or 'Genel görünüm'}; baskı haritasında {len(pressure_rows)} birim izleniyor."]
    if pressure_rows:
        top = pressure_rows[0]
        bullets.append(
            f"İlk sırada {top.get('unit_name') or top.get('label') or '-'} bulunuyor; "
            f"risk skoru {top.get('risk_score') or top.get('score') or 0}."
        )
    if shortcut_rows:
        bullets.append("Kısayol filtreleriyle doğrudan açıkta, zincir, vekâlet veya muaf listesine geçebilirsiniz.")

    actions = [
        {"label": "Kritik birim", "value": critical, "tone": "critical" if critical else "calm"},
        {"label": "İzleme birimi", "value": warning, "tone": "watch" if warning else "calm"},
        {"label": "Filtre kısayolu", "value": len(shortcut_rows), "tone": "watch" if shortcut_rows else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
    }

