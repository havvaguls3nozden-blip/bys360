from pathlib import Path
import argparse, importlib.util, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    mod_path = root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase7_8_base_header_pro.py"
    if not mod_path.exists():
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_8_BASE_HEADER_PRO_GATE_FAIL")
        print("HATA: repair script bulunamadı")
        return 2
    spec = importlib.util.spec_from_file_location("phase78", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.gate(root)

if __name__ == "__main__":
    raise SystemExit(main())
