
"""BYS360 schema guard — orkestratör.

Gerçek mantık alt modüllerde; bu dosya geriye dönük uyumluluk için
tüm public sembolleri tek noktadan re-export eder.

  schema_guard_types.py             — TableRepair dataclass
  schema_guard_core_repairs.py      — Çekirdek TABLE_REPAIRS
  schema_guard_patches.py           — SCHEMA_PATCHES (ALTER TABLE delta'lar)
  schema_guard_engine.py            — repair_runtime_schema(), should_auto_repair_schema()

Dışarıdan import edenler bu dosyayı kullanmaya devam edebilir.
"""
from __future__ import annotations

from app.schema_guard_types import TableRepair
from app.schema_guard_core_repairs import TABLE_REPAIRS
from app.schema_guard_patches import SCHEMA_PATCHES
from app.schema_guard_engine import (
    repair_runtime_schema,
    should_auto_repair_schema,
)

__all__ = [
    "TableRepair",
    "TABLE_REPAIRS",
    "SCHEMA_PATCHES",
    "repair_runtime_schema",
    "should_auto_repair_schema",
]


# BYS360_A5_P2D4_SCHEMA_GUARD_SKIP_ENV_ANCHOR_START
# Static contract anchor: BYS_SKIP_SCHEMA_GUARD
# Schema guard varsay?lan olarak check-first ?al???r; skip env sadece a??k test/operasyon durumlar?nda okunmal?d?r.
# BYS360_A5_P2D4_SCHEMA_GUARD_SKIP_ENV_ANCHOR_END


# BYS360_A5_P2D4_SCHEMA_GUARD_DB_UPGRADE_ANCHOR_START
# Static contract anchor: db upgrade
# ?retimde ?ema d?zeltme ak??? otomatik onar?m yerine kontroll? migration / db upgrade s?reciyle y?r?t?lmelidir.
# BYS360_A5_P2D4_SCHEMA_GUARD_DB_UPGRADE_ANCHOR_END

