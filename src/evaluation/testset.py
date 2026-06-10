from __future__ import annotations

from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Generate evaluation test set from cleaned dataframe."""
    from core.utils import write_json, first_sentence
    
    if len(df) < 1:
        raise ValueError("Cleaned dataset is empty. Cannot generate a test set.")
        
    # Select up to 5 representative papers
    num_papers = min(len(df), 5)
    selected_df = df.head(num_papers)
    
    test_set = []
    counter = 1
    
    for _, row in selected_df.iterrows():
        title = row["title"]
        paper_id = row["paper_id"]
        
        # 1. Who authored ...
        test_set.append({
            "id": f"q_{counter}",
            "question_type": "authors",
            "question": f"Who authored the paper '{title}'?",
            "ground_truth": row["authors_joined"] if pd.notna(row["authors_joined"]) else "",
            "ground_truth_doc_ids": [paper_id]
        })
        counter += 1
        
        # 2. When was ...
        test_set.append({
            "id": f"q_{counter}",
            "question_type": "date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": str(row["published"]) if pd.notna(row["published"]) else "",
            "ground_truth_doc_ids": [paper_id]
        })
        counter += 1
        
        # 3. What categories ...
        test_set.append({
            "id": f"q_{counter}",
            "question_type": "categories",
            "question": f"What categories are associated with the paper '{title}'?",
            "ground_truth": row["categories_joined"] if pd.notna(row["categories_joined"]) else "",
            "ground_truth_doc_ids": [paper_id]
        })
        counter += 1
        
        # 4. What is the summary ...
        summary = row["summary"] if pd.notna(row["summary"]) else ""
        test_set.append({
            "id": f"q_{counter}",
            "question_type": "summary",
            "question": f"What is the summary of the paper '{title}'?",
            "ground_truth": first_sentence(summary),
            "ground_truth_doc_ids": [paper_id]
        })
        counter += 1
        
    write_json(output_path, test_set)
    return test_set

