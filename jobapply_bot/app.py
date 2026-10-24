import streamlit as st
from jobapply.search import search_all_sources, dedupe_jobs
from jobapply.db import init_db, save_search_results, list_saved_jobs, update_status
from jobapply.matcher import score_job

st.set_page_config(page_title="JobApply Bot", page_icon="🤖", layout="wide")
init_db()

st.title("🤖 JobApply Bot — Auto Search")
st.write("Automatically searches connected job sources, ranks roles against your preferences, and tracks applications. You do not need to add jobs manually.")

with st.sidebar:
    st.header("Your search profile")
    roles = st.multiselect(
        "Target roles",
        ["Data Analyst", "Power BI", "Business Intelligence", "SQL Developer",
         "Python Developer", "Django Developer", "AI/ML Intern", "Data Science"],
        default=["Data Analyst", "Power BI", "Business Intelligence", "Python Developer", "AI/ML Intern"]
    )
    location = st.selectbox("Location", ["Remote", "Lucknow", "Remote + Lucknow", "India (remote or hybrid)"], index=2)
    min_stipend = st.number_input("Minimum monthly stipend (₹)", min_value=0, value=8000, step=1000)
    arrangement = st.multiselect("Acceptable arrangements", ["Remote", "Hybrid", "On-site"], default=["Remote", "Hybrid"])
    experience = st.selectbox("Experience level", ["Internship", "Internship + entry-level"], index=0)
    st.caption("API keys are configured in the .env file. Never paste passwords, OTPs, or bank details here.")

st.subheader("Automatic job discovery")
st.caption("Searches every configured source in one click, merges duplicate results, and ranks them. Sources depend on available API credentials and their coverage.")

if st.button("🔎 Search jobs across connected sources", type="primary", use_container_width=True):
    with st.spinner("Searching connected job sources…"):
        results, source_status = search_all_sources(roles=roles, location=location, experience=experience)
        results = dedupe_jobs(results)
        for job in results:
            job["score"], job["reasons"] = score_job(job, roles, min_stipend, arrangement, location)
        results.sort(key=lambda j: (j["score"], j.get("date", "")), reverse=True)
        save_search_results(results)
        st.session_state["results"] = results
        st.session_state["source_status"] = source_status

if "source_status" in st.session_state:
    st.write("**Source status**")
    cols = st.columns(max(1, len(st.session_state["source_status"])))
    for col, (source, message) in zip(cols, st.session_state["source_status"].items()):
        with col:
            st.metric(source, message)

results = st.session_state.get("results", [])
if results:
    st.success(f"Found {len(results)} unique listings from connected sources.")
    min_score = st.slider("Minimum match score", 0, 100, 25, 5)
    shown = [j for j in results if j.get("score", 0) >= min_score]
    st.caption(f"Showing {len(shown)} matching results.")
    for idx, job in enumerate(shown):
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"### {job.get('title') or 'Untitled role'}")
                st.write(f"**{job.get('company') or 'Company not listed'}** · {job.get('location') or 'Location not stated'}")
                if job.get("url"):
                    st.markdown(f"[Open original listing / apply]({job['url']})")
                st.caption(f"Source: {job.get('source','Unknown')} · Stipend/salary: {job.get('salary') or 'Not stated'} · Posted: {job.get('date') or 'Not stated'}")
                st.write("**Match reasons:** " + ("; ".join(job.get("reasons", [])) or "Limited listing details"))
                if job.get("snippet"):
                    st.write(job["snippet"][:650])
            with c2:
                st.metric("Match", f"{job.get('score', 0)}/100")
                if st.button("Save to tracker", key=f"save_{idx}"):
                    save_search_results([job], status="Review")
                    st.toast("Saved to tracker")
else:
    st.info("Click **Search jobs across connected sources** to discover listings. For full coverage, configure at least one search provider API key in `.env`.")

st.divider()
st.subheader("Application tracker")
saved = list_saved_jobs()
if not saved:
    st.caption("Saved jobs will appear here automatically when you choose Save to tracker.")
else:
    for item in saved:
        jid, title, company, url, source, status, saved_at = item
        with st.container(border=True):
            a, b, c = st.columns([5, 2, 2])
            with a:
                st.markdown(f"**{title}** — {company}")
                if url:
                    st.markdown(f"[Open listing]({url})")
                st.caption(f"{source} · Saved {saved_at}")
            with b:
                statuses = ["Review", "Ready to apply", "Applied", "Interview", "Rejected", "Offer"]
                selected = st.selectbox("Status", statuses, index=statuses.index(status) if status in statuses else 0, key=f"status_{jid}")
            with c:
                if st.button("Update status", key=f"update_{jid}"):
                    update_status(jid, selected)
                    st.rerun()

st.divider()
st.subheader("Application automation")
st.write("The current version discovers and ranks jobs automatically. Browser-assisted form filling is a separate next step: it should stop for your review before submitting, respect each portal's rules, and never bypass CAPTCHA or login protections.")
