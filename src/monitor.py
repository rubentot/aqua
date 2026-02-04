"""
Main Monitor Orchestrator for Norwegian Aquaculture Regulatory Monitor
Coordinates scraping, change detection, AI summarization, and delivery
"""
import logging
import os
import yaml
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

from .models import (
    init_database, get_session, Source, Snapshot, Change, Client,
    Notification, DigestQueue
)
from .scraper import NorwegianAquacultureScraper, ScrapedContent
from .change_detector import ChangeDetector, ChangeAnalysis
from .ai_summarizer import AISummarizer, RegulatorySummary
from .delivery import EmailDelivery, SlackDelivery, DeliveryResult

logger = logging.getLogger(__name__)


class AquaRegMonitor:
    """
    Main orchestrator for the aquaculture regulatory monitoring service.
    Handles the complete workflow from scraping to delivery.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize monitor with configuration"""
        self.config = self._load_config(config_path)
        self.db_session = None
        self.scraper = None
        self.change_detector = None
        self.ai_summarizer = None
        self.email_delivery = None
        self.slack_delivery = None

        self._init_components()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _init_components(self):
        """Initialize all service components"""
        # Database
        db_config = self.config.get("database", {})
        db_path = db_config.get("path", "data/aquaregwatch.db")

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        engine, Session = init_database(f"sqlite:///{db_path}")
        self.db_session = Session()
        logger.info(f"Database initialized: {db_path}")

        # Scraper
        monitoring_config = self.config.get("monitoring", {})
        self.scraper = NorwegianAquacultureScraper(
            timeout=monitoring_config.get("request_timeout_seconds", 30),
            max_retries=monitoring_config.get("max_retries", 3),
            rate_limit_delay=60 / monitoring_config.get("rate_limit_requests_per_minute", 10)
        )
        logger.info("Scraper initialized")

        # Change Detector
        change_config = self.config.get("change_detection", {})
        self.change_detector = ChangeDetector(
            min_change_threshold=change_config.get("min_change_threshold_percent", 1.0)
        )
        logger.info("Change detector initialized")

        # AI Summarizer
        ai_config = self.config.get("ai", {})
        try:
            self.ai_summarizer = AISummarizer(
                provider=ai_config.get("provider", "anthropic"),
                model=ai_config.get("model")
            )
            logger.info("AI summarizer initialized")
        except Exception as e:
            logger.warning(f"AI summarizer not available: {e}")
            self.ai_summarizer = None

        # Email Delivery
        email_config = self.config.get("delivery", {}).get("email", {})
        if email_config.get("enabled", True):
            try:
                self.email_delivery = EmailDelivery(
                    provider=email_config.get("provider", "sendgrid"),
                    from_address=email_config.get("from_address"),
                    from_name=email_config.get("from_name", "AquaRegWatch Norway")
                )
                logger.info("Email delivery initialized")
            except Exception as e:
                logger.warning(f"Email delivery not available: {e}")

        # Slack Delivery
        slack_config = self.config.get("delivery", {}).get("slack", {})
        if slack_config.get("enabled", True):
            try:
                self.slack_delivery = SlackDelivery(
                    default_channel=slack_config.get("default_channel", "#aquaculture-alerts")
                )
                logger.info("Slack delivery initialized")
            except Exception as e:
                logger.warning(f"Slack delivery not available: {e}")

    def _init_sources(self):
        """Initialize sources from configuration into database"""
        sources_config = self.config.get("sources", [])

        for source_data in sources_config:
            existing = self.db_session.query(Source).filter_by(id=source_data["id"]).first()

            if not existing:
                source = Source(
                    id=source_data["id"],
                    name=source_data["name"],
                    url=source_data["url"],
                    category=source_data.get("category", "unknown"),
                    check_interval_hours=source_data.get("check_interval_hours", 4),
                    priority=source_data.get("priority", "medium"),
                    selectors=source_data.get("selectors"),
                    is_active=True
                )
                self.db_session.add(source)
                logger.info(f"Added source: {source.name}")

        self.db_session.commit()

    def get_sources_to_check(self) -> List[Source]:
        """Get sources that are due for checking"""
        now = datetime.utcnow()
        sources = []

        all_sources = self.db_session.query(Source).filter_by(is_active=True).all()

        for source in all_sources:
            # Check if due for refresh
            if source.last_checked is None:
                sources.append(source)
            else:
                next_check = source.last_checked + timedelta(hours=source.check_interval_hours)
                if now >= next_check:
                    sources.append(source)

        return sources

    def check_source(self, source: Source) -> Optional[Change]:
        """
        Check a single source for changes.
        Returns Change object if changes detected, None otherwise.
        """
        logger.info(f"Checking source: {source.name} ({source.url})")

        # Fetch current content
        scraped = self.scraper.fetch_page(
            source.url,
            custom_selectors=source.selectors
        )

        if scraped.error:
            logger.error(f"Failed to fetch {source.name}: {scraped.error}")
            source.last_checked = datetime.utcnow()
            self.db_session.commit()
            return None

        # Create snapshot
        current_snapshot = Snapshot(
            source_id=source.id,
            content_hash=scraped.content_hash,
            content_text=scraped.text,
            content_html=scraped.html[:50000],  # Limit storage
            word_count=scraped.word_count,
            http_status=scraped.http_status,
            response_time_ms=scraped.response_time_ms
        )
        self.db_session.add(current_snapshot)
        self.db_session.flush()  # Get ID

        # Get previous snapshot
        previous_snapshot = self.db_session.query(Snapshot).filter(
            Snapshot.source_id == source.id,
            Snapshot.id != current_snapshot.id
        ).order_by(Snapshot.captured_at.desc()).first()

        # Update source
        source.last_checked = datetime.utcnow()

        # Compare if we have previous content
        if previous_snapshot and previous_snapshot.content_hash != current_snapshot.content_hash:
            # Detect changes
            analysis = self.change_detector.detect_changes(
                old_content=previous_snapshot.content_text or "",
                new_content=current_snapshot.content_text or "",
                source_name=source.name
            )

            if analysis.has_changes and analysis.is_significant:
                logger.info(f"Significant change detected on {source.name}: {analysis.change_percent}%")

                # Create change record
                change = Change(
                    source_id=source.id,
                    previous_snapshot_id=previous_snapshot.id,
                    current_snapshot_id=current_snapshot.id,
                    change_type="modified",
                    change_percent=analysis.change_percent,
                    diff_text=analysis.diff_text[:10000],
                    added_text="\n".join(analysis.added_lines[:50]),
                    removed_text="\n".join(analysis.removed_lines[:50]),
                    keywords_found=analysis.significant_keywords_found,
                    is_significant=analysis.is_significant,
                    priority=source.priority
                )

                # AI Summarization
                if self.ai_summarizer:
                    try:
                        summary = self.ai_summarizer.summarize_change(
                            source_name=source.name,
                            source_url=source.url,
                            category=source.category,
                            old_content=previous_snapshot.content_text or "",
                            new_content=current_snapshot.content_text or "",
                            diff_summary=analysis.change_summary,
                            keywords_found=analysis.significant_keywords_found
                        )

                        change.summary_no = summary.summary_no
                        change.summary_en = summary.summary_en
                        change.impact_analysis = summary.potential_impact
                        change.affected_parties = summary.who_affected
                        change.action_items = summary.action_items
                        change.deadlines = summary.deadlines
                        change.processed_at = datetime.utcnow()
                        change.priority = summary.priority

                        logger.info(f"AI summary generated: {summary.title}")

                    except Exception as e:
                        logger.error(f"AI summarization failed: {e}")

                self.db_session.add(change)
                source.last_changed = datetime.utcnow()
                self.db_session.commit()

                return change

        self.db_session.commit()
        return None

    def check_all_sources(self) -> List[Change]:
        """Check all due sources and return list of changes"""
        self._init_sources()
        sources = self.get_sources_to_check()

        logger.info(f"Checking {len(sources)} sources")

        changes = []
        for source in sources:
            change = self.check_source(source)
            if change:
                changes.append(change)

        logger.info(f"Found {len(changes)} changes across {len(sources)} sources")
        return changes

    def get_pending_notifications(self) -> List[Dict]:
        """Get changes that need to be notified"""
        # Get changes from the last 24 hours that haven't been fully notified
        cutoff = datetime.utcnow() - timedelta(hours=24)

        changes = self.db_session.query(Change).filter(
            Change.detected_at >= cutoff,
            Change.is_significant == True
        ).all()

        return [self._change_to_dict(c) for c in changes]

    def _change_to_dict(self, change: Change) -> Dict:
        """Convert Change model to dictionary for delivery"""
        source = self.db_session.query(Source).get(change.source_id)

        return {
            "id": change.id,
            "title": f"Endring på {source.name}" if source else "Regulatory Change",
            "summary_no": change.summary_no or "Endringer oppdaget - se detaljer",
            "summary_en": change.summary_en or "Changes detected - see details",
            "what_changed": change.diff_text[:500] if change.diff_text else "",
            "who_affected": change.affected_parties or ["Akvakulturaktører"],
            "potential_impact": change.impact_analysis or "",
            "opportunities": [],
            "risks": [],
            "action_items": change.action_items or [],
            "deadlines": change.deadlines or [],
            "penalties": [],
            "category": source.category if source else "unknown",
            "priority": change.priority or "medium",
            "source_url": source.url if source else "",
            "detected_at": change.detected_at.isoformat() if change.detected_at else ""
        }

    def notify_clients(self, changes: List[Change] = None):
        """Send notifications to all relevant clients"""
        if changes is None:
            changes = self.db_session.query(Change).filter(
                Change.detected_at >= datetime.utcnow() - timedelta(hours=24),
                Change.is_significant == True
            ).all()

        if not changes:
            logger.info("No changes to notify")
            return

        clients = self.db_session.query(Client).filter_by(is_active=True).all()

        for client in clients:
            relevant_changes = self._filter_changes_for_client(changes, client)

            if not relevant_changes:
                continue

            summaries = [self._change_to_dict(c) for c in relevant_changes]

            # Email notification
            if client.email_enabled and self.email_delivery:
                if client.digest_frequency == "realtime":
                    for summary in summaries:
                        result = self.email_delivery.send_alert(
                            to_email=client.email,
                            summary=summary,
                            client_name=client.name
                        )
                        self._log_notification(client, relevant_changes[0], "email", result)
                else:
                    result = self.email_delivery.send_digest(
                        to_email=client.email,
                        summaries=summaries,
                        client_name=client.name
                    )
                    for change in relevant_changes:
                        self._log_notification(client, change, "email", result)

            # Slack notification
            if client.slack_enabled and self.slack_delivery:
                webhook = client.slack_webhook_url
                channel = client.slack_channel

                for summary in summaries:
                    result = self.slack_delivery.send_alert(
                        summary=summary,
                        channel=channel,
                        webhook_url=webhook
                    )
                    self._log_notification(client, relevant_changes[0], "slack", result)

    def _filter_changes_for_client(self, changes: List[Change], client: Client) -> List[Change]:
        """Filter changes based on client preferences"""
        filtered = []

        client_categories = client.categories or []
        priority_order = ["critical", "high", "medium", "low"]
        min_priority_idx = priority_order.index(client.priority_threshold or "low")

        for change in changes:
            source = self.db_session.query(Source).get(change.source_id)

            # Category filter
            if client_categories and source.category not in client_categories:
                continue

            # Priority filter
            change_priority_idx = priority_order.index(change.priority or "medium")
            if change_priority_idx > min_priority_idx:
                continue

            # Keyword filter
            if client.keywords:
                has_keyword = any(
                    kw.lower() in (change.diff_text or "").lower()
                    for kw in client.keywords
                )
                if not has_keyword:
                    continue

            filtered.append(change)

        return filtered

    def _log_notification(
        self,
        client: Client,
        change: Change,
        method: str,
        result: DeliveryResult
    ):
        """Log notification attempt to database"""
        notification = Notification(
            client_id=client.id,
            change_id=change.id,
            delivery_method=method,
            status="sent" if result.success else "failed",
            sent_at=datetime.utcnow() if result.success else None,
            error_message=result.error
        )
        self.db_session.add(notification)
        self.db_session.commit()

    def add_client(
        self,
        name: str,
        email: str,
        organization: str = None,
        tier: str = "basic",
        categories: List[str] = None,
        slack_webhook: str = None
    ) -> Client:
        """Add a new client/subscriber"""
        client = Client(
            name=name,
            email=email,
            organization=organization,
            tier=tier,
            categories=categories,
            slack_enabled=bool(slack_webhook),
            slack_webhook_url=slack_webhook
        )
        self.db_session.add(client)
        self.db_session.commit()
        logger.info(f"Added client: {name} ({email})")
        return client

    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        return {
            "sources": {
                "total": self.db_session.query(Source).count(),
                "active": self.db_session.query(Source).filter_by(is_active=True).count()
            },
            "snapshots": {
                "total": self.db_session.query(Snapshot).count(),
                "last_24h": self.db_session.query(Snapshot).filter(
                    Snapshot.captured_at >= day_ago
                ).count()
            },
            "changes": {
                "total": self.db_session.query(Change).count(),
                "last_24h": self.db_session.query(Change).filter(
                    Change.detected_at >= day_ago
                ).count(),
                "last_week": self.db_session.query(Change).filter(
                    Change.detected_at >= week_ago
                ).count()
            },
            "clients": {
                "total": self.db_session.query(Client).count(),
                "active": self.db_session.query(Client).filter_by(is_active=True).count()
            },
            "notifications": {
                "total": self.db_session.query(Notification).count(),
                "sent": self.db_session.query(Notification).filter_by(status="sent").count(),
                "failed": self.db_session.query(Notification).filter_by(status="failed").count()
            }
        }

    def run_full_cycle(self):
        """Run a complete monitoring cycle: check sources, analyze, notify"""
        logger.info("="*60)
        logger.info("Starting full monitoring cycle")
        logger.info("="*60)

        # Check all sources
        changes = self.check_all_sources()

        # Notify clients
        if changes:
            self.notify_clients(changes)

        # Log stats
        stats = self.get_stats()
        logger.info(f"Cycle complete. Stats: {stats}")

        return changes


# CLI interface
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="AquaRegWatch Monitor")
    parser.add_argument("--config", default="config/settings.yaml", help="Config file path")
    parser.add_argument("--check", action="store_true", help="Run a single check cycle")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--add-client", nargs=2, metavar=("NAME", "EMAIL"), help="Add a client")

    args = parser.parse_args()

    monitor = AquaRegMonitor(config_path=args.config)

    if args.check:
        changes = monitor.run_full_cycle()
        print(f"\nDetected {len(changes)} changes")

    elif args.stats:
        stats = monitor.get_stats()
        print("\nAquaRegWatch Statistics:")
        print("-" * 40)
        for category, values in stats.items():
            print(f"\n{category.upper()}:")
            for key, value in values.items():
                print(f"  {key}: {value}")

    elif args.add_client:
        name, email = args.add_client
        client = monitor.add_client(name=name, email=email)
        print(f"Added client: {client.name} ({client.email})")

    else:
        parser.print_help()
