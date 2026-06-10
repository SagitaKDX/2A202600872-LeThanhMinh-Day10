from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src/ to python path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question
from pipelines.phase1 import main as run_phase1_main


class CorruptionRunRequest(BaseModel):
    drop_latest: bool = True
    blank_summaries: bool = True
    inject_noise: bool = True
    truncate_titles: bool = True
    stale_dates: bool = True
    duplicate_rows: bool = True


agent_instance = None
settings_instance = None
index_instance = None
pipeline_running = False
corruption_running = False


def background_run_corruption(req: CorruptionRunRequest):
    global corruption_running, agent_instance, settings_instance, index_instance
    try:
        corruption_running = True
        print("[Server] Starting background corruption flow run...")
        from pipelines.corruption_flow import main as run_corruption_main
        run_corruption_main(
            drop_latest=req.drop_latest,
            blank_summaries=req.blank_summaries,
            inject_noise=req.inject_noise,
            truncate_titles=req.truncate_titles,
            stale_dates=req.stale_dates,
            duplicate_rows=req.duplicate_rows,
        )
        # Reload index and agent
        settings_instance = load_settings()
        index_instance = LocalEmbeddingIndex.load(settings_instance)
        agent_instance = build_agent(settings_instance, index_instance)
        print("[Server] Background corruption flow completed.")
    except Exception as e:
        print(f"[Server] Error in background corruption run: {e}")
    finally:
        corruption_running = False


def background_run_pipeline():
    global pipeline_running, agent_instance, settings_instance, index_instance
    try:
        pipeline_running = True
        print("[Server] Starting background pipeline rerun...")
        run_phase1_main()
        # Reload index and agent
        settings_instance = load_settings()
        index_instance = LocalEmbeddingIndex.load(settings_instance)
        agent_instance = build_agent(settings_instance, index_instance)
        print("[Server] Background pipeline rerun completed successfully.")
    except Exception as e:
        print(f"[Server] Error during background pipeline: {e}")
    finally:
        pipeline_running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance, settings_instance, index_instance
    try:
        settings_instance = load_settings()
        index_instance = LocalEmbeddingIndex.load(settings_instance)
        agent_instance = build_agent(settings_instance, index_instance)
        print("[Server] RAG Agent loaded successfully.")
    except Exception as e:
        print(f"[Server] Startup warning - could not load agent: {e}")
    yield


app = FastAPI(lifespan=lifespan)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(request: ChatRequest):
    global agent_instance
    if not agent_instance:
        raise HTTPException(
            status_code=503,
            detail="Agent is not ready or GOOGLE_API_KEY is not configured.",
        )
    try:
        response = run_agent_question(agent_instance, request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/observability/status")
async def get_status():
    global pipeline_running
    return {"pipeline_running": pipeline_running}


@app.post("/api/pipeline/run")
async def run_pipeline(background_tasks: BackgroundTasks):
    global pipeline_running
    if pipeline_running:
        return {"message": "Pipeline is already running.", "status": "running"}
    background_tasks.add_task(background_run_pipeline)
    return {"message": "Pipeline run started in the background.", "status": "started"}


@app.get("/api/observability/metrics")
async def get_metrics():
    settings = load_settings()
    path = settings.paths.baseline_metrics
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/observability/quality")
async def get_quality():
    settings = load_settings()
    path = settings.paths.quality_dir / "baseline_quality.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/observability/freshness")
async def get_freshness():
    settings = load_settings()
    path = settings.paths.freshness_report
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/observability/report")
async def get_report():
    settings = load_settings()
    path = settings.paths.baseline_report
    if not path.exists():
        return {"report": "Report has not been generated yet."}
    with open(path, "r", encoding="utf-8") as f:
        return {"report": f.read()}


@app.post("/api/corruption/run")
async def run_corruption(req: CorruptionRunRequest, background_tasks: BackgroundTasks):
    global corruption_running, pipeline_running
    if corruption_running or pipeline_running:
        return {"message": "Pipeline or corruption flow is already running.", "status": "running"}
    background_tasks.add_task(background_run_corruption, req)
    return {"message": "Corruption flow started in the background.", "status": "started"}


@app.get("/api/corruption/status")
async def get_corruption_status():
    global corruption_running
    return {"corruption_running": corruption_running}


@app.get("/api/corruption/results")
async def get_corruption_results():
    settings = load_settings()
    
    def read_json_safe(path):
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    report_content = ""
    if settings.paths.comparison_report.exists():
        with open(settings.paths.comparison_report, "r", encoding="utf-8") as f:
            report_content = f.read()
            
    corrupted_quality = read_json_safe(settings.paths.quality_dir / "corrupted_quality.json")
    repaired_quality = read_json_safe(settings.paths.quality_dir / "repaired_quality.json")
    corrupted_freshness = read_json_safe(settings.paths.quality_dir / "freshness_report_corrupted.json")
    repaired_freshness = read_json_safe(settings.paths.quality_dir / "freshness_report_repaired.json")
            
    return {
        "baseline_metrics": read_json_safe(settings.paths.baseline_metrics),
        "corrupted_metrics": read_json_safe(settings.paths.corrupted_metrics),
        "repaired_metrics": read_json_safe(settings.paths.repaired_metrics),
        "corrupted_quality": corrupted_quality,
        "repaired_quality": repaired_quality,
        "corrupted_freshness": corrupted_freshness,
        "repaired_freshness": repaired_freshness,
        "report": report_content
    }


# Mount the static frontend files
app.mount("/", StaticFiles(directory="fe", html=True), name="static")
