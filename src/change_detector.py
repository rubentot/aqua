"""
Change Detection Module for Norwegian Aquaculture Regulatory Monitor
Uses difflib to identify and analyze content changes
"""
import difflib
import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ChangeAnalysis:
    """Detailed analysis of detected changes"""
    has_changes: bool
    change_percent: float
    added_lines: List[str]
    removed_lines: List[str]
    modified_sections: List[Dict]
    diff_html: str
    diff_text: str
    significant_keywords_found: List[str]
    is_significant: bool
    change_summary: str


class ChangeDetector:
    """
    Detects and analyzes changes between content snapshots.
    Optimized for Norwegian aquaculture regulatory content.
    """

    # Norwegian regulatory keywords that indicate significant changes
    SIGNIFICANT_KEYWORDS = {
        # Regulations & Laws
        "forskrift": "regulation",
        "lov": "law",
        "forordning": "ordinance",
        "vedtak": "decision",
        "endring": "change/amendment",
        "ikrafttredelse": "entry into force",

        # Permits & Licenses
        "tillatelse": "permit",
        "konsesjon": "license",
        "søknad": "application",
        "godkjenning": "approval",
        "avslag": "rejection",

        # Biomass & Production
        "mtb": "maximum biomass",
        "biomasse": "biomass",
        "produksjon": "production",
        "kapasitet": "capacity",
        "utsett": "stocking",

        # Fish Health
        "lakselus": "sea lice",
        "sykdom": "disease",
        "smitte": "infection",
        "behandling": "treatment",
        "vaksine": "vaccine",
        "ila": "ISA (infectious salmon anemia)",
        "pd": "PD (pancreas disease)",

        # Environmental
        "miljø": "environment",
        "utslipp": "emissions",
        "rømming": "escape",
        "bunnpåvirkning": "seabed impact",
        "trafikklys": "traffic light system",

        # Compliance & Penalties
        "gebyr": "fee",
        "bot": "fine",
        "overtredelse": "violation",
        "sanksjoner": "sanctions",
        "stenging": "closure",
        "forbud": "prohibition",

        # Deadlines & Dates
        "frist": "deadline",
        "høring": "consultation",
        "høringsfrist": "consultation deadline",
        "innen": "by/within",

        # Zones & Areas
        "produksjonsområde": "production area",
        "rød sone": "red zone",
        "gul sone": "yellow zone",
        "grønn sone": "green zone",
    }

    # Patterns to ignore (timestamps, minor formatting)
    IGNORE_PATTERNS = [
        r'\d{1,2}\.\d{1,2}\.\d{4}',  # Norwegian date format: DD.MM.YYYY
        r'\d{4}-\d{2}-\d{2}',         # ISO date format
        r'kl\.\s*\d{1,2}[:.]\d{2}',   # Time: kl. HH:MM
        r'Sist\s+oppdatert',           # "Last updated"
        r'Publisert',                  # "Published"
        r'^\s*$',                       # Empty lines
    ]

    def __init__(
        self,
        min_change_threshold: float = 1.0,
        context_lines: int = 3
    ):
        """
        Initialize change detector.

        Args:
            min_change_threshold: Minimum percentage change to consider significant
            context_lines: Number of context lines around changes in diff
        """
        self.min_change_threshold = min_change_threshold
        self.context_lines = context_lines
        self.ignore_patterns = [re.compile(p, re.IGNORECASE) for p in self.IGNORE_PATTERNS]

    def _clean_text(self, text: str) -> str:
        """Remove noise patterns from text for comparison"""
        cleaned = text
        for pattern in self.ignore_patterns:
            cleaned = pattern.sub('', cleaned)
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """Find significant regulatory keywords in text"""
        found = []
        text_lower = text.lower()
        for keyword, english in self.SIGNIFICANT_KEYWORDS.items():
            if keyword in text_lower:
                found.append(f"{keyword} ({english})")
        return list(set(found))

    def _calculate_change_percent(self, old_lines: List[str], new_lines: List[str]) -> float:
        """Calculate percentage of content that changed"""
        if not old_lines and not new_lines:
            return 0.0
        if not old_lines:
            return 100.0

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        ratio = matcher.ratio()
        return round((1 - ratio) * 100, 2)

    def _generate_diff(
        self,
        old_text: str,
        new_text: str,
        old_label: str = "Previous",
        new_label: str = "Current"
    ) -> Tuple[str, str]:
        """
        Generate human-readable diff in text and HTML formats.

        Returns:
            Tuple of (diff_text, diff_html)
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        # Text diff (unified format)
        diff_text = ''.join(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=old_label,
            tofile=new_label,
            lineterm=''
        ))

        # HTML diff for visual display
        diff_html = difflib.HtmlDiff().make_table(
            old_lines, new_lines,
            fromdesc=old_label,
            todesc=new_label,
            context=True,
            numlines=self.context_lines
        )

        return diff_text, diff_html

    def _extract_changes(self, old_text: str, new_text: str) -> Tuple[List[str], List[str]]:
        """
        Extract added and removed lines.

        Returns:
            Tuple of (added_lines, removed_lines)
        """
        old_lines = set(old_text.splitlines())
        new_lines = set(new_text.splitlines())

        added = [line.strip() for line in (new_lines - old_lines) if line.strip()]
        removed = [line.strip() for line in (old_lines - new_lines) if line.strip()]

        return added, removed

    def _identify_modified_sections(
        self,
        old_text: str,
        new_text: str
    ) -> List[Dict]:
        """Identify which sections of the document were modified"""
        sections = []

        # Split by headers (lines starting with common header patterns)
        header_pattern = re.compile(r'^(#{1,4}|[A-ZÆØÅ][a-zæøå]+:|\d+\.\s)', re.MULTILINE)

        old_sections = header_pattern.split(old_text)
        new_sections = header_pattern.split(new_text)

        matcher = difflib.SequenceMatcher(None, old_sections, new_sections)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                section_name = "Unknown section"
                if j1 < len(new_sections):
                    # Try to extract section header
                    section_text = new_sections[j1][:100]
                    first_line = section_text.split('\n')[0].strip()
                    if first_line:
                        section_name = first_line

                sections.append({
                    'type': tag,
                    'section': section_name,
                    'old_range': (i1, i2),
                    'new_range': (j1, j2)
                })

        return sections

    def _generate_summary(
        self,
        added: List[str],
        removed: List[str],
        keywords: List[str],
        change_percent: float
    ) -> str:
        """Generate a brief summary of the changes"""
        summary_parts = []

        if change_percent >= 50:
            summary_parts.append("Major changes detected (>50% of content modified)")
        elif change_percent >= 20:
            summary_parts.append(f"Significant changes detected ({change_percent}% modified)")
        elif change_percent >= 5:
            summary_parts.append(f"Moderate changes detected ({change_percent}% modified)")
        else:
            summary_parts.append(f"Minor changes detected ({change_percent}% modified)")

        if keywords:
            summary_parts.append(f"Keywords found: {', '.join(keywords[:5])}")

        if added:
            summary_parts.append(f"Added {len(added)} new lines/items")

        if removed:
            summary_parts.append(f"Removed {len(removed)} lines/items")

        return ". ".join(summary_parts) + "."

    def detect_changes(
        self,
        old_content: str,
        new_content: str,
        source_name: str = "Unknown"
    ) -> ChangeAnalysis:
        """
        Main method to detect and analyze changes between two content versions.

        Args:
            old_content: Previous version of content
            new_content: Current version of content
            source_name: Name of the source for logging

        Returns:
            ChangeAnalysis object with detailed results
        """
        # Quick hash check - if identical, no changes
        if old_content == new_content:
            return ChangeAnalysis(
                has_changes=False,
                change_percent=0.0,
                added_lines=[],
                removed_lines=[],
                modified_sections=[],
                diff_html="",
                diff_text="",
                significant_keywords_found=[],
                is_significant=False,
                change_summary="No changes detected."
            )

        # Clean texts for comparison (remove noise)
        old_cleaned = self._clean_text(old_content)
        new_cleaned = self._clean_text(new_content)

        # Check if changes are just noise
        if old_cleaned == new_cleaned:
            logger.info(f"[{source_name}] Only noise changes detected (timestamps, etc.)")
            return ChangeAnalysis(
                has_changes=False,
                change_percent=0.0,
                added_lines=[],
                removed_lines=[],
                modified_sections=[],
                diff_html="",
                diff_text="",
                significant_keywords_found=[],
                is_significant=False,
                change_summary="Only formatting/timestamp changes (no substantive updates)."
            )

        # Calculate change percentage
        old_lines = old_cleaned.splitlines()
        new_lines = new_cleaned.splitlines()
        change_percent = self._calculate_change_percent(old_lines, new_lines)

        # Extract additions and removals
        added, removed = self._extract_changes(old_content, new_content)

        # Generate diffs
        diff_text, diff_html = self._generate_diff(old_content, new_content)

        # Find significant keywords in new/changed content
        changed_text = '\n'.join(added)
        keywords_found = self._extract_keywords(changed_text)

        # Identify modified sections
        modified_sections = self._identify_modified_sections(old_content, new_content)

        # Determine significance
        is_significant = (
            change_percent >= self.min_change_threshold or
            len(keywords_found) > 0 or
            any(kw in changed_text.lower() for kw in ['forskrift', 'frist', 'bot', 'stenging'])
        )

        # Generate summary
        summary = self._generate_summary(added, removed, keywords_found, change_percent)

        logger.info(f"[{source_name}] Changes: {change_percent}%, significant={is_significant}")

        return ChangeAnalysis(
            has_changes=True,
            change_percent=change_percent,
            added_lines=added,
            removed_lines=removed,
            modified_sections=modified_sections,
            diff_html=diff_html,
            diff_text=diff_text,
            significant_keywords_found=keywords_found,
            is_significant=is_significant,
            change_summary=summary
        )

    def compare_snapshots(
        self,
        old_snapshot: Dict,
        new_snapshot: Dict
    ) -> ChangeAnalysis:
        """
        Compare two snapshot dictionaries.
        Convenience method for database-backed comparisons.
        """
        return self.detect_changes(
            old_content=old_snapshot.get('content_text', ''),
            new_content=new_snapshot.get('content_text', ''),
            source_name=new_snapshot.get('source_id', 'Unknown')
        )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    detector = ChangeDetector()

    # Simulate old and new content
    old_content = """
    Akvakultur i Norge

    Maksimalt tillatt biomasse (MTB)
    Grensen for lakselus er 0.5 voksne hunnlus per fisk.

    Søknadsfrister:
    - Nye konsesjoner: 1. mars 2026
    - Fornyelse: Løpende

    Sist oppdatert: 01.01.2026
    """

    new_content = """
    Akvakultur i Norge

    Maksimalt tillatt biomasse (MTB)
    NY FORSKRIFT: Grensen for lakselus er redusert til 0.25 voksne hunnlus per fisk.
    Brudd på grensen kan medføre bot opptil 1 million NOK.

    Søknadsfrister:
    - Nye konsesjoner: 15. mars 2026 (endret frist)
    - Fornyelse: Løpende
    - Trafikklyssystemet evaluering: 1. april 2026

    Sist oppdatert: 03.02.2026
    """

    result = detector.detect_changes(old_content, new_content, "Test Source")

    print(f"\n{'='*60}")
    print(f"Has Changes: {result.has_changes}")
    print(f"Change %: {result.change_percent}")
    print(f"Significant: {result.is_significant}")
    print(f"Keywords: {result.significant_keywords_found}")
    print(f"\nSummary: {result.change_summary}")
    print(f"\nAdded lines:")
    for line in result.added_lines[:5]:
        print(f"  + {line[:80]}")
    print(f"\nRemoved lines:")
    for line in result.removed_lines[:5]:
        print(f"  - {line[:80]}")
