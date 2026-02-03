"""Configuration for the designer portfolio research agent."""

# Search queries to find director-level designers with minimal portfolios
SEARCH_QUERIES = [
    "design director portfolio minimal",
    "head of design personal website",
    "principal designer portfolio clean",
    "VP design portfolio minimalist",
    "creative director portfolio white space",
    "design lead portfolio simple",
    "senior design director personal site",
    "chief design officer portfolio",
]

# Keywords indicating director-level roles
DIRECTOR_LEVEL_KEYWORDS = [
    "design director",
    "head of design",
    "vp design",
    "vp of design",
    "vice president design",
    "principal designer",
    "creative director",
    "chief design officer",
    "cdo",
    "design lead",
    "senior director",
    "executive creative director",
    "global head of design",
]

# Keywords indicating minimal design aesthetic
MINIMAL_DESIGN_KEYWORDS = [
    "minimal",
    "minimalist",
    "clean",
    "simple",
    "white space",
    "whitespace",
    "monochrome",
    "typography",
    "swiss design",
    "brutalist",
]

# Notable companies (for scoring)
NOTABLE_COMPANIES = [
    "google",
    "apple",
    "meta",
    "facebook",
    "microsoft",
    "amazon",
    "airbnb",
    "spotify",
    "stripe",
    "figma",
    "dropbox",
    "uber",
    "lyft",
    "netflix",
    "tesla",
    "ibm",
    "salesforce",
    "adobe",
    "slack",
    "notion",
    "linear",
    "vercel",
    "pentagram",
    "ideo",
    "frog",
    "r/ga",
    "huge",
    "instrument",
]

# Scoring weights
SCORING_WEIGHTS = {
    "role_level": 0.30,
    "minimal_aesthetic": 0.25,
    "portfolio_quality": 0.20,
    "company_reputation": 0.15,
    "site_performance": 0.10,
}

# Search settings
MAX_RESULTS_PER_QUERY = 20
TOTAL_TOP_RESULTS = 10
REQUEST_DELAY = 2  # seconds between requests to avoid rate limiting
