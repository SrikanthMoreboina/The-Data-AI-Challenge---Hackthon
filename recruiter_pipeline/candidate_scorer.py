# recruiter_pipeline/candidate_scorer.py
"""
Candidate Scorer.
Computes technical base scores and applies recruiter weight multipliers.
"""

import math
from datetime import date
from recruiter_pipeline.hiring_rubric import (
    SKILL_WEIGHTS, TITLE_WEIGHTS, LOCATION_MULTIPLIERS, 
    EMPLOYER_MULTIPLIERS, TARGET_HUBS, TIER_1_INDIAN_CITIES,
    NON_TECH_TITLES, TUTORIAL_INDICATORS
)
from recruiter_pipeline.resume_fetcher import normalize_text, classify_employer_history
from recruiter_pipeline.resume_screener import parse_date_string, REFERENCE_DATE

def calculate_base_score(candidate):
    """
    Calculates the candidate's core technical base score (0 to 100 points)
    with hybrid scaling for skill depth, title blocking, and learning/tutorial filters.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    
    headline = normalize_text(profile.get("headline", ""))
    summary = normalize_text(profile.get("summary", ""))
    
    base_score = 0.0
    
    # Check each skill group weights
    for group_name, info in SKILL_WEIGHTS.items():
        points = info["points"]
        keywords = info["keywords"]
        
        matched = False
        matched_skill_obj = None
        
        for kw in keywords:
            # A. Check explicit skills array (highest trust)
            for s in skills:
                if normalize_text(s.get("name", "")) == kw:
                    matched = True
                    matched_skill_obj = s
                    break
            if matched:
                break
                
            # B. Check Headline (high trust, very short summary of self)
            if kw in headline:
                matched = True
                break
                
            # C. Check Summary (verify learning indicators)
            if kw in summary:
                has_tutorial = any(ind in summary for ind in TUTORIAL_INDICATORS)
                if not has_tutorial:
                    matched = True
                    break
                    
            # D. Check Career History (verify non-tech role blockers and learning indicators)
            for job in career_history:
                job_title = normalize_text(job.get("title", ""))
                
                # Blocker check: Skip if it's a non-tech role
                is_non_tech = any(non_tech in job_title for non_tech in NON_TECH_TITLES)
                if is_non_tech:
                    continue
                    
                job_desc = normalize_text(job.get("description", ""))
                full_job_text = f"{job_title} {job_desc}"
                
                if kw in full_job_text:
                    # Check if job description contains tutorial keywords
                    has_tutorial = any(ind in job_desc for ind in TUTORIAL_INDICATORS)
                    if not has_tutorial:
                        matched = True
                        break
            if matched:
                break
                
        if matched:
            if matched_skill_obj:
                endorsements = matched_skill_obj.get("endorsements", 0)
                duration = matched_skill_obj.get("duration_months", 0)
                
                # Diminishing returns: cap duration at 24 months
                capped_duration = min(24, duration)
                # Power-law normalization: log-scale endorsements
                log_ends = math.log2(1 + endorsements)
                
                F_depth = 1.0 + 0.05 * log_ends + 0.05 * (capped_duration / 12.0)
                base_score += points * F_depth
            else:
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
    Computes all weight multipliers (Experience, Location, Employer, Availability, and Behavior).
    Returns (M_exp, M_loc, M_emp, M_avail, M_behavior)
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
        # Senior candidate check. Active coder override on Github cancels penalty.
        github_score = signals.get("github_activity_score", -1)
        if github_score >= 70:
            M_exp = 1.0  # Active coder override (no seniority penalty)
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
    
    # --- E. Platform Behavioral Signals Multiplier ---
    M_behavior = 1.0
    
    # 1. Open to work flag (1.1 boost if active job seeker)
    if signals.get("open_to_work_flag", False):
        M_behavior *= 1.1
        
    # 2. Profile completeness (up to 5% boost for highly complete profiles)
    completeness = signals.get("profile_completeness_score", 100.0)
    M_behavior *= (1.0 + 0.05 * (completeness / 100.0))
    
    # 3. Verified contact credentials (up to 2% boost for verifications)
    email_ver = signals.get("verified_email", False)
    phone_ver = signals.get("verified_phone", False)
    contact_boost = 1.0
    if email_ver: contact_boost += 0.01
    if phone_ver: contact_boost += 0.01
    M_behavior *= contact_boost
    
    # 4. Recruiter saves in last 30 days (log-scaled count boost, capped max +10%)
    saved_count = signals.get("saved_by_recruiters_30d", 0)
    if saved_count > 0:
        M_behavior *= (1.0 + min(0.1, 0.03 * math.log2(1 + saved_count)))
        
    # 5. Reliability: Interview completion rate
    inter_rate = signals.get("interview_completion_rate", 1.0)
    M_behavior *= (0.9 + 0.1 * inter_rate)
    
    # 6. Offer acceptance rate (-1 if no history, otherwise linear scale)
    offer_rate = signals.get("offer_acceptance_rate", -1.0)
    if offer_rate >= 0:
        M_behavior *= (0.95 + 0.05 * offer_rate)
        
    # 7. Redrob Skill Assessment scores
    assessment_scores = signals.get("skill_assessment_scores", {})
    if assessment_scores:
        scores_list = list(assessment_scores.values())
        if scores_list:
            avg_assessment = sum(scores_list) / len(scores_list)
            M_behavior *= (1.0 + 0.05 * (avg_assessment / 100.0))
            
    # 8. Salary Fit: Cap budget at 50 LPA expected min salary
    expected_salary = signals.get("expected_salary_range_inr_lpa", {})
    if expected_salary:
        min_salary = expected_salary.get("min", 0.0)
        if min_salary > 50.0:
            # Scale down linearly for candidates who exceed our target budget limits
            M_behavior *= max(0.5, 50.0 / min_salary)
            
    return M_exp, M_loc, M_emp, M_avail, M_behavior

def evaluate_candidate_score(candidate):
    """
    Evaluates and calculates the final normalized match score (0.0 to 1.0)
    for a candidate profile, incorporating Tier-1 academic bonus and Redrob behavioral signals.
    """
    base_score = calculate_base_score(candidate)
    M_exp, M_loc, M_emp, M_avail, M_behavior = calculate_multipliers(candidate)
    
    # --- E. Pedigree Modifier ---
    education = candidate.get("education", [])
    has_tier_1 = any(edu.get("tier") == "tier_1" for edu in education)
    M_pedigree = 1.05 if has_tier_1 else 1.0
    
    final_score = base_score * M_exp * M_loc * M_emp * M_avail * M_pedigree * M_behavior
    
    # Normalize score between 0.0 and 1.0 (base score is out of 100 max)
    normalized_score = final_score / 100.0
    
    # Clamp between 0.0 and 1.0
    return max(0.0, min(1.0, normalized_score))
