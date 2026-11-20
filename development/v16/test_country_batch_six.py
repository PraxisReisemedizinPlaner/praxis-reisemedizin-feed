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
CODES=("NA","BW","MU","SC")
class SixthCountryBatchTests(unittest.TestCase):
    def setUp(self):
        read=lambda f:json.loads((HERE/f).read_text(encoding="utf-8"))
        self.c=read("country_profiles_draft_v16.json")
        self.g=read("region_profiles_draft_v1.json")
        self.s=read("region_source_packages_v2.json")
    def test_approved_batch_and_next_drafts_are_separate(self):
        out=build_public(self.c,date(2026,11,20))
        self.assertEqual(out["coverageCount"],62)
        self.assertEqual(out["approvedCount"],58)
        for code in CODES:
            self.assertIn(code,out["countries"])
            self.assertEqual(self.c["countries"][code]["medicalReview"]["reviewedAt"],"2026-11-18")
        next_codes = ("GB", "IE", "NL", "BE")
        preview = render(self.c)
        self.assertEqual(preview.count("<article id="), len(next_codes))
        for code in next_codes:
            self.assertEqual(self.c["countries"][code]["routeAssessment"]["regionalSelectionRequired"], code in ("GB", "NL"))
            self.assertIn("<article id='" + code + "'>", preview)
            self.assertNotIn(code,out["countries"])
            self.assertFalse(self.c["countries"][code]["publicationAllowed"])
        rows=build_public_regions(self.g,self.c,self.s,date(2026,11,20))["regions"]
        for r in rows:
            if r["country"] in next_codes:
                self.assertNotIn("malaria",r)
                self.assertNotIn("sourceNotice",r)
    def test_routes_and_evidence_are_complete(self):
        self.assertEqual(validate_all(self.c,self.g,self.s),62)
        self.assertEqual(sum(r["country"] in CODES for r in self.g["regions"]),12)
        for code in ("NA","BW"):
            self.assertTrue(self.c["countries"][code]["routeAssessment"]["regionalSelectionRequired"])
        for code in ("MU","SC"):
            self.assertFalse(self.c["countries"][code]["routeAssessment"]["regionalSelectionRequired"])
            self.assertEqual(self.c["countries"][code]["malariaAssessment"]["riskLevel"],"none")
            self.assertIn("widersprüchliche" if code=="MU" else "Quellenabweichung",
                str(self.c["countries"][code]["vaccineAssessment"]["routeDependent"]))
        self.assertIn("Polio",self.c["countries"]["NA"]["vaccineAssessment"]["forAll"])
        self.assertIn("Antananarivo",str(self.c["countries"]["MU"]["missions"]))
        self.assertNotIn("Pretoria",str(self.c["countries"]["MU"]["missions"]))
        html=render(self.c,codes=CODES)
        for code in CODES:self.assertIn(self.c["countries"][code]["name"],html)
        self.assertIn("2026-11-18",html)
    def test_release_keeps_seasonal_conflicts_unclassified(self):
        self.assertEqual(build_public(self.c,date(2026,11,20))["approvedCount"],58)
        rows={r["id"]:r for r in build_public_regions(self.g,self.c,self.s,date(2026,11,20))["regions"]}
        for rid in ("NA-ETOSHA","NA-KUNENE","BW-OKAVANGO","BW-GABORONE"):
            self.assertEqual(rows[rid]["clinicalStatus"],"source_conflict")
            self.assertNotIn("malaria",rows[rid])
        self.assertEqual(rows["NA-ZAMBEZI"]["malaria"]["riskLevel"],"high")
        self.assertEqual(rows["NA-WINDHOEK"]["malaria"]["riskLevel"],"none")
        self.assertIn("Juni",rows["NA-ETOSHA"]["sourceNotice"])
if __name__=="__main__":unittest.main()
