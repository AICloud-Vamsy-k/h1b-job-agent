# streamlit_app.py

import textwrap
from pathlib import Path
import streamlit as st

from src.crews.job_match_crew import evaluate_job
from src.crews.resume_builder_crew import generate_tailored_resume
from src.crews.gap_analyzer_crew import analyze_gaps_for_learning
from src.pipelines.daily_pipeline import run_daily_job_pipeline
from src.core.resume_source import set_current_resume, get_current_resume_config
from src.rag.profile_rag import build_or_refresh_profile_index




st.set_page_config(
    page_title="H1B Job Search Agent",
    layout="wide",
)

# Build index when resume exists at startup (best-effort; if no resume yet, it does nothing)
#cfg = get_current_resume_config()
#if cfg is not None:
#    build_or_refresh_profile_index()


st.title("H1B Job Search Agent (Local UI)")
st.write("Upload your resume, paste a job description, or run the daily pipeline over jobs_sample.csv.")


# ===================== TABS =====================
TAB_PROFILE, TAB_SINGLE, TAB_H1B, TAB_PIPELINE = st.tabs([
    "📄 Profile & Resume",
    "💼 Single Job Analysis",
    "🌐 H1B Job Finder",  # NEW TAB
    "⚙️ Daily Pipeline"
])


# ============= TAB 0: Profile / Resume =============
with TAB_PROFILE:
    st.subheader("Current Resume")

    st.write(
        textwrap.dedent(
            """
            Upload your current resume (DOCX or PDF). The app will:
            - Store it under data/uploads/
            - Remember it as the *active* resume
            - Use it as the source of skills/experience for RAG and agents
            """
        )
    )

    # Show current config if available
    cfg = get_current_resume_config()
    if cfg is not None:
        st.info(
            f"Active resume: **{cfg.path.name}** "
            f"(type: `{cfg.type}`, uploaded at: {cfg.uploaded_at.isoformat()})"
        )
    else:
        st.warning("No active resume set yet. Please upload a DOCX or PDF resume.")

    uploaded_file = st.file_uploader(
        "Upload your current resume",
        type=["pdf", "docx"],
        help="Upload the resume you want all agents to use.",
    )

    if uploaded_file is not None:
        try:
            new_cfg = set_current_resume(
                uploaded_bytes=uploaded_file.getvalue(),
                original_filename=uploaded_file.name,
            )
            # Rebuild RAG index from new resume
            #build_or_refresh_profile_index()

            st.success(
                f"Current resume updated: **{new_cfg.path.name}** "
                f"(type: `{new_cfg.type}`, uploaded at: {new_cfg.uploaded_at.isoformat()})"
            )
        except Exception as e:
            st.error(f"Failed to set current resume: {e}")


# ============= TAB 1: Single JD flow =============
with TAB_SINGLE:
    st.subheader("Single Job Analysis")

    jd_text = st.text_area(
        "Job Description",
        height=300,
        help="Paste any JD here",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        do_match = st.button("1️⃣ Evaluate Match")
    with col2:
        do_resume = st.button("2️⃣ Generate Tailored Resume")
    with col3:
        do_gap = st.button("3️⃣ Generate Gap Plan")

    if jd_text and (do_match or do_resume or do_gap):
        # Always evaluate once; reuse for other actions
        with st.spinner("Evaluating job match..."):
            match_result = evaluate_job(jd_text)

        st.markdown("### Match Result")
        st.write("**Match score:**", match_result.get("match_score"))
        st.write("**Strengths:**", match_result.get("strengths"))
        st.write("**Gaps:**", match_result.get("gaps"))
        st.write("**Summary:**", match_result.get("summary"))

        # ---- Tailored resume generation ----
        if do_resume:
            with st.spinner("Generating tailored resume..."):
                resume_result = generate_tailored_resume(jd_text, match_result)

            st.markdown("### Tailored Resume (Preview)")
            st.markdown(resume_result["markdown_text"])

            if resume_result["docx_path"] is not None:
                docx_path = resume_result["docx_path"]
                with open(docx_path, "rb") as f:
                    docx_bytes = f.read()

                st.download_button(
                    label="📥 Download Tailored Resume (DOCX)",
                    data=docx_bytes,
                    file_name=docx_path.name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                st.warning("DOCX could not be generated (no template or invalid JSON).")

        # ---- Gap analysis ----
        if do_gap:
            with st.spinner("Generating gap analysis + learning plan..."):
                gap_text = analyze_gaps_for_learning(jd_text, match_result)
            st.markdown("### Gap Analysis & Learning Plan")
            st.markdown(gap_text)


# ============ NEW TAB: H1B JOB FINDER ============
with TAB_H1B:
    st.subheader("🌐 Real-Time H1B Job Finder")
    st.write("""
    Search real job boards (LinkedIn, Indeed, etc.) and filter for H1B-eligible positions.
    - ✅ Scrapes live jobs from APIs
    - ✅ AI-powered H1B eligibility filtering
    - ✅ Excludes "GC/Citizen only" postings
    - ✅ Generates downloadable CSV report
    """)
    
    # Search parameters
    col1, col2 = st.columns(2)
    with col1:
        job_keywords = st.text_input(
            "Job Title/Keywords",
            value="Data Engineer",
            help="e.g., 'DevOps Engineer Azure', 'Software Engineer Python'"
        )
    with col2:
        job_location = st.text_input(
            "Location",
            value="United States",
            help="e.g., 'California', 'New York', 'United States'"
        )
    
    col3, col4 = st.columns(2)
    with col3:
        num_pages = st.slider("Pages to scrape", 1, 10, 3, 
                              help="Each page = ~10 jobs")
    with col4:
        use_ai_filter = st.checkbox("Use AI filtering (slower but more accurate)", value=True)
    
    # Run button
    if st.button("🔍 Find H1B Jobs", type="primary"):
        with st.spinner("Searching job boards..."):
            try:
                # Import and run H1B finder
                from src.pipelines.h1b_pipeline import run_h1b_job_finder_streamlit
                
                results = run_h1b_job_finder_streamlit(
                    keywords=job_keywords,
                    location=job_location,
                    num_pages=num_pages,
                    use_ai=use_ai_filter
                )
                
                if results and results['h1b_jobs']:
                    st.success(f"✅ Found {len(results['h1b_jobs'])} H1B-eligible jobs out of {results['total_jobs']} scraped")
                    
                    # Display results
                    import pandas as pd
                    df = pd.DataFrame(results['h1b_jobs'])
                    
                    # Show summary metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Scraped", results['total_jobs'])
                    col2.metric("H1B Eligible", len(results['h1b_jobs']))
                    col3.metric("Exclusion Rate", f"{results['exclusion_rate']:.1f}%")
                    
                    # Show table
                    st.markdown("### 📊 H1B-Eligible Jobs")
                    display_df = df[['title', 'company', 'location', 'source', 'eligibility_reason']]
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Full Report (CSV)",
                        data=csv,
                        file_name=f"h1b_jobs_{job_keywords.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                    
                    # Show individual job details (expandable)
                    st.markdown("### 📋 Job Details")
                    for idx, job in enumerate(results['h1b_jobs'][:10]):  # Show first 10
                        with st.expander(f"{job['title']} - {job['company']}"):
                            st.write(f"**Location:** {job['location']}")
                            st.write(f"**Source:** {job['source']}")
                            st.write(f"**H1B Status:** {job['eligibility_reason']}")
                            st.write(f"**Description:** {job['description'][:300]}...")
                            st.link_button("Apply Now", job['url'])
                else:
                    st.warning("No H1B-eligible jobs found. Try different keywords or location.")
                    
            except Exception as e:
                st.error(f"Error running H1B finder: {e}")
                st.code(str(e), language="text")
    
    # Show previous results if available
    st.markdown("---")
    st.markdown("### 📁 Recent Reports")
    report_path = Path("output/reports/h1b_daily_report.csv")
    if report_path.exists():
        try:
            import pandas as pd
            df = pd.read_csv(report_path)
            st.write(f"Last run: {report_path.stat().st_mtime}")
            st.dataframe(df.head(10), use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load previous report: {e}")


# ============= TAB 2: Daily pipeline over CSV =============
with TAB_PIPELINE:
    st.subheader("Daily Pipeline on jobs_sample.csv")

    st.write(
        "This runs over `data/jobs_sample.csv`, scores sponsorship + match, "
        "and writes `output/daily_report.csv`."
    )

    sponsorship_threshold = st.slider(
        "Sponsorship threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
    )
    match_threshold = st.slider(
        "Match threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.65,
        step=0.05,
    )
    generate_resumes = st.checkbox(
        "Generate tailored resumes and gap plans for candidate jobs",
        value=True,
    )

    if st.button("Run Daily Pipeline"):
        with st.spinner("Running daily pipeline..."):
            report_path = run_daily_job_pipeline(
                sponsorship_threshold=sponsorship_threshold,
                match_threshold=match_threshold,
                generate_resumes=generate_resumes,
            )

        st.success(f"Pipeline finished. Report: {report_path}")

        # Try to read and show the CSV as a table
        try:
            import pandas as pd

            df = pd.read_csv(report_path)
            st.markdown("### Daily Report")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Could not read report CSV: {e}")
