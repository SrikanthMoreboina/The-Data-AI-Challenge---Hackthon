# Concept: Non-Linear Recruiter Multipliers

To mimic a real-world recruiter, our candidate scorer does not rely on simple keyword addition. It uses a combination of base points and non-linear weight multipliers.

$$\text{Final Score} = \text{Base Score} \times M_{\text{experience}} \times M_{\text{location}} \times M_{\text{employer}} \times M_{\text{availability}}$$

---

## 1. Experience Sweet Spot Curve ($M_{\text{experience}}$)
The Job Description targets candidates with **5–9 years** of experience. A simple search engine might filter out a candidate with 4.9 years or 9.5 years. Instead, we use a curve:
- **6.0 to 8.0 years (Sweet Spot)**: Boosted with a `1.1` multiplier.
- **5.0 to 9.0 years**: Kept neutral at `1.0`.
- **Under 5.0 years (Junior)**: Scaled down linearly using `0.1 * years_of_experience` (with a minimum floor of `0.1`).
- **Over 9.0 years (Senior)**: Scaled down gradually: `1.0 - 0.05 * (years - 9.0)` (minimum floor of `0.5` to prevent complete disqualification of highly skilled seniors).

---

## 2. Inactivity Exponential Decay ($M_{\text{availability}}$)
A perfect candidate who hasn't logged into the platform for a long time is likely unavailable. We decay their score based on their `last_active_date` using a half-life curve:

$$A_{\text{factor}} = e^{-\text{Days} / 180}$$

* **Active today (0 days)**: $e^0 = 1.0$ (no penalty).
* **Active 6 months ago (180 days)**: $e^{-1} \approx 0.368$ (significant penalty).
* **Active 1 year ago (365 days)**: $e^{-2} \approx 0.135$ (near-complete down-weight).

We also scale this by the candidate's `recruiter_response_rate` ($R$):

$$R_{\text{factor}} = 0.5 + 0.5 \times R$$

If a candidate has a response rate of 100%, they get a full `1.0` multiplier. If they never respond, they get scaled down to `0.5`.

---

## 3. Location Modifier ($M_{\text{location}}$)
We match their current city and relocation interest:
* **Pune / Noida Resident**: Boosted to `1.2`.
* **Indian Tier-1 Resident (Willing to relocate)**: Neutral at `1.0`.
* **Other Indian Resident (Willing to relocate)**: Set to `0.8`.
* **Indian Resident (Unwilling to relocate)**: Penalized with `0.1`.
* **Overseas Resident**: Penalized with `0.1` (since we do not sponsor work visas).

---

## 4. Employer Background Modifier ($M_{\text{employer}}$)
* **Product Only**: Multiplier is `1.1`.
* **Hybrid (mix of services and product)**: Multiplier is `0.8`.
* **Services Only (TCS, Infosys, Wipro, etc.)**: Penalized with `0.1`.

---

## 5. Non-Tech Job Title & Learning Context Blocker
To prevent simple keyword-stuffer profiles (like a graphic designer who adds "TensorFlow" once to their description) from ranking highly, we perform context auditing:
1. **Title Blocklist**: If a career history job title matches a non-technical field (e.g. `marketing`, `sales`, `writer`, `hr specialist`, `designer`), we ignore all keyword matches in that job's details.
2. **Learning Context Blocker**: If a matched technical keyword is surrounded by learning indicators (such as `tutorial`, `bootcamp`, `udemy`, `coursera`, `class project`, `toy project`), the match is marked as academic/classroom-only and no technical base points are awarded.

