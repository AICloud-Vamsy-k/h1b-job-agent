# streamlit_app.py

import textwrap
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from src.crews.job_match_crew import evaluate_job
from src.crews.resume_builder_crew import generate_tailored_resume
from src.crews.gap_analyzer_crew import analyze_gaps_for_learning
from src.pipelines.h1b_pipeline import run_h1b_job_finder_streamlit
from src.rag.profile_rag import (
    build_or_refresh_profile_index,
    retrieve_relevant_chunks,
)

st.set_page_config(
    page_title="H1B Job Search Agent",
    layout="wide",
)

# Cancel flag for long runs
if "cancel_run" not in st.session_state:
    st.session_state.cancel_run = False

# ===================== GLOBAL RAG STATUS =====================
rag_status_col1, rag_status_col2 = st.columns([3, 1])
with rag_status_col1:
    st.markdown("### 📄 Resume & RAG Status")
with rag_status_col2:
    if st.button("🔄 Refresh RAG Index", use_container_width=True):
        with st.spinner("Rebuilding RAG index from latest resume..."):
            try:
                build_or_refresh_profile_index()
                st.success("✅ RAG index refreshed!")
            except Exception as e:
                st.error(f"❌ RAG refresh failed: {e}")

# Check RAG status
try:
    test_chunks = retrieve_relevant_chunks("software engineer", top_k=1)
    if test_chunks:
        total_chunks = len(retrieve_relevant_chunks("test", top_k=1000))
        st.success(
            f"✅ **RAG READY** - {total_chunks} chunks from your full resume indexed"
        )
    else:
        st.warning("⚠️ **No resume indexed**. Upload DOCX in Profile tab first.")
except Exception:
    st.warning("⚠️ RAG setup incomplete. Upload resume first.")

st.title("H1B Job Search Agent (Local UI)")
st.write(
    "Upload your resume, paste a job description, or run the daily pipeline over jobs_sample.csv."
)

# ===================== TABS =====================
TAB_PROFILE, TAB_SINGLE, TAB_H1B, TAB_PIPELINE = st.tabs(
    [
        "📄 Profile & Resume",
        "💼 Single Job Analysis",
        "🌐 H1B Job Finder",
        "⚙️ Daily Pipeline",
    ]
)

# ============= TAB 0: Profile / Resume =============
with TAB_PROFILE:
    st.subheader("Current Resume")

    st.write(
        textwrap.dedent(
            """
            Upload your current resume (**DOCX recommended**). The app will:
            - Store it under `data/uploads/`
            - **Automatically chunk & index** your **FULL resume** in ChromaDB (RAG)
            - Use it as the source of skills/experience for **ALL agents**
            """
        )
    )

    st.markdown("### 🔍 Current RAG Index Status")
    try:
        collection_count = len(retrieve_relevant_chunks("test", top_k=1000))
        st.success(f"✅ **{collection_count} chunks** indexed from your latest resume")
        if collection_count > 0:
            st.info(
                "💡 RAG is pulling from your **full resume** - projects, experience, skills, everything!"
            )
    except Exception:
        st.warning("⚠️ No resume indexed yet")

    uploaded_file = st.file_uploader(
        "Upload your current resume",
        type=["docx"],
        help="**DOCX recommended** - best for RAG chunking + resume templating",
    )

    if uploaded_file is not None:
        try:
            uploads_dir = Path("data") / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resume_{timestamp}_{Path(uploaded_file.name).stem}.docx"
            resume_path = uploads_dir / filename

            with open(resume_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            st.success(f"✅ Resume saved: **{resume_path.name}**")

            with st.spinner("🔄 Indexing FULL resume for RAG..."):
                build_or_refresh_profile_index()

            test_chunks = retrieve_relevant_chunks(
                "software engineer python data", top_k=3
            )
            st.success(
                f"✅ **RAG ACTIVE** - Found {len(test_chunks)} relevant sections:"
            )

            with st.expander("Preview your indexed resume chunks"):
                for i, chunk in enumerate(test_chunks):
                    st.markdown(f"**{i+1}.** {chunk[:300]}...")

            if st.button("📊 Show FULL RAG Stats"):
                try:
                    all_chunks = retrieve_relevant_chunks("", top_k=1000)
                    st.success(
                        f"✅ **FULL INDEX**: {len(all_chunks)} chunks from your ENTIRE resume"
                    )

                    st.markdown("### Coverage Test:")
                    sections = [
                        "python",
                        "aws",
                        "sql",
                        "projects",
                        "experience",
                        "education",
                    ]
                    for section in sections:
                        chunks = retrieve_relevant_chunks(section, top_k=1)
                        status = "✅" if chunks else "❌"
                        st.write(
                            f"{status} **{section.upper()}**: "
                            f"{chunks[0][:100] if chunks else 'Nothing found'}..."
                        )
                except Exception as e:
                    st.error(f"Stats error: {e}")

        except Exception as e:
            st.error(f"❌ Failed to process resume: {e}")
            st.exception(e)

# ============ TAB 1: Single Job Analysis ============
with TAB_SINGLE:
    st.subheader("💼 Single Job Analysis")

    col1, col2 = st.columns([3, 1])
    with col1:
        job_desc = st.text_area(
            "Paste Job Description",
            height=250,
            placeholder=(
                "Paste the full job description here "
                "(requirements, responsibilities, etc.)"
            ),
        )
    with col2:
        match_threshold = st.slider("Match threshold", 0.0, 1.0, 0.6, 0.05)
        generate_resume = st.checkbox("Generate tailored resume", value=False)
        generate_gaps = st.checkbox("Generate gap analysis", value=False)

    if st.button("🔍 Analyze Job", type="primary") and job_desc.strip():
        with st.spinner("🤖 Running RAG-enhanced analysis..."):
            match_result = evaluate_job(job_desc)

            st.markdown("### 📊 Match Results")
            col1, col2 = st.columns(2)
            col1.metric(
                "Match Score", f"{match_result.get('match_score', 0):.1%}"
            )
            col2.metric(
                "Status",
                "✅ Good Match"
                if match_result.get("match_score", 0) >= match_threshold
                else "❌ Below Threshold",
            )

            st.markdown("**Strengths:**")
            st.json(match_result.get("strengths", []))

            st.markdown("**Gaps:**")
            st.warning(match_result.get("gaps", []))

            st.markdown("**Summary:**")
            st.info(match_result.get("summary", ""))

            if generate_resume:
                st.markdown("### 📄 Tailored Resume")
                with st.spinner("Generating tailored resume..."):
                    resume_result = generate_tailored_resume(job_desc, match_result)

                    st.markdown("**Preview:**")
                    st.markdown(resume_result["markdown_text"])

                    if resume_result.get("docx_path"):
                        with open(resume_result["docx_path"], "rb") as f:
                            st.download_button(
                                "📥 Download Tailored Resume (DOCX)",
                                f.read(),
                                f"tailored_resume_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            )

            if generate_gaps:
                st.markdown("### 🎯 Gap Analysis & Learning Plan")
                with st.spinner("Creating personalized learning plan..."):
                    gap_report = analyze_gaps_for_learning(job_desc, match_result)
                    st.markdown(gap_report)

# ============ TAB 2: H1B JOB FINDER ============
with TAB_H1B:
    st.subheader("🌐 Real-Time H1B Job Finder")
    st.write(
        """
        Search real job boards (LinkedIn, Indeed, etc.) and filter for H1B-eligible positions.
        - ✅ Scrapes live jobs from APIs
        - ✅ AI-powered H1B eligibility filtering
        - ✅ **RAG-powered resume matching**
        - ✅ Generates tailored resumes for top matches
        - ✅ Downloadable CSV reports
        """
    )

    # Search parameters
    col1, col2 = st.columns(2)
    with col1:
        job_keywords = st.text_input(
            "Job Title/Keywords",
            value="Data Engineer, Cloud Engineer, Software Engineer, Cloud Architect, Data Architect",
            help="e.g., 'DevOps Engineer Azure', 'Software Engineer Python'",
        )
    with col2:
        job_location = st.text_input(
            "Location",
            value="United States",
            help="e.g., 'California', 'New York', 'United States'",
        )

    col3, col4 = st.columns(2)
    with col3:
        num_pages = st.slider(
            "Pages to scrape",
            1,
            10,
            3,
            help="Each page = ~10 jobs",
        )
        match_threshold = st.slider(
            "Resume match threshold",
            0.0,
            1.0,
            0.65,
        )
    with col4:
        use_ai_filter = st.checkbox(
            "Use AI filtering (slower but more accurate)",
            value=True,
        )
        generate_resumes = st.checkbox(
            "Generate tailored resumes",
            value=False,
        )

    # Posted date filter (default = Last 24 hours)
    date_filter = st.selectbox(
        "Posted date",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "Any time"],
        index=0,
        help="Filter jobs based on when they were posted",
    )

    # Source filters
    st.markdown("### Sources to use")
    src_col1, src_col2, src_col3 = st.columns(3)
    with src_col1:
        use_jsearch = st.checkbox("JSearch", value=True)
    with src_col2:
        use_adzuna = st.checkbox("Adzuna", value=True)
    with src_col3:
        use_indeed = st.checkbox("Indeed", value=True)

    # Email settings
    st.markdown("### 📧 Email Report Settings")
    col5, col6 = st.columns(2)
    with col5:
        recipient_email = st.text_input(
            "Recipient Email",
            value="",
            placeholder="your-email@example.com",
            help="Email address to receive the job report",
        )
    with col6:
        send_email_enabled = st.checkbox("Send email report", value=True)

    # Debug panel
    with st.expander("🔧 Email Debug Panel (expand to check config)"):
        st.write("**Current Settings:**")
        st.write(f"- Send email enabled: `{send_email_enabled}`")
        st.write(
            f"- Recipient email: `{recipient_email if recipient_email else 'NOT SET'}`"
        )
        st.write(
            f"- Will send email: `{send_email_enabled and bool(recipient_email)}`"
        )

        st.markdown("---")
        st.write("**Email Configuration Check:**")
        try:
            from config.settings import (
                SMTP_HOST,
                SMTP_PORT,
                EMAIL_USER,
                EMAIL_PASSWORD,
            )

            st.success("✅ Email config imported successfully")
            st.code(
                f"""
SMTP_HOST: {SMTP_HOST}
SMTP_PORT: {SMTP_PORT}
EMAIL_USER: {EMAIL_USER}
EMAIL_PASSWORD: {'***' + EMAIL_PASSWORD[-4:] if EMAIL_PASSWORD else 'NOT SET'}
                """,
                language="text",
            )
        except Exception as config_error:
            st.error(f"❌ Config import failed: {config_error}")
            import traceback

            st.code(traceback.format_exc())

    # Run / Cancel buttons
    run_col, cancel_col = st.columns([3, 1])
    with run_col:
        run_clicked = st.button("🔍 Find H1B Jobs", type="primary")
    with cancel_col:
        if st.button("⛔ Cancel current run"):
            st.session_state.cancel_run = True
            st.info("Current run will stop after the current job finishes.")

    if run_clicked:
        # Reset cancel flag at start of a new run
        st.session_state.cancel_run = False
        with st.spinner("Searching job boards + matching your resume..."):
            try:
                results = run_h1b_job_finder_streamlit(
                    keywords=job_keywords,
                    location=job_location,
                    num_pages=num_pages,
                    use_ai=use_ai_filter,
                    match_threshold=match_threshold,
                    date_filter=date_filter,
                    sources={
                        "jsearch": use_jsearch,
                        "adzuna": use_adzuna,
                        "indeed": use_indeed,
                    },
                )

                if results and results["matched_jobs"]:
                    st.success(
                        f"✅ Found **{len(results['matched_jobs'])}** H1B + resume matches!"
                    )

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Scraped", results["total_jobs"])
                    col2.metric("H1B Eligible", len(results["h1b_jobs"]))
                    col3.metric("Resume Matches", len(results["matched_jobs"]))
                    col4.metric(
                        "Exclusion Rate",
                        f"{results['exclusion_rate']:.1f}%",
                    )

                    df = pd.DataFrame(results["matched_jobs"])

                    if "posted_at" in df.columns:
                        df["posted_date"] = pd.to_datetime(
                            df["posted_at"]
                        ).dt.date.astype(str)
                    elif "posted_date" in df.columns:
                        df["posted_date"] = pd.to_datetime(
                            df["posted_date"]
                        ).dt.date.astype(str)
                    else:
                        df["posted_date"] = ""

                    display_df = df[
                        [
                            "title",
                            "company",
                            "location",
                            "source",
                            "match_score",
                            "posted_date",
                            "gap_skills",
                            "gap_use_case",
                            "url",
                        ]
                    ]
                    st.markdown("### 🔥 Top H1B + Resume Matches")
                    st.dataframe(display_df, use_container_width=True)

                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Full Report (CSV)",
                        csv,
                        f"h1b_jobs_{job_keywords.replace(' ', '_')}.csv",
                        mime="text/csv",
                    )

                    if "resume_path" in df.columns:
                        resume_jobs = df[df["resume_path"].notna()]
                        if not resume_jobs.empty:
                            st.markdown("### 📄 Generated Tailored Resumes")
                            for _, row in resume_jobs.iterrows():
                                st.info(
                                    f"✅ **{row['title'][:60]}** → {row['resume_path']}"
                                )

                elif results and results["h1b_jobs"]:
                    st.warning(
                        f"✅ Found {len(results['h1b_jobs'])} H1B jobs, but **no strong resume matches**"
                    )
                    st.info(
                        "💡 Try: lower match threshold, upload different resume, or broader keywords"
                    )

                    df = pd.DataFrame(results["h1b_jobs"])
                    cols = ["title", "company", "location", "source"]
                    if "posted_at" in df.columns:
                        df["posted_date"] = pd.to_datetime(
                            df["posted_at"]
                        ).dt.date.astype(str)
                        cols.append("posted_date")

                    st.markdown("### H1B-Eligible Jobs")
                    st.dataframe(df[cols].head(20))
                else:
                    st.warning("No H1B-eligible jobs found.")

                # ================= EMAIL SENDING =================
                st.markdown("---")
                if send_email_enabled and recipient_email:
                    st.markdown("### 📧 Sending Email Report")
                    with st.spinner(f"Sending email to {recipient_email}..."):
                        try:
                            st.info("Step 1/5: Importing email sender module...")
                            from src.utils.email_sender import send_email

                            st.success("✅ Email sender imported successfully")

                            st.info("Step 2/5: Creating HTML email body...")
                            email_body = f"""
<html>
<head>
  <style>
    body {{ font-family: Arial, sans-serif; }}
    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
    .summary {{ margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 5px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
    th {{ background-color: #4CAF50; color: white; padding: 12px; text-align: left; }}
    td {{ border: 1px solid #ddd; padding: 12px; }}
    tr:nth-child(even) {{ background-color: #f2f2f2; }}
    .footer {{ margin-top: 30px; padding: 10px; font-size: 12px; color: #666; border-top: 1px solid #ddd; }}
    a {{ color: #0073b1; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>🌐 H1B Job Search Report</h1>
    <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p EST')}</p>
  </div>

  <div class="summary">
    <h2>Search Summary</h2>
    <p><strong>Keywords:</strong> {job_keywords}</p>
    <p><strong>Location:</strong> {job_location}</p>
    <p><strong>Total Jobs Scraped:</strong> {results['total_jobs']}</p>
    <p><strong>H1B-Eligible Jobs:</strong> {len(results['h1b_jobs'])}</p>
    <p><strong>Exclusion Rate:</strong> {results['exclusion_rate']:.1f}%</p>
  </div>

  <h2>Top H1B-Eligible Jobs</h2>
  <table>
    <thead>
      <tr>
        <th>Job Title</th>
        <th>Company</th>
        <th>Location</th>
        <th>Source</th>
        <th>Link</th>
      </tr>
    </thead>
    <tbody>
"""
                            for job in results["h1b_jobs"][:20]:
                                email_body += f"""
      <tr>
        <td>{job.get('title', 'N/A')}</td>
        <td>{job.get('company', 'N/A')}</td>
        <td>{job.get('location', 'N/A')}</td>
        <td>{job.get('source', 'N/A')}</td>
        <td><a href="{job.get('url', '#')}">Apply</a></td>
      </tr>
"""

                            email_body += """
    </tbody>
  </table>

  <div class="footer">
    <p>Full CSV report is attached to this email.</p>
    <p>This is an automated report from H1B Job Search Agent.</p>
  </div>
</body>
</html>
"""
                            st.success("✅ Email body created")

                            st.info("Step 3/5: Creating CSV attachment...")
                            from pathlib import Path
                            import tempfile

                            if results and results.get("matched_jobs"):
                                df_email = pd.DataFrame(results["matched_jobs"])
                            elif results and results.get("h1b_jobs"):
                                df_email = pd.DataFrame(results["h1b_jobs"])
                            else:
                                df_email = pd.DataFrame([])

                            temp_dir = Path(tempfile.gettempdir())
                            csv_filename = (
                                f"h1b_jobs_{job_keywords.replace(' ', '_')}_"
                                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            )
                            csv_path = temp_dir / csv_filename
                            df_email.to_csv(csv_path, index=False)
                            st.success(f"✅ CSV saved: {csv_path}")

                            st.info(
                                f"Step 4/5: Sending email to {recipient_email}..."
                            )
                            result_msg = send_email(
                                recipient=recipient_email,
                                subject=(
                                    f"H1B Jobs Report: {job_keywords} - "
                                    f"{len(results['h1b_jobs'])} jobs found"
                                ),
                                body=email_body,
                                attachment=str(csv_path),
                            )

                            st.success(f"✅ Step 5/5: {result_msg}")
                            st.info(
                                f"📎 Attached: {csv_filename} "
                                f"({len(results['h1b_jobs'])} jobs)"
                            )

                            csv_path.unlink(missing_ok=True)
                            st.success("✅ Temporary file cleaned up")

                        except ImportError as import_error:
                            st.error(f"❌ Import Error: {str(import_error)}")
                            import traceback

                            st.code(traceback.format_exc())
                            st.warning(
                                "Results are still available for download above."
                            )
                        except Exception as email_error:
                            st.error(
                                f"❌ Email sending failed: {str(email_error)}"
                            )
                            import traceback

                            st.code(traceback.format_exc())
                            st.warning(
                                "Results are still available for download above."
                            )

                elif send_email_enabled and not recipient_email:
                    st.warning(
                        "⚠️ Email sending is enabled but no recipient email entered!"
                    )
                    st.info(
                        "💡 Enter your email address in the 'Recipient Email' field above."
                    )
                elif not send_email_enabled:
                    st.info(
                        "ℹ️ Email sending is disabled. Check the 'Send email report' box to enable."
                    )

                st.markdown("### 📋 Job Details")
                jobs_to_show = results.get(
                    "matched_jobs", results.get("h1b_jobs", [])
                )
                for idx, job in enumerate(jobs_to_show[:10]):
                    with st.expander(f"{job['title']} - {job['company']}"):
                        st.write(f"**Location:** {job['location']}")
                        st.write(f"**Source:** {job['source']}")
                        st.write(f"**Match Score:** {job.get('match_score', 'N/A')}")
                        st.write(f"**Description:** {job['description'][:300]}...")
                        if job.get("url"):
                            st.link_button("Apply Now", job["url"])

            except Exception as e:
                st.error(f"Error running H1B finder: {e}")
                st.exception(e)

    st.markdown("---")
    st.markdown("### 📁 Recent Reports")
    report_path = Path("output/reports/h1b_daily_report.csv")
    if report_path.exists():
        try:
            df_report = pd.read_csv(report_path)
            mod_time = datetime.fromtimestamp(report_path.stat().st_mtime)
            st.write(f"Last run: {mod_time.strftime('%B %d, %Y at %I:%M %p')}")
            st.dataframe(df_report.head(10), use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load previous report: {e}")

# ============= TAB 3: Daily Pipeline (disabled) =============
with TAB_PIPELINE:
    st.subheader("⚙️ Daily Pipeline")
    st.warning("⏳ **Daily pipeline temporarily disabled** (needs refactor)")
    st.info(
        "💡 Use **H1B Job Finder** tab for live scraping + RAG matching instead!"
    )

# Build index at startup (best-effort)
try:
    build_or_refresh_profile_index()
except Exception:
    pass
