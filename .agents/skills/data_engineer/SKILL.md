---
name: data_engineer
description: Manages streaming candidate ingestion, text preprocessing, feature cleaning, and company type classification.
---

# Data Engineer Agent Skill

You are the Data Engineer Agent. Your primary goal is to build an efficient, low-memory pipeline to parse and preprocess candidate profiles.

## Pipeline Requirements

### 1. Low-Memory Streaming Ingestion
- Do **NOT** load the entire `candidates.jsonl` (465MB uncompressed) into memory at once.
- Use Python generators to read and process candidates line-by-line:
  ```python
  import json
  def stream_candidates(file_path):
      with open(file_path, "r", encoding="utf-8") as f:
          for line in f:
              if line.strip():
                  yield json.loads(line)
  ```
- This ensures memory usage stays under 500 MB (well below the 16 GB constraint).

### 2. Company Classification (IT Services vs. Product)
- Define a list of known service-oriented IT consulting firms:
  `TCS, Tata Consultancy Services, Infosys, Wipro, Accenture, Cognizant, Capgemini, Tech Mahindra, Mindtree, HCL, L&T, Larsen & Toubro, LTI, DXC Technology, Genpact, WNS, Mphasis`.
- Inspect candidate's `career_history`:
  - Flag if the candidate has only worked at these companies.
  - Compute a boolean flag `has_product_experience` which is True if any company in `career_history` is outside this service-firm list and has duration > 6 months.

### 3. Skill & Text Preprocessing
- Lowercase and normalize text in `headline`, `summary`, and `career_history[i]['description']`.
- Extract list of skills: both listed in the `skills` array and mentioned in the summaries/headlines.

### 4. CSV Exporter
- Export columns: `candidate_id`, `rank`, `score`, `reasoning`.
- Ensure column order is exact.
- Output file must use UTF-8 encoding.
