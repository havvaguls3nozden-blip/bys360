from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_WHEELHOUSE_BUILDER_V1"

DEFAULT_PYTHON_VERSION = "3.12"
DEFAULT_PLATFORM = "win_amd64"
DEFAULT_IMPLEMENTATION = "cp"
DEFAULT_ABI = "cp312"

HASH_LINE_RE = re.compile(r"--hash=sha256:([0-9a-fA-F]{64})")
REQ_LINE_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9._!+-]*)\s*\\?\s*$")
WHEEL_NAME_RE = re.compile(
    r"^(?P<dist>.+)-(?P<version>[^-]+)(?:-(?P<build>\d[^-]*))?"
    r"-(?P<pytag>[^-]+)-(?P<abitag>[^-]+)-(?P<platform>[^-]+)\.whl$"
)
SOURCE_SUFFIXES = {".tar.gz", ".tar.bz2", ".tar.xz", ".zip", ".tgz"}


class WheelhouseBuildError(Exception):
    """Base error for anything that must stop the build cold."""


class LockFileError(WheelhouseBuildError):
    """requirements.lock is missing, empty, or does not parse as pip hash-syntax."""


class DownloadError(WheelhouseBuildError):
    """pip download failed -- most commonly because a pinned package has no
    compatible Windows x64 CPython 3.12 wheel and would require a local
    compiler to build from source. This tool never falls back to a source
    build; it surfaces the failure and stops."""


class VerificationError(WheelhouseBuildError):
    """The wheelhouse directory does not match what requirements.lock demands
    (missing package, extra file, non-wheel artifact, wrong platform tag, or
    a hash that does not match any pinned entry)."""


class LockRequirement:
    __slots__ = ("name", "version", "hashes", "line_no")

    def __init__(self, name: str, version: str, hashes: list[str], line_no: int) -> None:
        self.name = name
        self.version = version
        self.hashes = hashes
        self.line_no = line_no


def parse_lock(path: Path) -> list[LockRequirement]:
    if not path.is_file():
        raise LockFileError(f"kilit dosyasi bulunamadi: {path}")

    raw_lines = path.read_text(encoding="utf-8").splitlines()

    # Join backslash-continued lines the way pip's requirements parser does,
    # skipping blank lines and full-line comments first.
    joined: list[tuple[int, str]] = []
    buffer = ""
    start_line = 0
    for idx, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not buffer:
            if not stripped or stripped.startswith("#"):
                continue
            start_line = idx
        buffer += stripped
        if buffer.endswith("\\"):
            buffer = buffer[:-1]
            continue
        joined.append((start_line, buffer))
        buffer = ""
    if buffer:
        joined.append((start_line, buffer))

    requirements: list[LockRequirement] = []
    for line_no, text in joined:
        match = REQ_LINE_RE.match(text.split("--hash=", 1)[0].strip())
        if match is None:
            raise LockFileError(
                f"{path}:{line_no}: satir pip hash-syntax olarak ayristirilamadi: {text!r}"
            )
        name, version = match.group(1), match.group(2)
        hashes = HASH_LINE_RE.findall(text)
        if not hashes:
            raise LockFileError(
                f"{path}:{line_no}: {name}=={version} icin --hash=sha256:... yok "
                "(kilit dosyasi tamami hash'li olmali)"
            )
        requirements.append(LockRequirement(name, version, hashes, line_no))

    if not requirements:
        raise LockFileError(f"{path}: hic gecerli gereksinim satiri bulunamadi")
    return requirements


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_pip_download(
    python_exe: str,
    lock_path: Path,
    dest: Path,
    python_version: str,
    platform: str,
    implementation: str,
    abi: str,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        python_exe,
        "-m",
        "pip",
        "download",
        "-r",
        str(lock_path),
        "--dest",
        str(dest),
        "--no-deps",
        "--python-version",
        python_version,
        "--platform",
        platform,
        "--implementation",
        implementation,
        "--abi",
        abi,
        "--only-binary=:all:",
    ]
    print("+ " + " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc


def verify_wheelhouse(
    dest: Path, requirements: list[LockRequirement], platform: str
) -> list[dict[str, object]]:
    all_files = sorted(p for p in dest.iterdir() if p.is_file())

    non_wheel = [p for p in all_files if p.suffix != ".whl"]
    if non_wheel:
        names = ", ".join(p.name for p in non_wheel)
        raise VerificationError(
            "wheelhouse'ta .whl olmayan dosya bulundu (sdist/kaynak paket sizmis olabilir, "
            f"bu derleyici gerektirebilir ve sessizce kabul edilmeyecek): {names}"
        )

    wheel_files = all_files
    if len(wheel_files) != len(requirements):
        raise VerificationError(
            f"beklenen paket sayisi {len(requirements)}, indirilen wheel sayisi {len(wheel_files)}"
        )

    expected_hashes: dict[str, LockRequirement] = {}
    for req in requirements:
        for h in req.hashes:
            expected_hashes[h.lower()] = req

    manifest: list[dict[str, object]] = []
    matched_reqs: set[int] = set()
    for wheel in wheel_files:
        name_match = WHEEL_NAME_RE.match(wheel.name)
        if name_match is None:
            raise VerificationError(f"wheel dosya adi ayristirilamadi: {wheel.name}")
        platform_tag = name_match.group("platform")
        if platform_tag != "any" and platform_tag != platform:
            raise VerificationError(
                f"{wheel.name}: platform etiketi '{platform_tag}', beklenen '{platform}' veya 'any' degil "
                "(hedef Windows x64 disina sizmis bir wheel)"
            )

        actual_hash = sha256_of(wheel)
        matched_req = expected_hashes.get(actual_hash.lower())
        if matched_req is None:
            raise VerificationError(
                f"{wheel.name}: sha256={actual_hash} kilit dosyasindaki hicbir gereksinimle eslesmiyor"
            )
        matched_reqs.add(id(matched_req))
        manifest.append(
            {
                "name": matched_req.name,
                "version": matched_req.version,
                "filename": wheel.name,
                "sha256": actual_hash,
                "size_bytes": wheel.stat().st_size,
                "pytag": name_match.group("pytag"),
                "abitag": name_match.group("abitag"),
                "platform": platform_tag,
            }
        )

    unmatched = [req for req in requirements if id(req) not in matched_reqs]
    if unmatched:
        names = ", ".join(f"{r.name}=={r.version}" for r in unmatched)
        raise VerificationError(f"kilitte olup wheelhouse'ta karsiligi bulunamayan paketler: {names}")

    manifest.sort(key=lambda row: str(row["filename"]).lower())
    return manifest


def wheelhouse_identity(manifest: list[dict[str, object]]) -> str:
    lines = [f"{row['filename']}:{row['sha256']}" for row in manifest]
    blob = "\n".join(lines) + "\n"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build(
    root: Path,
    lock_path: Path,
    output: Path,
    report_path: Path,
    python_exe: str,
    python_version: str,
    platform: str,
    implementation: str,
    abi: str,
    clean: bool,
) -> dict[str, object]:
    requirements = parse_lock(lock_path)

    if output.exists():
        if not clean:
            raise WheelhouseBuildError(
                f"{output} zaten var; deterministik bir build icin --clean ile temizden baslatin"
            )
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    proc = run_pip_download(python_exe, lock_path, output, python_version, platform, implementation, abi)
    if proc.returncode != 0:
        raise DownloadError(
            f"pip download basarisiz oldu (exit {proc.returncode}). En olasi sebep: kilitteki "
            f"paketlerden en az biri {platform}/{implementation}{abi} icin uyumlu bir wheel yayinlamiyor "
            "ve yerel derleyici gerektirirdi -- bu arac boyle bir durumda kaynak koddan build'e "
            "sessizce dusmez, yukaridaki pip ciktisinda hangi paket oldugunu gorun."
        )

    manifest = verify_wheelhouse(output, requirements, platform)
    identity = wheelhouse_identity(manifest)
    total_bytes = 0
    for row in manifest:
        row_size = row["size_bytes"]
        if not isinstance(row_size, int):
            raise WheelhouseBuildError(
                f"manifest kaydinda beklenmeyen size_bytes turu: {type(row_size).__name__}"
            )
        total_bytes += row_size

    result = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "lock_path": str(lock_path),
        "output": str(output),
        "target": {
            "python_version": python_version,
            "platform": platform,
            "implementation": implementation,
            "abi": abi,
        },
        "expected_package_count": len(requirements),
        "wheel_count": len(manifest),
        "total_bytes": total_bytes,
        "wheelhouse_identity_sha256": identity,
        "wheelhouse_identity_method": (
            "sha256 over UTF-8 text blob of sorted 'filename:sha256\\n' lines, "
            "one line per wheel in the wheelhouse, trailing newline included"
        ),
        "manifest": manifest,
        "ok": True,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "requirements.lock icindeki tam cozulmus bagimlilik grafigini alir ve "
            "Windows x64 / CPython 3.12 icin tamamen offline kurulabilir bir "
            "build/wheelhouse/ dizini uretir. Uyumlu wheel bulunamayan herhangi bir "
            "paket icin sessizce kaynak build'e dusmez; acikca hata verir."
        )
    )
    parser.add_argument("--root", default=".", help="Depo koku (varsayilan: mevcut dizin)")
    parser.add_argument(
        "--lock",
        default=None,
        help="requirements.lock yolu (varsayilan: <root>/requirements.lock)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Uretilecek wheelhouse dizini (varsayilan: <root>/build/wheelhouse)",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Build raporu JSON yolu (varsayilan: <root>/reports/quality/BYS360_WHEELHOUSE_BUILD_REPORT.json)",
    )
    parser.add_argument(
        "--python-exe",
        default=sys.executable,
        help="pip download'u calistiracak Python yorumlayicisi (varsayilan: bu scripti calistiran yorumlayici)",
    )
    parser.add_argument("--python-version", default=DEFAULT_PYTHON_VERSION)
    parser.add_argument("--platform", default=DEFAULT_PLATFORM)
    parser.add_argument("--implementation", default=DEFAULT_IMPLEMENTATION)
    parser.add_argument("--abi", default=DEFAULT_ABI)
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Cikti dizini zaten varsa once silip temizden yeniden uret",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    lock_path = Path(args.lock).resolve() if args.lock else root / "requirements.lock"
    output = Path(args.output).resolve() if args.output else root / "build" / "wheelhouse"
    report_path = (
        Path(args.report).resolve()
        if args.report
        else root / "reports" / "quality" / "BYS360_WHEELHOUSE_BUILD_REPORT.json"
    )

    try:
        result = build(
            root=root,
            lock_path=lock_path,
            output=output,
            report_path=report_path,
            python_exe=args.python_exe,
            python_version=args.python_version,
            platform=args.platform,
            implementation=args.implementation,
            abi=args.abi,
            clean=args.clean,
        )
    except WheelhouseBuildError as exc:
        print(json.dumps({"ok": False, "package": PACKAGE, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "output": result["output"],
                "wheel_count": result["wheel_count"],
                "total_bytes": result["total_bytes"],
                "wheelhouse_identity_sha256": result["wheelhouse_identity_sha256"],
                "report": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
