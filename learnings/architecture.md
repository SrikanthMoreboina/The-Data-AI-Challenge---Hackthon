# System Architecture

Our solution represents a modular **Recruiter reasoning engine** rather than a simple keyword-matching parser. It splits the workflow into dedicated functional steps mapping directly to the roles of a professional recruiting agency.

---

## The Recruiting Agency Pipeline

```mermaid
graph TD
    JSONL[candidates.jsonl] -->|Line-by-line stream| Fetcher[resume_fetcher.py]
    Fetcher -->|1. Parse and Normalise| Screener[resume_screener.py]
    Screener -->|2. Filter Honeypots| Scorer[candidate_scorer.py]
    Scorer -->|3. Evaluate Base Score & Multipliers| Prober[interview_prober.py]
    Prober -->|4. Generate Factual Reasonings & Tailored Probes| Selector[final_selector.py]
    Selector -->|5. Sort, Break Ties, and Export| OutCSV[submission.csv]
    Selector -->|5. Export Recruiter Debrief Report| DebugCSV[ranking_debug.csv]
```

### 1. Requirements: `hiring_rubric.py`
Defines the target qualifications for the Senior AI Engineer role (AI core skills, title weights, Pune/Noida target locations, experience Sweet spots, and IT consulting blocklists).

### 2. Ingestion: `resume_fetcher.py`
Streams candidate objects line-by-line to maintain a constant memory profile. Normalizes text strings to lowercase and classifies the candidate's historical employers (Product vs. Services).

### 3. Verification: `resume_screener.py`
Inspects each profile for obvious disqualifications (such as overseas residents requiring visa sponsorship) and logical contradictions (trap profiles or honeypots).

### 4. Evaluation: `candidate_scorer.py`
Calculates technical base scores (max 100 points) and applies weight multipliers:
- **Experience**: Curve peaked at 6–8 years.
- **Location**: Noida/Pune residents and relocatable Tier-1 candidates.
- **Employer**: Startups/Product company history favored.
- **Availability**: Exponential platform engagement decay based on days since last active date.

### 5. Interviewing: `interview_prober.py`
Writes factual, non-templated reasoning strings for each shortlist candidate (referencing years, title, skills, and notice period). Also generates 2–3 tailored interview questions targeting candidate gaps.

### 6. Orchestration: `final_selector.py` & `rank.py`
Runs the pipeline end-to-end, resolves equal score ties lexicographically by ascending candidate ID, slices the top 100 "selected employees", and writes the files.
