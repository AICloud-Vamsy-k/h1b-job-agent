"""
Safe file reorganization script
Run this to move files to new structure
"""
import shutil
import os

migrations = [
    # (old_path, new_path)
    ("src/resume_parser.py", "src/core/resume_parser.py"),
    ("src/profile_summary.py", "src/core/profile_builder.py"),
    ("src/resume_docx_renderer.py", "src/core/resume_renderer.py"),
    ("src/profile_rag.py", "src/rag/profile_rag.py"),
    ("src/pipeline.py", "src/pipelines/daily_pipeline.py"),
    ("src/config.py", "config/settings.py"),
]

def migrate_files():
    for old, new in migrations:
        if os.path.exists(old):
            print(f"Moving {old} -> {new}")
            shutil.move(old, new)
        else:
            print(f"⚠️  {old} not found, skipping")
    
    # Copy crew files into crews/ folder
    crew_files = [
        "src/job_match_crew.py",
        "src/resume_builder_crew.py", 
        "src/gap_analyzer_crew.py"
    ]
    
    for crew_file in crew_files:
        if os.path.exists(crew_file):
            new_path = crew_file.replace("src/", "src/crews/")
            print(f"Copying {crew_file} -> {new_path}")
            shutil.copy(crew_file, new_path)
    
    print("\n✅ Migration complete!")
    print("⚠️  Remember to update import statements in moved files")

if __name__ == "__main__":
    migrate_files()
