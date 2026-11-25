import copy
from datetime import date
import json
from pathlib import Path
import unittest
from export_public_v16 import build_public
from export_public_regions_v2 import build_public_regions
from validate_route_requirements import validate_all
from build_country_review_preview import render
HERE=Path(__file__).resolve().parent
CODES=("LK","NP","MY","PH")
class AsiaBatchTests(unittest.TestCase):
    def setUp(self):
        read=lambda name:json.loads((HERE/name).read_text(encoding="utf-8"))
        self.c=read("country_profiles_draft_v16.json")
        self.g=read("region_profiles_draft_v1.json")
        self.s=read("region_source_packages_v2.json")
    def test_withdrawn_countries_do_not_publish_medical_content(self):
        for code in CODES:
            self.c["countries"][code]["publicationAllowed"]=False
            self.c["countries"][code]["medicalReview"]["status"]="pending"
        out=build_public(self.c,date(2026,11,25))
        self.assertEqual(out["coverageCount"],174)
        self.assertEqual(out["approvedCount"],166)
        for code in CODES:
            self.assertNotIn(code,out["countries"])
            self.assertEqual(out["coverage"][code]["status"],"medical_review_required")
        for r in build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]:
            if r["country"] in CODES:
                self.assertNotIn("sourceNotice",r)
                self.assertNotIn("malaria",r)
    def test_complete_packages_with_route_options_and_explicit_stiko_basis(self):
        self.assertEqual(validate_all(self.c,self.g,self.s),174)
        for code in CODES:
            p=self.c["countries"][code]
            self.assertTrue(p["publicationAllowed"])
            self.assertEqual(p["medicalReview"]["status"],"approved")
            self.assertEqual(p["sourceReview"]["vaccinationBasis"]["authority"],"STIKO")
            self.assertGreaterEqual(len(p["routeAssessment"]["regionIds"]),2)
            self.assertTrue(p["missions"]["verifiedEntries"])
        self.assertIn("Typhus",self.c["countries"]["NP"]["vaccineAssessment"]["forAll"])
    def test_simulated_country_approval_retains_regional_source_conflicts(self):
        for code in CODES:
            p=self.c["countries"][code]
            p["publicationAllowed"]=True
            p["medicalReview"]={"status":"approved","reviewer":"TEST ONLY",
                "reviewedAt":"2026-11-15","nextReviewDate":"2027-01-15",
                "approvedSources":p["sourceReview"]["proposedSources"]}
            for f in ("vaccineAssessment","malariaAssessment","missions"):p[f]["status"]="approved"
        self.assertEqual(build_public(self.c,date(2026,11,25))["approvedCount"],170)
        rows={r["id"]:r for r in build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]}
        for rid in ("NP-WEST-LOW","MY-BORNEO-FOREST","PH-PALAWAN-N","PH-CEBU"):
            self.assertEqual(rows[rid]["clinicalStatus"],"source_conflict")
            self.assertNotIn("malaria",rows[rid])
        self.assertEqual(rows["PH-PALAWAN-S"]["malaria"]["riskLevel"],"high")
        self.assertEqual(rows["MY-KL"]["malaria"]["riskLevel"],"none")
    def test_preview_contains_new_country_batch_and_compact_itinerary(self):
        html=render(self.c,codes=CODES)
        for code in CODES:self.assertIn(self.c["countries"][code]["name"],html)
        for code in ("ES","IT","PT","GR"):
            route=self.c["countries"][code]["vaccineAssessment"]["routeDependent"]
            self.assertNotIn("Impfzuordnung nach",str(route))
            self.assertLess(len(" ".join(route)),400)
if __name__=="__main__":unittest.main()
