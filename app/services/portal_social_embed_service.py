# -*- coding: utf-8 -*-
"""BYS360 Portal V3B5 Kurumsal sosyal medya otomatik takip, normal portal paylaşımı ve uygulama içi otomatik görev durumu servisi.

Canlı ilke:
- Sosyal medya ayrı vitrin/kart olarak gösterilmez.
- Bulunan X/Instagram gönderi bağlantıları normal portal gönderisi olarak yayın akışına düşer.
- API'siz ortamda profil kontrolü en iyi çaba (best-effort) şeklindedir; manuel ön tarama + bekleyenleri yayınla + zamanlanmış otomatik yayın akışı desteklenir.
"""
from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import current_app

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import PortalPost, PortalPostAttachment, User
from app.route_support import sanitize_free_text

SUPPORTED_X_HOSTS = {'x.com', 'twitter.com', 'mobile.twitter.com'}
SUPPORTED_INSTAGRAM_HOSTS = {'instagram.com', 'www.instagram.com'}
DEFAULT_X_ACCOUNTS = {'tarihialan'}
DEFAULT_INSTAGRAM_ACCOUNTS = {'tarihialanbaskanligi', 'casamer_tarihialan'}
PROFILE_FETCH_TIMEOUT = 10


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _safe_html_attr(value: Any) -> str:
    return html.escape(str(value or ''), quote=True)


def _tr_lower(value: Any) -> str:
    text = str(value or '')
    text = text.replace('İ', 'i').replace('I', 'ı').lower()
    return text.translate(str.maketrans({'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'}))


def _data_dir() -> Path:
    try:
        base = Path(current_app.instance_path) / 'portal'
    except RuntimeError:
        base = Path.cwd() / 'instance' / 'portal'
    base.mkdir(parents=True, exist_ok=True)
    return base


def _queue_path() -> Path:
    return _data_dir() / 'social_media_links_v3b.json'


def _history_path() -> Path:
    return _data_dir() / 'social_media_embed_history_v3b.json'


def _watch_state_path() -> Path:
    return _data_dir() / 'social_media_watch_state_v3b2.json'


def _watch_links_path() -> Path:
    return _data_dir() / 'social_media_watch_links_v3b2.json'


def _report_path() -> Path:
    try:
        base = Path(current_app.root_path).parent / 'reports' / 'portal'
    except RuntimeError:
        base = Path.cwd() / 'reports' / 'portal'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'BYS360_SOCIAL_MEDIA_AUTO_IMPORT_V3B4_LAST_REPORT.json'


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default
    return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def allowed_x_accounts() -> set[str]:
    raw = os.getenv('BYS360_SOCIAL_X_ACCOUNTS', '').strip()
    if raw:
        return {_tr_lower(x.strip().lstrip('@')) for x in raw.replace(',', '|').split('|') if x.strip()}
    return set(DEFAULT_X_ACCOUNTS)


def allowed_instagram_accounts() -> set[str]:
    raw = os.getenv('BYS360_SOCIAL_INSTAGRAM_ACCOUNTS', '').strip()
    if raw:
        return {_tr_lower(x.strip().lstrip('@')) for x in raw.replace(',', '|').split('|') if x.strip()}
    return set(DEFAULT_INSTAGRAM_ACCOUNTS)


def watch_sources() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for account in sorted(allowed_x_accounts()):
        items.append({'platform': 'x', 'account': account, 'profile_url': f'https://x.com/{account}'})
    for account in sorted(allowed_instagram_accounts()):
        items.append({'platform': 'instagram', 'account': account, 'profile_url': f'https://www.instagram.com/{account}/'})
    return items


def canonical_social_url(raw_url: str) -> dict[str, Any]:
    raw = sanitize_free_text(raw_url, limit=1000)
    if not raw:
        return {'ok': False, 'reason': 'Boş bağlantı'}
    try:
        parsed = urllib.parse.urlparse(raw)
    except Exception:
        return {'ok': False, 'reason': 'Bağlantı okunamadı'}
    if parsed.scheme not in {'http', 'https'}:
        return {'ok': False, 'reason': 'Bağlantı http/https olmalıdır'}
    host = (parsed.netloc or '').lower().replace('www.', '')
    path_parts = [p for p in (parsed.path or '').strip('/').split('/') if p]
    if host in SUPPORTED_X_HOSTS:
        if len(path_parts) >= 3 and path_parts[1].lower() in {'status', 'statuses'} and re.fullmatch(r'\d{6,30}', path_parts[2] or ''):
            account = _tr_lower(path_parts[0].lstrip('@'))
            if account not in allowed_x_accounts():
                return {'ok': False, 'reason': f'X hesabı izinli listede değil: @{account}'}
            return {'ok': True, 'platform': 'x', 'account': account, 'post_id': path_parts[2], 'url': f'https://x.com/{account}/status/{path_parts[2]}'}
        return {'ok': False, 'reason': 'X için tekil gönderi bağlantısı gerekir: https://x.com/TarihiAlan/status/...'}
    if host in SUPPORTED_INSTAGRAM_HOSTS:
        if len(path_parts) >= 2 and path_parts[0].lower() in {'p', 'reel', 'tv'} and re.fullmatch(r'[A-Za-z0-9_-]{5,80}', path_parts[1] or ''):
            kind = path_parts[0].lower(); shortcode = path_parts[1]
            return {'ok': True, 'platform': 'instagram', 'account': '', 'post_id': shortcode, 'kind': kind, 'url': f'https://www.instagram.com/{kind}/{shortcode}/'}
        return {'ok': False, 'reason': 'Instagram için tekil gönderi/reels bağlantısı gerekir: https://www.instagram.com/p/.../'}
    return {'ok': False, 'reason': 'Sadece X veya Instagram gönderi bağlantısı desteklenir'}


def _fetch_url(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; BYS360SocialWatch/3.2; +https://bys360.local)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.7',
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=PROFILE_FETCH_TIMEOUT) as resp:
        raw = resp.read(1200000)
    return raw.decode('utf-8', errors='replace')


def _extract_x_status_urls(html_text: str, account: str) -> list[str]:
    urls: list[str] = []
    account_re = re.escape(account)
    patterns = [
        rf'https?://(?:www\.)?(?:x|twitter)\.com/{account_re}/status/(\d{{6,30}})',
        rf'/(?:{account_re})/status/(\d{{6,30}})',
        rf'\\/{account_re}\\/status\\/(\d{{6,30}})',
    ]
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, html_text, flags=re.I):
            post_id = match.group(1)
            url = f'https://x.com/{account}/status/{post_id}'
            if url not in seen:
                seen.add(url); urls.append(url)
    return urls[:8]


def _extract_instagram_post_urls(html_text: str, account: str) -> list[str]:
    urls: list[str] = []
    seen = set()
    patterns = [
        r'https?://(?:www\.)?instagram\.com/(p|reel|tv)/([A-Za-z0-9_-]{5,80})/?',
        r'/(p|reel|tv)/([A-Za-z0-9_-]{5,80})/?',
        r'\\/(p|reel|tv)\\/([A-Za-z0-9_-]{5,80})\\/?',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html_text, flags=re.I):
            kind, code = match.group(1).lower(), match.group(2)
            url = f'https://www.instagram.com/{kind}/{code}/'
            if url not in seen:
                seen.add(url); urls.append(url)
    return urls[:8]


def discover_latest_social_links() -> dict[str, Any]:
    """İzinli kurumsal hesaplardan tekil gönderi bağlantısı bulmayı dener.

    Not: API'siz profil kontrolü platform sayfa yapısına bağlıdır. Bulamazsa sistem hata vermez;
    link havuzu/manual ekleme güvenli yedek kanal olarak kalır.
    """
    state = _read_json(_watch_state_path(), {'seen_urls': []})
    seen = set(state.get('seen_urls') or [])
    manual_bank = _read_json(_watch_links_path(), {'links': []})
    discovered: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    # 1) Önceden dosyaya bırakılan kurumsal gömme/link havuzu: API'siz en stabil yedek kanal.
    for item in manual_bank.get('links', []):
        url = item.get('url') if isinstance(item, dict) else str(item)
        parsed = canonical_social_url(url)
        if parsed.get('ok') and parsed['url'] not in seen:
            discovered.append({'url': parsed['url'], 'platform': parsed['platform'], 'account': parsed.get('account') or item.get('account', '') if isinstance(item, dict) else '', 'source': 'watch_links'})

    # 2) Kurumsal profil sayfasında best-effort link arama.
    for source in watch_sources():
        result = {'platform': source['platform'], 'account': source['account'], 'profile_url': source['profile_url'], 'ok': False, 'found': 0, 'message': ''}
        try:
            html_text = _fetch_url(source['profile_url'])
            if source['platform'] == 'x':
                urls = _extract_x_status_urls(html_text, source['account'])
            else:
                urls = _extract_instagram_post_urls(html_text, source['account'])
            added = 0
            for url in urls:
                parsed = canonical_social_url(url)
                if not parsed.get('ok'):
                    continue
                if parsed['url'] in seen:
                    continue
                discovered.append({'url': parsed['url'], 'platform': parsed['platform'], 'account': source['account'], 'source': 'profile_scan'})
                seen.add(parsed['url']); added += 1
            result.update(ok=True, found=added, message='Kontrol tamamlandı')
        except Exception as exc:
            result.update(ok=False, message=str(exc)[:240])
        findings.append(result)

    # Aynı run içinde tekrarları temizle
    unique: list[dict[str, Any]] = []
    unique_seen = set()
    for item in discovered:
        url = item.get('url') or ''
        if url and url not in unique_seen:
            unique_seen.add(url); unique.append(item)

    state['seen_urls'] = sorted(set(state.get('seen_urls') or []) | unique_seen)
    state['last_run_at'] = _now_iso()
    state['last_findings'] = findings
    _write_json(_watch_state_path(), state)
    return {'ok': True, 'sources': findings, 'discovered': unique, 'discovered_count': len(unique), 'state_path': str(_watch_state_path()), 'generated_at': _now_iso(), 'message': 'Kurumsal hesap kontrolü tamamlandı'}


def _x_oembed_html(url: str) -> str:
    try:
        endpoint = 'https://publish.x.com/oembed?' + urllib.parse.urlencode({'url': url, 'omit_script': 'true', 'dnt': 'true', 'align': 'center'})
        req = urllib.request.Request(endpoint, headers={'User-Agent': 'BYS360/portal-social-embed'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='replace'))
        html_value = str(data.get('html') or '').strip()
        html_value = re.sub(r'<script[^>]*>.*?</script>', '', html_value, flags=re.I | re.S)
        if html_value:
            return html_value
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        pass
    safe_url = _safe_html_attr(url)
    return f'<blockquote class="twitter-tweet" data-dnt="true"><a href="{safe_url}"></a></blockquote>'


def _instagram_embed_html(url: str) -> str:
    safe_url = _safe_html_attr(url)
    return ('<blockquote class="instagram-media" data-instgrm-permalink="' + safe_url + '" '
            'data-instgrm-version="14" style="background:#fff;border:0;border-radius:12px;box-shadow:0 0 1px rgba(0,0,0,.15),0 1px 10px rgba(0,0,0,.08);margin:1px auto;max-width:540px;min-width:280px;padding:0;width:99.375%;"></blockquote>')


def _embed_html(platform: str, url: str) -> str:
    if platform == 'x':
        return _x_oembed_html(url)
    if platform == 'instagram':
        return _instagram_embed_html(url)
    return ''


def _system_author() -> User | None:
    admin = User.query.filter_by(email='bys360@ktb.gov.tr').first()
    if admin:
        return admin
    return User.query.filter(User.role == 'admin').order_by(User.id.asc()).first()


def _existing_post_id(url: str) -> int | None:
    parsed = canonical_social_url(url)
    if not parsed.get('ok'):
        return None
    try:
        row = PortalPostAttachment.query.filter_by(mime_type='text/x-portal-social-url', stored_path=parsed['url']).first()
        return int(row.post_id) if row else None
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None


def publish_social_url_to_portal(raw_url: str, actor: User | None = None, *, source: str = 'manual', auto_commit: bool = True) -> dict[str, Any]:
    parsed = canonical_social_url(raw_url)
    if not parsed.get('ok'):
        return {'ok': False, 'status': 'invalid', 'message': parsed.get('reason') or 'Bağlantı desteklenmedi'}
    url = parsed['url']; platform = parsed['platform']
    existing_id = _existing_post_id(url)
    if existing_id:
        return {'ok': True, 'status': 'duplicate', 'post_id': existing_id, 'message': 'Bu sosyal medya paylaşımı daha önce portala eklenmiş.'}
    author = actor if actor and getattr(actor, 'id', None) else _system_author()
    if not author:
        return {'ok': False, 'status': 'no_author', 'message': 'Portal gönderisi için sistem kullanıcısı bulunamadı.'}

    if platform == 'x':
        title = 'X hesabından paylaşım'
        body = 'Tarihi Alan Başkanlığı X hesabında yayımlanan paylaşım portal akışına eklenmiştir. Paylaşımı aşağıda görüntüleyebilir veya kaynak bağlantısından açabilirsiniz.'
    else:
        title = 'Instagram hesabından paylaşım'
        body = 'Tarihi Alan Başkanlığı ve bağlı hesaplara ait Instagram paylaşımı portal akışına eklenmiştir. Paylaşımı aşağıda görüntüleyebilir veya kaynak bağlantısından açabilirsiniz.'

    post = PortalPost(author_user_id=int(author.id), wall_owner_user_id=int(author.id), title=title, body=body, post_type='normal', visibility_scope='public', status='published', comments_enabled=True, is_pinned=False, is_featured_home=False, published_at=utc_now())
    db.session.add(post); db.session.flush()
    attachments = [
        PortalPostAttachment(post_id=post.id, filename='social-url', stored_path=url, mime_type='text/x-portal-social-url', size_bytes=0, uploaded_by_user_id=author.id),
        PortalPostAttachment(post_id=post.id, filename='social-platform', stored_path=platform, mime_type='text/x-portal-social-platform', size_bytes=0, uploaded_by_user_id=author.id),
        PortalPostAttachment(post_id=post.id, filename='social-source', stored_path=source, mime_type='text/x-portal-social-source', size_bytes=0, uploaded_by_user_id=author.id),
        PortalPostAttachment(post_id=post.id, filename='social-embed', stored_path=_embed_html(platform, url), mime_type='text/x-portal-social-embed', size_bytes=0, uploaded_by_user_id=author.id),
    ]
    account = parsed.get('account') or ''
    if account:
        attachments.append(PortalPostAttachment(post_id=post.id, filename='social-account', stored_path=account, mime_type='text/x-portal-social-account', size_bytes=0, uploaded_by_user_id=author.id))
    for attachment in attachments:
        db.session.add(attachment)
    history = _read_json(_history_path(), {'items': []})
    history.setdefault('items', []).append({'url': url, 'platform': platform, 'post_id': post.id, 'source': source, 'created_at': _now_iso()})
    _write_json(_history_path(), history)
    if auto_commit:
        db.session.commit()
    return {'ok': True, 'status': 'created', 'post_id': int(post.id), 'url': url, 'platform': platform, 'message': 'Sosyal medya paylaşımı portal gönderisi olarak yayınlandı.'}


def queue_social_urls(urls: list[str], *, source: str = 'manual') -> dict[str, Any]:
    current = _read_json(_queue_path(), {'links': []})
    links = current.setdefault('links', [])
    added = []
    existing = {str(item.get('url') or item) for item in links}
    for raw in urls:
        parsed = canonical_social_url(raw)
        if not parsed.get('ok'):
            continue
        if parsed['url'] in existing:
            continue
        item = {'url': parsed['url'], 'platform': parsed['platform'], 'status': 'pending', 'source': source, 'added_at': _now_iso()}
        links.append(item); existing.add(parsed['url']); added.append(item)
    _write_json(_queue_path(), current)
    return {'ok': True, 'added': len(added), 'path': str(_queue_path())}

def discover_and_queue_social_links() -> dict[str, Any]:
    """Kurumsal hesapları kontrol eder, bulunan bağlantıları yalnızca sıraya alır.

    Bu fonksiyon manuel ekrandaki "Önce Tara" akışı içindir. Portal gönderisi oluşturmaz;
    kullanıcı isterse "Bulunanları Yayın Akışına Ekle" butonuyla bekleyenleri paylaşır.
    Zamanlanmış görev ise run_social_embed_scan(auto_discover=True) ile otomatik yayın yapabilir.
    """
    discovery = discover_latest_social_links()
    urls = [item.get('url') for item in discovery.get('discovered', []) if item.get('url')]
    queued = queue_social_urls(urls, source='profile_scan') if urls else {'ok': True, 'added': 0}
    report = {
        'ok': True,
        'mode': 'discover_only',
        'created': 0,
        'duplicate': 0,
        'failed': 0,
        'invalid': 0,
        'queued': queued.get('added', 0),
        'discovery': discovery,
        'generated_at': _now_iso(),
        'message': 'Kurumsal hesaplar kontrol edildi. Bulunan bağlantılar bekleyenler listesine alındı.'
    }
    _write_json(_report_path(), report)
    return report


def social_import_context() -> dict[str, Any]:
    queue = _read_json(_queue_path(), {'links': []})
    history = _read_json(_history_path(), {'items': []})
    state = _read_json(_watch_state_path(), {'seen_urls': [], 'last_findings': []})
    report = _read_json(_report_path(), {})
    try:
        from app.services.portal_social_task_service import get_social_auto_task_status
        task_status = get_social_auto_task_status()
    except Exception as exc:
        task_status = {'ok': False, 'enabled': False, 'message': 'Otomatik kontrol durumu alınamadı.', 'error': str(exc)[:240]}
    return {
        'queue_path': str(_queue_path()),
        'history_path': str(_history_path()),
        'watch_state_path': str(_watch_state_path()),
        'watch_links_path': str(_watch_links_path()),
        'pending_links': [x for x in queue.get('links', []) if (x.get('status') or 'pending') == 'pending'][:50],
        'history_items': list(reversed(history.get('items', [])))[:50],
        'allowed_x_accounts': sorted(allowed_x_accounts()),
        'allowed_instagram_accounts': sorted(allowed_instagram_accounts()),
        'watch_sources': watch_sources(),
        'last_watch_state': state,
        'last_report': report,
        'task_status': task_status,
    }


def run_social_embed_scan(*, manual: bool = False, actor: User | None = None, auto_discover: bool = False) -> dict[str, Any]:
    discovery = {'ok': True, 'discovered_count': 0, 'discovered': [], 'sources': []}
    if auto_discover:
        discovery = discover_latest_social_links()
        queue_social_urls([item['url'] for item in discovery.get('discovered', []) if item.get('url')], source='auto_discover')

    queue = _read_json(_queue_path(), {'links': []})
    links = queue.setdefault('links', [])
    stats = {'ok': True, 'manual': bool(manual), 'auto_discover': bool(auto_discover), 'checked': 0, 'created': 0, 'duplicate': 0, 'invalid': 0, 'failed': 0, 'items': [], 'discovery': discovery, 'generated_at': _now_iso()}
    for item in links:
        if (item.get('status') or 'pending') != 'pending':
            continue
        url = item.get('url') or ''
        stats['checked'] += 1
        try:
            result = publish_social_url_to_portal(url, actor=actor, source=item.get('source') or ('auto_discover' if auto_discover else 'queue'), auto_commit=False)
            item['last_result'] = result; item['processed_at'] = _now_iso()
            if result.get('ok') and result.get('status') == 'created':
                item['status'] = 'published'; item['post_id'] = result.get('post_id'); stats['created'] += 1
            elif result.get('status') == 'duplicate':
                item['status'] = 'duplicate'; item['post_id'] = result.get('post_id'); stats['duplicate'] += 1
            elif result.get('status') == 'invalid':
                item['status'] = 'invalid'; stats['invalid'] += 1
            else:
                item['status'] = 'failed'; stats['failed'] += 1
            stats['items'].append({'url': url, 'result': result})
        except Exception as exc:
            item['status'] = 'failed'; item['last_result'] = {'ok': False, 'message': str(exc)[:240]}; stats['failed'] += 1
    db.session.commit()
    _write_json(_queue_path(), queue)
    _write_json(_report_path(), stats)
    return stats
