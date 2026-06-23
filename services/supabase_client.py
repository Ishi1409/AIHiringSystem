"""
Hybrid client: Supabase for auth + local JSON for business data.
Keeps everything working offline for data operations while
Supabase handles user authentication securely.
"""
import os
import json
import uuid
import io
from datetime import datetime
from collections import Counter

import pandas as pd
import numpy as np
import PyPDF2
from docx import Document
from dotenv import load_dotenv
from supabase import create_client

from services.resume_parser import parse_resume_text
from services.skill_extractor import SKILL_DB, extract_skills
from services.job_matcher import match_skills
from services.candidate_ranker import rank_candidates, calculate_experience_years
from services.ml_models import get_sentiment_model, get_offer_predictor, models_available as ml_available

load_dotenv()

# ── Supabase Auth Client ──────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase = None
_supabase_available = False

_is_placeholder = (
    not SUPABASE_URL
    or not SUPABASE_KEY
    or "your-project-id" in SUPABASE_URL
    or "placeholder" in SUPABASE_URL
    or SUPABASE_KEY.startswith("your-")
)

if not _is_placeholder:
    try:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        _supabase_available = True
    except Exception:
        _supabase_available = False


def is_supabase_available():
    return _supabase_available


# ── Local JSON Storage (for business data) ────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

_USERS_FILE = os.path.join(DATA_DIR, "users.json")
_RESUMES_FILE = os.path.join(DATA_DIR, "resumes.json")
_JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")
_INTERVIEWS_FILE = os.path.join(DATA_DIR, "interviews.json")
_OFFERS_FILE = os.path.join(DATA_DIR, "offers.json")
_CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.json")


def _read_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def _gen_id():
    return str(uuid.uuid4())[:8]


def _now():
    return datetime.utcnow().isoformat()


# ═══════════════════════════════════════════════════════════════════
# SUPABASE AUTH
# ═══════════════════════════════════════════════════════════════════

def sign_up(email, password, name, role="candidate"):
    """Register via Supabase Auth. Falls back to local JSON if Supabase fails or is unavailable."""
    if _supabase_available:
        try:
            res = _supabase.auth.sign_up({"email": email, "password": password})
            if not res.user:
                return None, "Registration failed"
            # Store profile
            _supabase.table("profiles").insert({
                "id": res.user.id, "email": email, "name": name, "role": role,
            }).execute()
            return {"user_id": res.user.id}, None
        except Exception:
            pass  # fall back to local JSON below

    # Fallback: local JSON
    users = _read_json(_USERS_FILE)
    if any(u["email"].lower() == email.lower() for u in users):
        return None, "Email already registered"
    user = {
        "id": _gen_id(), "email": email, "password": password,
        "name": name, "role": role, "created_at": _now(),
    }
    users.append(user)
    _write_json(_USERS_FILE, users)
    return {"user_id": user["id"]}, None


def sign_in(email, password):
    """Login via Supabase Auth. Falls back to local JSON if Supabase fails or is unavailable."""
    if _supabase_available:
        try:
            res = _supabase.auth.sign_in_with_password({"email": email, "password": password})
            if not res.user:
                return None, "Invalid credentials"
            return {
                "access_token": res.session.access_token,
                "user": {"id": res.user.id, "email": res.user.email},
            }, None
        except Exception:
            pass  # fall back to local JSON below

    # Fallback: local JSON
    users = _read_json(_USERS_FILE)
    for u in users:
        if u["email"].lower() == email.lower() and u["password"] == password:
            return {
                "access_token": f"local-token-{u['id']}",
                "user": {"id": u["id"], "email": u["email"]},
            }, None
    return None, "Invalid credentials"


def sign_out(token):
    """Sign out from Supabase."""
    if _supabase_available and token and not token.startswith("local-token"):
        try:
            _supabase.auth.sign_out()
        except Exception:
            pass


def get_user(token):
    """Get user from Supabase or local fallback."""
    if _supabase_available and token and not token.startswith("local-token"):
        try:
            res = _supabase.auth.get_user(token)
            if res and res.user:
                return res.user
        except Exception:
            pass
    # Local fallback
    users = _read_json(_USERS_FILE)
    for u in users:
        uid = u.get("id")
        if uid and token and (token.endswith(uid) or uid in token):
            return {"id": uid, "email": u.get("email")}
    return {"id": "local-user", "email": "local@example.com"} if token else None


def get_profile(user_id):
    """Get user profile from Supabase or local fallback."""
    if _supabase_available and user_id and user_id != "local-user":
        try:
            res = _supabase.table("profiles").select("*").eq("id", user_id).execute()
            if res.data:
                return res.data[0]
        except Exception:
            pass
    # Local fallback
    users = _read_json(_USERS_FILE)
    for u in users:
        if u["id"] == user_id:
            return u
    return {"id": user_id, "name": "User", "email": "user@example.com"}


# ═══════════════════════════════════════════════════════════════════
# BUSINESS DATA (all local JSON — no Supabase dependency)
# ═══════════════════════════════════════════════════════════════════

# ── Resumes ────────────────────────────────────────────────────────

def _extract_text(file_bytes, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == "docx":
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        return file_bytes.decode("utf-8", errors="ignore")


def upload_resume(user_id, file_obj):
    file_bytes = file_obj.read()
    filename = file_obj.name
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    local_path = os.path.join(upload_dir, f"{user_id}_{filename}")
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    text = _extract_text(file_bytes, filename)
    parsed = parse_resume_text(text, SKILL_DB)

    resumes = _read_json(_RESUMES_FILE)
    record = {
        "id": _gen_id(), "user_id": user_id, "filename": filename,
        "file_path": local_path, "parsed_name": parsed["name"],
        "parsed_email": parsed["email"], "parsed_phone": parsed["phone"],
        "education": parsed["education"], "skills": parsed["skills"],
        "raw_text": parsed["raw_text"], "created_at": _now(),
    }
    resumes.append(record)
    _write_json(_RESUMES_FILE, resumes)
    return parsed


def list_resumes(user_id=None):
    resumes = _read_json(_RESUMES_FILE)
    if user_id:
        return [r for r in resumes if r["user_id"] == user_id]
    return resumes


def get_resume(resume_id):
    resumes = _read_json(_RESUMES_FILE)
    for r in resumes:
        if r["id"] == resume_id:
            return r
    return None


def delete_resume(resume_id):
    resumes = _read_json(_RESUMES_FILE)
    resumes = [r for r in resumes if r["id"] != resume_id]
    _write_json(_RESUMES_FILE, resumes)
    return True


# ── Candidates ─────────────────────────────────────────────────────

def create_candidate(name, email, phone="", skills=None):
    candidates = _read_json(_CANDIDATES_FILE)
    candidate = {
        "id": _gen_id(), "name": name, "email": email, "phone": phone,
        "skills": skills or [], "status": "new", "score": 0.0,
        "experience_years": 0.0, "created_at": _now(),
    }
    candidates.append(candidate)
    _write_json(_CANDIDATES_FILE, candidates)
    return candidate


def list_candidates():
    return _read_json(_CANDIDATES_FILE)


def get_candidate(candidate_id):
    candidates = _read_json(_CANDIDATES_FILE)
    for c in candidates:
        if c["id"] == candidate_id:
            return c
    return None


def update_candidate(candidate_id, updates):
    candidates = _read_json(_CANDIDATES_FILE)
    for i, c in enumerate(candidates):
        if c["id"] == candidate_id:
            candidates[i].update(updates)
            _write_json(_CANDIDATES_FILE, candidates)
            return candidates[i]
    return None


def delete_candidate(candidate_id):
    candidates = _read_json(_CANDIDATES_FILE)
    candidates = [c for c in candidates if c["id"] != candidate_id]
    _write_json(_CANDIDATES_FILE, candidates)
    return True


# ── Jobs ───────────────────────────────────────────────────────────

def create_job(title, description, skills, experience_required):
    jobs = _read_json(_JOBS_FILE)
    job = {
        "id": _gen_id(), "title": title, "description": description,
        "skills": skills, "experience_required": experience_required,
        "status": "open", "created_at": _now(),
    }
    jobs.append(job)
    _write_json(_JOBS_FILE, jobs)
    return job


def list_jobs():
    return _read_json(_JOBS_FILE)


def get_job(job_id):
    jobs = _read_json(_JOBS_FILE)
    for j in jobs:
        if j["id"] == job_id:
            return j
    return None


def delete_job(job_id):
    jobs = _read_json(_JOBS_FILE)
    jobs = [j for j in jobs if j["id"] != job_id]
    _write_json(_JOBS_FILE, jobs)
    return True


# ── Interviews ─────────────────────────────────────────────────────

def create_interview(candidate_id, job_id, interview_type="technical", scheduled_date=None):
    interviews = _read_json(_INTERVIEWS_FILE)
    interview = {
        "id": _gen_id(), "candidate_id": candidate_id, "job_id": job_id,
        "interview_type": interview_type, "status": "scheduled",
        "scheduled_date": scheduled_date or _now(),
        "feedback": "", "transcript": "", "sentiment_score": 0.0,
        "created_at": _now(),
    }
    interviews.append(interview)
    _write_json(_INTERVIEWS_FILE, interviews)
    return interview


def analyze_interview_sentiment(transcript):
    """Score interview transcript sentiment using trained ML model."""
    model = get_sentiment_model()
    if not model:
        return 0.0
    try:
        pred = model.predict([transcript])[0]
        proba = model.predict_proba([transcript])[0]
        confidence = max(proba)
        # Map class (0=neg, 1=neutral, 2=pos) to -1..1 score
        score_map = {0: -confidence, 1: 0.0, 2: confidence}
        return round(score_map.get(pred, 0.0), 2)
    except Exception:
        return 0.0


def list_interviews():
    return _read_json(_INTERVIEWS_FILE)


def get_interview(interview_id):
    interviews = _read_json(_INTERVIEWS_FILE)
    for iv in interviews:
        if iv["id"] == interview_id:
            return iv
    return None


def update_interview(interview_id, updates):
    interviews = _read_json(_INTERVIEWS_FILE)
    for i, iv in enumerate(interviews):
        if iv["id"] == interview_id:
            interviews[i].update(updates)
            _write_json(_INTERVIEWS_FILE, interviews)
            return interviews[i]
    return None


def delete_interview(interview_id):
    interviews = _read_json(_INTERVIEWS_FILE)
    interviews = [iv for iv in interviews if iv["id"] != interview_id]
    _write_json(_INTERVIEWS_FILE, interviews)
    return True


# ── Offers ─────────────────────────────────────────────────────────

def create_offer(candidate_id, job_id, salary_offered, benefits=""):
    offers = _read_json(_OFFERS_FILE)
    offer = {
        "id": _gen_id(), "candidate_id": candidate_id, "job_id": job_id,
        "salary_offered": salary_offered, "benefits": benefits,
        "status": "pending", "sent_date": _now(),
        "expiry_date": None, "accepted_date": None,
        "created_at": _now(),
    }

    # Predict acceptance probability using ML model
    predictor = get_offer_predictor()
    if predictor:
        try:
            model = predictor["model"]
            scaler = predictor["scaler"]
            candidates = _read_json(_CANDIDATES_FILE)
            jobs = _read_json(_JOBS_FILE)
            c = next((c for c in candidates if c["id"] == candidate_id), None)
            j = next((j for j in jobs if j["id"] == job_id), None)
            if c:
                features = [[
                    salary_offered,
                    len(c.get("skills", []) or []),
                    c.get("experience_years", 0),
                    c.get("score", 50),
                    j.get("experience_required", 0) if j else 0,
                ]]
                X = scaler.transform(features)
                prob = model.predict_proba(X)[0][1]
                offer["acceptance_probability"] = round(prob, 2)
        except Exception:
            pass

    offers.append(offer)
    _write_json(_OFFERS_FILE, offers)
    return offer


def list_offers():
    return _read_json(_OFFERS_FILE)


def get_offer(offer_id):
    offers = _read_json(_OFFERS_FILE)
    for o in offers:
        if o["id"] == offer_id:
            return o
    return None


def update_offer(offer_id, updates):
    offers = _read_json(_OFFERS_FILE)
    for i, o in enumerate(offers):
        if o["id"] == offer_id:
            offers[i].update(updates)
            _write_json(_OFFERS_FILE, offers)
            return offers[i]
    return None


# ── Interview Bot ──────────────────────────────────────────────────

def save_chat_message(session_id, sender, message):
    path = os.path.join(DATA_DIR, f"chat_{session_id}.json")
    msgs = _read_json(path) if os.path.exists(path) else []
    msgs.append({"sender": sender, "message": message, "timestamp": _now()})
    _write_json(path, msgs)
    return msgs


def get_chat_messages(session_id):
    path = os.path.join(DATA_DIR, f"chat_{session_id}.json")
    return _read_json(path) if os.path.exists(path) else []


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD / ANALYTICS (data-science powered)
# ═══════════════════════════════════════════════════════════════════

def match_candidates_for_job(job_id):
    job = get_job(job_id)
    if not job:
        return None
    resumes = _read_json(_RESUMES_FILE)
    candidates = _read_json(_CANDIDATES_FILE)
    if not resumes and not candidates:
        return []

    required_skills = job.get("skills", [])
    all_people = []

    for r in resumes:
        result = match_skills(r.get("skills", []), required_skills)
        all_people.append({
            "user_id": r["user_id"], "name": r.get("parsed_name", "Unknown"),
            "email": r.get("parsed_email", ""), "skills": r.get("skills", []),
            "match_percentage": result["match_percentage"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "experience_years": calculate_experience_years(r.get("education", [])),
        })
    for c in candidates:
        result = match_skills(c.get("skills", []), required_skills)
        all_people.append({
            "user_id": c["id"], "name": c.get("name", "Unknown"),
            "email": c.get("email", ""), "skills": c.get("skills", []),
            "match_percentage": result["match_percentage"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "experience_years": c.get("experience_years", 0),
        })

    return rank_candidates(all_people)


def get_dashboard():
    """Data-science powered dashboard with analytics."""
    try:
        resumes = _read_json(_RESUMES_FILE)
        jobs = _read_json(_JOBS_FILE)
        candidates = _read_json(_CANDIDATES_FILE)
        interviews = _read_json(_INTERVIEWS_FILE)
        offers = _read_json(_OFFERS_FILE)

        total_candidates = len(set(r["user_id"] for r in resumes)) + len(candidates)
        total_resumes = len(resumes)
        total_jobs = len(jobs)
        total_interviews = len(interviews)
        total_offers = len(offers)
        accepted_offers = sum(1 for o in offers if o.get("status") == "accepted")

        # Skill gap analysis
        all_skills_counts = Counter()
        for r in resumes:
            for s in r.get("skills", []):
                all_skills_counts[s.lower()] += 1
        for c in candidates:
            for s in c.get("skills", []):
                all_skills_counts[s.lower()] += 1

        total_people = total_candidates or 1
        skill_gaps = [
            {"skill": skill, "count": count, "pct": round(count / total_people * 100, 1)}
            for skill, count in all_skills_counts.most_common(20)
        ]

        # Education distribution
        edu_levels = Counter()
        for r in resumes:
            for edu in r.get("education", []):
                el = edu.lower()
                if "phd" in el or "ph.d" in el: edu_levels["PhD"] += 1
                elif "master" in el or "m.tech" in el or "m.sc" in el: edu_levels["Master"] += 1
                elif "bachelor" in el or "b.tech" in el or "b.sc" in el: edu_levels["Bachelor"] += 1
                else: edu_levels["Other"] += 1
        education_dist = [{"level": k, "count": v} for k, v in edu_levels.items()]

        # Top candidates
        all_skills = set()
        for j in jobs:
            all_skills.update(j.get("skills", []))
        people_list = []
        for r in resumes:
            result = match_skills(r.get("skills", []), list(all_skills))
            people_list.append({
                "name": r.get("parsed_name", "Unknown"), "skills": r.get("skills", []),
                "match_percentage": result["match_percentage"],
                "experience_years": calculate_experience_years(r.get("education", [])),
            })
        for c in candidates:
            result = match_skills(c.get("skills", []), list(all_skills))
            people_list.append({
                "name": c.get("name", "Unknown"), "skills": c.get("skills", []),
                "match_percentage": result["match_percentage"],
                "experience_years": c.get("experience_years", 0),
            })
        top_candidates = rank_candidates(people_list)[:10]

        # Interview analytics
        avg_sentiment = 0.0
        if interviews:
            scores = [iv.get("sentiment_score", 0) for iv in interviews]
            avg_sentiment = round(np.mean(scores), 2)

        # Status funnel
        status_funnel = {
            "new": sum(1 for c in candidates if c.get("status") == "new"),
            "screened": sum(1 for c in candidates if c.get("status") == "screened"),
            "interviewed": sum(1 for c in candidates if c.get("status") == "interviewed"),
            "offered": sum(1 for c in candidates if c.get("status") == "offered"),
            "hired": sum(1 for c in candidates if c.get("status") == "hired"),
        }
        if resumes:
            status_funnel["new"] += len(resumes)

        return {
            "total_candidates": total_candidates,
            "total_resumes": total_resumes,
            "total_jobs": total_jobs,
            "total_interviews": total_interviews,
            "total_offers": total_offers,
            "accepted_offers": accepted_offers,
            "top_candidates": top_candidates,
            "skill_gaps": skill_gaps,
            "education_distribution": education_dist,
            "status_funnel": status_funnel,
            "avg_sentiment": avg_sentiment,
        }
    except Exception:
        return {
            "total_candidates": 0, "total_resumes": 0, "total_jobs": 0,
            "total_interviews": 0, "total_offers": 0, "accepted_offers": 0,
            "top_candidates": [], "skill_gaps": [], "education_distribution": [],
            "status_funnel": {}, "avg_sentiment": 0.0,
        }
