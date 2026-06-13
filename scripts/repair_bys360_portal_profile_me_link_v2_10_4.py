# -*- coding: utf-8 -*-
"""
BYS360_COMPILEALL_LEGACY_SCRIPT_FIX_V2_13_3

Bu dosya eski ve tek seferlik bir portal onarım scriptinin güvenli arşivlenmiş
halidir. Önceki içerikte bozuk çok satırlı string kaldığı için `python -m compileall
app config.py scripts` kontrolünü düşürüyordu.

Canlı uygulama runtime akışına bağlı değildir. Asıl içerik aynı klasörde
`.bak_before_BYS360_COMPILEALL_LEGACY_SCRIPT_FIX_V2_13_3_YYYYMMDD_HHMMSS` uzantısıyla yedeklenmiştir.
"""
from __future__ import annotations

VERSION = "BYS360_COMPILEALL_LEGACY_SCRIPT_FIX_V2_13_3"


def main() -> None:
    print(f"{VERSION}: Bu eski tek seferlik script arşivlendi; çalıştırılacak işlem yok.")


if __name__ == "__main__":
    main()
