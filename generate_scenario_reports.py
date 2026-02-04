"""
Additional Demo Scenarios for Sales Presentations
Creates various crisis/regulatory scenarios to show AquaRegWatch value
"""
import os
from datetime import datetime, timedelta
from pathlib import Path


def generate_ila_outbreak_scenario():
    """ILA (Infectious Salmon Anemia) outbreak scenario"""
    return {
        "scenario_name": "ILA Outbreak - Crisis Response",
        "alerts": [
            {
                "id": 1,
                "source": "Mattilsynet",
                "url": "https://www.mattilsynet.no/fisk_og_akvakultur/fiskehelse/fiskesykdommer/ila/",
                "detected": datetime.now() - timedelta(hours=1),
                "priority": "KRITISK",
                "title": "ILA pavist i Hardanger - Bekjempelsessone opprettet",
                "summary_no": """Mattilsynet har pavist infeksios lakseanemi (ILA) ved et oppdrettsanlegg i Hardanger.
Det er opprettet bekjempelsessone med radius 10 km og overvakingssone med radius 20 km.

Alle anlegg i sonene ma folge strenge restriksjoner pa flytting av fisk og utstyr.
Sonen gjelder til 90 dager etter slakting av siste fisk ved det infiserte anlegget.""",
                "summary_en": """The Norwegian Food Safety Authority has confirmed Infectious Salmon Anemia (ILA) at a farm in Hardanger.
A control zone with 10 km radius and surveillance zone with 20 km radius has been established.

All facilities in the zones must follow strict restrictions on fish and equipment movement.
The zone applies until 90 days after slaughter of the last fish at the infected facility.""",
                "affected": ["Alle anlegg innen 10 km radius", "Alle anlegg innen 20 km radius (overvaking)", "Bronnbatoperatorer", "Slakterier i omradet"],
                "action_items": [
                    {"action": "Sjekk om ditt anlegg er i sonen", "deadline": "Umiddelbart", "priority": "Kritisk"},
                    {"action": "Stopp all flytting av fisk", "deadline": "Umiddelbart", "priority": "Kritisk"},
                    {"action": "Rapporter all fiskehelsestatus til Mattilsynet", "deadline": "Innen 24 timer", "priority": "Hoy"},
                    {"action": "Implementer forsterket smittevern", "deadline": "Umiddelbart", "priority": "Kritisk"},
                    {"action": "Varsle forsikringsselskap", "deadline": "Innen 48 timer", "priority": "Hoy"},
                ],
                "potential_fines": "Overtredelse av soneregler: Opptil 15G (ca. 1.8 MNOK)",
                "change_percent": 100.0,
            },
            {
                "id": 2,
                "source": "Fiskeridirektoratet",
                "url": "https://www.fiskeridir.no/Akvakultur/Drift-og-tilsyn/Sykdom",
                "detected": datetime.now() - timedelta(hours=2),
                "priority": "HOY",
                "title": "Oppdaterte koordinater for ILA-soner",
                "summary_no": """Fiskeridirektoratet har publisert oppdaterte koordinater for bekjempelsessone og overvakingssone.
Se kartlaget i AkvaStat for a sjekke om ditt anlegg er rammet.""",
                "summary_en": """The Directorate of Fisheries has published updated coordinates for control and surveillance zones.
Check the map layer in AkvaStat to see if your facility is affected.""",
                "affected": ["Alle oppdrettere i Hardanger-regionen"],
                "action_items": [
                    {"action": "Sjekk koordinater mot dine lokaliteter", "deadline": "Umiddelbart", "priority": "Hoy"},
                    {"action": "Last ned oppdatert sonekart", "deadline": "I dag", "priority": "Medium"},
                ],
                "potential_fines": "N/A",
                "change_percent": 45.2,
            },
        ],
    }


def generate_mtb_changes_scenario():
    """MTB (Maximum Tillatt Biomasse) changes scenario"""
    return {
        "scenario_name": "MTB Regulation Changes",
        "alerts": [
            {
                "id": 1,
                "source": "Fiskeridirektoratet",
                "url": "https://www.fiskeridir.no/Akvakultur/Tildeling-og-tillatelser/Kapasitetsokning-i-lakse-og-orretoppdrett",
                "detected": datetime.now() - timedelta(hours=4),
                "priority": "HOY",
                "title": "Kapasitetsjustering 2026 - Nye MTB-regler",
                "summary_no": """Fiskeridirektoratet kunngjor nye regler for kapasitetsjustering i lakse- og orretoppdrett.
Fra 1. juli 2026 endres beregningsmetoden for MTB.

Viktige endringer:
- Ny beregninsformel for lokalitets-MTB
- Endret vekting av miljoindikatorer
- Strengere krav til dokumentasjon ved soknad om okning""",
                "summary_en": """The Directorate of Fisheries announces new rules for capacity adjustment in salmon and trout farming.
From July 1, 2026, the calculation method for MTB changes.

Key changes:
- New calculation formula for site MTB
- Changed weighting of environmental indicators
- Stricter documentation requirements for increase applications""",
                "affected": ["Alle lakse- og orretoppdrettere", "Tillatelsesinnehavere som planlegger kapasitetsokning"],
                "action_items": [
                    {"action": "Les fullstendig forskriftstekst", "deadline": "Denne uken", "priority": "Hoy"},
                    {"action": "Beregn konsekvens for dine lokaliteter", "deadline": "Innen 30 dager", "priority": "Hoy"},
                    {"action": "Oppdater produksjonsplaner", "deadline": "For 1. juli 2026", "priority": "Medium"},
                    {"action": "Vurder soknad for kapasitetsokning", "deadline": "Innen april 2026", "priority": "Medium"},
                ],
                "potential_fines": "Overskridelse av MTB: Tvangsmulkt og reduksjon i tillatelse",
                "change_percent": 28.5,
            },
        ],
    }


def generate_eu_regulation_scenario():
    """EU regulation affecting Norwegian aquaculture"""
    return {
        "scenario_name": "EU Regulation Impact",
        "alerts": [
            {
                "id": 1,
                "source": "EUR-Lex / Regjeringen",
                "url": "https://eur-lex.europa.eu/",
                "detected": datetime.now() - timedelta(days=1),
                "priority": "MEDIUM",
                "title": "Ny EU-forordning om sporbarhet i sjomat",
                "summary_no": """EU har vedtatt ny forordning om sporbarhet i sjomatkjeden som vil bli implementert i EOS-avtalen.
Forordningen krever digitale sporbarhetssystemer fra fangst/oppdrett til sluttkunde.

Norge ma implementere forordningen innen 18 maneder.
Dette vil kreve oppgradering av eksisterende sporbarhetssystemer.""",
                "summary_en": """The EU has adopted a new regulation on traceability in the seafood chain that will be implemented in the EEA agreement.
The regulation requires digital traceability systems from catch/farming to end consumer.

Norway must implement the regulation within 18 months.
This will require upgrading existing traceability systems.""",
                "affected": ["Alle sjomatprodusenter", "Eksportorer til EU", "Foredlingsbedrifter"],
                "action_items": [
                    {"action": "Kartlegg navarende sporbarhetssystem", "deadline": "Q2 2026", "priority": "Medium"},
                    {"action": "Identifiser gap mot nye krav", "deadline": "Q3 2026", "priority": "Medium"},
                    {"action": "Budsjetter for systemoppgradering", "deadline": "Q4 2026", "priority": "Hoy"},
                ],
                "potential_fines": "Eksportforbud ved manglende compliance",
                "change_percent": 12.3,
            },
        ],
    }


def generate_html_scenario_report(scenario, client_name="Demo Kunde"):
    """Generate HTML report for a specific scenario"""
    alerts = scenario["alerts"]
    scenario_name = scenario["scenario_name"]

    priority_colors = {
        "KRITISK": "#ef4444",
        "HOY": "#f59e0b",
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
                        {alert['source']} - Oppdaget: {alert['detected'].strftime('%d.%m.%Y kl. %H:%M')} - {alert['change_percent']}% endret
                    </p>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <h4 style="margin: 0 0 8px 0; color: #c0392b;">Norsk</h4>
                    <p style="margin: 0; color: #333; line-height: 1.6;">{alert['summary_no']}</p>
                </div>
                <div style="background: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <h4 style="margin: 0 0 8px 0; color: #27ae60;">English</h4>
                    <p style="margin: 0; color: #333; line-height: 1.6;">{alert['summary_en']}</p>
                </div>
            </div>

            <div style="margin: 20px 0;">
                <h4 style="margin: 0 0 8px 0;">Hvem pavirkes</h4>
                <ul style="margin: 0; padding-left: 20px; color: #555;">
                    {affected_html}
                </ul>
            </div>

            <div style="margin: 20px 0;">
                <h4 style="margin: 0 0 12px 0;">Handlingspunkter</h4>
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
                <strong>Potensielle sanksjoner:</strong> {alert['potential_fines']}
            </div>

            <p style="margin: 16px 0 0 0; font-size: 13px;">
                <a href="{alert['url']}" style="color: #0066cc;">Se original kilde</a>
            </p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AquaRegWatch - {scenario_name}</title>
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
    <div style="background: linear-gradient(135deg, #c0392b, #e74c3c); color: white; padding: 40px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
        <h1 style="margin: 0; font-size: 32px;">AquaRegWatch Norway</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 20px;">{scenario_name}</p>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Demo-rapport for {client_name}</p>
        <p style="margin: 5px 0 0 0; opacity: 0.7; font-size: 14px;">{datetime.now().strftime('%d. %B %Y')}</p>
    </div>

    <div style="background: #fee2e2; border: 2px solid #ef4444; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h3 style="margin: 0 0 10px 0; color: #dc2626;">KRISESCENARIO - Demonstrasjon</h3>
        <p style="margin: 0; color: #7f1d1d;">
            Denne rapporten viser hvordan AquaRegWatch varsler deg ved kritiske hendelser.
            Varsler sendes via e-post og Slack innen minutter etter at endringen oppdages.
        </p>
    </div>

    {alerts_html}

    <div style="background: white; padding: 24px; border-radius: 8px; margin-top: 30px; text-align: center; color: #666; font-size: 14px;">
        <p style="margin: 0;">Denne rapporten er automatisk generert av AquaRegWatch Norway</p>
        <p style="margin: 8px 0 0 0;">
            Sporsmaal? Kontakt oss paa <a href="mailto:support@aquaregwatch.no">support@aquaregwatch.no</a>
        </p>
        <p style="margin: 16px 0 0 0; font-size: 12px; color: #999;">
            2026 AquaRegWatch Norway. Alle rettigheter reservert.
        </p>
    </div>
</body>
</html>"""

    return html


def main():
    """Generate all scenario reports"""
    print("\n" + "="*60)
    print("AquaRegWatch - Generating Scenario Reports")
    print("="*60)

    # Ensure output directory exists
    output_dir = Path("demo_reports/scenarios")
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        ("ila_outbreak", generate_ila_outbreak_scenario()),
        ("mtb_changes", generate_mtb_changes_scenario()),
        ("eu_regulation", generate_eu_regulation_scenario()),
    ]

    for filename, scenario in scenarios:
        html = generate_html_scenario_report(scenario, "Demo Kunde AS")
        path = output_dir / f"{filename}_{datetime.now().strftime('%Y%m%d')}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] Created: {path}")

    print("\n" + "="*60)
    print("Scenario reports ready for sales demos!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
