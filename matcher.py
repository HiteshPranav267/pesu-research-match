import json
import numpy as np
import torch
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

EMBED_MODEL_NAME = "BAAI/bge-large-en-v1.5"


def _minmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    if x.size == 0:
        return x
    mn, mx = float(x.min()), float(x.max())
    diff = mx - mn
    if diff < 1e-9:
        return np.zeros_like(x, dtype=np.float32)
    return (x - mn) / diff


def _tokenize(s: str):
    return s.lower().strip().replace("|", " ").replace(",", " ").split()


class ProfessorMatcher:
    def __init__(
        self,
        docs_path="professor_docs.json",
        embeddings_path="professor_embeddings.npy",
        w_dense=0.4,
        w_bm25=0.6,
    ):
        self.docs_path = docs_path
        self.embeddings_path = embeddings_path
        self.w_dense = w_dense
        self.w_bm25 = w_bm25

        with open(self.docs_path, "r", encoding="utf-8") as f:
            self.docs = json.load(f)

        self.doc_matrix = np.load(self.embeddings_path).astype(np.float32)
        # Normalize defensively
        norms = np.linalg.norm(self.doc_matrix, axis=1, keepdims=True) + 1e-9
        self.doc_matrix = self.doc_matrix / norms

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME, device=device)
        if device == "cuda":
            self.embedder.to(torch.float16)

        self.corpus_tokens = [_tokenize(d.get("text", "")) for d in self.docs]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def expand_query(self, query: str) -> str:
        q = query.lower()
        expansions = {
            "nlp": ["natural language processing", "language models", "text mining"],
            "rl": ["reinforcement learning", "sequential decision making"],
            "hci": ["human computer interaction", "user studies", "ux"],
            "ml": ["machine learning", "statistical learning", "predictive modeling"],
            "robotics": ["autonomous systems", "drones", "mechatronics", "control", "ROS"],
        }
        extra = []
        for k, vals in expansions.items():
            if k in q:
                extra.extend(vals)
        if extra:
            return f"{query} " + " ".join(extra)
        return query

    def _dense_scores(self, query: str) -> np.ndarray:
        q = f"query: {query}"
        q_emb = self.embedder.encode([q], normalize_embeddings=True)[0].astype(np.float32)
        # cosine similarity
        return self.doc_matrix @ q_emb

    def _bm25_scores(self, query: str) -> np.ndarray:
        return np.asarray(self.bm25.get_scores(_tokenize(query)), dtype=np.float32)

    def search(self, query: str, top_k_retrieve=50, top_k_final=10, campus=None, department=None):
        qx = self.expand_query(query)

        dense = self._dense_scores(qx)
        sparse = self._bm25_scores(qx)

        dense_n = _minmax(dense)
        sparse_n = _minmax(sparse)

        # Hybrid weighting (more weight to BM25 for technical keyword precision)
        hybrid = self.w_dense * dense_n + self.w_bm25 * sparse_n
        
        # Apply pre-filters
        if campus or department:
            for i in range(len(self.docs)):
                raw = self.docs[i].get("raw", {})
                match = True
                if campus and raw.get("campus", "").upper() != campus.upper():
                    match = False
                if department and raw.get("department", "").lower() != department.lower():
                    match = False
                if not match:
                    hybrid[i] = -100.0

        cand_idx = np.argsort(-hybrid)[:top_k_retrieve]
        # Valid candidates only
        cand_idx = [int(i) for i in cand_idx if hybrid[i] > -50.0]

        if not cand_idx:
            return []

        cand_arr = np.array(cand_idx)
        # Sort by hybrid score as final rank (simplified for speed/CPU)
        ranked = sorted(
            zip(cand_idx, hybrid[cand_arr], dense[cand_arr], sparse[cand_arr]),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k_final]

        results = []
        for i, hs, ds, bs in ranked:
            d = self.docs[i]
            prof = dict(d.get("raw", {}))
            
            # Map hybrid score (0 to 1) to a readable percentage (0.6 to 1.0 looks better)
            final_percentage = min(1.0, 0.4 + (hs * 0.6))
            
            prof["score"] = float(final_percentage)
            prof["hybrid_score"] = float(hs)
            prof["dense_score"] = float(ds)
            prof["bm25_score"] = float(bs)
            prof["id"] = d.get("id", f"prof_{i}")
            results.append(prof)
            
        return results