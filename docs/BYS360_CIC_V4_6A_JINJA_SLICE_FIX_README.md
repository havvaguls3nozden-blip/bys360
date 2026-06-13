# BYS360_CIC_V4_6A_JINJA_SLICE_FIX

V4.6 Kutlamalar tasarım şablonunda Jinja'nın filtre sonrası liste dilimleme ifadesinden kaynaklanan 500 hatasını düzeltir.

Düzeltme:
- `_c.upcoming_birthdays|default([], true)[:8]` → `(_c.upcoming_birthdays|default([], true))[:8]`
- Aynı düzeltme hizmet yılı ve özel gün listeleri için de uygulanır.
- V4.6 repair scripti de yamalanır; V4.6 tekrar çalıştırılırsa aynı hata geri gelmez.
