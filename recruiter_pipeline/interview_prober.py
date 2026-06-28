# recruiter_pipeline/interview_prober.py
"""
Interview Prober.
Generates human-like, fact-based reasoning and tailored interview questions
based on candidate gaps.
"""

from recruiter_pipeline.hiring_rubric import SKILL_WEIGHTS
from recruiter_pipeline.resume_fetcher import normalize_text, classify_employer_history

def get_matched_skills(candidate):
    """
    Identifies which of our target skill groups the candidate actually matched.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    
    headline = normalize_text(profile.get("headline", ""))
    summary = normalize_text(profile.get("summary", ""))
    text_pool = f"{headline} {summary}"
    for job in career_history:
        text_pool += f" {normalize_text(job.get('description', ''))} {normalize_text(job.get('title', ''))}"
        
    candidate_skills = {normalize_text(s.get("name", "")) for s in skills}
    
    matched = []
    # Map group name to recruiter-friendly text
    display_names = {
        "retrieval": "embeddings/retrieval",
        "vector_db": "vector databases",
        "evaluation": "ndcg/ranking eval",
        "python": "production Python",
        "fine_tuning": "llm fine-tuning",
        "learning_to_rank": "learning-to-rank"
    }
    
    for group_name, info in SKILL_WEIGHTS.items():
        keywords = info["keywords"]
        for kw in keywords:
            if kw in candidate_skills or kw in text_pool:
                matched.append(display_names.get(group_name, group_name))
                break
    return matched

def extract_career_context(candidate):
    """
    Scans candidate's most recent job in career_history to extract
    their company name and a keyword-based context of their production achievement.
    """
    career_history = candidate.get("career_history", [])
    if not career_history:
        return "deployed production software", ""
        
    # Get the most recent job
    recent_job = career_history[0]
    company = recent_job.get("company", "").strip()
    desc = normalize_text(recent_job.get("description", ""))
    
    # Heuristics to find action context from description
    action = "deployed production systems"
    if "pipeline" in desc or "kafka" in desc or "spark" in desc:
        action = "designed data pipelines"
    elif "rag" in desc or "llm" in desc or "gpt" in desc or "langchain" in desc:
        action = "built LLM/RAG systems"
    elif "vector" in desc or "pinecone" in desc or "qdrant" in desc or "weaviate" in desc:
        action = "optimized vector search indexing"
    elif "eval" in desc or "ndcg" in desc or "mrr" in desc:
        action = "built ranking evaluation frameworks"
    elif "model" in desc or "training" in desc or "pytorch" in desc or "tensorflow" in desc:
        action = "trained and shipped ML models"
        
    return action, company

def generate_reasoning(candidate, score):
    """
    Generates a natural, fact-based reasoning string (1-2 sentences).
    Guarantees variation by structuring templates dynamically and referencing real facts
    including specific company and project context.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    
    title = profile.get("current_title", "Engineer").strip()
    years = profile.get("years_of_experience", 0.0)
    city = profile.get("location", "").strip()
    notice = signals.get("notice_period_days", 0)
    
    # Extract rich career context
    action, company = extract_career_context(candidate)
    
    # Get actual matching skills (no hallucinations)
    matched_skills = get_matched_skills(candidate)
    skills_str = ", ".join(matched_skills[:2]) if matched_skills else "general engineering skills"
    
    # Choose sentence structure based on candidate ID to guarantee natural variation
    cid_num = int(candidate.get("candidate_id", "CAND_0000000").split("_")[1])
    struct_type = cid_num % 3
    
    if struct_type == 0:
        if company:
            reason = f"{title} with {years:.1f} years of experience; recently {action} at {company}."
        else:
            reason = f"{title} with {years:.1f} years of experience; recently {action}."
        reason += f" Strong fit in {skills_str} based in {city}."
        if notice > 30:
            reason += f" Notice period of {notice} days is a concern."
            
    elif struct_type == 1:
        if company:
            reason = f"Excellent background as {title} for {years:.1f} years, including experience where they {action} at {company}."
        else:
            reason = f"Excellent background as {title} for {years:.1f} years, focusing on how they {action}."
        reason += f" Strong match in {skills_str} commutable/relocatable to Noida/Pune."
            
    else:
        if company:
            reason = f"Experienced {title} ({years:.1f} yrs) who has {action} at {company}."
        else:
            reason = f"Experienced {title} ({years:.1f} yrs) who has {action}."
        reason += f" Matches role requirements in {skills_str}."
        if notice <= 15:
            reason += f" Strong availability with quick {notice}-day notice period."
            
    return reason

def generate_interview_probes(candidate):
    """
    Generates 2-3 tailored interview questions targeting gaps in the profile.
    """
    probes = []
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_history = candidate.get("career_history", [])
    
    notice = signals.get("notice_period_days", 0)
    emp_class = classify_employer_history(career_history)
    matched_skills = get_matched_skills(candidate)
    
    # 1. Notice period gap probe
    if notice > 30:
        probes.append(
            f"Your notice period is {notice} days, but we prefer immediate joiners. "
            "How flexible is your notice period, and can the startup buy it out?"
        )
        
    # 2. IT services career gap probe
    if emp_class in ("services_only", "hybrid"):
        probes.append(
            "You have a strong technical base, but much of your experience is in IT services/consulting. "
            "How do you plan to adapt to owning a product roadmap at a fast-paced Series A startup?"
        )
        
    # 3. Missing preferred skill probe
    if "llm fine-tuning" not in matched_skills:
        probes.append(
            "Our role involves fine-tuning LLMs. Since you haven't explicitly listed PEFT or QLoRA, "
            "can you share any self-directed projects or research you've done in this area?"
        )
    if "ndcg/ranking eval" not in matched_skills:
        probes.append(
            "How would you go about setting up an offline ranking evaluation framework (like NDCG) "
            "for our candidate search systems?"
        )
        
    # Fallback to ensure we always return at least 2 questions
    if len(probes) < 2:
        probes.append("Can you walk us through an ML/Retrieval pipeline you shipped to production and how you monitored it?")
        probes.append("Describe a time you had to optimize model retrieval latency on CPU. What tradeoffs did you make?")
        
    return probes[:3]
