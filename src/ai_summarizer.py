"""
AI Summarization Module for Norwegian Aquaculture Regulatory Changes
Enhanced prompts optimized for Norwegian regulatory language and aquaculture terminology
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RegulatorySummary:
    """Structured summary of regulatory changes"""
    # Core summary
    title: str
    title_en: str
    summary_no: str
    summary_en: str

    # Impact analysis
    what_changed: str
    what_changed_en: str
    who_affected: List[str]
    affected_areas: List[str]  # Production areas (PO1-PO13)
    potential_impact: str
    opportunities: List[str]
    risks: List[str]

    # Compliance
    action_items: List[Dict]
    deadlines: List[Dict]
    penalties: List[str]
    forms_required: List[str]

    # Metadata
    category: str
    priority: str
    confidence: float
    source_url: str
    detected_at: datetime

    # Numbers extracted
    numbers_mentioned: Dict  # e.g., {"lice_limit": 0.25, "fine_max": 1000000}


class AISummarizer:
    """
    AI-powered summarization for regulatory changes.
    Optimized for Norwegian aquaculture terminology and regulatory language.
    """

    SYSTEM_PROMPT_ENHANCED = """Du er en ekspert pa norsk akvakulturregulering med dyp kunnskap om:

MYNDIGHETER:
- Fiskeridirektoratet (konsesjoner, MTB, trafikklys, lokaliteter)
- Mattilsynet (fiskehelse, lakselus, sykdommer, ILA, PD)
- Miljodirektoratet (utslipp, miljopavirkning, resipientundersokelser)
- Statsforvalterne (regionale tillatelser)

REGELVERK:
- Akvakulturloven
- Akvakulturdriftsforskriften
- Lakselusforskriften
- ILA-forskriften
- Forskrift om bekjempelse av lakselus

BRANSJETERM:
- MTB (Maksimalt Tillatt Biomasse)
- Trafikklyssystemet (gronn/gul/rod sone)
- Produksjonsomrader (PO1-PO13)
- Lakselus (voksne hunnlus per fisk)
- Lokalitet, konsesjon, tillatelse
- Settefisk, matfisk, stamfisk
- Romming, not, fortoyning

DIN OPPGAVE:
Analyser endringer og gi PRAKTISKE, HANDLINGSORIENTERTE oppsummeringer.

For HVER endring, identifiser:
1. EKSAKTE TALL som har endret seg (grenser, frister, boter)
2. HVEM som pavirkes (type oppdretter, omrade, storrelse)
3. KONKRETE HANDLINGER som ma gjores
4. FRISTER med datoer
5. KONSEKVENSER ved manglende etterlevelse

Bruk NORSK fagsprak korrekt. Vær PRESIS - ikke generaliser.

VIKTIG: Svar KUN i JSON-format som spesifisert."""

    OUTPUT_SCHEMA_ENHANCED = {
        "title": "Kort, presis tittel pa norsk (maks 80 tegn)",
        "title_en": "Same title in English",
        "summary_no": "2-3 setninger som forklarer endringen pa norsk. Inkluder spesifikke tall.",
        "summary_en": "Same summary in English for international stakeholders",
        "what_changed": "Detaljert beskrivelse av HVA som er endret, med konkrete tall og paragrafer",
        "what_changed_en": "Same in English",
        "who_affected": [
            "Spesifikk liste over hvem som pavirkes",
            "F.eks: 'Lakseoppdrettere med lokalitet i PO3'",
            "F.eks: 'Settefiskanlegg med mer enn 5 millioner smolt'"
        ],
        "affected_areas": ["Liste over PO-omrader hvis relevant, f.eks: 'PO3', 'PO4'"],
        "potential_impact": "Konkret beskrivelse av okonomisk/operasjonell pavirkning",
        "opportunities": ["Eventuelle muligheter denne endringen gir"],
        "risks": ["Risikoer ved a ikke folge opp"],
        "action_items": [
            {
                "action": "Konkret handling som ma gjores",
                "deadline": "YYYY-MM-DD eller null",
                "priority": "critical/high/medium/low",
                "responsible": "Hvem bor gjore dette (f.eks: 'Driftssjef', 'Miljoleder')"
            }
        ],
        "deadlines": [
            {
                "date": "YYYY-MM-DD",
                "description": "Hva fristen gjelder",
                "consequence": "Hva skjer hvis fristen ikke overholdes"
            }
        ],
        "penalties": ["Spesifikke sanksjoner med belop, f.eks: 'Tvangsmulkt opptil 1 000 000 NOK'"],
        "forms_required": ["Eventuelle skjemaer som ma fylles ut, f.eks: 'Soknad om dispensasjon'"],
        "category": "En av: sea_lice, fish_health, biomass, environmental, licenses, legislation, traffic_light",
        "priority": "critical/high/medium/low basert pa hastegrad og alvorlighet",
        "numbers_mentioned": {
            "example_lice_limit": 0.25,
            "example_fine_amount": 1000000,
            "example_deadline_days": 14
        }
    }

    CATEGORY_CONTEXT = {
        "sea_lice": """
            Lakselus-relaterte endringer. Se etter:
            - Grenser for voksne hunnlus per fisk (normalt 0.5, kan vare 0.2 i sommerperioden)
            - Koordinert avlusing
            - Tellefrekvens
            - Behandlingsmetoder (mekanisk, termisk, medikamentell)
            - Soneinndeling
        """,
        "fish_health": """
            Fiskehelse og sykdom. Se etter:
            - ILA (Infeksios lakseanemi) - meldepliktig
            - PD (Pankreassykdom)
            - Bekjempelsessoner
            - Vaksinasjonskrav
            - Karantene
        """,
        "biomass": """
            MTB og produksjonskapasitet. Se etter:
            - MTB-endringer (tonn)
            - Kapasitetsjusteringer
            - Utnyttelsesgrad
            - Produksjonsomrade-tilhorighet
        """,
        "traffic_light": """
            Trafikklyssystemet. Se etter:
            - Fargendring (gronn -> gul -> rod)
            - Produksjonsomrade (PO1-PO13)
            - Kapasitetsjustering (opp til +6% i gronn, 0% i gul, -6% i rod)
            - Vurderingsperiode
        """,
        "environmental": """
            Miljokrav. Se etter:
            - Utslippsgrenser
            - MOM-undersokelser (B og C)
            - Bunntilstand
            - Resipientkapasitet
            - Organisk belastning
        """,
        "licenses": """
            Konsesjoner og tillatelser. Se etter:
            - Nye tildelingsrunder
            - Soknadsfrister
            - Vilkar
            - Overforinger
            - Lokalitetsklarering
        """
    }

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = None,
        api_key: str = None
    ):
        self.provider = provider.lower()

        if self.provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.model = model or "claude-sonnet-4-20250514"
            self._init_anthropic()
        elif self.provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.model = model or "gpt-4o"
            self._init_openai()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _init_anthropic(self):
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Initialized Anthropic client with model {self.model}")
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def _init_openai(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAI client with model {self.model}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _build_enhanced_prompt(
        self,
        source_name: str,
        source_url: str,
        category: str,
        old_content: str,
        new_content: str,
        diff_summary: str,
        keywords_found: List[str]
    ) -> str:
        category_hint = self.CATEGORY_CONTEXT.get(category, "")

        prompt = f"""Analyser folgende reguleringsendring fra norske myndigheter:

=== KILDE ===
Navn: {source_name}
URL: {source_url}
Kategori: {category}

=== KATEGORI-KONTEKST ===
{category_hint}

=== NOKKELORD FUNNET ===
{', '.join(keywords_found) if keywords_found else 'Ingen spesifikke'}

=== OPPSUMMERING AV ENDRINGER ===
{diff_summary}

=== TIDLIGERE INNHOLD ===
{old_content[:3000]}{'...[forkortet]' if len(old_content) > 3000 else ''}

=== NYTT INNHOLD ===
{new_content[:3000]}{'...[forkortet]' if len(new_content) > 3000 else ''}

=== INSTRUKSJONER ===
1. Identifiser ALLE spesifikke tall, datoer og grenser som er nevnt eller endret
2. Vær KONKRET om hvem som pavirkes - ikke "alle oppdrettere" men "lakseoppdrettere i PO3-PO5"
3. List opp PRAKTISKE handlingspunkter med realistiske frister
4. Angi ALVORLIGHETSGRAD basert pa konsekvenser

Svar UTELUKKENDE i folgende JSON-format:
{json.dumps(self.OUTPUT_SCHEMA_ENHANCED, indent=2, ensure_ascii=False)}

JSON:"""
        return prompt

    def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2500,
            temperature=0.2,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _call_openai(self, prompt: str, system_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2500,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def _parse_response(self, response_text: str) -> Dict:
        # Extract JSON from response
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()

        # Find JSON object
        if "{" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            response_text = response_text[start:end]

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> Dict:
        return {
            "title": "Reguleringsendring oppdaget",
            "title_en": "Regulatory change detected",
            "summary_no": "En endring ble oppdaget. Manuell gjennomgang anbefales.",
            "summary_en": "A change was detected. Manual review recommended.",
            "what_changed": "Automatisk analyse kunne ikke fullføres",
            "what_changed_en": "Automatic analysis could not be completed",
            "who_affected": ["Ukjent - krever manuell vurdering"],
            "affected_areas": [],
            "potential_impact": "Ukjent",
            "opportunities": [],
            "risks": ["Mulig manglende etterlevelse ved manglende oppfolging"],
            "action_items": [{"action": "Gjennomga endringen manuelt", "deadline": None, "priority": "high", "responsible": "Compliance-ansvarlig"}],
            "deadlines": [],
            "penalties": [],
            "forms_required": [],
            "category": "unknown",
            "priority": "high",
            "numbers_mentioned": {}
        }

    def summarize_change(
        self,
        source_name: str,
        source_url: str,
        category: str,
        old_content: str,
        new_content: str,
        diff_summary: str,
        keywords_found: List[str] = None,
        language: str = "no"
    ) -> RegulatorySummary:
        keywords_found = keywords_found or []

        prompt = self._build_enhanced_prompt(
            source_name, source_url, category,
            old_content, new_content, diff_summary, keywords_found
        )

        try:
            if self.provider == "anthropic":
                response_text = self._call_anthropic(prompt, self.SYSTEM_PROMPT_ENHANCED)
            else:
                response_text = self._call_openai(prompt, self.SYSTEM_PROMPT_ENHANCED)

            result = self._parse_response(response_text)

            return RegulatorySummary(
                title=result.get("title", "Endring oppdaget"),
                title_en=result.get("title_en", "Change detected"),
                summary_no=result.get("summary_no", ""),
                summary_en=result.get("summary_en", ""),
                what_changed=result.get("what_changed", ""),
                what_changed_en=result.get("what_changed_en", ""),
                who_affected=result.get("who_affected", []),
                affected_areas=result.get("affected_areas", []),
                potential_impact=result.get("potential_impact", ""),
                opportunities=result.get("opportunities", []),
                risks=result.get("risks", []),
                action_items=result.get("action_items", []),
                deadlines=result.get("deadlines", []),
                penalties=result.get("penalties", []),
                forms_required=result.get("forms_required", []),
                category=result.get("category", category),
                priority=result.get("priority", "medium"),
                confidence=0.9,
                source_url=source_url,
                detected_at=datetime.utcnow(),
                numbers_mentioned=result.get("numbers_mentioned", {})
            )

        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            return RegulatorySummary(
                title=f"Endring pa {source_name}",
                title_en=f"Change on {source_name}",
                summary_no=f"Endringer oppdaget. Automatisk analyse feilet: {str(e)[:100]}",
                summary_en=f"Changes detected. Automatic analysis failed.",
                what_changed=diff_summary[:500],
                what_changed_en="See Norwegian description",
                who_affected=["Krever manuell vurdering"],
                affected_areas=[],
                potential_impact="Ukjent",
                opportunities=[],
                risks=[],
                action_items=[{"action": "Gjennomga endringene manuelt", "deadline": None, "priority": "high", "responsible": "Compliance"}],
                deadlines=[],
                penalties=[],
                forms_required=[],
                category=category,
                priority="high",
                confidence=0.0,
                source_url=source_url,
                detected_at=datetime.utcnow(),
                numbers_mentioned={}
            )


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if os.getenv("ANTHROPIC_API_KEY"):
        summarizer = AISummarizer(provider="anthropic")

        old_content = """
        Lakselusgrenser
        Grensen for voksne hunnlus er 0.5 per fisk.
        Telling skal gjores ukentlig.
        """

        new_content = """
        Lakselusgrenser - OPPDATERT 01.02.2026
        NY FORSKRIFT: Grensen for voksne hunnlus er redusert til 0.25 per fisk.
        Gjelder fra 1. mars 2026 for PO3, PO4 og PO5.
        Telling skal gjores to ganger per uke.
        Brudd kan medfore tvangsmulkt pa opptil 1 million NOK.
        Anlegg ma soke dispensasjon innen 15. mars 2026.
        """

        summary = summarizer.summarize_change(
            source_name="Mattilsynet - Lakselus",
            source_url="https://www.mattilsynet.no/fisk/lakselus",
            category="sea_lice",
            old_content=old_content,
            new_content=new_content,
            diff_summary="Lakselusgrense redusert fra 0.5 til 0.25",
            keywords_found=["lakselus", "forskrift", "grense"]
        )

        print(f"\nTitle: {summary.title}")
        print(f"Summary: {summary.summary_no}")
        print(f"Affected: {summary.who_affected}")
        print(f"Areas: {summary.affected_areas}")
        print(f"Actions: {summary.action_items}")
        print(f"Numbers: {summary.numbers_mentioned}")
    else:
        print("ANTHROPIC_API_KEY not set")
