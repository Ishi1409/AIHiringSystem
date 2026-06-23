import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import sys
    print("Downloading spaCy model...", file=sys.stderr)
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


def extract_skills_from_text(doc, skill_list):
    found = []
    text_lower = doc.text.lower()
    for skill in skill_list:
        if skill.lower() in text_lower:
            found.append(skill)
    return list(set(found))


def parse_resume_text(text, skill_list):
    doc = nlp(text[:100000])
    return {
        "name": extract_name(doc),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "education": extract_education(doc),
        "skills": extract_skills_from_text(doc, skill_list),
        "raw_text": text[:5000],
    }
