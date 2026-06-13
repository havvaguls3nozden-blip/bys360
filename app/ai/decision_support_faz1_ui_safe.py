# -*- coding: utf-8 -*-
"""BYS360 Karar Destek Merkezi Faz 1 bağımsız kurumsal ekranı."""
from __future__ import annotations

from html import escape
from typing import Any


def build_faz1_health_response(payload: dict[str, Any] | None) -> str:
    """Base template'e bağlı kalmadan beyaz ekran riskini azaltan HTML üretir."""
    payload = payload or {}
    policy = payload.get("policy", {}) if isinstance(payload, dict) else {}
    is_ready = bool(payload.get("ok")) if isinstance(payload, dict) else False

    def enabled(*names: str) -> bool:
        if not isinstance(policy, dict):
            return False
        return any(bool(policy.get(name)) for name in names)

    def text_value(value: Any, fallback: Any) -> str:
        return escape(str(fallback if value in (None, "") else value))

    low_score = text_value(policy.get("low_score_threshold") if isinstance(policy, dict) else None, 70)
    high_score = text_value(policy.get("high_score_threshold") if isinstance(policy, dict) else None, 90)
    status_title = "Merkez hazır" if is_ready else "Kontrol gerekli"
    status_note = (
        "Karar destek kontrolleri güvenli kullanım için hazır."
        if is_ready
        else "Kurumsal ekran açıldı; arka plan kontrolü ayrıca incelenebilir."
    )

    controls = [
        (
            "Düşük performansta üst onay",
            "70 altı sonuçlarda yetkili üst onay süreci öne çıkarılır; sonuç doğrudan kesinleşmiş sayılmaz.",
            enabled("low_score_requires_upper_approval", "president_approval_required", "requires_president_approval"),
        ),
        (
            "Yayın öncesi koruma",
            "Onay gerektiren düşük performans sonucu süreç tamamlanmadan personele açılmaz.",
            enabled("publish_lock_for_low_score", "low_score_publish_lock", "publish_lock_enabled"),
        ),
        (
            "Gerekçeli değerlendirme",
            "1 ve 5 puanlarda açıklama istenmesi sistem ayarlarına göre yönetilir.",
            enabled("require_comment_for_score_1", "require_comment_for_score_5", "score_1_comment_required", "score_5_comment_required"),
        ),
        (
            "Eşik dışı sonuçlarda genel görüş",
            "Düşük veya çok yüksek performans sonucunda ayrıntılı kanaat kontrolü yapılır.",
            enabled("require_general_comment_below_low", "require_general_comment_above_high", "general_comment_required"),
        ),
    ]

    control_rows = "".join(
        f"""
        <article class=\"control-row\">
          <div>
            <strong>{escape(title)}</strong>
            <p>{escape(desc)}</p>
          </div>
          <span class=\"pill {'active' if active else 'passive'}\">{'Aktif' if active else 'Kontrol edilecek'}</span>
        </article>
        """
        for title, desc, active in controls
    )

    dot_bg = "#267347" if is_ready else "#b56a00"
    dot_shadow = "rgba(38,115,71,.14)" if is_ready else "rgba(181,106,0,.14)"

    return f"""<!doctype html>
<html lang=\"tr\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Karar Destek Merkezi</title>
  <style>
    :root {{ --red:#8B0000; --red-dark:#5f0000; --ink:#251917; --muted:#6f615c; --line:rgba(139,0,0,.16); --soft:rgba(139,0,0,.08); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; font-family:Inter, Segoe UI, Arial, sans-serif; color:var(--ink); background:radial-gradient(circle at top left, rgba(139,0,0,.12), transparent 32%), linear-gradient(135deg,#fff8f4,#f7f1ec 52%,#fff); }}
    .page {{ max-width:1180px; margin:0 auto; padding:32px 18px 48px; }}
    .topline {{ display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:18px; }}
    .brand {{ display:flex; align-items:center; gap:12px; font-weight:900; color:var(--red); letter-spacing:.02em; }}
    .brand-mark {{ width:42px; height:42px; border-radius:16px; display:grid; place-items:center; color:#fff; background:linear-gradient(145deg,var(--red),var(--red-dark)); box-shadow:0 14px 28px rgba(139,0,0,.22); }}
    .safe-note {{ padding:10px 14px; border-radius:999px; background:rgba(255,255,255,.78); border:1px solid var(--line); color:var(--muted); font-size:.92rem; }}
    .hero {{ position:relative; overflow:hidden; display:grid; grid-template-columns:minmax(0,1fr) 290px; gap:24px; min-height:330px; padding:36px; border-radius:34px; background:rgba(255,255,255,.84); border:1px solid var(--line); box-shadow:0 24px 60px rgba(82,38,28,.13); backdrop-filter:blur(16px); }}
    .hero:before {{ content:\"\"; position:absolute; width:330px; height:330px; left:-90px; top:-90px; border-radius:999px; background:radial-gradient(circle, rgba(139,0,0,.20), transparent 68%); }}
    .hero-content {{ position:relative; z-index:1; }}
    .eyebrow {{ margin:0 0 10px; color:var(--red); text-transform:uppercase; letter-spacing:.13em; font-size:.78rem; font-weight:900; }}
    h1 {{ max-width:790px; margin:0; font-size:clamp(2.15rem,4.6vw,3.75rem); line-height:1.04; letter-spacing:-.055em; }}
    .lead {{ max-width:790px; margin:18px 0 0; color:var(--muted); font-size:1.08rem; line-height:1.72; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:28px; }}
    .btn {{ display:inline-flex; align-items:center; justify-content:center; min-height:46px; padding:0 18px; border-radius:999px; text-decoration:none; font-weight:900; }}
    .btn.primary {{ color:#fff; background:linear-gradient(135deg,var(--red),var(--red-dark)); box-shadow:0 14px 28px rgba(139,0,0,.22); }}
    .btn.secondary {{ color:var(--red); border:1px solid var(--line); background:rgba(255,255,255,.78); }}
    .status {{ align-self:end; position:relative; z-index:1; padding:24px; border-radius:26px; background:rgba(255,255,255,.76); border:1px solid var(--line); box-shadow:inset 0 1px 0 rgba(255,255,255,.8); }}
    .dot {{ display:inline-flex; width:18px; height:18px; border-radius:50%; background:{dot_bg}; box-shadow:0 0 0 8px {dot_shadow}; }}
    .status strong {{ display:block; margin-top:20px; font-size:1.25rem; }}
    .status p {{ margin:8px 0 0; color:var(--muted); line-height:1.6; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-top:18px; }}
    .card {{ min-height:210px; padding:22px; border-radius:26px; background:rgba(255,255,255,.82); border:1px solid var(--line); box-shadow:0 16px 36px rgba(82,38,28,.08); }}
    .card.strong {{ color:#fff; background:linear-gradient(145deg,rgba(139,0,0,.96),rgba(92,0,0,.95)); }}
    .icon {{ width:42px; height:42px; display:grid; place-items:center; margin-bottom:18px; border-radius:16px; color:var(--red); background:var(--soft); font-weight:900; }}
    .card.strong .icon {{ color:#fff; background:rgba(255,255,255,.16); }}
    h2 {{ margin:0; font-size:1.13rem; letter-spacing:-.02em; }}
    .card p, .section p {{ color:var(--muted); line-height:1.64; }}
    .card.strong p {{ color:rgba(255,255,255,.86); }}
    .section {{ margin-top:18px; padding:28px; border-radius:30px; background:rgba(255,255,255,.84); border:1px solid var(--line); box-shadow:0 18px 42px rgba(82,38,28,.09); }}
    .section-head {{ display:grid; gap:6px; margin-bottom:20px; }}
    .section-head span {{ color:var(--muted); line-height:1.6; }}
    .control-list {{ display:grid; gap:12px; }}
    .control-row {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:16px; align-items:center; padding:18px; border-radius:20px; background:rgba(255,255,255,.74); border:1px solid rgba(139,0,0,.10); }}
    .control-row strong {{ display:block; }}
    .control-row p {{ margin:6px 0 0; }}
    .pill {{ display:inline-flex; align-items:center; justify-content:center; min-width:116px; min-height:34px; padding:0 12px; border-radius:999px; font-size:.83rem; font-weight:900; }}
    .pill.active {{ color:#1f6840; background:rgba(39,117,71,.12); border:1px solid rgba(39,117,71,.20); }}
    .pill.passive {{ color:#8a5b00; background:rgba(181,106,0,.12); border:1px solid rgba(181,106,0,.20); }}
    .bottom {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; margin-top:18px; }}
    .bottom .section {{ margin-top:0; }}
    @media (max-width:980px) {{ .hero,.bottom {{ grid-template-columns:1fr; }} .cards {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .status {{ align-self:stretch; }} }}
    @media (max-width:640px) {{ .page {{ padding:18px 10px 36px; }} .topline {{ align-items:flex-start; flex-direction:column; }} .hero,.section,.card {{ border-radius:22px; padding:22px; }} .cards,.bottom,.control-row {{ grid-template-columns:1fr; }} .actions .btn {{ width:100%; }} }}
  </style>
</head>
<body>
  <main class=\"page\">
    <div class=\"topline\">
      <div class=\"brand\"><span class=\"brand-mark\">B</span><span>BYS360 Karar Destek Merkezi</span></div>
      <div class=\"safe-note\">Güvenli kullanım • İnsan onayı • Yetki sınırı</div>
    </div>

    <section class=\"hero\" aria-labelledby=\"title\">
      <div class=\"hero-content\">
        <p class=\"eyebrow\">Yönetici karar destek alanı</p>
        <h1 id=\"title\">Yönetim kararlarını güçlendiren güvenli analiz merkezi</h1>
        <p class=\"lead\">Performans verileri, açıklama gereklilikleri ve üst onay ihtiyacı tek bakışta anlaşılır hale getirilir. Bu alan karar vermez; yetkili kullanıcıya değerlendirme öncesi güvenli destek sunar.</p>
        <div class=\"actions\">
          <a class=\"btn primary\" href=\"/performance/dashboard\">Yönetici görünümüne geç</a>
          <a class=\"btn secondary\" href=\"/performance/reports\">Performans raporlarını aç</a>
        </div>
      </div>
      <aside class=\"status\" aria-label=\"Merkez durumu\">
        <span class=\"dot\"></span>
        <strong>{escape(status_title)}</strong>
        <p>{escape(status_note)}</p>
      </aside>
    </section>

    <section class=\"cards\" aria-label=\"Karar destek ilkeleri\">
      <article class=\"card strong\"><span class=\"icon\">✓</span><h2>İnsan onayı esastır</h2><p>Üretilen notlar yöneticinin değerlendirmesine yardımcı olur; nihai idari karar yetkili kişidedir.</p></article>
      <article class=\"card\"><span class=\"icon\">↘</span><h2>Düşük performans görünürlüğü</h2><p>{low_score} puanın altındaki sonuçlarda üst onay ihtiyacı görünür hale getirilir.</p></article>
      <article class=\"card\"><span class=\"icon\">★</span><h2>Yüksek başarı gerekçesi</h2><p>{high_score} puanın üzerindeki sonuçlarda ayrıntılı genel görüş kontrolü desteklenir.</p></article>
      <article class=\"card\"><span class=\"icon\">⌁</span><h2>Yayın koruması</h2><p>Onay süreci tamamlanmadan personel sonucunun açılması engellenir.</p></article>
    </section>

    <section class=\"section\">
      <div class=\"section-head\">
        <p class=\"eyebrow\">Canlı kullanım özeti</p>
        <h2>Kurumsal kontrol başlıkları</h2>
        <span>Bu başlıklar, karar destek alanının hangi kurumsal güvenceyle çalıştığını sade şekilde gösterir.</span>
      </div>
      <div class=\"control-list\">{control_rows}</div>
    </section>

    <section class=\"bottom\">
      <article class=\"section\"><p class=\"eyebrow\">Yönetici notu</p><h2>Bu ekranın anlamı</h2><p>Karar Destek Merkezi; performans sürecinde dikkat edilmesi gereken eşikleri, onay ihtiyaçlarını ve yayın korumasını sade bir dille gösterir. Kişisel karar vermez, otomatik idari işlem oluşturmaz.</p></article>
      <article class=\"section\"><p class=\"eyebrow\">Güvenli kullanım</p><h2>Veri sınırı korunur</h2><p>Kullanıcı yalnızca yetkisi kapsamındaki özetleri görür. Hassas içerik, kişisel veri ve mahrem değerlendirme ayrıntıları bu alanda açık biçimde sunulmaz.</p></article>
    </section>
  </main>
</body>
</html>"""
