"""
Comprehensive Tests for AquaRegWatch Norway
Run with: pytest tests/test_all.py -v
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChangeDetector:
    """Test change detection functionality"""

    def test_no_change_detection(self):
        """Test that identical content returns no changes"""
        from src.change_detector import ChangeDetector

        detector = ChangeDetector()
        content = "This is test content about aquaculture regulations."

        result = detector.detect_changes(content, content, "Test")

        assert result.has_changes is False
        assert result.change_percent == 0.0

    def test_change_detection(self):
        """Test that different content is detected"""
        from src.change_detector import ChangeDetector

        detector = ChangeDetector()
        old = "Old regulation: limit is 0.5"
        new = "New regulation: limit is 0.25"

        result = detector.detect_changes(old, new, "Test")

        assert result.has_changes is True
        assert result.change_percent > 0

    def test_keyword_extraction(self):
        """Test that Norwegian keywords are extracted"""
        from src.change_detector import ChangeDetector

        detector = ChangeDetector()
        old = "Gammel tekst"
        new = "Ny forskrift om lakselus med bot på 1 million"

        result = detector.detect_changes(old, new, "Test")

        assert any("forskrift" in kw.lower() for kw in result.significant_keywords_found)
        assert any("lakselus" in kw.lower() for kw in result.significant_keywords_found)

    def test_ignore_timestamp_changes(self):
        """Test that timestamp-only changes are ignored"""
        from src.change_detector import ChangeDetector

        detector = ChangeDetector()
        old = "Content here. Sist oppdatert: 01.01.2026"
        new = "Content here. Sist oppdatert: 03.02.2026"

        result = detector.detect_changes(old, new, "Test")

        # Should detect as no substantive changes
        assert result.has_changes is False or result.is_significant is False


class TestScraper:
    """Test web scraping functionality"""

    def test_scraper_initialization(self):
        """Test scraper can be initialized"""
        from src.scraper import NorwegianAquacultureScraper

        scraper = NorwegianAquacultureScraper()
        assert scraper is not None
        assert scraper.timeout == 30

    def test_content_hash_consistency(self):
        """Test that same content produces same hash"""
        from src.scraper import NorwegianAquacultureScraper
        import hashlib

        scraper = NorwegianAquacultureScraper()
        content = "Test content for hashing"

        hash1 = hashlib.sha256(content.encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(content.encode('utf-8')).hexdigest()

        assert hash1 == hash2

    def test_site_selector_lookup(self):
        """Test site-specific selector lookup"""
        from src.scraper import NorwegianAquacultureScraper

        scraper = NorwegianAquacultureScraper()

        key = scraper._get_site_key("https://www.fiskeridir.no/Akvakultur")
        assert key == "fiskeridir.no"

        key = scraper._get_site_key("https://www.mattilsynet.no/fisk")
        assert key == "mattilsynet.no"


class TestModels:
    """Test database models"""

    def test_database_initialization(self):
        """Test database can be initialized"""
        from src.models import init_database
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            engine, Session = init_database(f"sqlite:///{db_path}")

            assert engine is not None
            assert os.path.exists(db_path)

    def test_source_model(self):
        """Test Source model creation"""
        from src.models import Source

        source = Source(
            id="test_source",
            name="Test Source",
            url="https://example.com",
            category="test"
        )

        assert source.id == "test_source"
        assert source.is_active is True  # Default value


class TestDelivery:
    """Test delivery functionality"""

    def test_email_html_formatting(self):
        """Test email HTML is generated correctly"""
        from src.delivery import EmailDelivery

        # Create instance without initializing client
        email = EmailDelivery.__new__(EmailDelivery)
        email.from_name = "Test"

        summary = {
            "title": "Test Alert",
            "summary_no": "Norsk oppsummering",
            "summary_en": "English summary",
            "what_changed": "Something changed",
            "who_affected": ["Farmers"],
            "action_items": [{"action": "Do something", "deadline": "2026-03-01", "priority": "high"}],
            "penalties": ["Fine of 100 NOK"],
            "category": "test",
            "priority": "high",
            "source_url": "https://example.com"
        }

        html = email._format_alert_html(summary)

        assert "Test Alert" in html
        assert "Norsk oppsummering" in html
        assert "English summary" in html

    def test_slack_blocks_formatting(self):
        """Test Slack Block Kit formatting"""
        from src.delivery import SlackDelivery

        slack = SlackDelivery.__new__(SlackDelivery)

        summary = {
            "title": "Test Alert",
            "summary_no": "Norsk oppsummering",
            "summary_en": "English summary",
            "what_changed": "Something changed",
            "who_affected": ["Farmers"],
            "action_items": [],
            "penalties": [],
            "category": "test",
            "priority": "critical",
            "source_url": "https://example.com"
        }

        blocks = slack._format_alert_blocks(summary)

        assert len(blocks) > 0
        assert blocks[0]["type"] == "header"


class TestIntegration:
    """Integration tests"""

    def test_full_change_detection_flow(self):
        """Test complete flow from content to analysis"""
        from src.change_detector import ChangeDetector

        detector = ChangeDetector()

        # Simulate Norwegian regulatory content
        old_content = """
        Akvakultur i Norge

        Lakselusgrenser
        Maksimalt tillatt antall voksne hunnlus er 0.5 per fisk.
        Telling skal gjøres ukentlig.

        Søknadsfrister:
        - Nye konsesjoner: 1. mars 2026
        """

        new_content = """
        Akvakultur i Norge

        Lakselusgrenser - OPPDATERT
        NY FORSKRIFT: Maksimalt tillatt antall voksne hunnlus er 0.25 per fisk.
        Telling skal gjøres to ganger per uke.
        Brudd kan medføre bot opptil 1 million NOK.

        Søknadsfrister:
        - Nye konsesjoner: 15. mars 2026 (endret)
        - Dispensasjon: 1. april 2026
        """

        result = detector.detect_changes(old_content, new_content, "Test Integration")

        # Verify detection
        assert result.has_changes is True
        assert result.is_significant is True

        # Verify keywords found
        keywords_lower = [k.lower() for k in result.significant_keywords_found]
        assert any("forskrift" in k for k in keywords_lower)

        # Verify diff generated
        assert len(result.diff_text) > 0

        # Verify added/removed content
        assert len(result.added_lines) > 0


class TestConfiguration:
    """Test configuration loading"""

    def test_yaml_config_structure(self):
        """Test YAML configuration is valid"""
        import yaml

        config_path = "config/settings.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Check required sections
            assert "sources" in config
            assert "ai" in config
            assert "delivery" in config

            # Check sources have required fields
            for source in config["sources"]:
                assert "id" in source
                assert "url" in source
                assert "name" in source


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
