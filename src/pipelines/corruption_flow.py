from __future__ import annotations

import pandas as pd
from datetime import datetime

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json, read_json
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report


def main(
    drop_latest: bool = True,
    blank_summaries: bool = True,
    inject_noise: bool = True,
    truncate_titles: bool = True,
    stale_dates: bool = True,
    duplicate_rows: bool = True,
) -> None:
    """End-to-end corruption, evaluation, repair, and comparison pipeline."""
    # 1. Load settings
    print("Step 1: Loading settings...")
    settings = load_settings()
    
    # 2. Load baseline metrics & clean dataset
    print("Step 2: Loading baseline dataset...")
    if not settings.paths.clean_csv.exists():
        raise FileNotFoundError(
            f"Baseline clean CSV not found at {settings.paths.clean_csv}. "
            "Please run run_phase1.py first to build baseline data."
        )
    df_clean = pd.read_csv(settings.paths.clean_csv).fillna("")
    
    if not settings.paths.baseline_metrics.exists():
        raise FileNotFoundError(
            f"Baseline metrics not found at {settings.paths.baseline_metrics}. "
            "Please run run_phase1.py first."
        )
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"Loaded baseline clean dataset of size: {len(df_clean)}")
    
    # 3. Create corrupted dataframe
    print("Step 3: Creating corrupted dataset...")
    df_corrupted = corrupt_clean_dataframe(
        df_clean,
        settings.paths.corruption_log,
        drop_latest=drop_latest,
        blank_summaries=blank_summaries,
        inject_noise=inject_noise,
        truncate_titles=truncate_titles,
        stale_dates=stale_dates,
        duplicate_rows=duplicate_rows,
    )
    print(f"Corrupted dataset created of size: {len(df_corrupted)}")
    
    # 4. Save corrupted artifacts
    print("Step 4: Saving corrupted CSV/JSON...")
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, df_corrupted.to_dict(orient="records"))
    
    # 5. Rebuild embedding index for corrupted dataset
    print("Step 5: Building embedding index for corrupted dataset...")
    corrupted_index = LocalEmbeddingIndex.build(
        df_corrupted,
        settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    
    # 6. Evaluate corrupted RAG pipeline
    print("Step 6: Evaluating corrupted pipeline...")
    corrupted_eval_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f"Corrupted summary metrics: {corrupted_eval_bundle.summary}")
    
    # 7. Run quality checks on corrupted dataset
    print("Step 7: Running quality checks on corrupted dataset...")
    corrupted_quality = run_data_quality_checks(
        df_corrupted,
        settings,
        report_name="corrupted_quality",
    )
    corrupted_freshness_path = settings.paths.quality_dir / "freshness_report_corrupted.json"
    corrupted_freshness = build_freshness_report(
        df_corrupted,
        settings,
        corrupted_freshness_path,
    )
    
    # 8. Repair data by loading raw records and cleaning from scratch
    print("Step 8: Repairing dataset from raw source cache...")
    raw_records_path = settings.paths.raw_records_json
    if not raw_records_path.exists():
        raise FileNotFoundError(f"Raw records cache not found at {raw_records_path}")
    raw_records = load_raw_records(raw_records_path)
    
    run_date = now_utc()
    df_repaired = build_clean_dataframe(raw_records, run_date)
    print(f"Repaired dataset created of size: {len(df_repaired)}")
    
    # 9. Save repaired CSV/JSON
    print("Step 9: Saving repaired CSV/JSON...")
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, df_repaired.to_dict(orient="records"))
    
    # 10. Rebuild embedding index for repaired dataset
    print("Step 10: Building embedding index for repaired dataset...")
    repaired_index = LocalEmbeddingIndex.build(
        df_repaired,
        settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    
    # 11. Evaluate repaired RAG pipeline
    print("Step 11: Evaluating repaired pipeline...")
    repaired_eval_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print(f"Repaired summary metrics: {repaired_eval_bundle.summary}")
    
    # 12. Run quality checks on repaired dataset
    print("Step 12: Running quality checks on repaired dataset...")
    repaired_quality = run_data_quality_checks(
        df_repaired,
        settings,
        report_name="repaired_quality",
    )
    repaired_freshness_path = settings.paths.quality_dir / "freshness_report_repaired.json"
    repaired_freshness = build_freshness_report(
        df_repaired,
        settings,
        repaired_freshness_path,
    )
    
    # 13. Generate comparison markdown report
    print("Step 13: Generating comparison report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval_bundle.summary,
        repaired_metrics=repaired_eval_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"Comparison report written to: {settings.paths.comparison_report}")
    print("\n--- Corruption & Repair flow pipeline completed successfully! ---")

