"""Job-candidate matcher — uses trained ML model when available."""
from services.ml_models import get_job_matcher
from sklearn.metrics.pairwise import cosine_similarity


def match_skills(candidate_skills, required_skills):
    """Match candidate skills against job requirements.
    Uses trained ML model when available, falls back to set-based scoring.
    """
    model_data = get_job_matcher()
    if model_data and model_data.get("vectorizer"):
        return _match_with_model(candidate_skills, required_skills, model_data)
    return _match_basic(candidate_skills, required_skills)


def _match_with_model(candidate_skills, required_skills, model_data):
    vectorizer = model_data["vectorizer"]
    c_text = " ".join(candidate_skills) if candidate_skills else ""
    r_text = " ".join(required_skills) if required_skills else ""
    c_vec = vectorizer.transform([c_text])
    r_vec = vectorizer.transform([r_text])
    sim = cosine_similarity(c_vec, r_vec)[0][0] if r_text else 0.0
    match_pct = round(sim * 100, 1)

    c_set = set(s.lower() for s in candidate_skills)
    r_set = set(s.lower() for s in required_skills)
    matched = c_set & r_set
    missing = r_set - c_set
    return {
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "match_percentage": match_pct,
    }


def _match_basic(candidate_skills, required_skills):
    c_skills = set(s.lower() for s in candidate_skills)
    r_skills = set(s.lower() for s in required_skills)
    matched = c_skills & r_skills
    missing = r_skills - c_skills
    match_pct = round(len(matched) / max(len(r_skills), 1) * 100, 1)
    return {
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "match_percentage": match_pct,
    }
