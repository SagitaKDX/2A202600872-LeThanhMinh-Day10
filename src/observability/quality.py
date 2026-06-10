from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Perform baseline data quality checks on the papers DataFrame."""
    from pathlib import Path
    from core.utils import write_json
    
    total_rows = len(df)
    null_paper_id = df["paper_id"].isnull().sum()
    unique_paper_ids = df["paper_id"].nunique()
    is_unique_paper_id = bool(unique_paper_ids == total_rows)
    
    null_title = df["title"].isnull().sum()
    
    # Check summary lengths: summary should be at least 20 chars
    short_summaries = (df["summary"].str.len() < 20).sum()
    
    # Check freshness: papers should not exceed the freshness threshold age
    stale_rows = (df["age_days"] > settings.freshness_threshold_days).sum()
    
    success = bool(
        total_rows > 0 and
        null_paper_id == 0 and
        is_unique_paper_id and
        null_title == 0 and
        short_summaries == 0 and
        stale_rows == 0
    )
    
    report = {
        "report_name": report_name,
        "total_rows": total_rows,
        "null_paper_id_count": int(null_paper_id),
        "is_unique_paper_id": is_unique_paper_id,
        "null_title_count": int(null_title),
        "short_summaries_count": int(short_summaries),
        "stale_rows_count": int(stale_rows),
        "freshness_threshold_days": settings.freshness_threshold_days,
        "success": success
    }
    
    report_file = settings.paths.quality_dir / f"{report_name}.json"
    write_json(report_file, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Generate aggregate freshness report from the papers DataFrame."""
    from pathlib import Path
    from core.utils import write_json
    
    if df.empty:
        latest_pub = "N/A"
        oldest_pub = "N/A"
        stale_rows = 0
        total_rows = 0
        is_fresh = False
    else:
        latest_pub = str(df["published"].max())
        oldest_pub = str(df["published"].min())
        total_rows = len(df)
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
        is_fresh = bool(stale_rows == 0)
        
    payload = {
        "latest_published": latest_pub,
        "oldest_published": oldest_pub,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }
    
    write_json(Path(report_path), payload)
    return payload

