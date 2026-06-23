def rank_candidates(candidates, weight_score=0.7, weight_experience=0.3):
    if not candidates:
        return []

    max_score = max(c["match_percentage"] for c in candidates) or 1
    max_exp = max(c.get("experience_years", 0) for c in candidates) or 1

    scored = []
    for c in candidates:
        norm_score = c["match_percentage"] / max_score
        norm_exp = c.get("experience_years", 0) / max_exp
        composite = (weight_score * norm_score) + (weight_experience * norm_exp)
        scored.append({**c, "rank_score": round(composite * 100, 2)})

    scored.sort(key=lambda x: x["rank_score"], reverse=True)
    for i, c in enumerate(scored, 1):
        c["rank"] = i

    return scored


def calculate_experience_years(education_list):
    edu_years = {
        "phd": 5, "master": 2, "bachelor": 0, "diploma": 0,
    }
    max_years = 0
    for edu in education_list:
        edu_lower = edu.lower()
        for keyword, years in edu_years.items():
            if keyword in edu_lower:
                max_years = max(max_years, years)
    return max_years
