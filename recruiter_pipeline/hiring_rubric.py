# recruiter_pipeline/hiring_rubric.py
"""
Hiring Rubric.
Defines the static job requirements, weights, and multipliers 
for the Senior AI Engineer role at Redrob AI.
"""

# 1. Base Score Technical Skill Weights (Max 80 points)
SKILL_WEIGHTS = {
    # Essential Skills (15 points each)
    "retrieval": {
        "points": 15,
        "keywords": [
            "embeddings", "sentence-transformers", "sentence_transformers", 
            "dense retrieval", "bge", "e5", "colbert", "cross-encoder", 
            "retrieval-augmented generation", "rag", "semantic search", "dense search"
        ]
    },
    "vector_db": {
        "points": 15,
        "keywords": [
            "pinecone", "weaviate", "qdrant", "milvus", 
            "elasticsearch", "opensearch", "faiss", "chroma", "pgvector"
        ]
    },
    "evaluation": {
        "points": 15,
        "keywords": [
            "ndcg", "mrr", "mean reciprocal rank", "map", 
            "mean average precision", "evaluation framework", 
            "ab test", "a/b testing", "rank metrics"
        ]
    },
    "python": {
        "points": 15,
        "keywords": [
            "python", "pytorch", "tensorflow", "numpy", "pandas", "scikit-learn"
        ]
    },
    # Preferred Skills (10 points each)
    "fine_tuning": {
        "points": 10,
        "keywords": [
            "fine-tuning", "fine_tuning", "lora", "qlora", "peft"
        ]
    },
    "learning_to_rank": {
        "points": 10,
        "keywords": [
            "learning-to-rank", "learning_to_rank", "xgboost", "lightgbm"
        ]
    }
}

# 2. Base Score Title Match Weights (Max 20 points)
# Directly related AI engineering titles get full points; generalists get partial points.
TITLE_WEIGHTS = {
    "direct_ai_ml": {
        "points": 20,
        "keywords": ["ai engineer", "machine learning", "ml engineer", "data scientist", "nlp engineer", "applied scientist"]
    },
    "software_generalist": {
        "points": 10,
        "keywords": ["software engineer", "backend engineer", "full stack", "tech lead", "developer"]
    }
}

# 3. Location Configurations & Multipliers
TARGET_HUBS = {"pune", "noida"}
TIER_1_INDIAN_CITIES = {"bangalore", "bengaluru", "hyderabad", "mumbai", "delhi", "gurgaon", "gurugram", "chennai"}

LOCATION_MULTIPLIERS = {
    "target_hub": 1.2,        # Currently in Noida/Pune
    "tier_1_relocate": 1.0,   # In Tier-1 Indian city and willing to relocate
    "other_relocate": 0.8,    # Other Indian cities and willing to relocate
    "not_relocatable": 0.1,   # In India but unwilling to relocate
    "international": 0.1      # Outside India (no visa sponsorship)
}

# 4. IT Services Companies Blocklist (to identify service-only careers)
IT_SERVICES_FIRMS = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "tech mahindra", "mindtree", "hcl", 
    "l&t", "larsen & toubro", "lti", "dxc technology", "genpact", "wns", "mphasis"
}

# 5. Non-Technical / Blocker Job Titles (unrelated to hands-on AI/ML development)
NON_TECH_TITLES = {
    "marketing", "sales", "writer", "hr specialist", "recruiter", "graphic designer", 
    "content creator", "product manager", "project manager", "scrum master", "analyst"
}

# 6. Tutorial / Classroom learning context markers (indicates non-production toy projects)
TUTORIAL_INDICATORS = {
    "tutorial", "bootcamp", "course project", "dummy project", "toy project", 
    "udemy", "coursera", "class project", "classroom", "academic project"
}


EMPLOYER_MULTIPLIERS = {
    "product_only": 1.1,      # Only startup or product company history
    "hybrid": 0.8,            # Mix of IT services and product history
    "services_only": 0.1      # Only IT service firms in career history
}
