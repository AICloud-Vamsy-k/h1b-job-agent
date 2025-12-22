# streamlit_app.py

import textwrap
from pathlib import Path

import streamlit as st

from src.job_match_crew import evaluate_job
from src.resume_builder_crew import generate_tailored_resume
from src.gap_analyzer_crew import analyze_gaps_for_learning
from src.pipeline import run_daily_job_pipeline


st.set_page_config(
    page_title="H1B Job Search Agent",
    layout="wide",
)


st.title("H1B Job Search Agent (Local UI)")
st.write("Paste a job description or run the daily pipeline over jobs_sample.csv.")


TAB_SINGLE, TAB_PIPELINE = st.tabs(["Single Job (Chat-style)", "Daily Pipeline"])


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

        if do_resume:
            with st.spinner("Generating tailored resume..."):
                resume_text = generate_tailored_resume(jd_text, match_result)
            st.markdown("### Tailored Resume")
            st.code(resume_text, language="markdown")

        if do_gap:
            with st.spinner("Generating gap analysis + learning plan..."):
                gap_text = analyze_gaps_for_learning(jd_text, match_result)
            st.markdown("### Gap Analysis & Learning Plan")
            st.markdown(gap_text)


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
