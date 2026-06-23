"""
Train candidate ranker: RandomForest regression to score and rank candidates.
Output: models/candidate_ranker.pkl
"""
import json, os, sys, pickle, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score

DATA_DIR = "datasets"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 60)
print("CANDIDATE RANKER TRAINING")
print("=" * 60)

# 1. Load data
print("\n[1] Loading data...")
with open(f"{DATA_DIR}/candidates.json") as f:
    candidates = json.load(f)
with open(f"{DATA_DIR}/resumes.json") as f:
    resumes = json.load(f)
with open(f"{DATA_DIR}/interviews.json") as f:
    interviews = json.load(f)
with open(f"{DATA_DIR}/jobs.json") as f:
    jobs = json.load(f)
with open(f"{DATA_DIR}/offers.json") as f:
    offers = json.load(f)

print(f"    {len(candidates)} candidates, {len(resumes)} resumes")
print(f"    {len(interviews)} interviews, {len(offers)} offers")

# 2. Feature engineering
print("\n[2] Building feature matrix...")

def skill_count(skills):
    return len(skills) if skills else 0

def skill_diversity(skills, all_skills_list):
    if not skills:
        return 0
    s_lower = [s.lower() for s in skills]
    cats = set()
    for s in s_lower:
        for cat, clist in all_skills_list.items():
            if any(cs in s for cs in clist):
                cats.add(cat)
    return len(cats)

ALL_SKILLS_CATS = {
    "programming": ["python","java","javascript","typescript","c++","c#","go","rust","kotlin","swift"],
    "web": ["react","angular","vue","node","django","flask","spring","express","next"],
    "data": ["pandas","numpy","sql","tableau","power bi","excel","r","matlab","sas","spss"],
    "ml": ["tensorflow","pytorch","scikit","keras","xgboost","lightgbm","opencv","nltk","spacy","langchain"],
    "cloud": ["aws","azure","gcp","docker","kubernetes","terraform","jenkins","git"],
    "soft": ["leadership","communication","problem solving","teamwork","project management"],
}

X, y = [], []
people = candidates + [{
    "id": r["user_id"], "name": r.get("parsed_name", ""),
    "skills": r.get("skills", []), "experience_years": 0,
    "score": 50,  # default mid score
} for r in resumes]

for p in people:
    skills = p.get("skills", [])
    n_skills = skill_count(skills)
    diversity = skill_diversity(skills, ALL_SKILLS_CATS)
    exp = p.get("experience_years", 0)
    score = p.get("score", 50)

    # Count interviews and offers for this candidate
    n_interviews = sum(1 for iv in interviews if iv.get("candidate_id") == p["id"])
    n_offers = sum(1 for o in offers if o.get("candidate_id") == p["id"])
    avg_sentiment = np.mean([
        iv.get("sentiment_score", 0) for iv in interviews
        if iv.get("candidate_id") == p["id"]
    ]) or 0

    X.append([n_skills, diversity, exp, n_interviews, n_offers, avg_sentiment])
    y.append(score / 100.0)  # Normalize to 0-1

X = np.array(X)
y = np.array(y)

print(f"    Feature matrix: {X.shape}")
print(f"    Features: n_skills, diversity, exp_years, n_interviews, n_offers, avg_sentiment")

# 3. Train model
print("\n[3] Training RandomForest regressor...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(
    n_estimators=200, max_depth=10, min_samples_leaf=4,
    random_state=42, n_jobs=-1
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring="r2")

print(f"    MAE:  {mae:.4f}")
print(f"    R²:   {r2:.4f}")
print(f"    CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")

# Feature importance
for name, imp in zip(
    ["n_skills","diversity","exp_years","n_interviews","n_offers","avg_sentiment"],
    model.feature_importances_
):
    print(f"    {name}: {imp:.3f}")

# 4. Save
print("\n[4] Saving model...")
payload = {"model": model, "scaler": scaler, "feature_names": X_train.shape[1]}
with open(f"{MODEL_DIR}/candidate_ranker.pkl", "wb") as f:
    pickle.dump(payload, f)
print(f"    Saved to {MODEL_DIR}/candidate_ranker.pkl")
print("\n✓ Candidate ranker training complete!")
