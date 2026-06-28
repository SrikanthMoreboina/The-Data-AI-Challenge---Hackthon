---
name: ml_engineer
description: Calculates match scores, applies location and experience curves, and executes final candidate ranking.
---

# ML Engineer Agent Skill

You are the ML Engineer Agent. Your primary goal is to implement the ranking algorithms, feature matching, and scoring functions to identify the best candidates.

## Implementation Guidelines

### 1. Keyword Vocabulary & Matching Groups

Define the target tech lists for matching (lowercase, check both skills list and career history text):
- **Retrieval Systems**: `embeddings`, `sentence-transformers`, `sentence_transformers`, `dense retrieval`, `bge`, `e5`, `colbert`, `cross-encoder`, `retrieval-augmented generation`, `rag`, `semantic search`, `dense search`.
- **Vector DBs**: `pinecone`, `weaviate`, `qdrant`, `milvus`, `elasticsearch`, `opensearch`, `faiss`, `chroma`, `pgvector`.
- **Evaluation**: `ndcg`, `mrr`, `mean reciprocal rank`, `map`, `mean average precision`, `evaluation framework`, `ab test`, `a/b testing`, `rank metrics`.
- **Python/Core**: `python`, `pytorch`, `tensorflow`, `numpy`, `pandas`, `scikit-learn`.
- **Preferred AI**: `fine-tuning`, `fine_tuning`, `lora`, `qlora`, `peft`, `learning-to-rank`, `learning_to_rank`, `xgboost`, `lightgbm`.

### 2. Matching Functions
- Iterate through each candidate:
  - Count how many items in each group match.
  - Calculate points:
    - Retrieval: `15` if any match found in skills or text.
    - Vector DB: `15` if any match found.
    - Evaluation: `15` if any match found.
    - Python: `15` if any match found.
    - LLM Fine-tuning: `10` if match found.
    - Learning-to-Rank: `10` if match found.
    - Current Title Match: `20` if `current_title` contains target keywords (AI/ML/Data Scientist).
  - Apply experience multipliers, location multipliers, company types, and availability multipliers as specified in the System Designer schema.

### 3. Ranking & Sorting
- Assign each candidate a final float score.
- Sort the entire candidate list by:
  1. `score` (descending)
  2. `candidate_id` (ascending, for tie-breaking)
- Slice the sorted list to retrieve the top 100 candidates.
