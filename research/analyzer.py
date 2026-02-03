"""Analysis and scoring logic for designer portfolios."""

import re
from scraper import PortfolioCandidate
from config import (
    DIRECTOR_LEVEL_KEYWORDS,
    MINIMAL_DESIGN_KEYWORDS,
    NOTABLE_COMPANIES,
    SCORING_WEIGHTS,
)


class PortfolioAnalyzer:
    """Analyzes and scores designer portfolios."""

    def analyze_candidate(self, candidate: PortfolioCandidate) -> PortfolioCandidate:
        """Analyze a single portfolio candidate and compute scores."""
        text = f"{candidate.title} {candidate.snippet} {candidate.page_content}".lower()

        # Compute individual scores
        candidate.scores = {
            "role_level": self._score_role_level(text),
            "minimal_aesthetic": self._score_minimal_aesthetic(text, candidate.url),
            "portfolio_quality": self._score_portfolio_quality(text, candidate),
            "company_reputation": self._score_company_reputation(text),
            "site_performance": self._score_site_performance(candidate),
        }

        # Extract name, role, company
        candidate.name = self._extract_name(candidate.title, text)
        candidate.role = self._extract_role(text)
        candidate.company = self._extract_company(text)

        # Compute weighted total score
        candidate.total_score = sum(
            candidate.scores[key] * SCORING_WEIGHTS[key]
            for key in SCORING_WEIGHTS
        )

        return candidate

    def _score_role_level(self, text: str) -> float:
        """Score based on director-level role indicators (0-10)."""
        score = 0
        matches = 0

        for keyword in DIRECTOR_LEVEL_KEYWORDS:
            if keyword in text:
                matches += 1
                # Higher weight for more senior titles
                if any(w in keyword for w in ["vp", "vice president", "chief", "head of", "executive"]):
                    score += 3
                elif any(w in keyword for w in ["director", "principal"]):
                    score += 2
                else:
                    score += 1

        # Normalize to 0-10
        return min(10, score)

    def _score_minimal_aesthetic(self, text: str, url: str) -> float:
        """Score based on minimal design indicators (0-10)."""
        score = 0

        # Check for minimal design keywords in content
        for keyword in MINIMAL_DESIGN_KEYWORDS:
            if keyword in text:
                score += 1.5

        # Bonus for personal domains (often more minimal)
        if self._is_personal_domain(url):
            score += 2

        # Bonus for known minimal design platforms
        minimal_platforms = ["cargo.site", "squarespace", "readymag", "format.com"]
        if any(platform in url.lower() for platform in minimal_platforms):
            score += 1

        return min(10, score)

    def _score_portfolio_quality(self, text: str, candidate: PortfolioCandidate) -> float:
        """Score based on portfolio content quality (0-10)."""
        score = 5  # Base score

        # Check for case study indicators
        case_study_keywords = ["case study", "project", "work", "portfolio", "design process", "challenge", "solution"]
        for keyword in case_study_keywords:
            if keyword in text:
                score += 0.5

        # Check for depth indicators
        depth_keywords = ["research", "user testing", "iteration", "prototype", "wireframe", "strategy"]
        for keyword in depth_keywords:
            if keyword in text:
                score += 0.5

        # Penalty for very short content
        if len(candidate.page_content) < 500:
            score -= 2

        return max(0, min(10, score))

    def _score_company_reputation(self, text: str) -> float:
        """Score based on notable company associations (0-10)."""
        score = 0
        found_companies = []

        for company in NOTABLE_COMPANIES:
            if company in text:
                found_companies.append(company)
                # FAANG/top tech gets higher score
                if company in ["google", "apple", "meta", "facebook", "microsoft", "amazon"]:
                    score += 3
                # Top design companies
                elif company in ["pentagram", "ideo", "frog", "figma", "airbnb", "stripe"]:
                    score += 2.5
                else:
                    score += 1.5

        return min(10, score)

    def _score_site_performance(self, candidate: PortfolioCandidate) -> float:
        """Score based on site characteristics (0-10)."""
        score = 5  # Base score

        # HTTPS bonus
        if candidate.url.startswith("https"):
            score += 1

        # Personal domain bonus
        if self._is_personal_domain(candidate.url):
            score += 2

        # Penalty for very long URLs (often aggregator pages)
        if len(candidate.url) > 100:
            score -= 2

        return max(0, min(10, score))

    def _is_personal_domain(self, url: str) -> bool:
        """Check if URL appears to be a personal domain."""
        aggregators = [
            "dribbble.com", "behance.net", "linkedin.com",
            "medium.com", "twitter.com", "about.me",
            "carbonmade.com", "coroflot.com"
        ]
        return not any(agg in url.lower() for agg in aggregators)

    def _extract_name(self, title: str, text: str) -> str:
        """Attempt to extract designer name from content."""
        # Try to get name from title (often "Name - Title" or "Name | Portfolio")
        separators = [" - ", " | ", " – ", " — "]
        for sep in separators:
            if sep in title:
                potential_name = title.split(sep)[0].strip()
                # Basic validation: 2-4 words, no common non-name words
                words = potential_name.split()
                if 1 <= len(words) <= 4:
                    non_name_words = ["portfolio", "design", "creative", "studio", "agency", "the", "welcome"]
                    if not any(w.lower() in non_name_words for w in words):
                        return potential_name

        return "Unknown"

    def _extract_role(self, text: str) -> str:
        """Extract the most senior role mentioned."""
        # Priority order for roles
        role_priority = [
            ("chief design officer", "Chief Design Officer"),
            ("cdo", "Chief Design Officer"),
            ("vp of design", "VP of Design"),
            ("vp design", "VP of Design"),
            ("vice president", "VP of Design"),
            ("head of design", "Head of Design"),
            ("executive creative director", "Executive Creative Director"),
            ("design director", "Design Director"),
            ("creative director", "Creative Director"),
            ("principal designer", "Principal Designer"),
            ("design lead", "Design Lead"),
        ]

        for keyword, role_name in role_priority:
            if keyword in text:
                return role_name

        return "Designer"

    def _extract_company(self, text: str) -> str:
        """Extract the most notable company mentioned."""
        # Check for notable companies in order of prestige
        priority_companies = [
            "google", "apple", "meta", "microsoft", "amazon",
            "airbnb", "stripe", "figma", "spotify", "netflix",
            "pentagram", "ideo", "frog"
        ]

        for company in priority_companies:
            if company in text:
                return company.title()

        # Check remaining notable companies
        for company in NOTABLE_COMPANIES:
            if company in text:
                return company.title()

        return "Independent"

    def analyze_all(self, candidates: list[PortfolioCandidate]) -> list[PortfolioCandidate]:
        """Analyze all candidates and return sorted by score."""
        analyzed = []
        for candidate in candidates:
            analyzed.append(self.analyze_candidate(candidate))

        # Sort by total score descending
        analyzed.sort(key=lambda c: c.total_score, reverse=True)

        return analyzed

    def get_top_results(self, candidates: list[PortfolioCandidate], n: int = 10) -> list[PortfolioCandidate]:
        """Get top N candidates by score."""
        return candidates[:n]
