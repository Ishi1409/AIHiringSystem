from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILL_DB = [
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "rust", "swift", "kotlin", "php", "scala", "r",
    "react", "angular", "vue", "svelte", "next.js", "nuxt.js",
    "node.js", "express", "django", "flask", "spring boot", "fastapi",
    "html", "css", "sass", "tailwind", "bootstrap",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "github", "gitlab", "jenkins", "ci/cd",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "rest api", "graphql", "grpc",
    "linux", "bash", "powershell",
    "agile", "scrum", "jira", "confluence",
    "communication", "leadership", "teamwork", "problem solving",
    "data structures", "algorithms", "oop", "design patterns",
    "unit testing", "integration testing", "selenium", "jest",
    "tableau", "power bi", "excel", "spss",
    "blockchain", "solidity", "web3",
    "figma", "sketch", "adobe xd", "photoshop",
]


def extract_skills(text, custom_skills=None):
    skills = custom_skills if custom_skills else SKILL_DB
    found = []
    text_lower = text.lower()
    for skill in skills:
        if skill.lower() in text_lower:
            found.append(skill)

    if not found:
        vectorizer = TfidfVectorizer().fit([text] + skills)
        vectors = vectorizer.transform([text] + skills)
        similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
        top_indices = similarities.argsort()[-5:][::-1]
        found = [skills[i] for i in top_indices if similarities[i] > 0.1]

    return list(set(found))
