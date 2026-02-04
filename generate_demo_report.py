"""
Generate Demo Reports for Sales Presentations
Creates realistic sample alerts to show prospects what they'll receive
"""
import os
from datetime import datetime, timedelta
from pathlib import Path


def generate_sample_alerts():
    """Generate realistic sample regulatory alerts"""
    return [
        {
            "id": 1,
            "source": "Mattilsynet",
            "url": "https://www.mattilsynet.no/fisk_og_akvakultur/akvakultur/lakselus/",
            "detected": datetime.now() - timedelta(hours=2),
            "priority": "KRITISK",
            "title": "Nye lakselusgrenser fra 1. mars 2026",
            "summary_no": """Mattilsynet har vedtatt strengere grenser for lakselus med umiddelbar virkning for
produksjonsområde 3, 4 og 5. Grensen reduseres fra 0,5 til 0,25 voksne hunnlus per fisk.

Anlegg som overskrider grensen vil få pålegg om behandling innen 14 dager.
Ved gjentatte brudd kan det ilegges tvangsmulkt på opptil 1 million kroner.""",
            "summary_en": """The Norwegian Food Safety Authority has adopted stricter sea lice limits with immediate
effect for Production Areas 3, 4, and 5. The threshold is reduced from 0.5 to 0.25 adult female lice per fish.

Facilities exceeding the limit will be ordered to treat within 14 days.
Repeated violations may result in coercive fines up to 1 million NOK.""",
            "affected": ["Lakseoppdrettere i PO3, PO4, PO5", "Regnbueørretoppdrettere", "Settefiskanlegg med sjøvannsfase"],
            "action_items": [
                {"action": "Gjennomfør ekstra lusetelling denne uken", "deadline": "Umiddelbart", "priority": "Høy"},
                {"action": "Vurder forebyggende behandling", "deadline": "Innen 7 dager", "priority": "Høy"},
                {"action": "Oppdater interne rutiner for luseovervåking", "deadline": "1. mars 2026", "priority": "Medium"},
                {"action": "Søk dispensasjon hvis nødvendig", "deadline": "15. februar 2026", "priority": "Høy"},
            ],
            "potential_fines": "Opptil 1 000 000 NOK ved gjentatte brudd",
            "change_percent": 23.4,
        },
        {
            "id": 2,
            "source": "Fiskeridirektoratet",
            "url": "https://www.fiskeridir.no/Akvakultur/Registre-og-skjema/MTB",
            "detected": datetime.now() - timedelta(hours=8),
            "priority": "HØY",
            "title": "Trafikklyssystemet: PO4 nedgradert til gult",
            "summary_no": """Produksjonsområde 4 (Nordhordland til Stadt) er nedgradert fra grønt til gult basert på
siste vurdering av miljøpåvirkning. Dette betyr at kapasiteten fryses på nåværende nivå.

Oppdrettere i området kan ikke lenger søke om kapasitetsøkning før neste vurdering i 2027.""",
            "summary_en": """Production Area 4 (Nordhordland to Stadt) has been downgraded from green to yellow based on
the latest environmental impact assessment. This means capacity is frozen at current levels.

Farmers in the area can no longer apply for capacity increases until the next assessment in 2027.""",
            "affected": ["Alle oppdrettere i PO4", "Nye søkere om lokaliteter i området"],
            "action_items": [
                {"action": "Revider produksjonsplan for 2026", "deadline": "Innen 30 dager", "priority": "Høy"},
                {"action": "Vurder tiltak for å bedre miljøstatus", "deadline": "Løpende", "priority": "Medium"},
                {"action": "Oppdater investorrapporter", "deadline": "Neste kvartal", "priority": "Medium"},
            ],
            "potential_fines": "Ingen direkte, men tapt vekstmulighet",
            "change_percent": 15.8,
        },
        {
            "id": 3,
            "source": "Miljødirektoratet",
            "url": "https://www.miljodirektoratet.no/tema/akvakultur/",
            "detected": datetime.now() - timedelta(days=1),
            "priority": "MEDIUM",
            "title": "Nye krav til utslippsrapportering fra 2027",
            "summary_no": """Miljødirektoratet innfører nye krav til rapportering av organisk belastning og
næringssaltutslipp fra oppdrettsanlegg. Digital innrapportering blir obligatorisk fra 1. januar 2027.

Alle anlegg må installere godkjent måleutstyr og rapportere månedlig via Altinn.""",
            "summary_en": """The Norwegian Environment Agency introduces new requirements for reporting organic load and
nutrient emissions from aquaculture facilities. Digital reporting becomes mandatory from January 1, 2027.

All facilities must install approved measuring equipment and report monthly via Altinn.""",
            "affected": ["Alle oppdrettsanlegg med tillatelse", "Slakterier", "Settefiskanlegg"],
            "action_items": [
                {"action": "Kartlegg nåværende måleutstyr", "deadline": "Q2 2026", "priority": "Medium"},
                {"action": "Budsjetter for nytt utstyr hvis nødvendig", "deadline": "Q3 2026", "priority": "Medium"},
                {"action": "Etabler rutiner for månedlig rapportering", "deadline": "Q4 2026", "priority": "Høy"},
            ],
            "potential_fines": "Ikke spesifisert, men manglende rapportering kan føre til inndragning av tillatelse",
            "change_percent": 8.2,
        },
        {
            "id": 4,
            "source": "Lovdata",
            "url": "https://lovdata.no/dokument/SF/forskrift/2024-xx-xx",
            "detected": datetime.now() - timedelta(days=2),
            "priority": "MEDIUM",
            "title": "Endring i akvakulturdriftsforskriften § 47",
            "summary_no": """Ny formulering av krav til rømmingssikring. Alle anlegg må nå dokumentere
årlig inspeksjon av not og fortøyning utført av sertifisert inspektør.

Dokumentasjon må være tilgjengelig ved tilsyn.""",
            "summary_en": """New wording of escape prevention requirements. All facilities must now document
annual inspection of nets and moorings performed by a certified inspector.

Documentation must be available during inspections.""",
            "affected": ["Alle sjøbaserte oppdrettsanlegg"],
            "action_items": [
                {"action": "Bestill årlig inspeksjon hos sertifisert leverandør", "deadline": "Innen 6 måneder", "priority": "Høy"},
                {"action": "Oppdater dokumentasjonssystem", "deadline": "Løpende", "priority": "Medium"},
            ],
            "potential_fines": "Tvangsmulkt ved manglende dokumentasjon",
            "change_percent": 5.1,
        },
    ]


def generate_html_report(alerts, client_name="Demo Kunde"):
    """Generate a professional HTML report"""

    priority_colors = {
        "KRITISK": "#ef4444",
        "HØY": "#f59e0b",
        "MEDIUM": "#eab308",
        "LAV": "#10b981"
    }

    alerts_html = ""
    for alert in alerts:
        color = priority_colors.get(alert["priority"], "#94a3b8")

        action_items_html = ""
        for item in alert["action_items"]:
            action_items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item['action']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item['deadline']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item['priority']}</td>
            </tr>
            """

        affected_html = "".join(f"<li>{a}</li>" for a in alert["affected"])

        alerts_html += f"""
        <div style="border: 1px solid #ddd; border-left: 5px solid {color}; border-radius: 8px; padding: 24px; margin: 20px 0; background: white;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                <div>
                    <span style="background: {color}20; color: {color}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">{alert['priority']}</span>
                    <h2 style="margin: 12px 0 4px 0; color: #1a1a1a;">{alert['title']}</h2>
                    <p style="color: #666; font-size: 14px; margin: 0;">
                        {alert['source']} • {alert['detected'].strftime('%d.%m.%Y kl. %H:%M')} • {alert['change_percent']}% endret
                    </p>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <h4 style="margin: 0 0 8px 0; color: #c0392b;">🇳🇴 Norsk</h4>
                    <p style="margin: 0; color: #333; line-height: 1.6;">{alert['summary_no']}</p>
                </div>
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <h4 style="margin: 0 0 8px 0; color: #27ae60;">🇬🇧 English</h4>
                    <p style="margin: 0; color: #333; line-height: 1.6;">{alert['summary_en']}</p>
                </div>
            </div>

            <div style="margin: 20px 0;">
                <h4 style="margin: 0 0 8px 0;">👥 Hvem påvirkes</h4>
                <ul style="margin: 0; padding-left: 20px; color: #555;">
                    {affected_html}
                </ul>
            </div>

            <div style="margin: 20px 0;">
                <h4 style="margin: 0 0 12px 0;">🎯 Handlingspunkter</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #f0f0f0;">
                            <th style="padding: 10px; text-align: left;">Handling</th>
                            <th style="padding: 10px; text-align: left; width: 150px;">Frist</th>
                            <th style="padding: 10px; text-align: left; width: 100px;">Prioritet</th>
                        </tr>
                    </thead>
                    <tbody>
                        {action_items_html}
                    </tbody>
                </table>
            </div>

            <div style="background: #fff3cd; padding: 12px 16px; border-radius: 6px; margin-top: 16px;">
                <strong>⚠️ Potensielle sanksjoner:</strong> {alert['potential_fines']}
            </div>

            <p style="margin: 16px 0 0 0; font-size: 13px;">
                <a href="{alert['url']}" style="color: #0066cc;">Se original kilde →</a>
            </p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaRegWatch - Reguleringsrapport</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
        }}
    </style>
</head>
<body>
    <div style="background: linear-gradient(135deg, #1a5276, #2980b9); color: white; padding: 40px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
        <h1 style="margin: 0; font-size: 32px;">🐟 AquaRegWatch Norway</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Daglig reguleringsrapport for {client_name}</p>
        <p style="margin: 5px 0 0 0; opacity: 0.7; font-size: 14px;">{datetime.now().strftime('%d. %B %Y')}</p>
    </div>

    <div style="background: white; padding: 24px; border-radius: 8px; margin-bottom: 20px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; text-align: center;">
        <div>
            <div style="font-size: 32px; font-weight: bold; color: #e74c3c;">{len([a for a in alerts if a['priority'] == 'KRITISK'])}</div>
            <div style="color: #666; font-size: 14px;">Kritiske</div>
        </div>
        <div>
            <div style="font-size: 32px; font-weight: bold; color: #f39c12;">{len([a for a in alerts if a['priority'] == 'HØY'])}</div>
            <div style="color: #666; font-size: 14px;">Høy prioritet</div>
        </div>
        <div>
            <div style="font-size: 32px; font-weight: bold; color: #f1c40f;">{len([a for a in alerts if a['priority'] == 'MEDIUM'])}</div>
            <div style="color: #666; font-size: 14px;">Medium</div>
        </div>
        <div>
            <div style="font-size: 32px; font-weight: bold; color: #2ecc71;">{len(alerts)}</div>
            <div style="color: #666; font-size: 14px;">Totalt</div>
        </div>
    </div>

    {alerts_html}

    <div style="background: white; padding: 24px; border-radius: 8px; margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
        <p style="margin: 0;">Denne rapporten er automatisk generert av AquaRegWatch Norway</p>
        <p style="margin: 8px 0 0 0;">
            Spørsmål? Kontakt oss på <a href="mailto:support@aquaregwatch.no">support@aquaregwatch.no</a>
        </p>
        <p style="margin: 16px 0 0 0; font-size: 12px; color: #999;">
            © 2026 AquaRegWatch Norway. Alle rettigheter reservert.
        </p>
    </div>
</body>
</html>"""

    return html


def generate_slack_message(alerts):
    """Generate Slack-formatted message"""
    message = "*🐟 AquaRegWatch Daglig Oversikt*\n"
    message += f"_{datetime.now().strftime('%d. %B %Y')}_\n\n"

    critical = len([a for a in alerts if a['priority'] == 'KRITISK'])
    high = len([a for a in alerts if a['priority'] == 'HØY'])

    if critical > 0:
        message += f"🚨 *{critical} kritiske endringer krever umiddelbar oppmerksomhet*\n\n"

    for alert in alerts:
        emoji = {"KRITISK": "🚨", "HØY": "🔴", "MEDIUM": "🟡", "LAV": "🟢"}.get(alert["priority"], "📋")
        message += f"{emoji} *{alert['title']}*\n"
        message += f"_{alert['source']} • {alert['detected'].strftime('%H:%M')}_\n"
        message += f"{alert['summary_no'][:200]}...\n\n"

    message += "_Se full rapport i dashboardet eller e-post_"

    return message


def main():
    """Generate demo reports"""
    print("\n" + "="*60)
    print("AquaRegWatch - Generating Demo Reports")
    print("="*60)

    # Ensure output directory exists
    output_dir = Path("demo_reports")
    output_dir.mkdir(exist_ok=True)

    # Generate alerts
    alerts = generate_sample_alerts()

    # Generate HTML report
    html_report = generate_html_report(alerts, "Mowi ASA")
    html_path = output_dir / f"demo_report_{datetime.now().strftime('%Y%m%d')}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"\n[OK] HTML Report: {html_path}")

    # Generate Slack message
    slack_message = generate_slack_message(alerts)
    slack_path = output_dir / "demo_slack_message.txt"
    with open(slack_path, "w", encoding="utf-8") as f:
        f.write(slack_message)
    print(f"[OK] Slack Message: {slack_path}")

    # Open HTML in browser
    print(f"\nOpening report in browser...")
    os.startfile(str(html_path.absolute()))

    print("\n" + "="*60)
    print("Use these for sales demos and cold calls!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
