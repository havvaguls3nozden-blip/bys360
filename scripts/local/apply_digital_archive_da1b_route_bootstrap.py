from pathlib import Path

path = Path("app/bootstrap/route_bootstrap.py")
text = path.read_text(encoding="utf-8")

if 'key="digital_archive"' in text:
    raise SystemExit("digital_archive blueprint kaydı zaten var.")

needle = '''    BlueprintRegistration(
        key="ai_agent",
        module_path="app.ai_agent.routes",
        attribute_name="ai_agent_bp",
        required=False,
    ),  # BYS360_AG1_AI_AGENT_ROUTE_BOOTSTRAP
'''

insert = '''    BlueprintRegistration(
        key="ai_agent",
        module_path="app.ai_agent.routes",
        attribute_name="ai_agent_bp",
        required=False,
    ),  # BYS360_AG1_AI_AGENT_ROUTE_BOOTSTRAP
    BlueprintRegistration(
        key="digital_archive",
        module_path="app.digital_archive.routes",
        attribute_name="digital_archive_bp",
        required=False,
    ),  # BYS360_DA1B_DIGITAL_ARCHIVE_ROUTE_BOOTSTRAP
'''

if needle not in text:
    raise SystemExit("Beklenen ai_agent blueprint anchor bulunamadı. route_bootstrap.py manuel kontrol edilmeli.")

text = text.replace(needle, insert)

path.write_text(text, encoding="utf-8")
print("OK: route_bootstrap.py içine digital_archive blueprint kaydı eklendi.")
