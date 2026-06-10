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


agent_instance = None
settings_instance = None
index_instance = None
pipeline_running = False


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


# Mount the static frontend files
app.mount("/", StaticFiles(directory="fe", html=True), name="static")
