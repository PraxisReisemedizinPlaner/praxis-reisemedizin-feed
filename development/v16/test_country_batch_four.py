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
CODES=("KH","LA","ZA","BR")
class FourthCountryBatchTests(unittest.TestCase):
    def setUp(self):
        read=lambda f:json.loads((HERE/f).read_text(encoding="utf-8"))
        self.c=read("country_profiles_draft_v16.json")
        self.g=read("region_profiles_draft_v1.json")
        self.s=read("region_source_packages_v2.json")
    def test_withdrawn_country_packages_stay_private(self):
        for code in CODES:
            self.c["countries"][code]["publicationAllowed"]=False
            self.c["countries"][code]["medicalReview"]["status"]="pending"
        out=build_public(self.c,date(2026,11,21))
        self.assertEqual(out["coverageCount"],98)
        self.assertEqual(out["approvedCount"],90)
        for code in ("LK","NP","MY","PH"):
            self.assertIn(code,out["countries"])
            self.assertEqual(self.c["countries"][code]["medicalReview"]["reviewer"],"Dr. med. Sebastian Münster")
        for code in CODES:self.assertNotIn(code,out["countries"])
        for r in build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]:
            if r["country"] in CODES:
                self.assertNotIn("malaria",r)
                self.assertNotIn("sourceNotice",r)
    def test_country_routes_sources_and_contacts_ready(self):
        self.assertEqual(validate_all(self.c,self.g,self.s),98)
        for code in CODES:
            p=self.c["countries"][code]
            self.assertTrue(p["publicationAllowed"])
            self.assertEqual(p["medicalReview"]["status"],"approved")
            self.assertGreaterEqual(len(p["routeAssessment"]["regionIds"]),4)
            self.assertTrue(p["missions"]["verifiedEntries"])
        self.assertIn("Polio",self.c["countries"]["LA"]["vaccineAssessment"]["forAll"])
        self.assertNotIn("Gelbfieber",self.c["countries"]["BR"]["vaccineAssessment"]["forAll"])
        self.assertTrue(any("Gelbfieber" in x for x in self.c["countries"]["BR"]["vaccineAssessment"]["riskBased"]))
    def test_simulated_approval_keeps_conflicts_unclassified(self):
        for code in CODES:
            p=self.c["countries"][code]
            p["publicationAllowed"]=True
            p["medicalReview"]={"status":"approved","reviewer":"TEST ONLY","reviewedAt":"2026-11-15",
                "nextReviewDate":"2027-01-15","approvedSources":p["sourceReview"]["proposedSources"]}
            for f in ("vaccineAssessment","malariaAssessment","missions"):p[f]["status"]="approved"
        self.assertEqual(build_public(self.c,date(2026,11,21))["approvedCount"],94)
        rows={r["id"]:r for r in build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]}
        for rid in ("KH-ANGKOR","ZA-KRUGER","BR-IGUACU"):
            self.assertEqual(rows[rid]["clinicalStatus"],"source_conflict")
            self.assertNotIn("malaria",rows[rid])
        self.assertEqual(rows["KH-PHNOM"]["malaria"]["riskLevel"],"none")
        self.assertEqual(rows["LA-NORTH"]["malaria"]["riskLevel"],"low")
        html=render(self.c,codes=CODES)
        for code in CODES:self.assertIn(self.c["countries"][code]["name"],html)
if __name__=="__main__":unittest.main()
