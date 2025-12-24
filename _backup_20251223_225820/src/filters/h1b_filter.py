import re
from openai import OpenAI

class H1BFilter:
    """Filters jobs to exclude GC/Citizen-only postings"""
    
    def __init__(self, openai_api_key):
        self.client = OpenAI(api_key=openai_api_key)
        
        # Common phrases that indicate NO H1B sponsorship
        self.exclude_patterns = [
            r'green card.*required',
            r'gc.*required',
            r'citizenship.*required',
            r'us citizen.*required',
            r'must be.*us citizen',
            r'must be.*green card',
            r'no visa sponsor',
            r'no sponsorship',
            r'cannot sponsor',
            r'will not sponsor',
            r'us authorization required',
            r'permanent.*resident.*only',
            r'security clearance.*required',
            r'active.*clearance'
        ]
        
    def is_h1b_friendly_rule_based(self, job):
        """Quick rule-based filter using regex patterns"""
        combined_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        for pattern in self.exclude_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return False, f"Excluded: Found pattern '{pattern}'"
                
        return True, "No exclusion patterns found"
        
    def is_h1b_friendly_ai(self, job):
        """
        Use OpenAI to detect subtle exclusions
        Returns: (is_eligible: bool, reason: str)
        """
        prompt = f"""You are an H1B visa eligibility expert. Analyze this job posting and determine if it excludes H1B visa holders.

Job Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Description: {job.get('description', '')[:800]}

Look for:
1. Explicit requirements: "Green Card required", "US Citizen only", "No visa sponsorship"
2. Implicit restrictions: "Must have permanent US work authorization", "No sponsorship available"
3. Positive signals: "Visa sponsorship available", "H1B welcome", no restrictions mentioned

Answer in this format:
ELIGIBLE: Yes/No
REASON: Brief explanation

Be conservative - if unsure, mark as "Yes" (eligible)."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse response
            is_eligible = "ELIGIBLE: Yes" in result or "ELIGIBLE: YES" in result.upper()
            reason_match = re.search(r'REASON: (.+)', result, re.IGNORECASE)
            reason = reason_match.group(1).strip() if reason_match else result
            
            return is_eligible, reason
            
        except Exception as e:
            print(f"  ⚠️  AI filter error: {e}")
            return True, "AI check failed, defaulting to eligible"
            
    def filter_jobs(self, jobs, use_ai=True):
        """
        Filter jobs and return only H1B-friendly ones
        Returns: list of filtered jobs with eligibility fields added
        """
        filtered = []
        
        print(f"\n🔍 Filtering {len(jobs)} jobs for H1B eligibility...")
        
        for idx, job in enumerate(jobs, 1):
            print(f"  [{idx}/{len(jobs)}] Checking: {job.get('title', 'N/A')[:50]}...")
            
            # First: Quick rule-based filter
            rule_eligible, rule_reason = self.is_h1b_friendly_rule_based(job)
            
            if not rule_eligible:
                job['h1b_eligible'] = False
                job['eligibility_reason'] = rule_reason
                print(f"    ❌ {rule_reason}")
                continue  # Skip this job
                
            # Second: AI-based deep check (optional, slower but more accurate)
            if use_ai:
                ai_eligible, ai_reason = self.is_h1b_friendly_ai(job)
                job['h1b_eligible'] = ai_eligible
                job['eligibility_reason'] = ai_reason
                
                if ai_eligible:
                    filtered.append(job)
                    print(f"    ✅ {ai_reason[:60]}")
                else:
                    print(f"    ❌ {ai_reason[:60]}")
            else:
                job['h1b_eligible'] = True
                job['eligibility_reason'] = rule_reason
                filtered.append(job)
                print(f"    ✅ Passed rule-based check")
                
        print(f"\n✅ Filtered: {len(filtered)} H1B-eligible jobs out of {len(jobs)}")
        return filtered
