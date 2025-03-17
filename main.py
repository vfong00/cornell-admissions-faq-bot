from flask import Flask, request, jsonify, render_template
from http.server import BaseHTTPRequestHandler
from werkzeug.serving import run_simple
from dotenv import load_dotenv
import os

import pandas as pd
import numpy as np
from huggingface_hub import InferenceClient

import sqlite3

# anything below this is too dissimilar to be posted as a result 
SIMILARITY_THRESHOLD = 0.5

load_dotenv()
app = Flask(__name__, static_folder="static", template_folder="templates")
wsgi_app = app
api_key = os.getenv("API_KEY")
greetings = ["hello", "hi", "hey", "good morning", "good evening"]
farewells = ["bye", "goodbye", "see you", "have a nice day"]

def get_db_connection():
    return sqlite3.connect("logs.db")

def log_to_db(level, event):
    print(f"[{level}] {event}")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            event TEXT
        )
    """)

    # Insert the log entry
    cursor.execute("INSERT INTO logs (level, event) VALUES (?, ?)", (level, event))

    conn.commit()
    cursor.close()
    conn.close()

# Read in embeddings, metadata, start HuggingFace API
df = pd.read_pickle("faq_with_embeddings.pkl")
cosines = np.load("embeddings.npy")
client = InferenceClient(token=api_key)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")
    
@app.route("/search", methods=["POST"])
def semantic_search():
    data = request.json
    if not data or "question" not in data:
        log_to_db("WARNING", f"QUERY ERROR - Missing 'question' in request body")
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
                {"role": "system", "content": "You are helping a retrieval system in providing correct answers to the FAQ section for Cornell University's general admissions website. You are given two possible answers, and you should summarize the relevant information from them. Do not add filler besides your summary - format the answer as if it were your own."},
                {"role": "user", "content": prompt}
            ]
        elif sims_above_threshold == 1:
            # if 1 relevant article found, model just summarizes that
            match_idx = np.argmax(similarities)
            url = df.loc[match_idx, "Source"]
            prompt = df.loc[match_idx, "Answer"]
            messages = [
                {"role": "system", "content": "You are helping a retrieval system in providing correct answers to the FAQ section for Cornell University's general admissions website. You are given an answer that you should summarize the relevant information from. Do not add filler besides your summary - format the answer as if it were your own."},
                {"role": "user", "content": prompt}
            ]
        else:
            if any(word.strip() in query.lower() for word in greetings):
                log_to_db("INFO", f"USER CONVERSATIONAL - '{query}'")
                return jsonify({"query": query, "answer": "Hello! How can I help you today?"})

            elif any(word in query.lower() for word in farewells):
                log_to_db("INFO", f"USER CONVERSATIONAL - '{query}'")
                return jsonify({"query": query, "answer": "Goodbye! Have a great day!"})
            
            else:
                log_to_db("WARNING", f"QUERY ERROR - No relevant results found for: '{query}' (Similarity too low)")
            return jsonify({"error": "no relevant answer"})

        completion = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct", 
            messages=messages,
            max_tokens=1024
        )
        answer = completion.choices[0].message.content

        log_to_db("INFO", f"USER QUERY - Query: '{query}'")
        log_to_db("INFO", f"MODEL RESPONSE - Answer: '{answer[:100]}...'")

        return jsonify({"query": query, "answer": answer})
            
    except Exception as e:
        log_to_db("ERROR", f"SERVER ERROR - {str(e)}")
        return jsonify({"error": "An internal error occurred."}), 500
    
@app.route("/log_feedback", methods=["POST"])
def log_feedback():
    data = request.json
    if not data or "query" not in data or "answer" not in data or "feedback" not in data:
        log_to_db("WARNING", f"FEEDBACK ERROR - Invalid feedback data received")
        return jsonify({"error": "Invalid feedback data"}), 400
    
    query = data["query"]
    answer = data["answer"]
    feedback = data["feedback"]

    log_to_db("INFO", f"USER FEEDBACK - Query: '{query}', Answer: '{answer[:100]}...', Feedback: {feedback}")
    return jsonify({"message": "Feedback recorded. Thank you!"})

class VercelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        run_simple('0.0.0.0', 5000, app)

    def do_POST(self):
        run_simple('0.0.0.0', 5000, app)

if __name__ == "__main__":
    app.run(debug=True)