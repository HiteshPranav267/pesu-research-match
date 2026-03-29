"""
api.py — FastAPI backend for ResearchMatch (BGE + Chunk + Cross-Encoder).

Usage:
    uvicorn api:app --reload --port 8000
"""

import json
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, CrossEncoder

from matcher import (
    apply_filters,
    cosine_similarity,
    build_profile_text,
    expand_query,
    BI_ENCODER_NAME,
    CROSS_ENCODER_NAME,
    BGE_QUERY_PREFIX,
    RETRIEVAL_POOL,
)

EMBEDDINGS_FILE = "professors_embeddings.npy"
CHUNK_MAP_FILE = "professors_chunk_map.json"
INDEX_FILE = "professors_index.json"
TOP_K = 10

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

professors: list[dict] = []
embeddings: np.ndarray = np.array([])
chunk_to_prof: list[int] = []
num_profs: int = 0
bi_encoder: Optional[SentenceTransformer] = None
cross_encoder: Optional[CrossEncoder] = None


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global professors, embeddings, chunk_to_prof, num_profs, bi_encoder, cross_encoder

    print("Loading professor index ...")
    with open(INDEX_FILE, "r", encoding="utf-8") as fh:
        professors = json.load(fh)
    num_profs = len(professors)
    print(f"  Loaded {num_profs} professors.")

    print("Loading chunk embeddings ...")
    embeddings = np.load(EMBEDDINGS_FILE)
    print(f"  Embeddings shape: {embeddings.shape}")

    print("Loading chunk map ...")
    with open(CHUNK_MAP_FILE, "r", encoding="utf-8") as fh:
        chunk_to_prof = json.load(fh)
    print(f"  {len(chunk_to_prof)} chunks mapped.")

    print(f"Loading bi-encoder '{BI_ENCODER_NAME}' ...")
    bi_encoder = SentenceTransformer(BI_ENCODER_NAME)
    print("  Bi-encoder ready.")

    print(f"Loading cross-encoder '{CROSS_ENCODER_NAME}' ...")
    cross_encoder = CrossEncoder(CROSS_ENCODER_NAME)
    print("  Cross-encoder ready.")

    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="ResearchMatch API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchRequest(BaseModel):
    query: str
    campus: Optional[str] = None
    department: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def read_root():
    return FileResponse("index.html")


@app.get("/professors")
def get_professors(
    campus: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None),
):
    result = professors
    if campus:
        result = [p for p in result if p.get("campus", "").upper() == campus.upper()]
    if department:
        result = [p for p in result if p.get("department", "").lower() == department.lower()]
    return result


@app.get("/departments")
def get_departments(campus: Optional[str] = Query(default=None)):
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
    """
    Three-phase matching:
    1. Query expansion (domain synonyms for short queries)
    2. BGE chunk retrieval with max-pool
    3. Cross-encoder re-ranking
    """
    if bi_encoder is None or cross_encoder is None or embeddings.size == 0:
        raise HTTPException(status_code=503, detail="Models not yet loaded.")

    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    # ── Phase 0: Query Expansion ──
    expanded_query = expand_query(req.query)

    # ── Phase 1: BGE Chunk Retrieval + Max-Pool ──
    prefixed_query = BGE_QUERY_PREFIX + expanded_query
    query_vec = bi_encoder.encode(
        [prefixed_query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0]

    chunk_scores = cosine_similarity(query_vec, embeddings)

    # Max-pool per professor
    prof_scores = np.zeros(num_profs)
    for chunk_idx, prof_idx in enumerate(chunk_to_prof):
        if chunk_scores[chunk_idx] > prof_scores[prof_idx]:
            prof_scores[prof_idx] = chunk_scores[chunk_idx]

    prof_scores = apply_filters(prof_scores, professors, req.campus, req.department)

    pool_size = min(RETRIEVAL_POOL, num_profs)
    candidate_indices = np.argsort(prof_scores)[::-1][:pool_size]
    candidate_indices = [i for i in candidate_indices if prof_scores[i] > 0]

    if not candidate_indices:
        return {"results": []}

    # ── Phase 2: Cross-Encoder Re-ranking ──
    pairs = []
    for idx in candidate_indices:
        prof_text = build_profile_text(professors[idx])
        pairs.append((req.query, prof_text))

    ce_scores = cross_encoder.predict(pairs)
    ce_scores_norm = 1 / (1 + np.exp(-np.array(ce_scores)))

    ranked = sorted(
        zip(candidate_indices, ce_scores_norm),
        key=lambda x: x[1],
        reverse=True,
    )

    results = []
    for idx, score in ranked[:TOP_K]:
        prof = dict(professors[idx])
        prof["score"] = round(float(score), 4)
        results.append(prof)

    return {"results": results}
