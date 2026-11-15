#!/usr/bin/env python3
"""Validate current and future country packages before public export."""
import json
from pathlib import Path
from route_planning import validate_route_assessment
HERE=Path(__file__).resolve().parent
def validate_all(countries,geography,sources):
    if countries.get("policy",{}).get("regionalRouteAssessmentRequired") is not True: raise ValueError("Regional route policy missing")
    for code,p in countries["countries"].items():
        validate_route_assessment(code,p,geography,sources)
    return len(countries["countries"])
if __name__=="__main__":
    read=lambda n:json.loads((HERE/n).read_text(encoding="utf-8"))
    count=validate_all(read("country_profiles_draft_v16.json"),read("region_profiles_draft_v1.json"),read("region_source_packages_v2.json"))
    print(f"Regional route requirements OK for {count} country packages")
