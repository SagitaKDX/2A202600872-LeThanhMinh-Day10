// Corruption Page Controller & API Manager
let corruptionInterval = null;

async function initCorruption() {
    console.log("Initializing Corruption dashboard...");
    clearInterval(corruptionInterval);
    
    // Load existing metrics and report
    await fetchCorruptionResults();
    
    // Check initial running status
    await checkCorruptionRunningStatus();
}

async function fetchCorruptionResults() {
    try {
        const res = await fetch("/api/corruption/results");
        if (!res.ok) throw new Error("Could not fetch corruption comparison data.");
        
        const data = await res.json();
        renderCorruptionResults(data);
    } catch (e) {
        console.error("Error loading corruption results:", e);
    }
}

function renderCorruptionResults(data) {
    const formatPercent = (val) => (val !== undefined && val !== null) ? `${(val * 100).toFixed(1)}%` : "-";
    const formatScore = (val) => (val !== undefined && val !== null) ? `${val.toFixed(2)}/5.0` : "-";
    
    // 1. Render baseline metrics (just to be safe, though they should be 100% / 5.0)
    if (data.baseline_metrics && Object.keys(data.baseline_metrics).length > 0) {
        document.getElementById("m-baseline-hitrate").innerText = formatPercent(data.baseline_metrics.retrieval_hit_rate);
        document.getElementById("m-baseline-f1").innerText = formatPercent(data.baseline_metrics.mean_token_f1);
        document.getElementById("m-baseline-accuracy").innerText = formatPercent(data.baseline_metrics.judge_accuracy);
        document.getElementById("m-baseline-score").innerText = formatScore(data.baseline_metrics.mean_judge_score);
    }

    // 2. Render corrupted metrics
    if (data.corrupted_metrics && Object.keys(data.corrupted_metrics).length > 0) {
        document.getElementById("m-corrupted-hitrate").innerText = formatPercent(data.corrupted_metrics.retrieval_hit_rate);
        document.getElementById("m-corrupted-f1").innerText = formatPercent(data.corrupted_metrics.mean_token_f1);
        document.getElementById("m-corrupted-accuracy").innerText = formatPercent(data.corrupted_metrics.judge_accuracy);
        document.getElementById("m-corrupted-score").innerText = formatScore(data.corrupted_metrics.mean_judge_score);
    } else {
        document.getElementById("m-corrupted-hitrate").innerText = "-";
        document.getElementById("m-corrupted-f1").innerText = "-";
        document.getElementById("m-corrupted-accuracy").innerText = "-";
        document.getElementById("m-corrupted-score").innerText = "-";
    }

    // 3. Render repaired metrics
    if (data.repaired_metrics && Object.keys(data.repaired_metrics).length > 0) {
        document.getElementById("m-repaired-hitrate").innerText = formatPercent(data.repaired_metrics.retrieval_hit_rate);
        document.getElementById("m-repaired-f1").innerText = formatPercent(data.repaired_metrics.mean_token_f1);
        document.getElementById("m-repaired-accuracy").innerText = formatPercent(data.repaired_metrics.judge_accuracy);
        document.getElementById("m-repaired-score").innerText = formatScore(data.repaired_metrics.mean_judge_score);
    } else {
        document.getElementById("m-repaired-hitrate").innerText = "-";
        document.getElementById("m-repaired-f1").innerText = "-";
        document.getElementById("m-repaired-accuracy").innerText = "-";
        document.getElementById("m-repaired-score").innerText = "-";
    }

    // 4. Render Data Quality Badges
    const badgeQualityCorrupted = document.getElementById("m-corrupted-quality");
    if (data.corrupted_quality && Object.keys(data.corrupted_quality).length > 0) {
        const pass = data.corrupted_quality.success;
        badgeQualityCorrupted.innerText = pass ? "PASS" : "FAIL";
        badgeQualityCorrupted.className = pass ? "badge badge-success" : "badge badge-error";
    } else {
        badgeQualityCorrupted.innerText = "-";
        badgeQualityCorrupted.className = "badge badge-neutral";
    }

    const badgeQualityRepaired = document.getElementById("m-repaired-quality");
    if (data.repaired_quality && Object.keys(data.repaired_quality).length > 0) {
        const pass = data.repaired_quality.success;
        badgeQualityRepaired.innerText = pass ? "PASS" : "FAIL";
        badgeQualityRepaired.className = pass ? "badge badge-success" : "badge badge-error";
    } else {
        badgeQualityRepaired.innerText = "-";
        badgeQualityRepaired.className = "badge badge-neutral";
    }

    // 5. Render Freshness Badges
    const badgeFreshnessCorrupted = document.getElementById("m-corrupted-freshness");
    if (data.corrupted_freshness && Object.keys(data.corrupted_freshness).length > 0) {
        const fresh = data.corrupted_freshness.is_fresh;
        badgeFreshnessCorrupted.innerText = fresh ? "FRESH" : "STALE";
        badgeFreshnessCorrupted.className = fresh ? "badge badge-success" : "badge badge-warning";
    } else {
        badgeFreshnessCorrupted.innerText = "-";
        badgeFreshnessCorrupted.className = "badge badge-neutral";
    }

    const badgeFreshnessRepaired = document.getElementById("m-repaired-freshness");
    if (data.repaired_freshness && Object.keys(data.repaired_freshness).length > 0) {
        const fresh = data.repaired_freshness.is_fresh;
        badgeFreshnessRepaired.innerText = fresh ? "FRESH" : "STALE";
        badgeFreshnessRepaired.className = fresh ? "badge badge-success" : "badge badge-warning";
    } else {
        badgeFreshnessRepaired.innerText = "-";
        badgeFreshnessRepaired.className = "badge badge-neutral";
    }

    // 6. Render Report Markdown
    const reportPre = document.getElementById("report-pre-text-corruption");
    if (data.report) {
        reportPre.innerText = data.report;
    } else {
        reportPre.innerText = "Run the Corruption & Repair Flow to generate the comparison report.";
    }
}

async function triggerCorruptionRun() {
    const body = {
        drop_latest: document.getElementById("chk-drop-latest").checked,
        blank_summaries: document.getElementById("chk-blank-summaries").checked,
        inject_noise: document.getElementById("chk-inject-noise").checked,
        truncate_titles: document.getElementById("chk-truncate-titles").checked,
        stale_dates: document.getElementById("chk-stale-dates").checked,
        duplicate_rows: document.getElementById("chk-duplicate-rows").checked
    };

    const runBtn = document.getElementById("btn-run-corruption");
    if (!runBtn) return;

    try {
        runBtn.disabled = true;
        runBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Triggering...`;

        const res = await fetch("/api/corruption/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        const data = await res.json();
        if (data.status === "started") {
            startCorruptionPolling();
        } else {
            alert(data.message || "Failed to start corruption flow.");
            runBtn.disabled = false;
            runBtn.innerHTML = `<i class="fa-solid fa-play"></i> Run Corruption & Repair Flow`;
        }
    } catch (e) {
        console.error("Error triggering corruption run:", e);
        runBtn.disabled = false;
        runBtn.innerHTML = `<i class="fa-solid fa-play"></i> Run Corruption & Repair Flow`;
    }
}

function startCorruptionPolling() {
    const runBtn = document.getElementById("btn-run-corruption");
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = `<i class="fa-solid fa-arrows-rotate fa-spin"></i> Processing RAG Pipeline (Corruption -> Evaluate -> Repair)...`;
    }

    clearInterval(corruptionInterval);
    corruptionInterval = setInterval(async () => {
        try {
            const res = await fetch("/api/corruption/status");
            const data = await res.json();
            
            if (!data.corruption_running) {
                clearInterval(corruptionInterval);
                if (runBtn) {
                    runBtn.disabled = false;
                    runBtn.innerHTML = `<i class="fa-solid fa-play"></i> Run Corruption & Repair Flow`;
                }
                // Fetch fresh results
                await fetchCorruptionResults();
            }
        } catch (e) {
            console.error("Error polling corruption status:", e);
        }
    }, 4000);
}

async function checkCorruptionRunningStatus() {
    try {
        const res = await fetch("/api/corruption/status");
        const data = await res.json();
        if (data.corruption_running) {
            startCorruptionPolling();
        }
    } catch (e) {
        console.error("Error checking initial running status:", e);
    }
}

function copyCorruptionReport() {
    const reportText = document.getElementById("report-pre-text-corruption").innerText;
    navigator.clipboard.writeText(reportText).then(() => {
        alert("Comparison Markdown Report copied to clipboard!");
    }).catch(err => {
        console.error("Failed to copy report: ", err);
    });
}
