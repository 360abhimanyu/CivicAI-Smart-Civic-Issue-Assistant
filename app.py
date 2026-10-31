import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "civicai.db"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma4")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

CATEGORIES = [
    "Roads & Potholes", "Waste Management", "Water Supply",
    "Streetlights", "Drainage", "Public Safety", "Other"
]
URGENCY_LEVELS = ["Low", "Medium", "High", "Critical"]


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                urgency TEXT NOT NULL,
                department TEXT NOT NULL,
                suggested_action TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def rule_based_analysis(description):
    text = description.lower()
    rules = [
        (["pothole", "road", "crack", "traffic"], "Roads & Potholes", "Road Maintenance Department"),
        (["garbage", "waste", "trash", "rubbish"], "Waste Management", "Sanitation Department"),
        (["water", "leak", "pipe", "supply"], "Water Supply", "Water Works Department"),
        (["streetlight", "street light", "dark", "lamp"], "Streetlights", "Electrical Department"),
        (["drain", "sewage", "flood", "waterlogging"], "Drainage", "Drainage Department"),
        (["unsafe", "accident", "open wire", "danger"], "Public Safety", "Public Safety Department"),
    ]
    category, department = "Other", "Municipal Helpdesk"
    for keywords, found_category, found_department in rules:
        if any(word in text for word in keywords):
            category, department = found_category, found_department
            break

    urgent_words = ["urgent", "danger", "accident", "injury", "overflow", "fire", "exposed wire"]
    urgency = "High" if any(word in text for word in urgent_words) else "Medium"
    if any(word in text for word in ["life-threatening", "electrocution", "major accident"]):
        urgency = "Critical"
    return {
        "category": category,
        "urgency": urgency,
        "department": department,
        "summary": description[:180].strip(),
        "suggested_action": f"Forward this report to the {department} for inspection and appropriate action.",
        "ai_mode": "rule-based fallback"
    }


def analyze_with_gemma(description):
    prompt = f"""You are CivicAI, an assistant that triages citizen reports about public infrastructure.
Analyze the report and return ONLY valid JSON with these exact keys:
category (one of {CATEGORIES}),
urgency (one of {URGENCY_LEVELS}),
department (short responsible public department),
summary (one-sentence neutral summary),
suggested_action (one practical next step for the responsible department).
Do not invent facts, addresses, officials, or promises. If there is immediate danger, set urgency to Critical.
Citizen report: {description}
"""
    response = requests.post(
        OLLAMA_URL,
        json={"model": GEMMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
        timeout=45
    )
    response.raise_for_status()
    raw = response.json().get("response", "")
    data = json.loads(raw)
    if data.get("category") not in CATEGORIES:
        data["category"] = "Other"
    if data.get("urgency") not in URGENCY_LEVELS:
        data["urgency"] = "Medium"
    for key in ("department", "summary", "suggested_action"):
        data[key] = str(data.get(key, "")).strip()[:500]
    data["ai_mode"] = f"Gemma ({GEMMA_MODEL})"
    return data


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        r.raise_for_status()
        return jsonify({"status": "ok", "gemma_server": "reachable", "model": GEMMA_MODEL})
    except requests.RequestException:
        return jsonify({"status": "ok", "gemma_server": "offline", "model": GEMMA_MODEL})


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    description = str(payload.get("description", "")).strip()
    if len(description) < 15:
        return jsonify({"error": "Please describe the issue in at least 15 characters."}), 400
    if len(description) > 3000:
        return jsonify({"error": "Please keep the report under 3,000 characters."}), 400

    try:
        result = analyze_with_gemma(description)
    except (requests.RequestException, ValueError, KeyError, json.JSONDecodeError):
        result = rule_based_analysis(description)
    return jsonify(result)


@app.post("/api/complaints")
def create_complaint():
    payload = request.get_json(silent=True) or {}
    required = ["title", "description", "category", "urgency", "department", "suggested_action"]
    if any(not str(payload.get(k, "")).strip() for k in required):
        return jsonify({"error": "Please analyze the report before saving it."}), 400

    created_at = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO complaints
            (title, description, category, urgency, department, suggested_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(str(payload[k]).strip() for k in required) + (created_at,))
        complaint_id = cur.lastrowid
    return jsonify({"id": complaint_id, "created_at": created_at}), 201


@app.get("/api/complaints")
def list_complaints():
    with db() as conn:
        rows = conn.execute("SELECT * FROM complaints ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/stats")
def stats():
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        critical = conn.execute("SELECT COUNT(*) FROM complaints WHERE urgency='Critical'").fetchone()[0]
        by_category = conn.execute(
            "SELECT category, COUNT(*) AS count FROM complaints GROUP BY category ORDER BY count DESC"
        ).fetchall()
    return jsonify({"total": total, "critical": critical, "by_category": [dict(r) for r in by_category]})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
