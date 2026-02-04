#!/usr/bin/env python3
"""
AquaRegWatch - Production Monitor
=================================
Simple, working regulatory monitor that:
1. Fetches Norwegian government pages
2. Detects changes from previous run
3. Summarizes with AI
4. Sends email alerts

Run: python monitor.py
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SNAPSHOTS_FILE = DATA_DIR / "snapshots.json"
CHANGES_LOG = DATA_DIR / "changes.json"

# Sources to monitor
SOURCES = [
    {
        "id": "fiskeridir-akvakultur",
        "name": "Fiskeridirektoratet - Akvakultur",
        "url": "https://www.fiskeridir.no/Akvakultur",
        "category": "licenses"
    },
    {
        "id": "fiskeridir-tildelinger",
        "name": "Fiskeridirektoratet - Tildelinger",
        "url": "https://www.fiskeridir.no/Akvakultur/Tildeling-og-tillatelser",
        "category": "licenses"
    },
    {
        "id": "mattilsynet-fisk",
        "name": "Mattilsynet - Fisk og akvakultur",
        "url": "https://www.mattilsynet.no/fisk_og_akvakultur/",
        "category": "health"
    },
    {
        "id": "mattilsynet-lakselus",
        "name": "Mattilsynet - Lakselus",
        "url": "https://www.mattilsynet.no/fisk_og_akvakultur/akvakultur/lakselus/",
        "category": "sea_lice"
    },
    {
        "id": "lovdata-akvakultur",
        "name": "Lovdata - Akvakulturloven",
        "url": "https://lovdata.no/dokument/NL/lov/2005-06-17-79",
        "category": "legislation"
    },
    {
        "id": "regjeringen-fiskeri",
        "name": "Regjeringen - Fiskeri og havbruk",
        "url": "https://www.regjeringen.no/no/tema/mat-fiske-og-landbruk/fiskeri-og-havbruk/",
        "category": "policy"
    },
    {
        "id": "sjomatnorge",
        "name": "Sjømat Norge",
        "url": "https://sjomatnorge.no/",
        "category": "industry"
    },
]

# Request settings
HEADERS = {
    "User-Agent": "AquaRegWatch/1.0 (Regulatory Monitor for Norwegian Aquaculture)"
}
TIMEOUT = 30


def fetch_page(url: str) -> tuple[str, str]:
    """Fetch page and extract text content. Returns (content, hash)."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Get text
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(lines)

        # Hash for quick comparison
        content_hash = hashlib.md5(content.encode()).hexdigest()

        return content, content_hash

    except Exception as e:
        log.error(f"Failed to fetch {url}: {e}")
        return None, None


def load_snapshots() -> dict:
    """Load previous snapshots."""
    if SNAPSHOTS_FILE.exists():
        with open(SNAPSHOTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_snapshots(snapshots: dict):
    """Save snapshots."""
    with open(SNAPSHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, indent=2, ensure_ascii=False)


def load_changes() -> list:
    """Load changes log."""
    if CHANGES_LOG.exists():
        with open(CHANGES_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_change(change: dict):
    """Append change to log."""
    changes = load_changes()
    changes.append(change)
    # Keep last 100 changes
    changes = changes[-100:]
    with open(CHANGES_LOG, "w", encoding="utf-8") as f:
        json.dump(changes, f, indent=2, ensure_ascii=False)


def summarize_change(source: dict, old_content: str, new_content: str) -> dict:
    """Use Claude to summarize the change."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("No ANTHROPIC_API_KEY - skipping AI summary")
        return {
            "title": f"Endring oppdaget: {source['name']}",
            "summary_no": "AI-oppsummering ikke tilgjengelig (mangler API-nøkkel)",
            "summary_en": "AI summary not available (missing API key)",
            "action_items": []
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Truncate content to avoid token limits
        old_excerpt = old_content[:3000] if old_content else "(ingen tidligere innhold)"
        new_excerpt = new_content[:3000] if new_content else "(tomt)"

        prompt = f"""Du er en ekspert på norske akvakulturreguleringer. Analyser denne endringen:

KILDE: {source['name']}
URL: {source['url']}
KATEGORI: {source['category']}

TIDLIGERE INNHOLD:
{old_excerpt}

NYTT INNHOLD:
{new_excerpt}

Gi en kort oppsummering på JSON-format:
{{
    "title": "Kort tittel på endringen (norsk)",
    "title_en": "Short title in English",
    "summary_no": "2-3 setninger om hva som har endret seg og hvorfor det er viktig",
    "summary_en": "2-3 sentences about what changed and why it matters",
    "who_affected": ["Liste over hvem som påvirkes"],
    "action_items": [
        {{"action": "Hva må gjøres", "deadline": "Når", "priority": "Høy/Medium/Lav"}}
    ],
    "priority": "KRITISK/HØY/MEDIUM/LAV"
}}

Svar KUN med JSON, ingen annen tekst."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from response
        text = response.content[0].text.strip()
        # Handle markdown code blocks
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        return json.loads(text)

    except Exception as e:
        log.error(f"AI summarization failed: {e}")
        return {
            "title": f"Endring oppdaget: {source['name']}",
            "summary_no": f"Automatisk oppsummering feilet: {str(e)[:100]}",
            "summary_en": f"Automatic summary failed: {str(e)[:100]}",
            "action_items": [],
            "priority": "MEDIUM"
        }


def send_alert(source: dict, summary: dict):
    """Send email alert about the change."""
    to_email = os.getenv("ALERT_EMAIL")

    if not to_email:
        log.warning("No ALERT_EMAIL set - printing alert instead")
        print_alert(source, summary)
        return

    # Build HTML content
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #0066FF; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">AquaRegWatch Alert</h1>
        </div>
        <div style="padding: 24px; border: 1px solid #ddd; border-top: none;">
            <span style="background: {'#ef4444' if summary.get('priority') == 'KRITISK' else '#f59e0b' if summary.get('priority') == 'HØY' else '#eab308'};
                   color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                {summary.get('priority', 'MEDIUM')}
            </span>
            <h2 style="margin: 16px 0 8px;">{summary.get('title', 'Change Detected')}</h2>
            <p style="color: #666; margin: 0;">{source['name']} | {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>

            <div style="background: #f5f5f5; padding: 16px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin: 0 0 8px;">Norsk</h4>
                <p style="margin: 0;">{summary.get('summary_no', 'N/A')}</p>
            </div>

            <div style="background: #f5f5f5; padding: 16px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin: 0 0 8px;">English</h4>
                <p style="margin: 0;">{summary.get('summary_en', 'N/A')}</p>
            </div>

            <p><a href="{source['url']}" style="color: #0066FF;">View source</a></p>
        </div>
    </div>
    """

    subject = f"[{summary.get('priority', 'ALERT')}] {summary.get('title', 'Regulatory Change')}"

    # Try SendGrid first
    if os.getenv("SENDGRID_API_KEY"):
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content

            message = Mail(
                from_email=Email(os.getenv("EMAIL_FROM_ADDRESS", "alerts@tefiaqua.no")),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
            response = sg.send(message)
            log.info(f"Alert sent via SendGrid to {to_email} (status: {response.status_code})")
            return
        except Exception as e:
            log.error(f"SendGrid failed: {e}")

    # Try Gmail
    if os.getenv("GMAIL_ADDRESS") and os.getenv("GMAIL_APP_PASSWORD"):
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            gmail_user = os.getenv("GMAIL_ADDRESS")
            gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = gmail_user
            msg['To'] = to_email
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, gmail_pass)
                server.sendmail(gmail_user, to_email, msg.as_string())

            log.info(f"Alert sent via Gmail to {to_email}")
            return
        except Exception as e:
            log.error(f"Gmail failed: {e}")

    # Fallback: print
    log.warning("No email provider configured - printing alert")
    print_alert(source, summary)


def print_alert(source: dict, summary: dict):
    """Print alert to console."""
    print("\n" + "="*60)
    print(f"ALERT: {summary.get('title', 'Change detected')}")
    print("="*60)
    print(f"Source: {source['name']}")
    print(f"URL: {source['url']}")
    print(f"Priority: {summary.get('priority', 'MEDIUM')}")
    print(f"\nSummary (NO): {summary.get('summary_no', 'N/A')}")
    print(f"\nSummary (EN): {summary.get('summary_en', 'N/A')}")
    if summary.get('action_items'):
        print("\nAction Items:")
        for item in summary['action_items']:
            print(f"  - {item.get('action')} (Deadline: {item.get('deadline')})")
    print("="*60 + "\n")


def run_monitor():
    """Main monitoring loop."""
    log.info("="*60)
    log.info("AquaRegWatch - Starting regulatory monitor")
    log.info("="*60)

    snapshots = load_snapshots()
    changes_found = []

    for source in SOURCES:
        log.info(f"Checking: {source['name']}")

        content, content_hash = fetch_page(source['url'])

        if content is None:
            log.warning(f"  Skipped (fetch failed)")
            continue

        source_id = source['id']
        previous = snapshots.get(source_id, {})
        previous_hash = previous.get('hash')

        if previous_hash is None:
            # First time seeing this source
            log.info(f"  First snapshot saved")
            snapshots[source_id] = {
                'hash': content_hash,
                'content': content[:5000],  # Store excerpt
                'last_checked': datetime.now().isoformat(),
                'url': source['url']
            }
        elif content_hash != previous_hash:
            # Change detected!
            log.info(f"  CHANGE DETECTED!")

            # Summarize with AI
            summary = summarize_change(source, previous.get('content', ''), content)

            # Record change
            change = {
                'source_id': source_id,
                'source_name': source['name'],
                'url': source['url'],
                'detected_at': datetime.now().isoformat(),
                'summary': summary
            }
            save_change(change)
            changes_found.append(change)

            # Send alert
            send_alert(source, summary)

            # Update snapshot
            snapshots[source_id] = {
                'hash': content_hash,
                'content': content[:5000],
                'last_checked': datetime.now().isoformat(),
                'url': source['url']
            }
        else:
            log.info(f"  No changes")
            snapshots[source_id]['last_checked'] = datetime.now().isoformat()

    # Save snapshots
    save_snapshots(snapshots)

    # Summary
    log.info("="*60)
    log.info(f"Monitor complete: {len(changes_found)} changes detected")
    if changes_found:
        for c in changes_found:
            log.info(f"  - {c['source_name']}: {c['summary'].get('title', 'Change')}")
    log.info("="*60)

    return changes_found


if __name__ == "__main__":
    run_monitor()
