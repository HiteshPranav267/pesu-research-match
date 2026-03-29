"""
matcher.py — Two-stage matching: BGE-Large chunk retrieval + Cross-Encoder re-ranking.

Upgrades over previous version:
  1. BGE-Large-v1.5 with query instruction prefix
  2. Chunk-based max-pool retrieval (each professor has multiple embeddings)
  3. Query expansion for short/vague queries
  4. Cross-Encoder re-ranking on top candidates

Usage:
    python matcher.py "I am interested in NLP and deep learning"
    python matcher.py "computer vision" --campus RR
"""

import argparse
import json
import re

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder

# ── Models ──
BI_ENCODER_NAME = "BAAI/bge-large-en-v1.5"
CROSS_ENCODER_NAME = "cross-encoder/ms-marco-MiniLM-L-12-v2"

# BGE requires this instruction prefix on QUERIES (not on passages)
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# ── Files ──
EMBEDDINGS_FILE = "professors_embeddings.npy"
CHUNK_MAP_FILE = "professors_chunk_map.json"
INDEX_FILE = "professors_index.json"
TOP_K = 10
RETRIEVAL_POOL = 75  # How many candidates to pull for re-ranking

# ── Query Expansion Synonyms ──
DOMAIN_SYNONYMS = {
    "ml": "machine learning, ML, statistical learning, predictive modeling",
    "machine learning": "ML, statistical learning, deep learning, neural networks",
    "ai": "artificial intelligence, AI, intelligent systems, cognitive computing",
    "artificial intelligence": "AI, intelligent systems, machine learning, deep learning",
    "nlp": "natural language processing, NLP, text mining, computational linguistics, transformers",
    "natural language processing": "NLP, text mining, computational linguistics, language models",
    "cv": "computer vision, CV, image processing, visual recognition, object detection",
    "computer vision": "CV, image processing, visual recognition, pattern recognition",
    "dl": "deep learning, DL, neural networks, CNN, RNN, transformers",
    "deep learning": "DL, neural networks, convolutional networks, deep neural networks",
    "iot": "internet of things, IoT, embedded systems, smart sensors, edge computing",
    "internet of things": "IoT, embedded systems, smart devices, sensor networks",
    "cloud": "cloud computing, distributed systems, serverless, microservices",
    "cloud computing": "cloud, distributed computing, AWS, Azure, virtualization",
    "cyber": "cybersecurity, network security, cryptography, information security",
    "cybersecurity": "cyber security, network security, ethical hacking, penetration testing",
    "data science": "data analytics, big data, data mining, statistical analysis",
    "robotics": "autonomous systems, mechatronics, robot control, motion planning",
    "blockchain": "distributed ledger, cryptocurrency, smart contracts, decentralized",
    "vlsi": "VLSI design, integrated circuits, chip design, semiconductor",
    "signal processing": "DSP, digital signal processing, image processing, filtering",
    "networking": "computer networks, network protocols, wireless networks, SDN",
    "embedded": "embedded systems, microcontrollers, RTOS, firmware, IoT",
    "database": "database management, SQL, NoSQL, data warehousing, DBMS",
    "bioinformatics": "computational biology, genomics, proteomics, biological data",
    "image processing": "digital image processing, computer vision, pattern recognition",
}


def expand_query(raw_query: str) -> str:
    """
    Expand short/vague queries with domain synonyms.

    If the query is already long (e.g., full resume text), skip expansion
    to avoid diluting the signal. For short queries like "I like ML",
    append relevant synonyms to help the embedding model understand intent.
    """
    # Don't expand long queries (resume text, detailed descriptions)
    if len(raw_query.split()) > 40:
        return raw_query

    expanded = raw_query
    query_lower = raw_query.lower()

    # Find matching synonyms
    additions = []
    for keyword, synonyms in DOMAIN_SYNONYMS.items():
        # Check if the keyword appears as a word boundary match
        if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
            additions.append(synonyms)

    if additions:
        expanded = raw_query + ". Related areas: " + "; ".join(additions)

    return expanded


def cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between a 1-D query vector and each row of matrix."""
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    matrix_normed = matrix / matrix_norms
    return matrix_normed @ query_norm


def apply_filters(
    scores: np.ndarray,
    professors: list[dict],
    campus: str | None,
    department: str | None,
) -> np.ndarray:
    """Zero out scores for professors that do not match the given filters."""
    mask = np.ones(len(professors), dtype=bool)
    if campus:
        mask &= np.array(
            [p.get("campus", "").upper() == campus.upper() for p in professors]
        )
    if department:
        mask &= np.array(
            [p.get("department", "").lower() == department.lower() for p in professors]
        )
    result = scores.copy()
    result[~mask] = 0.0
    return result


def build_profile_text(prof: dict) -> str:
    """Build a rich text representation of a professor for cross-encoder input."""
    parts = []

    name = prof.get("name", "").strip()
    title = prof.get("title", "").strip()
    department = prof.get("department", "").strip()

    if name:
        intro = name
        if title:
            intro += f", {title}"
        if department:
            intro += f" ({department})"
        parts.append(intro)

    about = prof.get("About", "").strip()
    if about:
        parts.append(about[:500])

    interests = prof.get("Research Interest", "").strip()
    if interests:
        parts.append(f"Research interests: {interests}")

    projects = prof.get("Research Projects", "").strip()
    if projects:
        parts.append(f"Projects: {projects[:400]}")

    teaching = prof.get("Teaching", "").strip()
    if teaching:
        parts.append(f"Teaches: {teaching}")

    return ". ".join(parts)


class Matcher:
    """Two-stage matcher: BGE chunk retrieval + Cross-Encoder re-ranking."""

    def __init__(self) -> None:
        print("Loading chunk embeddings ...")
        self.embeddings: np.ndarray = np.load(EMBEDDINGS_FILE)

        with open(CHUNK_MAP_FILE, "r", encoding="utf-8") as fh:
            self.chunk_to_prof: list[int] = json.load(fh)

        with open(INDEX_FILE, "r", encoding="utf-8") as fh:
            self.professors: list[dict] = json.load(fh)

        self.num_profs = len(self.professors)
        print(f"Loaded {self.num_profs} professors, {len(self.chunk_to_prof)} chunks.")

        print(f"Loading bi-encoder '{BI_ENCODER_NAME}' ...")
        self.bi_encoder = SentenceTransformer(BI_ENCODER_NAME)

        print(f"Loading cross-encoder '{CROSS_ENCODER_NAME}' ...")
        self.cross_encoder = CrossEncoder(CROSS_ENCODER_NAME)
        print("Matcher ready (BGE + Chunk Max-Pool + Cross-Encoder).")

    def match(
        self,
        query: str,
        campus: str | None = None,
        department: str | None = None,
        top_k: int = TOP_K,
    ) -> list[dict]:
        """
        Three-phase matching:
        1. Query expansion (add domain synonyms for short queries)
        2. Chunk-based retrieval with max-pool (BGE bi-encoder)
        3. Cross-encoder re-ranking of top candidates
        """
        # ── Phase 0: Query Expansion ──
        expanded_query = expand_query(query)

        # ── Phase 1: BGE Chunk Retrieval ──
        # Add BGE instruction prefix to the query
        prefixed_query = BGE_QUERY_PREFIX + expanded_query
        query_vec = self.bi_encoder.encode(
            [prefixed_query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        # Score every chunk
        chunk_scores = cosine_similarity(query_vec, self.embeddings)

        # Max-pool: for each professor, take the highest chunk score
        prof_scores = np.zeros(self.num_profs)
        for chunk_idx, prof_idx in enumerate(self.chunk_to_prof):
            if chunk_scores[chunk_idx] > prof_scores[prof_idx]:
                prof_scores[prof_idx] = chunk_scores[chunk_idx]

        # Apply campus/department filters
        prof_scores = apply_filters(prof_scores, self.professors, campus, department)

        # Get top candidates for re-ranking
        pool_size = min(RETRIEVAL_POOL, self.num_profs)
        candidate_indices = np.argsort(prof_scores)[::-1][:pool_size]
        candidate_indices = [i for i in candidate_indices if prof_scores[i] > 0]

        if not candidate_indices:
            return []

        # ── Phase 2: Cross-Encoder Re-ranking ──
        pairs = []
        for idx in candidate_indices:
            prof_text = build_profile_text(self.professors[idx])
            pairs.append((query, prof_text))  # Use original query, not expanded

        ce_scores = self.cross_encoder.predict(pairs)
        ce_scores_norm = 1 / (1 + np.exp(-np.array(ce_scores)))

        ranked = sorted(
            zip(candidate_indices, ce_scores_norm),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for idx, score in ranked[:top_k]:
            prof = dict(self.professors[idx])
            prof["score"] = round(float(score), 4)
            results.append(prof)

        return results


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Match a student query to professors.")
    parser.add_argument("query", help="Student interest query string")
    parser.add_argument("--campus", help="Filter by campus: RR or EC", default=None)
    parser.add_argument("--department", help="Filter by department name", default=None)
    args = parser.parse_args()

    matcher = Matcher()
    results = matcher.match(args.query, campus=args.campus, department=args.department)

    print(f"\nTop {len(results)} matches for: \"{args.query}\"\n")
    for i, prof in enumerate(results, 1):
        score_pct = prof["score"] * 100
        interests = prof.get("Research Interest", "N/A")
        print(
            f"{i:2}. [{score_pct:5.1f}%] {prof['name']} — {prof['title']}\n"
            f"       {prof['department']} | {prof['campus']} Campus\n"
            f"       Interests: {interests[:80]}\n"
            f"       {prof.get('profile_url', '')}"
        )


if __name__ == "__main__":
    main()
