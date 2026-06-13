from pathlib import Path
import subprocess, sys

def main():
    root=Path(__file__).resolve().parents[2]
    old=root/'scripts'/'quality'/'check_corporate_information_center_v3_0_phase5_1_gate_fix.py'
    py=root/'.venv'/'Scripts'/'python.exe'
    python=str(py) if py.exists() else sys.executable
    if not old.exists():
        print('BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_2_FLAT_GATE_FIX_GATE_FAIL')
        print(f'HATA: Eksik kontrol scripti: {old}')
        return 2
    res=subprocess.run([python,str(old)],cwd=str(root),text=True,capture_output=True)
    if res.stdout: print(res.stdout,end='')
    if res.stderr: print(res.stderr,end='',file=sys.stderr)
    if res.returncode != 0: return res.returncode
    print('BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_2_FLAT_GATE_FIX_GATE_OK')
    print('BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_2_FLAT_GATE_FIX_FINAL_OK')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
