"""
Train skill extractor: TF-IDF + LogisticRegression
Uses real Kaggle resume dataset (2484 resumes, 24 categories) + synthetic data.
Output: models/skill_extractor.pkl, models/tfidf_vectorizer.pkl
"""
import json, os, re, sys, pickle, warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

DATA_DIR = "datasets"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 60)
print("SKILL EXTRACTOR TRAINING")
print("=" * 60)

# 1. Load Kaggle resume dataset
print("\n[1] Loading Kaggle resume dataset...")
df = pd.read_csv(f"{DATA_DIR}/resumes_classification.csv")
print(f"    {len(df)} resumes loaded")

# 2. Build skill vocabulary from the synthetic data
print("\n[2] Building skill vocabulary...")
with open(f"{DATA_DIR}/resumes.json") as f:
    synthetic_resumes = json.load(f)

skill_vocab = set()
for r in synthetic_resumes:
    for s in r.get("skills", []):
        skill_vocab.add(s.lower())

# Add common tech skills
extra_skills = [
    "python","java","javascript","typescript","c++","c#","go","rust","kotlin","swift",
    "react","angular","vue.js","node.js","django","flask","spring boot","express","next.js",
    "pandas","numpy","sql","tableau","power bi","excel","r","matlab",
    "tensorflow","pytorch","scikit-learn","keras","xgboost","lightgbm","opencv","nltk","spacy",
    "aws","azure","gcp","docker","kubernetes","terraform","jenkins","git","linux",
    "machine learning","deep learning","nlp","computer vision","data science","data analysis",
    "leadership","communication","problem solving","project management","agile","scrum",
]
skill_vocab.update(s.lower() for s in extra_skills)
print(f"    {len(skill_vocab)} skills in vocabulary")

# 3. Extract skill mentions from resume text
print("\n[3] Extracting skill features from resume text...")

def extract_skill_features(text):
    """Return a bag-of-skills vector for a given text."""
    text_lower = text.lower()
    features = {}
    for skill in skill_vocab:
        if skill in text_lower:
            features[skill] = features.get(skill, 0) + 1
    return features

# Build feature matrix from Kaggle resumes
X_texts = df["Resume_str"].fillna("").tolist()
y_labels = df["Category"].tolist()

# 4. Train TF-IDF + Logistic Regression pipeline
print("\n[4] Training pipeline...")
X_train, X_test, y_train, y_test = train_test_split(
    X_texts, y_labels, test_size=0.2, random_state=42, stratify=y_labels
)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=5000, ngram_range=(1, 3),
        stop_words="english", sublinear_tf=True
    )),
    ("clf", LogisticRegression(max_iter=1000, C=1.0)),
])

pipeline.fit(X_train, y_train)
train_acc = pipeline.score(X_train, y_train)
test_acc = pipeline.score(X_test, y_test)
print(f"    Train accuracy: {train_acc:.3f}")
print(f"    Test accuracy:  {test_acc:.3f}")

# 5. Train skill tagger (binary classifier per skill)
print("\n[5] Training skill tagger (multi-label)...")
skill_list = sorted(skill_vocab)
skill_present = []
for text in X_texts:
    tl = text.lower()
    skill_present.append([1 if s in tl else 0 for s in skill_list])
skill_matrix = np.array(skill_present)

skill_clf = OneVsRestClassifier(LogisticRegression(max_iter=1000, C=0.5, class_weight="balanced"))
skill_clf.fit(
    pipeline.named_steps["tfidf"].fit_transform(X_texts),
    skill_matrix
)

# 6. Save models
print("\n[6] Saving models...")
models = {
    "pipeline": pipeline,
    "skill_clf": skill_clf,
    "skill_vocab": list(skill_vocab),
    "categories": pipeline.classes_.tolist(),
}
with open(f"{MODEL_DIR}/skill_extractor.pkl", "wb") as f:
    pickle.dump(models, f)
print(f"    Saved to {MODEL_DIR}/skill_extractor.pkl")
print("\n✓ Skill extractor training complete!")
