import schedule
import time
from scripts.run_h1b_finder import run_h1b_job_finder

# Run every day at 9 AM
schedule.every().day.at("09:00").do(run_h1b_job_finder)

print("📅 H1B Job Finder scheduled to run daily at 9 AM")
print("   Press Ctrl+C to stop")

while True:
    schedule.run_pending()
    time.sleep(60)
