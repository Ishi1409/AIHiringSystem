def match_skills(candidate_skills, required_skills):
    c_skills = set(s.lower() for s in candidate_skills)
    r_skills = set(s.lower() for s in required_skills)

    matched = c_skills & r_skills
    missing = r_skills - c_skills

    if len(r_skills) == 0:
        match_pct = 0.0
    else:
        match_pct = round(len(matched) / len(r_skills) * 100, 1)

    return {
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "match_percentage": match_pct,
    }
