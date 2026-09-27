"""
Automated Verification Suite for Phishing Sentinel Enterprise Platform
======================================================================
Tests:
1. Universal Multi-Modal Document Parsers (.eml, .pdf, .docx, .xlsx, HTML, images)
2. Cyber Threat Heuristics & Anti-Evasion (zero-width characters, domain mismatch, sender spoofing)
3. Explainable SVM Token Heatmaps & Attribution
4. Dataset Telemetry & Ingestion
5. FastAPI Endpoints via TestClient
"""

import io
import unittest
from fastapi.testclient import TestClient

from server import app
from document_parsers import UniversalDocumentParser, extract_masked_links_from_text_and_html
from security_heuristics import (
    sanitize_evasions,
    analyze_headers,
    inspect_hyperlinks,
    inspect_attachments,
    inspect_url
)
import phishing_svm_classifier as classifier
import dataset_manager


class TestPhishingSentinelPlatform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # ------------------------------------------------------------------------
    # 1. Anti-Evasion & Zero-Width Sanitizer Tests
    # ------------------------------------------------------------------------
    def test_zero_width_evasion_sanitizer(self):
        evasive_text = "P\u200Ba\u200Bs\u200Bs\u200Bw\u200Bo\u200Br\u200Bd reset"
        cleaned, signals = sanitize_evasions(evasive_text)
        self.assertEqual(cleaned, "Password reset")
        self.assertTrue(any(s["category"] == "evasion" for s in signals))

    def test_hidden_html_evasion_sanitizer(self):
        html_text = 'Verify <span style="display:none">garbage noise</span> account'
        cleaned, signals = sanitize_evasions(html_text)
        self.assertNotIn("garbage noise", cleaned)
        self.assertIn("Verify", cleaned)
        self.assertTrue(any(s["category"] == "evasion" for s in signals))

    # ------------------------------------------------------------------------
    # 2. Masked Hyperlinks, Buttons & Domain Spoofing Tests
    # ------------------------------------------------------------------------
    def test_masked_link_unmasking(self):
        sample = '<a href="http://evil-tracker.xyz/auth">Click Here to verify your account</a>'
        links = extract_masked_links_from_text_and_html(sample)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["anchor_text"], "Click Here to verify your account")
        self.assertEqual(links[0]["target_url"], "http://evil-tracker.xyz/auth")

        inspected, signals = inspect_hyperlinks(links)
        self.assertEqual(len(inspected), 1)
        self.assertTrue(any("Generic Urgency" in f for f in inspected[0]["flags"]))
        self.assertTrue(any("High-Risk" in f for f in inspected[0]["flags"]))

    def test_domain_spoofing_mismatch(self):
        # Anchor text says paypal.com, but target is fake domain
        sample = '<a href="http://paypa1-update.top/security">https://www.paypal.com/security</a>'
        links = extract_masked_links_from_text_and_html(sample)
        inspected, signals = inspect_hyperlinks(links)
        self.assertTrue(inspected[0]["is_mismatch"])
        self.assertEqual(inspected[0]["risk_severity"], "danger")
        self.assertTrue(any(s["category"] == "link_spoofing" for s in signals))

    def test_punycode_and_ip_host_detection(self):
        puny_res = inspect_url("http://xn--pypal-4ve.com/login")
        self.assertTrue(puny_res["is_suspicious"])
        self.assertTrue(any("Punycode" in f for f in puny_res["flags"]))

        ip_res = inspect_url("http://192.168.1.100/auth")
        self.assertTrue(ip_res["is_suspicious"])
        self.assertTrue(any("IP Hostname" in f for f in ip_res["flags"]))

    # ------------------------------------------------------------------------
    # 3. Sender Identity & Header Spoofing Tests
    # ------------------------------------------------------------------------
    def test_display_name_brand_spoofing(self):
        headers = {
            "From": '"Microsoft Support Desk" <attacker8392@gmail.com>',
            "Reply-To": "hacker@evil-domain.ru",
            "Authentication-Results": "spf=fail dkim=fail dmarc=fail"
        }
        signals = analyze_headers(headers)
        self.assertTrue(any(s["category"] == "sender_spoofing" for s in signals))
        self.assertTrue(any(s["category"] == "reply_to_mismatch" for s in signals))
        self.assertTrue(any(s["category"] == "auth_failure" for s in signals))

    # ------------------------------------------------------------------------
    # 4. Attachment Screening Tests
    # ------------------------------------------------------------------------
    def test_double_extension_and_macro_attachments(self):
        attachments = [
            {"filename": "Invoice_2026.pdf.exe", "size_bytes": 102400, "content_type": "application/x-msdownload"},
            {"filename": "Payroll_Q3.docm", "size_bytes": 45000, "content_type": "application/vnd.ms-word.document.macroEnabled.12"},
            {"filename": "Quarterly_Notes.txt", "size_bytes": 1200, "content_type": "text/plain"}
        ]
        scanned, signals = inspect_attachments(attachments)
        self.assertEqual(len(scanned), 3)
        self.assertEqual(scanned[0]["risk_severity"], "danger")
        self.assertEqual(scanned[1]["risk_severity"], "danger")
        self.assertEqual(scanned[2]["risk_severity"], "safe")

    # ------------------------------------------------------------------------
    # 5. Multi-Modal Document Parsing Tests
    # ------------------------------------------------------------------------
    def test_eml_parsing(self):
        raw_eml = (
            b"From: \"Bank Alert\" <service@bank-notify.com>\r\n"
            b"To: victim@company.com\r\n"
            b"Subject: Immediate Action Required: Account Locked\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n\r\n"
            b"<html><body>Please <a href=\"http://bank-unlock.xyz\">Click Here</a> to restore.</body></html>"
        )
        parsed = UniversalDocumentParser.parse_file(raw_eml, "alert.eml")
        self.assertEqual(parsed["extension"], ".eml")
        self.assertIn("Immediate Action Required", parsed["subject"])
        self.assertEqual(len(parsed["links"]), 1)
        self.assertEqual(parsed["links"][0]["target_url"], "http://bank-unlock.xyz")

    def test_plaintext_and_html_parsing(self):
        html_bytes = b"<html><head><title>Phish Test</title></head><body>Login at <a href='http://fake.top'>Portal</a></body></html>"
        parsed = UniversalDocumentParser.parse_file(html_bytes, "page.html")
        self.assertEqual(parsed["extension"], ".html")
        self.assertEqual(len(parsed["links"]), 1)

    # ------------------------------------------------------------------------
    # 6. Native SVM Explainability & Attribution
    # ------------------------------------------------------------------------
    def test_svm_explain_prediction(self):
        import joblib
        model = joblib.load("phishing_detector_model.joblib")
        sample = "Urgent: Click here to verify your PayPal account now at http://fake-login.xyz"
        res = classifier.explain_prediction(model, sample, top_k=5)
        self.assertIn(res["verdict"], ["PHISHING", "LEGITIMATE"])
        self.assertIsInstance(res["phishing_prob"], float)
        self.assertTrue(len(res["top_features"]) > 0)
        self.assertTrue(len(res["heatmap_tokens"]) > 0)

    # ------------------------------------------------------------------------
    # 7. Dataset Management Tests
    # ------------------------------------------------------------------------
    def test_dataset_telemetry(self):
        stats = dataset_manager.get_dataset_statistics()
        self.assertGreater(stats["total_samples"], 50000)
        self.assertIn("accuracy", stats["metrics"])

    # ------------------------------------------------------------------------
    # 8. REST API Endpoints Verification
    # ------------------------------------------------------------------------
    def test_api_health_and_examples(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["model_loaded"])

        res2 = self.client.get("/api/examples")
        self.assertEqual(res2.status_code, 200)
        self.assertGreater(len(res2.json()["examples"]), 0)

    def test_api_predict_text(self):
        payload = {
            "email_text": "Subject: Urgent: Verify your Bank Account immediately at <a href='http://bank-phish.xyz'>Click Here</a>",
            "sensitivity": 0.50
        }
        res = self.client.post("/api/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_phishing"])
        self.assertEqual(data["risk_level"], "CRITICAL")
        self.assertGreater(len(data["inspected_links"]), 0)
        self.assertGreater(len(data["heatmap_tokens"]), 0)

    def test_api_scan_file(self):
        eml_content = (
            b"From: \"PayPal Security\" <alert@fake-paypa1.top>\r\n"
            b"To: victim@domain.com\r\n"
            b"Subject: Your account is restricted\r\n\r\n"
            b"Please visit <a href=\"http://paypa1-fake.top/auth\">https://www.paypal.com</a> to unlock."
        )
        files = {
            "file": ("security_alert.eml", io.BytesIO(eml_content), "message/rfc822")
        }
        data = {"sensitivity": "0.50"}
        res = self.client.post("/api/scan-file", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        resp_data = res.json()
        self.assertTrue(resp_data["is_phishing"])
        self.assertEqual(resp_data["file_metadata"]["extension"], ".eml")
        self.assertTrue(any(l["is_mismatch"] for l in resp_data["inspected_links"]))


if __name__ == "__main__":
    unittest.main()
