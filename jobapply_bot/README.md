# JobApply Bot — MVP

A local Streamlit app for tracking internship listings and scoring them against a job-search profile.

## What it does
- Save jobs with title, company, URL, location, stipend, description, and status.
- Assign a transparent keyword-based fit score using your target roles and preferences.
- Track jobs from Found to Applied, Interview, Rejected, or Offer.
- Optionally extract text from a local resume PDF.

## What it does not do yet
- It does not log into job sites or submit applications automatically.
- It does not bypass CAPTCHAs, access controls, or application limits.
- It does not invent experience, education, salary, or eligibility answers.

## Setup (Windows / PowerShell)
```powershell
cd jobapply_bot
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```
The app opens in your browser. Data is stored locally in `jobapply.sqlite3`.

## Next milestones
1. Add job discovery from approved APIs / user-provided links.
2. Create resume variants for analytics, Python/Django, and AI/ML roles.
3. Generate editable cover letters and application answers for review.
4. Add Playwright-assisted form filling for sites where automation is permitted; pause before final submission for user review.
5. Add duplicate detection and application logs.
