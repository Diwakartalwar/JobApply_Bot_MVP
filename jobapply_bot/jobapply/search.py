import os, re, requests
from urllib.parse import urlencode, quote_plus
from dotenv import load_dotenv

load_dotenv()
TIMEOUT = 18

ROLE_QUERIES = {
    "Data Analyst": ["data analyst intern", "data analytics internship"],
    "Power BI": ["Power BI intern", "Power BI developer intern"],
    "Business Intelligence": ["business intelligence intern", "BI analyst intern"],
    "SQL Developer": ["SQL developer intern", "SQL analyst intern"],
    "Python Developer": ["Python developer intern", "Python internship"],
    "Django Developer": ["Django developer intern", "backend developer Python intern"],
    "AI/ML Intern": ["machine learning intern", "AI intern LLM fine tuning"],
    "Data Science": ["data science intern", "data science internship"],
}

def queries_for(roles):
    q = []
    for role in roles:
        q.extend(ROLE_QUERIES.get(role, [role + " internship"]))
    return list(dict.fromkeys(q))[:8]

def _job(title="", company="", url="", location="", salary="", date="", snippet="", source=""):
    return {"title": title or "", "company": company or "", "url": url or "", "location": location or "",
            "salary": salary or "", "date": date or "", "snippet": snippet or "", "source": source or ""}

def search_jooble(queries, location):
    key = os.getenv("JOOBLE_API_KEY", "").strip()
    if not key:
        return [], "No API key configured"
    results = []
    # Jooble API expects a country-specific API key; query a few high-priority terms.
    loc = "Lucknow" if "Lucknow" in location else "India"
    for q in queries[:5]:
        try:
            r = requests.post(f"https://jooble.org/api/{key}", json={"keywords": q, "location": loc, "page": 1, "ResultOnPage": 20}, timeout=TIMEOUT)
            if r.ok:
                data = r.json()
                for x in data.get("jobs", []):
                    results.append(_job(x.get("title"), x.get("company"), x.get("link"), x.get("location"),
                                        x.get("salary"), x.get("updated"), x.get("snippet"), "Jooble"))
            else:
                return results, f"HTTP {r.status_code}"
        except Exception as e:
            return results, f"Error: {type(e).__name__}"
    return results, f"{len(results)} results"

def search_adzuna(queries, location):
    app_id, app_key = os.getenv("ADZUNA_APP_ID", "").strip(), os.getenv("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        return [], "No API keys configured"
    results = []
    where = "Lucknow" if "Lucknow" in location else "India"
    # Adzuna API availability and supported country codes depend on account/API coverage.
    country = os.getenv("ADZUNA_COUNTRY_CODE", "in").strip().lower()
    for q in queries[:5]:
        try:
            params = {"app_id": app_id, "app_key": app_key, "results_per_page": 20, "what": q, "where": where, "content-type": "application/json"}
            r = requests.get(f"https://api.adzuna.com/v1/api/jobs/{country}/search/1", params=params, timeout=TIMEOUT)
            if r.ok:
                for x in r.json().get("results", []):
                    loc = (x.get("location") or {}).get("display_name", "")
                    salary = ""
                    if x.get("salary_min") or x.get("salary_max"):
                        salary = f"{x.get('salary_min','?')}–{x.get('salary_max','?')} (API currency)"
                    results.append(_job(x.get("title"), (x.get("company") or {}).get("display_name"), x.get("redirect_url"),
                                        loc, salary, x.get("created"), x.get("description"), "Adzuna"))
            else:
                return results, f"HTTP {r.status_code} (check country/API access)"
        except Exception as e:
            return results, f"Error: {type(e).__name__}"
    return results, f"{len(results)} results"

def search_serpapi(queries, location):
    key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not key:
        return [], "No API key configured"
    results = []
    loc = "Lucknow, Uttar Pradesh, India" if "Lucknow" in location else "India"
    # Google Jobs aggregator results through SerpAPI.
    for q in queries[:6]:
        try:
            params = {"engine": "google_jobs", "q": q + " internship", "location": loc, "hl": "en", "api_key": key}
            r = requests.get("https://serpapi.com/search.json", params=params, timeout=TIMEOUT)
            if r.ok:
                data = r.json()
                for x in data.get("jobs_results", []):
                    company = x.get("company_name", "")
                    loc2 = x.get("location", "")
                    extensions = " · ".join(x.get("detected_extensions", {}).values()) if isinstance(x.get("detected_extensions"), dict) else ""
                    links = x.get("apply_options") or []
                    url = links[0].get("link", "") if links else ""
                    desc = x.get("description", "")
                    results.append(_job(x.get("title"), company, url, loc2, extensions, x.get("detected_extensions", {}).get("posted_at", ""), desc, "Google Jobs (SerpAPI)"))
            else:
                return results, f"HTTP {r.status_code}"
        except Exception as e:
            return results, f"Error: {type(e).__name__}"
    return results, f"{len(results)} results"

def search_public_portal_links(queries, location):
    # Always include direct search links for major portals; these are not scraped and don't require credentials.
    # This ensures the user has one-click searches even when no API provider is configured.
    links = []
    site_map = [
        ("LinkedIn", "linkedin.com/jobs/search/"),
        ("Indeed", "in.indeed.com/jobs"),
        ("Internshala", "internshala.com/internships/"),
        ("Naukri", "naukri.com"),
        ("Foundit", "foundit.in"),
    ]
    loc = "Lucknow" if "Lucknow" in location else "India"
    for q in queries[:4]:
        for source, base in site_map:
            if source == "LinkedIn":
                url = "https://www.linkedin.com/jobs/search/?" + urlencode({"keywords": q, "location": loc})
            elif source == "Indeed":
                url = "https://in.indeed.com/jobs?" + urlencode({"q": q, "l": loc})
            elif source == "Internshala":
                url = "https://internshala.com/internships/" + quote_plus(q.replace(" ", "-")) + "-internship/"
            elif source == "Naukri":
                url = "https://www.naukri.com/" + "-".join(q.lower().split()) + "-jobs-in-" + "-".join(loc.lower().split())
            else:
                url = "https://www.foundit.in/srp/results?" + urlencode({"query": q, "locations": loc})
            links.append(_job(q, source, url, loc, "", "", "Open this portal's live search results. These are search links, not scraped job records.", f"{source} search link"))
    return links

def search_all_sources(roles, location, experience="Internship"):
    queries = queries_for(roles)
    all_jobs, status = [], {}
    for name, func in [("Jooble", search_jooble), ("Adzuna", search_adzuna), ("Google Jobs", search_serpapi)]:
        jobs, message = func(queries, location)
        all_jobs.extend(jobs)
        status[name] = message
    # Include search shortcuts so the dashboard remains useful without API credentials.
    shortcuts = search_public_portal_links(queries, location)
    all_jobs.extend(shortcuts)
    status["Portal shortcuts"] = f"{len(shortcuts)} links"
    return all_jobs, status

def dedupe_jobs(jobs):
    seen, out = set(), []
    for j in jobs:
        key = (re.sub(r"\W+", "", (j.get("title") or "").lower()),
               re.sub(r"\W+", "", (j.get("company") or "").lower()))
        if not key[0]:
            key = (j.get("url", ""), j.get("source", ""))
        if key not in seen:
            seen.add(key)
            out.append(j)
    return out
