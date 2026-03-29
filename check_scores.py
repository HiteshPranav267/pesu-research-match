import numpy as np
import json
from sentence_transformers import SentenceTransformer
from matcher import BGE_QUERY_PREFIX, expand_query, cosine_similarity

BI = "BAAI/bge-large-en-v1.5"
model = SentenceTransformer(BI)
embs = np.load("professors_embeddings.npy")
with open("professors_chunk_map.json") as f: cmap = json.load(f)
with open("professors_index.json") as f: profs = json.load(f)

q = "robotics"
expanded = expand_query(q)
vec = model.encode([BGE_QUERY_PREFIX + expanded], normalize_embeddings=True)[0]

chunk_scores = cosine_similarity(vec, embs)

prof_scores = np.zeros(len(profs))
for c_idx, p_idx in enumerate(cmap):
    if chunk_scores[c_idx] > prof_scores[p_idx]:
        prof_scores[p_idx] = chunk_scores[c_idx]

# Find Shikha and Rashmi
for i, p in enumerate(profs):
    n = p.get('name', '').lower()
    if 'shikha' in n or 'rashmi n' in n:
        print(f"{p['name']}: BGE score = {prof_scores[i]}")

# Top 40
tops = np.argsort(prof_scores)[::-1][:40]
print("\nTop 40 from BGE:")
for i, idx in enumerate(tops):
    print(f"{i+1}. {profs[idx]['name']} : {prof_scores[idx]:.3f} - Dept: {profs[idx].get('department')}")

