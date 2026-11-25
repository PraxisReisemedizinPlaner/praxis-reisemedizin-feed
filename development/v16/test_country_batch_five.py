from datetime import date
import json
from pathlib import Path
import unittest
from export_public_v16 import build_public
from export_public_regions_v2 import build_public_regions
from validate_route_requirements import validate_all
from build_country_review_preview import render
HERE=Path(__file__).resolve().parent
CODES=("MX","CR","DO","PE")
class FifthCountryBatchTests(unittest.TestCase):
    def setUp(self):
        read=lambda f:json.loads((HERE/f).read_text(encoding="utf-8"))
        self.c=read("country_profiles_draft_v16.json")
        self.g=read("region_profiles_draft_v1.json")
        self.s=read("region_source_packages_v2.json")
    def test_approved_batch_and_pending_batch_are_separate(self):
        out=build_public(self.c,date(2026,11,25))
        self.assertEqual(out["coverageCount"],146)
        self.assertEqual(out["approvedCount"],142)
        for code in ("KH","LA","ZA","BR"):
            self.assertIn(code,out["countries"])
            self.assertEqual(self.c["countries"][code]["medicalReview"]["reviewer"],"Dr. med. Sebastian Münster")
        for code in CODES:self.assertIn(code,out["countries"])
        for r in build_public_regions(self.g,self.c,self.s,date(2026,11,20))["regions"]:
            if r["country"] in CODES:
                self.assertIn("approvalScope",r)
    def test_routes_and_country_preview_complete(self):
        self.assertEqual(validate_all(self.c,self.g,self.s),146)
        for code in CODES:
            p=self.c["countries"][code]
            self.assertTrue(p["publicationAllowed"])
            self.assertEqual(p["sourceReview"]["vaccinationBasis"]["authority"],"STIKO")
            self.assertGreaterEqual(len(p["routeAssessment"]["regionIds"]),4)
            self.assertTrue(p["missions"]["verifiedEntries"])
        self.assertNotIn("Gelbfieber",self.c["countries"]["PE"]["vaccineAssessment"]["forAll"])
        html=render(self.c,codes=CODES)
        for code in CODES:self.assertIn(self.c["countries"][code]["name"],html)
    def test_simulated_approval_keeps_route_conflicts_and_expiry(self):
        for code in CODES:
            p=self.c["countries"][code]
            p["publicationAllowed"]=True
            p["medicalReview"]={"status":"approved","reviewer":"TEST ONLY","reviewedAt":"2026-11-16",
                "nextReviewDate":"2027-01-15","approvedSources":p["sourceReview"]["proposedSources"]}
            for f in ("vaccineAssessment","malariaAssessment","missions"):p[f]["status"]="approved"
        self.assertEqual(build_public(self.c,date(2026,11,25))["approvedCount"],142)
        rows={r["id"]:r for r in build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]}
        for rid in ("MX-CHIAPAS","CR-LIMON","DO-PUNTACANA","PE-IQUITOS"):
            self.assertEqual(rows[rid]["clinicalStatus"],"source_conflict")
            self.assertNotIn("malaria",rows[rid])
        self.assertEqual(rows["PE-CUSCO"]["malaria"]["riskLevel"],"none")
        expired={r["id"]:r for r in build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]}
        self.assertNotIn("sourceNotice",expired["CR-NORTHWEST"])
if __name__=="__main__":unittest.main()
