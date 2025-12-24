"""
All LLM prompts in one place for easy tuning
"""

H1B_ELIGIBILITY_PROMPT = """
You are an H1B visa eligibility expert. Analyze this job posting and determine if it excludes H1B visa holders.

Job Title: {title}
Company: {company}
Description: {description}

Look for:
1. Explicit requirements: "Green Card required", "US Citizen only", "No visa sponsorship"
2. Implicit restrictions: "Must have permanent US work authorization", "No sponsorship available"
3. Positive signals: "Visa sponsorship available", "H1B welcome", no restrictions mentioned

Answer in this format:
ELIGIBLE: Yes/No
REASON: Brief explanation

Be conservative - if unsure, mark as "Yes" (eligible).
"""

PROFILE_SUMMARY_PROMPT = """
Create a professional 5-7 line summary of this resume for job matching:

{resume_text}

Focus on:
- Key technical skills
- Years of experience
- Domain expertise
- Notable achievements

Keep it concise and ATS-friendly.
"""

# Add more prompts as needed...
