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
    print(f"Loading Local LLM (Qwen2.5-0.5B-Instruct)...")
    llm_pipe = pipeline(
        "text-generation", 
        model="Qwen/Qwen2.5-0.5B-Instruct", 
        device_map="auto",
        model_kwargs={"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32}
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

    top_k_retrieve = int(body.get("top_k_retrieve", 500))
    top_k_final = int(body.get("top_k_final", 500))

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
            # Use a more explicit generation call for better CPU compatibility
            res = llm_pipe(
                messages, 
                max_new_tokens=120, 
                do_sample=False, 
                clean_up_tokenization_spaces=True
            )
            
            # Extract the generated text safely
            if isinstance(res, list) and len(res) > 0:
                # If it's the newer chat-style output
                if 'generated_text' in res[0]:
                    gen = res[0]['generated_text']
                    if isinstance(gen, list):
                        ai_summary = gen[-1]['content'].strip()
                    else:
                        # Fallback for string-based output
                        ai_summary = str(gen).strip()
                else:
                    ai_summary = "Match found, but summary could not be formatted."
            else:
                ai_summary = "Match found, but the advisor is currently busy."

        except Exception as e:
            # This will now show up in your Hugging Face "Logs" tab!
            print(f"--- LLM GENERATION ERROR ---")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            ai_summary = "An error occurred generating the AI insight. Please check the server logs."

    return jsonify({
        "results": results,
        "ai_summary": ai_summary
    })

@app.route("/suggest", methods=["GET", "OPTIONS"])
def suggest():
    query = request.args.get("query", "").lower().strip()
    if not query or len(query) < 2:
        return jsonify([])

    try:
        import json
        if not os.path.exists("search_suggestions.json"):
            return jsonify([])
        with open("search_suggestions.json", "r") as f:
            all_suggestions = json.load(f)
        
        # Filter suggestions that contain the query
        matches = [s for s in all_suggestions if query in s.lower()]
        
        # Sort by relevance: starts with query first, then contains query
        matches.sort(key=lambda s: (not s.lower().startswith(query), s.lower()))
        
        return jsonify(matches[:8])  # Return top 8 suggestions
    except Exception as e:
        print(f"Suggestion error: {e}")
        return jsonify([])

if __name__ == "__main__":
    # Hugging Face Spaces port is 7860
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)