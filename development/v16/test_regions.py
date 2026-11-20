#!/usr/bin/env python3
"""Region directory is safe to publish, medical claims need an independent sign-off."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest

from export_public_regions_v1 import build_public_regions

ROOT=Path(__file__).resolve().parent
TODAY=date(2026,11,18)

class RegionSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((ROOT/"region_profiles_draft_v1.json").read_text(encoding="utf-8"))
        cls.approved_catalogue=copy.deepcopy(cls.r)
        # Synthetic pending fixture keeps each independent publication-gate test isolated.
        for row in cls.r["regions"]:
            row["publicationAllowed"]=False
            row["clinicalReview"]["status"]="pending"
        cls.c=json.loads((ROOT/"country_profiles_draft_v16.json").read_text(encoding="utf-8"))

    def published(self,r=None,c=None,as_of=TODAY):
        return build_public_regions(copy.deepcopy(r or self.r),copy.deepcopy(c or self.c),as_of)

    def test_names_without_any_clinical_risk(self):
        out=self.published()
        self.assertEqual(out["geographyCount"],208)
        self.assertEqual(out["regionalApprovedCount"],0)
        self.assertTrue(all(x["clinicalStatus"]=="medical_review_required" for x in out["regions"]))
        blob=json.dumps(out,ensure_ascii=False)
        for forbidden in ("clinicalRecommendation","malariaAssessment","preventionType","medicationName","sourceUrls","riskLevel"):
            self.assertNotIn(forbidden,blob)
        self.assertIn("Little Koh Chang (Ranong",blob)
        self.assertIn("Ko Chang (Trat",blob)

    def test_all_twenty_five_explicit_physician_releases(self):
        out=self.published(self.approved_catalogue)
        approved={row["id"]:row for row in out["regions"] if row["clinicalStatus"]=="approved"}
        self.assertEqual(set(approved),{r["id"] for r in self.approved_catalogue["regions"] if r["publicationAllowed"]})
        self.assertEqual(len(approved),25)
        self.assertEqual(approved["TH-BKK"]["malaria"]["riskLevel"],"uncertain")
        self.assertEqual(approved["TH-LITTLE-CHANG-RANONG"]["malaria"]["preventionType"],"regional_assessment_required")
        self.assertEqual(approved["TH-PTY"]["malaria"]["riskLevel"],"none")
        self.assertEqual(approved["ID-JKT"]["malaria"]["riskLevel"],"none")
        self.assertEqual(approved["TH-HKT"]["malaria"]["preventionType"],"exposure_only")
        self.assertEqual(approved["ID-SUMBA"]["malaria"]["preventionType"],"chemoprophylaxis_consider")
        for row in out["regions"]:
            if row["id"] not in approved:
                self.assertNotIn("malaria",row)

    def test_publication_flag_alone_cannot_publish(self):
        d=copy.deepcopy(self.r); d["regions"][0]["publicationAllowed"]=True
        with self.assertRaises(ValueError):self.published(d)

    def test_region_requires_parent_medical_release(self):
        d=copy.deepcopy(self.r);r=d["regions"][0]
        self.approve(r)
        c=copy.deepcopy(self.c);c["countries"]["TH"]["publicationAllowed"]=False
        with self.assertRaises(ValueError):self.published(d,c)

    def approve(self,r):
        r["publicationAllowed"]=True
        r["clinicalReview"]={"status":"approved","reviewer":"Dr. med. Sebastian Münster",
            "reviewedAt":"2026-11-15","nextReviewDate":"2027-01-15",
            "sourceUrls":["https://www.auswaertiges-amt.de/de/service/laender/thailand-node/thailandsicherheit-201558"],
            "reuseRightsChecked":True}
        r["malariaAssessment"]={"riskLevel":"none","preventionType":"none",
            "medicationName":None,"clinicalRecommendation":"Nur Testdaten – nicht für reale Veröffentlichung"}

    def test_approved_region_only_after_all_gates(self):
        d=copy.deepcopy(self.r); self.approve(d["regions"][0])
        out=self.published(d)
        self.assertEqual(out["regionalApprovedCount"],1)
        self.assertEqual(out["regions"][0]["clinicalStatus"],"approved")
        self.assertIn("malaria",out["regions"][0])
        self.assertNotIn("reviewer",json.dumps(out).lower())

    def test_expired_region_never_provides_medical_advice(self):
        d=copy.deepcopy(self.r); self.approve(d["regions"][0])
        r=d["regions"][0];r["clinicalReview"]["reviewedAt"]="2026-10-15";r["clinicalReview"]["nextReviewDate"]="2026-11-14"
        out=self.published(d)
        self.assertEqual(out["regionalApprovedCount"],0)
        self.assertNotIn("malaria",out["regions"][0])

    def test_rights_missing_blocks_medical_publication(self):
        d=copy.deepcopy(self.r); self.approve(d["regions"][0])
        d["regions"][0]["clinicalReview"]["reuseRightsChecked"]=False
        with self.assertRaises(ValueError):self.published(d)

    def test_dtg_cannot_be_used_as_region_data(self):
        d=copy.deepcopy(self.r); self.approve(d["regions"][0])
        d["regions"][0]["clinicalReview"]["sourceUrls"]=["https://www.dtg.org/empfehlungen/malaria"]
        with self.assertRaises(ValueError):self.published(d)

    def test_medication_name_not_allowed_by_default(self):
        d=copy.deepcopy(self.r); self.approve(d["regions"][0])
        d["regions"][0]["malariaAssessment"]["medicationName"]="Test drug"
        with self.assertRaises(ValueError):self.published(d)

    def test_duplicate_or_malformed_region_ids_fail(self):
        d=copy.deepcopy(self.r);d["regions"][1]["id"]=d["regions"][0]["id"]
        with self.assertRaises(ValueError):self.published(d)

if __name__=="__main__":
    unittest.main()
