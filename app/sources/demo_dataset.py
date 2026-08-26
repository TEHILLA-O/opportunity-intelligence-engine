"""Synthetic, realistic opportunity records used by the mock connector and demo."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.config import get_settings

ORGANISATIONS = [
    "Northbridge Digital Services",
    "Westborough Housing Partnership",
    "Cedar Finance Group",
    "Eastmere Borough Services",
    "Thornfield Analytics Ltd",
    "Harbourline Logistics",
    "Ashford Civic Authority",
    "Meridian Health Trust",
    "Oakridge Procurement Office",
    "Silverstream Energy",
    "Pendleton Research Institute",
    "Blackwood Municipal Council",
    "Rivermead Education Consortium",
    "Foxwell Transport Authority",
    "Greystone Utilities",
    "Haverford Data Cooperative",
    "Elmhurst Social Care Trust",
    "Kingswell Water Partnership",
    "Bramley Heritage Foundation",
    "Southmere Digital Authority",
]

TITLES = [
    "Python Data Extraction Automation",
    "Supplier Data Normalisation Service",
    "Document Processing Workflow Development",
    "Internal Reporting Automation",
    "Procurement Data Integration Support",
    "ETL Pipeline Modernisation",
    "API Integration and Workflow Orchestration",
    "Web Scraping Quality Assurance Framework",
    "Contract Opportunity Monitoring Platform",
    "PostgreSQL Reporting Warehouse Build",
    "FastAPI Case Management Service",
    "Scheduled Data Collection Engine",
    "Invoice Parsing and Validation Service",
    "Grant Application Tracking Dashboard",
    "Supplier Onboarding Automation",
    "Tender Portal Data Consolidation",
    "Python Test Automation for ETL Jobs",
    "Records Digitisation Workflow",
    "Business Process Automation Discovery",
    "Secure File Transfer and Ingestion Service",
    "WordPress Brochure Site Redesign",
    "Graphic Design for Campaign Assets",
    "Logo Design and Brand Refresh",
    "Shopify Storefront Theme Customisation",
]

CATEGORIES = [
    "software-development",
    "data-engineering",
    "automation",
    "integration",
    "analytics",
    "procurement",
    "infrastructure",
    "graphic-design",
]

LOCATIONS = [
    "London, United Kingdom",
    "Manchester, UK",
    "Birmingham",
    "Leeds, England",
    "Remote, United Kingdom",
    "Hybrid - Glasgow",
    "Cardiff, Wales",
    "Edinburgh",
    "Bristol",
    "UK-wide",
    "Newcastle upon Tyne",
]

CONTRACTS = [
    "Fixed-price contract",
    "Time and materials",
    "Framework call-off",
    "Grant funded engagement",
    "Subcontract",
    "RFQ",
    "Contract",
]

SKILLS = [
    ["Python", "SQL", "ETL"],
    ["Python", "FastAPI", "PostgreSQL"],
    ["Playwright", "Python", "pytest"],
    ["Pandas", "SQLAlchemy", "Airflow"],
    ["httpx", "BeautifulSoup", "data extraction"],
    ["WordPress", "PHP"],
    ["Graphic design", "Adobe"],
]

CONTACTS = [
    ("Amelia Hart", "procurement@{slug}.example"),
    ("Daniel Okoye", "contracts@{slug}.example"),
    ("Priya Raman", "tenders@{slug}.example"),
    ("James Whitlock", "commercial@{slug}.example"),
]


def _slug(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "" for ch in name.split()[0])


def _description(title: str, org: str, extra: str) -> str:
    return (
        f"{org} is seeking a supplier to deliver {title.lower()} across operational teams. "
        f"The engagement covers collection from multiple source systems, structured extraction, "
        f"validation, and repeatable reporting. {extra} "
        f"Bidders should demonstrate production Python automation, responsible data collection, "
        f"and an auditable pipeline rather than one-off scripts."
    )


def generate_records(*, seed: int = 42, mutate: bool = False) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    now = datetime.now(UTC)
    records: list[dict[str, Any]] = []
    sequence = 0

    def add(record: dict[str, Any]) -> None:
        nonlocal sequence
        sequence += 1
        record.setdefault("external_id", f"DEMO-{sequence:04d}")
        records.append(record)

    for index in range(180):
        org = ORGANISATIONS[index % len(ORGANISATIONS)]
        title = TITLES[index % (len(TITLES) - 4)]  # keep design titles for later
        location = LOCATIONS[index % len(LOCATIONS)]
        category = CATEGORIES[index % (len(CATEGORIES) - 1)]
        contract = CONTRACTS[index % len(CONTRACTS)]
        skills = SKILLS[index % (len(SKILLS) - 2)]
        contact = CONTACTS[index % len(CONTACTS)]
        value = rng.randint(8, 240) * 1000
        deadline = now + timedelta(days=rng.randint(-12, 75))
        extra = (
            "Work must be delivered against a documented run history and source health checks."
            if index % 3 == 0
            else "Emphasis is placed on idempotent re-runs and duplicate detection."
        )
        add(
            {
                "title": title if index % 17 else f"{title} — Phase {(index % 3) + 1}",
                "organisation": org,
                "description": _description(title, org, extra),
                "location": location,
                "value": f"£{value:,}" if index % 11 else f"GBP {value} - {value + 25000}",
                "deadline": deadline.strftime("%Y-%m-%d" if index % 2 else "%d/%m/%Y"),
                "category": category,
                "contact_name": contact[0],
                "contact_email": contact[1].format(slug=_slug(org)),
                "requirements": f"Experience with {', '.join(skills)} and production automation.",
                "skills": skills,
                "url": f"https://opportunities.example.invalid/{_slug(org)}/{index + 1}",
                "metadata": {
                    "status": "open" if deadline > now else "expired",
                    "contract_type": contract,
                    "published_at": (now - timedelta(days=rng.randint(1, 40))).date().isoformat(),
                    "category": category,
                },
            }
        )

    # Exact duplicates (same source ID later applied by cloning external_id)
    original = records[4]
    add(
        {
            **original,
            "external_id": original["external_id"],
            "title": original["title"],
            "url": original["url"],
        }
    )
    add(
        {
            **records[9],
            "external_id": "DEMO-DUP-URL",
            "url": records[9]["url"],
        }
    )

    # Near-duplicate titles
    add(
        {
            "title": "Python Data Extraction Automation Programme",
            "organisation": records[0]["organisation"],
            "description": records[0]["description"],
            "location": records[0]["location"],
            "value": records[0]["value"],
            "deadline": records[0]["deadline"],
            "category": records[0]["category"],
            "contact_name": records[0]["contact_name"],
            "contact_email": records[0]["contact_email"],
            "requirements": records[0]["requirements"],
            "skills": records[0]["skills"],
            "url": "https://opportunities.example.invalid/near-duplicate/extraction",
            "metadata": records[0]["metadata"],
        }
    )

    # Same title, different organisation — should not auto-merge
    add(
        {
            **{k: records[12][k] for k in records[12]},
            "external_id": "DEMO-DIFF-ORG",
            "organisation": "Kingswell Water Partnership",
            "url": "https://opportunities.example.invalid/kingswell/extraction-support",
        }
    )

    # Excluded-keyword low scorers
    for offset, title in enumerate(TITLES[-4:]):
        add(
            {
                "title": title,
                "organisation": ORGANISATIONS[offset],
                "description": f"{ORGANISATIONS[offset]} requires {title.lower()} for a marketing campaign.",
                "location": "London",
                "value": "£4,500",
                "deadline": (now + timedelta(days=20)).strftime("%Y-%m-%d"),
                "category": "graphic-design",
                "contact_name": "Studio Desk",
                "contact_email": "studio@northbridge.example",
                "requirements": "Portfolio of brand work.",
                "skills": ["Graphic design"],
                "url": f"https://opportunities.example.invalid/creative/{offset}",
                "metadata": {
                    "status": "open",
                    "contract_type": "fixed-price",
                    "category": "graphic-design",
                },
            }
        )

    # Malformed records
    add(
        {
            "title": "",
            "organisation": "Eastmere Borough Services",
            "description": "Missing title should be rejected.",
            "location": "Leeds",
            "value": "£25,000",
            "deadline": "2026-09-01",
            "url": "https://opportunities.example.invalid/invalid/missing-title",
            "metadata": {},
        }
    )
    add(
        {
            "title": "Broken URL Procurement Feed",
            "organisation": "Oakridge Procurement Office",
            "description": "This record uses an invalid URL and should be captured as an ingestion error.",
            "location": "Reading",
            "value": "not-a-price",
            "deadline": "first Friday after Michaelmas",
            "url": "notaurl",
            "metadata": {},
        }
    )
    add(
        {
            "title": "Malformed Currency Tender",
            "organisation": "Greystone Utilities",
            "description": "Python automation for meter data collection. Value field is intentionally messy.",
            "location": "Bristol",
            "value": "approx lots of money",
            "deadline": "31/12/2026",
            "url": "https://opportunities.example.invalid/greystone/malformed-currency",
            "metadata": {"status": "open", "contract_type": "contract"},
        }
    )

    # High-scoring Python automation set
    for index, org in enumerate(ORGANISATIONS[:8]):
        add(
            {
                "title": "Python Automation and ETL Platform Support",
                "organisation": org,
                "description": _description(
                    "Python automation and ETL platform support",
                    org,
                    "FastAPI services, SQLAlchemy persistence and Playwright smoke checks are in scope.",
                ),
                "location": "Remote, United Kingdom",
                "value": f"£{85000 + index * 5000:,}",
                "deadline": (now + timedelta(days=12 + index)).strftime("%Y-%m-%d"),
                "category": "automation",
                "contact_name": "Automation Desk",
                "contact_email": f"automation@{_slug(org)}.example",
                "requirements": "Python, ETL, FastAPI, PostgreSQL, scraping, data extraction.",
                "skills": ["Python", "ETL", "FastAPI", "SQL"],
                "url": f"https://opportunities.example.invalid/high-score/{index}",
                "metadata": {
                    "status": "open",
                    "contract_type": "fixed-price contract",
                    "category": "automation",
                    "published_at": (now - timedelta(days=5)).date().isoformat(),
                },
            }
        )

    if mutate:
        for record in records:
            if record.get("external_id") in {"DEMO-0007", "DEMO-0015", "DEMO-0028"}:
                record["deadline"] = (now + timedelta(days=2)).strftime("%Y-%m-%d")
                record["value"] = "£125,000"
                record["description"] = (
                    record.get("description") or ""
                ) + " Deadline brought forward by the buyer."

    return records


def write_demo_files(directory: Path | None = None) -> Path:
    settings = get_settings()
    target = directory or settings.demo_data_dir
    target.mkdir(parents=True, exist_ok=True)
    records = generate_records()
    (target / "mock_opportunities.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    json_subset = records[20:40]
    (target / "sample_feed.json").write_text(
        json.dumps({"items": json_subset}, indent=2), encoding="utf-8"
    )
    rss_items = "\n".join(
        (
            "    <item>\n"
            f"      <title>{_xml(item['title'])}</title>\n"
            f"      <link>{_xml(item['url'])}</link>\n"
            f"      <guid>{_xml(item.get('external_id') or item['url'])}</guid>\n"
            f"      <description>{_xml(item.get('description') or '')}</description>\n"
            f"      <author>{_xml(item.get('organisation') or '')}</author>\n"
            "    </item>"
        )
        for item in records[40:55]
    )
    (target / "sample_feed.rss").write_text(
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<rss version='2.0'><channel>\n"
        "<title>Sample Opportunity Feed</title>\n"
        f"{rss_items}\n"
        "</channel></rss>\n",
        encoding="utf-8",
    )
    html_rows = "\n".join(
        (
            "<article class='opportunity'>"
            f"<h2><a href='{item['url']}'>{item['title']}</a></h2>"
            f"<p class='org'>{item.get('organisation') or ''}</p>"
            f"<p class='desc'>{item.get('description') or ''}</p>"
            f"<p class='meta'>Value: {item.get('value') or ''} | Deadline: {item.get('deadline') or ''}"
            f" | Location: {item.get('location') or ''}</p>"
            "</article>"
        )
        for item in records[55:70]
    )
    (target / "sample_listing.html").write_text(
        "<html><body><main>" + html_rows + "</main></body></html>",
        encoding="utf-8",
    )
    mutated = generate_records(mutate=True)
    (target / "mock_opportunities_updated.json").write_text(
        json.dumps(mutated, indent=2), encoding="utf-8"
    )
    return target


def _xml(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def load_demo_records(*, mutate: bool = False) -> list[dict[str, Any]]:
    settings = get_settings()
    path = settings.demo_data_dir / (
        "mock_opportunities_updated.json" if mutate else "mock_opportunities.json"
    )
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return generate_records(mutate=mutate)
