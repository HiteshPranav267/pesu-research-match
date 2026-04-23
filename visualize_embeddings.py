import numpy as np
import json
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

def visualize():
    print("Loading data...")
    embeddings = np.load("professor_embeddings.npy")
    with open("professor_docs.json", "r") as f:
        docs = json.load(f)
    
    # Extract departments for coloring
    departments = [d['department'] for d in docs]
    
    print(f"Reducing {len(embeddings)} dimensions from 1024 to 2 using t-SNE...")
    # t-SNE reduction
    tsne = TSNE(n_components=2)
    embeddings_2d = tsne.fit_transform(embeddings)
    
    # Mapping departments to colors
    unique_depts = list(set(departments))
    colors = plt.cm.get_cmap('tab20', len(unique_depts))
    dept_to_color = {dept: colors(i) for i, dept in enumerate(unique_depts)}
    
    # Plotting
    plt.figure(figsize=(14, 9))
    
    for dept in unique_depts:
        idx = [i for i, d in enumerate(departments) if d == dept]
        plt.scatter(
            embeddings_2d[idx, 0], 
            embeddings_2d[idx, 1], 
            label=dept,
            alpha=0.7,
            s=60,
            edgecolor='none'
        )
    
    plt.title("ResearchMatch: 2D Projection of the Professor Concept Space (t-SNE)", fontsize=16, fontweight='bold')
    plt.xlabel("t-SNE Dimension 1")
    plt.ylabel("t-SNE Dimension 2")
    
    # Legend - limit to top departments to avoid clutter
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small', title="Departments")
    
    plt.tight_layout()
    output_file = "concept_space_visualization.png"
    plt.savefig(output_file, dpi=300)
    print(f"Success! Visualization saved to {output_file}")

if __name__ == "__main__":
    try:
        visualize()
    except Exception as e:
        print(f"An error occurred: {e}")
