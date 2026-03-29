# 🎓 PESU ResearchMatch

> Match your skills and interests to the right research professor at PES University — powered by local machine learning, no internet or API keys required after setup.

Built as a university ML project, this tool uses `sentence-transformers` to semantically match student resumes or interest descriptions to PES faculty across RR and EC campuses.

---

## 🚀 Demo

![ResearchMatch Mockup](assets/demo.png)

---

## 🧠 How It Works

1.  **Scrape** — `scraper.py` pulls faculty names, titles, and departments from `staff.pes.edu` across all departments.
2.  **Embed** — `embed.py` converts professor profiles into 384-dimensional semantic vectors using the `all-MiniLM-L6-v2` model.
3.  **Match** — `matcher.py` (and the API) embeds your resume or interests and finds the closest professors using cosine similarity.
4.  **Display** — The React frontend (`App.jsx`) lets you filter by campus & department and shows ranked results with similarity scores.

---

## 🏗️ Project Structure

```text
pesu-research-match/
├── scraper.py               # Scrapes staff.pes.edu for faculty data
├── embed.py                 # Generates sentence embeddings for all professors
├── matcher.py               # Core matching engine & CLI tool
├── api.py                   # FastAPI backend (runs on localhost:8000)
├── App.jsx                  # React frontend (Single-file HTML/Babel app)
├── professors.json          # Scraped faculty data (generated)
├── professors_embeddings.npy  # Pre-computed embeddings (generated)
├── professors_index.json    # Mapping for vector lookup (generated)
└── assets/                  # Images and demo assets
```

---

## ⚙️ Setup

### 1. Install Dependencies
Ensure you have Python 3.8+ installed.
```bash
pip install requests beautifulsoup4 sentence-transformers fastapi uvicorn numpy scipy
```

### 2. Prepare Data
First, scrape the faculty list, enrich it with detailed profiles, and generate the embeddings.

```bash
# 1. Scrape basic faculty list (names/titles)
python scraper.py

# 2. Enrich with detailed research interests/bios (takes ~10 mins)
python enrich_data.py

# 3. Generate semantic embeddings
python embed.py
```

### 3. Start the Backend
Run the FastAPI server to handle matching requests.
```bash
uvicorn api:app --reload --port 8000
```
The API serves at `http://localhost:8000`.

### 4. Open the Frontend
The frontend is a self-contained HTML/React file (`App.jsx`). Simply open it in your browser (e.g., using a VS Code Live Server or just double-clicking the file).

---

## 🔍 Features

-   🏫 Filter by **RR Campus** or **EC Campus**.
-   📚 Filter by **Department** (Computer Science, ECE, Mechanical, etc.).
-   📄 **Resume Upload** — Client-side PDF text extraction using `pdf.js`.
-   ✍️ **Interests Search** — Describe your research goals in plain text.
-   🧮 **Semantic Similarity** — High-performance matching using `all-MiniLM-L6-v2`.
-   🔒 **100% Local** — Your data never leaves your browser.

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| **Scraping** | Python, BeautifulSoup, Requests |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **Backend** | FastAPI, NumPy, SciPy |
| **Frontend** | React (UMD), CSS Grid/Variables |
| **PDF Parsing** | `pdf.js` (Client-side) |

---

## 📄 License

MIT
