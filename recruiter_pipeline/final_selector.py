# recruiter_pipeline/final_selector.py
"""
Final Selector.
Orchestrates the pipeline: screens, scores, sorts, and writes output files.
"""

import heapq
import csv
from pathlib import Path
from recruiter_pipeline.resume_fetcher import stream_candidates, classify_employer_history
from recruiter_pipeline.resume_screener import screen_candidate
from recruiter_pipeline.candidate_scorer import evaluate_candidate_score
from recruiter_pipeline.interview_prober import generate_reasoning, generate_interview_probes

def get_heap_key(score, candidate_id):
    """
    Constructs a comparison key for the Min-Heap.
    Python compares tuples lexicographically:
      1. Score (ascending - min score is worst, popped first).
      2. Negative candidate ID integer (descending ID - larger ID number yields a smaller negative key, popped first).
    """
    try:
        id_num = int(candidate_id.split("_")[1])
    except (IndexError, ValueError, TypeError):
        id_num = 0
    return (score, -id_num)

def select_top_candidates(candidates_path, output_csv_path, debug_csv_path):
    """
    Ingests all candidates, filters out honeypots/unqualified,
    scores and streams the top 100 candidates into a bounded Min-Heap,
    and exports submission and debug CSVs.
    """
    heap = []
    
    # 1. Stream, Screen, and Score using a Min-Heap
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
            
        # Score candidate and round to 4 decimal places to prevent decimal-tie validation errors
        score = round(evaluate_candidate_score(candidate), 4)
        candidate_id = candidate.get("candidate_id")
        
        # Construct heap item: (key, candidate_id, score, candidate_data)
        key = get_heap_key(score, candidate_id)
        item = (key, candidate_id, score, candidate)
        
        if len(heap) < 100:
            heapq.heappush(heap, item)
        else:
            # Compare current key with the heap root (worst key in top-100)
            if key > heap[0][0]:
                heapq.heappushpop(heap, item)
                
    print(f"Total parsed: {count} | Passed screening: {count - screened_out} | Screened out: {screened_out}")
    print(f"Heap final size: {len(heap)}")
    
    # 2. Extract and Reverse
    # Since heappop yields elements in ascending order (worst to best),
    # reversing the popped list gives us descending score (and ascending candidate_id).
    print("Extracting candidates from heap and ordering...")
    popped_list = [heapq.heappop(heap) for _ in range(len(heap))]
    popped_list.reverse()
    
    # 3. Post-Process (Generate reasonings and interview questions)
    print("Generating recruiter reasonings and interview questions for the shortlist...")
    top_100 = []
    for idx, (key, candidate_id, score, raw) in enumerate(popped_list):
        top_100.append({
            "candidate_id": candidate_id,
            "rank": idx + 1,
            "score": score,
            "raw_candidate": raw,
            "reasoning": generate_reasoning(raw, score),
            "probes": generate_interview_probes(raw)
        })
        
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
