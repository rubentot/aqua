"""
Web Scraper for Norwegian Government Aquaculture Pages
Handles fetching and content extraction with rate limiting and error handling
"""
import hashlib
import logging
import re
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Container for scraped page content"""
    url: str
    html: str
    text: str
    content_hash: str
    word_count: int
    links: List[Dict[str, str]]
    headers: List[str]
    timestamp: datetime
    http_status: int
    response_time_ms: int
    error: Optional[str] = None


class NorwegianAquacultureScraper:
    """
    Scraper optimized for Norwegian government aquaculture websites.
    Handles Norwegian language content and specific site structures.
    """

    DEFAULT_HEADERS = {
        "User-Agent": "AquaRegWatch/1.0 (Regulatory Monitoring Service; contact@aquaregwatch.no)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "no,nb,nn,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    # Site-specific selectors for content extraction
    SITE_SELECTORS = {
        "fiskeridir.no": {
            "content": ["main", ".main-content", "article", ".content"],
            "news": [".news-list", ".article-list", ".nyhetsliste"],
            "exclude": ["nav", "header", "footer", ".breadcrumb", ".navigation", "script", "style"]
        },
        "mattilsynet.no": {
            "content": ["main", ".page-content", "article", ".content-area"],
            "news": [".news-items", ".aktuelt"],
            "exclude": ["nav", "header", "footer", ".menu", "script", "style"]
        },
        "miljodirektoratet.no": {
            "content": ["main", ".article-content", "article"],
            "news": [".news-list"],
            "exclude": ["nav", "header", "footer", "script", "style"]
        },
        "lovdata.no": {
            "content": [".search-results", ".dokument", ".lovtekst", "main"],
            "news": [".results"],
            "exclude": ["nav", "header", "footer", "script", "style"]
        },
        "regjeringen.no": {
            "content": ["main", ".article", ".content", "article"],
            "news": [".news-list", ".aktuelt"],
            "exclude": ["nav", "header", "footer", ".breadcrumbs", "script", "style"]
        },
        "eur-lex.europa.eu": {
            "content": [".SearchResult", ".results", "#document", "main"],
            "news": [".search-results"],
            "exclude": ["nav", "header", "footer", "script", "style"]
        }
    }

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 5,
        rate_limit_delay: float = 1.0
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.last_request_time = 0
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # No line wrapping

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _get_site_key(self, url: str) -> str:
        """Extract site key for selector lookup"""
        domain = urlparse(url).netloc.lower()
        for site_key in self.SITE_SELECTORS:
            if site_key in domain:
                return site_key
        return "default"

    def _extract_content(self, soup: BeautifulSoup, url: str, custom_selectors: Dict = None) -> Tuple[str, List[Dict], List[str]]:
        """
        Extract main content from page, removing navigation, headers, footers.
        Returns: (text_content, links, headers)
        """
        site_key = self._get_site_key(url)
        selectors = self.SITE_SELECTORS.get(site_key, {
            "content": ["main", "article", ".content"],
            "exclude": ["nav", "header", "footer", "script", "style"]
        })

        # Use custom selectors if provided
        if custom_selectors:
            selectors.update(custom_selectors)

        # Remove excluded elements
        for exclude_selector in selectors.get("exclude", []):
            for elem in soup.select(exclude_selector):
                elem.decompose()

        # Find main content area
        content_element = None
        for selector in selectors.get("content", []):
            content_element = soup.select_one(selector)
            if content_element:
                break

        # Fall back to body if no content area found
        if not content_element:
            content_element = soup.body or soup

        # Extract links with context
        links = []
        for link in content_element.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if href and text:
                full_url = urljoin(url, href)
                links.append({
                    "url": full_url,
                    "text": text,
                    "is_document": any(ext in href.lower() for ext in [".pdf", ".doc", ".xlsx", ".xls"])
                })

        # Extract headers for structure understanding
        headers = []
        for header in content_element.find_all(["h1", "h2", "h3", "h4"]):
            text = header.get_text(strip=True)
            if text:
                headers.append(f"{header.name}: {text}")

        # Convert to clean text
        text_content = content_element.get_text(separator="\n", strip=True)

        # Clean up whitespace
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        text_content = re.sub(r' {2,}', ' ', text_content)

        return text_content, links, headers

    def fetch_page(self, url: str, custom_selectors: Dict = None) -> ScrapedContent:
        """
        Fetch and process a single page with retry logic.
        """
        self._rate_limit()

        start_time = time.time()
        error = None
        html_content = ""
        http_status = 0

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                http_status = response.status_code

                if response.status_code == 200:
                    html_content = response.text
                    break
                elif response.status_code == 404:
                    error = f"Page not found (404): {url}"
                    break
                elif response.status_code >= 500:
                    error = f"Server error ({response.status_code})"
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                else:
                    error = f"HTTP {response.status_code}"

            except requests.exceptions.Timeout:
                error = f"Timeout after {self.timeout}s"
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except requests.exceptions.ConnectionError as e:
                error = f"Connection error: {str(e)[:100]}"
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except Exception as e:
                error = f"Unexpected error: {str(e)[:100]}"
                break

        response_time_ms = int((time.time() - start_time) * 1000)

        if error and not html_content:
            logger.warning(f"Failed to fetch {url}: {error}")
            return ScrapedContent(
                url=url,
                html="",
                text="",
                content_hash="",
                word_count=0,
                links=[],
                headers=[],
                timestamp=datetime.utcnow(),
                http_status=http_status,
                response_time_ms=response_time_ms,
                error=error
            )

        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')

        # Extract content
        text_content, links, headers = self._extract_content(soup, url, custom_selectors)

        # Calculate hash of text content (for change detection)
        content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()

        # Word count
        word_count = len(text_content.split())

        return ScrapedContent(
            url=url,
            html=html_content,
            text=text_content,
            content_hash=content_hash,
            word_count=word_count,
            links=links,
            headers=headers,
            timestamp=datetime.utcnow(),
            http_status=http_status,
            response_time_ms=response_time_ms
        )

    def fetch_multiple(self, urls: List[str]) -> List[ScrapedContent]:
        """Fetch multiple pages with rate limiting"""
        results = []
        for url in urls:
            result = self.fetch_page(url)
            results.append(result)
            logger.info(f"Fetched {url}: {result.word_count} words, hash={result.content_hash[:8]}")
        return results


class VisualPingIntegration:
    """
    Helper class for setting up Visualping.io monitoring.
    Provides configuration guidance and webhook handling.
    """

    @staticmethod
    def generate_setup_instructions(sources: List[Dict]) -> str:
        """Generate step-by-step Visualping setup instructions"""
        instructions = """
# Visualping.io Setup for Norwegian Aquaculture Monitoring

## Step 1: Create Account
1. Go to https://visualping.io/
2. Sign up for a Business plan (recommended for hourly checks)

## Step 2: Add Monitoring Jobs

For each URL below, create a new monitoring job:

"""
        for i, source in enumerate(sources, 1):
            instructions += f"""
### {i}. {source['name']}
- **URL:** {source['url']}
- **Check Frequency:** Every {source.get('check_interval_hours', 4)} hours
- **Comparison Mode:** Visual + Text
- **Sensitivity:** Medium-High (to catch regulation changes)
- **Area to Monitor:** Select the main content area (avoid headers/footers)

"""

        instructions += """
## Step 3: Configure Webhook (for automation)

1. Go to Account Settings > Integrations
2. Add a Webhook with your server URL:
   `https://your-server.com/api/visualping-webhook`

3. The webhook will receive JSON like:
```json
{
  "job_id": "12345",
  "url": "https://www.fiskeridir.no/Akvakultur",
  "change_detected": true,
  "screenshot_url": "https://...",
  "timestamp": "2026-02-03T10:30:00Z"
}
```

## Step 4: Set Up Alerts
- Email alerts: Add team members
- Slack integration: Connect your workspace
- Set "Only alert on significant changes"

## Estimated Cost
- ~10 URLs at hourly checks = ~$50-100/month on Business plan
"""
        return instructions


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test scraper
    scraper = NorwegianAquacultureScraper()

    test_urls = [
        "https://www.fiskeridir.no/Akvakultur",
        "https://www.fiskeridir.no/Akvakultur/Nyheter",
    ]

    for url in test_urls:
        result = scraper.fetch_page(url)
        print(f"\n{'='*60}")
        print(f"URL: {result.url}")
        print(f"Status: {result.http_status}")
        print(f"Words: {result.word_count}")
        print(f"Hash: {result.content_hash[:16]}...")
        print(f"Headers found: {len(result.headers)}")
        print(f"Links found: {len(result.links)}")
        if result.error:
            print(f"Error: {result.error}")
        print(f"First 500 chars:\n{result.text[:500]}...")
