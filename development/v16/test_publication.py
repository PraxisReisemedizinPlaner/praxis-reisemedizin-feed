#!/usr/bin/env python3
"""Safety regression tests for medically reviewed V16 public feed."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest

from export_public_v16 import build_public

HERE = Path(__file__).resolve().parent
TODAY = date(2026, 11, 11)
APPROVED = {"MA", "AT"}
PENDING = {"TH", "ID", "TZ", "KE", "VN", "IN", "EG"}


class PublishingSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = json.loads((HERE / "country_profiles_draft_v16.json")
                               .read_text(encoding="utf-8"))

    def test_only_reviewed_countries_are_exported(self):
        out = build_public(copy.deepcopy(self.draft), TODAY)
        self.assertEqual(out["coverageCount"], 9)
        self.assertEqual(out["approvedCount"], 2)
        self.assertEqual(set(out["countries"]), APPROVED)
        self.assertEqual(set(out["coverage"]), APPROVED | PENDING)
        self.assertTrue(all(out["coverage"][code]["status"] == "medical_review_required"
                            for code in PENDING))
        self.assertTrue(all(out["coverage"][code]["status"] == "verified"
                            for code in APPROVED))
        rendered = json.dumps(out, ensure_ascii=False)
        self.assertNotIn("legacySnapshot", rendered)
        self.assertNotIn("previousRiskBased", rendered)
        self.assertNotIn("reviewer", rendered.lower())

    def test_austria_has_no_blanket_hepatitis_b_recommendation(self):
        out = build_public(copy.deepcopy(self.draft), TODAY)
        vaccinations = json.dumps(out["countries"]["AT"]["vaccinations"],
                                  ensure_ascii=False).lower()
        self.assertNotIn("hepatitis b", vaccinations)
        self.assertIn("fsm", vaccinations)
        self.assertIn("stiko", vaccinations)

    def test_marocco_has_indicated_hbv_only(self):
        out = build_public(copy.deepcopy(self.draft), TODAY)
        at_risk = out["countries"]["MA"]["vaccinations"]["riskBased"]
        self.assertTrue(any("Hepatitis B bei individueller Indikation" in v
                            for v in at_risk))

    def test_pending_country_cannot_be_published_by_flag_alone(self):
        data = copy.deepcopy(self.draft)
        data["countries"]["TH"]["publicationAllowed"] = True
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

    def test_unapproved_country_not_leaked_if_notes_added(self):
        data = copy.deepcopy(self.draft)
        data["countries"]["TH"]["vaccineAssessment"]["forAll"] = [
            "TEST – not reviewed"]
        out = build_public(data, TODAY)
        self.assertNotIn("TEST – not reviewed", json.dumps(out))
        self.assertEqual(set(out["countries"]), APPROVED)

    def test_expired_approval_is_omitted(self):
        data = copy.deepcopy(self.draft)
        data["countries"]["MA"]["medicalReview"]["reviewedAt"] = "2026-10-11"
        data["countries"]["MA"]["medicalReview"]["nextReviewDate"] = "2026-11-10"
        out = build_public(data, TODAY)
        self.assertEqual(set(out["countries"]), {"AT"})
        self.assertEqual(out["coverage"]["MA"]["status"],
                         "medical_review_required")

    def test_dtg_structured_reuse_blocked(self):
        data = copy.deepcopy(self.draft)
        links = data["countries"]["MA"]["malariaAssessment"]["sourceLinks"]
        dtg = next(s for s in links if "dtg.org" in s["url"])
        dtg["use"] = "structured_import"
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

    def test_missing_rights_review_blocks_publication(self):
        data = copy.deepcopy(self.draft)
        sources = data["countries"]["MA"]["medicalReview"]["approvedSources"]
        sources[0]["reuseRightsChecked"] = False
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

    def test_missing_clinical_section_approval_blocks_publication(self):
        data = copy.deepcopy(self.draft)
        data["countries"]["AT"]["missions"]["status"] = "needs_verification"
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

    def test_missing_reviewer_blocks_publication(self):
        data = copy.deepcopy(self.draft)
        data["countries"]["MA"]["medicalReview"]["reviewer"] = None
        with self.assertRaises(ValueError):
            build_public(data, TODAY)


if __name__ == "__main__":
    unittest.main()
