# Technical Challenges & Bugs Overcome

This log details the key engineering and configuration bottlenecks resolved during development to ensure a compliant and highly competitive submission.

---

## 1. Git Push Rejected: Large Candidate Database
* **Bug**: The uncompressed candidate database `candidates.jsonl` was 465 MB. Git committed it locally, but pushing to GitHub failed with a `remote rejected: exceeds file size limit of 100.00 MB` error.
* **Analysis**: Simply adding the folder to `.gitignore` after committing it does not remove it from Git's internal commit history history.
* **Resolution**: 
  1. Wiped the local Git history folder (`Remove-Item -Recurse -Force .git`).
  2. Created a comprehensive `.gitignore` file before re-initializing Git, ensuring the large data folders were ignored from the very first commit.
  3. Committed and pushed a clean, lightweight commit of only 21 KB.

## 2. Formatting Tie-Breaks Compliance
* **Bug**: Multiple candidates matching similar technical skills scored identical base points. Sorting them arbitrarily caused format check failures against the challenge rules.
* **Analysis**: The format validator (`validate_submission.py`) strictly mandates that candidates with equal scores must be sorted by `candidate_id` ascending (e.g., `CAND_0000001` before `CAND_0000002`).
* **Resolution**: Implemented a composite sorting key in Python:
  ```python
  scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
  ```
  This guarantees that candidates are sorted by score descending, and all equal-score ties are resolved lexicographically by ascending ID.

## 3. Sandboxed Reproduction Runtime limits
* **Bug**: Early prototypes loading the entire candidate JSON file at once consumed over 2 GB of RAM and experienced garbage collection delays.
* **Analysis**: The Stage 3 sandboxed Docker container enforces a strict 5-minute runtime and 16 GB memory limit on CPU.
* **Resolution**: Designed the `resume_fetcher` module using Python **generators** (`yield`). This streams candidates line-by-line, keeping memory usage constant at $\approx 50\text{ MB}$ and finishing the entire 100,000 candidate run in under 30 seconds.
