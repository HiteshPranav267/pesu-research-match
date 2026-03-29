"""
api.py — FastAPI backend for ResearchMatch.

Usage:
    uvicorn api:app --reload --port 8000

Endpoints:
    GET  /professors          — list all professors (optional ?campus= / ?department=)
    GET  /departments         — unique departments per campus (optional ?campus=)
    POST /match               — match a student query to professors
"""

import json
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

from matcher import apply_filters

EMBEDDINGS_FILE = "professors_embeddings.npy"
INDEX_FILE = "professors_index.json"
TOP_K = 10

# ---------------------------------------------------------------------------
# Globals (loaded once at startup)
# ---------------------------------------------------------------------------

professors: list[dict] = []
embeddings: np.ndarray = np.array([])
model: Optional[SentenceTransformer] = None


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for the FastAPI application.

    Loads the professor index, pre-computed embeddings, and the sentence-transformer
    model once at startup so every request can reuse them without re-loading.
    No explicit cleanup is required on shutdown.
    """
    global professors, embeddings, model

    print("Loading professor index ...")
    with open(INDEX_FILE, "r", encoding="utf-8") as fh:
        professors = json.load(fh)
    print(f"  Loaded {len(professors)} professors.")

    print("Loading embeddings ...")
    embeddings = np.load(EMBEDDINGS_FILE)
    print(f"  Embeddings shape: {embeddings.shape}")

    print(f"Loading embedding model '{MODEL_NAME}' ...")
    model = SentenceTransformer(MODEL_NAME)
    print("  Model ready.")

    yield  # Application runs here

    # Shutdown: nothing special to do


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="ResearchMatch API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class MatchRequest(BaseModel):
    query: str
    campus: Optional[str] = None
    department: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    matrix_normed = matrix / matrix_norms
    return matrix_normed @ query_norm


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/professors")
def get_professors(
    campus: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None),
):
    """Return all professors, optionally filtered by campus and/or department."""
    result = professors
    if campus:
        result = [p for p in result if p.get("campus", "").upper() == campus.upper()]
    if department:
        result = [p for p in result if p.get("department", "").lower() == department.lower()]
    return result


@app.get("/departments")
def get_departments(campus: Optional[str] = Query(default=None)):
    """Return unique departments, grouped by campus."""
    filtered = professors
    if campus:
        filtered = [p for p in filtered if p.get("campus", "").upper() == campus.upper()]

    dept_map: dict[str, set] = {}
    for p in filtered:
        c = p.get("campus", "Unknown")
        d = p.get("department", "Unknown")
        dept_map.setdefault(c, set()).add(d)

    return {c: sorted(depts) for c, depts in dept_map.items()}


@app.post("/match")
def match_professors(req: MatchRequest):
    """Embed a student query and return top-10 matching professors."""
    if model is None or embeddings.size == 0:
        raise HTTPException(status_code=503, detail="Model not yet loaded.")

    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    query_vec = model.encode([req.query], convert_to_numpy=True)[0]
    scores = cosine_similarity(query_vec, embeddings)
    scores = apply_filters(scores, professors, req.campus, req.department)

    top_indices = np.argsort(scores)[::-1][:TOP_K]
    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        prof = dict(professors[idx])
        prof["score"] = round(score, 4)
        results.append(prof)

    return {"results": results}
