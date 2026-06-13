from __future__ import annotations

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get('BYS360_PROJECT_ROOT', r'C:\bys360\project'))
AUTH = PROJECT_ROOT / 'app' / 'main_handlers' / 'auth_handlers.py'
CONFIG = PROJECT_ROOT / 'config.py'
ENV = PROJECT_ROOT / '.env'

errors: list[str] = []

def read(path: Path) -> str:
    if not path.exists():
        errors.append(f'Dosya bulunamadı: {path}')
        return ''
    return path.read_text(encoding='utf-8')


auth = read(AUTH)
config = read(CONFIG)
env = read(ENV) if ENV.exists() else ''

if re.search(r'login_user\(user,\s*remember\s*=\s*True\)', auth):
    errors.append('login_user(user, remember=True) hala duruyor.')
if 'login_user(user, remember=False)' not in auth:
    errors.append('login_user(user, remember=False) bulunamadı.')
if re.search(r'session\.permanent\s*=\s*True', auth):
    errors.append('auth_handlers.py içinde session.permanent = True hala duruyor.')
if 'session.clear()' not in auth:
    errors.append('logout içinde session.clear() bulunamadı.')
if 'PERMANENT_SESSION_LIFETIME_MINUTES = int(os.getenv' in config and ', 480))' in config:
    errors.append('config.py varsayılan session süresi hala 480 dakika.')
if ENV.exists() and 'PERMANENT_SESSION_LIFETIME_MINUTES=480' in env:
    errors.append('.env içinde session süresi hala 480 dakika.')

if errors:
    print('BYS360_SESSION_TIMEOUT_SECURITY_V1_GATE_FAIL')
    for e in errors:
        print(' - ' + e)
    raise SystemExit(1)

print('BYS360_SESSION_TIMEOUT_SECURITY_V1_GATE_OK')
