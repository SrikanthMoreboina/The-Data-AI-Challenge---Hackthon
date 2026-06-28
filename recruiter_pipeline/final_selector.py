# recruiter_pipeline/final_selector.py
"""
Final Selector.
Orchestrates the pipeline: screens, scores, sorts, and writes output files.
"""

import csv
from pathlib import Path
from recruiter_pipeline.resume_fetcher import stream_candidates, classify_employer_history
from recruiter_pipeline.resume_screener import screen_candidate
from recruiter_pipeline.candidate_scorer import evaluate_candidate_score
from recruiter_pipeline.interview_prober import generate_reasoning, generate_interview_probes

def select_top_candidates(candidates_path, output_csv_path, debug_csv_path):
    """
    Ingests all candidates, filters out honeypots/unqualified,
    scores and ranks the remaining candidates, and exports submission and debug CSVs.
    """
    scored_candidates = []
    
    # 1. Stream, Screen, and Score
    print(f"Streaming and scoring candidates from: {candidates_path}")
    count = 0
    screened_out = 0
    
    for candidate in stream_candidates(candidates_path):
        count += 1
        if count % 10000 == 0:
            print(f"Processed {count} profiles...")
            
        # Run pre-screening checks
        is_passed, reason = screen_candidate(candidate)
        if not is_passed:
            screened_out += 1
            continue
            
        # Score candidate
        score = evaluate_candidate_score(candidate)
        
        scored_candidates.append({
            "candidate_id": candidate.get("candidate_id"),
            "score": score,
            "raw_candidate": candidate
        })
        
    print(f"Total parsed: {count} | Passed screening: {len(scored_candidates)} | Screened out: {screened_out}")
    
    # 2. Sort candidates with strict tie-breaking
    # Primary key: Score (descending)
    # Secondary key: Candidate ID (ascending - lexicographical tie-breaker)
    print("Sorting candidates and resolving tie-breaks...")
    scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Slice the top 100
    top_100 = scored_candidates[:100]
    
    # 3. Post-Process (Generate reasonings and interview questions)
    print("Generating recruiter reasonings and interview questions...")
    for idx, cand in enumerate(top_100):
        raw = cand["raw_candidate"]
        cand["rank"] = idx + 1
        cand["reasoning"] = generate_reasoning(raw, cand["score"])
        cand["probes"] = generate_interview_probes(raw)
        
    # 4. Write official submission CSV
    out_path = Path(output_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing official submission CSV to: {output_csv_path}")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for cand in top_100:
            writer.writerow([
                cand["candidate_id"],
                cand["rank"],
                f"{cand['score']:.4f}",
                cand["reasoning"]
            ])
            
    # 5. Write detailed debugging CSV
    debug_path = Path(debug_csv_path)
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing recruiter detailed debug CSV to: {debug_csv_path}")
    with open(debug_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "candidate_id", "rank", "score", "location", 
            "years_of_experience", "employer_type", "reasoning", 
            "interview_probe_1", "interview_probe_2", "interview_probe_3"
        ])
        
        for cand in top_100:
            raw = cand["raw_candidate"]
            profile = raw.get("profile", {})
            career_history = raw.get("career_history", [])
            
            probes = cand["probes"]
            # Fill missing probes with blank space
            while len(probes) < 3:
                probes.append("")
                
            writer.writerow([
                cand["candidate_id"],
                cand["rank"],
                f"{cand['score']:.4f}",
                profile.get("location", ""),
                profile.get("years_of_experience", 0.0),
                classify_employer_history(career_history),
                cand["reasoning"],
                probes[0],
                probes[1],
                probes[2]
            ])
            
    print("Pipeline run completed successfully.")
