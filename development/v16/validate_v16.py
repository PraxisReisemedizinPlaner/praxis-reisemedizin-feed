#!/usr/bin/env python3
"""Validate V16 DEVELOPMENT profiles. No medical approval is performed by this script."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROFILES = ROOT / "country_profiles_draft_v16.json"
SOURCES = ROOT / "malaria_sources_registry.json"
ALLOWED_STATUS = {"pending", "approved", "rejected"}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    data = json.loads(PROFILES.read_text(encoding="utf-8"))
    registry = json.loads(SOURCES.read_text(encoding="utf-8"))
    countries = data["countries"]
    require(data["schemaVersion"] == 2, "Wrong schema version")
    require(data["countryCount"] == len(countries), "Country count mismatch")
    require(data["mode"] == "DRAFT_ONLY_NOT_CONNECTED_TO_LIVE_WEBSITE",
            "This file is a development-only draft")
    require(len(countries) >= 9, "Unexpected loss of the original nine draft countries")
    require(data["policy"]["noDTGStructuredReuse"] is True,
            "DTG restriction missing")
    for code, profile in countries.items():
        require(len(code) == 2 and code.isupper(), f"Invalid country code: {code}")
        require(profile["name"], f"Missing country name: {code}")
        review = profile["medicalReview"]
        require(review["status"] in ALLOWED_STATUS,
                f"Invalid review status: {code}")
        # No existing review has been done; fail closed rather than trust imports.
        if review["status"] != "approved":
            require(profile["publicationAllowed"] is False,
                    f"Unapproved profile marked publishable: {code}")
            # Draft clinical notes are allowed here, but publication stays blocked.
            # Only export_public_v16.py may create patient-facing recommendations.
        else:
            require(bool(review["reviewer"] and review["reviewedAt"] and
                         review["approvedSources"]),
                    f"Medical approval details missing: {code}")
        require("originalCheckedDate" in profile["legacySnapshot"],
                f"Legacy provenance missing: {code}")
    require(registry["publicationStatus"] == "REFERENCE_ONLY",
            "Registry must remain reference-only")
    for item in registry["sources"]:
        require(item["ingestionEnabled"] is False,
                f"Unexpected automatic ingestion: {item['id']}")
    dtg = next(item for item in registry["sources"] if item["id"] == "DTG")
    require(dtg["role"] == "external_link_only", "DTG link-only policy violated")
    print(f"OK: {len(countries)} draft country profiles, "
          f"{len(registry['sources'])} reference sources; "
          "no unapproved medical publication.")

if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
