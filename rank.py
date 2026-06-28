# rank.py
"""
Senior AI Engineer Ranker - Recruitment Agency Pipeline.
The primary entrypoint command to run the candidate selection.
Usage:
    python rank.py --candidates <path_to_jsonl> --out <path_to_output_csv>
"""

import argparse
import time
from recruiter_pipeline.final_selector import select_top_candidates

def main():
    parser = argparse.ArgumentParser(
        description="Rank candidate profiles against the Senior AI Engineer hiring rubric."
    )
    parser.add_argument(
        "--candidates", 
        required=True, 
        help="Path to the candidates.jsonl file (or gzipped)"
    )
    parser.add_argument(
        "--out", 
        required=True, 
        help="Path where the official submission.csv should be saved"
    )
    
    args = parser.parse_args()
    
    start_time = time.time()
    print("====================================================")
    print("      RECRUITMENT AGENCY ENGINE: PIPELINE START      ")
    print("====================================================")
    
    # Establish a default debug report output path in the outputs/ folder
    debug_csv_path = "outputs/ranking_debug.csv"
    
    try:
        select_top_candidates(
            candidates_path=args.candidates,
            output_csv_path=args.out,
            debug_csv_path=debug_csv_path
        )
    except Exception as e:
        print(f"\n[FATAL ERROR] Pipeline execution crashed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
        
    duration = time.time() - start_time
    print("====================================================")
    print(f"PIPELINE RUN COMPLETED IN: {duration:.2f} seconds")
    print("====================================================")

if __name__ == "__main__":
    main()
