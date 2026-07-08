# BYS360 Message Interactions V1 Teknik Not

## Amaç

Mesajlaşma ekranını daha akıcı hale getirmek:

- Tepki: kullanıcı mesajlara beğen/beğenme ve diğer kısa tepkileri verebilir.
- AJAX mesaj gönderimi: mesaj gönderildiğinde tam sayfa yenilenmez.
- Yorum: mesajın altında kısa yorum akışı tutulur.

## Değişen ana dosyalar

- `app/models/communication_models.py`
- `app/models/__init__.py`
- `app/schema_guard_core_maintenances.py`
- `app/services/messages/constants.py`
- `app/services/messages/comments.py`
- `app/services/messages/serialization.py`
- `app/services/messages/__init__.py`
- `app/communication/messages_routes.py`
- `app/templates/messages_inbox.html`
- `app/templates/messages_thread.html`
- `app/static/js/messages_messenger_mobile.js`
- `app/static/css/messages_messenger_mobile.css`

## Yeni tablo

`message_comments`

Alanlar:

- `id`
- `message_id`
- `user_id`
- `body`
- `is_deleted`
- `edited_at`
- `created_at`
- `updated_at`

## Güvenlik

Yorum ve tepki yalnızca konuşma katılımcıları tarafından yapılabilir. Yetkisiz kullanıcılar endpoint'e doğrudan erişse bile 403 alır.
