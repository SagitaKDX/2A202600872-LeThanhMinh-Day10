from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write Phase 1 baseline report to a markdown file."""
    from pathlib import Path
    from core.utils import write_text

    md = f"""# Baseline Data Pipeline & Observability Report

Generated on: {source_summary.get("run_date", "N/A")}

## 📊 Source API Data Extraction Summary
- **Source Endpoint**: {source_summary.get("source_api", "N/A")}
- **Search Query**: `{source_summary.get("source_query", "N/A")}`
- **Max Results Target**: {source_summary.get("max_results", "N/A")}
- **Total Records Extracted**: {source_summary.get("total_raw_records", "N/A")}

## 🔍 Retrieval & QA Evaluation Metrics
- **Total Samples Tested**: {metrics.get("samples", 0)}
- **Retrieval Hit Rate (Top-K)**: {metrics.get("retrieval_hit_rate", 0.0) * 100:.1f}%
- **Mean Token F1 Score**: {metrics.get("mean_token_f1", 0.0) * 100:.1f}%
- **Judge Correctness Accuracy**: {metrics.get("judge_accuracy", 0.0) * 100:.1f}%
- **Mean LLM Judge Score (1-5)**: {metrics.get("mean_judge_score", 0.0):.2f}/5.0

### Ragas Pass Evaluation:
- `{metrics.get("ragas", {}).get("skipped", "N/A")}` (Configured via `RUN_RAGAS` env var)

## 🛠 Data Quality checks
- **Status**: {"🟢 PASS" if quality.get("success") else "🔴 FAIL"}
- **Total Cleaned Rows**: {quality.get("total_rows", 0)}
- **Missing Paper ID Count**: {quality.get("null_paper_id_count", 0)}
- **Is Paper ID Unique?**: {"Yes" if quality.get("is_unique_paper_id") else "No"}
- **Missing Title Count**: {quality.get("null_title_count", 0)}
- **Short Summaries Count (<20 chars)**: {quality.get("short_summaries_count", 0)}

## 📅 Freshness Monitoring Report
- **Status**: {"🟢 FRESH" if freshness.get("is_fresh") else "🟡 STALE"}
- **Latest Published Paper**: {freshness.get("latest_published", "N/A")}
- **Oldest Published Paper**: {freshness.get("oldest_published", "N/A")}
- **Total Stale Rows**: {freshness.get("stale_rows", 0)}
""".strip()
    
    write_text(Path(report_path), md)



def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """TODO(student): viet markdown report so sanh baseline/corrupted/repaired."""
    raise NotImplementedError("Student task: implement corruption comparison report.")
