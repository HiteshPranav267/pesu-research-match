# 🎓 PESU ResearchMatch

> Match your skills and interests to the right research faculty at PES University — powered by state-of-the-art Hybrid Search (Semantic AI + Keyword Precision).

Built as a project for the course Machine Learning and Applications (UE23EC352B), this tool uses **BGE-Large** embeddings and **BM25** ranking to semantically match student resumes or interest descriptions to the full professional profiles of PES faculty across RR and EC campuses.

---

## 🛠️ Technical Overview

1.  **Full-Profile Indexing** — Scans teaching history, industry experience, projects, and publications to build a comprehensive professional profile.
2.  **Hybrid Embedding** — Converts profiles into **1024-dimensional** semantic vectors using the `BAAI/bge-large-en-v1.5` model.
3.  **Cross-Modal Matching** — Combines semantic similarity (Dense Vectors) with literal keyword matching (BM25) to ensure specific technical terms (like "Robotics") are never missed.
4.  **Local LLM Summaries** — Utilizes a local `Qwen-2.5-0.5B` model to generate personalized explanations for each professor match.

---

## 🏗️ Project Structure

```text
pesu-research-match/
├── api.py                   # Flask backend (localhost:8000)
├── matcher.py               # Hybrid Search Engine Logic
├── embed.py                 # Indexing & Vector Generation
├── index.html               # Responsive Web Interface (Tailwind/React)
├── professor_docs.json      # Processed faculty metadata
├── professor_embeddings.npy # Pre-computed 1024-dim vectors
└── professors.json          # Scraped raw faculty data
```

---

## 🎓 Course Integration & Learnings

This project serves as a practical implementation of core concepts from the **Machine Learning and Applications** course:

### **ML Principles Applied:**
*   **Distance-Based Classification (Unit 3):** Implementation of **Cosine Similarity** for nearest-neighbor retrieval in high-dimensional latent space.
*   **Model Selection (Unit 2):** Benchmarking and selecting specific transformer architectures (BGE vs MiniLM) to optimize for cross-domain technical queries.
*   **Performance Metrics (Unit 1):** Development of a scoring normalization layer to map raw model outputs to human-readable confidence percentages.
*   **Feature Engineering (Unit 2):** Transformation of unstructured textual data into meaningful numerical representations (embeddings).

### **Structured Learning Process:**
1.  **Pipeline Construction:** Developed a robust data pipeline from raw scraping to structured search.
2.  **Semantic Mapping:** Learned to map natural language queries to a shared vector space with faculty biographies.
3.  **Hybrid Architecture:** Solved the "semantic dilution" problem by balancing parametric (Dense Vector) and non-parametric (Sparse Keyword) methods.
4.  **Inference Optimization:** Managed local model deployment to ensure low-latency responses for the end user.

---

## ⚙️ Setup

### 1. Install Dependencies
```bash
pip install flask flask-cors torch transformers sentence-transformers rank-bm25 numpy
```

### 2. Prepare the Data
If you modify the source data, re-generate the embeddings:
```bash
python embed.py professors.json
```

### 3. Start the Backend
```bash
python api.py
```
The API serves at `http://localhost:8000`.

### 4. Open the Web App
Simply open `index.html` in your browser.

---

## 🔍 Features

-   🏫 Filter by **RR Campus** or **EC Campus**.
-   📚 Filter by **Department** (Computer Science, ECE, Mechanical, etc.).
-   📄 **Resume Analysis** — Client-side PDF text extraction.
-   ✍️ **Interests Search** — Describe your research goals in plain text.
-   ⚡ **Hybrid Scoring** — High-performance matching using BGE-Large + BM25.
-   🔒 **100% Local** — All AI processing happens on your machine.

---

## 📄 License
MIT
