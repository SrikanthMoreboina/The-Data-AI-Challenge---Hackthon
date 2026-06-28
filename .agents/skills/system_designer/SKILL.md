---
name: system_designer
description: Establishes the scoring framework, feature coefficients, location modifiers, and availability weights.
---

# System Designer Agent Skill

You are the System Designer Agent. Your goal is to design the scoring model and mathematical filters that rate candidate suitability for the Senior AI Engineer role at Redrob AI.

## Scoring Model Design

The matching score for any candidate $C$ is computed as:

$$\text{Final Score}(C) = \text{Base Score}(C) \times M_{\text{experience}}(C) \times M_{\text{location}}(C) \times M_{\text{employer}}(C) \times M_{\text{availability}}(C) \times M_{\text{honeypot\_penalty}}(C)$$

### 1. Base Score calculation (max 100)
- **Essential Technical Skills (up to 60 points)**:
  - Embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5, etc.): +15 points.
  - Vector databases/hybrid search (Pinecone, Weaviate, Qdrant, Milvus, Elasticsearch, FAISS, etc.): +15 points.
  - Evaluation frameworks (NDCG, MRR, MAP, A/B testing): +15 points.
  - Strong Python / Software Engineering (clean code, frameworks): +15 points.
- **Preferred AI Skills (up to 20 points)**:
  - LLM Fine-tuning (LoRA, QLoRA, PEFT): +10 points.
  - Learning-to-rank models (XGBoost, neural): +10 points.
- **Role Title Matching (up to 20 points)**:
  - Current/recent title contains "AI Engineer", "Machine Learning Engineer", "ML Engineer", "Data Scientist", "Applied Scientist", or "NLP Engineer": +20 points.
  - Software Engineer / Backend Engineer: +10 points.
  - Unrelated titles (Marketing, HR, Writer): +0 points (likely a trap/keyword stuffer).

### 2. Multipliers

- **Experience Multiplier ($M_{\text{experience}}$)**:
  - 5–9 years of experience: `1.0`.
  - 6–8 years of experience (ideal sweet spot): `1.1`.
  - < 5 years of experience: `0.1 * years_of_experience` (linear scale down to 0.1).
  - > 9 years of experience: `1.0 - 0.05 * (years_of_experience - 9)` (capped at min 0.5; penalizes over-seniority/architecture focus unless they are active coders).

- **Location Multiplier ($M_{\text{location}}$)**:
  - Located in Pune or Noida (target hubs): `1.2`.
  - Located in target Tier-1 India cities (Hyderabad, Mumbai, Bangalore, Delhi NCR) AND willing to relocate: `1.0`.
  - Located in India (other cities) AND willing to relocate: `0.8`.
  - Outside India / Not willing to relocate: `0.1` (no work visa sponsorship is provided).

- **Employer Multiplier ($M_{\text{employer}}$)**:
  - Entire career at IT Services companies (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini, Tech Mahindra, Mindtree, HCL, LTI, etc.): `0.1` (direct disqualification criteria).
  - Mix of IT Services and Product/Startup experience: `0.8`.
  - Product-only or Startup-only experience: `1.1`.

- **Availability & Engagement Multiplier ($M_{\text{availability}}$)**:
  - Computed using `recruiter_response_rate` ($R$) and `last_active_date` ($A$, represented as days since last active $D$):
    $$M_{\text{availability}} = R_{\text{factor}} \times A_{\text{factor}}$$
  - $R_{\text{factor}} = 0.5 + 0.5 \times R$ (response rate of 5% results in $\approx 0.52$; response rate of 90% results in $\approx 0.95$).
  - $A_{\text{factor}} = \exp(-D / 180)$ (decay factor; if inactive for 6 months/180 days, $A_{\text{factor}} \approx 0.36$).

- **Honeypot Penalty ($M_{\text{honeypot\_penalty}}$)**:
  - Detected honeypot: `0.0` (eliminates them from top-100 completely).
