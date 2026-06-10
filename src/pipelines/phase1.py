from __future__ import annotations


from datetime import datetime
import pandas as pd
from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe


def main() -> None:
    """baseline pipeline end-to-end (implemented crawl & clean)."""
    # 1. Load settings
    print("Step 1: Loading settings...")
    settings = load_settings()
    
    # 2. Load or fetch raw records
    print("Step 2: Crawling raw records from Crossref API or loading from cache...")
    raw_records_path = settings.paths.raw_records_json
    
    if settings.refresh_source or not raw_records_path.exists():
        print(f"refresh_source is True or cache does not exist. Fetching from Crossref API...")
        records = fetch_source_records(settings)
    else:
        print(f"Loading raw records from local cache: {raw_records_path}")
        records = load_raw_records(raw_records_path)
        
    print(f"Successfully loaded {len(records)} raw records.")
    
    # 3. Clean data
    print("Step 3: Cleaning data...")
    run_date = now_utc()
    df_clean = build_clean_dataframe(records, run_date)
    print(f"Data cleaned. Columns: {list(df_clean.columns)}")
    print(f"Number of cleaned records: {len(df_clean)}")
    
    # 4. Save clean CSV/JSON
    print("Step 4: Saving clean CSV and JSON...")
    write_csv(df_clean, settings.paths.clean_csv)
    clean_records = df_clean.to_dict(orient="records")
    write_json(settings.paths.clean_json, clean_records)
    print(f"Saved cleaned CSV to: {settings.paths.clean_csv}")
    print(f"Saved cleaned JSON to: {settings.paths.clean_json}")
    
    # 5. Generate evaluation test set
    print("Step 5: Generating evaluation test set...")
    from evaluation.testset import build_test_set
    test_set = build_test_set(df_clean, settings.paths.eval_testset)
    print(f"Generated test set with {len(test_set)} questions at {settings.paths.eval_testset}")
    
    print("\n--- Crawl, Clean & Test Set Generation completed successfully! ---")
    print("Steps 6-10 (Index building, Evaluation, Quality/Freshness checks, Reporting) are not implemented yet.")
    raise NotImplementedError("Student task: implement remaining steps of phase1 pipeline.")


