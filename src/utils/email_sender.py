import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path


class EmailReporter:
    def __init__(self, smtp_host, smtp_port, email_user, email_password):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_password = email_password

    def generate_html_table(self, jobs):
        """Convert jobs list to HTML table"""
        if not jobs:
            return "<p>No H1B-friendly jobs found today.</p>"
        
        df = pd.DataFrame(jobs)
        
        # Select and reorder columns for report
        columns = ['title', 'company', 'location', 'source', 'eligibility_reason', 'url']
        df = df[columns]
        
        # Create clickable links
        df['url'] = df['url'].apply(lambda x: f'<a href="{x}">Apply</a>')
        
        # Convert to HTML with styling
        html = df.to_html(index=False, escape=False, classes='job-table')
        
        # Add CSS styling
        styled_html = f"""
        <style>
            .job-table {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
            }}
            .job-table th {{
                background-color: #0073b1;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            .job-table td {{
                border: 1px solid #ddd;
                padding: 10px;
            }}
            .job-table tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .job-table a {{
                color: #0073b1;
                text-decoration: none;
                font-weight: bold;
            }}
        </style>
        {html}
        """
        return styled_html

    def send_report(self, jobs, recipient_email):
        """Send email report with jobs table"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"H1B Job Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = self.email_user
        msg['To'] = recipient_email
        
        # Email body
        html_table = self.generate_html_table(jobs)
        html_body = f"""
        <html>
        <body>
            <h2>Daily H1B-Friendly Job Report</h2>
            <p>Found <strong>{len(jobs)}</strong> H1B-eligible jobs today.</p>
            <br>
            {html_table}
            <br>
            <p><em>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            print(f"✅ Email sent to {recipient_email}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")


# ========== STANDALONE FUNCTION FOR STREAMLIT (OUTSIDE THE CLASS!) ==========
def send_email(recipient: str, subject: str, body: str, attachment: str = None) -> str:
    """
    Standalone function to send email (compatible with streamlit_app.py).
    
    Args:
        recipient: Email address of recipient
        subject: Email subject line
        body: HTML email body
        attachment: Optional path to CSV file
    
    Returns:
        Success message string
    """
    import sys
    from pathlib import Path
    import os
    
    # Add parent directories to path to find config
    sys.path.insert(0, str(Path(__file__).parents[2]))
    
    # Try to import from config.settings
    try:
        from config.settings import SMTP_HOST, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD
    except ImportError:
        # Fallback to environment variables
        SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        EMAIL_USER = os.getenv('EMAIL_USER')
        EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    
    # Validate configuration
    if not all([SMTP_HOST, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD]):
        raise ValueError(
            f"Email configuration incomplete. Check .env file.\n"
            f"SMTP_HOST: {SMTP_HOST}\n"
            f"SMTP_PORT: {SMTP_PORT}\n"
            f"EMAIL_USER: {EMAIL_USER}\n"
            f"EMAIL_PASSWORD: {'***' if EMAIL_PASSWORD else 'NOT SET'}"
        )
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = recipient
    
    # Attach HTML body
    html_part = MIMEText(body, 'html')
    msg.attach(html_part)
    
    # Attach file if provided
    if attachment:
        attachment_path = Path(attachment)
        if attachment_path.exists():
            with open(attachment_path, 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={attachment_path.name}'
                )
                msg.attach(part)
    
    # Send email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return f"Email sent successfully to {recipient}"
    
    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"SMTP Authentication failed. Check Gmail App Password: {e}")
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")


# Test function
if __name__ == "__main__":
    import sys
    
    print("Testing email functionality...")
    
    if len(sys.argv) > 1:
        test_recipient = sys.argv[1]
    else:
        test_recipient = input("Enter test email address: ")
    
    try:
        result = send_email(
            recipient=test_recipient,
            subject="Test Email from H1B Job Agent",
            body="<h1>Test Email</h1><p>If you see this, email configuration is working!</p>",
        )
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Failed: {e}")
