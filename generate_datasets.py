"""Generate realistic synthetic datasets for ML training."""
import json, csv, random, os
from datetime import datetime, timedelta

random.seed(42)
DATA_DIR = "datasets"
os.makedirs(DATA_DIR, exist_ok=True)

# ── Personal names ──────────────────────────────────────────────
FIRST = ["Aarav","Vivaan","Aditya","Vihaan","Arjun","Sai","Ishaan","Ayaan","Reyansh","Shaurya",
         "Pratyush","Siddharth","Rohan","Kabir","Dhruv","Aryan","Anaya","Ishika","Myra","Aanya",
         "Diya","Avni","Sara","Riya","Navya","Aditi","Pari","Jhanvi","Ananya","Tanvi",
         "James","Mary","Robert","Patricia","John","Jennifer","David","Linda","Richard","Barbara",
         "Michael","Susan","William","Jessica","Joseph","Sarah","Thomas","Karen","Daniel","Lisa"]
LAST  = ["Kumar","Sharma","Patel","Singh","Verma","Reddy","Joshi","Gupta","Das","Rao",
         "Nair","Iyer","Menon","Sen","Bose","Mishra","Pandey","Tiwari","Dubey","Chauhan",
         "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Taylor"]

# ── Skills pool ─────────────────────────────────────────────────
SKILLS = {
    "programming": ["Python","Java","JavaScript","TypeScript","C++","C#","Go","Rust","Kotlin","Swift"],
    "web": ["React","Angular","Vue.js","Node.js","Django","Flask","Spring Boot","Express","Next.js","FastAPI"],
    "data": ["Pandas","NumPy","SQL","Tableau","Power BI","Excel","R","MATLAB","SAS","SPSS"],
    "ml": ["TensorFlow","PyTorch","scikit-learn","Keras","XGBoost","LightGBM","OpenCV","NLTK","spaCy","LangChain"],
    "cloud": ["AWS","Azure","GCP","Docker","Kubernetes","Terraform","Jenkins","GitHub Actions","Ansible","Prometheus"],
    "soft": ["Leadership","Communication","Problem Solving","Teamwork","Time Management","Critical Thinking",
             "Adaptability","Conflict Resolution","Presentation","Project Management"],
}
ALL_SKILLS = [s for cat in SKILLS.values() for s in cat]

# ── Job titles / departments ────────────────────────────────────
ROLES = {
    "Software Engineer": {"skills": ["programming","web"]},
    "Data Scientist": {"skills": ["ml","data","programming"]},
    "ML Engineer": {"skills": ["ml","programming","cloud"]},
    "DevOps Engineer": {"skills": ["cloud","programming"]},
    "Product Manager": {"skills": ["soft","web"]},
    "HR Manager": {"skills": ["soft"]},
    "Marketing Analyst": {"skills": ["data","soft"]},
    "Backend Developer": {"skills": ["programming","web","cloud"]},
    "Frontend Developer": {"skills": ["web","programming"]},
    "Full Stack Developer": {"skills": ["web","programming","cloud"]},
    "Data Analyst": {"skills": ["data","ml"]},
    "Cloud Architect": {"skills": ["cloud","programming"]},
    "UX Designer": {"skills": ["web","soft"]},
    "Security Engineer": {"skills": ["programming","cloud"]},
    "Business Analyst": {"skills": ["data","soft"]},
}

COMPANIES = ["Google","Microsoft","Amazon","Meta","Apple","Netflix","Uber","Airbnb","Spotify","Twitter",
             "Goldman Sachs","JPMorgan","Deloitte","PwC","Accenture","Infosys","TCS","Wipro","Flipkart","Swiggy",
             "Stripe","Palantir","Databricks","Snowflake","Twilio","Shopify","Square","Pinterest","LinkedIn","Salesforce"]

def gen_person():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"

def gen_skills(n_min=3, n_max=10):
    return random.sample(ALL_SKILLS, random.randint(n_min, n_max))

def gen_experience_years():
    return round(random.uniform(0.5, 15), 1)

def gen_email(name):
    domains = ["gmail.com","outlook.com","yahoo.com","icloud.com","proton.me"]
    return name.lower().replace(" ",".") + str(random.randint(1,99)) + "@" + random.choice(domains)

def gen_phone():
    return f"+1 ({random.randint(200,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}"


# ═══════════════════════════════════════════════════════════════════
# 1. CANDIDATES + RESUME DATA (500 candidates)
# ═══════════════════════════════════════════════════════════════════
print("Generating candidates & resumes...")
candidates = []
resumes = []
for i in range(500):
    name = gen_person()
    email = gen_email(name)
    phone = gen_phone()
    skills = gen_skills(4, 12)
    exp_years = gen_experience_years()
    role = random.choice(list(ROLES.keys()))
    dept_skills = ROLES[role]["skills"]
    selected = [s for s in skills if any(s in SKILLS[ds] for ds in dept_skills)]
    if not selected:
        selected = skills[:2]

    candidates.append({
        "id": f"C{i+1:04d}", "name": name, "email": email, "phone": phone,
        "skills": skills, "status": random.choice(["new","screened","interviewed","offered","hired"]),
        "score": round(random.uniform(0, 100), 1),
        "experience_years": exp_years,
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
    })
    resumes.append({
        "id": f"R{i+1:04d}", "user_id": f"C{i+1:04d}", "filename": f"resume_{i+1}.pdf",
        "parsed_name": name, "parsed_email": email, "parsed_phone": phone,
        "skills": skills, "education": [f"{random.choice(['B.Tech','M.Tech','B.Sc','MBA','PhD'])} in {random.choice(['CS','IT','ECE','Business','Math'])}"],
        "raw_text": f"Experienced {role} with skills in {', '.join(skills[:6])}.",
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
    })

with open(f"{DATA_DIR}/candidates.json", "w") as f:
    json.dump(candidates, f, indent=2)
with open(f"{DATA_DIR}/resumes.json", "w") as f:
    json.dump(resumes, f, indent=2)
print(f"  {len(candidates)} candidates")
print(f"  {len(resumes)}   resumes")

# ═══════════════════════════════════════════════════════════════════
# 2. JOB POSTINGS (30 jobs)
# ═══════════════════════════════════════════════════════════════════
print("Generating jobs...")
jobs = []
for i, (title, info) in enumerate(ROLES.items()):
    n_skills = random.randint(3, 7)
    role_skills = []
    for cat in info["skills"]:
        role_skills.extend(random.sample(SKILLS[cat], min(n_skills, len(SKILLS[cat]))))
    jobs.append({
        "id": f"J{i+1:04d}", "title": title,
        "description": f"We are looking for a talented {title} to join our team at {random.choice(COMPANIES)}.",
        "skills": role_skills[:n_skills],
        "experience_required": random.randint(1, 8),
        "status": random.choice(["open","open","open","closed"]),
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
    })

with open(f"{DATA_DIR}/jobs.json", "w") as f:
    json.dump(jobs, f, indent=2)
print(f"  {len(jobs)} jobs")

# ═══════════════════════════════════════════════════════════════════
# 3. INTERVIEW RECORDS (200 interviews)
# ═══════════════════════════════════════════════════════════════════
print("Generating interviews...")
interviews = []
sentiments = []
for i in range(200):
    c = random.choice(candidates)
    j = random.choice(jobs)
    sentiment = round(random.uniform(-1, 1), 2)
    sentiments.append(sentiment)
    feedbacks = [
        "Strong technical skills, great communication",
        "Needs improvement in system design",
        "Excellent problem solver",
        "Average performance, could be better",
        "Outstanding candidate, highly recommend",
    ]
    interviews.append({
        "id": f"IV{i+1:04d}", "candidate_id": c["id"], "job_id": j["id"],
        "interview_type": random.choice(["technical","behavioral","hr","coding"]),
        "status": random.choice(["scheduled","completed","completed","completed"]),
        "scheduled_date": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
        "feedback": random.choice(feedbacks),
        "transcript": f"Candidate discussed experience with {', '.join(c['skills'][:3])}.",
        "sentiment_score": sentiment,
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
    })

with open(f"{DATA_DIR}/interviews.json", "w") as f:
    json.dump(interviews, f, indent=2)
print(f"  {len(interviews)} interviews")

# ═══════════════════════════════════════════════════════════════════
# 4. OFFERS (100 offers)
# ═══════════════════════════════════════════════════════════════════
print("Generating offers...")
offers = []
for i in range(100):
    c = random.choice(candidates)
    j = random.choice(jobs)
    salary = random.randint(50000, 250000)
    offers.append({
        "id": f"O{i+1:04d}", "candidate_id": c["id"], "job_id": j["id"],
        "salary_offered": salary,
        "benefits": random.choice(["Health insurance, 401k", "Full benefits, equity", "Standard package", "Premium package"]),
        "status": random.choice(["pending","accepted","rejected"]),
        "sent_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
    })

with open(f"{DATA_DIR}/offers.json", "w") as f:
    json.dump(offers, f, indent=2)
# Also write for the app's data folder
import shutil
APP_DATA = os.path.join(os.path.dirname(DATA_DIR), "data")
os.makedirs(APP_DATA, exist_ok=True)
for fname in ["candidates.json","resumes.json","jobs.json","interviews.json","offers.json"]:
    shutil.copy2(f"{DATA_DIR}/{fname}", f"{APP_DATA}/{fname}")
print(f"  {len(offers)} offers")
print(f"\nCopied to {APP_DATA}/ for immediate app use")
print("Done!")
