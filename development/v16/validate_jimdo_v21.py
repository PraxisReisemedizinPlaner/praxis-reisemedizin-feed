#!/usr/bin/env python3
"""Structural and JS checks for ReiseCheck Jimdo V21. Not clinical approval."""
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[2]
html = (root / "website/ReiseCheck_Jimdo_V21.html").read_text(encoding="utf-8")
match = re.search(r"<script>(.*?)</script>", html, flags=re.S)
assert match, "JavaScript missing"
script = match.group(1)
assert "V21.0" in html[:250], "Wrong version"
assert "country_profiles_public_v16.json" in script, "Approved medical feed missing"
assert "country_profiles_v1.json" not in html, "Unsafe v1 feed exposed"
assert "const STARTER={countries:{}};" in script, "Embedded draft country data still present"
assert "medically_approved" in script and "profileFresh(p)" in script, "Approval guard missing"
assert "profiles=Object.create(null);feedMode=false;" in script, "Fail-closed error handling missing"
for name in ("rm-style", "rm-purpose", "rm-activities"):
    assert f'id="{name}-picker"' in html, f"Multi selector {name} missing"
    assert f'<fieldset id="{name}"' in html, f"Checkbox fieldset {name} missing"
    assert f'<select id="{name}"' not in html, f"Old single selector {name} present"
    for suffix in ("-clear","-done","-toggle","-summary"):
        assert f'id="{name}{suffix}"' in html, f"{name}{suffix} missing"
assert html.count('name="rm-style-option" value=') == 5, "Reiseform options missing"
assert html.count('name="rm-purpose-option" value=') == 4, "Reisegrund options missing"
assert html.count('name="rm-activity" value=') == 6, "Aktivitaeten options missing"
for name in ("getSelectedMulti", "getSelectedActivities", "getSelectedStyles", "getSelectedPurposes",
             "updateMultiLabel", "onMultiChange", "renderSpecialNotes", "renderSharedVaccinations",
             "renderOne", "parseTripDate", "updateResult", "loadInternationalFeed"):
    assert f"function {name}(" in script, f"JS function {name} missing"
assert "Höhenaufenthalt über 2.500 m" in script
assert 'rm-altitude-note' in script and 'rm-dive-note' in script
# The medical sources are available in the final collapsed source index only.
assert "https://www.usz.ch/krankheit/hoehenkrankheit/" in html
assert "https://www.cdc.gov/yellow-book/hcp/environmental-hazards-risks/high-altitude-travel-and-altitude-illness.html" in html
assert "https://www.usz.ch/krankheit/hoehenkrankheit/" not in script
assert "Originalquellen zur Höhenmedizin" in html
assert html.index("Originalquellen zur Höhenmedizin") < html.index("<script>")
assert "divingMask:" in script and "mountain:" in script
assert "icon('divingMask')+'Tauchen / Schnorcheln" in script
assert "icon('mountain')+'Höhenaufenthalt" in script
assert "icon('health')+'Tauchen / Schnorcheln" not in script
assert "icon('health')+'Höhenaufenthalt" not in script
assert "if(note)note.open=true" in script, "Collapsed advice state lost on change"
result = subprocess.run(["node","--check","-"], input=script, encoding="utf-8",
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
assert result.returncode == 0, result.stdout
print("OK: V21 Reiseformen, Reisegründe, Aktivitäten, Höhenhinweis, medical safety and JS syntax.")
