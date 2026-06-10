// Observability Dashboard Logic Controller
let statusPollInterval = null;

function initObservability() {
    // 1. Fetch all pipeline details & populate cards
    loadDashboardMetrics();

    // 2. Clear any old polling timers and check if pipeline is currently active
    if (statusPollInterval) clearInterval(statusPollInterval);
    checkPipelinePolling();
}

// Fetch all reports & metrics dynamically
async function loadDashboardMetrics() {
    try {
        const [qualityRes, freshnessRes, metricsRes, reportRes] = await Promise.all([
            fetch("/api/observability/quality"),
            fetch("/api/observability/freshness"),
            fetch("/api/observability/metrics"),
            fetch("/api/observability/report")
        ]);

        // 1. Populate Data Quality Card
        if (qualityRes.ok) {
            const data = await qualityRes.json();
            document.getElementById("val-quality-total-rows").innerText = data.total_rows ?? "0";
            document.getElementById("val-quality-null-ids").innerText = data.null_paper_id_count ?? "0";
            document.getElementById("val-quality-unique-ids").innerText = data.is_unique_paper_id === false ? "No" : "Yes";
            document.getElementById("val-quality-null-titles").innerText = data.null_title_count ?? "0";

            const badge = document.getElementById("badge-quality-status");
            if (data.success) {
                badge.className = "badge badge-success";
                badge.innerText = "PASS";
            } else {
                badge.className = "badge badge-warning";
                badge.innerText = "FAIL";
            }
        }

        // 2. Populate Freshness Card
        if (freshnessRes.ok) {
            const data = await freshnessRes.json();
            document.getElementById("val-freshness-latest").innerText = data.latest_published ?? "N/A";
            document.getElementById("val-freshness-oldest").innerText = data.oldest_published ?? "N/A";
            document.getElementById("val-freshness-stale").innerText = data.stale_rows ?? "0";

            const badge = document.getElementById("badge-freshness-status");
            if (data.is_fresh) {
                badge.className = "badge badge-success";
                badge.innerText = "FRESH";
            } else {
                badge.className = "badge badge-warning";
                badge.innerText = "STALE";
            }
        }

        // 3. Populate Evaluation Metrics Card
        if (metricsRes.ok) {
            const data = await metricsRes.json();
            const hitRate = data.retrieval_hit_rate ? (data.retrieval_hit_rate * 100).toFixed(1) + "%" : "0%";
            const tokenF1 = data.mean_token_f1 ? (data.mean_token_f1 * 100).toFixed(1) + "%" : "0%";
            const accuracy = data.judge_accuracy ? (data.judge_accuracy * 100).toFixed(1) + "%" : "0%";
            const score = data.mean_judge_score ? data.mean_judge_score.toFixed(2) + "/5.0" : "0.00/5.0";

            document.getElementById("val-eval-hitrate").innerText = hitRate;
            document.getElementById("val-eval-f1").innerText = tokenF1;
            document.getElementById("val-eval-accuracy").innerText = accuracy;
            document.getElementById("val-eval-score").innerText = score;
        }

        // 4. Populate Markdown Report
        if (reportRes.ok) {
            const data = await reportRes.json();
            document.getElementById("report-pre-text").innerText = data.report || "No report content found.";
        }

    } catch (e) {
        console.error("Error loading dashboard metrics:", e);
    }
}

// Trigger Pipeline Rerun
async function triggerPipelineRun() {
    const btn = document.getElementById("btn-run-pipeline");
    if (!btn) return;

    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-arrows-rotate fa-spin"></i> Running Pipeline...`;

    try {
        const res = await fetch("/api/pipeline/run", { method: "POST" });
        const data = await res.json();
        
        // Notify global indicator immediately
        pollPipelineStatusGlobal();
        
        // Start polling for completions
        checkPipelinePolling();
    } catch (e) {
        console.error("Error triggering pipeline rerun:", e);
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-play"></i> Rerun Pipeline`;
    }
}

// Background status checking
function checkPipelinePolling() {
    if (statusPollInterval) clearInterval(statusPollInterval);

    statusPollInterval = setInterval(async () => {
        try {
            const res = await fetch("/api/observability/status");
            const data = await res.json();
            const btn = document.getElementById("btn-run-pipeline");

            if (!data.pipeline_running) {
                // Pipeline finished! Stop polling & refresh metrics dashboard
                clearInterval(statusPollInterval);
                statusPollInterval = null;
                
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-play"></i> Rerun Pipeline`;
                }

                loadDashboardMetrics();
                pollPipelineStatusGlobal();
            } else {
                // Pipeline is currently running: lock run button
                if (btn && !btn.disabled) {
                    btn.disabled = true;
                    btn.innerHTML = `<i class="fa-solid fa-arrows-rotate fa-spin"></i> Running Pipeline...`;
                }
            }
        } catch (e) {
            console.error("Error polling run status:", e);
        }
    }, 2000);
}

// Copy Markdown Report Helper
function copyReport() {
    const reportText = document.getElementById("report-pre-text").innerText;
    navigator.clipboard.writeText(reportText).then(() => {
        alert("Observability markdown report copied to clipboard!");
    }).catch(err => {
        console.error("Could not copy report text:", err);
    });
}
