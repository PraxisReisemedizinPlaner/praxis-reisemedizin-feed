import copy
import json
from datetime import date
from pathlib import Path
import unittest
from export_public_regions_v2 import build_public_regions
HERE=Path(__file__).resolve().parent
class CountryPackageTests(unittest.TestCase):
    def setUp(self):
        read=lambda n:json.loads((HERE/n).read_text(encoding="utf-8"))
        self.g=read("region_profiles_draft_v1.json")
        self.c=read("country_profiles_draft_v16.json")
        self.p=read("region_source_packages_v2.json")
    def out(self,today=date(2026,11,18)):
        return build_public_regions(self.g,self.c,self.p,today)
    def row(self,rid):
        return next(r for r in self.out()["regions"] if r["id"]==rid)
    def source(self,rid):
        return next(r for r in self.p["regions"] if r["id"]==rid)
    def test_no_local_signoff_needed(self):
        for r in self.g["regions"]:
            r["publicationAllowed"]=False
            r["clinicalReview"]["status"]="pending"
        self.assertEqual(self.out()["sourceBasedCount"],51)
        self.assertEqual(self.row("TH-USM")["approvalScope"],"country_package")
    def test_conflict_never_becomes_low_risk(self):
        r=self.row("TH-BKK")
        self.assertEqual(r["clinicalStatus"],"source_conflict")
        self.assertNotIn("malaria",r)
        self.assertIn("CDC",r["sourceNotice"])
    def test_route_exception_is_not_approval_task(self):
        r=self.row("ID-FLORES")
        self.assertEqual(r["clinicalStatus"],"route_required")
        self.assertNotIn("malaria",r)
        self.assertEqual(self.out()["exceptionCount"],169)
    def test_withdrawn_or_expired_country_suppresses_only_that_country(self):
        for status in ("withdrawn","expired"):
            if status=="withdrawn": self.c["countries"]["TH"]["publicationAllowed"]=False
            else:
                self.c["countries"]["TH"]["publicationAllowed"]=True
                self.c["countries"]["TH"]["medicalReview"]["nextReviewDate"]="2026-11-14"
            rows=self.out()["regions"]
            self.assertTrue(all("malaria" not in r and "sourceNotice" not in r for r in rows if r["country"]=="TH"))
            self.assertIn("malaria",next(r for r in rows if r["id"]=="ID-SUMBA"))
    def test_future_country_not_currently_approved(self):
        self.c["countries"]["TH"]["medicalReview"]["reviewedAt"]="2026-11-19"
        self.assertNotIn("malaria",self.row("TH-USM"))
    def test_expired_or_future_sources_hide_assessment(self):
        r=self.source("TH-USM")
        r["nextSourceCheckDate"]="2026-11-14"
        self.assertNotIn("malaria",self.row("TH-USM"))
        r["nextSourceCheckDate"]="2027-01-15";r["checkedAt"]="2026-11-19"
        self.assertNotIn("malaria",self.row("TH-USM"))
    def test_missing_sources_do_not_inherit_country_risk(self):
        self.p["regions"]=[r for r in self.p["regions"] if r["id"]!="TH-USM"]
        self.assertEqual(self.row("TH-USM")["clinicalStatus"],"source_unavailable")
        self.assertNotIn("malaria",self.row("TH-USM"))
    def test_forbidden_source_and_drug_data_suppressed(self):
        r=self.source("TH-USM")
        r["sourceUrls"]=["https://www.dtg.org/maps","https://wwwnc.cdc.gov/travel"]
        self.assertNotIn("malaria",self.row("TH-USM"))
        r["sourceUrls"]=self.source("TH-HKT")["sourceUrls"]
        r["medicationName"]="test"
        self.assertNotIn("malaria",self.row("TH-USM"))
    def test_no_local_physician_label_or_details_in_feed(self):
        blob=json.dumps(self.out())
        self.assertNotIn("reviewer",blob)
        self.assertNotIn("medicationName",blob)
        self.assertNotIn("clinicalReview",blob)
    def test_conflict_cannot_publish_a_risk(self):
        self.source("TH-BKK")["riskLevel"]="none"
        with self.assertRaises(ValueError): self.out()
    def test_scope_mismatch_suppressed(self):
        self.source("TH-USM")["scope"]="different island"
        self.assertNotIn("malaria",self.row("TH-USM"))
if __name__=="__main__": unittest.main()
