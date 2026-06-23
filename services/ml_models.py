"""Central ML model loader — loads trained models or falls back to basic logic."""
import os, pickle, logging

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

_models = {}

def _load(name):
    path = os.path.join(MODEL_DIR, f"{name}.pkl")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

def get_skill_extractor():
    if "skill_extractor" not in _models:
        _models["skill_extractor"] = _load("skill_extractor")
    return _models.get("skill_extractor")

def get_job_matcher():
    if "job_matcher" not in _models:
        _models["job_matcher"] = _load("job_matcher")
    return _models.get("job_matcher")

def get_candidate_ranker():
    if "candidate_ranker" not in _models:
        _models["candidate_ranker"] = _load("candidate_ranker")
    return _models.get("candidate_ranker")

def get_sentiment_model():
    if "sentiment_model" not in _models:
        _models["sentiment_model"] = _load("sentiment_model")
    return _models.get("sentiment_model")

def get_offer_predictor():
    if "offer_predictor" not in _models:
        _models["offer_predictor"] = _load("offer_predictor")
    return _models.get("offer_predictor")

def models_available():
    return all(os.path.exists(os.path.join(MODEL_DIR, f"{n}.pkl"))
               for n in ["skill_extractor", "job_matcher", "candidate_ranker",
                         "sentiment_model", "offer_predictor"])
