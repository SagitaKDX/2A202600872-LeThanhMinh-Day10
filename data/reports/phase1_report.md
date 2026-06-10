# Baseline Data Pipeline & Observability Report

Generated on: 2026-06-10T08:30:57.822992+00:00

## 📊 Source API Data Extraction Summary
- **Source Endpoint**: Crossref REST API
- **Search Query**: `agentic retrieval augmented generation large language model`
- **Max Results Target**: 24
- **Total Records Extracted**: 23

## 🔍 Retrieval & QA Evaluation Metrics
- **Total Samples Tested**: 20
- **Retrieval Hit Rate (Top-K)**: 100.0%
- **Mean Token F1 Score**: 100.0%
- **Judge Correctness Accuracy**: 100.0%
- **Mean LLM Judge Score (1-5)**: 5.00/5.0

### Ragas Pass Evaluation:
- `Set RUN_RAGAS=1 to enable the slower Ragas pass.` (Configured via `RUN_RAGAS` env var)

## 🛠 Data Quality checks
- **Status**: 🟢 PASS
- **Total Cleaned Rows**: 23
- **Missing Paper ID Count**: 0
- **Is Paper ID Unique?**: Yes
- **Missing Title Count**: 0
- **Short Summaries Count (<20 chars)**: 0

## 📅 Freshness Monitoring Report
- **Status**: 🟢 FRESH
- **Latest Published Paper**: 2026-06-02
- **Oldest Published Paper**: 2025-12-19
- **Total Stale Rows**: 0