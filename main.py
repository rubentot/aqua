#!/usr/bin/env python3
"""
AquaRegWatch Norway - Norwegian Aquaculture Regulatory Monitor
Main entry point for the monitoring service

Usage:
    python main.py --check          # Run single monitoring cycle
    python main.py --daemon         # Run as continuous daemon
    python main.py --dashboard      # Launch Streamlit dashboard
    python main.py --setup          # Initial setup and configuration
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure directories exist BEFORE setting up logging
dirs = ['data', 'data/logs', 'config']
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/aquaregwatch.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def ensure_directories():
    """Ensure required directories exist"""
    dirs = ['data', 'data/logs', 'config']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def run_setup():
    """Interactive setup wizard"""
    print("\n" + "="*60)
    print("🐟 AquaRegWatch Norway - Setup Wizard")
    print("="*60 + "\n")

    # Check for .env file
    if not Path('.env').exists():
        print("Creating .env file from template...")
        if Path('.env.example').exists():
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file. Please edit it with your API keys.\n")
        else:
            print("❌ .env.example not found. Please create .env manually.\n")

    # Initialize database
    print("Initializing database...")
    from src.models import init_database
    engine, Session = init_database("sqlite:///data/aquaregwatch.db")
    print("✅ Database initialized: data/aquaregwatch.db\n")

    # Initialize sources
    print("Initializing monitored sources...")
    from src.monitor import AquaRegMonitor
    monitor = AquaRegMonitor()
    monitor._init_sources()
    print(f"✅ Initialized {len(monitor.config.get('sources', []))} sources\n")

    # Check API keys
    print("Checking API keys...")
    checks = [
        ("ANTHROPIC_API_KEY", "AI Summarization (Claude)"),
        ("SENDGRID_API_KEY", "Email Delivery"),
        ("SLACK_WEBHOOK_URL", "Slack Notifications"),
    ]

    for key, description in checks:
        value = os.getenv(key)
        status = "✅" if value else "❌"
        print(f"  {status} {description}: {key}")

    print("\n" + "="*60)
    print("Setup complete! Next steps:")
    print("="*60)
    print("""
1. Edit .env file with your API keys
2. Run a test: python main.py --check
3. Start dashboard: python main.py --dashboard
4. For production: python main.py --daemon

See README.md for detailed documentation.
""")


def run_check():
    """Run single monitoring cycle"""
    logger.info("Starting monitoring cycle...")
    from src.monitor import AquaRegMonitor
    monitor = AquaRegMonitor()
    changes = monitor.run_full_cycle()
    print(f"\n✅ Monitoring cycle complete. Detected {len(changes)} changes.")
    return changes


def run_daemon(interval: int = 60):
    """Run as continuous daemon"""
    logger.info(f"Starting daemon with {interval} minute interval...")
    from src.scheduler import MonitorScheduler
    scheduler = MonitorScheduler()
    scheduler.run_daemon(check_interval_minutes=interval)


def run_dashboard():
    """Launch Streamlit dashboard"""
    import subprocess
    print("\n🌐 Launching AquaRegWatch Dashboard...")
    print("Access at: http://localhost:8501\n")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "dashboard.py",
        "--server.port=8501",
        "--server.address=localhost"
    ])


def run_test():
    """Run a test with simulated change"""
    print("\n" + "="*60)
    print("🧪 Running Test with Simulated Change")
    print("="*60 + "\n")

    # Test scraper
    print("1. Testing web scraper...")
    from src.scraper import NorwegianAquacultureScraper
    scraper = NorwegianAquacultureScraper()
    result = scraper.fetch_page("https://www.fiskeridir.no/Akvakultur/Nyheter")
    print(f"   ✅ Fetched {result.word_count} words, hash: {result.content_hash[:16]}...")

    # Test change detector
    print("\n2. Testing change detection...")
    from src.change_detector import ChangeDetector
    detector = ChangeDetector()

    old_text = "Lakselusgrense: 0.5 voksne hunnlus per fisk"
    new_text = "Lakselusgrense: 0.25 voksne hunnlus per fisk (endret fra 0.5)"

    analysis = detector.detect_changes(old_text, new_text, "Test")
    print(f"   ✅ Change detected: {analysis.change_percent}% changed")
    print(f"   Keywords found: {analysis.significant_keywords_found}")

    # Test AI summarization (if API key available)
    print("\n3. Testing AI summarization...")
    if os.getenv("ANTHROPIC_API_KEY"):
        from src.ai_summarizer import AISummarizer
        summarizer = AISummarizer(provider="anthropic")

        summary = summarizer.summarize_change(
            source_name="Test Source",
            source_url="https://example.com",
            category="fish_health",
            old_content=old_text,
            new_content=new_text,
            diff_summary="Lakselusgrense redusert fra 0.5 til 0.25",
            keywords_found=["lakselus"]
        )
        print(f"   ✅ AI Summary generated:")
        print(f"   Title: {summary.title}")
        print(f"   Norwegian: {summary.summary_no[:100]}...")
    else:
        print("   ⚠️ Skipped (ANTHROPIC_API_KEY not set)")

    # Test email formatting
    print("\n4. Testing email formatting...")
    from src.delivery import EmailDelivery
    email = EmailDelivery.__new__(EmailDelivery)
    email.from_name = "Test"

    test_summary = {
        "title": "Test Change",
        "summary_no": "Dette er en test oppsummering",
        "summary_en": "This is a test summary",
        "what_changed": "Test change description",
        "who_affected": ["Lakseoppdrettere"],
        "action_items": [{"action": "Test action", "deadline": "2026-03-01", "priority": "high"}],
        "penalties": ["Test penalty"],
        "category": "fish_health",
        "priority": "high",
        "source_url": "https://example.com"
    }

    html = email._format_alert_html(test_summary)
    print(f"   ✅ Email HTML generated ({len(html)} characters)")

    # Test Slack formatting
    print("\n5. Testing Slack formatting...")
    from src.delivery import SlackDelivery
    slack = SlackDelivery()
    blocks = slack._format_alert_blocks(test_summary)
    print(f"   ✅ Slack blocks generated ({len(blocks)} blocks)")

    print("\n" + "="*60)
    print("✅ All tests completed successfully!")
    print("="*60 + "\n")


def show_stats():
    """Show current statistics"""
    from src.monitor import AquaRegMonitor
    monitor = AquaRegMonitor()
    stats = monitor.get_stats()

    print("\n" + "="*60)
    print("📊 AquaRegWatch Statistics")
    print("="*60)

    for category, values in stats.items():
        print(f"\n{category.upper()}:")
        for key, value in values.items():
            print(f"  {key}: {value}")

    print("\n")


def add_client(name: str, email: str, tier: str = "basic"):
    """Add a new client"""
    from src.monitor import AquaRegMonitor
    monitor = AquaRegMonitor()
    client = monitor.add_client(name=name, email=email, tier=tier)
    print(f"✅ Added client: {client.name} ({client.email}) - Tier: {client.tier}")


def main():
    ensure_directories()

    parser = argparse.ArgumentParser(
        description="AquaRegWatch Norway - Norwegian Aquaculture Regulatory Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --setup              # Initial setup
  python main.py --check              # Run single monitoring cycle
  python main.py --daemon             # Run as continuous service
  python main.py --dashboard          # Launch web dashboard
  python main.py --test               # Run tests with simulated data
  python main.py --add-client "Name" "email@example.com"
        """
    )

    parser.add_argument("--setup", action="store_true", help="Run initial setup wizard")
    parser.add_argument("--check", action="store_true", help="Run single monitoring cycle")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous daemon")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard")
    parser.add_argument("--test", action="store_true", help="Run tests with simulated data")
    parser.add_argument("--stats", action="store_true", help="Show current statistics")
    parser.add_argument("--interval", type=int, default=60, help="Daemon check interval in minutes")
    parser.add_argument("--add-client", nargs=2, metavar=("NAME", "EMAIL"), help="Add a new client")
    parser.add_argument("--tier", default="basic", choices=["basic", "pro", "enterprise"], help="Client tier")

    args = parser.parse_args()

    if args.setup:
        run_setup()
    elif args.check:
        run_check()
    elif args.daemon:
        run_daemon(args.interval)
    elif args.dashboard:
        run_dashboard()
    elif args.test:
        run_test()
    elif args.stats:
        show_stats()
    elif args.add_client:
        name, email = args.add_client
        add_client(name, email, args.tier)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
