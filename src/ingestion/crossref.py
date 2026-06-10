from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


import re

def clean_abstract(text: str | None) -> str:
    if not text:
        return ""
    # Strip HTML/XML tags
    cleaned = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_crossref_date(date_dict: dict | None) -> str | None:
    if not date_dict or "date-parts" not in date_dict:
        return None
    try:
        parts = date_dict["date-parts"][0]
        if not parts:
            return None
        year = parts[0]
        month = parts[1] if len(parts) > 1 else 1
        day = parts[2] if len(parts) > 2 else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    except (IndexError, TypeError, ValueError):
        return None


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into a list of PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records = []
    
    for item in items:
        # DOI is the unique identifier
        doi = item.get("DOI", "")
        if not doi:
            continue
            
        # Title is a list, take the first one
        titles = item.get("title", [])
        title = ""
        if isinstance(titles, list) and len(titles) > 0:
            title = str(titles[0]).strip()
        elif isinstance(titles, str):
            title = titles.strip()
            
        if not title:
            continue
            
        # Abstract
        abstract = clean_abstract(item.get("abstract"))
        if not abstract:
            continue
            
        # Authors: list of dicts with given and family names
        raw_authors = item.get("author", [])
        authors = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, dict):
                    given = a.get("given", "").strip()
                    family = a.get("family", "").strip()
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)
                    elif a.get("name"):
                        authors.append(str(a.get("name")).strip())

        # Categories
        categories = item.get("subject", [])
        if not isinstance(categories, list):
            categories = [categories] if categories else []
        categories = [str(c).strip() for c in categories if c]
        
        primary_category = categories[0] if categories else "scholarly"
        
        # Date of publication
        published = (
            parse_crossref_date(item.get("published-online"))
            or parse_crossref_date(item.get("published-print"))
            or parse_crossref_date(item.get("issued"))
            or parse_crossref_date(item.get("created"))
            or "1970-01-01"
        )
        
        # Updated date
        updated = parse_crossref_date(item.get("updated")) or published
        
        # URLs
        abs_url = item.get("URL") or f"https://doi.org/{doi}"
        
        # Find PDF URL in links
        pdf_url = ""
        links = item.get("link", [])
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    if "pdf" in link.get("content-type", "").lower():
                        pdf_url = link.get("URL", "")
                        break
                        
        # Comment: use container title or publisher
        container_titles = item.get("container-title", [])
        comment = ""
        if isinstance(container_titles, list) and len(container_titles) > 0:
            comment = str(container_titles[0]).strip()
        elif isinstance(container_titles, str):
            comment = container_titles.strip()
            
        if not comment:
            comment = item.get("publisher", "") or ""
            
        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=abstract,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Call external source API, save raw response, parse to records."""
    import time
    import requests
    from core.utils import write_json
    
    url = "https://api.crossref.org/works"
    
    # Setup query parameters
    params = {
        "query": settings.source_query,
        "rows": settings.max_results,
        "mailto": "student@example.com"  # Polite pool identification
    }
    
    if settings.source_filter:
        params["filter"] = settings.source_filter
        
    headers = {
        "User-Agent": "DataPipelineAgent/1.0 (mailto:student@example.com)"
    }
    
    max_retries = 3
    backoff_factor = 2
    payload = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                payload = response.json()
                break
            elif response.status_code in (429, 503):
                time.sleep(backoff_factor ** attempt)
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(backoff_factor ** attempt)
            
    if payload is None:
        raise RuntimeError("Failed to fetch works from Crossref API after retries.")
        
    # Ensure parents and save raw API response
    write_json(settings.paths.raw_api_response, payload)
    
    # Parse payload to PaperRecord objects
    records = parse_crossref_payload(payload)
    
    # Save raw records as JSON list
    from dataclasses import asdict
    records_dict = [asdict(r) for r in records]
    write_json(settings.paths.raw_records_json, records_dict)
    
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load JSON snapshot and map to PaperRecord objects."""
    from core.utils import read_json
    if not path.exists():
        return []
        
    payload = read_json(path)
    records = []
    for data in payload:
        records.append(
            PaperRecord(
                paper_id=data["paper_id"],
                title=data["title"],
                summary=data["summary"],
                authors=data["authors"],
                categories=data["categories"],
                primary_category=data["primary_category"],
                published=data["published"],
                updated=data["updated"],
                abs_url=data["abs_url"],
                pdf_url=data["pdf_url"],
                comment=data["comment"]
            )
        )
    return records
