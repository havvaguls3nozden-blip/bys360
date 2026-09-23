"""BYS360_P0_WAVE_AGENT1_UPLOAD_SECURITY_BEHAVIORAL_CONTRACT

`app/security/upload_security.py` her yüklenen dosyanın geçtiği ortak
güvenlik kapısıdır (profil fotoğrafı, dosya merkezi belgeleri, portal medyası,
kullanıcı geri bildirimi ekleri, destek talebi ekleri). Bu dosya modülün dört
genel işlevini -- `sanitize_original_filename`, `safe_store_filename`,
`detect_mime_from_stream`, `validate_upload` -- gerçek bayt dizileri (PNG/
JPEG/PDF sihirli başlıkları, bellek-içi ZIP arşivleri) üzerinden uçtan uca
sınar. Doğrulama mantığının kendisi asla mock'lanmaz.

Modülün tek dış bağımlılığı Flask `current_app.config`'dir (dosya sistemine
veya ağa dokunmaz); bu yüzden testler burada kurulan minimal, izole bir Flask
uygulama bağlamı (`_app().app_context()`) içinde çalışır -- gerçek uygulamanın
ağır `tests/conftest.py::app` fixture'ına (DB kurulumu vb.) ihtiyaç yoktur.
"""
from __future__ import annotations

import io
import zipfile

import flask
import pytest
from werkzeug.datastructures import FileStorage

from app.security.upload_security import (
    UploadValidationError,
    detect_mime_from_stream,
    safe_store_filename,
    sanitize_original_filename,
    validate_upload,
)

# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def _app(**config: object) -> flask.Flask:
    """Modülün okuduğu yapılandırma anahtarlarını taşıyan minimal bir Flask
    uygulaması. Gerçek dağıtımda MAX_CONTENT_LENGTH her zaman config.py
    tarafından bir tamsayıya ayarlanır; Flask'ın kendi varsayılanı (None)
    `_max_size`'da `int(None)` patlamasına yol açacağından burada açıkça
    ayarlıyoruz."""
    app = flask.Flask("upload_security_test")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app.config.update(config)
    return app


def _fs(filename: str, data: bytes) -> FileStorage:
    return FileStorage(stream=io.BytesIO(data), filename=filename)


def _ooxml_zip(root: str) -> bytes:
    """[Content_Types].xml + <root>document.xml içeren, gerçek bir
    docx/xlsx/pptx'in iskeletine denk düşen geçerli bir OOXML zip'i üretir."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr(f"{root}document.xml", "<r/>")
    return buf.getvalue()


def _plain_zip(entries: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _empty_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    return buf.getvalue()


def _many_entry_zip(count: int) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for i in range(count):
            zf.writestr(f"f{i}.txt", "x")
    return buf.getvalue()


PDF_BYTES = b"%PDF-1.4\n1 0 obj\n%%EOF"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 20
JPEG_BYTES = b"\xff\xd8\xff" + b"0" * 20
GIF_BYTES = b"GIF89a" + b"0" * 20
WEBP_BYTES = b"RIFF" + b"0" * 20


# ---------------------------------------------------------------------------
# sanitize_original_filename
# ---------------------------------------------------------------------------


def test_sanitize_accepts_clean_filename_unchanged() -> None:
    with _app().app_context():
        assert sanitize_original_filename("Report_2026.pdf") == "Report_2026.pdf"


def test_sanitize_rejects_blank_name() -> None:
    with _app().app_context(), pytest.raises(UploadValidationError, match="Geçerli bir dosya adı"):
        sanitize_original_filename("   ")


def test_sanitize_rejects_suspicious_name_patterns() -> None:
    """Yol gezinme, ters eğik çizgi, null bayt ve çoklu boşluk -- dördü de
    aynı güvenlik reddi mesajı ile aynı kapıdan geri çevrilmeli."""
    suspicious_names = [
        "../../etc/passwd.pdf",  # dot-dot traversal
        "a\\b.pdf",  # backslash
        "bad\x00name.pdf",  # embedded null byte
        "bad  name.pdf",  # double whitespace
    ]
    with _app().app_context():
        for name in suspicious_names:
            with pytest.raises(UploadValidationError, match="güvenlik nedeniyle") as exc_info:
                sanitize_original_filename(name)
            assert exc_info.value.args, f"boş hata mesajı: {name!r}"


def test_sanitize_rejects_double_extension_smuggling_dangerous_type() -> None:
    # Görünen uzantı .pdf'dir, fakat tehlikeli .exe segmenti önüne
    # kaçırılmıştır -- klasik çift-uzantı kaçırma saldırısı.
    with _app().app_context(), pytest.raises(UploadValidationError, match="Çift uzantılı"):
        sanitize_original_filename("invoice.exe.pdf")


def test_sanitize_rejects_dangerous_single_extension() -> None:
    with _app().app_context(), pytest.raises(
        UploadValidationError, match=r"Riskli dosya uzantısı.*\.exe"
    ):
        sanitize_original_filename("malware.exe")


def test_sanitize_filename_length_boundary_and_config_override() -> None:
    with _app().app_context():
        at_limit = "a" * 176 + ".txt"  # tam 180 karakter == varsayılan sınır
        assert len(at_limit) == 180
        assert sanitize_original_filename(at_limit) == at_limit

        over_limit = "a" * 177 + ".txt"  # 181 karakter
        with pytest.raises(UploadValidationError, match="uzunluğu aşıyor"):
            sanitize_original_filename(over_limit)

    # UPLOAD_MAX_FILENAME_LENGTH yapılandırması gerçekten okunuyor ve
    # sınırı daraltıyor mu?
    with (
        _app(UPLOAD_MAX_FILENAME_LENGTH=10).app_context(),
        pytest.raises(UploadValidationError, match="uzunluğu aşıyor"),
    ):
        sanitize_original_filename("this-name-is-longer-than-ten-chars.txt")


def test_max_filename_length_falls_back_to_default_on_invalid_config() -> None:
    # UPLOAD_MAX_FILENAME_LENGTH int()'e çevrilemeyen bir değer taşıyorsa
    # (bozuk ortam değişkeni/yapılandırma), modül çökmek yerine güvenli
    # varsayılana (180) geri dönmeli.
    with _app(UPLOAD_MAX_FILENAME_LENGTH="not-a-number").app_context():
        at_default_limit = "a" * 176 + ".txt"  # 180 karakter
        assert sanitize_original_filename(at_default_limit) == at_default_limit

        over_default_limit = "a" * 177 + ".txt"  # 181 karakter
        with pytest.raises(UploadValidationError, match="uzunluğu aşıyor"):
            sanitize_original_filename(over_default_limit)


def test_sanitize_rejects_name_that_becomes_empty_after_secure_filename() -> None:
    # "???.???" hiçbir şüpheli desene uymaz (.. / [/\\] / null / çift boşluk
    # yok) ama werkzeug secure_filename() tüm karakterleri güvensiz bulup
    # boş dizeye indirger -- modül bu durumu ayrı, açık bir hata ile
    # yakalamalı, sessizce boş bir dosya adıyla devam etmemeli.
    with _app().app_context(), pytest.raises(
        UploadValidationError, match="güvenli bir biçime dönüştürülemedi"
    ):
        sanitize_original_filename("???.???")


# ---------------------------------------------------------------------------
# safe_store_filename
# ---------------------------------------------------------------------------


def test_safe_store_filename_randomizes_token_and_preserves_extension() -> None:
    with _app().app_context():
        first = safe_store_filename("Invoice.PDF")
        second = safe_store_filename("Invoice.PDF")

    token, _, ext = first.partition(".")
    assert ext == "pdf"  # uzantı küçük harfe çevrilerek korunuyor
    assert len(token) == 32
    int(token, 16)  # hex olmayan bir token burada ValueError fırlatır

    # secrets.token_hex tabanlı üretim -- iki çağrı asla aynı dosya adını
    # vermemeli (öngörülebilir depolama adı == çakışma/üzerine yazma riski).
    assert first != second


def test_safe_store_filename_rejects_dangerous_extension_via_sanitizer() -> None:
    # safe_store_filename kendi doğrulamasını yapmaz; sanitize_original_filename
    # üzerinden aynı riskli-uzantı reddini miras almalı.
    with _app().app_context(), pytest.raises(UploadValidationError, match=r"\.exe"):
        safe_store_filename("payload.exe")


# ---------------------------------------------------------------------------
# detect_mime_from_stream
# ---------------------------------------------------------------------------


def test_detect_mime_matches_known_signatures_and_falls_back() -> None:
    cases = [
        (PDF_BYTES, "application/pdf"),
        (PNG_BYTES, "image/png"),
        (JPEG_BYTES, "image/jpeg"),
        (GIF_BYTES, "image/gif"),
        (WEBP_BYTES, "image/webp"),
        (b"PK\x03\x04rest-of-zip-payload", "application/zip"),
        (b"this-is-not-a-known-magic-signature", "application/octet-stream"),
    ]
    for data, expected_mime in cases:
        assert detect_mime_from_stream(io.BytesIO(data)) == expected_mime


def test_detect_mime_restores_original_stream_position() -> None:
    # Çağıran taraf akışı okumaya devam edebilmeli; sniffing yan etkisiz
    # olmalı -- bu, `validate_upload`'ın aynı stream'i daha sonra tekrar
    # okuyabilmesinin (ör. arşiv doğrulaması için) ön koşuludur.
    stream = io.BytesIO(b"XX" + PDF_BYTES)
    stream.seek(2)
    mime = detect_mime_from_stream(stream)
    assert mime == "application/pdf"
    assert stream.tell() == 2


# ---------------------------------------------------------------------------
# validate_upload -- mutlu yol
# ---------------------------------------------------------------------------


def test_validate_upload_accepts_each_explicitly_supported_binary_type() -> None:
    cases = [
        ("doc.pdf", PDF_BYTES, "pdf", "application/pdf"),
        ("pic.png", PNG_BYTES, "png", "image/png"),
        ("pic.jpg", JPEG_BYTES, "jpg", "image/jpeg"),
        ("pic.gif", GIF_BYTES, "gif", "image/gif"),
        ("pic.webp", WEBP_BYTES, "webp", "image/webp"),
        ("report.docx", _ooxml_zip("word/"), "docx", "application/zip"),
        ("book.xlsx", _ooxml_zip("xl/"), "xlsx", "application/zip"),
        ("deck.pptx", _ooxml_zip("ppt/"), "pptx", "application/zip"),
    ]
    with _app().app_context():
        for filename, data, expected_ext, expected_mime in cases:
            result = validate_upload(_fs(filename, data))
            assert result["extension"] == expected_ext
            assert result["detected_mime"] == expected_mime
            assert result["size"] == len(data)
            assert result["original_filename"] == filename


def test_validate_upload_accepts_csv_and_txt_without_magic_signature() -> None:
    # csv/txt'nin kendine ait bir sihirli başlığı yoktur; modülün
    # application/octet-stream geri düşüşünü yalnızca bu iki uzantı için
    # kabul etmesi gerekir (bkz. upload_security.py satır 198-200).
    with _app().app_context():
        csv_result = validate_upload(_fs("data.csv", b"a,b,c\n1,2,3"))
        txt_result = validate_upload(_fs("notes.txt", b"plain text content"))
    assert csv_result["detected_mime"] == "application/octet-stream"
    assert txt_result["detected_mime"] == "application/octet-stream"


# ---------------------------------------------------------------------------
# validate_upload -- red yolları
# ---------------------------------------------------------------------------


def test_validate_upload_rejects_missing_file_or_missing_filename() -> None:
    with _app().app_context():
        with pytest.raises(UploadValidationError, match="bulunamadı"):
            validate_upload(None)  # type: ignore[arg-type]
        with pytest.raises(UploadValidationError, match="bulunamadı"):
            validate_upload(_fs("", b"data"))


def test_validate_upload_rejects_empty_file() -> None:
    with _app().app_context(), pytest.raises(UploadValidationError, match="Boş dosya"):
        validate_upload(_fs("empty.txt", b""))


def test_validate_upload_extension_allow_list_precedence() -> None:
    """Uzantı izin listesinin üç kaynağı da gerçekten etkili olmalı:
    varsayılan sözlük, `allowed_extensions` parametresi (genişletir) ve
    `ALLOWED_UPLOAD_EXTENSIONS` yapılandırması (daraltır)."""
    # 1) Varsayılan: .md ne sabit sözlükte ne de bir yapılandırmada var ->
    #    reddedilmeli.
    with _app().app_context():
        with pytest.raises(UploadValidationError, match="İzin verilmeyen"):
            validate_upload(_fs("notes.md", b"hello world"))

        # 2) allowed_extensions parametresi varsayılan sözlüğü genişletebilir.
        widened = validate_upload(_fs("notes.md", b"hello world"), allowed_extensions={"md"})
        assert widened["extension"] == "md"
        assert widened["detected_mime"] == "application/octet-stream"

    # 3) ALLOWED_UPLOAD_EXTENSIONS yapılandırması, normalde varsayılan
    #    olarak izinli olan bir uzantıyı (pdf) bile dışarıda bırakabilir.
    with _app(ALLOWED_UPLOAD_EXTENSIONS="png").app_context():
        with pytest.raises(UploadValidationError, match="İzin verilmeyen"):
            validate_upload(_fs("doc.pdf", PDF_BYTES))
        allowed = validate_upload(_fs("pic.png", PNG_BYTES))
        assert allowed["extension"] == "png"


def test_allowed_extensions_config_accepts_list_type_and_ignores_invalid_type() -> None:
    """ALLOWED_UPLOAD_EXTENSIONS bir virgüllü dize olmak zorunda değil --
    .env dışındaki çağıranlar (ör. programatik test/araç kurulumları) bir
    liste/tuple/set de geçebilir. Beklenmeyen bir tip (ör. None) ise sessizce
    boş küme olarak ele alınıp varsayılan sözlüğe geri düşülmeli, çökmemeli."""
    with _app(ALLOWED_UPLOAD_EXTENSIONS=["png", "pdf"]).app_context():
        accepted = validate_upload(_fs("pic.png", PNG_BYTES))
        assert accepted["extension"] == "png"
        with pytest.raises(UploadValidationError, match="İzin verilmeyen"):
            validate_upload(_fs("a.gif", GIF_BYTES))

    with _app(ALLOWED_UPLOAD_EXTENSIONS=None).app_context():
        # Ne str ne list/tuple/set -> boş küme -> varsayılan sözlüğe düş.
        fallback = validate_upload(_fs("doc.pdf", PDF_BYTES))
        assert fallback["extension"] == "pdf"


def test_validate_upload_rejects_spoofed_mime_extension_mismatch() -> None:
    # Dosya adı .png iddia ediyor ama baytlar gerçek bir JPEG başlığı --
    # bu, modülün var olma sebebi olan tam senaryo: uzantı sahteciliği.
    with _app().app_context(), pytest.raises(
        UploadValidationError, match="beklenen tür ile uyuşmuyor"
    ):
        validate_upload(_fs("pic.png", JPEG_BYTES))


def test_validate_upload_size_boundary_exact_limit_and_one_over() -> None:
    with _app().app_context():
        at_limit = validate_upload(_fs("x.txt", b"A" * 10), max_size=10)
        assert at_limit["size"] == 10

        with pytest.raises(UploadValidationError, match="izin verilen sınırı aşıyor"):
            validate_upload(_fs("x.txt", b"A" * 11), max_size=10)


def test_validate_upload_rejects_docx_missing_expected_ooxml_root() -> None:
    # Yapısal olarak geçerli bir zip, doğru PK sihirli baytları -- ama hiçbir
    # kayıt word/ altında değil, yani gerçek bir docx değil.
    data = _plain_zip({"readme.txt": "not office content"})
    with _app().app_context(), pytest.raises(
        UploadValidationError, match="iç yapısı beklenen türle"
    ):
        validate_upload(_fs("report.docx", data))


def test_validate_upload_rejects_malicious_entries_inside_well_formed_zip() -> None:
    """Aksi halde yapısal olarak sağlam bir zip, içindeki tek bir kayıt
    kötücül olduğunda reddedilmeli: yol gezinmesi veya tehlikeli uzantı."""
    with _app().app_context():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(zipfile.ZipInfo("../../evil.txt"), "x")
        with pytest.raises(UploadValidationError, match="güvenli olmayan yol"):
            validate_upload(_fs("bundle.zip", buf.getvalue()))

        dangerous_entry = _plain_zip({"payload.exe": "MZ"})
        with pytest.raises(UploadValidationError, match="riskli uzantı bulundu"):
            validate_upload(_fs("bundle.zip", dangerous_entry))


def test_validate_upload_archive_entry_count_boundaries() -> None:
    """Sınır değerler: 0 kayıt (boş arşiv) ve tam 2500 (izinli üst sınır,
    kabul edilmeli) ile 2501 (zip-bomb şeklinde -- limiti bir aşan, reddedilmeli)."""
    with _app().app_context():
        with pytest.raises(UploadValidationError, match="boş görünüyor"):
            validate_upload(_fs("bundle.zip", _empty_zip()))

        at_limit = validate_upload(_fs("bundle.zip", _many_entry_zip(2500)))
        assert at_limit["extension"] == "zip"

        with pytest.raises(UploadValidationError, match="çok fazla kayıt"):
            validate_upload(_fs("bundle.zip", _many_entry_zip(2501)))


def test_validate_upload_rejects_malformed_archive_with_zip_magic_but_corrupt_body() -> None:
    # PK\x03\x04 imzası MIME kontrolünü application/zip olarak geçer, ama
    # gövde bozuk -- zipfile.BadZipFile'a düşmeli ve UploadValidationError'a
    # çevrilmeli (çökme değil).
    corrupt = b"PK\x03\x04" + b"\x00" * 20
    with _app().app_context(), pytest.raises(
        UploadValidationError, match="yapısı geçerli değil"
    ):
        validate_upload(_fs("bundle.zip", corrupt))
