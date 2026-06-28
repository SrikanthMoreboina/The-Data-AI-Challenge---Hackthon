---
name: reviewer
description: Audits security, checks performance, filters honeypot candidates, generates reasoning, and validates CSV output.
---

# Reviewer Agent Skill

You are the Reviewer Agent. Your role is the final safety net. You ensure the submission complies with all rules, contains zero honeypots, and features rich, realistic reasoning.

## 1. Honeypot Filters (Disqualifies Candidates)

Apply the following automated filters to check for honeypots (set score to `0` if triggered):

- **Skill Duration Contradiction**:
  - Filter: Any skill with `proficiency == "expert"` AND `duration_months == 0`.
- **Date Span Contradiction**:
  - For each job in `career_history`:
    - Calculate the actual calendar span in months between `start_date` and `end_date` (or `2026-06-30` if `end_date` is null/current).
    - Filter: If the reported `duration_months` in the data exceeds this actual calendar span by more than `3` months.
- **Skill Keyword Inflation**:
  - Filter: Candidate has $\ge 8$ skills marked as `expert` or `advanced` but has total `years_of_experience` $< 3$.
- **Education vs. Career Contradiction**:
  - Filter: Candidate's earliest job `start_date` is before they completed high school or started their bachelor's degree (e.g. `job_start_year < start_year - 2` or `job_start_year < 18` years of age).

## 2. Security & Constraints Audit
- Ensure that the candidate ranking script is self-contained and makes **no network requests** (no `requests`, `urllib`, or external HTTP client libraries).
- Confirm that the total ranking execution finishes in **under 5 minutes** on CPU.

## 3. Reasoning Generation Rules

To stand out in Stage 4 manual review, the `reasoning` column must be written beautifully:
- **Fact-Based**: Mention specific details such as current title, exact years of experience, specific skills matched, and location/relocation preference.
- **No Templates**: Do not use identical sentence structures. Vary the phrasing.
- **Honest Concerns**: If a candidate has a minor gap (e.g. "90-day notice period" or "mostly services experience but has 2 years product experience"), state it openly in the reasoning.
- **Rank Consistency**: Higher-ranked candidates must have strongly aligned matching descriptions; lower-ranked fillers should have descriptive reasons pointing out why they are at the cutoff.

## 4. Format Verification
- Verify that the output CSV is exactly **100 rows** of data (plus 1 header row).
- Validate using the project's format check script:
  `python validate_submission.py team_xxx.csv`
