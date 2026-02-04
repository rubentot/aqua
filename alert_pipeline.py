"""
Simple Alert Pipeline for Norwegian Aquaculture Monitor
MVP: Fetch URL -> Summarize with Claude -> Send Email Alert
"""
import os
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Import from existing modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.ai_summarizer import AISummarizer
from src.delivery import EmailDelivery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_url_content(url: str) -> str:
    """Fetch URL and extract text content using BeautifulSoup"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        logger.info(f"Fetched {len(clean_text)} characters from {url}")
        return clean_text

    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise


def summarize_content(content: str, source_name: str, source_url: str) -> dict:
    """Summarize content using Claude API"""
    try:
        summarizer = AISummarizer(provider="anthropic")

        # Use the existing summarize_change method with minimal diff context
        summary = summarizer.summarize_change(
            source_name=source_name,
            source_url=source_url,
            category="legislation",
            old_content="",  # No previous content for simple fetch
            new_content=content[:8000],  # Limit content size
            diff_summary=f"New content fetched from {source_name}",
            keywords_found=[]
        )

        # Convert RegulatorySummary to dict for email delivery
        return {
            "title": summary.title,
            "title_en": summary.title_en,
            "summary_no": summary.summary_no,
            "summary_en": summary.summary_en,
            "what_changed": summary.what_changed,
            "what_changed_en": summary.what_changed_en,
            "who_affected": summary.who_affected,
            "affected_areas": summary.affected_areas,
            "potential_impact": summary.potential_impact,
            "opportunities": summary.opportunities,
            "risks": summary.risks,
            "action_items": summary.action_items,
            "deadlines": summary.deadlines,
            "penalties": summary.penalties,
            "forms_required": summary.forms_required,
            "category": summary.category,
            "priority": summary.priority,
            "source_url": source_url,
            "detected_at": summary.detected_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise


def send_alert_email(summary: dict, to_email: str, client_name: str = "AquaRegWatch User"):
    """Send alert email using existing delivery module"""
    try:
        # Try SendGrid first, fall back to Gmail
        provider = "sendgrid" if os.getenv("SENDGRID_API_KEY") else "gmail"
        email_delivery = EmailDelivery(provider=provider)

        result = email_delivery.send_alert(
            to_email=to_email,
            summary=summary,
            client_name=client_name
        )

        if result.success:
            logger.info(f"Alert email sent to {to_email}")
        else:
            logger.error(f"Failed to send email: {result.error}")

        return result

    except Exception as e:
        logger.error(f"Email delivery failed: {e}")
        raise


def process_alert(url: str, source_name: str, to_email: str = None, client_name: str = "AquaRegWatch User"):
    """
    Full alert pipeline: Fetch -> Summarize -> Email

    Args:
        url: URL to fetch content from
        source_name: Human-readable name for the source
        to_email: Email address to send alert to (optional, skips email if not provided)
        client_name: Name to use in email greeting

    Returns:
        dict with summary and delivery result
    """
    logger.info(f"Processing alert for: {source_name} ({url})")

    # Step 1: Fetch URL content
    content = fetch_url_content(url)
    logger.info(f"Step 1 complete: Fetched {len(content)} chars")

    # Step 2: Summarize with Claude
    summary = summarize_content(content, source_name, url)
    logger.info(f"Step 2 complete: Generated summary - {summary['title']}")

    # Step 3: Send email alert (if email provided)
    delivery_result = None
    if to_email:
        delivery_result = send_alert_email(summary, to_email, client_name)
        logger.info(f"Step 3 complete: Email {'sent' if delivery_result.success else 'failed'}")
    else:
        logger.info("Step 3 skipped: No email address provided")

    return {
        "summary": summary,
        "delivery_result": delivery_result,
        "content_length": len(content),
        "processed_at": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    # Load environment variables from .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Test URL - Norwegian Directorate of Fisheries aquaculture page
    test_url = "https://www.fiskeridir.no/Akvakultur"
    test_source = "Fiskeridirektoratet - Akvakultur"

    print("=" * 60)
    print("AquaRegWatch Alert Pipeline - MVP Test")
    print("=" * 60)
    print(f"\nSource: {test_source}")
    print(f"URL: {test_url}")
    print()

    try:
        # Run pipeline without email (just fetch and summarize)
        result = process_alert(
            url=test_url,
            source_name=test_source,
            to_email=None  # Set to your email to test delivery
        )

        print("\n" + "=" * 60)
        print("SUMMARY RESULT")
        print("=" * 60)
        print(f"\nTitle: {result['summary']['title']}")
        print(f"Title (EN): {result['summary']['title_en']}")
        print(f"\nSummary (NO):\n{result['summary']['summary_no']}")
        print(f"\nSummary (EN):\n{result['summary']['summary_en']}")
        print(f"\nCategory: {result['summary']['category']}")
        print(f"Priority: {result['summary']['priority']}")
        print(f"\nWho Affected: {result['summary']['who_affected']}")
        print(f"\nAction Items:")
        for item in result['summary'].get('action_items', []):
            print(f"  - {item.get('action')} (Priority: {item.get('priority')})")

        print(f"\nContent fetched: {result['content_length']} characters")
        print(f"Processed at: {result['processed_at']}")

        print("\n" + "=" * 60)
        print("SUCCESS: Pipeline completed")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
