import copy
from datetime import date
import json
from pathlib import Path
import unittest
from export_public_v16 import build_public
from build_country_review_preview import render
HERE=Path(__file__).resolve().parent
CODES={"TZ","KE","VN","IN"}
class NextCountryPackageTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((HERE/"country_profiles_draft_v16.json").read_text(encoding="utf-8"))
    def test_four_physician_approved_countries_are_published(self):
        public=build_public(self.data,date(2026,11,25))
        self.assertEqual(public["approvedCount"],170)
        for code in CODES:
            p=self.data["countries"][code]
            self.assertTrue(p["publicationAllowed"])
            self.assertEqual(p["medicalReview"]["status"],"approved")
            self.assertEqual(p["medicalReview"]["reviewer"],"Dr. med. Sebastian Münster")
            self.assertEqual(p["medicalReview"]["reviewedAt"],"2026-11-15")
            self.assertIn(code,public["countries"])
            self.assertEqual(public["coverage"][code]["status"],"verified")
    def test_withdrawn_country_package_is_not_published(self):
        for code in CODES:
            data=copy.deepcopy(self.data)
            data["countries"][code]["publicationAllowed"]=False
            data["countries"][code]["medicalReview"]["status"]="pending"
            public=build_public(data,date(2026,11,25))
            self.assertNotIn(code,public["countries"])
            self.assertEqual(public["coverage"][code]["status"],"medical_review_required")
    def test_draft_completeness_and_simulated_release(self):
        simulated=copy.deepcopy(self.data)
        for code in CODES:
            p=simulated["countries"][code]
            self.assertTrue(p["sourceReview"]["researchReady"])
            self.assertTrue(p["vaccineAssessment"]["forAll"])
            self.assertTrue(p["vaccineAssessment"]["routeDependent"])
            self.assertTrue(p["malariaAssessment"]["regions"])
            self.assertIsNone(p["malariaAssessment"]["medicationName"])
            self.assertTrue(p["missions"]["verifiedEntries"])
            sources=p["sourceReview"]["proposedSources"]
            self.assertGreaterEqual(len(sources),4)
            p["medicalReview"]={"status":"approved","reviewer":"TEST ONLY – never publish this fixture",
                "reviewedAt":"2026-11-15","nextReviewDate":"2027-01-15","approvedSources":sources}
            for key in ("vaccineAssessment","malariaAssessment","missions"):p[key]["status"]="approved"
            p["publicationAllowed"]=True
        public=build_public(simulated,date(2026,11,25))
        self.assertEqual(public["approvedCount"],170)
        self.assertTrue(CODES.issubset(public["countries"]))
        self.assertNotIn("TEST ONLY",json.dumps(public))
    def test_source_disagreements_and_route_constraints_preserved(self):
        p=self.data["countries"]
        self.assertIn("1.800",json.dumps(p["TZ"]["malariaAssessment"],ensure_ascii=False))
        self.assertIn("2.500",json.dumps(p["TZ"]["malariaAssessment"],ensure_ascii=False))
        self.assertIn("Nairobi",json.dumps(p["KE"]["malariaAssessment"],ensure_ascii=False))
        self.assertIn("Gelbfieber",json.dumps(p["KE"]["vaccineAssessment"],ensure_ascii=False))
        self.assertIn("Ho-Chi-Minh",json.dumps(p["VN"]["malariaAssessment"],ensure_ascii=False))
        self.assertIn("CDC",json.dumps(p["IN"]["malariaAssessment"],ensure_ascii=False))
        self.assertIn("ABHAYRAB",json.dumps(p["IN"]["vaccineAssessment"],ensure_ascii=False))
    def test_review_preview_contains_exact_drafts_and_warning(self):
        html=render(self.data,codes=tuple(sorted(CODES)))
        self.assertIn("Ärztliche Prüfvorschau",html)
        self.assertIn("keine Patientenempfehlung",html)
        self.assertIn("noindex,nofollow",html)
        for code in CODES:
            self.assertIn(self.data["countries"][code]["name"],html)
            self.assertIn(self.data["countries"][code]["malariaAssessment"]["clinicalRecommendation"],html)
if __name__=="__main__":unittest.main()
