"""
BYS360 AI Stub Engine — Genişletilmiş Senaryo Kütüphanesi
Eksik 8 modül için tam kural tabanlı yanıt üretici.

Mevcut stub_engine.py dosyasına eklenecek:
  1. SUPPORTED_STUB_SCENARIOS listesine yeni senaryolar eklenir
  2. _SCENARIO_BUILDERS dict'ine yeni builder'lar eklenir
  3. _infer_scenario hints dict'ine yeni ipuçları eklenir

Bu dosya doğrudan çalıştırılmaz; stub_engine.py ile birleştirilir.
"""
from __future__ import annotations

from typing import Any

# ── Yardımcı fonksiyonlar (stub_engine.py'dekilerle aynı imza) ──────────────

def _norm(value: Any) -> str:
    return str(value or "").strip().lower()

def _text(value: Any, fallback: str = "-") -> str:
    text = str(value or "").strip()
    return text or fallback

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default

def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value or default))
    except (TypeError, ValueError):
        return default

def _lines(*rows: str) -> str:
    return "\n".join(row for row in rows if str(row or "").strip())


# ═══════════════════════════════════════════════════════════════════
# 1. GÖRÜŞME SONRASI NOTLAR — aftercare / koçluk
# ═══════════════════════════════════════════════════════════════════
def _build_aftercare_coaching(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    meeting_type   = _text(payload.get("meeting_type"), "birebir görüşme")
    note_count     = _safe_int(payload.get("note_count"))
    prep_note      = _text(payload.get("prep_note"), "")
    _safe_int(payload.get("action_count"))
    open_actions   = _safe_int(payload.get("open_actions"))
    employee_name  = _text((payload.get("employee") or {}).get("full_name"), "Personel")
    score          = _safe_float(payload.get("score"))

    # Görüşme kalitesi değerlendirmesi
    if note_count == 0:
        quality_text = "görüşme notu henüz girilmemiş; içerik belgelenmeden görüşme tamamlanamaz"
    elif note_count < 3:
        quality_text = "görüşme kısmen belgelenmiş; ek detay eklenmesi izlenebilirliği artırır"
    else:
        quality_text = "görüşme yeterince belgelenmiş"

    prep_text = (
        "hazırlık notu mevcut; görüşme hedefli başlamış"
        if prep_note
        else "hazırlık notu eksik; bir sonraki görüşme öncesinde eklenmesi önerilir"
    )

    action_text = (
        f"{open_actions} açık eylem planı devam ediyor; takip bildirimi zamanında yapılmalı"
        if open_actions > 0
        else "tüm eylem planları kapalı; yeni döngü başlatılabilir"
    )

    score_note = ""
    if score > 0:
        if score < 70:
            score_note = f"— Puan {score:.0f} ile risk bandında; görüşmenin bu puanı ele alıp almadığı kontrol edilmeli."
        elif score >= 90:
            score_note = f"— Puan {score:.0f} ile güçlü performans; güçlü yanların görüşmede teyit edilip edilmediğini not edin."

    return _lines(
        "Görüşme Koçluk Notu:",
        f"- {employee_name} ile yapılan {meeting_type}: {quality_text}.",
        f"- Hazırlık durumu: {prep_text}.",
        f"- Eylem planı: {action_text}.",
        score_note,
        "Sonraki Adım Önerileri:",
        "- Görüşme sonrası 48 saat içinde eylem planlarını güncelleyin ve personele özet gönderin.",
        "- Bir sonraki görüşmede bu döngünün açık maddelerini ilk 5 dakikada ele alın.",
        (
            "- Puan risk bandında olduğundan destek planı ve üst onay akışını kontrol edin."
            if score > 0 and score < 70
            else "- Sürecin kurumsal standartlarla uyumunu korumak için periyodik kontrol yeterli."
        ),
        "- Bu not AI karar destek çıktısıdır; idari karar ve yönetici kanaati belirleyicidir.",
    )


# ═══════════════════════════════════════════════════════════════════
# 2. DÖNEM İÇİ NOTLAR — pattern ve trend analizi
# ═══════════════════════════════════════════════════════════════════
def _build_interim_notes_pattern(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    summary        = payload.get("summary") or {}
    total          = _safe_int(summary.get("total"))
    positive       = _safe_int(summary.get("positive"))
    negative       = _safe_int(summary.get("negative"))
    development    = _safe_int(summary.get("development"))
    achievement    = _safe_int(summary.get("achievement", 0))
    scorecard_vis  = _safe_int(summary.get("visible_on_scoring"))
    employee_name  = _text((payload.get("employee") or {}).get("full_name"), "Personel")
    period_title   = _text(payload.get("period_title"), "aktif dönem")

    if total == 0:
        return _lines(
            "Dönem İçi Not Analizi:",
            f"- {employee_name} için {period_title} döneminde henüz not girilmemiş.",
            "Öneri:",
            "- Dönem ortasına gelindiğinde en az 2–3 gözlem notu eklenmesi değerlendirme kalitesini artırır.",
            "- Olumlu olay ve gelişim ihtiyacı notları dengeli tutulmalıdır.",
        )

    # Denge analizi
    if positive == 0 and negative > 0:
        balance_note = "yalnızca olumsuz olaylar belgelenmiş; dengeli geri bildirim için olumlu gözlemler de eklenmeli"
    elif negative == 0 and positive > 0:
        balance_note = "yalnızca olumlu olaylar belgelenmiş; gelişim alanlarının da not edilmesi önerilir"
    elif positive >= negative * 2:
        balance_note = "olumlu ağırlıklı denge; güçlü performans sinyalleri var"
    elif negative >= positive * 2:
        balance_note = "olumsuz ağırlıklı denge; gelişim desteği ve yönetici takibi önceliklendirilmeli"
    else:
        balance_note = "dengeli not dağılımı; gelişim ve güç yönleri birlikte izleniyor"

    # Karne görünürlüğü
    visibility_note = (
        f"{scorecard_vis} not karne değerlendirmesinde görünür olarak işaretlenmiş"
        if scorecard_vis > 0
        else "hiçbir not karne değerlendirmesine dahil edilmemiş; uygunlarını işaretleyin"
    )

    # Trend tahmini
    if development > 2:
        trend_note = f"{development} gelişim ihtiyacı notu; dönem sonu değerlendirmesinde odak alanı olarak kullanılabilir"
    elif achievement > 1:
        trend_note = f"{achievement} başarı notu; dönem özeti için güçlü referans malzeme mevcut"
    else:
        trend_note = "belirsiz trend; dönem sonuna kadar düzenli not eklenmesi analiz kalitesini artırır"

    return _lines(
        f"Dönem İçi Not Analizi — {employee_name} / {period_title}:",
        f"- Toplam {total} not: {positive} olumlu, {negative} olumsuz, {development} gelişim, {achievement} başarı.",
        f"- Denge değerlendirmesi: {balance_note}.",
        f"- Karne bağlantısı: {visibility_note}.",
        "Trend Yorumu:",
        f"- {trend_note}.",
        "Dönem Sonu Önerisi:",
        "- Bu notları değerlendirme yazarken referans olarak kullanın; tutarlı gerekçe oluşturmaya yardımcı olur.",
        "- Karne görünürlüğüne alınan notların nesnel ve belgeye dayalı olduğundan emin olun.",
        "- Bu not AI kural motoru çıktısıdır; nihai değerlendirme kararı yöneticidedir.",
    )


# ═══════════════════════════════════════════════════════════════════
# 3. EYLEM PLANI TAKİBİ — gecikme riski analizi
# ═══════════════════════════════════════════════════════════════════
def _build_followup_risk(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    open_count     = _safe_int(payload.get("open_count"))
    overdue_count  = _safe_int(payload.get("overdue_count"))
    closed_count   = _safe_int(payload.get("closed_count"))
    due_soon_count = _safe_int(payload.get("due_soon_count"))
    total          = open_count + closed_count
    completion_rate = (closed_count / total * 100) if total > 0 else 0.0

    if total == 0:
        return _lines(
            "Eylem Planı Takip Analizi:",
            "- Henüz eylem planı kaydı bulunmuyor.",
            "Öneri:",
            "- Görüşme sonrası oluşturulan eylem planlarını bu ekrandan takip edin.",
            "- 7 günlük takip bildirimleri otomatik oluşturulabilir.",
        )

    # Risk tespiti
    if overdue_count >= 3:
        risk_level = "yüksek"
        risk_note  = f"{overdue_count} gecikmiş eylem planı; acil müdahale gerekiyor"
    elif overdue_count > 0:
        risk_level = "orta"
        risk_note  = f"{overdue_count} gecikmiş eylem planı; bu hafta içinde kapatılmalı"
    elif due_soon_count > 0:
        risk_level = "düşük"
        risk_note  = f"{due_soon_count} plan yakında sona erecek; hatırlatma gönderilmeli"
    else:
        risk_level = "yok"
        risk_note  = "gecikmiş veya kritik tarihli plan yok; süreç sağlıklı ilerliyor"

    return _lines(
        "Eylem Planı Takip Analizi:",
        f"- Toplam {total} plandan {closed_count} kapatılmış, {open_count} açık. Tamamlanma: %{completion_rate:.0f}.",
        f"- Risk seviyesi {risk_level}: {risk_note}.",
        (
            f"- {due_soon_count} plan 7 gün içinde sona eriyor; öncelikli takip gerekiyor."
            if due_soon_count > 0
            else "- Yakın tarihli kritik bitiş tarihi bulunmuyor."
        ),
        "Aksiyon Önerisi:",
        (
            "- Gecikmiş planların sorumlu yöneticilerine bugün hatırlatma gönderin."
            if overdue_count > 0
            else "- Açık planları haftalık gözden geçirin; kapanış notlarını doldurun."
        ),
        "- Kapatılan planlarda öğrenilen dersleri bir sonraki görüşme gündemine alın.",
        "- Bu analiz AI kural motoru çıktısıdır; takip kararı yöneticidedir.",
    )


# ═══════════════════════════════════════════════════════════════════
# 4. SÜREÇ HATTI — tıkanma ve ilerleme analizi
# ═══════════════════════════════════════════════════════════════════
def _build_pipeline_status(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    overall_percent = _safe_int(payload.get("overall_percent"))
    total_steps     = _safe_int(payload.get("total"))
    ready_steps     = _safe_int(payload.get("ready"))
    attention_steps = _safe_int(payload.get("attention"))
    missing_steps   = _safe_int(payload.get("missing"))
    warning_count   = _safe_int(payload.get("warning_count"))

    if total_steps == 0:
        return _lines(
            "Süreç Hattı Analizi:",
            "- Süreç adımları henüz tanımlanmamış veya yüklenemedi.",
            "Öneri:",
            "- Migration tamamlandıktan sonra süreç hattı otomatik dolar.",
        )

    # Tıkanma tespiti
    if missing_steps >= 2:
        bottleneck = f"{missing_steps} adım kritik eksik; canlıya çıkış öncesi tamamlanmalı"
        urgency    = "yüksek"
    elif attention_steps >= 3:
        bottleneck = f"{attention_steps} adım dikkat gerektiriyor; bu hafta gözden geçirilmeli"
        urgency    = "orta"
    elif warning_count > 0:
        bottleneck = f"{warning_count} uyarı notu var; izleme yeterli"
        urgency    = "düşük"
    else:
        bottleneck = "belirgin tıkanma noktası yok; süreç sağlıklı"
        urgency    = "yok"

    progress_text = (
        "canlıya çıkış için kritik eşik aşıldı" if overall_percent >= 80
        else "ilerleme var ama eksikler kapatılmadan canlı geçiş risklidir" if overall_percent >= 50
        else "süreç başlangıç aşamasında; yapılandırma tamamlanmalı"
    )

    return _lines(
        "Süreç Hattı Analizi:",
        f"- Genel hazırlık %{overall_percent}; {total_steps} adımdan {ready_steps} hazır, {attention_steps} dikkat, {missing_steps} eksik.",
        f"- İlerleme yorumu: {progress_text}.",
        f"- Tıkanma değerlendirmesi ({urgency} risk): {bottleneck}.",
        "Öncelik Sırası:",
        (
            "- Önce eksik adımları tamamlayın (endpoint, şablon, DB tablosu kontrolü yapın)."
            if missing_steps > 0
            else "- Dikkat gerektiren adımları bu hafta içinde gözden geçirin."
        ),
        "- Her adımın bağımsız çalıştığını doğruladıktan sonra uçtan uca test yapın.",
        "- Bu analiz AI kural motoru çıktısıdır; nihai karar proje yöneticisindedir.",
    )


# ═══════════════════════════════════════════════════════════════════
# 5. GELİŞİM REHBERİ — P4/Faz10 kişiselleştirilmiş öneri
# ═══════════════════════════════════════════════════════════════════
def _build_development_guidance(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    employee_name   = _text((payload.get("employee") or {}).get("full_name"), "Personel")
    score           = _safe_float(payload.get("score"))
    category_label  = _text(payload.get("category_label"), "Genel")
    weak_criteria   = list(payload.get("weak_criteria") or [])
    strong_criteria = list(payload.get("strong_criteria") or [])
    existing_notes  = _safe_int(payload.get("existing_guidance_count"))

    if score <= 0:
        return _lines(
            "Gelişim Rehberi:",
            f"- {employee_name} için puan bilgisi mevcut değil; gelişim önerisi üretilemiyor.",
            "Öneri:",
            "- Değerlendirme tamamlandıktan sonra bu ekranı yenileyin.",
        )

    # Segment
    if score < 60:
        segment    = "kritik gelişim"
        focus_note = "temel yetkinliklerde sistematik destek programı başlatılmalı"
    elif score < 70:
        segment    = "gelişim odaklı"
        focus_note = "zayıf kriterlerde yönetici desteği ve periyodik kontrol planlanmalı"
    elif score < 85:
        segment    = "gelişim potansiyeli olan"
        focus_note = "güçlü yönler korunurken orta bant kriterler yükseltilmeli"
    else:
        segment    = "yüksek performanslı"
        focus_note = "güçlü yönler öne çıkarılmalı; mentorluk ve kariyer rotası konuşulabilir"

    weak_text  = (", ".join(str(c) for c in weak_criteria[:3]) if weak_criteria  else "belirlenmiş zayıf kriter yok")
    strong_text = (", ".join(str(c) for c in strong_criteria[:3]) if strong_criteria else "belirlenmiş güçlü kriter yok")

    note_status = (
        f"{existing_notes} gelişim notu zaten mevcut; yenilerini bunlarla uyumlu tutun"
        if existing_notes > 0
        else "henüz gelişim notu girilmemiş; ilk taslak olarak aşağıdakiler kullanılabilir"
    )

    return _lines(
        f"Gelişim Rehberi — {employee_name} / {category_label}:",
        f"- Segment: {segment} ({score:.0f} puan). Odak: {focus_note}.",
        f"- Güçlü yönler: {strong_text}.",
        f"- Gelişim alanları: {weak_text}.",
        f"- Not durumu: {note_status}.",
        "Önerilen 3 Adım:",
        f"- 1. {weak_criteria[0] if weak_criteria else 'Tespit edilen zayıf kriter'} için somut eylem planı oluşturun.",
        "- 2. Bir sonraki görüşmede ilerlemeyi ölçün ve notları güncelleyin.",
        "- 3. Güçlü yönleri kurumsal tanıma veya mentorluk kapsamında değerlendirin.",
        "- Bu rehber AI kural motoru çıktısıdır; nihai karar yöneticidedir.",
    )


# ═══════════════════════════════════════════════════════════════════
# 6. SÜREÇ TAKİP VE RAPORLAR — risk ve gecikme analizi
# ═══════════════════════════════════════════════════════════════════
def _build_process_tracking(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    total_flows    = _safe_int(payload.get("total_flows"))
    overdue_flows  = _safe_int(payload.get("overdue_flows"))
    pending_flows  = _safe_int(payload.get("pending_flows"))
    completed      = _safe_int(payload.get("completed_flows"))
    president_wait = _safe_int(payload.get("president_pending"))
    period_title   = _text(payload.get("period_title"), "aktif dönem")

    if total_flows == 0:
        return _lines(
            "Süreç Takip Analizi:",
            f"- {period_title} için aktif süreç akışı bulunmuyor.",
            "Öneri:",
            "- Performans atamaları oluşturulduktan sonra bu ekran otomatik dolar.",
        )

    completion_rate = (completed / total_flows * 100) if total_flows > 0 else 0.0

    risk_text = (
        f"{overdue_flows} gecikmiş akış kritik; derhal müdahale gerekiyor"
        if overdue_flows >= 3
        else f"{overdue_flows} gecikmiş akış var; bu hafta içinde kapatılmalı"
        if overdue_flows > 0
        else "gecikmiş akış yok; süreç zamanında ilerliyor"
    )

    president_text = (
        f"{president_wait} akış başkan/üst onayı bekliyor; onay gecikirse yayın kilidi devam eder"
        if president_wait > 0
        else "başkan/üst onay beklentisi yok; onay kanalı temiz"
    )

    return _lines(
        f"Süreç Takip Analizi — {period_title}:",
        f"- Toplam {total_flows} akıştan {completed} tamamlandı (%{completion_rate:.0f}), {pending_flows} devam ediyor.",
        f"- Risk: {risk_text}.",
        f"- Onay kanalı: {president_text}.",
        "Öncelikli Aksiyonlar:",
        (
            "- Gecikmiş akışların sorumlu yöneticilerini bilgilendirin; bitiş tarihlerini güncelleyin."
            if overdue_flows > 0
            else "- Devam eden akışları haftalık gözden geçirin; tamamlananları kapatın."
        ),
        (
            "- Başkan onayı bekleyen akışlar için yönetici hatırlatması gönderin."
            if president_wait > 0
            else "- Onay kanalı açık; onay gerekenler zamanında işleniyor."
        ),
        "- Bu analiz AI kural motoru çıktısıdır; aksiyon kararı yöneticidedir.",
    )


# ═══════════════════════════════════════════════════════════════════
# 7. GEÇMİŞ KARNE ARŞİVİ — tarihsel trend analizi
# ═══════════════════════════════════════════════════════════════════
def _build_archive_trend(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    employee_name = _text((payload.get("employee") or {}).get("full_name"), "Personel")
    records       = list(payload.get("archive_records") or [])
    period_count  = len(records)

    if period_count == 0:
        return _lines(
            "Tarihsel Trend Analizi:",
            f"- {employee_name} için arşiv kaydı bulunmuyor.",
            "Öneri:",
            "- Geçmiş dönem verileri arşive aktarıldıktan sonra bu ekran trend analizi sunar.",
        )

    scores = [_safe_float(r.get("score") or r.get("final_total")) for r in records if r]
    scores = [s for s in scores if s > 0]

    if len(scores) < 2:
        last_score = scores[0] if scores else 0
        return _lines(
            f"Tarihsel Trend Analizi — {employee_name}:",
            f"- {period_count} dönem kaydı mevcut; trend analizi için en az 2 dönem gerekiyor.",
            f"- Mevcut puan: {last_score:.0f}.",
            "Öneri:",
            "- Bir sonraki dönem tamamlandığında trend analizi otomatik güncellenir.",
        )

    first_score = scores[-1]   # en eski
    last_score  = scores[0]    # en yeni
    avg_score   = sum(scores) / len(scores)
    delta       = last_score - first_score
    max_score   = max(scores)
    min_score   = min(scores)

    if delta > 10:
        trend = "belirgin yükseliş trendi"
        trend_note = "Güçlü gelişim seyri; devam ettirici destekle kariyer rotası konuşulabilir."
    elif delta > 3:
        trend = "hafif yükseliş trendi"
        trend_note = "Kademeli gelişim var; mevcut destek yöntemlerini sürdürün."
    elif delta < -10:
        trend = "belirgin düşüş trendi"
        trend_note = "Kritik düşüş; nedenler analiz edilmeli, destek planı başlatılmalı."
    elif delta < -3:
        trend = "hafif düşüş trendi"
        trend_note = "Dikkat gerektiren eğilim; yönetici periyodik kontrol artırmalı."
    else:
        trend = "stabil seyir"
        trend_note = "Tutarlı performans; güçlü yönler korunuyor."

    return _lines(
        f"Tarihsel Trend Analizi — {employee_name} ({period_count} dönem):",
        f"- Ortalama puan: {avg_score:.1f} | En yüksek: {max_score:.0f} | En düşük: {min_score:.0f}.",
        f"- Trend: {trend} (ilk dönem {first_score:.0f} → son dönem {last_score:.0f}, fark {delta:+.0f}).",
        f"- Yorum: {trend_note}",
        "Yönetici Önerisi:",
        (
            "- Düşüş nedenlerini bireysel görüşmede ele alın; gelişim planını güncelle."
            if delta < -3
            else "- Yükseliş dinamiklerini koruyun; başarıyı ekiple paylaşın." if delta > 3
            else "- Stabil seyri sürdürün; periyodik kontrol ve geri bildirim yeterli."
        ),
        "- Bu analiz AI kural motoru çıktısıdır; kariyer kararı yönetim ve İK'dadır.",
    )


# ═══════════════════════════════════════════════════════════════════
# 8. İZİN / HR — sayfaya bağlı leave_brief genişletme
# ═══════════════════════════════════════════════════════════════════
def _build_hr_leave_detail(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    """Leave_brief'in daha detaylı versiyonu — HR sayfasındaki widget için."""
    if not isinstance(payload, dict):
        return _build_generic_response(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)

    pending        = _safe_int(payload.get("pending_count"))
    approved       = _safe_int(payload.get("approved_count"))
    rejected       = _safe_int(payload.get("rejected_count"))
    _safe_int(payload.get("delegation_ok"))
    delegation_gap = _safe_int(payload.get("delegation_gap"))
    department     = _text(payload.get("department"), "birim")
    period_title   = _text(payload.get("period_title"), "aktif dönem")

    total = pending + approved + rejected
    if total == 0:
        return _lines(
            "İzin Yönetimi Analizi:",
            f"- {department} için {period_title} döneminde izin kaydı bulunmuyor.",
        )

    approval_rate = (approved / total * 100) if total > 0 else 0.0

    coverage_text = (
        f"{delegation_gap} izin kaydında vekâlet ataması eksik; kritik görev akışı risk altında"
        if delegation_gap > 0
        else "tüm izinler için vekâlet ataması tamamlanmış; kapsama sağlam"
    )

    urgency_text = (
        f"{pending} bekleyen talep; onay gecikmesi departman planlamasını etkileyebilir"
        if pending > 3
        else f"{pending} bekleyen talep; normal operasyon içinde" if pending > 0
        else "bekleyen onay talebi yok; kuyruk temiz"
    )

    return _lines(
        f"İzin Yönetimi Analizi — {department} / {period_title}:",
        f"- Toplam {total} kayıt: {approved} onaylı (%{approval_rate:.0f}), {pending} beklemede, {rejected} reddedildi.",
        f"- Kapsama: {coverage_text}.",
        f"- Onay kuyruğu: {urgency_text}.",
        "Aksiyon Önerisi:",
        (
            "- Vekâletsiz izin kayıtlarını bugün tamamlayın; görev akışı kopukluğu önlensin."
            if delegation_gap > 0
            else "- Bekleyen talepleri haftalık döngüde onaylayın."
        ),
        "- Bu analiz AI kural motoru çıktısıdır; izin kararı yöneticidedir.",
    )


# ═══════════════════════════════════════════════════════════════════
# Genel fallback (mevcut stub_engine.py'deki ile aynı)
# ═══════════════════════════════════════════════════════════════════
def _build_generic_response(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    return _lines(
        "Özet:",
        "- AI servisi kontrollü gelişim stub modunda çalışıyor ve güvenli bir kurumsal cevap üretti.",
        "- Bu senaryo için özel kural motoru tanımlanmışsa üstten, değilse varsayılan karar destek notu olarak yorumlanmalıdır.",
        "Not:",
        "- Nihai işlem ve onay yetkisi her zaman ilgili kullanıcı ve yönetici rollerinde kalır.",
    )


# ═══════════════════════════════════════════════════════════════════
# SENARYOLAR ve BUILDER KAYDEDME (stub_engine.py'ye eklenecek)
# ═══════════════════════════════════════════════════════════════════

NEW_STUB_SCENARIOS = (
    ("performance", "aftercare_coaching"),
    ("performance", "interim_notes_pattern"),
    ("performance", "followup_risk"),
    ("performance", "pipeline_status"),
    ("performance", "development_guidance"),
    ("performance", "process_tracking"),
    ("performance", "archive_trend"),
    ("hr", "leave_detail"),
)

NEW_SCENARIO_BUILDERS = {
    ("performance", "aftercare_coaching"):   _build_aftercare_coaching,
    ("performance", "interim_notes_pattern"): _build_interim_notes_pattern,
    ("performance", "followup_risk"):        _build_followup_risk,
    ("performance", "pipeline_status"):      _build_pipeline_status,
    ("performance", "development_guidance"): _build_development_guidance,
    ("performance", "process_tracking"):     _build_process_tracking,
    ("performance", "archive_trend"):        _build_archive_trend,
    ("hr", "leave_detail"):                  _build_hr_leave_detail,
}

NEW_SCENARIO_HINTS = {
    ("performance", "aftercare_coaching"):   ["görüşme sonrası", "koçluk", "aftercare"],
    ("performance", "interim_notes_pattern"):["dönem içi not", "pattern", "gözlem analizi"],
    ("performance", "followup_risk"):        ["eylem planı takibi", "gecikme riski", "followup"],
    ("performance", "pipeline_status"):      ["süreç hattı", "pipeline", "tıkanma"],
    ("performance", "development_guidance"): ["gelişim rehberi", "öneri", "faz10"],
    ("performance", "process_tracking"):     ["süreç takip", "akış analizi", "gecikmiş akış"],
    ("performance", "archive_trend"):        ["arşiv trend", "tarihsel", "dönem karşılaştırma"],
    ("hr", "leave_detail"):                  ["izin detay", "vekâlet kapsama", "izin kuyruğu"],
}
