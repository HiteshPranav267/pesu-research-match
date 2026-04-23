import numpy as np
import json
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sentence_transformers import SentenceTransformer
from matcher import ProfessorMatcher

def demo_search_visualization():
    # 1. Load Data for Options
    with open("professor_docs.json", "r") as f:
        docs = json.load(f)
    
    campuses = sorted(list(set(d['raw'].get('campus', 'Unknown') for d in docs)))
    departments_all = sorted(list(set(d['raw'].get('department', 'Unknown') for d in docs)))

    print("=== ResearchMatch Interactive Search Demo ===")
    
    # 2. Campus Selection
    print("\n[STEP 1: SELECT CAMPUS]")
    for i, c in enumerate(campuses):
        print(f"{i+1}. {c} Campus")
    print(f"{len(campuses)+1}. All Campuses")
    
    c_choice = input("Select campus (number): ").strip()
    target_campus = None
    if c_choice.isdigit():
        idx = int(c_choice) - 1
        if 0 <= idx < len(campuses):
            target_campus = campuses[idx]
            print(f"Selected: {target_campus}")
            # Filter departments for this campus
            departments_all = sorted(list(set(d['raw'].get('department', 'Unknown') for d in docs if d['raw'].get('campus') == target_campus)))

    # 3. Department Selection
    print("\n[STEP 2: SELECT DEPARTMENT]")
    for i, d in enumerate(departments_all):
        print(f"{i+1}. {d}")
    print(f"{len(departments_all)+1}. All Departments")
    
    d_choice = input("Select department (number): ").strip()
    target_dept = None
    if d_choice.isdigit():
        idx = int(d_choice) - 1
        if 0 <= idx < len(departments_all):
            target_dept = departments_all[idx]
            print(f"Selected: {target_dept}")

    # 4. Query Input
    print("\n[STEP 3: DESCRIBE INTERESTS]")
    query = input("Enter your research interests (e.g. 'Image processing'): ").strip()
    if not query:
        query = "Image processing"
        print(f"Using default: {query}")
        
    # 5. Show Query Expansion
    matcher = ProfessorMatcher()
    
    print("\n--- [PHASE 1: QUERY EXPANSION] ---")
    print(f"Original Query: '{query}'")
    
    expanded_query = matcher.expand_query(query)
    if expanded_query != query:
        print(f"Dictionary triggered! New Query: {expanded_query}")
    else:
        print("No expansion dictionary matches found.")

    # 6. Search
    print("\n--- [PHASE 2: HYBRID SEARCH] ---")
    results = matcher.search(
        query, 
        campus=target_campus, 
        department=target_dept, 
        top_k_final=5
    )
    
    if not results:
        print("No results found for these filters.")
        return

    print(f"Top Matches found:")
    for i, r in enumerate(results):
        print(f"#{i+1}: {r['name']} (Score: {r['score']:.2f})")
        print(f"    [Semantic: {r['dense_score']:.2f} | Keyword: {r['bm25_score']:.2f}]")

    # 7. Visualize
    print("\n--- [PHASE 3: CONCEPT SPACE VISUALIZATION] ---")
    print("Reducing dimensions... this may take a moment.")
    prof_embeddings = np.load("professor_embeddings.npy")
    
    # Embed the query
    model = SentenceTransformer("BAAI/bge-large-en-v1.5")
    query_emb = model.encode([f"query: {expanded_query}"], normalize_embeddings=True)
    
    # Combine for t-SNE
    combined_embeddings = np.vstack([prof_embeddings, query_emb])
    tsne = TSNE(n_components=2)
    coords = tsne.fit_transform(combined_embeddings)
    
    prof_coords = coords[:-1]
    query_coord = coords[-1]
    
    plt.figure(figsize=(14, 10))
    
    # Plot all professors
    plt.scatter(prof_coords[:, 0], prof_coords[:, 1], c='grey', alpha=0.1, s=30, label='Other Professors')
    
    # Highlight department/campus if selected
    filtered_indices = []
    for i, d in enumerate(docs):
        match = True
        if target_campus and d['raw'].get('campus') != target_campus: match = False
        if target_dept and d['raw'].get('department') != target_dept: match = False
        if match: filtered_indices.append(i)
    
    if filtered_indices:
        label = f"Filtered: {target_campus or ''} {target_dept or ''}".strip()
        plt.scatter(prof_coords[filtered_indices, 0], prof_coords[filtered_indices, 1], c='skyblue', alpha=0.5, s=60, label=label)
    
    # Highlight top matches
    match_names = [r['name'] for r in results]
    match_indices = [i for i, d in enumerate(docs) if d['name'] in match_names]
    plt.scatter(prof_coords[match_indices, 0], prof_coords[match_indices, 1], c='forestgreen', s=150, label='Top Matches', zorder=5)
    
    # Plot Query
    plt.scatter(query_coord[0], query_coord[1], c='red', marker='*', s=400, label=f'QUERY: "{query}"', edgecolor='black', zorder=10)
    
    # Annotate top matches
    for i, r in enumerate(results[:3]):
        name = r['name']
        match_idx_list = [j for j, d in enumerate(docs) if d['name'] == name]
        if match_idx_list:
            idx = match_idx_list[0]
            plt.annotate(f"{i+1}. {name}", xy=prof_coords[idx], xytext=(8, 8), textcoords='offset points', fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7))

    plt.title(f"Concept Space Visualization\nQuery: '{query}'", fontsize=16)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.3)
    
    output_file = "search_visualization.png"
    plt.savefig(output_file, dpi=300)
    print(f"\nDone! View the 'search_visualization.png' file to see how your query mapped to the professors.")

if __name__ == "__main__":
    demo_search_visualization()
