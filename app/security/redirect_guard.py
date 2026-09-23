from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import unquote, urlsplit

"""Framework'ten bağımsız yönlendirme (redirect) hedefi güvenlik denetimi.

BYS360_PHASE5_3A_A2_HOST_HEADER_OPEN_REDIRECT_HARDENING

Bu modül bilinçli olarak Flask `request` nesnesine dokunmaz. Sebep basit:
`request.host` / `request.host_url`, istemcinin gönderdiği `Host` başlığından
(veya bir ters-proxy/IIS zincirinde yanlış yapılandırılmış
`X-Forwarded-Host`'tan) türetilir ve saldırgan tarafından kontrol edilebilir.
"Bu hedef bizim origin'imizle aynı mı?" sorusunun cevabı asla istemcinin
beyanına (Host header) değil, sunucu tarafında sabit kanonik bir değere
(`APP_BASE_URL`) ve/veya operatörün açıkça belirttiği bir allowlist'e
dayanmalıdır. Aksi halde "host header poisoning" ile `is_safe_redirect_target`
kontrolü saldırganın kendi sahte Host'una göre öz-doğrulama yapar ve dış bir
adrese güvenli yönlendirme "izni" verebilir.

Fonksiyonlar saf (pure) tutulur (girdi olarak canlı `current_app`/`request`
yerine düz string/koleksiyon alırlar) ki tam bir Flask app/request context
kurmadan yüzlerce saldırı deseniyle hızlı ve deterministik birim testi
yazılabilsin. `app/route_support.py`, `current_app.config`'ten okuduğu
`APP_BASE_URL` (+ opsiyonel host allowlist'i) bu modüle parametre olarak
geçirerek ince bir köprü görevi görür.
"""

_ALLOWED_SCHEMES = {"http", "https"}

# Yerel geliştirme için sabit, dar bir liste; canlı/staging ortamında
# `allow_local_dev=False` geçirilerek tamamen devre dışı bırakılmalıdır.
_LOCAL_DEV_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]", "0.0.0.0"}

_DEFAULT_PORTS = {"http": 80, "https": 443}

# ASCII kontrol karakterleri (tab/newline/CR dahil). Tarayıcılar bir URL'yi
# yorumlamadan önce bu karakterleri sessizce budar; biz de aynısını yapıp
# "javascript:\n alert(1)" veya "/\t/evil.example" gibi gizleme denemelerinin
# kontrol karakteri kaldırıldıktan SONRA yeniden ve tam olarak
# değerlendirilmesini sağlıyoruz.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")

# Adayın en başındaki '/' ve '\' karakterlerinin HERHANGİ bir karışımından
# oluşan >=2 uzunluklu diziyi yakalar: '//x', '/\\x', '\\/x', '\\\\x'.
# WHATWG URL algoritması, http/https gibi "special" şemalarda ters eğik
# çizgiyi de yol ayracıyla aynı şekilde ele alır; bu yüzden yalnızca '//'
# değil, bu dört kombinasyonun tamamı "scheme-relative" (authority başlatan)
# sayılmalı ve reddedilmelidir.
_LEADING_SEPARATORS_RE = re.compile(r"^[/\\]{2,}")

_MAX_DECODE_PASSES = 3


def _strip_control_chars(value: str) -> str:
    return _CONTROL_CHARS_RE.sub("", value)


def _decode_variants(value: str) -> list[str]:
    """Percent-encoding (tek/çift kodlama) ile gizlenmiş ayraçları ortaya çıkarır.

    '/%2Fevil.example' -> '//evil.example', '/%252Fevil.example' -> (2 adımda)
    aynı sonuca ulaşır. En fazla `_MAX_DECODE_PASSES` adım uygulanır; adımlar
    sabit noktaya ulaştığında (artık çözülecek bir şey kalmadığında) durur.
    """
    seen = {value}
    variants = [value]
    current = value
    for _ in range(_MAX_DECODE_PASSES):
        decoded = unquote(current)
        if decoded == current or decoded in seen:
            break
        seen.add(decoded)
        variants.append(decoded)
        current = decoded
    return variants


def _looks_scheme_relative(value: str) -> bool:
    return bool(_LEADING_SEPARATORS_RE.match(value))


def _effective_port(port: int | None, scheme: str) -> int | None:
    if port is not None:
        return port
    return _DEFAULT_PORTS.get(scheme)


def _strip_optional_port(value: str) -> str:
    if not value or value.startswith("["):
        return value
    head, sep, tail = value.rpartition(":")
    if sep and tail.isdigit():
        return head
    return value


def is_trusted_host(hostname: str | None, allowed_hosts: Iterable[str]) -> bool:
    """`hostname`, `allowed_hosts` listesindeki bir girdiyle güvenli biçimde eşleşiyor mu?

    Kurallar (Werkzeug'ün kendi `Host` başlığı doğrulama sözleşmesiyle bilinçli
    olarak uyumlu -- bkz. ``werkzeug.sansio.utils.host_is_trusted``):
      * Girdi '.' ile başlıyorsa (ör. ``.bys360.com``) bu bir ALT ALAN ADI
        SONEKİ kuralıdır: yalnızca ``*.bys360.com`` biçimindeki gerçek alt
        alan adları eşleşir (nokta sınırı ZORUNLU). Böylece
        ``trusted.example.evil.example`` gibi "güvenilir host'u prefix/alt
        dize olarak taşıyan ama aslında farklı bir domain olan" adresler,
        salt ``str.endswith(trusted)`` gibi naif bir kontrolün aksine
        REDDEDİLİR (``evil.example`` ile biten ama ``.bys360.com`` ile
        bitmeyen bir host, sonek kuralına asla uymaz).
      * Girdi '.' ile başlamıyorsa TAM eşleşme aranır.
      * Karşılaştırma her zaman küçük harfe çevrilerek yapılır (host adları
        case-insensitive'dir).
      * Girdide isteğe bağlı bir ``:port`` soneki varsa (operatör alışkanlıkla
        host:port yapıştırabilir) yok sayılır; port kontrolü yalnızca kanonik
        `APP_BASE_URL` karşılaştırmasında (bkz. `is_safe_redirect_target`)
        yapılır.
    """
    host = (hostname or "").strip().lower()
    if not host:
        return False
    for raw in allowed_hosts:
        entry = str(raw or "").strip().lower()
        if not entry:
            continue
        is_suffix = entry.startswith(".")
        if is_suffix:
            entry = entry[1:]
        entry = _strip_optional_port(entry)
        if not entry:
            continue
        if is_suffix:
            if host == entry or host.endswith("." + entry):
                return True
        elif host == entry:
            return True
    return False


def is_safe_redirect_target(
    target: str | None,
    *,
    app_base_url: str | None = None,
    allowed_hosts: Iterable[str] | None = None,
    allow_local_dev: bool = False,
) -> bool:
    """Bir "next"/yönlendirme hedefinin açık yönlendirme (open redirect) ve
    host-header poisoning riski taşımadan kullanılıp kullanılamayacağını saptar.

    Sözleşme:
      * Boş/None hedef -> güvensiz.
      * Şema yalnızca ``http``/``https`` olabilir (``javascript:``, ``data:``,
        ``file:``, ``vbscript:`` vb. reddedilir).
      * Göreli (aynı uygulama içi) hedefler, tek bir ``/`` ile başladığı ve
        gerçekte "scheme-relative" bir authority başlatmadığı sürece
        güvenlidir. ``//evil.example``, ``/\\evil.example``,
        ``\\/evil.example``, bunların percent-encode edilmiş (``%2F``,
        ``%5C``) ve çift kodlanmış (``%252F``) varyantları GÖRELİ SAYILMAZ.
      * Mutlak hedefler yalnızca host, kanonik ``app_base_url``'in host:port
        ikilisiyle TAM eşleştiğinde ya da `allowed_hosts` allowlist'inde
        (bkz. `is_trusted_host`) yer aldığında kabul edilir.
      * `allow_local_dev=True` iken yalnızca sabit, dar bir yerel geliştirme
        host kümesi (localhost/127.0.0.1/::1) ek olarak güvenilir sayılır;
        bu asla canlı/staging'de açık bırakılmamalıdır.
      * Karşılaştırma HİÇBİR ZAMAN istemcinin ``Host`` başlığına dayanmaz --
        çağıran (bkz. ``app/route_support.py``) buraya yalnızca sunucu
        tarafında sabit `app_base_url`/`allowed_hosts` değerlerini geçirir.
    """
    if not target:
        return False
    candidate = _strip_control_chars(str(target)).strip()
    if not candidate:
        return False

    for variant in _decode_variants(candidate):
        if _looks_scheme_relative(variant):
            return False

    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return False

    scheme = (parsed.scheme or "").lower()
    if scheme and scheme not in _ALLOWED_SCHEMES:
        return False

    if not parsed.netloc:
        # '//', '/\\' vb. yukarıda zaten elendi; kalan tek geçerli güvenli
        # biçim tek '/' ile başlayan uygulama-içi göreli bir yoldur.
        return candidate.startswith("/")

    if not scheme:
        # netloc dolu ama scheme yok demek pratikte yukarıdaki
        # scheme-relative kontrolünden kaçmış bir biçim olurdu; savunma
        # amaçlı ikinci bir bariyer olarak yine de reddet.
        return False

    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return False
    if not hostname:
        return False

    host = hostname.lower()
    candidate_port = _effective_port(port, scheme)

    canonical = urlsplit((app_base_url or "").strip())
    canonical_host = (canonical.hostname or "").lower()
    if canonical_host:
        canonical_scheme = (canonical.scheme or scheme or "https").lower()
        try:
            canonical_port = _effective_port(canonical.port, canonical_scheme)
        except ValueError:
            canonical_port = None
        if host == canonical_host and candidate_port == canonical_port:
            return True

    combined_allowed = list(allowed_hosts or [])
    if allow_local_dev:
        combined_allowed += list(_LOCAL_DEV_HOSTS)
    return is_trusted_host(host, combined_allowed)
