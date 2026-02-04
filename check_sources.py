#!/usr/bin/env python3
"""
AquaRegWatch Norway - Source Checker
=====================================
Simple script to check if regulatory sources are accessible.
Designed to run via GitHub Actions (FREE tier: 2000 minutes/month).

This is a lightweight check that can be expanded later to include:
- Full content scraping
- Change detection
- AI summarization
- Notification triggers
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

# Norwegian aquaculture regulatory sources to monitor
SOURCES = [
    {
        "name": "Fiskeridirektoratet",
        "url": "https://www.fiskeridir.no/Akvakultur",
        "description": "Norwegian Directorate of Fisheries - Aquaculture",
    },
    {
        "name": "Mattilsynet",
        "url": "https://www.mattilsynet.no/fisk_og_akvakultur/",
        "description": "Norwegian Food Safety Authority - Fish & Aquaculture",
    },
    {
        "name": "Regjeringen - Fiskeri",
        "url": "https://www.regjeringen.no/no/tema/mat-fiske-og-landbruk/fiskeri-og-havbruk/",
        "description": "Norwegian Government - Fisheries & Aquaculture",
    },
    {
        "name": "Lovdata - Akvakulturloven",
        "url": "https://lovdata.no/dokument/NL/lov/2005-06-17-79",
        "description": "Norwegian Law Database - Aquaculture Act",
    },
    {
        "name": "Sjømat Norge",
        "url": "https://sjomatnorge.no/",
        "description": "Norwegian Seafood Federation - Industry News",
    },
]

# Request timeout in seconds
TIMEOUT = 30

# User agent to identify our crawler
USER_AGENT = "AquaRegWatch/1.0 (Norwegian Aquaculture Regulatory Monitor; github.com/aquaregwatch)"


def check_source(source: dict) -> dict:
    """
    Check if a source URL is accessible.

    Returns a dict with status information.
    """
    result = {
        "name": source["name"],
        "url": source["url"],
        "timestamp": datetime.utcnow().isoformat(),
        "status": "unknown",
        "status_code": None,
        "response_time_ms": None,
        "error": None,
    }

    try:
        headers = {"User-Agent": USER_AGENT}
        start_time = datetime.utcnow()

        response = requests.get(
            source["url"],
            headers=headers,
            timeout=TIMEOUT,
            allow_redirects=True,
        )

        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000

        result["status_code"] = response.status_code
        result["response_time_ms"] = round(response_time, 2)

        if response.status_code == 200:
            result["status"] = "ok"
            print(f"  [OK] {source['name']} - {response_time:.0f}ms")
        else:
            result["status"] = "error"
            result["error"] = f"HTTP {response.status_code}"
            print(f"  [WARN] {source['name']} - HTTP {response.status_code}")

    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = f"Timeout after {TIMEOUT}s"
        print(f"  [TIMEOUT] {source['name']}")

    except requests.exceptions.ConnectionError as e:
        result["status"] = "connection_error"
        result["error"] = str(e)[:200]
        print(f"  [CONN ERROR] {source['name']}")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:200]
        print(f"  [ERROR] {source['name']}: {e}")

    return result


def main():
    """
    Main entry point - check all sources and save results.
    """
    print("=" * 60)
    print("AquaRegWatch Norway - Source Availability Check")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    print()

    print(f"Checking {len(SOURCES)} sources...")
    print()

    results = []
    for source in SOURCES:
        result = check_source(source)
        results.append(result)

    # Summary
    print()
    print("-" * 60)
    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"Summary: {ok_count}/{len(results)} sources accessible")
    print("-" * 60)

    # Save results to JSON
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = data_dir / f"source_check_{timestamp}.json"

    report = {
        "check_time": datetime.utcnow().isoformat(),
        "total_sources": len(SOURCES),
        "sources_ok": ok_count,
        "sources_failed": len(results) - ok_count,
        "results": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

    # Exit with error if any sources failed
    if ok_count < len(results):
        print(f"\nWarning: {len(results) - ok_count} source(s) not accessible")
        # Don't fail the workflow for source issues - just warn
        # sys.exit(1)

    print("\nCheck complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
