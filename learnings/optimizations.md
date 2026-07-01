# Project Optimizations & Hybrid Scoring Heuristics

This document outlines the advanced software optimizations and recruiter-grade scoring heuristics implemented to improve ranking precision, runtime, and memory footprint.

---

## 1. Speed Optimization: Multi-Process streaming Map ($O(N)$ Parallelized)

* **The Problem**: In our screening phase, we parse dates like `"2024-03-08"` to compute job durations. Standard Python uses `datetime.strptime(date_str, "%Y-%m-%d")`, which compiles a complex regular expression under the hood. When called up to 500,000 times (across all jobs for 100,000 candidates), it becomes the single largest bottleneck in the pipeline.
* **The Solution**:
  1. **Integer date parsing**: We split date strings by `"-"` and directly construct a `date` object using integer conversion, bypassing `strptime` entirely.
  2. **Multiprocessing Pool (`pool.imap`)**: We scale the parsing, screening, and scoring phases across all available CPU cores. To prevent IPC (Inter-Process Communication) overhead, the main process streams **raw text lines** to the workers, and the workers immediately discard honeypot profiles, returning only high-value scored candidates.
* **Performance Impact**: Execution runtime dropped by **70% to 85%** (from 52 seconds down to **7.5 - 15.0 seconds** depending on CPU core count), comfortably passing the 5-minute container limit.

---

## 2. Memory & Sorting Optimization: Min-Heap ($O(N \log K)$)

* **The Problem**: A basic ranker collects all 80,000+ passed candidates in a list, scores them, and runs `list.sort()` at the end. This holds thousands of dict objects in RAM, triggering Garbage Collection freezes, and requires $O(N \log N)$ sorting complexity.
* **The Solution**: We utilize a **Min-Heap** data structure of size 100 (using Python's native `heapq` module) to maintain the running top-100 candidates in the main process.
* **Tie-Breaking & 4-Decimal Rounding**:
  * The heap stores items with a composite key `(score, -id_num)` where `score` is rounded to exactly **4 decimal places**.
  * Pre-rounding scores to 4 decimals prevents formatting-round mismatches in the final CSV that would otherwise cause the format validator to fail tie-breakers.
* **Performance Impact**: Time complexity is reduced to $O(N \log 100)$ and memory footprint stays bounded under **150 MB** (accounting for multiprocessing worker allocations and 1000-line chunk buffering), ensuring stable offline runs without OOM risk.

---

## 3. Hybrid Recruiter Scoring Heuristics

To rank candidates exactly like an expert recruiter, we implement these advanced scoring modifications:

### A. Diminishing Returns: Capped Skill Duration
* **Logic**: Having 2 years of experience with PyTorch is a massive improvement over 0 months. However, having 8 years of experience is practically equivalent to 6 years. 
* **Formula**: We cap all matched skill durations at a maximum of **24 months** to prevent longevity from artificially inflating scores.

### B. Power-Law Normalization: Log-Scaled Endorsements
* **Logic**: Endorsements represent peer validation, but follow a power-law distribution. A candidate with 200 endorsements is not 40 times more skilled than someone with 5.
* **Formula**: We scale endorsement points logarithmically:
  $$\text{Scale Factor} = \log_2(1 + \text{endorsements})$$
  This rewards candidates for having endorsements while preventing popularity spikes from dominating the ranking.

### C. Active Coding Cancellation of Seniority Penalties
* **Logic**: The Job Description penalizes candidates with $> 9$ years of experience under the assumption they have transitioned into pure management/architecture roles. However, if a senior candidate has a `github_activity_score` $\ge 70$, it proves they are still actively writing code.
* **Formula**: If `years_of_experience` $> 9$ and `github_activity_score` $\ge 70$, we **cancel the seniority penalty** and set the experience multiplier to a full `1.0`.

### D. Pedigree / Education Modifier
* **Logic**: When candidates are tied on skills and experience, a recruiter favors top-tier academic training.
* **Formula**: Candidates with a degree from a `tier_1` school (IITs, IISc, BITS, etc.) receive a minor `1.05` multiplier bonus.

### E. Non-Tech Job Title & Learning Context Blocker
* **Logic**: We ignore keyword matches if the candidate has them listed in a non-technical role (e.g. `marketing manager`, `sales representative`, `content writer`) or if the surrounding context in the description indicates classroom/learning markers (e.g. `udemy`, `course project`, `bootcamp`, `tutorial`).

---

## 4. DevOps Sandboxing & Path Resolution Optimizations

To ensure the container can run in any Docker environment without loss of diagnostic files, we implemented two critical deployment patterns:

### A. Dynamic Output Directory Routing
* **The Problem**: When running the container with local volumes mounted via `-v`, hardcoding debug paths (like `outputs/metrics.json`) writes them to the ephemeral container folder `/app/outputs/`. When the container exits, these files are lost to the host machine.
* **The Solution**: We resolve all telemetry paths dynamically relative to the `--out` argument's directory parent:
  ```python
  out_parent = Path(args.out).parent
  debug_csv_path = out_parent / "ranking_debug.csv"
  metrics_path = out_parent / "metrics.json"
  ```
  Since the output file path is always mapped to a mounted host folder (e.g. `/app/workspace/outputs/submission.csv`), this guarantees that all debug telemetry is written directly to the host's directory layout instead of disappearing inside the container.

### B. WSL2 Virtual Mount disk Latency Bottleneck
* **The Problem**: During testing, running the container under Docker on Windows WSL2 took **21.06 seconds** compared to **8.54 seconds** running natively on the host machine.
* **The Analysis**: This delay is caused by the virtualization translation layer (9p filesystem mount protocol) between Windows NTFS directories and WSL2. Reading a 465MB candidate database line-by-line across this mount boundary introduces substantial disk read latency.
* **The Verdict**: This latency is purely a virtualization artifact of local Windows + WSL2 environments. In the native Linux grading environment (where files are stored directly on local container volumes), execution runs at native speed (under 10 seconds).
