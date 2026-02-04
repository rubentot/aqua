"""
Delivery Module for Norwegian Aquaculture Regulatory Monitor
Handles Email (SendGrid/Gmail) and Slack notifications
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    """Result of a delivery attempt"""
    success: bool
    method: str  # email, slack
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EmailDelivery:
    """
    Email delivery using SendGrid or Gmail.
    Supports both individual alerts and digest emails.
    """

    def __init__(
        self,
        provider: str = "sendgrid",
        api_key: str = None,
        from_address: str = None,
        from_name: str = "AquaRegWatch Norway"
    ):
        self.provider = provider.lower()
        self.from_address = from_address or os.getenv("EMAIL_FROM_ADDRESS", "alerts@aquaregwatch.no")
        self.from_name = from_name

        if self.provider == "sendgrid":
            self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
            self._init_sendgrid()
        elif self.provider == "gmail":
            self.email = os.getenv("GMAIL_ADDRESS")
            self.password = os.getenv("GMAIL_APP_PASSWORD")
        else:
            raise ValueError(f"Unknown email provider: {provider}")

    def _init_sendgrid(self):
        """Initialize SendGrid client"""
        try:
            from sendgrid import SendGridAPIClient
            self.client = SendGridAPIClient(self.api_key)
            logger.info("Initialized SendGrid client")
        except ImportError:
            raise ImportError("sendgrid package not installed. Run: pip install sendgrid")

    def _format_alert_html(self, summary: Dict) -> str:
        """Format a single alert as HTML"""
        action_items_html = ""
        if summary.get("action_items"):
            action_items_html = "<h3>🎯 Handlingspunkter / Action Items</h3><ul>"
            for item in summary["action_items"]:
                deadline = f" (Frist: {item.get('deadline')})" if item.get('deadline') else ""
                priority_badge = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(item.get("priority", "medium"), "")
                action_items_html += f"<li>{priority_badge} {item.get('action')}{deadline}</li>"
            action_items_html += "</ul>"

        penalties_html = ""
        if summary.get("penalties"):
            penalties_html = "<h3>⚠️ Potensielle sanksjoner / Potential Penalties</h3><ul>"
            for penalty in summary["penalties"]:
                penalties_html += f"<li>{penalty}</li>"
            penalties_html += "</ul>"

        affected_html = ""
        if summary.get("who_affected"):
            affected_html = f"<p><strong>Hvem påvirkes:</strong> {', '.join(summary['who_affected'])}</p>"

        return f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 10px 0; background: #fff;">
            <h2 style="color: #1a5276; margin-top: 0;">{summary.get('title', 'Regulatory Update')}</h2>

            <div style="background: #eef9ff; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3 style="margin-top: 0;">🇳🇴 Norsk</h3>
                <p>{summary.get('summary_no', '')}</p>
            </div>

            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3 style="margin-top: 0;">🇬🇧 English</h3>
                <p>{summary.get('summary_en', '')}</p>
            </div>

            {affected_html}

            <h3>📋 Hva har endret seg / What Changed</h3>
            <p>{summary.get('what_changed', '')}</p>

            {action_items_html}
            {penalties_html}

            <p style="color: #666; font-size: 0.9em;">
                <strong>Kilde / Source:</strong>
                <a href="{summary.get('source_url', '#')}">{summary.get('source_url', 'Unknown')}</a><br>
                <strong>Kategori:</strong> {summary.get('category', 'Unknown')}<br>
                <strong>Prioritet:</strong> {summary.get('priority', 'medium').upper()}
            </p>
        </div>
        """

    def _format_digest_html(self, summaries: List[Dict], client_name: str) -> str:
        """Format multiple alerts as a digest email"""
        alerts_html = ""
        for summary in summaries:
            alerts_html += self._format_alert_html(summary)

        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for s in summaries:
            p = s.get("priority", "medium")
            priority_counts[p] = priority_counts.get(p, 0) + 1

        stats_html = f"""
        <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">📊 Oversikt / Summary</h3>
            <p>
                🔴 Kritisk/Critical: {priority_counts['critical']} |
                🟠 Høy/High: {priority_counts['high']} |
                🟡 Medium: {priority_counts['medium']} |
                🟢 Lav/Low: {priority_counts['low']}
            </p>
        </div>
        """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>AquaRegWatch Daily Digest</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
            <div style="background: #1a5276; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="margin: 0;">🐟 AquaRegWatch Norway</h1>
                <p style="margin: 5px 0 0 0;">Daglig oversikt over reguleringsendringer / Daily Regulatory Digest</p>
            </div>

            <div style="background: white; padding: 20px; border-radius: 0 0 8px 8px;">
                <p>Hei {client_name},</p>
                <p>Her er dagens oppdateringer fra norske akvakulturmyndigheter:</p>

                {stats_html}
                {alerts_html}

                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                <p style="color: #666; font-size: 0.9em;">
                    Dette er en automatisk generert rapport fra AquaRegWatch Norway.<br>
                    For spørsmål, kontakt oss på support@aquaregwatch.no<br><br>
                    <a href="#">Administrer varsler</a> | <a href="#">Avmeld</a>
                </p>
            </div>
        </body>
        </html>
        """

    def send_alert(
        self,
        to_email: str,
        summary: Dict,
        client_name: str = "Valued Customer"
    ) -> DeliveryResult:
        """Send a single alert email"""
        subject = f"🐟 AquaRegWatch: {summary.get('title', 'Regulatory Update')}"
        html_content = self._format_digest_html([summary], client_name)

        return self._send_email(to_email, subject, html_content)

    def send_digest(
        self,
        to_email: str,
        summaries: List[Dict],
        client_name: str = "Valued Customer"
    ) -> DeliveryResult:
        """Send a digest email with multiple alerts"""
        count = len(summaries)
        date_str = datetime.now().strftime("%d.%m.%Y")
        subject = f"🐟 AquaRegWatch Daglig Oversikt: {count} endringer ({date_str})"

        html_content = self._format_digest_html(summaries, client_name)

        return self._send_email(to_email, subject, html_content)

    def _send_email(self, to_email: str, subject: str, html_content: str) -> DeliveryResult:
        """Send email via configured provider"""
        if self.provider == "sendgrid":
            return self._send_via_sendgrid(to_email, subject, html_content)
        else:
            return self._send_via_gmail(to_email, subject, html_content)

    def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> DeliveryResult:
        """Send via SendGrid API"""
        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content

            message = Mail(
                from_email=Email(self.from_address, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return DeliveryResult(
                    success=True,
                    method="email",
                    recipient=to_email,
                    message_id=response.headers.get("X-Message-Id")
                )
            else:
                logger.error(f"SendGrid error: {response.status_code}")
                return DeliveryResult(
                    success=False,
                    method="email",
                    recipient=to_email,
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return DeliveryResult(
                success=False,
                method="email",
                recipient=to_email,
                error=str(e)
            )

    def _send_via_gmail(self, to_email: str, subject: str, html_content: str) -> DeliveryResult:
        """Send via Gmail SMTP"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.email}>"
            msg["To"] = to_email

            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email, self.password)
                server.send_message(msg)

            logger.info(f"Gmail sent successfully to {to_email}")
            return DeliveryResult(
                success=True,
                method="email",
                recipient=to_email
            )

        except Exception as e:
            logger.error(f"Gmail send failed: {e}")
            return DeliveryResult(
                success=False,
                method="email",
                recipient=to_email,
                error=str(e)
            )


class SlackDelivery:
    """
    Slack delivery via webhooks or Bot API.
    Supports real-time alerts and formatted messages.
    """

    def __init__(
        self,
        webhook_url: str = None,
        bot_token: str = None,
        default_channel: str = "#aquaculture-alerts"
    ):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = default_channel

        if self.bot_token:
            self._init_slack_client()

    def _init_slack_client(self):
        """Initialize Slack SDK client"""
        try:
            from slack_sdk import WebClient
            self.client = WebClient(token=self.bot_token)
            logger.info("Initialized Slack client")
        except ImportError:
            logger.warning("slack_sdk not installed, will use webhooks only")
            self.client = None

    def _format_alert_blocks(self, summary: Dict) -> List[Dict]:
        """Format alert as Slack Block Kit message"""
        priority_emoji = {
            "critical": "🚨",
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }.get(summary.get("priority", "medium"), "📋")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{priority_emoji} {summary.get('title', 'Regulatory Update')}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🇳🇴 Norsk:*\n{summary.get('summary_no', 'N/A')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🇬🇧 English:*\n{summary.get('summary_en', 'N/A')}"
                }
            },
            {"type": "divider"}
        ]

        # Who affected
        if summary.get("who_affected"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*👥 Hvem påvirkes:*\n{', '.join(summary['who_affected'])}"
                }
            })

        # Action items
        if summary.get("action_items"):
            action_text = "*🎯 Handlingspunkter:*\n"
            for item in summary["action_items"]:
                priority_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.get("priority"), "")
                deadline = f" _(Frist: {item['deadline']})_" if item.get("deadline") else ""
                action_text += f"• {priority_badge} {item.get('action')}{deadline}\n"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": action_text}
            })

        # Penalties
        if summary.get("penalties"):
            penalties_text = "*⚠️ Sanksjoner:*\n" + "\n".join(f"• {p}" for p in summary["penalties"])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": penalties_text}
            })

        # Source link
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📍 *Kilde:* <{summary.get('source_url', '#')}|{summary.get('source_url', 'Unknown')[:50]}...> | *Kategori:* {summary.get('category', 'N/A')} | *Prioritet:* {summary.get('priority', 'medium').upper()}"
                }
            ]
        })

        return blocks

    def send_alert(
        self,
        summary: Dict,
        channel: str = None,
        webhook_url: str = None
    ) -> DeliveryResult:
        """Send a single alert to Slack"""
        channel = channel or self.default_channel
        webhook = webhook_url or self.webhook_url

        blocks = self._format_alert_blocks(summary)

        # Try webhook first (simpler)
        if webhook:
            return self._send_via_webhook(webhook, blocks, summary.get("title", "Alert"))

        # Fall back to Bot API
        if self.client:
            return self._send_via_bot(channel, blocks, summary.get("title", "Alert"))

        return DeliveryResult(
            success=False,
            method="slack",
            recipient=channel,
            error="No webhook URL or bot token configured"
        )

    def send_digest(
        self,
        summaries: List[Dict],
        channel: str = None,
        webhook_url: str = None
    ) -> DeliveryResult:
        """Send a digest with multiple alerts"""
        channel = channel or self.default_channel

        # Header block
        date_str = datetime.now().strftime("%d.%m.%Y")
        header_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🐟 AquaRegWatch Daglig Oversikt - {date_str}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(summaries)} reguleringsendringer oppdaget*"
                }
            },
            {"type": "divider"}
        ]

        # Send header
        webhook = webhook_url or self.webhook_url
        if webhook:
            self._send_via_webhook(webhook, header_blocks, "Digest Header")

        # Send each alert as a threaded message (if using bot)
        results = []
        for summary in summaries:
            result = self.send_alert(summary, channel, webhook_url)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        return DeliveryResult(
            success=success_count == len(results),
            method="slack",
            recipient=channel,
            message_id=f"digest_{len(summaries)}_alerts"
        )

    def _send_via_webhook(self, webhook_url: str, blocks: List[Dict], fallback_text: str) -> DeliveryResult:
        """Send via Slack webhook"""
        import requests

        payload = {
            "blocks": blocks,
            "text": fallback_text  # Fallback for notifications
        }

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Slack webhook sent successfully")
                return DeliveryResult(
                    success=True,
                    method="slack",
                    recipient="webhook"
                )
            else:
                logger.error(f"Slack webhook error: {response.status_code} - {response.text}")
                return DeliveryResult(
                    success=False,
                    method="slack",
                    recipient="webhook",
                    error=f"HTTP {response.status_code}: {response.text}"
                )

        except Exception as e:
            logger.error(f"Slack webhook failed: {e}")
            return DeliveryResult(
                success=False,
                method="slack",
                recipient="webhook",
                error=str(e)
            )

    def _send_via_bot(self, channel: str, blocks: List[Dict], fallback_text: str) -> DeliveryResult:
        """Send via Slack Bot API"""
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=fallback_text
            )

            if response["ok"]:
                logger.info(f"Slack message sent to {channel}")
                return DeliveryResult(
                    success=True,
                    method="slack",
                    recipient=channel,
                    message_id=response.get("ts")
                )
            else:
                return DeliveryResult(
                    success=False,
                    method="slack",
                    recipient=channel,
                    error=response.get("error", "Unknown error")
                )

        except Exception as e:
            logger.error(f"Slack Bot API failed: {e}")
            return DeliveryResult(
                success=False,
                method="slack",
                recipient=channel,
                error=str(e)
            )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example summary
    example_summary = {
        "title": "Ny lakselusgrense fra mars 2026",
        "summary_no": "Mattilsynet har vedtatt nye, strengere grenser for lakselus. Grensen reduseres fra 0.5 til 0.25 voksne hunnlus per fisk, med virkning fra 1. mars 2026.",
        "summary_en": "The Norwegian Food Safety Authority has adopted new, stricter sea lice limits. The threshold is reduced from 0.5 to 0.25 adult female lice per fish, effective March 1, 2026.",
        "what_changed": "Lakselusgrensen er halvert fra 0.5 til 0.25 per fisk",
        "who_affected": ["Lakseoppdrettere", "Regnbueørretoppdrettere", "Oppdrettere i røde soner"],
        "potential_impact": "Økte behandlingskostnader, mulig produksjonsreduksjon",
        "action_items": [
            {"action": "Oppdater lusetellingsrutiner", "deadline": "2026-02-15", "priority": "high"},
            {"action": "Søk dispensasjon hvis nødvendig", "deadline": "2026-03-15", "priority": "high"},
            {"action": "Vurder behandlingskapasitet", "deadline": None, "priority": "medium"}
        ],
        "deadlines": [{"date": "2026-03-01", "description": "Ny forskrift trer i kraft"}],
        "penalties": ["Bot opptil 1 million NOK", "Mulig produksjonsstopp"],
        "category": "fish_health",
        "priority": "critical",
        "source_url": "https://www.mattilsynet.no/fisk/lakselus"
    }

    # Test Slack formatting (without actually sending)
    slack = SlackDelivery()
    blocks = slack._format_alert_blocks(example_summary)
    print("Slack blocks generated:")
    print(json.dumps(blocks, indent=2, ensure_ascii=False))

    # Test Email formatting (without actually sending)
    email = EmailDelivery.__new__(EmailDelivery)
    email.from_name = "AquaRegWatch"
    html = email._format_alert_html(example_summary)
    print("\n\nEmail HTML preview (first 1000 chars):")
    print(html[:1000])
