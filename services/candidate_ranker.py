"""Candidate ranker — uses trained ML model when available."""
from services.ml_models import get_candidate_ranker


def rank_candidates(candidates, weight_score=0.7, weight_experience=0.3):
    """Rank candidates using trained ML model or fallback heuristic."""
    if not candidates:
        return []

    model_data = get_candidate_ranker()
    if model_data:
        return _rank_with_model(candidates, model_data)
    return _rank_basic(candidates, weight_score, weight_experience)


def _rank_with_model(candidates, model_data):
    model = model_data["model"]
    scaler = model_data["scaler"]

    features = []
    for c in candidates:
        skills = c.get("skills", []) or []
        features.append([
            len(skills),
            len(set(s.lower().replace(" ", "") for s in skills)),
            c.get("experience_years", 0),
            c.get("n_interviews", 0),
            c.get("n_offers", 0),
            c.get("avg_sentiment", 0),
        ])

    if features:
        X = scaler.transform(features)
        scores = model.predict(X)
        for i, c in enumerate(candidates):
            c["rank_score"] = round(scores[i] * 100, 2)
    else:
        for c in candidates:
            c["rank_score"] = 50.0

    scored = sorted(candidates, key=lambda x: x["rank_score"], reverse=True)
    for i, c in enumerate(scored, 1):
        c["rank"] = i
    return scored


def _rank_basic(candidates, weight_score, weight_experience):
    max_score = max(c.get("match_percentage", 0) for c in candidates) or 1
    max_exp = max(c.get("experience_years", 0) for c in candidates) or 1

    scored = []
    for c in candidates:
        norm_score = c.get("match_percentage", 0) / max_score
        norm_exp = c.get("experience_years", 0) / max_exp
        composite = (weight_score * norm_score) + (weight_experience * norm_exp)
        scored.append({**c, "rank_score": round(composite * 100, 2)})

    scored.sort(key=lambda x: x["rank_score"], reverse=True)
    for i, c in enumerate(scored, 1):
        c["rank"] = i
    return scored


def calculate_experience_years(education_list):
    if not education_list:
        return 0
    edu_years = {"phd": 5, "master": 2, "bachelor": 0, "diploma": 0}
    max_years = 0
    for edu in education_list:
        edu_lower = edu.lower() if isinstance(edu, str) else ""
        for keyword, years in edu_years.items():
            if keyword in edu_lower:
                max_years = max(max_years, years)
    return max_years
