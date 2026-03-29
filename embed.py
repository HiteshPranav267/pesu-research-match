import json
import os
import glob
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-large-en-v1.5"

CANDIDATE_FILES = [
    "professors.json",
    "enriched_professors.json",
    "faculty.json",
    "data/professors.json",
    "data/enriched_professors.json",
    "output/professors.json",
    "output/enriched_professors.json",
]


def looks_like_prof(d: dict) -> bool:
    if not isinstance(d, dict):
        return False
    keys = set(d.keys())
    signal = {
        "name", "department", "bio", "description",
        "research_interests", "interests", "keywords",
        "publications", "id", "professor_id", "slug"
    }
    return ("name" in keys) or (len(keys.intersection(signal)) >= 2)


def extract_professor_dicts(obj):
    out = []

    def walk(x):
        if isinstance(x, dict):
            if looks_like_prof(x):
                out.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)

    walk(obj)
    # dedupe
    seen = set()
    unique = []
    for p in out:
        k = json.dumps(p, sort_keys=True, ensure_ascii=False)
        if k not in seen:
            seen.add(k)
            unique.append(p)
    return unique


def discover_input_file():
    # 1) fixed candidates
    for p in CANDIDATE_FILES:
        if os.path.exists(p):
            return p

    # 2) any json in root/data/output
    for pattern in ["*.json", "data/*.json", "output/*.json"]:
        for p in glob.glob(pattern):
            if "chunk_map" in p.lower():
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                profs = extract_professor_dicts(obj)
                if len(profs) >= 5:
                    return p
            except Exception:
                pass

    return None


def build_professor_text(prof: dict) -> str:
    """
    Constructs a comprehensive searchable text string from all relevant fields in the professor's profile.
    Prioritizes key research/teaching fields to stay within transformer token limits.
    """
    name = str(prof.get("name", "")).strip()
    dept = str(prof.get("department", "")).strip()
    campus = str(prof.get("campus", "")).strip()
    
    # Priority fields first (these contain the most distinguishing keywords)
    interests = prof.get("Research Interest", "") or prof.get("research_interests", []) or prof.get("interests", [])
    if isinstance(interests, list): interests = ", ".join(map(str, interests))
    
    teaching = str(prof.get("Teaching", "") or "")
    projects = str(prof.get("Research Projects", "") or "")
    responsibilities = str(prof.get("Responsibilities", "") or "")
    
    # Contextual fields second (truncate to stay within 512-token limits of BGE models)
    overview = str(prof.get("About", "") or prof.get("bio", "") or prof.get("description", "") or "")
    if len(overview) > 800:
        overview = overview[:800] + "..."
        
    experience = str(prof.get("Experience", "") or "")
    if len(experience) > 400:
        experience = experience[:400] + "..."
        
    # Success markers
    achievements = str(prof.get("Achievements", "") or "")
    patents = str(prof.get("Patents", "") or "")
    
    # Publications (take only top 10 to avoid token overflow)
    pubs = []
    for key in ["Journals", "Conferences", "Books", "publications"]:
        val = prof.get(key, [])
        if isinstance(val, list):
            pubs.extend(map(str, val))
        elif isinstance(val, str) and val.strip():
            pubs.append(val)
    
    # Truncate publications count
    pub_text = "; ".join(pubs[:10])
    
    parts = [
        f"Name: {name}" if name else "",
        f"Department: {dept}" if dept else "",
        f"Campus: {campus}" if campus else "",
        f"Research: {interests}" if interests else "",
        f"Expertise/Teaching: {teaching}" if teaching else "",
        f"Active Projects: {projects}" if projects else "",
        f"Responsibilities: {responsibilities}" if responsibilities else "",
        f"Bio: {overview}" if overview else "",
        f"Career History: {experience}" if experience else "",
        f"Success: {achievements} {patents}".strip() if (achievements or patents) else "",
        f"Recent Pubs: {pub_text}" if pub_text else "",
    ]
    
    # Filter out empty fields and join with a clear separator
    return " | ".join([p for p in parts if p.strip()]).strip()


def generate_embeddings(input_json=None, out_embeddings="professor_embeddings.npy", out_docs="professor_docs.json"):
    if input_json is None:
        input_json = discover_input_file()

    if not input_json:
        raise ValueError(
            "Could not find professor profile JSON automatically.\n"
            "Please run: python embed.py <path_to_professor_profile_json>"
        )

    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    professors = extract_professor_dicts(data)
    if not professors:
        raise ValueError(f"No professor-like dictionaries found in {input_json}")

    docs = []
    for idx, prof in enumerate(professors):
        prof_id = prof.get("id") or prof.get("professor_id") or prof.get("slug") or f"prof_{idx}"
        docs.append({
            "id": str(prof_id),
            "name": str(prof.get("name", f"Professor {idx}")),
            "department": str(prof.get("department", "")),
            "text": build_professor_text(prof),
            "raw": prof
        })

    model = SentenceTransformer(MODEL_NAME)
    passages = [f"passage: {d['text']}" for d in docs]
    emb = model.encode(passages, normalize_embeddings=True, show_progress_bar=True, batch_size=16)

    np.save(out_embeddings, np.asarray(emb, dtype=np.float32))
    with open(out_docs, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(f"Input file: {input_json}")
    print(f"Saved {len(docs)} docs -> {out_docs}")
    print(f"Saved embeddings -> {out_embeddings}")


if __name__ == "__main__":
    import sys
    input_arg = sys.argv[1] if len(sys.argv) > 1 else None
    generate_embeddings(input_json=input_arg)