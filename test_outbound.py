import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add directories to sys.path so we can import the modules
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_dir, 'Lead_Enrichment_Pipeline'))
sys.path.append(os.path.join(base_dir, 'Email_Warmup_Engine'))
sys.path.append(os.path.join(base_dir, 'Apify_Lead_Scraper'))

# Import functions to test
try:
    from parser import extract_email, extract_name, extract_summary
    from warmup_engine import EmailWarmupEngine
    from apify_service import build_actor_input
except Exception as e:
    print(f"Failed to import modules: {e}")
    sys.exit(1)

class TestOutboundPipeline(unittest.TestCase):
    
    # --- Lead Enrichment Pipeline Tests ---
    def test_extract_email(self):
        text = "Hello, you can contact us at info@vectraautomation.com or call us."
        email = extract_email(text)
        self.assertEqual(email, "info@vectraautomation.com")
        
        # Test invalid email (image)
        text_img = "Here is a picture info@company.png"
        self.assertIsNone(extract_email(text_img))

    def test_extract_name(self):
        text = "Our CEO John Doe founded the company in 2020."
        name = extract_name(text)
        # Should find John Doe
        self.assertEqual(name, "John Doe")
        
        text2 = "We have no specific roles mentioned here."
        self.assertIsNone(extract_name(text2))

    def test_extract_summary(self):
        text = "We are a trusted provider of HVAC services in Texas. We specialize in residential and commercial cooling. Call us today!"
        summary = extract_summary(text)
        self.assertIsNotNone(summary)
        self.assertIn("We are a trusted provider", summary)
        
    # --- Email Warmup Engine Tests ---
    @patch('warmup_engine.resend')
    @patch.dict('os.environ', {'RESEND_API_KEY': 'fake_key'})
    def test_warmup_engine_volume(self, mock_resend):
        # We don't want to actually send emails.
        # We just want to test if _get_daily_volume works.
        engine = EmailWarmupEngine()
        
        # Test explicit schedule
        self.assertEqual(engine._get_daily_volume(1), 5)
        self.assertEqual(engine._get_daily_volume(7), 50)
        # Test fallback
        self.assertEqual(engine._get_daily_volume(10), 100)

    # --- Apify Scraper Tests ---
    def test_apify_build_input(self):
        queries = ["HVAC contractors in Austin TX"]
        actor_input = build_actor_input(queries)
        self.assertIn("searchStringsArray", actor_input)
        self.assertEqual(actor_input["searchStringsArray"], queries)
        self.assertEqual(actor_input["maxCrawledPlacesPerSearch"], 50)

if __name__ == '__main__':
    unittest.main()
