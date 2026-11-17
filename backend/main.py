"""
FastAPI Backend Application for MedVerify.
Exposes endpoints for Adaptive Clinical QA, Observability Telemetry, and 3-Way Benchmarking.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import json

from config import PUBMED_DATA_FILE
from pipeline import MedVerifyPipeline

app = FastAPI(
    title="MedVerify API",
    description="Adaptive RAG, Cross-Encoder Reranking, and Hallucination Guardrails for Clinical QA",
    version="2.0.0"
)

# Enable CORS for React Frontend (vite default port 5173 / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = MedVerifyPipeline()


class QueryRequest(BaseModel):
    query: str


class BenchmarkRequest(BaseModel):
    query: str


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MedVerify Engine", "version": "2.0.0"}


@app.get("/api/scenarios")
def get_scenarios():
    """Returns curated clinical trial scenarios from the dataset."""
    try:
        with open(PUBMED_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            {
                "id": d["id"],
                "question": d["question"],
                "specialty": d.get("specialty", "Clinical Medicine"),
                "query_type": d.get("query_type", "clinical_evidence"),
                "gold_decision": d.get("final_decision", "yes")
            }
            for d in data
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def process_query(req: QueryRequest):
    """Executes the complete MedVerify Adaptive RAG pipeline on a question."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        result = pipeline.run_adaptive_pipeline(req.query.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/benchmark")
def run_benchmark(req: BenchmarkRequest):
    """Executes 3-way baseline benchmark (No-RAG vs Fixed-RAG vs MedVerify)."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        result = pipeline.run_3way_benchmark(req.query.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
