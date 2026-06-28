# Concept: Honeypot Detection & Evasion

Honeypots are fake candidate records injected into the 100,000 candidate dataset. They are designed to match core AI keyword searches but contain logical impossibilities that a human recruiter would instantly spot.

> [!WARNING]
> Submissions with a **honeypot rate > 10% in the top 100** are disqualified during Stage 3 evaluation.

---

## Honeypot Types & Our Evasion Filters

Our `resume_screener.py` implements four deterministic filters to identify and eliminate honeypots:

### 1. Stated Skill Duration Check
* **Anomaly**: Fake profiles listing "expert" proficiency in key AI skills but with `duration_months == 0`.
* **Filter**:
  ```python
  if skill["proficiency"] == "expert" and skill["duration_months"] == 0:
      return True  # Honeypot detected
  ```

### 2. Stated Duration vs. Calendar Span Check
* **Anomaly**: A candidate claiming they worked at a company for 96 months (8 years), but their `start_date` and `end_date` are only 2 years apart.
* **Filter**:
  We parse the job dates using Python `datetime` and compute the calendar span in months. If the candidate's reported `duration_months` in the data exceeds the actual calendar span by more than `3` months, we flag them.

### 3. Skill Inflation Check
* **Anomaly**: A resume listing 8 or more advanced or expert skills (such as RAG, Fine-Tuning, FAISS, PyTorch) but having a total `years_of_experience` less than `3`.
* **Filter**:
  We sum all expert and advanced skills. If count $\ge 8$ and total years of experience is $< 3$, they are flagged.

### 4. Educational Timeline Check
* **Anomaly**: Profiles where job start dates begin before college starts or when the candidate was a child.
* **Filter**:
  We identify the candidate's earliest university start year from `education` and compare it to their earliest job start year. If their job starts more than `2` years before college began, it's flagged as an impossible timeline.
