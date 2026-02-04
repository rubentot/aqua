"""
Scheduler for Norwegian Aquaculture Regulatory Monitor
Supports multiple scheduling backends: cron, APScheduler, GitHub Actions
"""
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """
    Flexible scheduler for the monitoring service.
    Can run as a daemon or be triggered by external schedulers.
    """

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.running = False
        self.monitor = None

    def _init_monitor(self):
        """Lazy initialization of monitor"""
        if self.monitor is None:
            from .monitor import AquaRegMonitor
            self.monitor = AquaRegMonitor(self.config_path)
        return self.monitor

    def run_once(self):
        """Run a single monitoring cycle"""
        logger.info(f"Running monitoring cycle at {datetime.now()}")
        monitor = self._init_monitor()
        changes = monitor.run_full_cycle()
        logger.info(f"Cycle complete: {len(changes)} changes detected")
        return changes

    def run_daemon(self, check_interval_minutes: int = 60):
        """
        Run as a continuous daemon process.
        Useful for running on a VM or container.
        """
        import schedule

        logger.info(f"Starting daemon with {check_interval_minutes} minute interval")

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal, stopping...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Schedule the job
        schedule.every(check_interval_minutes).minutes.do(self.run_once)

        # Run immediately on startup
        self.run_once()

        # Main loop
        self.running = True
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

        logger.info("Daemon stopped")

    def run_apscheduler(self, check_interval_minutes: int = 60):
        """
        Run using APScheduler for more advanced scheduling needs.
        Supports cron-like expressions.
        """
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BlockingScheduler(timezone="Europe/Oslo")

        # Add main monitoring job
        scheduler.add_job(
            self.run_once,
            IntervalTrigger(minutes=check_interval_minutes),
            id="main_monitor",
            name="Main regulatory monitoring",
            replace_existing=True
        )

        # Add daily digest job at 7 AM Oslo time
        scheduler.add_job(
            self._send_daily_digest,
            CronTrigger(hour=7, minute=0, timezone="Europe/Oslo"),
            id="daily_digest",
            name="Daily digest emails",
            replace_existing=True
        )

        # Add weekly report job on Monday at 8 AM
        scheduler.add_job(
            self._send_weekly_report,
            CronTrigger(day_of_week="mon", hour=8, minute=0, timezone="Europe/Oslo"),
            id="weekly_report",
            name="Weekly summary report",
            replace_existing=True
        )

        logger.info("Starting APScheduler")
        logger.info(f"Jobs scheduled: {[job.name for job in scheduler.get_jobs()]}")

        try:
            # Run once immediately
            self.run_once()
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")

    def _send_daily_digest(self):
        """Send daily digest to all clients"""
        logger.info("Sending daily digest emails")
        monitor = self._init_monitor()
        monitor.notify_clients()

    def _send_weekly_report(self):
        """Generate and send weekly summary report"""
        logger.info("Generating weekly report")
        monitor = self._init_monitor()
        stats = monitor.get_stats()
        # Additional weekly report logic can be added here
        logger.info(f"Weekly stats: {stats}")


def generate_cron_entries(check_interval_hours: int = 1) -> str:
    """
    Generate crontab entries for the monitoring service.
    """
    script_path = os.path.abspath(__file__)
    project_dir = os.path.dirname(os.path.dirname(script_path))

    cron_template = f"""# AquaRegWatch Norway - Regulatory Monitoring
# Generated: {datetime.now().isoformat()}

# Main monitoring job - runs every {check_interval_hours} hour(s)
0 */{check_interval_hours} * * * cd {project_dir} && /usr/bin/python3 -m src.scheduler --run-once >> /var/log/aquaregwatch.log 2>&1

# Daily digest at 7:00 AM Oslo time (5:00 UTC in winter, 6:00 UTC in summer)
0 6 * * * cd {project_dir} && /usr/bin/python3 -m src.scheduler --digest >> /var/log/aquaregwatch.log 2>&1

# Weekly report on Monday at 8:00 AM Oslo time
0 7 * * 1 cd {project_dir} && /usr/bin/python3 -m src.scheduler --weekly >> /var/log/aquaregwatch.log 2>&1
"""
    return cron_template


def generate_github_actions_workflow() -> str:
    """
    Generate GitHub Actions workflow for serverless monitoring.
    """
    return """# .github/workflows/monitor.yml
# AquaRegWatch Norway - GitHub Actions Workflow

name: Aquaculture Regulatory Monitor

on:
  schedule:
    # Run every hour
    - cron: '0 * * * *'
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        default: 'check'
        type: choice
        options:
          - check
          - digest
          - stats

env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

jobs:
  monitor:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Download previous database
        uses: actions/download-artifact@v4
        with:
          name: aquaregwatch-db
          path: data/
        continue-on-error: true

      - name: Run monitoring
        run: |
          python -m src.scheduler --run-once
        if: github.event.inputs.action == 'check' || github.event_name == 'schedule'

      - name: Send daily digest
        run: |
          python -m src.scheduler --digest
        if: github.event.inputs.action == 'digest'

      - name: Show stats
        run: |
          python -m src.scheduler --stats
        if: github.event.inputs.action == 'stats'

      - name: Upload database artifact
        uses: actions/upload-artifact@v4
        with:
          name: aquaregwatch-db
          path: data/aquaregwatch.db
          retention-days: 30
        if: always()

  daily-digest:
    runs-on: ubuntu-latest
    # Run at 7 AM Oslo time (6 AM UTC in summer, 5 AM UTC in winter)
    if: github.event.schedule == '0 6 * * *'

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Download database
        uses: actions/download-artifact@v4
        with:
          name: aquaregwatch-db
          path: data/
        continue-on-error: true

      - name: Send daily digest
        run: python -m src.scheduler --digest
        env:
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
"""


def generate_docker_compose() -> str:
    """Generate Docker Compose configuration for self-hosted deployment"""
    return """# docker-compose.yml
# AquaRegWatch Norway - Docker Deployment

version: '3.8'

services:
  monitor:
    build: .
    container_name: aquaregwatch
    restart: unless-stopped
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      - TZ=Europe/Oslo
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    command: python -m src.scheduler --daemon

  dashboard:
    build: .
    container_name: aquaregwatch-dashboard
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - TZ=Europe/Oslo
    volumes:
      - ./data:/app/data:ro
    command: streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0

volumes:
  data:
"""


# CLI interface
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="AquaRegWatch Scheduler")
    parser.add_argument("--config", default="config/settings.yaml", help="Config file path")
    parser.add_argument("--run-once", action="store_true", help="Run single monitoring cycle")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--apscheduler", action="store_true", help="Run with APScheduler")
    parser.add_argument("--digest", action="store_true", help="Send daily digest")
    parser.add_argument("--weekly", action="store_true", help="Send weekly report")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in minutes")
    parser.add_argument("--generate-cron", action="store_true", help="Generate cron entries")
    parser.add_argument("--generate-github", action="store_true", help="Generate GitHub Actions workflow")
    parser.add_argument("--generate-docker", action="store_true", help="Generate Docker Compose")

    args = parser.parse_args()

    scheduler = MonitorScheduler(config_path=args.config)

    if args.run_once:
        scheduler.run_once()

    elif args.daemon:
        scheduler.run_daemon(check_interval_minutes=args.interval)

    elif args.apscheduler:
        scheduler.run_apscheduler(check_interval_minutes=args.interval)

    elif args.digest:
        scheduler._send_daily_digest()

    elif args.weekly:
        scheduler._send_weekly_report()

    elif args.stats:
        monitor = scheduler._init_monitor()
        stats = monitor.get_stats()
        print("\nAquaRegWatch Statistics:")
        print("-" * 40)
        for category, values in stats.items():
            print(f"\n{category.upper()}:")
            for key, value in values.items():
                print(f"  {key}: {value}")

    elif args.generate_cron:
        print(generate_cron_entries(args.interval // 60 or 1))

    elif args.generate_github:
        print(generate_github_actions_workflow())

    elif args.generate_docker:
        print(generate_docker_compose())

    else:
        parser.print_help()
