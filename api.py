from flask import Flask, request, jsonify, send_file
from matcher import ProfessorMatcher
import torch
import os
from transformers import pipeline

# Optimize memory allocation to avoid fragmentation
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

app = Flask(__name__)

# Global placeholders
matcher = None
llm_pipe = None

def init_models():
    global matcher, llm_pipe
    if matcher is not None:
        return

    # Clear CUDA cache before loading
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("Loading matcher models (BGE-large, BGE-reranker)...")
    # load once
    matcher = ProfessorMatcher(
        docs_path="professor_docs.json",
        embeddings_path="professor_embeddings.npy",
        w_dense=0.4,
        w_bm25=0.6,
    )

    # Local LLM for personalized generation
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Loading Local LLM on {device} (Qwen2.5-0.5B-Instruct)...")
    llm_pipe = pipeline(
        "text-generation", 
        model="Qwen/Qwen2.5-0.5B-Instruct", 
        device=device,
        model_kwargs={"torch_dtype": torch.float16} if device == "cuda:0" else {}
    )

@app.before_request
def setup():
    # Only load models in the child process if debug is on, or always if debug is off
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        init_models()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/", methods=["GET"])
def index():
    return send_file("index.html")


@app.route("/<path:path>", methods=["GET", "OPTIONS"])
def static_proxy(path):
    if os.path.exists(path) and os.path.isfile(path):
        return send_file(path)
    return "Not Found", 404


@app.route("/departments", methods=["GET", "OPTIONS"])
def get_departments():
    campus = request.args.get("campus")
    filtered = [doc.get("raw", {}) for doc in matcher.docs]
    if campus:
        filtered = [p for p in filtered if p.get("campus", "").upper() == campus.upper()]

    dept_map = {}
    for p in filtered:
        c = p.get("campus", "Unknown")
        d = p.get("department", "Unknown")
        if c not in dept_map:
            dept_map[c] = set()
        dept_map[c].add(d)

    return jsonify({c: sorted(list(depts)) for c, depts in dept_map.items()})


@app.route("/match", methods=["POST", "OPTIONS"])
def search():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    body = request.get_json(silent=True) or {}
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"error": "query is required"}), 400

    top_k_retrieve = int(body.get("top_k_retrieve", 50))
    top_k_final = int(body.get("top_k_final", 10))

    campus = body.get("campus")
    department = body.get("department")

    results = matcher.search(
        query=query,
        top_k_retrieve=top_k_retrieve,
        top_k_final=top_k_final,
        campus=campus,
        department=department
    )

    # Generate a personalized summary using the Local LLM
    ai_summary = ""
    if results:
        # Provide the top 3 matches to the LLM context
        context_lines = []
        for i, r in enumerate(results[:3]):
            desc = r.get("raw", {}).get("About", r.get("raw", {}).get("Teaching", "No info"))
            context_lines.append(f"Professor: {r.get('name')}\nDepartment: {r.get('department')}\nBio: {desc[:250]}...")
        
        context_str = "\n".join(context_lines)
        prompt = f"""You are an AI advisor for PES University matching a student to relevant professors.
Student request: "{query}"

Here are the top matches from our database:
{context_str}

Write a short, engaging 2-sentence response directly addressing the student. Explain exactly why these specific professors are a good match for their research interests. Do not invent any information outside of the provided bios.
"""
        messages = [{"role": "system", "content": "You are a helpful academic advisor."},
                    {"role": "user", "content": prompt}]
        
        try:
            res = llm_pipe(messages, max_new_tokens=100, do_sample=False, return_full_text=False)
            generated = res[0]['generated_text']
            # If it's a list (chat format), get last content, else it's a string
            if isinstance(generated, list):
                ai_summary = generated[-1]['content'].strip()
            else:
                ai_summary = str(generated).strip()
        except Exception as e:
            ai_summary = "An error occurred generating the AI insight."
            print("LLM Error:", e)

    return jsonify({
        "results": results,
        "ai_summary": ai_summary
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)