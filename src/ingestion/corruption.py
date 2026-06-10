from __future__ import annotations

import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate various types of data corruption on a cleaned DataFrame.

    Corruption types:
    1. Drop some latest records.
    2. Blank summary on some rows.
    3. Inject noise into summary.
    4. Truncate title.
    5. Make published date stale.
    6. Add duplicate rows.
    7. Rebuild text_for_embedding.
    8. Write corruption log to output_log_path.
    """
    from pathlib import Path
    from core.utils import write_json
    
    df_corrupted = df.copy()
    
    # 1. Drop top 2 latest records
    dropped_records = df_corrupted.iloc[:2].to_dict(orient="records")
    df_corrupted = df_corrupted.iloc[2:].reset_index(drop=True)
    
    # 2. Blank summary at some rows
    blank_indices = [0, 1]
    blanked_ids = []
    for idx in blank_indices:
        if idx < len(df_corrupted):
            blanked_ids.append(df_corrupted.loc[idx, "paper_id"])
            df_corrupted.loc[idx, "summary"] = ""
            df_corrupted.loc[idx, "summary_chars"] = 0
            
    # 3. Inject noise into summary
    noise_indices = [2, 3]
    noised_ids = []
    for idx in noise_indices:
        if idx < len(df_corrupted):
            noised_ids.append(df_corrupted.loc[idx, "paper_id"])
            df_corrupted.loc[idx, "summary"] = "CORRUPTED ERROR SUMMARY REDACTED NOISE 12345"
            df_corrupted.loc[idx, "summary_chars"] = len(df_corrupted.loc[idx, "summary"])
            
    # 4. Truncate title
    truncate_indices = [4, 5]
    truncated_ids = []
    for idx in truncate_indices:
        if idx < len(df_corrupted):
            truncated_ids.append(df_corrupted.loc[idx, "paper_id"])
            df_corrupted.loc[idx, "title"] = df_corrupted.loc[idx, "title"][:10]
            
    # 5. Make published date stale
    stale_indices = [6, 7]
    stale_ids = []
    for idx in stale_indices:
        if idx < len(df_corrupted):
            stale_ids.append(df_corrupted.loc[idx, "paper_id"])
            df_corrupted.loc[idx, "published"] = "1995-01-01"
            df_corrupted.loc[idx, "age_days"] = 11000
            
    # 6. Add duplicate rows
    duplicate_indices = [8, 9]
    duplicated_ids = []
    if len(df_corrupted) > 10:
        dups = df_corrupted.iloc[duplicate_indices].copy()
        for _, row in dups.iterrows():
            duplicated_ids.append(row["paper_id"])
        df_corrupted = pd.concat([df_corrupted, dups], ignore_index=True)
        
    # 7. Rebuild text_for_embedding
    for idx, row in df_corrupted.iterrows():
        title = row["title"]
        authors_joined = row["authors_joined"]
        categories_joined = row["categories_joined"]
        published = row["published"]
        summary = row["summary"]
        
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Categories: {categories_joined}\n"
            f"Published: {published}\n"
            f"Summary: {summary}"
        )
        df_corrupted.loc[idx, "text_for_embedding"] = text_for_embedding

    # 8. Write corruption log
    log = {
        "dropped_papers": [r["paper_id"] for r in dropped_records],
        "blanked_summary_papers": blanked_ids,
        "noised_summary_papers": noised_ids,
        "truncated_title_papers": truncated_ids,
        "stale_published_papers": stale_ids,
        "duplicated_papers": duplicated_ids,
    }
    write_json(Path(output_log_path), log)
    
    return df_corrupted
