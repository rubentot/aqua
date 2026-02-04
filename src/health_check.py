"""
Health Check Module for AquaRegWatch
Ensures the system is running reliably and alerts on failures
"""
import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)


class HealthChecker:
    """Monitor system health and alert on failures"""

    def __init__(self):
        self.alert_email = os.getenv("ALERT_EMAIL")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")

    def check_source_accessibility(self, sources: List[Dict]) -> Dict:
        """Check if all monitored sources are accessible"""
        results = {
            "total": len(sources),
            "accessible": 0,
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }

        for source in sources:
            try:
                response = requests.head(
                    source["url"],
                    timeout=10,
                    headers={"User-Agent": "AquaRegWatch HealthCheck/1.0"}
                )
                if response.status_code < 400:
                    results["accessible"] += 1
                else:
                    results["failed"].append({
                        "name": source["name"],
                        "url": source["url"],
                        "status": response.status_code
                    })
            except Exception as e:
                results["failed"].append({
                    "name": source["name"],
                    "url": source["url"],
                    "error": str(e)
                })

        return results

    def check_database(self, db_path: str = "data/aquaregwatch.db") -> Dict:
        """Check database connectivity and basic stats"""
        import sqlite3

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get counts
            cursor.execute("SELECT COUNT(*) FROM sources")
            sources = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM changes")
            changes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM clients")
            clients = cursor.fetchone()[0]

            # Get latest snapshot time
            cursor.execute("SELECT MAX(captured_at) FROM snapshots")
            last_snapshot = cursor.fetchone()[0]

            conn.close()

            return {
                "status": "healthy",
                "sources": sources,
                "changes": changes,
                "clients": clients,
                "last_snapshot": last_snapshot
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def check_api_keys(self) -> Dict:
        """Verify API keys are configured"""
        keys = {
            "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
            "SENDGRID_API_KEY": bool(os.getenv("SENDGRID_API_KEY")),
            "SLACK_WEBHOOK_URL": bool(os.getenv("SLACK_WEBHOOK_URL")),
        }

        return {
            "configured": sum(keys.values()),
            "total": len(keys),
            "details": keys
        }

    def send_alert(self, title: str, message: str, severity: str = "warning"):
        """Send alert via Slack and/or email"""
        emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(severity, "📢")

        # Slack alert
        if self.slack_webhook:
            try:
                payload = {
                    "text": f"{emoji} *AquaRegWatch Alert*\n*{title}*\n{message}"
                }
                requests.post(self.slack_webhook, json=payload, timeout=10)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")

        # Log it
        logger.warning(f"ALERT [{severity}]: {title} - {message}")

    def run_full_health_check(self) -> Dict:
        """Run complete health check"""
        from src.models import get_session, Source

        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy"
        }

        # Check database
        results["database"] = self.check_database()
        if results["database"]["status"] != "healthy":
            results["overall_status"] = "degraded"

        # Check API keys
        results["api_keys"] = self.check_api_keys()
        if results["api_keys"]["configured"] == 0:
            results["overall_status"] = "degraded"

        # Check sources
        try:
            session = get_session()
            sources = session.query(Source).filter_by(is_active=True).all()
            source_list = [{"name": s.name, "url": s.url} for s in sources]
            results["sources"] = self.check_source_accessibility(source_list)

            if results["sources"]["failed"]:
                results["overall_status"] = "degraded"
                self.send_alert(
                    "Source Accessibility Issues",
                    f"{len(results['sources']['failed'])} sources are not accessible",
                    "warning"
                )
        except Exception as e:
            results["sources"] = {"error": str(e)}
            results["overall_status"] = "error"

        return results


def run_health_check():
    """CLI entry point for health check"""
    checker = HealthChecker()
    results = checker.run_full_health_check()

    print("\n" + "="*60)
    print("🏥 AquaRegWatch Health Check")
    print("="*60)
    print(f"\nTimestamp: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status'].upper()}")

    print("\n📊 Database:")
    db = results.get("database", {})
    if db.get("status") == "healthy":
        print(f"   ✅ Healthy - {db.get('sources', 0)} sources, {db.get('changes', 0)} changes")
        print(f"   Last snapshot: {db.get('last_snapshot', 'Never')}")
    else:
        print(f"   ❌ Error: {db.get('error', 'Unknown')}")

    print("\n🔑 API Keys:")
    api = results.get("api_keys", {})
    for key, configured in api.get("details", {}).items():
        status = "✅" if configured else "❌"
        print(f"   {status} {key}")

    print("\n🌐 Sources:")
    sources = results.get("sources", {})
    if "error" not in sources:
        print(f"   ✅ {sources.get('accessible', 0)}/{sources.get('total', 0)} accessible")
        for failed in sources.get("failed", []):
            print(f"   ❌ {failed.get('name')}: {failed.get('status', failed.get('error', 'Unknown'))}")
    else:
        print(f"   ❌ Error: {sources.get('error')}")

    print("\n" + "="*60)

    return results


if __name__ == "__main__":
    run_health_check()
