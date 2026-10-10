"""Regression tests for shared-CDN provider-wide routing guard."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_config as rc


class SharedCdnGuardTests(unittest.TestCase):
    def test_all_catalog_roots_are_suppressed_from_generic_proxy(self):
        self.assertGreaterEqual(len(rc.SHARED_CDN_ROOTS), 10)
        for root in rc.SHARED_CDN_ROOTS:
            rule = f"DOMAIN-SUFFIX,{root}"
            self.assertTrue(rc.blanket_shared_cdn_rule(rule), root)
            self.assertFalse(rc.keep_generic_proxy_rule(rule, set()), root)

    def test_specific_cdn_host_and_subdomain_are_kept(self):
        for rule in (
            "DOMAIN,d1example.cloudfront.net",
            "DOMAIN-SUFFIX,d1example.cloudfront.net",
            "DOMAIN,servd-anthropic-website.b-cdn.net",
            "DOMAIN-SUFFIX,abematv.akamaized.net",
            "DOMAIN-SUFFIX,openai.com",
            "AND,((DOMAIN-KEYWORD, openaicom-api-), (DOMAIN-SUFFIX, azurefd.net))",
        ):
            self.assertFalse(rc.blanket_shared_cdn_rule(rule), rule)
            self.assertTrue(rc.keep_generic_proxy_rule(rule, set()), rule)

    def test_domain_apex_is_not_a_suffix_catch_all(self):
        self.assertTrue(rc.keep_generic_proxy_rule("DOMAIN,cloudfront.net", set()))

    def test_explicit_manual_proxy_override_wins(self):
        rule = "DOMAIN-SUFFIX,cloudfront.net"
        self.assertTrue(rc.keep_generic_proxy_rule(rule, {rule}))


if __name__ == "__main__":
    unittest.main()
