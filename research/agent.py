#!/usr/bin/env python3
"""
Designer Portfolio Research Agent

Searches the web for portfolios of director-level designers with minimal
design aesthetics and generates a ranked report of the top 10 results.

Usage:
    python agent.py [--mock]

Options:
    --mock    Use mock data instead of live web search (for testing)
"""

import sys
import argparse
from pathlib import Path

from config import TOTAL_TOP_RESULTS
from scraper import PortfolioScraper, PortfolioCandidate
from analyzer import PortfolioAnalyzer
from report import ReportGenerator


def get_mock_candidates() -> list[PortfolioCandidate]:
    """Return mock candidates for testing without web access."""
    mock_data = [
        {
            "url": "https://www.mikeabbink.com",
            "title": "Mike Abbink - Executive Creative Director",
            "snippet": "Executive Creative Director at IBM. Minimal portfolio showcasing brand design work.",
            "page_content": "Mike Abbink Executive Creative Director IBM Design brand identity minimal clean typography swiss design case study project research user testing",
        },
        {
            "url": "https://www.bethanykoby.com",
            "title": "Bethany Koby - Design Director",
            "snippet": "Design Director and co-founder. Clean, minimal portfolio with tech focus.",
            "page_content": "Bethany Koby Design Director technology innovation minimal whitespace portfolio case study design process challenge solution prototype",
        },
        {
            "url": "https://www.emilykolar.com",
            "title": "Emily Kolar - Head of Design",
            "snippet": "Head of Design at Stripe. Minimalist portfolio featuring fintech design.",
            "page_content": "Emily Kolar Head of Design Stripe fintech minimal clean simple white space portfolio project work research strategy wireframe",
        },
        {
            "url": "https://www.jonathanhoefler.com",
            "title": "Jonathan Hoefler - Creative Director",
            "snippet": "Creative Director and type designer. Swiss-inspired minimal aesthetic.",
            "page_content": "Jonathan Hoefler Creative Director typography type design minimal swiss brutalist case study portfolio project",
        },
        {
            "url": "https://www.dieterrams.design",
            "title": "Dieter Rams Tribute - Design Philosophy",
            "snippet": "Principal Designer portfolio inspired by Rams. Less but better.",
            "page_content": "Principal Designer minimal design philosophy less better clean simple monochrome portfolio project case study iteration",
        },
        {
            "url": "https://www.marissamayer.com",
            "title": "Marissa Mayer - VP Design Portfolio",
            "snippet": "Former VP at Google. Clean portfolio of product design work.",
            "page_content": "Marissa Mayer VP Design Google Yahoo product design minimal clean portfolio case study user testing research strategy",
        },
        {
            "url": "https://www.jonyive.design",
            "title": "Industrial Design Director Portfolio",
            "snippet": "Design Director specializing in minimal industrial design at Apple.",
            "page_content": "Design Director Apple industrial design minimal clean white space portfolio case study project prototype iteration",
        },
        {
            "url": "https://www.katiekovalcin.com",
            "title": "Katie Kovalcin - Design Lead",
            "snippet": "Design Lead at Figma. Minimal portfolio with product focus.",
            "page_content": "Katie Kovalcin Design Lead Figma product design minimal whitespace portfolio case study research wireframe prototype",
        },
        {
            "url": "https://www.jasonfried.com",
            "title": "Jason Fried - Head of Product Design",
            "snippet": "Head of Product Design at Basecamp. Simple, minimal aesthetic.",
            "page_content": "Jason Fried Head of Design Basecamp product design minimal simple clean portfolio project case study",
        },
        {
            "url": "https://www.tobiasvanburen.com",
            "title": "Tobias Van Buren - Creative Director",
            "snippet": "Creative Director at Pentagram. Minimal portfolio showcasing brand work.",
            "page_content": "Tobias Van Buren Creative Director Pentagram brand design minimal clean typography portfolio case study project research",
        },
        {
            "url": "https://www.sararosso.com",
            "title": "Sara Rosso - Design Director",
            "snippet": "Design Director at Airbnb. Clean minimal portfolio.",
            "page_content": "Sara Rosso Design Director Airbnb product design minimal clean portfolio case study user testing",
        },
        {
            "url": "https://www.alexschleifer.com",
            "title": "Alex Schleifer - VP of Design",
            "snippet": "VP of Design at Airbnb. Minimalist portfolio.",
            "page_content": "Alex Schleifer VP Design Airbnb product design minimal portfolio case study research prototype",
        },
    ]

    return [
        PortfolioCandidate(
            url=d["url"],
            title=d["title"],
            snippet=d["snippet"],
            page_content=d["page_content"],
        )
        for d in mock_data
    ]


def run_agent(use_mock: bool = False):
    """Run the designer portfolio research agent."""
    print("=" * 60)
    print("Designer Portfolio Research Agent")
    print("=" * 60)
    print()

    # Initialize components
    scraper = PortfolioScraper()
    analyzer = PortfolioAnalyzer()
    reporter = ReportGenerator()

    try:
        # Step 1: Search for portfolios
        print("Step 1: Searching for designer portfolios...")
        print("-" * 40)

        if use_mock:
            print("Using mock data for testing...")
            candidates = get_mock_candidates()
        else:
            candidates = scraper.run_search()

            # Step 2: Enrich candidates with page content
            print()
            print("Step 2: Fetching portfolio content...")
            print("-" * 40)
            candidates = scraper.enrich_candidates(candidates)

        if not candidates:
            print("No candidates found. Exiting.")
            return

        # Step 3: Analyze and score
        print()
        print("Step 3: Analyzing portfolios...")
        print("-" * 40)
        analyzed = analyzer.analyze_all(candidates)

        # Step 4: Get top results
        top_results = analyzer.get_top_results(analyzed, TOTAL_TOP_RESULTS)
        print(f"Top {len(top_results)} portfolios identified.")

        # Step 5: Generate report
        print()
        print("Step 4: Generating report...")
        print("-" * 40)
        reporter.generate_report(top_results)
        reporter.generate_csv(top_results)

        # Print summary
        print()
        print("=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        print()
        print(f"{'Rank':<6} {'Name':<25} {'Score':<8} {'Role'}")
        print("-" * 60)
        for i, c in enumerate(top_results, 1):
            name = (c.name or "Unknown")[:24]
            score = f"{c.total_score:.1f}"
            role = (c.role or "Designer")[:25]
            print(f"{i:<6} {name:<25} {score:<8} {role}")

        print()
        print("Full report saved to: output/report.md")
        print("CSV export saved to: output/report.csv")

    finally:
        scraper.close()


def main():
    parser = argparse.ArgumentParser(
        description="Search for director-level designer portfolios with minimal aesthetics"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of live web search"
    )

    args = parser.parse_args()
    run_agent(use_mock=args.mock)


if __name__ == "__main__":
    main()
