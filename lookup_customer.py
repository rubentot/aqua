#!/usr/bin/env python3
"""
AquaRegWatch - Customer Lookup
==============================
Auto-populate customer profiles from Fiskeridirektoratet's public API.
Just give us an org number, we know everything about their operation.

Usage:
    python lookup_customer.py 969159570
    python lookup_customer.py "Lerøy"
"""

import sys
import json
import requests
from collections import defaultdict

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_BASE = "https://api.fiskeridir.no/pub-aqua/api/v1"


def lookup_by_org_number(org_nr: str) -> dict:
    """Lookup company by organization number."""
    print(f"🔍 Looking up org.nr: {org_nr}")

    # Get all licenses (API doesn't support direct org filter, so we fetch and filter)
    # In production, you'd cache this or use pagination
    response = requests.get(f"{API_BASE}/licenses", timeout=60)
    response.raise_for_status()
    licenses = response.json()

    # Filter by org number
    company_licenses = [l for l in licenses if l.get("openLegalEntityNr") == org_nr]

    if not company_licenses:
        print(f"❌ No licenses found for org.nr {org_nr}")
        return None

    return build_profile(company_licenses)


def lookup_by_name(name: str) -> dict:
    """Lookup company by name (partial match)."""
    print(f"🔍 Searching for: {name}")

    response = requests.get(f"{API_BASE}/licenses", timeout=60)
    response.raise_for_status()
    licenses = response.json()

    # Filter by name (case-insensitive partial match)
    name_lower = name.lower()
    company_licenses = [
        l for l in licenses
        if name_lower in l.get("legalEntityName", "").lower()
    ]

    if not company_licenses:
        print(f"❌ No licenses found matching '{name}'")
        return None

    # Group by company
    companies = defaultdict(list)
    for lic in company_licenses:
        companies[lic.get("legalEntityName")].append(lic)

    if len(companies) > 1:
        print(f"\n📋 Found {len(companies)} companies matching '{name}':")
        for i, (company_name, lics) in enumerate(companies.items(), 1):
            org_nr = lics[0].get("openLegalEntityNr", "N/A")
            print(f"  {i}. {company_name} (Org.nr: {org_nr}) - {len(lics)} licenses")
        print(f"\n💡 Use org number for exact match: python lookup_customer.py <org_nr>")
        return None

    return build_profile(company_licenses)


def build_profile(licenses: list) -> dict:
    """Build customer profile from licenses."""
    if not licenses:
        return None

    first_license = licenses[0]
    company_name = first_license.get("legalEntityName", "Unknown")
    org_nr = first_license.get("openLegalEntityNr", "")

    # Collect unique data across all licenses
    species = set()
    regions = set()
    counties = set()
    municipalities = set()
    prod_areas = set()
    total_mtb = 0
    site_count = 0
    license_types = set()

    for lic in licenses:
        # Species
        if lic.get("species") and lic["species"].get("fishCodes"):
            for fish in lic["species"]["fishCodes"]:
                species.add(fish.get("nbNoName", fish.get("enGbName", "Unknown")))

        # Location
        placement = lic.get("placement", {})
        if placement.get("countyName"):
            counties.add(placement["countyName"])
        if placement.get("municipalityName"):
            municipalities.add(placement["municipalityName"])
        if placement.get("prodAreaName"):
            prod_areas.add(placement["prodAreaName"])

        # Capacity
        capacity = lic.get("capacity", {})
        if capacity.get("current") and capacity.get("unit") == "TN":
            total_mtb += capacity["current"]

        # Sites
        connections = lic.get("connections", [])
        site_count += len(connections)

        # License type
        lic_type = lic.get("type", {})
        if lic_type.get("intentionValue"):
            license_types.add(lic_type["intentionValue"])

    # Map counties to regions
    county_to_region = {
        "NORDLAND": "Nordland",
        "TROMS": "Troms og Finnmark",
        "FINNMARK": "Troms og Finnmark",
        "TROMS OG FINNMARK": "Troms og Finnmark",
        "TRØNDELAG": "Trøndelag",
        "MØRE OG ROMSDAL": "Møre og Romsdal",
        "VESTLAND": "Vestland",
        "ROGALAND": "Rogaland",
        "AGDER": "Agder",
        "VESTFOLD OG TELEMARK": "Vestfold og Telemark",
        "VIKEN": "Viken",
        "OSLO": "Oslo",
        "INNLANDET": "Innlandet",
        "AKERSHUS": "Akershus",
    }

    for county in counties:
        region = county_to_region.get(county.upper(), county)
        regions.add(region)

    # Determine production type
    prod_type = "Ukjent"
    if any("sjø" in pa.lower() or "kyst" in pa.lower() for pa in prod_areas):
        prod_type = "Sjøbasert"
    elif any("land" in pa.lower() for pa in prod_areas):
        prod_type = "Landbasert"

    # Determine concerns based on species and location
    concerns = []
    if "Laks" in species or "Regnbueørret" in species:
        concerns.extend(["Lakselus", "Rømming", "Trafikklyssystemet"])
    if total_mtb > 0:
        concerns.append("MTB")
    concerns.extend(["Miljøovervåking", "Fiskehelse"])

    profile = {
        "id": f"auto-{org_nr}",
        "company": company_name,
        "org_number": org_nr,
        "email": "",  # Customer needs to provide this
        "plan": "professional",
        "active": False,  # Set to true when they pay
        "profile": {
            "licenses": list(species),
            "license_count": len(licenses),
            "regions": list(regions),
            "counties": list(counties),
            "production_areas": list(prod_areas),
            "production_type": prod_type,
            "mtb_tonnes": round(total_mtb, 1),
            "site_count": site_count,
            "concerns": concerns,
            "notes": f"Auto-populated from Akvakulturregisteret. {len(licenses)} licenses, {site_count} sites."
        },
        "_raw_license_count": len(licenses)
    }

    return profile


def print_profile(profile: dict):
    """Pretty print a customer profile."""
    if not profile:
        return

    print("\n" + "="*60)
    print(f"🏢 {profile['company']}")
    print(f"   Org.nr: {profile['org_number']}")
    print("="*60)

    p = profile['profile']
    print(f"\n📊 OVERSIKT:")
    print(f"   Lisenser: {p['license_count']}")
    print(f"   Lokaliteter: {p['site_count']}")
    print(f"   MTB: {p['mtb_tonnes']} tonn")
    print(f"   Produksjon: {p['production_type']}")

    print(f"\n🐟 ARTER:")
    for species in p['licenses']:
        print(f"   - {species}")

    print(f"\n📍 REGIONER:")
    for region in p['regions']:
        print(f"   - {region}")

    print(f"\n🎯 FOKUSOMRÅDER:")
    for concern in p['concerns']:
        print(f"   - {concern}")

    print("\n" + "="*60)
    print("📝 Kopier dette til customers.json:")
    print("="*60)

    # Output JSON for easy copy-paste
    output = {
        "id": profile["id"],
        "company": profile["company"],
        "email": "FYLL-INN@example.com",
        "plan": "professional",
        "active": True,
        "profile": profile["profile"]
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python lookup_customer.py <org_number>")
        print("  python lookup_customer.py <company_name>")
        print("\nExamples:")
        print("  python lookup_customer.py 969159570")
        print('  python lookup_customer.py "Lerøy"')
        print('  python lookup_customer.py "Mowi"')
        sys.exit(1)

    query = sys.argv[1]

    # Check if it's an org number (all digits)
    if query.isdigit():
        profile = lookup_by_org_number(query)
    else:
        profile = lookup_by_name(query)

    if profile:
        print_profile(profile)


if __name__ == "__main__":
    main()
