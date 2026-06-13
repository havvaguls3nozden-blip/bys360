from pathlib import Path

path = Path("scripts/quality/bys360_phase2a_architecture_debt_map.py")
text = path.read_text(encoding="utf-8")

needle = '''    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
'''

patch = '''    except FileNotFoundError as exc:
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "combined_tail": str(exc)[-30000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
'''

if "except FileNotFoundError as exc:" not in text:
    text = text.replace(needle, patch)

path.write_text(text, encoding="utf-8")
print("PHASE2A_RUFF_MISSING_HOTFIX_OK:", "except FileNotFoundError as exc:" in text)
