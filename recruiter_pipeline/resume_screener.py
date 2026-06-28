# recruiter_pipeline/resume_screener.py
"""
Resume Screener.
Pre-screens candidates for logical contradictions (honeypots) 
and obvious role disqualifications.
"""

from datetime import datetime, date

# Standard reference date for "current" jobs (since dataset is from mid-2026)
REFERENCE_DATE = date(2026, 6, 30)

def parse_date_string(date_str):
    """
    Parses 'YYYY-MM-DD' date string into a date object.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def get_month_difference(start_date, end_date):
    """
    Calculates the calendar difference in months between two date objects.
    """
    if not start_date or not end_date:
        return 0
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

def is_honeypot(candidate):
    """
    Checks for logical contradictions in the candidate profile.
    Returns True if the profile is a honeypot (trap).
    """
    skills = candidate.get("skills", [])
    career_history = candidate.get("career_history", [])
    education = candidate.get("education", [])
    profile = candidate.get("profile", {})
    
    # 1. Skill Duration Contradiction
    # Trap: Claiming "expert" proficiency but has 0 months of use
    for skill in skills:
        if skill.get("proficiency") == "expert" and skill.get("duration_months", 0) == 0:
            return True

    # 2. Date Span Contradiction
    # Trap: Working at a company longer than the calendar duration between start and end dates
    for job in career_history:
        start_str = job.get("start_date")
        end_str = job.get("end_date")
        reported_months = job.get("duration_months", 0)
        
        start_date = parse_date_string(start_str)
        # If it's the current job, use the REFERENCE_DATE
        end_date = parse_date_string(end_str) if end_str else REFERENCE_DATE
        
        if start_date and end_date:
            actual_span_months = get_month_difference(start_date, end_date)
            # If reported duration is larger than calendar span by more than 3 months
            if reported_months > (actual_span_months + 3):
                return True

    # 3. Skill Inflation Check
    # Trap: Listing 8 or more advanced/expert skills with under 3 years of total experience
    expert_advanced_count = sum(
        1 for s in skills if s.get("proficiency") in ("expert", "advanced")
    )
    total_exp = profile.get("years_of_experience", 0.0)
    if expert_advanced_count >= 8 and total_exp < 3.0:
        return True

    # 4. Education vs. Career Timeline Contradiction
    # Trap: Starting a job before university starts or when too young
    if education and career_history:
        # Find earliest start year of university
        edu_years = [edu.get("start_year") for edu in education if edu.get("start_year")]
        if edu_years:
            earliest_edu_year = min(edu_years)
            
            # Find earliest job start year
            job_years = []
            for job in career_history:
                start_date = parse_date_string(job.get("start_date"))
                if start_date:
                    job_years.append(start_date.year)
            
            if job_years:
                earliest_job_year = min(job_years)
                # If they started working more than 2 years before college started
                if earliest_job_year < (earliest_edu_year - 2):
                    return True

    return False

def screen_candidate(candidate):
    """
    Main screening function.
    Returns (is_passed, reason)
    """
    # Check for honeypots
    if is_honeypot(candidate):
        return False, "honeypot_detected"
        
    profile = candidate.get("profile", {})
    country = profile.get("country", "").lower().strip()
    willing_relocate = candidate.get("redrob_signals", {}).get("willing_to_relocate", False)
    
    # Pre-screen international candidates who aren't willing to relocate
    # (Since we do not sponsor visas, they are not viable candidates)
    if country not in ("india", "in", "") and not willing_relocate:
        return False, "international_no_relocation"
        
    return True, "passed"
