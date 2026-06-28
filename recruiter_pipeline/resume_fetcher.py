# recruiter_pipeline/resume_fetcher.py
"""
Resume Fetcher.
Handles low-memory streaming of candidates.jsonl, 
text normalization, and employer background classification.
"""

import json
import gzip
from recruiter_pipeline.hiring_rubric import IT_SERVICES_FIRMS

def stream_candidates(file_path):
    """
    Streams candidates from a .jsonl or .jsonl.gz file line-by-line.
    This prevents loading the entire 465MB file into RAM at once.
    """
    file_path_str = str(file_path)
    if file_path_str.endswith(".gz"):
        open_func = lambda fp: gzip.open(fp, "rt", encoding="utf-8")
    else:
        open_func = lambda fp: open(fp, "r", encoding="utf-8")
        
    with open_func(file_path) as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def normalize_text(text):
    """
    Cleans and lowercases text for uniform keyword matching.
    """
    if not text:
        return ""
    return text.lower().strip()

def classify_employer_history(career_history):
    """
    Classifies a candidate's career background into one of:
    - 'services_only': worked only at IT service firms
    - 'product_only': worked only at product/startup companies
    - 'hybrid': worked at a mix of service and product companies
    """
    if not career_history:
        return "product_only"  # Default assumption if career history is empty
    
    total_jobs = len(career_history)
    service_jobs_count = 0
    
    for job in career_history:
        company_name = normalize_text(job.get("company", ""))
        
        # Check if the company name contains any of our target services firms
        is_service = False
        for firm in IT_SERVICES_FIRMS:
            if firm in company_name:
                is_service = True
                break
        
        if is_service:
            service_jobs_count += 1
            
    if service_jobs_count == total_jobs:
        return "services_only"
    elif service_jobs_count == 0:
        return "product_only"
    else:
        return "hybrid"
