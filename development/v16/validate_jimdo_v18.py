#!/usr/bin/env python3
"""Static safety checks for the Jimdo V18 widget; not a medical correctness test."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HTML_FILE = ROOT / "website" / "ReiseCheck_Jimdo_V18.html"
html = HTML_FILE.read_text(encoding="utf-8")
source = re.search(r"<script>(.*?)</script>", html, flags=re.S)
assert source, "Inline Jimdo script missing"
script = source.group(1)

assert "V18.0" in html[:260], "Outdated version heading"
assert "country_profiles_public_v16.json" in script, "V16 feed missing"
assert "country_profiles_v1.json" not in html, "Old V1 feed must not be fetched"
assert "const STARTER={countries:{}};" in script, "Old medical drafts may still be embedded"
assert "const selected=[];let profiles=Object.create(null);" in script, "Wrong fallback logic"
assert "profileFresh(p)" in script and "p.nextReviewDate>=today" in script
assert "medically_approved" in script, "No medical-review guard"
assert "profiles=Object.create(null);feedMode=false;" in script, "Fail-closed error path missing"

for element_id in (
    "rm-tool", "rm-country", "rm-suggest", "rm-chips", "rm-region",
    "rm-when", "rm-duration", "rm-style", "rm-check", "rm-reset",
    "rm-results", "rm-shared-vaccinations", "rm-resultlist", "rm-print",
    "rm-intl-source-status", "rm-destination-source-links",
):
    assert f'id="{element_id}"' in html, f"Existing UI element missing: {element_id}"

for preserved_function in (
    "function parseTripDate(", "function renderSharedVaccinations(",
    "function renderOne(", "function updateResult(", "function renderMission(",
    "function riskInfo(", "function loadInternationalFeed(",
):
    assert preserved_function in script, f"Existing function lost: {preserved_function}"

result = subprocess.run(
    ["node", "--check", "-"], input=script, encoding="utf-8",
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
)
assert result.returncode == 0, f"JavaScript syntax error: {result.stdout}"

# V18-specific display and approval invariants.
assert "m.set(clean('STIKO-Standardimpfungen')" in script, "Global STIKO baseline missing"
assert "general:new Set(selected.map(e=>e.n))" in script, "STIKO does not include every selected country"
assert "if(key===clean('STIKO-Standardimpfungen'))continue;" in script, "Duplicate STIKO country profile entry"
assert "Freigegebene Länderinformationen · Stand" not in script, "Old per-country review badge remains"
assert 'id="rm-special-notes"' in html, "Dive notes container missing"
assert "rm-dive-note" in script and "<details class=\\"rm-dive-note\\"" in script, "Dive advice not collapsible"
assert "Freiwillig, z. B." not in html, "Outdated region placeholder"

print("OK: V18 Jimdo HTML – UI, feed safety gates and JS syntax validated.")
