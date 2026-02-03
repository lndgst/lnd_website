"""Web search and scraping functionality for finding designer portfolios."""

import time
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from dataclasses import dataclass, field

from config import (
    SEARCH_QUERIES,
    MAX_RESULTS_PER_QUERY,
    REQUEST_DELAY,
)


@dataclass
class PortfolioCandidate:
    """Represents a potential designer portfolio found during search."""
    url: str
    title: str
    snippet: str
    name: str = ""
    role: str = ""
    company: str = ""
    page_content: str = ""
    scores: dict = field(default_factory=dict)
    total_score: float = 0.0


class PortfolioScraper:
    """Scrapes the web for designer portfolios."""

    def __init__(self):
        self.client = httpx.Client(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            }
        )
        self.candidates: list[PortfolioCandidate] = []

    def search_google(self, query: str, num_results: int = 10) -> list[dict]:
        """
        Search Google for designer portfolios.
        Returns list of {url, title, snippet} dicts.
        """
        try:
            from googlesearch import search
            results = []
            for url in search(query, num_results=num_results, advanced=True):
                results.append({
                    "url": url.url if hasattr(url, 'url') else url,
                    "title": url.title if hasattr(url, 'title') else "",
                    "snippet": url.description if hasattr(url, 'description') else "",
                })
            return results
        except ImportError:
            print("googlesearch-python not installed. Using mock data.")
            return self._get_mock_results(query)
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            return []

    def _get_mock_results(self, query: str) -> list[dict]:
        """Return mock results for testing without API."""
        mock_portfolios = [
            {
                "url": "https://www.davidairey.com",
                "title": "David Airey - Logo Designer",
                "snippet": "Minimal brand identity designer portfolio"
            },
            {
                "url": "https://www.tbwa.com",
                "title": "TBWA Creative Director Portfolios",
                "snippet": "Global creative director work showcase"
            },
        ]
        return mock_portfolios

    def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch and parse page content from a URL."""
        try:
            response = self.client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Get text content
            text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            text = " ".join(chunk for chunk in lines if chunk)

            return text[:5000]  # Limit content length

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_meta_info(self, url: str) -> dict:
        """Extract metadata from a portfolio page."""
        try:
            response = self.client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            meta_info = {
                "title": "",
                "description": "",
                "og_title": "",
                "og_description": "",
            }

            # Get title
            title_tag = soup.find("title")
            if title_tag:
                meta_info["title"] = title_tag.get_text(strip=True)

            # Get meta description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                meta_info["description"] = meta_desc.get("content", "")

            # Get Open Graph data
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title:
                meta_info["og_title"] = og_title.get("content", "")

            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc:
                meta_info["og_description"] = og_desc.get("content", "")

            return meta_info

        except Exception as e:
            print(f"Error extracting meta from {url}: {e}")
            return {}

    def run_search(self) -> list[PortfolioCandidate]:
        """Run all search queries and collect candidates."""
        seen_urls = set()

        for query in SEARCH_QUERIES:
            print(f"Searching: {query}")
            results = self.search_google(query, MAX_RESULTS_PER_QUERY)

            for result in results:
                url = result.get("url", "")

                # Skip duplicates
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Skip non-portfolio URLs
                if self._is_excluded_domain(url):
                    continue

                candidate = PortfolioCandidate(
                    url=url,
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                )
                self.candidates.append(candidate)

            # Rate limiting
            time.sleep(REQUEST_DELAY)

        print(f"Found {len(self.candidates)} unique candidates")
        return self.candidates

    def _is_excluded_domain(self, url: str) -> bool:
        """Check if URL should be excluded (aggregator sites, etc.)."""
        excluded = [
            "linkedin.com/jobs",
            "indeed.com",
            "glassdoor.com",
            "pinterest.com",
            "twitter.com",
            "facebook.com",
            "instagram.com",
            "youtube.com",
            "medium.com/@",
            "wikipedia.org",
        ]
        return any(exc in url.lower() for exc in excluded)

    def enrich_candidates(self, candidates: list[PortfolioCandidate]) -> list[PortfolioCandidate]:
        """Fetch additional content for each candidate."""
        for i, candidate in enumerate(candidates):
            print(f"Enriching {i+1}/{len(candidates)}: {candidate.url}")

            # Fetch page content
            content = self.fetch_page_content(candidate.url)
            if content:
                candidate.page_content = content

            # Extract meta info
            meta = self.extract_meta_info(candidate.url)
            if meta.get("title"):
                candidate.title = meta["title"]

            time.sleep(REQUEST_DELAY)

        return candidates

    def close(self):
        """Close the HTTP client."""
        self.client.close()
