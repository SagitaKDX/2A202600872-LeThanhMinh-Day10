from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


from core.utils import normalize_whitespace, compact_join


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records and construct a pandas DataFrame ready for embedding.

    Follows these steps:
    1. Normalize whitespaces in titles and summaries.
    2. Filter out incomplete or short records.
    3. Parse the publication date to compute age in days relative to the run date.
    4. Create joins for authors and categories.
    5. Construct the formatted `text_for_embedding` search content column.
    6. Drop duplicates (by DOI/paper_id and case-insensitive title).
    7. Sort descending by publication date and ascending by title.
    """
    if not records:
        # Return an empty DataFrame with the expected columns
        columns = [
            "paper_id", "title", "summary", "authors", "categories",
            "primary_category", "published", "updated", "abs_url",
            "pdf_url", "comment", "authors_joined", "categories_joined",
            "summary_chars", "age_days", "text_for_embedding"
        ]
        return pd.DataFrame(columns=columns)

    processed = []
    for r in records:
        title = normalize_whitespace(r.title) if r.title else ""
        summary = normalize_whitespace(r.summary) if r.summary else ""

        # Discard invalid records: missing essential fields or summary is too short
        if not r.paper_id or not title or not summary or len(summary) < 20:
            continue

        authors_joined = compact_join(r.authors, ", ")
        categories_joined = compact_join(r.categories, ", ")
        summary_chars = len(summary)

        # Parse publication date to calculate age in days
        try:
            pub_date = datetime.strptime(r.published, "%Y-%m-%d").date()
            age_days = (run_date.date() - pub_date).days
        except Exception:
            age_days = 9999

        # Construct helper search content block
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Categories: {categories_joined}\n"
            f"Published: {r.published}\n"
            f"Summary: {summary}"
        )

        processed.append({
            "paper_id": r.paper_id,
            "title": title,
            "summary": summary,
            "authors": r.authors,
            "categories": r.categories,
            "primary_category": r.primary_category,
            "published": r.published,
            "updated": r.updated,
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment,
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": summary_chars,
            "age_days": age_days,
            "text_for_embedding": text_for_embedding
        })

    df = pd.DataFrame(processed)

    if not df.empty:
        # Deduplicate by DOI (paper_id)
        df = df.drop_duplicates(subset=["paper_id"], keep="first")
        # Deduplicate by case-insensitive title
        df["title_lower"] = df["title"].str.lower()
        df = df.drop_duplicates(subset=["title_lower"], keep="first")
        df = df.drop(columns=["title_lower"])

        # Sort descending by published date, and ascending alphabetically by title
        df = df.sort_values(by=["published", "title"], ascending=[False, True])
        df = df.reset_index(drop=True)

    return df
