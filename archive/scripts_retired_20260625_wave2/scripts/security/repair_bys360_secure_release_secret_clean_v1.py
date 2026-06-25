
from __future__ import annotations
import argparse, re
from pathlib import Path

START="# >>> BYS360 SECURE RELEASE SECRET CLEAN V1 >>>"
END="# <<< BYS360 SECURE RELEASE SECRET CLEAN V1 <<<"
BLOCK=f"""{START}
.env
.env.*
*.env
*.local
*.secret
*.secrets
!.env.example

*.bak
*.backup
*.tmp
*.temp
*.log
logs/
instance/
flask_session/
.cache/
.pytest_cache/
.mypy_cache/
.ruff_cache/
__pycache__/
*.py[cod]
*.pyo

.venv/
venv/
env/

*.db
*.sqlite
*.sqlite3
*.dump
*.backup.sql
*.sql.gz
*.pgdump

dist/
dist_secure/
_upload_parts/
*.zip
*.rar
*.7z
*.tar
*.tar.gz
{END}
"""

ENV_EXAMPLE="""# BYS360 ortam değişkenleri örneği
# Gerçek parola, DSN veya API anahtarı yazmayın.

APP_ENV=development
FLASK_ENV=development
SECRET_KEY=CHANGE_ME_WITH_STRONG_RANDOM_VALUE
DATABASE_URL=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
SQLALCHEMY_DATABASE_URI=DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT
DB_SSLMODE=require
DB_ALLOW_SSL_DISABLE=false
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
SENTRY_REQUIRED_IN_PRODUCTION=false
REDIS_URL=redis://127.0.0.1:6379/0
CACHE_REDIS_URL=redis://127.0.0.1:6379/1
SECURITY_RATE_LIMIT_REDIS_URL=redis://127.0.0.1:6379/2
BYS360_DEPLOYMENT_MODE=local
AI_API_KEY=
CSP_ENABLED=true
CSP_REPORT_ONLY=false
CSP_NONCE_ENABLED=true
CSP_ALLOW_UNSAFE_INLINE_SCRIPT=false
PDF_EXPORT_MAX_ROWS_INLINE=250
"""

def rt(p: Path)->str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

def wt(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def patch_gitignore(root: Path):
    p=root/".gitignore"; t=rt(p)
    pat=re.compile(re.escape(START)+r".*?"+re.escape(END), re.S)
    t=pat.sub(BLOCK.strip(), t) if pat.search(t) else (t.rstrip()+"\n\n"+BLOCK.strip()+"\n")
    wt(p,t)

def sanitize(k,v):
    K=k.upper()
    if K in {"DATABASE_URL","SQLALCHEMY_DATABASE_URI"}:
        return "DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT"
    if K=="DB_SSLMODE": return "require"
    if K=="DB_ALLOW_SSL_DISABLE": return "false"
    if K=="SENTRY_DSN": return ""
    if K=="SENTRY_ENVIRONMENT": return "development"
    if K=="SENTRY_REQUIRED_IN_PRODUCTION": return "false"
    if K in {"REDIS_URL","CACHE_REDIS_URL","SECURITY_RATE_LIMIT_REDIS_URL"}:
        return {"REDIS_URL":"redis://127.0.0.1:6379/0","CACHE_REDIS_URL":"redis://127.0.0.1:6379/1","SECURITY_RATE_LIMIT_REDIS_URL":"redis://127.0.0.1:6379/2"}[K]
    if K in {"APP_ENV","FLASK_ENV"}: return "development"
    if "SECRET" in K or "PASSWORD" in K or "TOKEN" in K or "KEY" in K:
        return "" if K=="AI_API_KEY" else "CHANGE_ME"
    return ""

def make_env_example(root: Path):
    env=root/".env"; out=root/".env.example"
    if not env.exists():
        if not out.exists(): wt(out, ENV_EXAMPLE)
        return
    rows=[]; seen=set()
    for raw in rt(env).splitlines():
        line=raw.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1); k=k.strip()
        if not k or k in seen: continue
        rows.append((k,sanitize(k,v))); seen.add(k)
    for k,v in [("APP_ENV","development"),("FLASK_ENV","development"),("SECRET_KEY","CHANGE_ME_WITH_STRONG_RANDOM_VALUE"),("DATABASE_URL","DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT"),("SQLALCHEMY_DATABASE_URI","DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT"),("DB_SSLMODE","require"),("SENTRY_DSN",""),("AI_API_KEY","")]:
        if k not in seen: rows.append((k,v)); seen.add(k)
    wt(out, "# BYS360 ortam değişkenleri örneği\n# Gerçek parola/DSN/API anahtarı yazmayın.\n\n"+"\n".join(f"{k}={v}" for k,v in rows)+"\n")

def add_import(t):
    if "generate_initial_password" not in t: return t
    if "from app.security.passwords import generate_initial_password" in t: return t
    lines=t.splitlines(); pos=0
    for i,l in enumerate(lines[:80]):
        s=l.strip()
        if s.startswith("import ") or s.startswith("from "): pos=i+1
        elif pos and s and not s.startswith("#"): break
    lines.insert(pos, "from app.security.passwords import generate_initial_password")
    return "\n".join(lines)+("\n" if t.endswith("\n") else "")

def patch_123456(root: Path):
    changed=[]
    app=root/"app"
    if not app.exists(): return changed
    assign=re.compile(r'(?P<i>^[ \t]*)(?P<n>(?:initial|default|temporary|temp|first)_password)\s*=\s*[\'"]123456[\'"]', re.I|re.M)
    setter=re.compile(r'\.set_password\(\s*[\'"]123456[\'"]\s*\)')
    for p in app.rglob("*.py"):
        rel=p.relative_to(root).as_posix()
        if "__pycache__" in rel or rel=="app/security/passwords.py": continue
        old=rt(p); new=assign.sub(r"\g<i>\g<n> = generate_initial_password()", old)
        new=setter.sub(".set_password(generate_initial_password())", new)
        if new!=old:
            wt(p, add_import(new)); changed.append(rel)
    return changed

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--project-root", required=True); a=ap.parse_args()
    root=Path(a.project_root).resolve()
    patch_gitignore(root); make_env_example(root)
    marker=root/"scripts/security/BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_APPLIED.txt"
    changed=patch_123456(root)
    wt(marker, "BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_APPLIED\npatched_password_files="+(",".join(changed) if changed else "none")+"\n")
    print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_REPAIR_OK")
    for c in changed: print(" - patched:", c)
if __name__=="__main__": main()
