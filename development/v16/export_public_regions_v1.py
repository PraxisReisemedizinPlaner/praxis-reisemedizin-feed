#!/usr/bin/env python3
"""Publish geography suggestions without publishing unapproved regional medical advice.

Medical data is strictly opt-in per *region* and only after the parent country
has a valid medical approval. The public directory is safe as a geography
picker, not a region-level malaria recommendation by itself.
"""
import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DRAFT = HERE / "region_profiles_draft_v1.json"
COUNTRIES = HERE / "country_profiles_draft_v16.json"

def require(ok, why):
    if not ok:
        raise ValueError(why)

def parse_date(value):
    require(isinstance(value, str), "Review date must be ISO string")
    return date.fromisoformat(value)

def valid_external_url(value):
    if not isinstance(value, str):
        return False
    parts = urlparse(value)
    return parts.scheme == "https" and bool(parts.netloc) and not parts.username and not parts.password

def build_public_regions(regions_draft, country_draft, as_of=None):
    as_of = as_of or datetime.now(timezone.utc).date()
    require(regions_draft.get("schemaVersion") == 1, "Wrong regional schema")
    require(regions_draft.get("mode") == "DRAFT_ONLY_GEO_CATALOGUE_NO_CLINICAL_RELEASE", "Regional draft flag missing")
    rules = regions_draft.get("policy") or {}
    for key in ("clinicalApprovalRequired", "noAutomaticRiskFromFreitext", "noDTGStructuredReuse", "noMedicationWithoutRegionClinicalApproval"):
        require(rules.get(key) is True, f"Missing policy: {key}")
    rows = regions_draft.get("regions")
    require(isinstance(rows, list) and rows, "Missing region catalogue")
    require(country_draft.get("schemaVersion") == 2, "Parent country schema mismatch")
    countries = country_draft.get("countries")
    require(isinstance(countries, dict), "Parent country data unavailable")
    out = []
    seen = set()
    for row in rows:
        code, rid = row.get("country"), row.get("id")
        require(isinstance(code, str) and code in countries, f"Unknown country: {code}")
        require(isinstance(rid, str) and rid.startswith(code + "-") and rid not in seen, f"Duplicate or invalid ID: {rid}")
        seen.add(rid)
        require(row.get("geographicalEntry") == "candidate", f"Unexpected geography state: {rid}")
        name, kind, aliases = row.get("name"), row.get("kind"), row.get("aliases")
        require(isinstance(name, str) and 2 <= len(name) < 130, f"Invalid name: {rid}")
        require(isinstance(kind, str) and kind in ("city","island","region"), f"Invalid kind: {rid}")
        require(isinstance(aliases, list) and all(isinstance(a, str) and 2 <= len(a) < 100 for a in aliases) and len(aliases) <= 15,
                f"Invalid aliases: {rid}")
        review, m = row.get("clinicalReview") or {}, row.get("malariaAssessment") or {}
        state = review.get("status")
        require(state in ("pending","approved","rejected"), f"Invalid clinical state: {rid}")
        allowed = row.get("publicationAllowed") is True
        require(not allowed or state == "approved", f"Unapproved region marked publishable: {rid}")
        item = {"id":rid,"country":code,"name":name,"kind":kind,"aliases":aliases,
                "clinicalStatus":"medical_review_required"}
        if allowed:
            parent = countries[code]
            country_review = parent.get("medicalReview") or {}
            require(parent.get("publicationAllowed") is True and country_review.get("status") == "approved"
                    and parse_date(country_review.get("nextReviewDate")) >= as_of,
                    f"Parent country not medically valid: {rid}")
            require(isinstance(review.get("reviewer"), str) and review["reviewer"].strip(), f"Reviewer missing: {rid}")
            checked, expiry = parse_date(review.get("reviewedAt")),parse_date(review.get("nextReviewDate"))
            require(checked <= as_of and expiry >= checked, f"Invalid regional review dates: {rid}")
            urls = review.get("sourceUrls")
            require(isinstance(urls,list) and urls and all(valid_external_url(s) for s in urls), f"Invalid sources: {rid}")
            require(review.get("reuseRightsChecked") is True, f"Source rights not approved: {rid}")
            require(all(urlparse(s).hostname not in ("dtg.org","www.dtg.org") for s in urls), f"DTG region data forbidden: {rid}")
            require(m.get("riskLevel") in ("none","low","moderate","high","uncertain"), f"Risk missing: {rid}")
            require(m.get("preventionType") in ("none","exposure_only","standby_consider","chemoprophylaxis_consider","regional_assessment_required"),
                    f"Prevention type missing: {rid}")
            require(isinstance(m.get("clinicalRecommendation"), str) and m["clinicalRecommendation"].strip(), f"Assessment missing: {rid}")
            require(m.get("medicationName") is None, f"No per-region drug directive allowed in v1: {rid}")
            if expiry >= as_of:
                item["clinicalStatus"] = "approved"
                item["nextReviewDate"] = expiry.isoformat()
                item["malaria"] = {k: m[k] for k in ("riskLevel","preventionType","clinicalRecommendation")}
                item["sources"] = urls
        out.append(item)
    return {"schemaVersion":1, "dataset":"praxis-dr-muenster-regions-public-v1",
            "generatedAt":datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "geographyCount":len(out),
            "regionalApprovedCount":sum(x["clinicalStatus"]=="approved" for x in out),
            "regions":out,
            "notice":"Ortsnamen dienen nur zur eindeutigen Reiseplanung. Ohne medizinische Regionalfreigabe gibt es keine lokalen Malariaempfehlungen."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--regions",type=Path,default=DRAFT)
    ap.add_argument("--countries",type=Path,default=COUNTRIES)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    data=build_public_regions(json.loads(args.regions.read_text(encoding="utf-8")),
                              json.loads(args.countries.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp=args.output.with_name(args.output.name+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(args.output)
    print(f"Region directory: {data['geographyCount']} names, {data['regionalApprovedCount']} medically approved")

if __name__ == "__main__":
    main()
