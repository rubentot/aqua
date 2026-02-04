#!/usr/bin/env python3
"""
AquaRegWatch - Production Monitor (Bulletproof Edition)
=======================================================
Reliable regulatory monitor with:
- Retry logic with exponential backoff
- Rate limiting to avoid blocks
- Smart content normalization (ignores timestamps/ads)
- Failure tracking and alerting
- Multiple email fallbacks
- Graceful error handling throughout

Run: python monitor.py
"""

import os
import re
import json
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

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
FAILURES_FILE = DATA_DIR / "failures.json"
CUSTOMERS_FILE = Path("customers.json")

# Sources to monitor (verified working URLs)
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
    "User-Agent": "AquaRegWatch/2.0 (Regulatory Monitor for Norwegian Aquaculture; contact@tefiaqua.no)"
}
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds, will be multiplied by attempt number
RATE_LIMIT_DELAY = 1  # seconds between requests


def normalize_content(text: str) -> str:
    """
    Normalize content to reduce false positives from:
    - Timestamps and dates
    - Dynamic counters
    - Session IDs
    - Random ads/widgets
    """
    # Remove common Norwegian date formats
    text = re.sub(r'\d{1,2}\.\d{1,2}\.\d{4}', '[DATE]', text)
    text = re.sub(r'\d{1,2}\. (januar|februar|mars|april|mai|juni|juli|august|september|oktober|november|desember) \d{4}', '[DATE]', text, flags=re.IGNORECASE)

    # Remove times
    text = re.sub(r'\d{1,2}:\d{2}(:\d{2})?', '[TIME]', text)

    # Remove "updated X minutes ago" type strings
    text = re.sub(r'(oppdatert|publisert|endret).*?(siden|ago)', '[UPDATED]', text, flags=re.IGNORECASE)

    # Remove numbers that look like counters (e.g., "123 results")
    text = re.sub(r'\d+ (resultater|treff|saker|dokumenter)', '[COUNT]', text, flags=re.IGNORECASE)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def fetch_page_with_retry(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch page with retry logic and exponential backoff."""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
                tag.decompose()

            # Get text
            text = soup.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = "\n".join(lines)

            # Normalize to reduce false positives
            normalized = normalize_content(content)

            # Hash the normalized content
            content_hash = hashlib.sha256(normalized.encode()).hexdigest()[:16]

            return content, content_hash

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                log.error(f"Page not found (404): {url}")
                return None, None  # Don't retry 404s
            last_error = e
        except requests.exceptions.Timeout:
            last_error = TimeoutError(f"Timeout after {TIMEOUT}s")
        except requests.exceptions.ConnectionError as e:
            last_error = e
        except Exception as e:
            last_error = e

        if attempt < MAX_RETRIES:
            delay = RETRY_DELAY * attempt
            log.warning(f"Attempt {attempt} failed for {url}, retrying in {delay}s...")
            time.sleep(delay)

    log.error(f"All {MAX_RETRIES} attempts failed for {url}: {last_error}")
    return None, None


def load_json_file(filepath: Path, default=None):
    """Safely load JSON file."""
    if default is None:
        default = {}
    try:
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"Failed to load {filepath}: {e}")
    return default


def save_json_file(filepath: Path, data):
    """Safely save JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log.error(f"Failed to save {filepath}: {e}")


def load_snapshots() -> dict:
    return load_json_file(SNAPSHOTS_FILE, {})


def save_snapshots(snapshots: dict):
    save_json_file(SNAPSHOTS_FILE, snapshots)


def load_failures() -> dict:
    return load_json_file(FAILURES_FILE, {})


def save_failures(failures: dict):
    save_json_file(FAILURES_FILE, failures)


def track_failure(source_id: str, error: str):
    """Track consecutive failures for a source."""
    failures = load_failures()
    if source_id not in failures:
        failures[source_id] = {"count": 0, "first_failure": None, "last_error": None}

    failures[source_id]["count"] += 1
    failures[source_id]["last_error"] = error
    if failures[source_id]["first_failure"] is None:
        failures[source_id]["first_failure"] = datetime.now().isoformat()

    save_failures(failures)

    # Alert if 3+ consecutive failures
    if failures[source_id]["count"] >= 3:
        log.warning(f"Source {source_id} has failed {failures[source_id]['count']} times consecutively!")
        return True
    return False


def clear_failure(source_id: str):
    """Clear failure tracking for a source that succeeded."""
    failures = load_failures()
    if source_id in failures:
        del failures[source_id]
        save_failures(failures)


def load_changes() -> list:
    return load_json_file(CHANGES_LOG, [])


def load_customers() -> list:
    """Load customer profiles for personalized alerts."""
    data = load_json_file(CUSTOMERS_FILE, {"customers": []})
    return [c for c in data.get("customers", []) if c.get("active", False)]


def save_change(change: dict):
    """Append change to log."""
    changes = load_changes()
    changes.append(change)
    changes = changes[-100:]  # Keep last 100
    save_json_file(CHANGES_LOG, changes)


def summarize_change_for_customer(source: dict, old_content: str, new_content: str, customer: dict) -> dict:
    """Use Claude to create a PERSONALIZED summary for a specific customer."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("No ANTHROPIC_API_KEY - skipping AI summary")
        return {
            "title": f"Endring oppdaget: {source['name']}",
            "summary_no": "AI-oppsummering ikke tilgjengelig (mangler API-nøkkel)",
            "summary_en": "AI summary not available (missing API key)",
            "action_items": [],
            "priority": "MEDIUM",
            "relevance": "UKJENT"
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        profile = customer.get("profile", {})
        company = customer.get("company", "Kunde")

        # Build customer context
        customer_context = f"""
KUNDEPROFIL - {company}:
- Lisenstyper: {', '.join(profile.get('licenses', ['Ukjent']))}
- Regioner: {', '.join(profile.get('regions', ['Ukjent']))}
- Produksjonstype: {profile.get('production_type', 'Ukjent')}
- MTB: {profile.get('mtb_tonnes', 'Ukjent')} tonn
- Fokusområder: {', '.join(profile.get('concerns', []))}
- Notater: {profile.get('notes', 'Ingen')}
"""

        old_excerpt = (old_content[:2500] if old_content else "(ingen tidligere innhold)")
        new_excerpt = (new_content[:2500] if new_content else "(tomt)")

        prompt = f"""Du er en ekspert på norske akvakulturreguleringer. Du gir PERSONALISERT rådgivning til oppdrettsbedrifter.

{customer_context}

REGULERINGSENDRING OPPDAGET:
Kilde: {source['name']}
URL: {source['url']}
Kategori: {source['category']}

TIDLIGERE INNHOLD:
{old_excerpt}

NYTT INNHOLD:
{new_excerpt}

Analyser denne endringen SPESIFIKT for {company}. Vurder:
1. Er dette relevant for DERES lisenser og regioner?
2. Hva betyr dette KONKRET for deres drift?
3. Hva må DE gjøre, og når?

Svar på JSON-format:
{{
    "title": "Kort tittel på endringen",
    "relevance": "HØY/MEDIUM/LAV/INGEN",
    "relevance_reason": "Kort forklaring på hvorfor dette er/ikke er relevant for {company}",
    "summary_no": "2-3 setninger om hva dette betyr SPESIFIKT for {company}",
    "summary_en": "2-3 sentences about what this means SPECIFICALLY for {company}",
    "impacts": ["Konkret påvirkning 1", "Konkret påvirkning 2"],
    "action_items": [
        {{"action": "Konkret handling {company} må gjøre", "deadline": "Dato/frist", "priority": "Høy/Medium/Lav"}}
    ],
    "priority": "KRITISK/HØY/MEDIUM/LAV"
}}

Svar KUN med JSON."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()

        if "```" in text:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                text = match.group(1)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
            raise

    except Exception as e:
        log.error(f"Personalized AI summary failed for {customer.get('company')}: {e}")
        return {
            "title": f"Endring oppdaget: {source['name']}",
            "summary_no": f"Automatisk oppsummering feilet: {str(e)[:100]}",
            "summary_en": f"Automatic summary failed: {str(e)[:100]}",
            "action_items": [],
            "priority": "MEDIUM",
            "relevance": "UKJENT"
        }


def summarize_change(source: dict, old_content: str, new_content: str) -> dict:
    """Use Claude to summarize the change with robust error handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("No ANTHROPIC_API_KEY - skipping AI summary")
        return {
            "title": f"Endring oppdaget: {source['name']}",
            "summary_no": "AI-oppsummering ikke tilgjengelig (mangler API-nøkkel)",
            "summary_en": "AI summary not available (missing API key)",
            "action_items": [],
            "priority": "MEDIUM"
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Truncate content to avoid token limits
        old_excerpt = (old_content[:3000] if old_content else "(ingen tidligere innhold)")
        new_excerpt = (new_content[:3000] if new_content else "(tomt)")

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

        # Parse JSON from response with robust handling
        text = response.content[0].text.strip()

        # Handle markdown code blocks
        if "```" in text:
            # Extract content between code blocks
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if match:
                text = match.group(1)

        # Try to parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
            raise

    except Exception as e:
        log.error(f"AI summarization failed: {e}")
        return {
            "title": f"Endring oppdaget: {source['name']}",
            "summary_no": f"Automatisk oppsummering feilet: {str(e)[:100]}",
            "summary_en": f"Automatic summary failed: {str(e)[:100]}",
            "action_items": [],
            "priority": "MEDIUM"
        }


def send_alert_to_customer(source: dict, summary: dict, customer: dict) -> bool:
    """Send personalized email alert to a specific customer."""
    to_email = customer.get("email")
    company = customer.get("company", "Customer")

    if not to_email:
        log.warning(f"No email for customer {company}")
        return False

    # Skip if not relevant to this customer
    relevance = summary.get("relevance", "MEDIUM")
    if relevance == "INGEN":
        log.info(f"  Skipping {company} - not relevant to them")
        return False

    priority_colors = {
        'KRITISK': '#dc2626',
        'HØY': '#ea580c',
        'MEDIUM': '#ca8a04',
        'LAV': '#16a34a'
    }
    priority = summary.get('priority', 'MEDIUM')
    color = priority_colors.get(priority, '#ca8a04')

    relevance_colors = {'HØY': '#16a34a', 'MEDIUM': '#ca8a04', 'LAV': '#9ca3af'}
    rel_color = relevance_colors.get(relevance, '#ca8a04')

    # Build personalized HTML
    impacts_html = ""
    if summary.get("impacts"):
        impacts_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
        for impact in summary.get("impacts", []):
            impacts_html += f"<li style='margin: 5px 0;'>{impact}</li>"
        impacts_html += "</ul>"

    actions_html = ""
    if summary.get("action_items"):
        actions_html = "<div style='background: #fef3c7; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;'>"
        actions_html += "<h4 style='margin: 0 0 10px; color: #92400e;'>⚡ Handlinger for " + company + "</h4>"
        for item in summary.get("action_items", []):
            actions_html += f"<p style='margin: 5px 0;'><strong>{item.get('action')}</strong><br>"
            actions_html += f"<span style='color: #666;'>Frist: {item.get('deadline', 'Ikke spesifisert')} | Prioritet: {item.get('priority', 'Medium')}</span></p>"
        actions_html += "</div>"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #0066FF; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🐟 AquaRegWatch Alert</h1>
            <p style="margin: 5px 0 0; opacity: 0.9; font-size: 14px;">Personalisert for {company}</p>
        </div>
        <div style="padding: 24px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
            <div style="margin-bottom: 16px;">
                <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 8px;">
                    {priority}
                </span>
                <span style="background: {rel_color}; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px;">
                    Relevans: {relevance}
                </span>
            </div>

            <h2 style="margin: 16px 0 8px;">{summary.get('title', 'Reguleringsendring')}</h2>
            <p style="color: #666; margin: 0;">{source['name']} | {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>

            <div style="background: #f0fdf4; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
                <h4 style="margin: 0 0 8px; color: #166534;">📋 Hvorfor dette er relevant for {company}</h4>
                <p style="margin: 0;">{summary.get('relevance_reason', 'Generell reguleringsendring')}</p>
            </div>

            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0066FF;">
                <h4 style="margin: 0 0 8px; color: #1e40af;">🇳🇴 Hva dette betyr for dere</h4>
                <p style="margin: 0; line-height: 1.6;">{summary.get('summary_no', 'N/A')}</p>
                {impacts_html}
            </div>

            {actions_html}

            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #6b7280;">
                <h4 style="margin: 0 0 8px; color: #374151;">🇬🇧 English Summary</h4>
                <p style="margin: 0; line-height: 1.6;">{summary.get('summary_en', 'N/A')}</p>
            </div>

            <p style="margin-top: 24px;">
                <a href="{source['url']}" style="background: #0066FF; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; display: inline-block;">
                    Se kilde →
                </a>
            </p>

            <hr style="margin: 24px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                AquaRegWatch by TefiAqua | Personalisert reguleringsovervåking for {company}
            </p>
        </div>
    </div>
    """

    subject = f"[{priority}] {summary.get('title', 'Reguleringsendring')} - {company}"

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

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
                server.login(gmail_user, gmail_pass)
                server.sendmail(gmail_user, to_email, msg.as_string())

            log.info(f"  ✉ Personalized alert sent to {company} ({to_email})")
            return True
        except Exception as e:
            log.error(f"Gmail failed for {company}: {e}")

    # Try SendGrid as fallback
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
            log.info(f"  ✉ Personalized alert sent to {company} via SendGrid")
            return True
        except Exception as e:
            log.error(f"SendGrid failed for {company}: {e}")

    log.error(f"Failed to send alert to {company}")
    return False


def send_alert(source: dict, summary: dict) -> bool:
    """Send email alert with multiple fallbacks. Returns True if sent successfully."""
    to_email = os.getenv("ALERT_EMAIL")

    if not to_email:
        log.warning("No ALERT_EMAIL set - printing alert instead")
        print_alert(source, summary)
        return False

    # Build HTML content
    priority_colors = {
        'KRITISK': '#dc2626',
        'HØY': '#ea580c',
        'MEDIUM': '#ca8a04',
        'LAV': '#16a34a'
    }
    priority = summary.get('priority', 'MEDIUM')
    color = priority_colors.get(priority, '#ca8a04')

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #0066FF; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">🐟 AquaRegWatch Alert</h1>
        </div>
        <div style="padding: 24px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
            <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                {priority}
            </span>
            <h2 style="margin: 16px 0 8px;">{summary.get('title', 'Change Detected')}</h2>
            <p style="color: #666; margin: 0;">{source['name']} | {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>

            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0066FF;">
                <h4 style="margin: 0 0 8px; color: #1e40af;">🇳🇴 Norsk</h4>
                <p style="margin: 0; line-height: 1.6;">{summary.get('summary_no', 'N/A')}</p>
            </div>

            <div style="background: #f8fafc; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0066FF;">
                <h4 style="margin: 0 0 8px; color: #1e40af;">🇬🇧 English</h4>
                <p style="margin: 0; line-height: 1.6;">{summary.get('summary_en', 'N/A')}</p>
            </div>

            <p style="margin-top: 24px;">
                <a href="{source['url']}" style="background: #0066FF; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; display: inline-block;">
                    View Source →
                </a>
            </p>

            <hr style="margin: 24px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                AquaRegWatch by TefiAqua | <a href="https://tefiaqua.no" style="color: #9ca3af;">tefiaqua.no</a>
            </p>
        </div>
    </div>
    """

    subject = f"[{priority}] {summary.get('title', 'Regulatory Change')}"

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
            return True
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

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
                server.login(gmail_user, gmail_pass)
                server.sendmail(gmail_user, to_email, msg.as_string())

            log.info(f"Alert sent via Gmail to {to_email}")
            return True
        except Exception as e:
            log.error(f"Gmail failed: {e}")

    # Fallback: print (at least it's in the logs)
    log.error("All email providers failed - printing alert to logs")
    print_alert(source, summary)
    return False


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
    """Main monitoring loop with comprehensive error handling."""
    log.info("="*60)
    log.info("AquaRegWatch v2.0 - Starting regulatory monitor")
    log.info("="*60)

    snapshots = load_snapshots()
    changes_found = []
    errors = []

    for i, source in enumerate(SOURCES):
        log.info(f"[{i+1}/{len(SOURCES)}] Checking: {source['name']}")

        # Rate limiting
        if i > 0:
            time.sleep(RATE_LIMIT_DELAY)

        content, content_hash = fetch_page_with_retry(source['url'])

        if content is None:
            errors.append(source['name'])
            should_alert = track_failure(source['id'], "Fetch failed")
            log.warning(f"  ⚠ Skipped (fetch failed)")
            continue

        # Clear any previous failure tracking
        clear_failure(source['id'])

        source_id = source['id']
        previous = snapshots.get(source_id, {})
        previous_hash = previous.get('hash')

        if previous_hash is None:
            log.info(f"  📸 First snapshot saved")
            snapshots[source_id] = {
                'hash': content_hash,
                'content': content[:5000],
                'last_checked': datetime.now().isoformat(),
                'url': source['url']
            }
        elif content_hash != previous_hash:
            log.info(f"  🔔 CHANGE DETECTED!")

            # Load customers for personalized alerts
            customers = load_customers()

            if customers:
                # Send PERSONALIZED alerts to each customer
                log.info(f"  Sending personalized alerts to {len(customers)} customers...")
                for customer in customers:
                    company = customer.get('company', 'Unknown')
                    log.info(f"    Analyzing for {company}...")

                    # Generate personalized summary for this customer
                    personalized_summary = summarize_change_for_customer(
                        source, previous.get('content', ''), content, customer
                    )

                    # Send personalized alert
                    send_alert_to_customer(source, personalized_summary, customer)

                    # Small delay to avoid rate limits
                    time.sleep(0.5)

                # Also save a generic summary for records
                summary = summarize_change(source, previous.get('content', ''), content)
            else:
                # No customers - use fallback alert email
                log.info(f"  No customers configured, using ALERT_EMAIL fallback")
                summary = summarize_change(source, previous.get('content', ''), content)
                send_alert(source, summary)

            # Record change
            change = {
                'source_id': source_id,
                'source_name': source['name'],
                'url': source['url'],
                'detected_at': datetime.now().isoformat(),
                'summary': summary if 'summary' in dir() else {"title": "Change detected"},
                'customers_notified': len(customers) if customers else 0
            }
            save_change(change)
            changes_found.append(change)

            # Update snapshot
            snapshots[source_id] = {
                'hash': content_hash,
                'content': content[:5000],
                'last_checked': datetime.now().isoformat(),
                'url': source['url']
            }
        else:
            log.info(f"  ✓ No changes")
            snapshots[source_id]['last_checked'] = datetime.now().isoformat()

    # Save snapshots
    save_snapshots(snapshots)

    # Summary
    log.info("="*60)
    log.info(f"Monitor complete: {len(changes_found)} changes, {len(errors)} errors")
    if changes_found:
        log.info("Changes detected:")
        for c in changes_found:
            log.info(f"  🔔 {c['source_name']}: {c['summary'].get('title', 'Change')}")
    if errors:
        log.warning(f"Failed sources: {', '.join(errors)}")
    log.info("="*60)

    return changes_found


if __name__ == "__main__":
    run_monitor()
