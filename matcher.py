"""
matcher.py — Cosine-similarity matching engine for professor lookup.

Can be imported by api.py or run standalone:

    python matcher.py "I am interested in NLP and deep learning"
    python matcher.py "computer vision" --campus RR --department "Computer Science"
"""

import argparse
import json

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDINGS_FILE = "professors_embeddings.npy"
INDEX_FILE = "professors_index.json"
TOP_K = 10


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



    """Load embeddings once and serve multiple match queries."""

    def __init__(self) -> None:
        print("Loading professor embeddings ...")
        self.embeddings: np.ndarray = np.load(EMBEDDINGS_FILE)
        with open(INDEX_FILE, "r", encoding="utf-8") as fh:
            self.professors: list[dict] = json.load(fh)
        print(f"Loaded {len(self.professors)} professors.")

        print(f"Loading embedding model '{MODEL_NAME}' ...")
        self.model = SentenceTransformer(MODEL_NAME)
        print("Matcher ready.")

    def match(
        self,
        query: str,
        campus: str | None = None,
        department: str | None = None,
        top_k: int = TOP_K,
    ) -> list[dict]:
        """
        Embed the query and return the top-k matching professors.

        Parameters
        ----------
        query:      Free-text query from the student.
        campus:     Optional campus filter ("RR" or "EC").
        department: Optional department filter (display name, case-insensitive).
        top_k:      Number of results to return.

        Returns
        -------
        List of dicts with professor info + "score" key (float, 0-1).
        """
        query_vec = self.model.encode([query], convert_to_numpy=True)[0]
        scores = cosine_similarity(query_vec, self.embeddings)
        scores = apply_filters(scores, self.professors, campus, department)

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            prof = dict(self.professors[idx])
            prof["score"] = round(score, 4)
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
        print(
            f"{i:2}. [{score_pct:5.1f}%] {prof['name']} — {prof['title']}\n"
            f"       {prof['department']} | {prof['campus']} Campus\n"
            f"       {prof.get('profile_url', '')}"
        )


if __name__ == "__main__":
    main()
