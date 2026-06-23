"""
Train interview sentiment analyzer: TF-IDF + LogisticRegression
Output: models/sentiment_model.pkl
"""
import json, os, sys, pickle, warnings, random
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

DATA_DIR = "datasets"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 60)
print("INTERVIEW SENTIMENT ANALYZER TRAINING")
print("=" * 60)

# 1. Build synthetic interview transcript data
print("\n[1] Generating training data from interviews...")
with open(f"{DATA_DIR}/interviews.json") as f:
    interviews = json.load(f)
with open(f"{DATA_DIR}/candidates.json") as f:
    candidates = json.load(f)

# Create sentiment-labeled training examples from interview data
texts, sentiments = [], []

positive_phrases = [
    "excellent communication skills", "strong technical background", "great problem solver",
    "highly recommend", "outstanding candidate", "perfect fit for the role",
    "impressive portfolio", "great team player", "quick learner", "exceptional skills",
    "well prepared", "confident and knowledgeable", "great cultural fit",
    "exceeded expectations", "top performer", "very professional",
]
negative_phrases = [
    "needs improvement", "lacks experience", "poor communication", "not a good fit",
    "below expectations", "insufficient knowledge", "weak technical skills",
    "unprepared", "lack of confidence", "poor attitude", "limited experience",
    "not suitable", "needs training", "lacks motivation", "inconsistent answers",
]
neutral_phrases = [
    "average performance", "meets expectations", "acceptable", "standard response",
    "moderate skills", "fair knowledge", "adequate preparation", "satisfactory",
    "decent candidate", "reasonable answers",
]

for iv in interviews:
    score = iv.get("sentiment_score", 0)
    feedback = iv.get("feedback", "")
    transcript = iv.get("transcript", "")

    text = f"{feedback} {transcript}".strip()
    if len(text) < 5:
        continue

    # Map continuous score to 3 classes
    if score > 0.3:
        label = 2  # positive
    elif score < -0.3:
        label = 0  # negative
    else:
        label = 1  # neutral

    texts.append(text)
    sentiments.append(label)

# Augment with synthetic phrases
for _ in range(500):
    if random.random() < 0.4:
        texts.append(random.choice(positive_phrases))
        sentiments.append(2)
    elif random.random() < 0.7:
        texts.append(random.choice(neutral_phrases))
        sentiments.append(1)
    else:
        texts.append(random.choice(negative_phrases))
        sentiments.append(0)

print(f"    {len(texts)} training examples")

# 2. Train
print("\n[2] Training sentiment classifier...")
X_train, X_test, y_train, y_test = train_test_split(
    texts, sentiments, test_size=0.2, random_state=42, stratify=sentiments
)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=3000, ngram_range=(1, 3),
        stop_words="english", sublinear_tf=True,
        min_df=2, max_df=0.95,
    )),
    ("clf", LogisticRegression(max_iter=1000, C=2.0, class_weight="balanced")),
])

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)

print(f"    Accuracy: {accuracy_score(y_test, y_pred):.3f}")
print("\n    Classification Report:")
print(classification_report(y_test, y_pred, target_names=["Negative", "Neutral", "Positive"]))

# 3. Save
print("\n[3] Saving model...")
with open(f"{MODEL_DIR}/sentiment_model.pkl", "wb") as f:
    pickle.dump(pipeline, f)
print(f"    Saved to {MODEL_DIR}/sentiment_model.pkl")
print("\n✓ Sentiment analyzer training complete!")
