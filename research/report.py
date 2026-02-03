"""Report generation for designer portfolio research."""

from datetime import datetime
from pathlib import Path
from scraper import PortfolioCandidate


class ReportGenerator:
    """Generates markdown reports from analyzed portfolios."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_report(
        self,
        candidates: list[PortfolioCandidate],
        filename: str = "report.md"
    ) -> str:
        """Generate a markdown report with top designer portfolios."""
        report_lines = [
            "# Designer Portfolio Research Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Overview",
            "",
            "This report identifies director-level designers with minimal design aesthetics,",
            "ranked by a weighted scoring system evaluating role seniority, design style,",
            "portfolio quality, company reputation, and site performance.",
            "",
            "---",
            "",
            "## Top 10 Designer Portfolios",
            "",
            self._generate_table(candidates),
            "",
            "---",
            "",
            "## Scoring Methodology",
            "",
            "| Criteria | Weight | Description |",
            "|----------|--------|-------------|",
            "| Role Level | 30% | Seniority of design role (Director, VP, Head of) |",
            "| Minimal Aesthetic | 25% | Clean, minimal design indicators |",
            "| Portfolio Quality | 20% | Depth of case studies and content |",
            "| Company Reputation | 15% | Notable company associations |",
            "| Site Performance | 10% | Technical site characteristics |",
            "",
            "---",
            "",
            "## Detailed Results",
            "",
            self._generate_detailed_results(candidates),
        ]

        report_content = "\n".join(report_lines)

        # Write to file
        output_path = self.output_dir / filename
        output_path.write_text(report_content)

        print(f"Report saved to: {output_path}")
        return report_content

    def _generate_table(self, candidates: list[PortfolioCandidate]) -> str:
        """Generate the main results table."""
        lines = [
            "| Rank | Name | Role | Company | Score | Portfolio |",
            "|------|------|------|---------|-------|-----------|",
        ]

        for i, candidate in enumerate(candidates[:10], 1):
            name = candidate.name or "Unknown"
            role = candidate.role or "Designer"
            company = candidate.company or "Independent"
            score = f"{candidate.total_score:.1f}/10"
            url = f"[Link]({candidate.url})"

            # Truncate long values
            name = name[:25] + "..." if len(name) > 25 else name
            role = role[:25] + "..." if len(role) > 25 else role
            company = company[:20] + "..." if len(company) > 20 else company

            lines.append(f"| {i} | {name} | {role} | {company} | {score} | {url} |")

        return "\n".join(lines)

    def _generate_detailed_results(self, candidates: list[PortfolioCandidate]) -> str:
        """Generate detailed breakdown for each candidate."""
        sections = []

        for i, candidate in enumerate(candidates[:10], 1):
            section = [
                f"### {i}. {candidate.name or 'Unknown'}",
                "",
                f"**Role:** {candidate.role or 'Designer'}",
                f"**Company:** {candidate.company or 'Independent'}",
                f"**URL:** {candidate.url}",
                "",
                "**Score Breakdown:**",
                "",
                "| Criteria | Score |",
                "|----------|-------|",
            ]

            for criteria, score in candidate.scores.items():
                criteria_name = criteria.replace("_", " ").title()
                section.append(f"| {criteria_name} | {score:.1f}/10 |")

            section.extend([
                "",
                f"**Total Score:** {candidate.total_score:.1f}/10",
                "",
                "**Snippet:**",
                f"> {candidate.snippet[:200]}..." if len(candidate.snippet) > 200 else f"> {candidate.snippet}",
                "",
                "---",
                "",
            ])

            sections.append("\n".join(section))

        return "\n".join(sections)

    def generate_csv(
        self,
        candidates: list[PortfolioCandidate],
        filename: str = "report.csv"
    ) -> str:
        """Generate a CSV version of the report."""
        lines = [
            "rank,name,role,company,total_score,role_score,minimal_score,quality_score,company_score,performance_score,url"
        ]

        for i, c in enumerate(candidates[:10], 1):
            row = [
                str(i),
                f'"{c.name}"',
                f'"{c.role}"',
                f'"{c.company}"',
                f"{c.total_score:.2f}",
                f"{c.scores.get('role_level', 0):.2f}",
                f"{c.scores.get('minimal_aesthetic', 0):.2f}",
                f"{c.scores.get('portfolio_quality', 0):.2f}",
                f"{c.scores.get('company_reputation', 0):.2f}",
                f"{c.scores.get('site_performance', 0):.2f}",
                f'"{c.url}"',
            ]
            lines.append(",".join(row))

        csv_content = "\n".join(lines)

        output_path = self.output_dir / filename
        output_path.write_text(csv_content)

        print(f"CSV saved to: {output_path}")
        return csv_content
