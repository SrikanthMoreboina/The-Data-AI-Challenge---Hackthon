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

## 4. Double-Precision Score Rounding Discrepancy (Rank Tie-Breaks)
* **Bug**: In testing, the output CSV failed validation check rule: `Equal scores at ranks 63 and 64: tie-break requires candidate_id ascending ('CAND_0010149' > 'CAND_0008677')`.
* **Analysis**: The candidate scorer calculated scores as double-precision floats (e.g. `0.53074` vs `0.53068`). Since `0.53074 > 0.53068`, they were sorted correctly. However, the CSV output rounded values to 4 decimal places, printing both as `0.5307`. The validator read the CSV, processed them as equal scores, and triggered a tie-break failure because the raw values were sorted but the printed rounded values violated lexicographical order.
* **Resolution**: Pre-rounded all score evaluations to exactly **4 decimal places** (`score = round(..., 4)`) *prior* to pushing them onto the Min-Heap. This ensures that any decimal-rounding ties are detected and resolved lexicographically by Candidate ID in the heap comparison key.

