#!/usr/bin/env python3
"""Create a fail-closed PUBLIC V16 feed. Medical content is never auto-approved.

Input is an internal draft. The output includes medical content ONLY when each
clinical section, rights check, reviewer and next review date are approved.
No DTG table or map data may be embedded. The producer is not itself a medical
or legal content review.
"""
import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE / "country_profiles_draft_v16.json"
DTG_DOMAIN = "dtg.org"

def require(test, message):
    if not test:
        raise ValueError(message)

def iso_date(value, field):
    require(isinstance(value, str), f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc

def check_list(value, field):
    require(isinstance(value, list) and all(isinstance(x, str) for x in value),
            f"{field} must be a list of texts")
    return value

def is_dtg_url(url):
    from urllib.parse import urlparse
    host = urlparse(url).hostname or ""
    return host == DTG_DOMAIN or host.endswith("." + DTG_DOMAIN)

def approved_profile(code, profile, as_of):
    review = profile["medicalReview"]
    require(review.get("reviewer") and isinstance(review["reviewer"], str),
            f"{code}: reviewer missing")
    reviewed_at = iso_date(review.get("reviewedAt"), f"{code}: reviewedAt")
    next_review = iso_date(review.get("nextReviewDate"), f"{code}: nextReviewDate")
    require(reviewed_at <= as_of and next_review >= reviewed_at,
            f"{code}: invalid review dates")
    source_list = review.get("approvedSources")
    require(isinstance(source_list, list) and source_list,
            f"{code}: verified source list missing")
    for s in source_list:
        require(isinstance(s, dict) and
                isinstance(s.get("url"), str) and s["url"].startswith("https://") and
                s.get("reuseRightsChecked") is True and
                iso_date(s.get("checkedAt"), f"{code}: source date") <= as_of,
                f"{code}: source rights/date not confirmed")
        require(not is_dtg_url(s["url"]) or s.get("use") == "external_link_only",
                f"{code}: DTG must be link-only")
    vax = profile["vaccineAssessment"]
    malaria = profile["malariaAssessment"]
    missions = profile["missions"]
    require(vax.get("status") == "approved" and malaria.get("status") == "approved",
            f"{code}: vaccine and malaria approvals required")
    require(missions.get("status") == "approved",
            f"{code}: mission information not verified")
    for field in ("forAll", "riskBased", "entryRequirements", "routeDependent"):
        check_list(vax.get(field), f"{code}: {field}")
    require(malaria.get("riskLevel") in ("none", "regional", "present", "uncertain"),
            f"{code}: malaria risk classification missing")
    require(malaria.get("preventionType") in
            ("none", "exposure_only", "standby_consider",
             "chemoprophylaxis_consider", "regional_assessment_required"),
            f"{code}: malaria prevention class missing")
    require(isinstance(malaria.get("clinicalRecommendation"), str) and
            malaria["clinicalRecommendation"].strip(),
            f"{code}: malaria assessment text missing")
    require(isinstance(malaria.get("regions"), list),
            f"{code}: malaria regions missing")
    if malaria["riskLevel"] in ("regional", "present"):
        require(malaria["regions"], f"{code}: regional information missing")
    require(isinstance(missions.get("verifiedEntries"), list) and
            missions["verifiedEntries"], f"{code}: mission contacts unverified")
    for source in malaria.get("sourceLinks", []):
        require(isinstance(source, dict) and isinstance(source.get("url"), str),
                f"{code}: malformed malaria source")
        require(not is_dtg_url(source["url"]) or
                source.get("use") == "external_link_only",
                f"{code}: DTG structured reuse prohibited")
    if next_review < as_of:
        return None  # expiry: never publish stale medical assertions
    # Explicit allowlist: no legacySnapshot, full draft, or internal reviewer identity.
    return {
        "name": profile["name"],
        "medicalReviewDate": reviewed_at.isoformat(),
        "nextReviewDate": next_review.isoformat(),
        "vaccinations": {k: vax[k] for k in
                         ("forAll", "riskBased", "entryRequirements", "routeDependent")},
        "malaria": {k: malaria.get(k) for k in
                    ("riskLevel", "preventionType", "regions",
                     "medicationName", "clinicalRecommendation", "sourceLinks")},
        "missions": missions["verifiedEntries"],
        "sources": [{"url": s["url"], "checkedAt": s["checkedAt"]}
                    for s in source_list if s.get("use") != "internal_only"]
    }

def build_public(data, as_of=None):
    as_of = as_of or datetime.now(timezone.utc).date()
    require(data.get("schemaVersion") == 2, "Unsupported profile schema")
    require(data.get("mode") == "DRAFT_ONLY_NOT_CONNECTED_TO_LIVE_WEBSITE",
            "Unexpected input dataset")
    policy = data.get("policy", {})
    for flag in ("approvedProfilesOnly", "legacySuggestionsMustNeverBePublished",
                 "noDTGStructuredReuse", "dtgLinksOnly"):
        require(policy.get(flag) is True, f"Safety policy {flag} is missing")
    profiles = data.get("countries")
    require(isinstance(profiles, dict), "Missing country records")
    require(data.get("countryCount") == len(profiles), "Country count mismatch")
    public, coverage = {}, {}
    for code in sorted(profiles):
        p = profiles[code]
        require(len(code) == 2 and code.isascii() and code.isupper(),
                f"Invalid country code {code!r}")
        require(isinstance(p.get("name"), str) and p["name"].strip(),
                f"{code}: missing name")
        review = p.get("medicalReview", {})
        status = review.get("status")
        require(status in ("pending", "approved", "rejected"),
                f"{code}: invalid review status")
        allowed = p.get("publicationAllowed") is True
        require(not allowed or status == "approved",
                f"{code}: unapproved country marked publishable")
        item = approved_profile(code, p, as_of) if allowed else None
        if item:
            public[code] = item
        coverage[code] = {
            "name": p["name"],
            "status": "verified" if item else "medical_review_required"
        }
    output = {
        "schemaVersion": 2,
        "dataset": "praxis-dr-muenster-reisecheck-public-v16",
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "coverageCount": len(coverage),
        "approvedCount": len(public),
        "coverage": coverage,
        "countries": public,
        "notice": "Nur medizinisch freigegebene Länder enthalten konkrete Empfehlungen. "
                  "Fehlende Informationen bedeuten nicht, dass kein Risiko besteht."
    }
    return output

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_public(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement: do not leave a half-written file behind on errors.
    tmp = args.output.with_name(args.output.name + ".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    tmp.replace(args.output)
    print(f"Public V16 feed: {result['approvedCount']} medically approved "
          f"of {result['coverageCount']} covered countries")

if __name__ == "__main__":
    main()
