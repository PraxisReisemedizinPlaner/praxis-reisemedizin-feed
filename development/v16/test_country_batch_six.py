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
    def test_approved_batch_and_review_preview(self):
        out=build_public(self.c,date(2026,11,22))
        self.assertEqual(out["coverageCount"],122)
        self.assertEqual(out["approvedCount"],118)
        for code in CODES:
            self.assertIn(code,out["countries"])
            self.assertEqual(self.c["countries"][code]["medicalReview"]["reviewedAt"],"2026-11-18")
        review_codes = ("AD", "MC", "SM", "LI")
        preview = render(self.c, codes=review_codes)
        self.assertEqual(preview.count("<article id="), len(review_codes))
        for code in review_codes:
            self.assertFalse(self.c["countries"][code]["routeAssessment"]["regionalSelectionRequired"])
            self.assertIn("<article id='" + code + "'>", preview)
            self.assertIn(code,out["countries"])
            self.assertTrue(self.c["countries"][code]["publicationAllowed"])
            self.assertEqual(out["countries"][code]["medicalReviewDate"], "2026-11-22")
        self.assertIn("FSME bei Zeckenexposition", self.c["countries"]["LI"]["vaccineAssessment"]["riskBased"])
        self.assertIn("2.000 m", preview)
        self.assertEqual(preview.count("class='badge'>Freigegeben"), len(review_codes))
        next_preview = render(self.c)
        for code in ("MH", "FM", "PW", "GU"):
            self.assertIn("<article id='" + code + "'>", next_preview)
            self.assertNotIn(code, out["countries"])
        self.assertIn("Tollwut · Typhus", next_preview)
        self.assertIn("US-Grenzbehörde", next_preview)
        self.assertTrue({"CK", "NU", "NR", "KI"}.issubset(out["countries"]))
        bhutan_south = next(row for row in self.s["regions"] if row["id"] == "BT-SOUTH")
        self.assertEqual(bhutan_south["status"], "source_conflict")
        self.assertNotIn("preventionType", bhutan_south)
        rows=build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]
        approved_batch = {"CO", "EC", "BO", "VE", "PA", "GT", "HN", "SV", "NI", "BZ", "CU", "JM", "BS", "BB", "DM", "GD", "AG", "LC", "KN", "VC"}
        self.assertTrue(approved_batch.issubset(out["countries"]))
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id["CO-AMZ"]["malaria"]["riskLevel"], "high")
        self.assertEqual(by_id["EC-YASUNI"]["clinicalStatus"], "source_conflict")
        self.assertNotIn("malaria", by_id["EC-YASUNI"])
        self.assertEqual(by_id["BO-HIGH"]["malaria"]["riskLevel"], "none")
        self.assertEqual(by_id["VE-CITY"]["clinicalStatus"], "source_conflict")
        self.assertEqual(by_id["PA-ANCON"]["clinicalStatus"], "source_conflict")
        self.assertNotIn("malaria", by_id["PA-ANCON"])
        self.assertEqual(by_id["HN-EAST"]["clinicalStatus"], "source_based")
        self.assertEqual(by_id["NI-NORTH"]["malaria"]["preventionType"], "chemoprophylaxis_consider")
        self.assertEqual(by_id["NI-CORN"]["clinicalStatus"], "source_conflict")
        self.assertNotIn("malaria", by_id["NI-CORN"])
        for r in rows:
            if r["country"] in review_codes:
                self.assertNotIn("malaria",r)
                self.assertNotIn("sourceNotice",r)
    def test_routes_and_evidence_are_complete(self):
        self.assertEqual(validate_all(self.c,self.g,self.s),122)
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
        self.assertEqual(build_public(self.c,date(2026,11,22))["approvedCount"],118)
        rows={r["id"]:r for r in build_public_regions(self.g,self.c,self.s,date(2026,11,21))["regions"]}
        for rid in ("NA-ETOSHA","NA-KUNENE","BW-OKAVANGO","BW-GABORONE"):
            self.assertEqual(rows[rid]["clinicalStatus"],"source_conflict")
            self.assertNotIn("malaria",rows[rid])
        self.assertEqual(rows["NA-ZAMBEZI"]["malaria"]["riskLevel"],"high")
        self.assertEqual(rows["NA-WINDHOEK"]["malaria"]["riskLevel"],"none")
        self.assertIn("Juni",rows["NA-ETOSHA"]["sourceNotice"])
if __name__=="__main__":unittest.main()
