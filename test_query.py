import argparse
import json
import numpy as np
from matcher import Matcher

if __name__ == "__main__":
    m = Matcher()
    # Let's bypass the top_k cutoff and see the scores for everyone
    q = "robotics"
    print(f"Query: {q}")
    expanded_query = m.expand_query(q) if hasattr(m, 'expand_query') else q
    from matcher import expand_query, BGE_QUERY_PREFIX, cosine_similarity, build_profile_text
    expanded_query = expand_query(q)
    prefixed_query = BGE_QUERY_PREFIX + expanded_query
    
    query_vec = m.bi_encoder.encode([prefixed_query], convert_to_numpy=True, normalize_embeddings=True)[0]
    chunk_scores = cosine_similarity(query_vec, m.embeddings)
    
    prof_scores = np.zeros(m.num_profs)
    for c_idx, p_idx in enumerate(m.chunk_to_prof):
        if chunk_scores[c_idx] > prof_scores[p_idx]:
            prof_scores[p_idx] = chunk_scores[c_idx]
            
    print("Top 10 Bi-Encoder Candidates:")
    top_candidates = np.argsort(prof_scores)[::-1][:m.num_profs]
    
    shikha_idx = None
    rashmi_idx = None
    
    for rank, idx in enumerate(top_candidates):
        prof = m.professors[idx]
        if 'shikha' in prof.get('name', '').lower():
            shikha_idx = (rank, idx, prof_scores[idx])
        if 'rashmi n ugar' in prof.get('name', '').lower():
            rashmi_idx = (rank, idx, prof_scores[idx])
        if rank < 10:
            print(f"{rank+1}. {prof['name']} (Score: {prof_scores[idx]:.3f})")
            
    if shikha_idx:
        print(f"\nShikha Tripathi Bi-Encoder: Rank {shikha_idx[0]+1}, Score: {shikha_idx[2]:.3f}")
    if rashmi_idx:
        print(f"Rashmi Ugarakhod Bi-Encoder: Rank {rashmi_idx[0]+1}, Score: {rashmi_idx[2]:.3f}")
        
    pairs = []
    for idx in top_candidates[:50]:
        prof_text = build_profile_text(m.professors[idx])
        pairs.append((q, prof_text))
        
    ce_scores = m.cross_encoder.predict(pairs)
    ce_scores_norm = 1 / (1 + np.exp(-np.array(ce_scores)))
    
    ranked_ce = sorted(zip(top_candidates[:50], ce_scores_norm), key=lambda x: x[1], reverse=True)
    print("\nTop 10 Cross-Encoder Results:")
    for rank, (idx, score) in enumerate(ranked_ce):
        prof = m.professors[idx]
        if rank < 10:
            print(f"{rank+1}. {prof['name']} (Score: {score:.3f})")
        if idx == (shikha_idx[1] if shikha_idx else -1):
            print(f"!!! Shikha Tripathi found at CE Rank {rank+1} with score {score:.3f} !!!")
        if idx == (rashmi_idx[1] if rashmi_idx else -1):
            print(f"!!! Rashmi Ugarakhod found at CE Rank {rank+1} with score {score:.3f} !!!")
