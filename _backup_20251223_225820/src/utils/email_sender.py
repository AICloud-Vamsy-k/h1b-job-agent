import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

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
