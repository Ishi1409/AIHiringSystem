# AI Hiring Assistant

A college-level project that automates resume parsing, skill extraction, job matching, and candidate ranking.

**One folder. One command. No separate backend.**

```
streamlit run app.py
```

---

## Quick Start

### 1. Prerequisites

- Python 3.12+ (3.12 recommended — spaCy doesn't yet support 3.14)
- [Supabase](https://supabase.com) free-tier project

### 2. Database setup

Open your Supabase project's **SQL Editor** and run these two files (in order):

| File | What it does |
|------|-------------|
| `supabase/schema.sql` | Creates `profiles`, `resumes`, `jobs` tables with Row Level Security |
| `supabase/storage.sql` | Creates a `resumes` storage bucket with access policies |

### 3. Configure

```bash
cp .env.example .env
```

Fill in your Supabase credentials in `.env`:

| Variable | Where to find it |
|----------|-----------------|
| `SUPABASE_URL` | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_KEY` | Supabase Dashboard → Settings → API → anon public |
| `SUPABASE_SERVICE_KEY` | Supabase Dashboard → Settings → API → service_role |

### 4. Install & run

```bash
# Windows
start.bat

# Or manually:
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run app.py
```

### 5. Use the app

Open **http://localhost:8501**

1. Register as **HR** → Create a job posting with required skills
2. Register as **Candidate** → Upload a resume (PDF, DOCX, or TXT)
3. Switch to HR account → In any job, click **Match Candidates**
4. View the **Dashboard** for stats and rankings

---

## Project Structure

```
ai-hiring-assistant/
├── app.py                  # Single entry point (Streamlit)
├── pages/
│   ├── dashboard.py        # HR Dashboard — stat cards + candidate table
│   ├── upload_resume.py    # Resume upload + AI parsing results
│   └── jobs.py             # Create jobs + match candidates
├── services/
│   ├── supabase_client.py  # All Supabase operations (auth, CRUD, storage)
│   ├── resume_parser.py    # spaCy + regex → name, email, phone, education
│   ├── skill_extractor.py  # Dictionary matching + TF-IDF fallback
│   ├── job_matcher.py      # Set intersection → match % + missing skills
│   └── candidate_ranker.py # Weighted score (70% skill match, 30% experience)
├── utils/
│   └── styles.py           # Apple design system CSS (global nav, pills, cards)
├── supabase/
│   ├── schema.sql          # PostgreSQL tables + RLS policies
│   └── storage.sql         # Storage bucket creation + access rules
├── .env                    # Your Supabase credentials
├── .env.example            # Template (safe to share)
├── requirements.txt        # All dependencies
├── start.bat               # Windows launcher
└── README.md
```

---

## How it works

No Flask, no HTTP calls, no separate servers. Streamlit calls the service functions directly:

```
User ──► Streamlit (app.py)
            │
            ├── pages/dashboard.py ──► services/supabase_client.py ──► Supabase
            ├── pages/upload_resume.py ──► services/resume_parser.py (spaCy)
            │                                └─► services/supabase_client.py
            └── pages/jobs.py ──► services/job_matcher.py
                                   └─► services/candidate_ranker.py
```

### AI Pipeline

```
Upload resume (PDF/DOCX/TXT)
       │
       ▼
  resume_parser.py
       │
       ├── spaCy NER ──────────────► Name
       ├── Regex ──────────────────► Email, Phone
       ├── Keyword matching ───────► Education
       └── Dictionary lookup ──────► Skills (90+ tech skills)
                                    └─ TF-IDF fallback via scikit-learn
       │
       ▼
  job_matcher.py
       │
       ├── match_pct = |candidate ∩ required| / |required| × 100
       └── missing   = required - candidate
       │
       ▼
  candidate_ranker.py
       │
       └── rank_score = 0.7 × (match / max_match) + 0.3 × (exp / max_exp)
```

---

## Design

The UI follows Apple's design language (see `design.md`):

- **Single accent:** `#0066cc` Action Blue for all interactive elements
- **Typography:** SF Pro (system-ui), negative letter-spacing on headlines
- **Layout:** Alternating white/parchment section tiles, 80px vertical rhythm
- **Cards:** `border-radius: 18px`, thin hairlines, no shadows
- **Buttons:** Pill-shaped, `scale(0.95)` on press
- **Nav:** Pure black global nav + parchment frosted sub-nav

---

## Deployment

### Streamlit Cloud (free, 1-click)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from your repo, main file: `app.py`
4. Add Secrets (Streamlit Cloud → Settings → Secrets):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
SUPABASE_SERVICE_KEY = "your-service-role-key"
SUPABASE_BUCKET = "resumes"
```

Streamlit Cloud auto-installs `requirements.txt` on deploy.

(NOTE: You need a **service_role** key because resume uploads use admin storage access. Keep this secret — never commit it.)
