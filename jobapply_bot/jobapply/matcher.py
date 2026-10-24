def score_job(job, roles, min_stipend, arrangements, preferred_location):
    text = " ".join([job.get("title",""), job.get("company",""), job.get("location",""), job.get("snippet","")]).lower()
    role_terms = {
        "Data Analyst": ["data analyst", "analytics", "sql", "python", "excel"],
        "Power BI": ["power bi", "dax", "power query", "dashboard", "bi developer"],
        "Business Intelligence": ["business intelligence", "bi analyst", "dashboard", "kpi"],
        "SQL Developer": ["sql", "database", "mysql"],
        "Python Developer": ["python", "django", "flask", "api"],
        "Django Developer": ["django", "python", "backend"],
        "AI/ML Intern": ["machine learning", "ai intern", "llm", "qlora", "transformers"],
        "Data Science": ["data science", "pandas", "numpy", "machine learning"],
    }
    terms = sorted({term for role in roles for term in role_terms.get(role, [])})
    hits = [term for term in terms if term in text]
    score = min(55, 10 + len(hits) * 6) if hits else 5
    reasons = ["Matched terms: " + ", ".join(hits[:6])] if hits else ["Role match uncertain; inspect listing"]
    loc = job.get("location","").lower()
    if any(a.lower() in loc for a in arrangements):
        score += 15
        reasons.append("Work arrangement may fit")
    if "remote" in loc or "work from home" in text:
        score += 10
        reasons.append("Remote-friendly wording")
    if preferred_location and preferred_location.lower() in loc:
        score += 10
        reasons.append("Location matches preference")
    salary = (job.get("salary") or "").lower()
    if salary and any(ch.isdigit() for ch in salary):
        score += 5
        reasons.append("Compensation information present")
    else:
        reasons.append("Stipend not confirmed")
    if "intern" in text or "trainee" in text:
        score += 5
        reasons.append("Internship/trainee wording")
    return min(score, 100), reasons
