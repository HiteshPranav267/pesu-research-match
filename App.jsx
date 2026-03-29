<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ResearchMatch — PES University</title>

    <!-- Google Fonts -->
    <link
      href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap"
      rel="stylesheet"
    />

    <!-- pdf.js (CDN) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>

    <!-- React + Babel (UMD, no build step needed) -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

    <style>
      :root {
        --bg: #0f0f14;
        --surface: #1a1a24;
        --surface2: #22222f;
        --border: #2e2e3e;
        --accent: #c9a84c;
        --accent2: #8b5e3c;
        --text: #e8e0d0;
        --muted: #8a8090;
        --green: #4caf82;
        --yellow: #e8c840;
        --red: #e86060;
      }

      * { box-sizing: border-box; margin: 0; padding: 0; }

      body {
        font-family: "DM Sans", sans-serif;
        background: var(--bg);
        color: var(--text);
        min-height: 100vh;
      }

      /* ── Header ── */
      header {
        background: var(--surface);
        border-bottom: 1px solid var(--border);
        padding: 1.25rem 2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      header .logo {
        font-family: "Playfair Display", serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--accent);
        letter-spacing: 0.02em;
      }
      header .tagline {
        color: var(--muted);
        font-size: 0.9rem;
        font-weight: 300;
      }

      /* ── Main layout ── */
      main {
        max-width: 900px;
        margin: 2.5rem auto;
        padding: 0 1.5rem;
      }

      /* ── Section titles ── */
      .section-title {
        font-family: "Playfair Display", serif;
        font-size: 1rem;
        color: var(--accent);
        margin-bottom: 0.75rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }

      /* ── Campus pills ── */
      .campus-row {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 2rem;
      }
      .campus-pill {
        cursor: pointer;
        border: 1.5px solid var(--border);
        background: transparent;
        color: var(--muted);
        padding: 0.45rem 1.4rem;
        border-radius: 999px;
        font-family: "DM Sans", sans-serif;
        font-size: 0.95rem;
        font-weight: 500;
        transition: all 0.18s;
      }
      .campus-pill:hover { border-color: var(--accent); color: var(--accent); }
      .campus-pill.active {
        background: var(--accent);
        border-color: var(--accent);
        color: #0f0f14;
      }

      /* ── Department chips ── */
      .dept-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 2rem;
      }
      .dept-chip {
        cursor: pointer;
        border: 1px solid var(--border);
        background: var(--surface2);
        color: var(--muted);
        padding: 0.3rem 0.9rem;
        border-radius: 6px;
        font-size: 0.82rem;
        transition: all 0.15s;
      }
      .dept-chip:hover { border-color: var(--accent2); color: var(--text); }
      .dept-chip.active {
        background: var(--accent2);
        border-color: var(--accent2);
        color: #fff;
      }

      /* ── Input tabs ── */
      .tabs {
        display: flex;
        gap: 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
      }
      .tab-btn {
        cursor: pointer;
        background: none;
        border: none;
        color: var(--muted);
        padding: 0.6rem 1.2rem;
        font-family: "DM Sans", sans-serif;
        font-size: 0.9rem;
        border-bottom: 2px solid transparent;
        transition: all 0.15s;
      }
      .tab-btn.active {
        color: var(--accent);
        border-bottom-color: var(--accent);
      }

      /* ── Textarea ── */
      textarea {
        width: 100%;
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--text);
        font-family: "DM Sans", sans-serif;
        font-size: 0.95rem;
        padding: 0.9rem 1rem;
        resize: vertical;
        min-height: 130px;
        outline: none;
        transition: border-color 0.15s;
      }
      textarea:focus { border-color: var(--accent); }
      textarea::placeholder { color: var(--muted); }

      /* ── Drop zone ── */
      .drop-zone {
        border: 2px dashed var(--border);
        border-radius: 10px;
        padding: 2.5rem 1rem;
        text-align: center;
        cursor: pointer;
        color: var(--muted);
        transition: all 0.18s;
        position: relative;
      }
      .drop-zone.over { border-color: var(--accent); background: rgba(201,168,76,0.05); }
      .drop-zone input[type="file"] {
        position: absolute; inset: 0; opacity: 0; cursor: pointer;
      }
      .drop-zone .drop-icon { font-size: 2rem; margin-bottom: 0.5rem; }
      .drop-zone .drop-label { font-size: 0.9rem; }
      .drop-zone .drop-hint { font-size: 0.78rem; color: var(--muted); margin-top: 0.3rem; }
      .pdf-name {
        margin-top: 0.6rem;
        font-size: 0.85rem;
        color: var(--accent);
      }

      /* ── Match button ── */
      .match-btn {
        margin-top: 1.25rem;
        width: 100%;
        padding: 0.85rem;
        background: var(--accent);
        color: #0f0f14;
        border: none;
        border-radius: 8px;
        font-family: "Playfair Display", serif;
        font-size: 1.05rem;
        font-weight: 600;
        cursor: pointer;
        letter-spacing: 0.03em;
        transition: opacity 0.15s;
      }
      .match-btn:disabled { opacity: 0.45; cursor: not-allowed; }
      .match-btn:not(:disabled):hover { opacity: 0.88; }

      /* ── Disclaimer note ── */
      .note {
        margin-top: 0.75rem;
        font-size: 0.78rem;
        color: var(--muted);
        text-align: center;
      }

      /* ── Results section ── */
      .results-header {
        font-family: "Playfair Display", serif;
        font-size: 1.3rem;
        margin: 2.5rem 0 1.2rem;
        color: var(--text);
      }

      /* ── Skeleton cards ── */
      .skeleton-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 1rem;
      }
      .skeleton-card {
        background: var(--surface);
        border-radius: 10px;
        padding: 1.2rem;
        border: 1px solid var(--border);
        animation: pulse 1.4s ease-in-out infinite;
      }
      .skel-circle { width: 60px; height: 60px; border-radius: 50%; background: var(--surface2); margin-bottom: 0.8rem; }
      .skel-line { height: 10px; border-radius: 4px; background: var(--surface2); margin-bottom: 0.55rem; }
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }

      /* ── Professor cards ── */
      .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
        gap: 1rem;
      }
      .prof-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1.2rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        position: relative;
        transition: border-color 0.15s;
      }
      .prof-card:hover { border-color: var(--accent2); }

      .prof-top { display: flex; align-items: flex-start; gap: 0.9rem; }
      .prof-photo {
        width: 60px; height: 60px;
        border-radius: 50%;
        object-fit: cover;
        background: var(--surface2);
        flex-shrink: 0;
        border: 2px solid var(--border);
      }
      .prof-info { flex: 1; min-width: 0; }
      .prof-name {
        font-family: "Playfair Display", serif;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text);
        line-height: 1.3;
      }
      .prof-title {
        font-size: 0.8rem;
        color: var(--muted);
        margin-top: 0.15rem;
        line-height: 1.4;
      }

      .prof-badges { display: flex; gap: 0.4rem; flex-wrap: wrap; }
      .badge {
        font-size: 0.7rem;
        padding: 0.2rem 0.55rem;
        border-radius: 4px;
        font-weight: 500;
        background: var(--surface2);
        color: var(--muted);
        border: 1px solid var(--border);
      }
      .badge.campus { color: var(--accent); border-color: var(--accent2); }

      /* ── Score badge ── */
      .score-badge {
        position: absolute;
        top: 0.9rem;
        right: 0.9rem;
        width: 44px; height: 44px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.72rem;
        font-weight: 700;
        flex-direction: column;
        border: 2px solid;
      }
      .score-badge.green { border-color: var(--green); color: var(--green); background: rgba(76,175,130,0.1); }
      .score-badge.yellow { border-color: var(--yellow); color: var(--yellow); background: rgba(232,200,64,0.1); }
      .score-badge.red { border-color: var(--red); color: var(--red); background: rgba(232,96,96,0.1); }

      .prof-link {
        font-size: 0.8rem;
        color: var(--accent);
        text-decoration: none;
        margin-top: 0.25rem;
      }
      .prof-link:hover { text-decoration: underline; }

      /* ── Empty state ── */
      .empty-state {
        text-align: center;
        margin: 3rem 0;
        color: var(--muted);
      }
      .empty-state .emoji { font-size: 3rem; margin-bottom: 1rem; }
      .empty-state p { font-size: 0.95rem; }
    </style>
  </head>

  <body>
    <header>
      <div>
        <div class="logo">ResearchMatch</div>
        <div class="tagline">PES University · Find your research professor</div>
      </div>
    </header>

    <main>
      <div id="root"></div>
    </main>

    <script type="text/babel">
      const { useState, useEffect, useCallback } = React;
      const API = "http://localhost:8000";
      const MIN_MATCH_THRESHOLD = 0.3; // Only show results with ≥30% similarity

      // ── Score badge color helper ──
      function ScoreBadge({ score }) {
        const pct = Math.round(score * 100);
        const cls = pct >= 80 ? "green" : pct >= 60 ? "yellow" : "red";
        return (
          <div className={`score-badge ${cls}`}>
            <span>{pct}%</span>
          </div>
        );
      }

      // ── Skeleton loader ──
      function SkeletonCards() {
        return (
          <div className="skeleton-grid">
            {Array.from({ length: 6 }).map((_, i) => (
              <div className="skeleton-card" key={i}>
                <div className="skel-circle" />
                <div className="skel-line" style={{ width: "70%" }} />
                <div className="skel-line" style={{ width: "50%" }} />
                <div className="skel-line" style={{ width: "90%" }} />
              </div>
            ))}
          </div>
        );
      }

      // ── Professor card ──
      function ProfCard({ prof }) {
        return (
          <div className="prof-card">
            <ScoreBadge score={prof.score} />
            <div className="prof-top">
              <img
                className="prof-photo"
                src={prof.photo_url || ""}
                alt={prof.name}
                onError={(e) => {
                  e.target.src =
                    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Crect width='60' height='60' rx='30' fill='%2322222f'/%3E%3Ctext x='50%25' y='55%25' dominant-baseline='middle' text-anchor='middle' fill='%238a8090' font-size='22'%3E👤%3C/text%3E%3C/svg%3E";
                }}
              />
              <div className="prof-info">
                <div className="prof-name">{prof.name}</div>
                <div className="prof-title">{prof.title}</div>
              </div>
            </div>
            <div className="prof-badges">
              <span className="badge">{prof.department}</span>
              <span className="badge campus">{prof.campus} Campus</span>
            </div>
            {prof.profile_url && (
              <a className="prof-link" href={prof.profile_url} target="_blank" rel="noreferrer">
                View Profile →
              </a>
            )}
          </div>
        );
      }

      // ── Main App ──
      function App() {
        const [campus, setCampus] = useState("RR");
        const [departments, setDepartments] = useState([]);
        const [activeDept, setActiveDept] = useState(null);
        const [tab, setTab] = useState("text"); // "text" | "pdf"
        const [query, setQuery] = useState("");
        const [pdfText, setPdfText] = useState("");
        const [pdfName, setPdfName] = useState("");
        const [dragOver, setDragOver] = useState(false);
        const [loading, setLoading] = useState(false);
        const [results, setResults] = useState(null); // null = not searched yet

        // Fetch departments whenever campus changes
        useEffect(() => {
          setActiveDept(null);
          setResults(null);
          fetch(`${API}/departments?campus=${campus}`)
            .then((r) => r.json())
            .then((data) => setDepartments(data[campus] || []))
            .catch(() => setDepartments([]));
        }, [campus]);

        // Extract text from a PDF file using pdf.js
        const extractPdfText = useCallback(async (file) => {
          setPdfName(file.name);
          const arrayBuffer = await file.arrayBuffer();
          const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
          let text = "";
          for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            text += content.items.map((item) => item.str).join(" ") + " ";
          }
          setPdfText(text.trim());
        }, []);

        const handleFileInput = useCallback(
          (file) => {
            if (file && file.type === "application/pdf") {
              extractPdfText(file);
            }
          },
          [extractPdfText]
        );

        const handleDrop = useCallback(
          (e) => {
            e.preventDefault();
            setDragOver(false);
            const file = e.dataTransfer.files[0];
            handleFileInput(file);
          },
          [handleFileInput]
        );

        const effectiveQuery = tab === "text" ? query : pdfText;

        const handleMatch = async () => {
          if (!effectiveQuery.trim()) return;
          setLoading(true);
          setResults(null);
          try {
            const body = { query: effectiveQuery, campus };
            if (activeDept) body.department = activeDept;
            const resp = await fetch(`${API}/match`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body),
            });
            const data = await resp.json();
            // Filter out results below the minimum threshold
            const filtered = (data.results || []).filter((p) => p.score >= MIN_MATCH_THRESHOLD);
            setResults(filtered);
          } catch (err) {
            alert("Could not reach the API. Make sure the FastAPI server is running on port 8000.");
          } finally {
            setLoading(false);
          }
        };

        return (
          <div>
            {/* ── Campus selector ── */}
            <p className="section-title">Select Campus</p>
            <div className="campus-row">
              {["RR", "EC"].map((c) => (
                <button
                  key={c}
                  className={`campus-pill${campus === c ? " active" : ""}`}
                  onClick={() => setCampus(c)}
                >
                  {c} Campus
                </button>
              ))}
            </div>

            {/* ── Department filter ── */}
            {departments.length > 0 && (
              <>
                <p className="section-title">Department</p>
                <div className="dept-chips">
                  <button
                    className={`dept-chip${activeDept === null ? " active" : ""}`}
                    onClick={() => setActiveDept(null)}
                  >
                    All Departments
                  </button>
                  {departments.map((d) => (
                    <button
                      key={d}
                      className={`dept-chip${activeDept === d ? " active" : ""}`}
                      onClick={() => setActiveDept(d === activeDept ? null : d)}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </>
            )}

            {/* ── Input tabs ── */}
            <p className="section-title">Your Research Interests</p>
            <div className="tabs">
              <button
                className={`tab-btn${tab === "text" ? " active" : ""}`}
                onClick={() => setTab("text")}
              >
                Describe Your Interests
              </button>
              <button
                className={`tab-btn${tab === "pdf" ? " active" : ""}`}
                onClick={() => setTab("pdf")}
              >
                Upload Resume (PDF)
              </button>
            </div>

            {tab === "text" ? (
              <textarea
                placeholder="e.g. I am interested in natural language processing, deep learning, and computer vision…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            ) : (
              <div
                className={`drop-zone${dragOver ? " over" : ""}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => handleFileInput(e.target.files[0])}
                />
                <div className="drop-icon">📄</div>
                <div className="drop-label">Drag & drop your resume PDF here</div>
                <div className="drop-hint">or click to browse</div>
                {pdfName && <div className="pdf-name">✓ {pdfName}</div>}
              </div>
            )}

            <p className="note">
              Matching is based on publicly available info (name, title, department). Visit the
              professor's profile for full details.
            </p>

            <button
              className="match-btn"
              disabled={!effectiveQuery.trim() || loading}
              onClick={handleMatch}
            >
              {loading ? "Matching…" : "Find Matching Professors"}
            </button>

            {/* ── Results ── */}
            {loading && (
              <>
                <p className="results-header">Finding matches…</p>
                <SkeletonCards />
              </>
            )}

            {!loading && results !== null && (
              <>
                <p className="results-header">
                  {results.length > 0
                    ? `${results.length} Match${results.length !== 1 ? "es" : ""} Found`
                    : "No Strong Matches Found"}
                </p>
                {results.length === 0 ? (
                  <div className="empty-state">
                    <div className="emoji">🔍</div>
                    <p>
                      No professors matched your query above {Math.round(MIN_MATCH_THRESHOLD * 100)}% similarity. Try broadening your
                      description or removing department filters.
                    </p>
                  </div>
                ) : (
                  <div className="results-grid">
                    {results.map((prof, i) => (
                      <ProfCard key={i} prof={prof} />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        );
      }

      ReactDOM.createRoot(document.getElementById("root")).render(<App />);
    </script>
  </body>
</html>
