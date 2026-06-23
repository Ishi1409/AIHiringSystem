"""
Train job-candidate matcher: TF-IDF cosine similarity + skill overlap scoring.
Output: models/job_matcher.pkl
"""
import json, os, sys, pickle, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = "datasets"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 60)
print("JOB-CANDIDATE MATCHER TRAINING")
print("=" * 60)

# 1. Load data
print("\n[1] Loading data...")
with open(f"{DATA_DIR}/jobs.json") as f:
    jobs = json.load(f)
with open(f"{DATA_DIR}/candidates.json") as f:
    candidates = json.load(f)
with open(f"{DATA_DIR}/resumes.json") as f:
    resumes = json.load(f)

print(f"    {len(jobs)} jobs, {len(candidates)} candidates, {len(resumes)} resumes")

# 2. Build skill similarity model
print("\n[2] Building skill embedding model...")
all_people = []
for c in candidates:
    all_people.append({
        "id": c["id"], "name": c["name"], "skills": " ".join(c.get("skills", [])),
        "experience_years": c.get("experience_years", 0),
    })
for r in resumes:
    all_people.append({
        "id": r["user_id"], "name": r.get("parsed_name", ""),
        "skills": " ".join(r.get("skills", [])),
        "experience_years": 0,
    })

job_texts = [" ".join(j.get("skills", [])) for j in jobs]
person_texts = [p["skills"] for p in all_people]

vectorizer = TfidfVectorizer(analyzer="word", token_pattern=r"(?u)\b\w+\b", lowercase=True)
all_texts = job_texts + person_texts
vectorizer.fit(all_texts)

job_vectors = vectorizer.transform(job_texts)
person_vectors = vectorizer.transform(person_texts)

# Compute similarity matrix
sim_matrix = cosine_similarity(job_vectors, person_vectors)
print(f"    Similarity matrix shape: {sim_matrix.shape}")

# 3. Train scoring model (weighted combination of skill match + experience)
print("\n[3] Training scoring weights...")
from sklearn.linear_model import LinearRegression

# Build training examples from synthetic interview data
with open(f"{DATA_DIR}/interviews.json") as f:
    interviews = json.load(f)

X_train, y_train = [], []
for iv in interviews:
    cid = iv.get("candidate_id", "")
    jid = iv.get("job_id", "")
    sentiment = iv.get("sentiment_score", 0)

    # Find candidate index
    p_idx = next((i for i, p in enumerate(all_people) if p["id"] == cid), None)
    j_idx = next((i for i, j in enumerate(jobs) if j["id"] == jid), None)
    if p_idx is None or j_idx is None:
        continue

    sim_score = sim_matrix[j_idx, p_idx]
    exp_years = all_people[p_idx]["experience_years"]
    X_train.append([sim_score, exp_years])
    y_train.append(max(0, sentiment * 10 + 5))  # Map sentiment to 0-10 score

if len(X_train) > 10:
    reg = LinearRegression()
    reg.fit(X_train, y_train)
    print(f"    Learned weights: skill_match={reg.coef_[0]:.3f}, experience={reg.coef_[1]:.3f}")
else:
    reg = None
    print("    Not enough training data for regression, using default weights")

# 4. Save model
print("\n[4] Saving model...")
model = {
    "vectorizer": vectorizer,
    "regressor": reg,
    "job_vectors": job_vectors,
    "sim_matrix": sim_matrix,
    "jobs": jobs,
    "all_people": all_people,
}
with open(f"{MODEL_DIR}/job_matcher.pkl", "wb") as f:
    pickle.dump(model, f)
print(f"    Saved to {MODEL_DIR}/job_matcher.pkl")
print("\n✓ Job matcher training complete!")
