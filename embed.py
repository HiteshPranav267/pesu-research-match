"""
embed.py — Generate chunk-based embeddings using BGE-Large-v1.5.

Instead of one embedding per professor, we create separate embeddings for
each semantic field (identity, research interests, projects, teaching, about).
At query time, the matcher takes the MAX score across all chunks for each
professor — so the most relevant section wins, and noise doesn't drag it down.

Usage:
    python embed.py

Outputs:
    professors_embeddings.npy   — (total_chunks, 1024) array
    professors_chunk_map.json   — maps each chunk index to its professor index
    professors_index.json       — ordered professor dicts
"""

import json

import numpy as np
from sentence_transformers import SentenceTransformer

# ── BGE-Large-v1.5: SOTA retrieval model ──
MODEL_NAME = "BAAI/bge-large-en-v1.5"

# BGE models perform better when passages are prefixed with this instruction
PASSAGE_PREFIX = ""  # No prefix for passages (only queries get a prefix)

INPUT_FILE = "professors.json"
EMBEDDINGS_FILE = "professors_embeddings.npy"
CHUNK_MAP_FILE = "professors_chunk_map.json"
INDEX_FILE = "professors_index.json"


def build_chunks(professor: dict) -> list[str]:
    """
    Build separate text chunks for each semantic field of a professor.
    Each chunk becomes its own embedding vector. At query time, the
    max similarity across all chunks determines the professor's score.
    """
    chunks = []

    name = professor.get("name", "").strip()
    title = professor.get("title", "").strip()
    department = professor.get("department", "").strip()
    campus = professor.get("campus", "").strip()

    # ── Chunk 1: Identity (always present) ──
    identity = name
    if title:
        identity += f", {title}"
    if department:
        identity += f" in {department}"
    if campus:
        identity += f" at PES University {campus} Campus"
    chunks.append(identity)

    # ── Chunk 2: Research Interests (highest signal) ──
    interests = professor.get("Research Interest", "").strip()
    if interests:
        chunks.append(f"{name} research interests: {interests}")

    # ── Chunk 3: About / Biography ──
    about = professor.get("About", "").strip()
    if about:
        # Truncate very long bios to keep embedding focused
        chunks.append(f"{name}: {about[:800]}")

    # ── Chunk 4: Research Projects ──
    projects = professor.get("Research Projects", "").strip()
    if projects:
        chunks.append(f"{name} research projects: {projects[:600]}")

    # ── Chunk 5: Teaching ──
    teaching = professor.get("Teaching", "").strip()
    if teaching:
        chunks.append(f"{name} teaches: {teaching}")

    # ── Chunk 6: Education ──
    education = professor.get("Education", "").strip()
    if education:
        chunks.append(f"{name} education: {education[:400]}")

    return chunks


def main() -> None:
    print(f"Loading professors from {INPUT_FILE} ...")
    with open(INPUT_FILE, "r", encoding="utf-8") as fh:
        professors: list[dict] = json.load(fh)

    print(f"Loaded {len(professors)} professors.")

    # Build all chunks and track which professor each chunk belongs to
    all_chunks: list[str] = []
    chunk_to_prof: list[int] = []  # chunk_index -> professor_index

    for prof_idx, prof in enumerate(professors):
        chunks = build_chunks(prof)
        for chunk_text in chunks:
            all_chunks.append(chunk_text)
            chunk_to_prof.append(prof_idx)

    print(f"Built {len(all_chunks)} chunks from {len(professors)} professors")
    print(f"  Average chunks per professor: {len(all_chunks) / len(professors):.1f}")

    # Show a sample
    sample_prof = professors[0].get("name", "Unknown")
    sample_chunks = [c for i, c in enumerate(all_chunks) if chunk_to_prof[i] == 0]
    print(f"\n── Sample chunks for '{sample_prof}' ──")
    for i, c in enumerate(sample_chunks):
        print(f"  Chunk {i+1}: {c[:100]}...")

    print(f"\nLoading model '{MODEL_NAME}' (first run downloads ~1.3 GB) ...")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings for all chunks ...")
    embeddings = model.encode(
        all_chunks,
        show_progress_bar=True,
        convert_to_numpy=True,
        batch_size=16,
        normalize_embeddings=True,  # BGE works best with normalized vectors
    )

    np.save(EMBEDDINGS_FILE, embeddings)
    print(f"Embeddings saved to {EMBEDDINGS_FILE}  shape={embeddings.shape}")

    with open(CHUNK_MAP_FILE, "w", encoding="utf-8") as fh:
        json.dump(chunk_to_prof, fh)
    print(f"Chunk map saved to {CHUNK_MAP_FILE}  ({len(chunk_to_prof)} entries)")

    with open(INDEX_FILE, "w", encoding="utf-8") as fh:
        json.dump(professors, fh, ensure_ascii=False, indent=2)
    print(f"Professor index saved to {INDEX_FILE}")


if __name__ == "__main__":
    main()
