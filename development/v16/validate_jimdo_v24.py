#!/usr/bin/env python3
"""Structural and JS checks for ReiseCheck Jimdo V24. Not clinical approval."""
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[2]
html = (root / "website/ReiseCheck_Jimdo_V24.html").read_text(encoding="utf-8")
match = re.search(r"<script>(.*?)</script>", html, flags=re.S)
assert match, "JavaScript missing"
script = match.group(1)
assert "V24.9" in html[:250], "Wrong version"
assert "country_profiles_public_v16.json" in script, "Approved medical feed missing"
assert "country_profiles_v1.json" not in html, "Unsafe v1 feed exposed"
assert "const STARTER={countries:{}};" in script, "Embedded draft country data still present"
assert "medically_approved" in script and "profileFresh(p)" in script, "Approval guard missing"
assert "profiles=Object.create(null);feedMode=false;" in script, "Fail-closed error handling missing"
for name in ("rm-style", "rm-purpose", "rm-activities"):
    assert f'id="{name}-picker"' in html, f"Multi selector {name} missing"
    assert f'<fieldset id="{name}"' in html, f"Checkbox fieldset {name} missing"
    assert f'<select id="{name}"' not in html, f"Old single selector {name} present"
    for suffix in ("-clear","-toggle","-summary"):
        assert f'id="{name}{suffix}"' in html, f"{name}{suffix} missing"
for name, count in (("rm-style", 5), ("rm-purpose", 4), ("rm-activities", 6)):
    field = re.search(r'<fieldset id="' + name + r'".*?</fieldset>', html, re.S).group(0)
    assert field.count('class="rm-activity-choice"') == count, name + " options missing"
    assert field.count('aria-pressed="false"') == count, name + " toggle state missing"
    assert 'type="checkbox"' not in field, name + " still uses checkboxes"
    assert f'id="{name}-done"' not in html, name + " still requires confirmation"
assert "function closeOtherMultiPickers(" in script
assert "button.setAttribute('aria-pressed',String(" in script
assert "if(!multiPointerActive)closeOtherMultiPickers(event.target);" in script
for name in ("getSelectedMulti", "getSelectedActivities", "getSelectedStyles", "getSelectedPurposes",
             "updateMultiLabel", "onMultiChange", "renderSpecialNotes", "renderSharedVaccinations",
             "renderOne", "parseTripDate", "updateResult", "loadInternationalFeed"):
    assert f"function {name}(" in script, f"JS function {name} missing"
assert "Höhenaufenthalt über 2.500 m" in script
assert 'rm-altitude-note' in script and 'rm-dive-note' in script
# Medical sources are in the collapsed index; legal links stay visible.
assert "https://www.usz.ch/krankheit/hoehenkrankheit/" in html
assert "https://www.cdc.gov/yellow-book/hcp/environmental-hazards-risks/high-altitude-travel-and-altitude-illness.html" in html
assert "https://www.usz.ch/krankheit/hoehenkrankheit/" not in script
assert "Alle Originalquellen" in html and "Weitere Fachquellen" in html
assert html.index("Weitere Fachquellen") < html.index("Universitätsspital Zürich · Höhenkrankheit") < html.index("<script>")
assert html.index('class="rm-source-legal"') > html.index("Medizinische Hinweise")
assert "rm-countries-data-note" not in html
assert "waves:" in script and "mountain:" in script
assert "icon('waves')+'Tauchen / Schnorcheln" in script
assert "divingMask:" not in script and "icon('divingMask')" not in script
assert "icon('mountain')+'Höhenaufenthalt" in script
assert "icon('health')+'Tauchen / Schnorcheln" not in script
assert "icon('health')+'Höhenaufenthalt" not in script
assert "if(note)note.open=true" in script, "Collapsed advice state lost on change"

assert 'id="rm-region-suggest"' in html and 'id="rm-region-chips"' in html
assert 'id="rm-region-picker"' in html, "Region picker wrapper missing"
assert 'button.rm-selected' in html, "Selected-row styling missing"
assert "regionDirectory.filter(r=>countries.has(r.country));" in script, "Previously selected places must stay in list"
assert "const had=regionPicks.some(x=>x.id===id);" in script, "Toggle-to-deselect absent"
assert "showRegionSuggestions(); // intentionally remains open" in script, "Multi-selection dropdown closes prematurely"
assert "document.addEventListener('focusin',event=>" in script, "Next-field auto-close missing"
assert "event.composedPath().includes($('rm-region-picker'))" in script, "Click on rerendered item must not close list"
assert "if(!multiPointerActive&&!event.target.closest?.('#rm-region-picker'))hideRegionSuggestions();" in script, "Picker loses focus within itself"
assert "regionActive?'true':'false'" not in script, "Keyboard highlight must not change selected state"

assert 'id="rm-region-risk"' in html
assert 'id="rm-region-feedback"' in html
assert 'role="combobox"' in html
assert "const REGION_DIRECTORY_FEED_URL='https://praxisreisemedizinplaner.github.io/praxis-reisemedizin-feed/region_directory_public_v2.json'" in script
for symbol in ("function showRegionSuggestions(","function chooseRegion(","function renderRegionChips(",
               "function renderRegionalRisk(","async function loadRegionDirectory(",
               "function hideRegionSuggestions("):
    assert symbol in script, f"Region UI function missing: {symbol}"
assert "data.sourceBasedCount" in script, "Regional medical gate missing"
assert "row.clinicalStatus==='source_based'" in script, "Regional clinical status not checked"
assert "profileFresh(parent)" in script, "Parent country medical review must remain active"
assert "approvalScope==='country_package'" in script
assert "Quellenabweichung – konkrete Reise berücksichtigen" in script
assert "regionDirectory=[];regionFeedReady=false;regionPicks=[];" in script, "Regional data fail-closed handling missing"
assert "regionPicks=regionPicks.filter(x=>countries.has(x.country)" in script, "Orphaned region chips not pruned"
assert "riskInfo(p,region)" in script, "Original country-level malaria safety retained"
assert "loadRegionDirectory();" in script, "Regional feed not loaded"

result = subprocess.run(["node","--check","-"], input=script, encoding="utf-8",
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
assert result.returncode == 0, result.stdout
print("OK: V24 Reiseformen, Reisegründe, Aktivitäten, Höhenhinweis, medical safety and JS syntax.")
