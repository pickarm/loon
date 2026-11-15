"""Regression checks for exact Gemini iOS domain routing."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_config as renderer


class GeminiOverridesTest(unittest.TestCase):
    def test_expected_hosts_are_exact_and_not_broad_google_suffixes(self):
        override = ROOT / "override" / "gemini.list"
        entries = {
            line.strip() for line in override.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        hosts = {
            "gemini.google.com",
            "jnn-pa.googleapis.com",
            "waa-pa.clients6.google.com",
            "ogads-pa.clients6.google.com",
            "optimizationguide-pa.googleapis.com",
            "www.googleapis.com",
            "ogs.google.com",
            "ssl.gstatic.com",
            "fonts.googleapis.com",
            "www.gstatic.com",
        }
        self.assertEqual(entries, {f"DOMAIN,{domain}" for domain in hosts})

    def test_ai_bundle_is_before_direct_and_uses_existing_remote_rule_slot(self):
        specs = renderer.BUNDLE_SPECS
        names = [spec["path"] for spec in specs]
        self.assertLess(names.index("Bundles/AI.list"), names.index("Bundles/Direct.list"))
        self.assertIn("{{REMOTE_RULES}}", renderer.TEMPLATE)
        self.assertNotIn("FINAL,🌐 国外网站", renderer.TEMPLATE)

    def test_existing_direct_conflicts_are_overridden_in_ai_bundle(self):
        # These were intentionally DIRECT in the old bundle. The AI remote
        # ruleset is first so the exact Gemini entries are evaluated first.
        entries = {
            line.strip() for line in (ROOT / "override" / "gemini.list").read_text(encoding="utf-8").splitlines()
        }
        for host in ("ssl.gstatic.com", "fonts.googleapis.com", "www.gstatic.com"):
            self.assertIn(f"DOMAIN,{host}", entries)


if __name__ == "__main__":
    unittest.main()
