import copy
from datetime import date
import json
from pathlib import Path
import unittest
from export_public_v16 import build_public
from export_public_regions_v2 import build_public_regions
from validate_route_requirements import validate_all
from route_planning import validate_route_assessment
from build_country_review_preview import render
HERE=Path(__file__).resolve().parent
class RoutePlanningTests(unittest.TestCase):
    def setUp(self):
        read=lambda n:json.loads((HERE/n).read_text(encoding="utf-8"))
        self.c=read("country_profiles_draft_v16.json")
        self.g=read("region_profiles_draft_v1.json")
        self.s=read("region_source_packages_v2.json")
    def regions(self,c=None):
        return build_public_regions(self.g,c or self.c,self.s,date(2026,11,15))
    def test_all_countries_have_explicit_route_decision(self):
        self.assertEqual(validate_all(self.c,self.g,self.s),14)
        for code in ("TH","ID","IN","TZ","KE","VN","GR","PT"):
            self.assertTrue(self.c["countries"][code]["routeAssessment"]["regionalSelectionRequired"])
    def test_india_has_thirteen_actual_route_options(self):
        rows={r["id"]:r for r in self.regions()["regions"] if r["country"]=="IN"}
        self.assertEqual(len(rows),13)
        self.assertEqual(rows["IN-GEEDAM"]["malaria"]["riskLevel"],"high")
        self.assertEqual(rows["IN-DELHI"]["clinicalStatus"],"source_conflict")
        self.assertNotIn("malaria",rows["IN-DELHI"])
        self.assertEqual(rows["IN-HIMALAYA"]["clinicalStatus"],"route_required")
        self.assertNotIn("malaria",rows["IN-HIMALAYA"])
    def test_other_active_regional_countries_have_options(self):
        rows={r["id"]:r for r in self.regions()["regions"]}
        self.assertEqual(rows["TZ-ZANZIBAR"]["malaria"]["riskLevel"],"high")
        self.assertEqual(rows["KE-NAIROBI-CENTRE"]["malaria"]["riskLevel"],"low")
        self.assertEqual(rows["KE-MOMBASA"]["malaria"]["riskLevel"],"high")
        self.assertEqual(rows["VN-HANOI"]["malaria"]["riskLevel"],"none")
    def test_future_country_without_regional_decision_is_blocked(self):
        del self.c["countries"]["IN"]["routeAssessment"]
        with self.assertRaises(ValueError): build_public(self.c,date(2026,11,15))
    def test_required_country_without_regions_is_blocked(self):
        self.c["countries"]["IN"]["routeAssessment"]["regionIds"]=[]
        with self.assertRaises(ValueError): validate_all(self.c,self.g,self.s)
    def test_missing_catalogue_or_source_is_blocked(self):
        self.g["regions"]=[r for r in self.g["regions"] if r["id"]!="IN-GEEDAM"]
        with self.assertRaises(ValueError): validate_all(self.c,self.g,self.s)
    def test_regional_malaria_cannot_claim_no_route_requirement(self):
        self.c["countries"]["IN"]["routeAssessment"]["regionalSelectionRequired"]=False
        with self.assertRaises(ValueError):validate_all(self.c,self.g,self.s)
    def test_unapproved_new_countries_and_regional_advice_not_published(self):
        out=build_public(self.c,date(2026,11,15))
        self.assertEqual(out["approvedCount"],10)
        for code in ("ES","IT","GR","PT"):
            self.assertNotIn(code,out["countries"])
        for row in self.regions()["regions"]:
            if row["country"] in ("GR","PT"):
                self.assertNotIn("malaria",row)
                self.assertNotIn("sourceNotice",row)
    def test_four_country_package_ready_for_single_medical_decision(self):
        c=copy.deepcopy(self.c)
        for code in ("ES","IT","GR","PT"):
            p=c["countries"][code]
            p["medicalReview"]={"status":"approved","reviewer":"TEST ONLY",
                "reviewedAt":"2026-11-15","nextReviewDate":"2027-01-15",
                "approvedSources":p["sourceReview"]["proposedSources"]}
            p["publicationAllowed"]=True
            for field in ("vaccineAssessment","malariaAssessment","missions"):
                p[field]["status"]="approved"
        self.assertEqual(build_public(c,date(2026,11,15))["approvedCount"],14)
        rows={r["id"]:r for r in self.regions(c)["regions"]}
        self.assertIn("Dengue",rows["PT-MADEIRA"]["malaria"]["clinicalRecommendation"])
        self.assertIn("Dengue",c["countries"]["PT"]["vaccineAssessment"]["routeDependent"][0])
        self.assertEqual(c["countries"]["IT"]["vaccineAssessment"]["forAll"],[])
        html=render(self.c)
        for name in ("Spanien","Italien","Griechenland","Portugal"): self.assertIn(name,html)
if __name__=="__main__":unittest.main()
