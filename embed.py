"""
embed.py — Generate sentence embeddings for all professors and save to disk.

Usage:
    python embed.py

Prerequisites:
    python scraper.py   (produces professors.json)

Outputs:
    professors_embeddings.npy  — numpy array of shape (N, 384)
    professors_index.json      — ordered list of professor dicts (same order as embeddings)

Note:
    The first run will download the all-MiniLM-L6-v2 model (~80 MB).
    Subsequent runs use the cached model.
"""

import json

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
INPUT_FILE = "professors.json"
EMBEDDINGS_FILE = "professors_embeddings.npy"
INDEX_FILE = "professors_index.json"


def build_text(professor: dict) -> str:
    """Create the text string used for embedding a professor."""
    name = professor.get("name", "")
    title = professor.get("title", "")
    department = professor.get("department", "")
    campus = professor.get("campus", "")
    return f"{name} - {title} - {department} - {campus} Campus"


def main() -> None:
    print(f"Loading professors from {INPUT_FILE} ...")
    with open(INPUT_FILE, "r", encoding="utf-8") as fh:
        professors: list[dict] = json.load(fh)

    print(f"Loaded {len(professors)} professors.")

    texts = [build_text(p) for p in professors]

    print(f"Loading model '{MODEL_NAME}' (first run downloads ~80 MB) ...")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings ...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    np.save(EMBEDDINGS_FILE, embeddings)
    print(f"Embeddings saved to {EMBEDDINGS_FILE}  shape={embeddings.shape}")

    with open(INDEX_FILE, "w", encoding="utf-8") as fh:
        json.dump(professors, fh, ensure_ascii=False, indent=2)
    print(f"Professor index saved to {INDEX_FILE}")


if __name__ == "__main__":
    main()
