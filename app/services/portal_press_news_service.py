# -*- coding: utf-8 -*-
"""BYS360 Portal V3A2 Basında Tarihi Alan haber takip sağlamlaştırma servisi.

Tasarım ilkesi:
- Haber adayı otomatik bulunabilir.
- Portal gönderisi otomatik yayınlanmaz.
- Yetkili onayı olmadan paylaşım oluşmaz.
- Haber metni/görseli kopyalanmaz; kısa özet ve kaynak bağlantısı tutulur.
- V3A2 ile alaka filtresi, kaynak güveni, risk etiketi, benzer haber birleştirme
  ve tarama sağlık raporu güçlendirilmiştir.
"""
from __future__ import annotations

import email.utils
import hashlib
import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import current_app

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import Notification, PortalPost, User
from app.route_support import sanitize_free_text

DEFAULT_QUERIES = [
    '"Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı"',
    '"Gelibolu Tarihi Alan Başkanlığı"',
    '"Tarihi Alan Başkanlığı" Çanakkale',
    '"Çanakkale Tarihi Alan"',
    '"İsmail Kaşdemir" "Tarihi Alan"',
    '"Şehitler Abidesi" "Tarihi Alan"',
]

# V3A2: Kaynak güven listesi. Liste sıkı engel değil; puanlama ve risk etiketi için kullanılır.
DEFAULT_TRUSTED_HOSTS = {
    'aa.com.tr', 'trthaber.com', 'iha.com.tr', 'dha.com.tr', 'ntv.com.tr',
    'milliyet.com.tr', 'hurriyet.com.tr', 'sabah.com.tr', 'haberturk.com',
    'ensonhaber.com', 'cumhuriyet.com.tr', 'sozcu.com.tr', 'anadoluajansi.com.tr',
    'canakkale.gov.tr', 'ktb.gov.tr', 'kulturportali.gov.tr', 'tccb.gov.tr',
    'gelibolu.gov.tr', 'eceabat.gov.tr', 'canakkale.bel.tr',
}

LOCAL_HOST_KEYWORDS = {
    'canakkale', 'çanakkale', 'gelibolu', 'eceabat', 'bozcaada', 'gokceada',
    'gökçeada', 'tarihialan', 'boğaz', 'bogaz', '17burda', 'objektif17',
}

STRONG_RELEVANCE_TERMS = {
    'çanakkale savaşları', 'canakkale savaslari', 'gelibolu tarihi alan',
    'tarihi alan başkanlığı', 'tarihi alan baskanligi', 'alan başkanlığı',
    'alan baskanligi', 'çanakkale tarihi alan', 'canakkale tarihi alan',
    'ismail kaşdemir', 'ismail kasdemir',
}

WEAK_RELEVANCE_TERMS = {
    'şehitler abidesi', 'sehitler abidesi', 'conkbayırı', 'conkbayiri',
    'kabatepe', 'kilitbahir', 'eceabat', 'gelibolu', 'tarihi alan',
    'çanakkale', 'canakkale', 'anma töreni', 'anma toreni',
}

RISK_WORDS = {
    'iddia', 'soruşturma', 'sorusturma', 'mahkeme', 'dava', 'şikayet', 'şikâyet',
    'sikayet', 'kaza', 'yangın', 'yangin', 'kriz', 'protesto', 'istifa', 'gözaltı',
    'gozalti', 'suç', 'suc', 'usulsüz', 'usulsuz', 'skandal', 'tepki', 'ceza',
    'tartışma', 'tartisma', 'yaralı', 'yarali', 'ölü', 'olu', 'saldırı', 'saldiri',
}

POSITIVE_WORDS = {
    'ziyaret', 'açılış', 'acilis', 'etkinlik', 'tören', 'toren', 'anma', 'proje',
    'sergi', 'başarı', 'basari', 'ödül', 'odul', 'eğitim', 'egitim', 'çalıştay',
    'calistay', 'toplantı', 'toplanti', 'imza', 'restorasyon',
}

STOPWORDS = {
    've', 'ile', 'bir', 'bu', 'şu', 'su', 'için', 'icin', 'son', 'yeni', 'haber',
    'güncel', 'guncel', 'başkanlığı', 'baskanligi', 'tarihi', 'alan', 'çanakkale',
    'canakkale', 'gelibolu', 'da', 'de', 'en', 'olan', 'olarak', 'hakkında', 'hakkinda',
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')




def _press_news_sort_key(item: dict[str, Any]) -> float:
    # Haberleri gerçek yayın/işlem tarihine göre sıralar; en yeni kayıt en üstte görünür.
    values = [item.get('published_at_iso'), item.get('published_at'), item.get('published_at_text'), item.get('approved_at'), item.get('created_at'), item.get('updated_at')]
    for raw in values:
        value = str(raw or '').strip()
        if not value: continue
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            return float(dt.timestamp())
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass
        try:
            dt = email.utils.parsedate_to_datetime(value)
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            return float(dt.timestamp())
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass
    return 0.0


def _data_path() -> Path:
    try:
        base = Path(current_app.instance_path) / 'portal'
    except RuntimeError:
        base = Path.cwd() / 'instance' / 'portal'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'press_news_candidates_v3a.json'


def _report_path() -> Path:
    try:
        base = Path(current_app.root_path).parent / 'reports' / 'portal'
    except RuntimeError:
        base = Path.cwd() / 'reports' / 'portal'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'BYS360_PRESS_NEWS_SCAN_V3A_LAST_REPORT.json'


def _health_report_path() -> Path:
    try:
        base = Path(current_app.root_path).parent / 'reports' / 'portal'
    except RuntimeError:
        base = Path.cwd() / 'reports' / 'portal'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'BYS360_PRESS_NEWS_SCAN_V3A2_HEALTH_REPORT.json'


def _tr_lower(value: Any) -> str:
    text = str(value or '')
    text = text.replace('İ', 'i').replace('I', 'ı')
    text = text.lower()
    repl = str.maketrans({'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'})
    return text.translate(repl)


def _clean(value: Any, limit: int = 500) -> str:
    text = html.unescape(str(value or ''))
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return sanitize_free_text(text, limit=limit)


def _host(url: str) -> str:
    try:
        return urllib.parse.urlparse(url or '').netloc.lower().replace('www.', '')
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return ''


def _canonical_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url or '')
        qs = urllib.parse.parse_qs(parsed.query)
        # Bing News bazen gerçek URL'yi url/u parametresine koyar.
        for key in ('url', 'u'):
            raw = qs.get(key, [''])[0]
            if raw and raw.startswith(('http://', 'https://')):
                return _canonical_url(raw)
        clean_qs = []
        for k, vals in qs.items():
            if k.lower().startswith('utm_') or k.lower() in {'fbclid', 'gclid', 'ved', 'usg'}:
                continue
            for v in vals:
                clean_qs.append((k, v))
        query = urllib.parse.urlencode(clean_qs, doseq=True)
        return urllib.parse.urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip('/'), '', query, ''))
    except Exception:
        return str(url or '')[:700]


def _candidate_id(url: str, title: str) -> str:
    canonical = _canonical_url(url)
    key = canonical or title or _now_iso()
    return hashlib.sha256(key.encode('utf-8', errors='ignore')).hexdigest()[:18]


def _title_fingerprint(title: str) -> str:
    normalized = _tr_lower(title)
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
    words = [w for w in normalized.split() if len(w) > 2 and w not in STOPWORDS]
    return ' '.join(words[:14]) or hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]


def _trusted_hosts() -> set[str]:
    raw = os.getenv('BYS360_PRESS_NEWS_ALLOWED_HOSTS', '').strip()
    if raw:
        hosts = {p.strip().lower().replace('www.', '') for p in raw.split('|') if p.strip()}
        if hosts:
            return hosts
    return set(DEFAULT_TRUSTED_HOSTS)


def _queries() -> list[str]:
    raw = os.getenv('BYS360_PRESS_NEWS_QUERIES', '').strip()
    if raw:
        parts = [p.strip() for p in raw.split('|') if p.strip()]
        if parts:
            return parts[:12]
    return DEFAULT_QUERIES


def _source_score(host: str) -> tuple[int, list[str]]:
    notes: list[str] = []
    normalized_host = _tr_lower(host)
    score = 0
    trusted = _trusted_hosts()
    if host in trusted or any(host.endswith('.' + h) for h in trusted):
        score += 2
        notes.append('Güvenilir kaynak listesinde')
    if any(key in normalized_host for key in LOCAL_HOST_KEYWORDS):
        score += 1
        notes.append('Yerel/konu bağlantılı kaynak')
    if not host:
        notes.append('Kaynak adresi okunamadı')
    return score, notes


def _relevance_score(title: str, summary: str, query: str) -> tuple[int, list[str]]:
    haystack = _tr_lower(f'{title} {summary} {query}')
    score = 0
    notes: list[str] = []
    strong_hits = [term for term in STRONG_RELEVANCE_TERMS if _tr_lower(term) in haystack]
    weak_hits = [term for term in WEAK_RELEVANCE_TERMS if _tr_lower(term) in haystack]
    if strong_hits:
        score += min(6, len(strong_hits) * 3)
        notes.append('Güçlü konu eşleşmesi: ' + ', '.join(strong_hits[:3]))
    if weak_hits:
        score += min(3, len(weak_hits))
        notes.append('Ek konu işareti: ' + ', '.join(weak_hits[:4]))
    return score, notes


def _risk_level(title: str, summary: str, source_score: int, relevance_score: int) -> tuple[str, list[str]]:
    haystack = _tr_lower(f'{title} {summary}')
    flags = [word for word in sorted(RISK_WORDS) if _tr_lower(word) in haystack]
    positives = [word for word in sorted(POSITIVE_WORDS) if _tr_lower(word) in haystack]
    if flags:
        return 'İnceleme gerekli', ['Riskli kelime: ' + ', '.join(flags[:5])]
    if source_score <= 0 and relevance_score < 4:
        return 'Kaynak kontrolü', ['Kaynak veya alaka düzeyi ayrıca kontrol edilmeli']
    if positives:
        return 'Düşük', ['Olumlu/kurumsal etkinlik işareti: ' + ', '.join(positives[:4])]
    return 'Normal', []


def _load_store() -> dict[str, Any]:
    path = _data_path()
    if not path.exists():
        return {'version': 'v3a2', 'items': [], 'last_rejected': [], 'last_health': {}}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return {'version': 'v3a2', 'items': [], 'last_rejected': [], 'last_health': {}}
        data.setdefault('items', [])
        data.setdefault('last_rejected', [])
        data.setdefault('last_health', {})
        data['version'] = 'v3a2'
        return data
    except Exception:
        return {'version': 'v3a2', 'items': [], 'last_rejected': [], 'last_health': {}}


def _save_store(data: dict[str, Any]) -> None:
    data['version'] = 'v3a2'
    path = _data_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _rss_url(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return f'https://www.bing.com/news/search?q={encoded}&format=rss&setlang=tr-TR&cc=TR'


def _fetch_url(url: str, timeout: int = 12) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'BYS360-PressNewsMonitor/3.2 (+internal approved publishing)',
            'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8',
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(2_000_000)


def _source_from_item(item: ET.Element, link: str) -> tuple[str, str]:
    source_el = item.find('source')
    source_name = _clean(source_el.text if source_el is not None else '', limit=120)
    source_url = _clean(source_el.attrib.get('url') if source_el is not None else '', limit=700)
    host = _host(source_url) or _host(link)
    if not source_name:
        source_name = host or 'Kaynak'
    return source_name, host


def _make_candidate(raw: dict[str, str]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    title = _clean(raw.get('title'), limit=220)
    link = _clean(raw.get('link'), limit=700)
    summary = _clean(raw.get('summary'), limit=420)
    query = _clean(raw.get('query'), limit=180)
    pub_date = _clean(raw.get('pub_date'), limit=120)
    source_name = _clean(raw.get('source_name'), limit=120)
    source_host = _clean(raw.get('source_host'), limit=160)
    if not title or not link:
        return None, {'title': title or '(başlık yok)', 'reason': 'Başlık veya bağlantı eksik', 'query': query}
    canonical = _canonical_url(link)
    host = _host(canonical) or source_host
    if host and host.endswith('bing.com') and source_host:
        host = source_host
    src_score, src_notes = _source_score(host)
    rel_score, rel_notes = _relevance_score(title, summary, query)
    # V3A2: Alaka eşiği. Güçlü konu yoksa ve yalnızca zayıf yer adı varsa elenir.
    if rel_score < 3:
        return None, {
            'title': title,
            'source': source_name or host,
            'url': canonical or link,
            'query': query,
            'reason': 'Konu alakası düşük',
            'relevance_score': rel_score,
            'notes': rel_notes,
        }
    risk_level, risk_notes = _risk_level(title, summary, src_score, rel_score)
    notes = src_notes + rel_notes + risk_notes
    candidate = {
        'id': _candidate_id(canonical or link, title),
        'title': title,
        'summary': summary,
        'url': canonical or link,
        'canonical_url': canonical or link,
        'source': source_name or host or 'Kaynak',
        'source_host': host,
        'published_at_text': pub_date,
        'query': query,
        'risk_level': risk_level,
        'risk_flags': risk_notes,
        'relevance_score': rel_score,
        'source_score': src_score,
        'filter_notes': notes,
        'title_fingerprint': _title_fingerprint(title),
        'status': 'new',
        'created_at': _now_iso(),
        'updated_at': _now_iso(),
        'portal_post_id': None,
        'duplicate_sources': [],
    }
    return candidate, None


def _parse_rss(raw: bytes, query: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(raw)
    except Exception as exc:
        return [], [{'query': query, 'reason': 'RSS okunamadı', 'error': str(exc)[:240]}]
    for item in root.findall('.//item')[:16]:
        link = _clean(item.findtext('link'), limit=700)
        source_name, source_host = _source_from_item(item, link)
        candidate, reject = _make_candidate({
            'title': item.findtext('title') or '',
            'link': link,
            'summary': item.findtext('description') or '',
            'pub_date': item.findtext('pubDate') or '',
            'query': query,
            'source_name': source_name,
            'source_host': source_host,
        })
        if candidate:
            candidates.append(candidate)
        elif reject:
            rejected.append(reject)
    return candidates, rejected


def _scan_bing_news_rss() -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    found: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    rejected: list[dict[str, Any]] = []
    for query in _queries():
        try:
            raw = _fetch_url(_rss_url(query))
            rows, rejects = _parse_rss(raw, query)
            found.extend(rows)
            rejected.extend(rejects)
            time.sleep(0.25)
        except Exception as exc:
            errors.append({'query': query, 'error': str(exc)[:240]})
    return found, errors, rejected


def _merge_duplicate(existing: dict[str, Any], candidate: dict[str, Any]) -> None:
    existing['updated_at'] = _now_iso()
    existing.setdefault('duplicate_sources', [])
    src = {
        'source': candidate.get('source'),
        'source_host': candidate.get('source_host'),
        'url': candidate.get('url'),
        'published_at_text': candidate.get('published_at_text'),
    }
    if src not in existing['duplicate_sources'] and candidate.get('url') != existing.get('url'):
        existing['duplicate_sources'].append(src)
    existing['duplicate_sources'] = existing['duplicate_sources'][:12]
    # Daha yüksek risk varsa üstte göster.
    if candidate.get('risk_level') == 'İnceleme gerekli':
        existing['risk_level'] = 'İnceleme gerekli'
        existing['risk_flags'] = candidate.get('risk_flags') or existing.get('risk_flags') or []


def scan_press_news_candidates(*, triggered_by_user_id: int | None = None, manual: bool = False) -> dict[str, Any]:
    store = _load_store()
    existing_by_id = {str(item.get('id')): item for item in store.get('items', []) if item.get('id')}
    existing_by_fingerprint = {str(item.get('title_fingerprint')): item for item in store.get('items', []) if item.get('title_fingerprint')}
    found, errors, rejected = _scan_bing_news_rss()
    added = 0
    touched = 0
    duplicates = 0
    risk_count = 0
    for candidate in found:
        cid = candidate.get('id')
        fp = str(candidate.get('title_fingerprint') or '')
        if not cid:
            continue
        if candidate.get('risk_level') == 'İnceleme gerekli':
            risk_count += 1
        if cid in existing_by_id:
            _merge_duplicate(existing_by_id[cid], candidate)
            touched += 1
            continue
        if fp and fp in existing_by_fingerprint:
            _merge_duplicate(existing_by_fingerprint[fp], candidate)
            duplicates += 1
            continue
        existing_by_id[cid] = candidate
        if fp:
            existing_by_fingerprint[fp] = candidate
        added += 1
    items = sorted(existing_by_id.values(), key=_press_news_sort_key, reverse=True)[:300]
    health = {
        'version': 'v3a2',
        'last_scan_at': _now_iso(),
        'manual': bool(manual),
        'found_after_filter': len(found),
        'added': added,
        'touched': touched,
        'duplicates_merged': duplicates,
        'rejected': len(rejected),
        'risk_candidates': risk_count,
        'source_errors': len(errors),
        'errors': errors,
        'rejected_samples': rejected[:20],
        'queries': _queries(),
    }
    store.update({
        'version': 'v3a2',
        'last_scan_at': health['last_scan_at'],
        'last_scan_manual': bool(manual),
        'last_scan_user_id': triggered_by_user_id,
        'last_health': health,
        'last_rejected': rejected[:60],
        'items': items,
    })
    _save_store(store)
    result = {
        'ok': True,
        'added': added,
        'touched': touched,
        'duplicates_merged': duplicates,
        'found': len(found),
        'rejected': len(rejected),
        'risk_candidates': risk_count,
        'errors': errors,
        'last_scan_at': store['last_scan_at'],
        'health_report': str(_health_report_path()),
    }
    _report_path().write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    _health_report_path().write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def _items(statuses: set[str] | None = None) -> list[dict[str, Any]]:
    data = _load_store()
    rows = data.get('items', []) or []
    if statuses:
        rows = [r for r in rows if str(r.get('status') or 'new') in statuses]
    return sorted(rows, key=_press_news_sort_key, reverse=True)


def _latest_published() -> dict[str, Any] | None:
    rows = [r for r in _items({'published'}) if r.get('portal_post_id')]
    return rows[0] if rows else None


def _pending_count() -> int:
    return len(_items({'new'}))


def _risk_count() -> int:
    return sum(1 for r in _items({'new'}) if str(r.get('risk_level')) == 'İnceleme gerekli')


def press_news_home_context(user: Any | None = None) -> dict[str, Any]:
    data = _load_store()
    latest = _latest_published()
    pending = _pending_count()
    risk = _risk_count()
    health = data.get('last_health') or {}
    can_review = False
    try:
        from app.services.portal_service import can_manage_portal
        can_review = bool(can_manage_portal(user))
    except Exception:
        can_review = False
    return {
        'press_news': {
            'enabled': True,
            'title': 'Basında Tarihi Alan',
            'subtitle': 'Başkanlığımız hakkında yayımlanan haberler onay sonrası portalda paylaşılır.',
            'latest': latest,
            'pending_count': pending,
            'risk_count': risk,
            'last_scan_at': data.get('last_scan_at'),
            'last_health': health,
            'can_review': can_review,
            'review_url': '/portal/press-news',
        }
    }


def press_news_review_context(user: Any | None = None) -> dict[str, Any]:
    data = _load_store()
    rows = sorted(data.get('items', []) or [], key=_press_news_sort_key, reverse=True)
    health = data.get('last_health') or {}
    return {
        'items_new': [r for r in rows if str(r.get('status') or 'new') == 'new'][:80],
        'items_published': [r for r in rows if str(r.get('status') or '') == 'published'][:20],
        'items_archived': [r for r in rows if str(r.get('status') or '') == 'archived'][:20],
        'last_scan_at': data.get('last_scan_at'),
        'last_health': health,
        'last_rejected': data.get('last_rejected', [])[:20],
        'data_path': str(_data_path()),
        'health_report_path': str(_health_report_path()),
    }


def _find_candidate(candidate_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    store = _load_store()
    for item in store.get('items', []) or []:
        if str(item.get('id')) == str(candidate_id):
            return store, item
    return store, None


def publish_press_news_candidate(candidate_id: str, actor: Any) -> dict[str, Any]:
    store, item = _find_candidate(candidate_id)
    if not item:
        return {'ok': False, 'message': 'Haber adayı bulunamadı.'}
    if str(item.get('status')) == 'published' and item.get('portal_post_id'):
        return {'ok': True, 'message': 'Bu haber daha önce yayınlanmış.', 'post_id': item.get('portal_post_id')}
    title = _clean(item.get('title'), limit=220)
    summary = _clean(item.get('summary'), limit=650)
    url = _clean(item.get('url'), limit=700)
    source = _clean(item.get('source'), limit=120) or 'Kaynak'
    body_parts = [
        'Başkanlığımız hakkında basında yer alan haber bağlantısı paylaşılmıştır.',
        '',
        f'Haber: {title}',
    ]
    if summary:
        body_parts += ['', summary]
    body_parts += ['', f'Kaynak: {source}', f'Bağlantı: {url}']
    post = PortalPost(
        author_user_id=int(getattr(actor, 'id', 0) or 0),
        wall_owner_user_id=int(getattr(actor, 'id', 0) or 0),
        title='Basında Tarihi Alan',
        body='\n'.join(body_parts),
        post_type='corporate_announcement',
        visibility_scope='public',
        comments_enabled=True,
        published_at=utc_now(),
    )
    db.session.add(post)
    db.session.flush()
    item['status'] = 'published'
    item['approved_by_user_id'] = int(getattr(actor, 'id', 0) or 0)
    item['approved_at'] = _now_iso()
    item['portal_post_id'] = int(post.id)
    item['updated_at'] = _now_iso()
    _save_store(store)
    try:
        admin_users = User.query.filter(User.role.in_(['admin', 'baskan', 'baskan_yardimcisi'])).limit(30).all()
        for user in admin_users:
            if int(getattr(user, 'id', 0) or 0) == int(getattr(actor, 'id', 0) or 0):
                continue
            db.session.add(Notification(
                user_id=user.id,
                title='Basında Tarihi Alan haberi yayınlandı',
                body=title,
                notification_type='portal_press_news_published',
                source_type='portal_post',
                source_id=post.id,
                link_url='/portal',
                priority='normal',
            ))
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        pass
    db.session.commit()
    return {'ok': True, 'post_id': int(post.id)}


def archive_press_news_candidate(candidate_id: str, actor: Any) -> dict[str, Any]:
    store, item = _find_candidate(candidate_id)
    if not item:
        return {'ok': False, 'message': 'Haber adayı bulunamadı.'}
    item['status'] = 'archived'
    item['archived_by_user_id'] = int(getattr(actor, 'id', 0) or 0)
    item['archived_at'] = _now_iso()
    item['updated_at'] = _now_iso()
    _save_store(store)
    return {'ok': True, 'message': 'Haber adayı arşivlendi.'}
