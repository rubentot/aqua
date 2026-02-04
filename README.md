# 🐟 AquaRegWatch Norway

**Norwegian Aquaculture Regulatory Monitoring Service**

Automated monitoring of Norwegian government websites for changes in aquaculture regulations, with AI-powered summarization and multi-channel delivery.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Quick Start](#quick-start)
4. [Setup Guide](#setup-guide)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Deployment](#deployment)
8. [API Reference](#api-reference)
9. [Pricing Tiers](#pricing-tiers)
10. [Testing](#testing)
11. [Legal & Compliance](#legal--compliance)

---

## Overview

AquaRegWatch Norway monitors Norwegian government websites for regulatory changes affecting the aquaculture industry, including:

- **Fiskeridirektoratet** (Norwegian Directorate of Fisheries)
- **Mattilsynet** (Norwegian Food Safety Authority)
- **Miljødirektoratet** (Norwegian Environment Agency)
- **Lovdata** (Norwegian Law Database)
- **Regjeringen** (Government of Norway)
- **EUR-Lex** (EU regulations via EEA)

Changes are detected, analyzed with AI, and delivered via email or Slack.

---

## Features

### 🔍 Monitoring
- Hourly/daily checks of 10+ Norwegian government sources
- Intelligent change detection (ignores timestamps, formatting)
- Keyword-based significance filtering
- Historical change tracking

### 🤖 AI Analysis
- Norwegian & English summaries via Claude/OpenAI
- Impact analysis for different stakeholders
- Automatic action item extraction
- Deadline identification

### 📬 Delivery
- Email digests (SendGrid/Gmail)
- Real-time Slack alerts
- Streamlit dashboard
- PDF reports (Enterprise)

### 👥 Multi-tenant
- Client management with subscription tiers
- Per-client filtering preferences
- Usage tracking and analytics

---

## Quick Start

```bash
# 1. Clone and enter directory
cd aquaculture-monitor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run setup
python main.py --setup

# 6. Run first check
python main.py --check

# 7. Launch dashboard
python main.py --dashboard
```

---

## Setup Guide

### Step 1: Prerequisites

- Python 3.10+
- API keys (at least one):
  - Anthropic Claude API key (recommended)
  - OpenAI API key (alternative)
- Email provider:
  - SendGrid API key (recommended)
  - Gmail with App Password (alternative)
- Slack webhook URL (optional)

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Copy `.env.example` to `.env` and fill in your keys:

```env
# AI (required - choose one)
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-your-key-here

# Email (required for notifications)
SENDGRID_API_KEY=SG.your-sendgrid-key
EMAIL_FROM_ADDRESS=alerts@yourdomain.com

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Step 4: Initialize Database

```bash
python main.py --setup
```

### Step 5: Add Your First Client

```bash
python main.py --add-client "Your Name" "your@email.com" --tier pro
```

### Step 6: Run Initial Check

```bash
python main.py --check
```

### Step 7: Start the Service

**Option A: Daemon mode (recommended for VMs)**
```bash
python main.py --daemon --interval 60
```

**Option B: Cron job**
```bash
# Generate cron entries
python -m src.scheduler --generate-cron
```

**Option C: GitHub Actions**
```bash
# Generate workflow
python -m src.scheduler --generate-github > .github/workflows/monitor.yml
```

### Step 8: Launch Dashboard

```bash
python main.py --dashboard
# Access at http://localhost:8501
```

---

## Configuration

### config/settings.yaml

Main configuration file for sources, monitoring settings, and delivery options.

Key sections:

```yaml
# Sources to monitor
sources:
  - id: "fiskeridir_main"
    name: "Fiskeridirektoratet - Akvakultur"
    url: "https://www.fiskeridir.no/Akvakultur"
    category: "licenses_permits"
    check_interval_hours: 1
    priority: "high"

# AI settings
ai:
  provider: "anthropic"  # or "openai"
  model: "claude-sonnet-4-20250514"

# Delivery settings
delivery:
  email:
    enabled: true
    provider: "sendgrid"
  slack:
    enabled: true
```

### Adding Custom Sources

Add new sources to `config/settings.yaml`:

```yaml
sources:
  - id: "custom_source"
    name: "My Custom Source"
    url: "https://example.com/regulations"
    category: "custom"
    check_interval_hours: 4
    priority: "medium"
    selectors:
      content: "main, .content, article"
```

---

## Usage

### Command Line Interface

```bash
# Run single monitoring cycle
python main.py --check

# Run as daemon
python main.py --daemon --interval 60

# Launch dashboard
python main.py --dashboard

# Show statistics
python main.py --stats

# Add client
python main.py --add-client "Name" "email@example.com" --tier pro

# Run tests
python main.py --test
```

### Scheduler Commands

```bash
# Generate cron entries
python -m src.scheduler --generate-cron

# Generate GitHub Actions workflow
python -m src.scheduler --generate-github

# Generate Docker Compose
python -m src.scheduler --generate-docker
```

### Python API

```python
from src.monitor import AquaRegMonitor

# Initialize
monitor = AquaRegMonitor()

# Run monitoring cycle
changes = monitor.run_full_cycle()

# Add client
client = monitor.add_client(
    name="Salmon Farm AS",
    email="compliance@salmonfarm.no",
    tier="pro"
)

# Get statistics
stats = monitor.get_stats()
```

---

## Deployment

### Docker

```bash
# Build image
docker build -t aquaregwatch .

# Run with environment variables
docker run -d \
  --name aquaregwatch \
  -e ANTHROPIC_API_KEY=your-key \
  -e SENDGRID_API_KEY=your-key \
  -v $(pwd)/data:/app/data \
  aquaregwatch
```

### Docker Compose

```bash
# Generate docker-compose.yml
python -m src.scheduler --generate-docker > docker-compose.yml

# Start services
docker-compose up -d
```

### GitHub Actions (Serverless)

1. Generate workflow:
   ```bash
   python -m src.scheduler --generate-github > .github/workflows/monitor.yml
   ```

2. Add secrets to repository:
   - `ANTHROPIC_API_KEY`
   - `SENDGRID_API_KEY`
   - `SLACK_WEBHOOK_URL`

3. Push to GitHub

### Visualping.io (Hybrid Approach)

For additional reliability, use Visualping.io alongside the Python monitoring:

1. Create account at https://visualping.io/
2. Add each URL with these settings:
   - Check frequency: Hourly
   - Comparison: Text + Visual
   - Sensitivity: Medium-High
3. Configure webhook to your server

---

## Sample Output

### Email Alert

```
🐟 AquaRegWatch: Ny lakselusgrense fra mars 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🇳🇴 NORSK OPPSUMMERING
Mattilsynet har vedtatt nye, strengere grenser for lakselus.
Grensen reduseres fra 0.5 til 0.25 voksne hunnlus per fisk,
med virkning fra 1. mars 2026.

🇬🇧 ENGLISH SUMMARY
The Norwegian Food Safety Authority has adopted stricter
sea lice limits. The threshold is reduced from 0.5 to 0.25
adult female lice per fish, effective March 1, 2026.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 HVEM PÅVIRKES / WHO IS AFFECTED
• Lakseoppdrettere (salmon farmers)
• Regnbueørretoppdrettere (rainbow trout farmers)
• Oppdrettere i røde soner (farmers in red zones)

🎯 HANDLINGSPUNKTER / ACTION ITEMS
🔴 Oppdater lusetellingsrutiner
   Frist: 15. februar 2026

🔴 Søk dispensasjon hvis nødvendig
   Frist: 15. mars 2026

🟡 Vurder behandlingskapasitet

⚠️ POTENSIELLE SANKSJONER
• Bot opptil 1 million NOK
• Mulig produksjonsstopp

📅 VIKTIGE FRISTER
• 2026-03-01: Ny forskrift trer i kraft
• 2026-03-15: Frist for dispensasjonssøknad

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Kilde: https://www.mattilsynet.no/fisk/lakselus
Kategori: fish_health
Prioritet: CRITICAL
```

### Slack Message

```
🚨 Ny lakselusgrense fra mars 2026

🇳🇴 Norsk:
Mattilsynet har vedtatt nye, strengere grenser for lakselus.
Grensen reduseres fra 0.5 til 0.25 voksne hunnlus per fisk.

🇬🇧 English:
The Norwegian Food Safety Authority has adopted stricter
sea lice limits, reducing from 0.5 to 0.25 per fish.

👥 Hvem påvirkes:
Lakseoppdrettere, Regnbueørretoppdrettere, Oppdrettere i røde soner

🎯 Handlingspunkter:
• 🔴 Oppdater lusetellingsrutiner (Frist: 2026-02-15)
• 🔴 Søk dispensasjon hvis nødvendig (Frist: 2026-03-15)

⚠️ Sanksjoner:
• Bot opptil 1 million NOK

📍 Kilde: mattilsynet.no | Kategori: fish_health | Prioritet: CRITICAL
```

---

## Pricing Tiers

| Feature | Basic (5000 NOK/mo) | Pro (15000 NOK/mo) | Enterprise (50000 NOK/mo) |
|---------|--------------------|--------------------|---------------------------|
| Email Digests | Daily | Hourly | Real-time |
| Slack Integration | ❌ | ✅ | ✅ |
| Dashboard Access | ❌ | ✅ | ✅ |
| AI Summaries | Basic | Detailed | Custom |
| Action Items | ❌ | ✅ | ✅ |
| Impact Analysis | ❌ | ✅ | ✅ |
| PDF Reports | ❌ | ❌ | ✅ |
| Custom Sources | ❌ | ❌ | ✅ |
| API Access | ❌ | ❌ | ✅ |
| Users | 2 | 10 | Unlimited |
| Support | Email | Priority | Dedicated |

---

## Testing

### Run All Tests

```bash
python main.py --test
```

### Simulate a Change

```python
from src.change_detector import ChangeDetector

detector = ChangeDetector()

old = "Lakselusgrense: 0.5 per fisk"
new = "Lakselusgrense: 0.25 per fisk (NY FORSKRIFT)"

result = detector.detect_changes(old, new, "Test")
print(f"Change detected: {result.has_changes}")
print(f"Keywords: {result.significant_keywords_found}")
```

### Test Email Delivery

```bash
# Set test mode in .env
TEST_MODE=true

# Run with test email
python -c "
from src.delivery import EmailDelivery
email = EmailDelivery()
result = email.send_alert('test@example.com', {'title': 'Test', 'summary_no': 'Test alert'})
print(result)
"
```

---

## Legal & Compliance

### Public Data

All monitored websites are **public government sources**. Norwegian law (offentlighetsloven) ensures public access to government information.

### Terms of Service Compliance

- Rate limiting: Max 10 requests/minute per source
- User-Agent: Identifies as monitoring service
- No personal data scraped
- Only text content analyzed

### GDPR

- Client data stored locally in SQLite
- Email addresses encrypted at rest
- No data shared with third parties
- Deletion on request

### Disclaimer

This service provides informational summaries only. Always verify regulatory requirements with official sources. AquaRegWatch is not liable for decisions made based on automated summaries.

---

## Support

- **Documentation**: This README
- **Issues**: GitHub Issues
- **Email**: support@aquaregwatch.no

---

## License

Proprietary - All rights reserved

---

*Built with ❤️ for Norwegian aquaculture*
