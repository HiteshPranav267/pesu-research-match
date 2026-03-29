# ResearchMatch — PES University

Find your perfect research professor at PES University — match your resume or research interests to faculty using local ML embeddings. **No API keys needed. Everything runs on your laptop.**

---

## Quick Start

### 1. Install dependencies

```bash
pip install requests beautifulsoup4 sentence-transformers fastapi uvicorn numpy scipy
```

### 2. Scrape professor data

```bash
python scraper.py
```

This fetches all departments from both RR and EC campuses and saves `professors.json`.  
⏱ *May take a few minutes due to pagination and the 1-second delay between requests.*

### 3. Generate embeddings

```bash
python embed.py
```

Downloads the `all-MiniLM-L6-v2` model (~80 MB on first run, then cached), generates embeddings for every professor, and saves:
- `professors_embeddings.npy`
- `professors_index.json`

### 4. Start the FastAPI backend

```bash
uvicorn api:app --reload --port 8000
```

The API will be available at <http://localhost:8000>.

### 5. Open the frontend

Open `App.jsx` in your browser:

```bash
# macOS
open App.jsx

# Linux
xdg-open App.jsx

# Windows
start App.jsx
```

Or simply double-click `App.jsx` in your file manager — it is a self-contained HTML file that loads React and pdf.js from CDN.

---

## Project Structure

| File | Purpose |
|------|---------|
| `scraper.py` | Scrapes professor listings from staff.pes.edu |
| `embed.py` | Generates sentence embeddings using all-MiniLM-L6-v2 |
| `matcher.py` | Cosine-similarity matching engine (also usable as CLI) |
| `api.py` | FastAPI backend — `/professors`, `/departments`, `/match` |
| `App.jsx` | Self-contained React frontend (HTML + JSX + CSS in one file) |

---

## CLI Matching (optional)

You can also run the matcher directly from the command line:

```bash
python matcher.py "I am interested in NLP and deep learning"
python matcher.py "computer vision" --campus RR --department "Computer Science"
```

---

## Notes

- **No external ML APIs** — sentence-transformers runs fully offline after the first model download.
- **Matching is based on publicly available info** (name, title, department). Individual professor profiles on staff.pes.edu require a PES login. The frontend reminds users of this.
- Scraper adds a 1-second delay between HTTP requests to be respectful to the server.
- All data is stored as flat JSON / numpy files — no database required.

