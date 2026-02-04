# AquaRegWatch - Deployment Guide

## Quick Start Options

### Option 1: Vercel (Recommended for Landing Page)
**Free tier includes:** Custom domain, SSL, CDN

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy landing page
cd aquaculture-monitor
vercel --prod

# 3. Add custom domain in Vercel dashboard
# Go to: vercel.com/dashboard -> Your project -> Settings -> Domains
```

### Option 2: Netlify (Alternative for Static Sites)
```bash
# 1. Install Netlify CLI
npm install -g netlify-cli

# 2. Deploy
netlify deploy --prod --dir=.

# 3. Add custom domain in Netlify dashboard
```

### Option 3: Railway (For Python Backend)
**Free tier:** $5/month credits, perfect for testing

```bash
# 1. Create railway.json in project root
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py --daemon"
  }
}

# 2. Deploy via Railway CLI or connect GitHub repo
railway login
railway init
railway up
```

---

## Full Production Setup

### 1. Domain Registration
Recommended registrars for .no domains:
- **Domeneshop.no** - Norwegian, good support
- **Namecheap** - International, cheaper

Suggested domains:
- aquaregwatch.no
- regwatch.no
- akvaregulering.no

### 2. Email Setup (SendGrid)
```bash
# 1. Sign up at sendgrid.com (free tier: 100 emails/day)

# 2. Create API key:
# Settings -> API Keys -> Create API Key

# 3. Add to .env:
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
EMAIL_FROM=varsler@aquaregwatch.no

# 4. Verify sender domain in SendGrid dashboard
```

### 3. Database (Supabase - Free PostgreSQL)
```bash
# 1. Sign up at supabase.com

# 2. Create new project

# 3. Get connection string from:
# Settings -> Database -> Connection string

# 4. Update .env:
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

### 4. Scheduled Jobs (GitHub Actions)
Create `.github/workflows/monitor.yml`:
```yaml
name: AquaRegWatch Monitor

on:
  schedule:
    # Run every hour
    - cron: '0 * * * *'
  workflow_dispatch:

jobs:
  check-regulations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run monitor
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python main.py --check
```

---

## Architecture Overview

```
+------------------+     +------------------+     +------------------+
|   Landing Page   |     |   Dashboard      |     |   Monitor        |
|   (Vercel)       |     |   (Streamlit)    |     |   (GitHub Actions)|
+------------------+     +------------------+     +------------------+
                              |                         |
                              v                         v
                         +------------------+     +------------------+
                         |   Database       |<--->|   AI Summarizer  |
                         |   (Supabase)     |     |   (Claude API)   |
                         +------------------+     +------------------+
                                                        |
                                                        v
                         +------------------+     +------------------+
                         |   Email          |     |   Slack          |
                         |   (SendGrid)     |     |   (Webhook)      |
                         +------------------+     +------------------+
```

---

## Cost Estimate (Monthly)

### Minimum Viable Product (Free/Almost Free)
| Service | Cost | Notes |
|---------|------|-------|
| Vercel | $0 | Landing page hosting |
| Supabase | $0 | Free tier PostgreSQL |
| SendGrid | $0 | 100 emails/day free |
| GitHub Actions | $0 | 2000 min/month free |
| Claude API | ~$5-20 | Pay per use |
| **Total** | **~$5-20/month** | |

### Production (10+ customers)
| Service | Cost | Notes |
|---------|------|-------|
| Vercel Pro | $20 | More bandwidth |
| Supabase Pro | $25 | More storage/compute |
| SendGrid Essentials | $20 | 50k emails/month |
| Railway | $20 | Always-on backend |
| Claude API | ~$50-100 | Depends on usage |
| Domain (.no) | ~$15/year | |
| **Total** | **~$135-185/month** | |

---

## Security Checklist

- [ ] Store API keys in environment variables, never in code
- [ ] Use HTTPS everywhere (Vercel/Netlify handle this)
- [ ] Set up rate limiting on API endpoints
- [ ] Enable 2FA on all service accounts
- [ ] Regular database backups (Supabase handles this)
- [ ] Monitor for unusual activity

---

## Quick Deploy Commands

```bash
# Clone and setup
git clone https://github.com/yourusername/aquaculture-monitor
cd aquaculture-monitor
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Test locally
python main.py --setup
python main.py --check

# Deploy landing page to Vercel
vercel --prod

# Run dashboard locally
streamlit run dashboard.py
```

---

## Monitoring & Alerts

### Uptime Monitoring (Free options)
- **UptimeRobot** - 50 monitors free
- **Freshping** - 50 monitors free
- **Better Uptime** - 10 monitors free

### Error Tracking
- **Sentry** - Free tier available
- Add to Python code:
```python
import sentry_sdk
sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
```

---

## Support Resources

- **Vercel Docs:** vercel.com/docs
- **Supabase Docs:** supabase.com/docs
- **SendGrid Docs:** docs.sendgrid.com
- **Anthropic Docs:** docs.anthropic.com

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
```

### SendGrid emails not sending
1. Check API key is correct
2. Verify sender domain in SendGrid dashboard
3. Check spam folder

### Database connection issues
1. Check DATABASE_URL format
2. Ensure IP is whitelisted in Supabase
3. Check SSL settings

### Claude API errors
1. Check API key is valid
2. Check rate limits
3. Ensure sufficient credits
