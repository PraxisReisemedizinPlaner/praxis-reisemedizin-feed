#!/usr/bin/env python3
"""Browser smoke tests for V23 geo-autocomplete and regional clinical gating."""
import json
from datetime import date
from pathlib import Path
# Playwright is imported only for the separately installed browser smoke step.

from export_public_regions_v1 import build_public_regions
from export_public_v16 import build_public as build_countries

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REGION=json.loads((HERE/"region_profiles_draft_v1.json").read_text(encoding="utf-8"))
COUNTRIES=json.loads((HERE/"country_profiles_draft_v16.json").read_text(encoding="utf-8"))
regions=build_public_regions(REGION,COUNTRIES,date(2026,11,18))
countries=build_countries(COUNTRIES,date(2026,11,18))
assert regions["regionalApprovedCount"] == 25
assert countries["approvedCount"] == 30

def intercept(route):
    url=route.request.url
    if "/region_directory_public_v1.json" in url:
        route.fulfill(status=200,content_type="application/json",
            headers={"access-control-allow-origin":"*"},body=json.dumps(regions,ensure_ascii=False))
    elif "/country_profiles_public_v16.json" in url:
        route.fulfill(status=200,content_type="application/json",
            headers={"access-control-allow-origin":"*"},body=json.dumps(countries,ensure_ascii=False))
    elif "/public_international_alerts.json" in url:
        route.fulfill(status=200,content_type="application/json",
            headers={"access-control-allow-origin":"*"},body='{"items":[]}')
    else:
        route.continue_()

def selected_country(page,name):
    box=page.locator("#rm-country")
    box.fill(name)
    first=page.locator("#rm-suggest .rm-choice").first
    first.wait_for(timeout=10000)
    first.click()

def smoke(browser,device):
    ctx=browser.new_context(viewport={"width":375 if device=="mobile" else 1140,"height":840})
    ctx.route("**/*", intercept)
    page=ctx.new_page()
    errors=[]
    page.on("pageerror",lambda error: errors.append(str(error)))
    page.goto((ROOT/"website/ReiseCheck_Jimdo_V23.html").as_uri(),wait_until="domcontentloaded")
    page.wait_for_function("() => document.querySelector('#rm-region-feedback')?.textContent?.includes('Stadt oder Insel')",timeout=15000)
    selected_country(page,"Thailand")
    # Koh Chang is ambiguous: both Trat and Little Koh Chang in Ranong must appear.
    page.locator("#rm-region").fill("Koh Chang")
    opts=page.locator("#rm-region-suggest button")
    assert opts.count() >= 2, f"Ambiguous Koh Chang suggestions absent: {opts.all_text_contents()}"
    names=" / ".join(opts.all_text_contents())
    assert "Little Koh Chang" in names and "Ko Chang (Trat" in names, names
    opts.filter(has_text="Little Koh Chang").first.click()
    assert page.locator("#rm-region-chips .rm-region-chip").count()==1
    page.locator("#rm-region").fill("Bangkok")
    page.locator("#rm-region-suggest button").filter(has_text="Bangkok").first.click()
    assert page.locator("#rm-region-chips .rm-region-chip").count()==2
    page.locator("#rm-check").click()
    page.locator("#rm-region-risk").wait_for(state="visible")
    details=page.locator("#rm-region-risk").inner_text()
    assert "Little Koh Chang" in details and "Bangkok" in details
    assert "Regionale Risikoabwägung erforderlich" in details, details
    assert "Kein Malariavorkommen nach regionaler" not in details
    # Unverified free text must not be interpreted as a clinical region.
    page.locator("#rm-region").fill("Unbekannter Waldort")
    assert "Nicht bestätigte Ortsangabe" in page.locator("#rm-region-risk").inner_text()
    # Clear all states, especially region chip selections.
    page.locator("#rm-reset").click()
    assert page.locator("#rm-region-chips .rm-region-chip").count()==0
    assert page.locator("#rm-region").input_value()==""
    assert not errors, "Runtime JS errors: "+"; ".join(errors)
    ctx.close()
    print(f"Browser V23 OK ({device}) – country, ambiguous island, multi-city, missing-risk, unknown text, reset.")

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        for label in ("desktop","mobile"):
            smoke(browser,label)
        browser.close()
