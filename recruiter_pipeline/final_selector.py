import heapq
import csv
import json
import gzip
import multiprocessing
from pathlib import Path
from recruiter_pipeline.resume_fetcher import classify_employer_history
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

def process_single_candidate(candidate_raw_str):
    """
    Worker process target function: parses, screens, and scores a single candidate.
    Returns (score, candidate_id, candidate) or None if screened out.
    """
    if not candidate_raw_str.strip():
        return None
    try:
        candidate = json.loads(candidate_raw_str)
    except json.JSONDecodeError:
        return None
        
    is_passed, reason = screen_candidate(candidate)
    if not is_passed:
        return None
        
    # Score candidate and round to 4 decimal places to prevent decimal-tie validation errors
    score = round(evaluate_candidate_score(candidate), 4)
    candidate_id = candidate.get("candidate_id")
    return (score, candidate_id, candidate)

def stream_raw_lines(file_path):
    """
    Streams raw lines from a .jsonl or .jsonl.gz file to workers.
    """
    file_path_str = str(file_path)
    if file_path_str.endswith(".gz"):
        open_func = lambda fp: gzip.open(fp, "rt", encoding="utf-8")
    else:
        open_func = lambda fp: open(fp, "r", encoding="utf-8")
        
    with open_func(file_path) as f:
        for line in f:
            if line.strip():
                yield line

def select_top_candidates(candidates_path, output_csv_path, debug_csv_path=None, write_debug=False):
    """
    Ingests all candidates using a multiprocessing Pool, filters out honeypots/unqualified,
    scores and streams the top 100 candidates into a bounded Min-Heap,
    and exports submission and debug CSVs.
    """
    heap = []
    
    # 1. Stream, Screen, and Score using a Multiprocessing Pool
    print(f"Streaming and scoring candidates in parallel from: {candidates_path}")
    count = 0
    screened_out = 0
    
    # Determine CPU cores count
    num_cores = max(1, multiprocessing.cpu_count())
    print(f"Spawning worker pool with {num_cores} cores...")
    
    with multiprocessing.Pool(processes=num_cores) as pool:
        # Use imap to process candidates in chunks lazily to save memory
        results = pool.imap(process_single_candidate, stream_raw_lines(candidates_path), chunksize=1000)
        
        for result in results:
            count += 1
            if count % 10000 == 0:
                print(f"Processed {count} profiles...")
                
            if result is None:
                screened_out += 1
                continue
                
            score, candidate_id, candidate = result
            
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
            
    # 5. Write detailed debugging CSV (only if debug mode is active)
    if write_debug and debug_csv_path:
        try:
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
        except Exception:
            pass
            
    print("Pipeline run completed successfully.")
    return {
        "total_parsed": count,
        "passed_screening": count - screened_out,
        "screened_out": screened_out,
        "num_cores": num_cores
    }

