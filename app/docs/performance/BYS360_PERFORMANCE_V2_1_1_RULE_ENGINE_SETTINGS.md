# BYS360 Performans Yönetimi V2.1.1 — Kural Motoru ve Ayar Merkezi

## Amaç

V2.1.1, Performans Yönetimi V2.1 uygulama programının ilk teknik paketidir. Bu aşamada performans kuralları tek merkezden okunur ve ayarlanabilir hale getirilir.

## Merkezi ayarlar

| Ayar anahtarı | Varsayılan | Açıklama |
|---|---:|---|
| `require_criterion_comment_for_score_1_5` | `true` | 1 ve 5 puanlarda kriter açıklaması zorunluluğu. |
| `require_general_comment_below_70` | `true` | Nihai puan 70 altıysa genel görüş zorunluluğu. |
| `require_general_comment_above_90` | `true` | Nihai puan 90 üstüyse genel görüş zorunluluğu. |
| `low_score_threshold` | `70` | Düşük performans eşiği. |
| `high_score_threshold` | `90` | Çok başarılı performans eşiği. |
| `require_president_approval_below_70` | `true` | 70 altı sonucu Başkan/Üst Onay'a düşürme. |
| `block_publish_until_president_approval` | `true` | Başkan/Üst Onay tamamlanmadan personel yayını engelleme. |
| `require_personnel_support_publish_preapproval` | `true` | Final yayından önce Personel ve Destek Hizmetleri Grup Başkanı ön onayı. |
| `third_supervisor_default_mode` | `comment_only` | 3. amir varsayılan modu. |
| `technical_status_localization_enabled` | `true` | Teknik statüleri Türkçe kurumsal etikete çevirme. |

## Canlıya geçiş kontrolü

1. `python -m compileall app scripts` hatasız çalışmalı.
2. `module_settings` içinde `performance` modülü için V2.1.1 anahtarları görünmeli.
3. `/performance/v2-1-1-rule-settings` ekranı Admin/Sistem Yöneticisiyle açılmalı.
4. 70 altı sonuç için yayın kilidi kuralı aktif görünmeli.
5. 1/5 açıklama ayarı ekrandan aç/kapat yapılabilmeli.
6. Teknik statüler kullanıcıya `president_pending` gibi kodlarla değil Türkçe ifadelerle dönmeli.

## Rollback

Bu paket mevcut veri şemasını değiştirmez. Geri almak için:

- Overlay ile gelen yeni dosyalar silinebilir.
- `module_settings` içindeki V2.1.1 ayarları pasife alınabilir.
- Scriptin oluşturduğu `.bak_v2_1_1_*` yedeklerinden `app/performance/__init__.py` geri döndürülebilir.
