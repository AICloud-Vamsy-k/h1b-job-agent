import os
from dotenv import load_dotenv
from src.utils.email_sender import EmailReporter

load_dotenv()

# Load settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
REPORT_RECIPIENT = os.getenv("REPORT_RECIPIENT", EMAIL_USER)

print(f"Email User: {EMAIL_USER}")
print(f"Password: {'*' * 10 if EMAIL_PASSWORD else 'NOT SET'}")
print(f"Recipient: {REPORT_RECIPIENT}")
print(f"SMTP: {SMTP_HOST}:{SMTP_PORT}")

# Test email
if EMAIL_USER and EMAIL_PASSWORD:
    print("\n🔧 Testing email sender...")
    
    reporter = EmailReporter(SMTP_HOST, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD)
    
    # Send test email with fake job data
    test_jobs = [{
        'title': 'Senior Python Developer',
        'company': 'Tech Corp',
        'location': 'New York, NY',
        'source': 'Test',
        'eligibility_reason': 'No visa restrictions mentioned',
        'url': 'https://example.com',
        'h1b_eligible': True,
        'description': 'Test job description'
    }]
    
    try:
        reporter.send_report(test_jobs, REPORT_RECIPIENT)
        print("✅ Test email sent successfully!")
        print(f"📧 Check your inbox at {REPORT_RECIPIENT}")
        print("   (Also check spam/junk folder)")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Email credentials not configured")
