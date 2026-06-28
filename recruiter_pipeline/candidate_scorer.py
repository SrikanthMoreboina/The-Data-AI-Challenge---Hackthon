# recruiter_pipeline/candidate_scorer.py
"""
Candidate Scorer.
Computes technical base scores and applies recruiter weight multipliers.
"""

import math
from datetime import date
from recruiter_pipeline.hiring_rubric import (
    SKILL_WEIGHTS, TITLE_WEIGHTS, LOCATION_MULTIPLIERS, 
    EMPLOYER_MULTIPLIERS, TARGET_HUBS, TIER_1_INDIAN_CITIES
)
from recruiter_pipeline.resume_fetcher import normalize_text, classify_employer_history
from recruiter_pipeline.resume_screener import parse_date_string, REFERENCE_DATE

def calculate_base_score(candidate):
    """
    Calculates the candidate's core technical base score (0 to 100 points).
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    
    # 1. Compile a single lowercase text pool of all profile copy for quick lookup
    headline = normalize_text(profile.get("headline", ""))
    summary = normalize_text(profile.get("summary", ""))
    
    text_pool = f"{headline} {summary}"
    for job in career_history:
        desc = normalize_text(job.get("description", ""))
        title = normalize_text(job.get("title", ""))
        text_pool += f" {desc} {title}"
        
    # Get set of candidate's explicit skills (lowercased)
    candidate_skills = {normalize_text(s.get("name", "")) for s in skills}
    
    base_score = 0.0
    
    # 2. Check each skill group weights
    for group_name, info in SKILL_WEIGHTS.items():
        points = info["points"]
        keywords = info["keywords"]
        
        # Check if any keyword matches their skills set OR exists inside text pool
        matched = False
        for kw in keywords:
            if kw in candidate_skills or kw in text_pool:
                matched = True
                break
                
        if matched:
            base_score += points
            
    # 3. Job Title Alignment Check
    current_title = normalize_text(profile.get("current_title", ""))
    
    title_points = 0.0
    # Check direct AI/ML match first
    for kw in TITLE_WEIGHTS["direct_ai_ml"]["keywords"]:
        if kw in current_title or kw in headline:
            title_points = TITLE_WEIGHTS["direct_ai_ml"]["points"]
            break
            
    # If no direct AI match, check software generalist keywords
    if title_points == 0.0:
        for kw in TITLE_WEIGHTS["software_generalist"]["keywords"]:
            if kw in current_title or kw in headline:
                title_points = TITLE_WEIGHTS["software_generalist"]["points"]
                break
                
    base_score += title_points
    
    # Cap base score at 100
    return min(100.0, base_score)

def calculate_multipliers(candidate):
    """
    Computes all weight multipliers (Experience, Location, Employer, and Availability).
    Returns (M_exp, M_loc, M_emp, M_avail)
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_history = candidate.get("career_history", [])
    
    # --- A. Experience Multiplier ---
    years_exp = profile.get("years_of_experience", 0.0)
    if 6.0 <= years_exp <= 8.0:
        M_exp = 1.1  # Ideal sweet spot
    elif 5.0 <= years_exp <= 9.0:
        M_exp = 1.0  # Acceptable range
    elif years_exp < 5.0:
        M_exp = max(0.1, 0.1 * years_exp)  # Linear scale down for juniors
    else:
        # Scale down gradually for seniors (e.g. 15 years exp gets ~0.7)
        M_exp = max(0.5, 1.0 - 0.05 * (years_exp - 9.0))
        
    # --- B. Location Multiplier ---
    city = normalize_text(profile.get("location", ""))
    country = normalize_text(profile.get("country", ""))
    willing_relocate = signals.get("willing_to_relocate", False)
    
    # Check target hubs (Pune/Noida)
    is_in_hub = any(hub in city for hub in TARGET_HUBS)
    
    if is_in_hub:
        M_loc = LOCATION_MULTIPLIERS["target_hub"]
    elif country not in ("india", "in", ""):
        # Overseas candidates have case-by-case fit but no visa sponsorship
        M_loc = LOCATION_MULTIPLIERS["international"]
    else:
        # Check Tier-1 Indian relocations
        is_tier_1 = any(t1 in city for t1 in TIER_1_INDIAN_CITIES)
        if willing_relocate:
            M_loc = LOCATION_MULTIPLIERS["tier_1_relocate"] if is_tier_1 else LOCATION_MULTIPLIERS["other_relocate"]
        else:
            M_loc = LOCATION_MULTIPLIERS["not_relocatable"]
            
    # --- C. Employer Multiplier ---
    emp_class = classify_employer_history(career_history)
    M_emp = EMPLOYER_MULTIPLIERS.get(emp_class, 1.0)
    
    # --- D. Availability & Engagement Multiplier ---
    response_rate = signals.get("recruiter_response_rate", 0.0)
    last_active_str = signals.get("last_active_date", "")
    
    # Calculate days since last active
    last_active = parse_date_string(last_active_str)
    if last_active:
        delta_days = (REFERENCE_DATE - last_active).days
        delta_days = max(0, delta_days)
    else:
        delta_days = 365  # Default: 1 year inactive if missing
        
    # Inactivity exponential decay
    A_factor = math.exp(-delta_days / 180.0)
    # Response rate linear scale (0.0 response rate -> 0.5, 1.0 response rate -> 1.0)
    R_factor = 0.5 + 0.5 * response_rate
    
    M_avail = R_factor * A_factor
    
    return M_exp, M_loc, M_emp, M_avail

def evaluate_candidate_score(candidate):
    """
    Evaluates and calculates the final normalized match score (0.0 to 1.0)
    for a candidate profile.
    """
    base_score = calculate_base_score(candidate)
    M_exp, M_loc, M_emp, M_avail = calculate_multipliers(candidate)
    
    final_score = base_score * M_exp * M_loc * M_emp * M_avail
    
    # Normalize score between 0.0 and 1.0 (base score is out of 100 max)
    normalized_score = final_score / 100.0
    
    # Clamp between 0.0 and 1.0
    return max(0.0, min(1.0, normalized_score))
