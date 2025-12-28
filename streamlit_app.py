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


# ============ NEW TAB: H1B JOB FINDER ============
with TAB_H1B:
    st.subheader("🌐 Real-Time H1B Job Finder")
    st.write("""
    Search real job boards (LinkedIn, Indeed, etc.) and filter for H1B-eligible positions.
    - ✅ Scrapes live jobs from APIs
    - ✅ AI-powered H1B eligibility filtering
    - ✅ Excludes "GC/Citizen only" postings
    - ✅ Generates downloadable CSV report
    - ✅ Sends email report automatically
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
    
    # EMAIL CONFIGURATION - NEW!
    st.markdown("### 📧 Email Report Settings")
    col5, col6 = st.columns(2)
    with col5:
        recipient_email = st.text_input(
            "Recipient Email",
            value="",  # IMPORTANT: Empty by default so user must enter
            placeholder="your-email@example.com",
            help="Email address to receive the job report"
        )
    with col6:
        send_email_enabled = st.checkbox("Send email report", value=True)
    
    # DEBUG PANEL - Shows current email settings
    with st.expander("🔧 Email Debug Panel (expand to check config)"):
        st.write("**Current Settings:**")
        st.write(f"- Send email enabled: `{send_email_enabled}`")
        st.write(f"- Recipient email: `{recipient_email if recipient_email else 'NOT SET'}`")
        st.write(f"- Will send email: `{send_email_enabled and bool(recipient_email)}`")
        
        st.markdown("---")
        st.write("**Email Configuration Check:**")
        try:
            from config.settings import SMTP_HOST, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD
            st.success("✅ Email config imported successfully")
            st.code(f"""
SMTP_HOST: {SMTP_HOST}
SMTP_PORT: {SMTP_PORT}
EMAIL_USER: {EMAIL_USER}
EMAIL_PASSWORD: {'***' + EMAIL_PASSWORD[-4:] if EMAIL_PASSWORD else 'NOT SET'}
            """, language="text")
        except Exception as config_error:
            st.error(f"❌ Config import failed: {config_error}")
            import traceback
            st.code(traceback.format_exc())
    
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
                    display_df = df[['title', 'company', 'location', 'source']]
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Full Report (CSV)",
                        data=csv,
                        file_name=f"h1b_jobs_{job_keywords.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                    
                    # ========== EMAIL SENDING - ENHANCED WITH DEBUG ==========
                    st.write(f"**Email Debug:** send_email_enabled={send_email_enabled}, recipient_email='{recipient_email}'")
                    
                    if send_email_enabled and recipient_email:
                        st.markdown("---")
                        st.markdown("### 📧 Sending Email Report")
                        
                        with st.spinner(f"Sending email to {recipient_email}..."):
                            try:
                                # Import email utilities
                                st.info("Step 1/5: Importing email sender module...")
                                from src.utils.email_sender import send_email
                                from datetime import datetime
                                st.success("✅ Email sender imported successfully")
                                
                                # Create HTML email body
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
                                
                                # Add first 20 jobs to email
                                for job in results['h1b_jobs'][:20]:
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
                                
                                # Save CSV temporarily for attachment
                                st.info("Step 3/5: Creating CSV attachment...")
                                from pathlib import Path
                                import tempfile
                                
                                temp_dir = Path(tempfile.gettempdir())
                                csv_filename = f"h1b_jobs_{job_keywords.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                                csv_path = temp_dir / csv_filename
                                df.to_csv(csv_path, index=False)
                                st.success(f"✅ CSV saved: {csv_path}")
                                
                                # Send email with attachment
                                st.info(f"Step 4/5: Sending email to {recipient_email}...")
                                result = send_email(
                                    recipient=recipient_email,
                                    subject=f"H1B Jobs Report: {job_keywords} - {len(results['h1b_jobs'])} jobs found",
                                    body=email_body,
                                    attachment=str(csv_path)
                                )
                                
                                st.success(f"✅ Step 5/5: {result}")
                                st.info(f"📎 Attached: {csv_filename} ({len(results['h1b_jobs'])} jobs)")
                                
                                # Clean up temp file
                                csv_path.unlink(missing_ok=True)
                                st.success("✅ Temporary file cleaned up")
                                
                            except ImportError as import_error:
                                st.error(f"❌ Import Error: {str(import_error)}")
                                st.error("This usually means the send_email function is not found in email_sender.py")
                                import traceback
                                st.code(traceback.format_exc())
                                st.warning("Results are still available for download above.")
                                
                            except Exception as email_error:
                                st.error(f"❌ Email sending failed: {str(email_error)}")
                                st.error(f"Error type: {type(email_error).__name__}")
                                import traceback
                                st.code(traceback.format_exc())
                                st.warning("Results are still available for download above.")
                    
                    elif send_email_enabled and not recipient_email:
                        st.warning("⚠️ Email sending is enabled but no recipient email entered!")
                        st.info("💡 Enter your email address in the 'Recipient Email' field above to receive the report.")
                    
                    elif not send_email_enabled:
                        st.info("ℹ️ Email sending is disabled. Check the 'Send email report' box to enable.")
                    
                    # Show individual job details (expandable)
                    st.markdown("### 📋 Job Details")
                    for idx, job in enumerate(results['h1b_jobs'][:10]):  # Show first 10
                        with st.expander(f"{job['title']} - {job['company']}"):
                            st.write(f"**Location:** {job['location']}")
                            st.write(f"**Source:** {job['source']}")
                            st.write(f"**Description:** {job['description'][:300]}...")
                            if 'url' in job and job['url']:
                                st.link_button("Apply Now", job['url'])
                else:
                    st.warning("No H1B-eligible jobs found. Try different keywords or location.")
                    
            except Exception as e:
                st.error(f"Error running H1B finder: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # Show previous results if available
    st.markdown("---")
    st.markdown("### 📁 Recent Reports")
    report_path = Path("output/reports/h1b_daily_report.csv")
    if report_path.exists():
        try:
            import pandas as pd
            df_report = pd.read_csv(report_path)
            from datetime import datetime
            mod_time = datetime.fromtimestamp(report_path.stat().st_mtime)
            st.write(f"Last run: {mod_time.strftime('%B %d, %Y at %I:%M %p')}")
            st.dataframe(df_report.head(10), use_container_width=True)
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
