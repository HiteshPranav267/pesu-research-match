# ResearchMatch: Technical Deep Dive
**A Hybrid Retrieval & Generative System for Academic Discovery**

---

## 🛠️ Comprehensive File-by-File Technical Logic

### 1. `scraper.py` (Data Acquisition)
- **Purpose**: Automates the collection of faculty metadata from the PES University staff directory.
- **Logic**: It iterates through a hardcoded dictionary of departments for both RR and EC campuses. For each department, it navigates paginated URLs (e.g., `?page=2`) and uses **BeautifulSoup** to parse HTML tags.
- **Key Lines**: It looks for `<div class="staff-profile">` to find individual cards. It handles "infinite pagination" loops by comparing the first professor's name on a new page with the previous page; if they match, it stops.
- **Output**: Generates `professors.json` containing names, titles, and profile links.

### 2. `enrich_data.py` (Deep Scraper)
- **Purpose**: Performs "Vertical Scraping" to gather detailed information missing from the main listing page.
- **Logic**: It reads the profile URLs from `professors.json` and visits every single one. It uses specific CSS selectors like `.bookings-item` (where PES stores Research/Teaching info) and `.list-single-main-item` (for Bios).
- **Technical Detail**: It uses `time.sleep(0.5)` to avoid triggering rate-limiting or 403 Forbidden errors from the university server. It periodically saves progress (every 20 profiles) to ensure data isn't lost if the script crashes.
- **Output**: Updates `professors.json` with "About", "Research Interests", "Education", and "Email" fields.

### 3. `embed.py` (Vector Indexing)
- **Purpose**: Converts unstructured text into mathematical vectors that an AI can understand.
- **Logic**: It combines multiple professor fields into a single long string using the `build_professor_text()` function. It prioritizes "Research Interests" and "Teaching" at the top of the string.
- **The Model**: Uses **BAAI/bge-large-en-v1.5**, a state-of-the-art embedding model. This model converts the text into a **1024-dimensional vector** (array of numbers).
- **Optimization**: It truncates bios and publications to fit within the 512-token limit of the transformer model to avoid data loss.
- **Output**: `professor_embeddings.npy` (binary vectors) and `professor_docs.json` (the text used for indexing).

### 4. `matcher.py` (Hybrid Search Engine)
- **Purpose**: The core logic that calculates "who is the best match" for a student's query.
- **Dual-Track Retrieval**:
    1. **Dense (Semantic)**: Uses Cosine Similarity between the student's query vector and the professor's vector. This finds "meaning" (e.g., matching "Drones" to "UAVs").
    2. **Sparse (Keyword)**: Uses the **BM25 algorithm** (via `rank_bm25` library). This ensures exact technical terms like "Verilog" or "FPGA" get heavy weight.
- **Scoring Logic**: It performs **Min-Max Scaling** on both scores to bring them to a 0-1 range, then calculates the final score: `(0.4 * Semantic) + (0.6 * Keyword)`.
- **Query Expansion**: Includes a hardcoded dictionary that expands "ML" to "Machine Learning" automatically to increase search accuracy.

### 5. `api.py` (Backend & AI Insights)
- **Purpose**: A **Flask** web server that connects the frontend to the ML models.
- **Model Loading**: It uses `app.before_request` to load the 1.5GB BGE model and the 0.5B parameter Qwen LLM once into memory to avoid slow response times on every search.
- **Generative AI**: When a match is found, it takes the top 3 professor bios and sends them to **Qwen2.5-0.5B-Instruct**. It uses a "System Prompt" to tell the AI: "You are an academic advisor. Do not invent info."
- **Memory Management**: Uses `torch.float16` and `PYTORCH_CUDA_ALLOC_CONF` to ensure the models can run on hardware with limited VRAM (like a free Hugging Face Space).

### 6. `index.html` (Interactive Frontend)
- **Architecture**: A Single Page Application (SPA) built using **React** (loaded via CDN) and **Tailwind CSS**.
- **Resume Parsing**: Uses the **pdf.js** library to process PDF files entirely in the user's browser. It extracts the raw text from the binary PDF and sends that text as the query to the backend.
- **State Management**: Uses React hooks (`useState`, `useEffect`) to manage real-time filtering by Campus (RR/EC) and Department.
- **Design**: Implements "Material Design 3" principles with dark-mode surfaces and custom neon glassmorphism effects for a premium feel.

### 7. `Dockerfile` & Infrastructure
- **Dockerfile**: Defines a Linux environment with Python 3.9. It installs `build-essential` so that C++ based libraries like `numpy` can be compiled correctly.
- **Security**: It creates a non-root user (`user`) with ID 1000, which is a security requirement for hosting on platforms like Hugging Face.
- **Requirements**: Lists all 15+ dependencies including `transformers`, `torch`, `flask`, and `scikit-learn`, ensuring the environment is identical across all machines.

---

## 🧠 Key ML Concepts for the Viva
1. **Cosine Similarity**: Measuring the angle between vectors to find how "close" two topics are in concept space.
2. **Inverted Index (BM25)**: A statistical method used by search engines (like Google) to rank documents based on keyword frequency.
3. **Hybrid Fusion**: Combining multiple search strategies to get the best of both worlds (semantic understanding + keyword precision).
4. **Local LLM Inference**: Running a Language Model on your own server rather than calling an expensive/private API like OpenAI.
