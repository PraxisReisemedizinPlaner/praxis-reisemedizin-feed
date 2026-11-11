#!/usr/bin/env python3
"""Safety regression tests for the public V16 export. Test data is synthetic."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest

from export_public_v16 import build_public

HERE = Path(__file__).resolve().parent
TODAY = date(2026, 11, 11)

class PublishingSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = json.loads((HERE / "country_profiles_draft_v16.json")
                               .read_text(encoding="utf-8"))

    def test_current_data_contains_no_approved_medical_assertions(self):
        out = build_public(copy.deepcopy(self.draft), TODAY)
        self.assertEqual(out["coverageCount"], 9)
        self.assertEqual(out["approvedCount"], 0)
        self.assertEqual(out["countries"], {})
        self.assertEqual(len(out["coverage"]), 9)
        self.assertNotIn("legacySnapshot", json.dumps(out))

    def test_a_pending_profile_can_never_be_flagged_for_publication(self):
        data = copy.deepcopy(self.draft)
        data["countries"]["MA"]["publicationAllowed"] = True
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

    def synthetic_approved(self):
        data = copy.deepcopy(self.draft)
        country = data["countries"]["MA"]
        country["publicationAllowed"] = True
        country["medicalReview"] = {
            "status": "approved",
            "reviewer": "TEST REVIEWER – NOT A REAL APPROVAL",
            "reviewedAt": "2026-11-11",
            "nextReviewDate": "2027-02-11",
            "approvedSources": [{
                "url": "https://example.org/test-only",
                "checkedAt": "2026-11-11",
                "reuseRightsChecked": True
            }]
        }
        country["vaccineAssessment"] = {
            "status": "approved", "forAll": [], "riskBased": [],
            "entryRequirements": [], "routeDependent": []
        }
        country["malariaAssessment"] = {
            "status": "approved", "riskLevel": "uncertain",
            "preventionType": "regional_assessment_required",
            "regions": [], "medicationName": None,
            "clinicalRecommendation": "TEST – incomplete data; review required",
            "sourceLinks": [{
                "label": "Direct DTG link only",
                "url": "https://www.dtg.org/empfehlungen-und-leitlinien/empfehlungen/malaria/karten.html",
                "use": "external_link_only"
            }]
        }
        country["missions"] = {"status": "approved", "verifiedEntries": [
            {"title": "TEST CONTACT – not an actual embassy"}]}
        return data

    def test_only_explicitly_approved_data_can_be_exported(self):
        data = self.synthetic_approved()
        out = build_public(data, TODAY)
        self.assertEqual(out["approvedCount"], 1)
        self.assertEqual(set(out["countries"]), {"MA"})
        rendered = json.dumps(out, ensure_ascii=False)
        self.assertNotIn("legacySnapshot", rendered)
        self.assertNotIn("TEST REVIEWER", rendered)
        self.assertNotIn("previousRiskBased", rendered)
        self.assertEqual(out["coverage"]["AT"]["status"], "medical_review_required")

    def test_expired_approval_not_exposed(self):
        data = self.synthetic_approved()
        data["countries"]["MA"]["medicalReview"]["reviewedAt"] = "2026-10-11"
        data["countries"]["MA"]["medicalReview"]["nextReviewDate"] = "2026-11-10"
        out = build_public(data, TODAY)
        self.assertEqual(out["approvedCount"], 0)
        self.assertEqual(out["countries"], {})

    def test_dtg_structured_use_blocked(self):
        data = self.synthetic_approved()
        data["countries"]["MA"]["malariaAssessment"]["sourceLinks"][0]["use"] = "structured_import"
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

    def test_missing_rights_check_blocks_publication(self):
        data = self.synthetic_approved()
        data["countries"]["MA"]["medicalReview"]["approvedSources"][0]["reuseRightsChecked"] = False
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

    def test_missing_section_approval_blocks_publication(self):
        data = self.synthetic_approved()
        data["countries"]["MA"]["missions"]["status"] = "needs_verification"
        with self.assertRaises(ValueError):
            build_public(data, TODAY)

if __name__ == "__main__":
    unittest.main()
