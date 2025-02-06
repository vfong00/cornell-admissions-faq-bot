from flask import Flask, request, jsonify, render_template
from http.server import BaseHTTPRequestHandler
from werkzeug.serving import run_simple
import logging
from dotenv import load_dotenv
import os

import pandas as pd
import numpy as np
from huggingface_hub import InferenceClient

SIMILARITY_THRESHOLD = 0.5

load_dotenv()
app = Flask(__name__, static_folder="static", template_folder="templates")
wsgi_app = app
api_key = os.getenv("API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Read in embeddings, metadata, start HuggingFace API
df = pd.read_pickle("faq_with_embeddings.pkl")
cosines = np.load("embeddings.npy")
client = InferenceClient(token=api_key)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/couldnot", methods=["GET"])
def couldnot():
    return render_template("couldnot.html")

@app.route("/response", methods=["GET"])
def response():
    query = request.args.get("query", "No query provided")
    answer = request.args.get("answer", "No answer available")
    source_url = request.args.get("source_url", "No url provides")
    return render_template("response.html", query=query, answer=answer, source_url=source_url)

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    if not data or "query" not in data or "answer" not in data or "feedback" not in data:
        return jsonify({"error": "Invalid feedback data"}), 400
    query = data["query"]
    answer = data["answer"]
    feedback = data["feedback"]

    logger.info(f"FEEDBACK - Query: {query}, Answer: {answer}, Feedback: {feedback}")
    return jsonify({"message": "Feedback recorded. Thank you!"})
    
@app.route("/search", methods=["POST"])
def semantic_search():
    data = request.json
    if not data or "question" not in data:
        return jsonify({"error": "Missing 'question' in request body"}), 400
    query = data["question"]
    
    try:
        query_embedding = client.feature_extraction(query, model="sentence-transformers/all-MiniLM-L6-v2")
        similarities = cosines@np.array(query_embedding)
        sims_above_threshold = np.sum(similarities > SIMILARITY_THRESHOLD)
        if sims_above_threshold > 1:
            # if >=2 relevant articles found, take top 2 blurbs and have model summarize them
            match_idxs = np.argsort(similarities)[-2:][::-1]
            url = df.loc[match_idxs[0], "Source"]
            prompt = ", ".join(["[GENERATED ANSWER] " + df.loc[idx, "Answer"] for idx in match_idxs])
            messages = [
                {"role": "system", "content": "You are helping a retrieval system in providing correct answers to the FAQ section for Cornell University's general admissions website. You are given two possible answers, and you should choose and summarize the best one. Do not add filler besides your summary."},
                {"role": "user", "content": prompt}
            ]
        elif sims_above_threshold == 1:
            # if 1 relevant article found, model just summarizes that
            match_idx = np.argmax(similarities)
            url = df.loc[match_idx, "Source"]
            prompt = df.loc[match_idx, "Answer"]
            messages = [
                {"role": "system", "content": "You are helping a retrieval system in providing correct answers to the FAQ section for Cornell University's general admissions website. You are given an answer that you should summarize. Do not add filler besides your summary."},
                {"role": "user", "content": prompt}
            ]
        else:
            logger.info(f"USER QUERY ERROR - model's similarity score too low to be deemed useful")
            return jsonify({
                "redirect_url": f"/couldnot?"
            })

        completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct", 
            messages=messages,
            max_tokens=1024
        )
        answer = completion.choices[0].message.content
        logger.info(f"USER QUERY - Query: {query}, Response: {answer}")
        return {
            "Answer": answer,
            "redirect_url": f"/response?query={query}&answer={answer}&source_url={url}"
        }
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

class VercelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        run_simple('0.0.0.0', 5000, app)

    def do_POST(self):
        run_simple('0.0.0.0', 5000, app)

if __name__ == "__main__":
    app.run(debug=True)