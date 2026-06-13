from __future__ import annotations

import argparse
import sys
from pathlib import Path

VERSION = 'BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_1_STAFF_NOON_MESSAGE'


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("project_root_pos", nargs="?", default=None)
    p.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root or args.project_root_pos or ".").resolve()
    sys.path.insert(0, str(root / "scripts" / "communication"))
    import repair_corporate_information_center_v3_0_phase6_1_staff_noon_message as repair
    checks = repair.gate(root, check_db=False)
    if checks:
        print(VERSION + "_GATE_FAIL")
        for c in checks:
            print("HATA:", c)
        return 2
    print(VERSION + "_GATE_OK")
    print(VERSION + "_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
