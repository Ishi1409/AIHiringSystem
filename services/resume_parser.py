"""Resume parser — uses ML model when available, falls back to rule-based."""
import re
import spacy
from services.ml_models import get_skill_extractor

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import sys
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

PHONE_REGEX = re.compile(r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]")
EMAIL_REGEX = re.compile(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+")


def extract_name(doc):
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "Unknown"


def extract_email(text):
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def extract_phone(text):
    match = PHONE_REGEX.search(text)
    return match.group(0).strip() if match else None


def extract_education(doc):
    education = []
    edu_keywords = [
        "bachelor", "master", "phd", "b.tech", "m.tech", "b.e.", "m.e.",
        "b.sc", "m.sc", "bca", "mca", "b.com", "m.com", "b.a.", "m.a.",
        "diploma", "high school", "secondary", "senior secondary",
    ]
    for sent in doc.sents:
        sent_lower = sent.text.lower()
        if any(kw in sent_lower for kw in edu_keywords):
            education.append(sent.text.strip())
    return education[:5]


def extract_skills_ml(text, skill_vocab):
    """Use trained ML model to extract skills from text."""
    model_data = get_skill_extractor()
    if model_data and skill_vocab:
        try:
            pipeline = model_data["pipeline"]
            skill_clf = model_data["skill_clf"]
            vocab = model_data["skill_vocab"]
            tfidf_vec = pipeline.named_steps["tfidf"]
            X = tfidf_vec.transform([text])
            preds = skill_clf.predict(X)
            found = [vocab[i] for i, p in enumerate(preds[0]) if p == 1]
            if found:
                return found
        except Exception:
            pass
    return None


def extract_skills_from_text(doc, skill_list):
    """Rule-based fallback using keyword matching."""
    found = []
    text_lower = doc.text.lower()
    for skill in skill_list:
        if skill.lower() in text_lower:
            found.append(skill)
    return list(set(found))


def parse_resume_text(text, skill_list):
    doc = nlp(text[:100000])
    skills = extract_skills_ml(text, skill_list)
    if not skills:
        skills = extract_skills_from_text(doc, skill_list)
    return {
        "name": extract_name(doc),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "education": extract_education(doc),
        "skills": skills,
        "raw_text": text[:5000],
    }
