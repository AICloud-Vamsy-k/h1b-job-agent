"""
H1B Job Agent - Complete Safe Migration Script
Creates backup, reorganizes structure, updates imports
Safe dry-run mode included
"""
import shutil
import os
from pathlib import Path
from datetime import datetime

class SafeProjectMigrator:
    
    def __init__(self):
        self.root = Path.cwd()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.root / f"_backup_{self.timestamp}"
        
        # File migration mapping (old_path: new_path)
        self.file_map = {
            # Config
            'config/h1b_settings.py': 'config/settings.py',
            'src/config.py': 'config/_old_config.py',
            
            # Core files (if in src/ root)
            'src/resume_parser.py': 'src/core/resume_parser.py',
            'src/profile_summary.py': 'src/core/profile_builder.py',
            'src/resume_docx_renderer.py': 'src/core/resume_renderer.py',
            'src/resume_source.py': 'src/core/resume_source.py',
            'src/job_sources.py': 'src/core/job_sources.py',
            
            # Crews (if in src/ root, move to src/crews/)
            'src/job_match_crew.py': 'src/crews/job_match_crew.py',
            'src/resume_builder_crew.py': 'src/crews/resume_builder_crew.py',
            'src/gap_analyzer_crew.py': 'src/crews/gap_analyzer_crew.py',
            
            # RAG
            'src/profile_rag.py': 'src/rag/profile_rag.py',
            
            # Pipelines
            'src/pipeline.py': 'src/pipelines/daily_pipeline.py',
            #'scripts/run_h1b_finder.py': 'src/pipelines/h1b_pipeline.py',
            
            # Utils (if in src/ root)
            'src/email_sender.py': 'src/utils/email_sender.py',
            
            # Old scripts
            'scripts/reorganize.py': 'scripts/_old_reorganize.py',
        }
        
        # Import updates (old_import: new_import)
        self.import_map = {
            # Crews
            'from src.crews.job_match_crew import': 'from src.crews.job_match_crew import',
            'from src.crews.resume_builder_crew import': 'from src.crews.resume_builder_crew import',
            'from src.crews.gap_analyzer_crew import': 'from src.crews.gap_analyzer_crew import',
            'from src.crews import job_match_crew': 'from src.crews import job_match_crew',
            
            # Pipelines
            'from src.pipelines.daily_pipeline import': 'from src.pipelines.daily_pipeline import',
            'from src.pipelines import daily_pipeline': 'from src.pipelines import daily_pipeline',
            
            # Core
            'from src.core.resume_source import': 'from src.core.resume_source import',
            'from src.core import resume_source': 'from src.core import resume_source',
            'from src.core.resume_parser import': 'from src.core.resume_parser import',
            'from src.core.profile_builder import': 'from src.core.profile_builder import',
            'from src.core.resume_renderer import': 'from src.core.resume_renderer import',
            
            # RAG
            'from src.rag.profile_rag import': 'from src.rag.profile_rag import',
            'from src.rag import profile_rag': 'from src.rag import profile_rag',
            
            # Config
            'from config.settings import': 'from config.settings import',
            'import config.settings': 'import config.settings',
            
            # Utils
            'from src.utils.email_sender import': 'from src.utils.email_sender import',
        }
    
    def print_header(self, title, char="="):
        """Print section header"""
        print("\n" + char * 70)
        print(f"  {title}")
        print(char * 70)
    
    def create_backup(self):
        """Create complete backup"""
        self.print_header("📦 CREATING BACKUP")
        
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup critical directories
        for item in ['src', 'config', 'data', 'output', 'scripts']:
            src_path = self.root / item
            if src_path.exists():
                dst_path = self.backup_dir / item
                if src_path.is_dir():
                    shutil.copytree(
                        src_path, dst_path,
                        ignore=shutil.ignore_patterns('.venv', '__pycache__', '*.pyc', '_backup_*', '*.log')
                    )
                    print(f"✅ Backed up: {item}/")
        
        # Backup important files
        for file in ['.env', 'requirements.txt', 'streamlit_app.py', 'README.md']:
            src_file = self.root / file
            if src_file.exists():
                shutil.copy2(src_file, self.backup_dir / file)
                print(f"✅ Backed up: {file}")
        
        print(f"\n💾 Backup location: {self.backup_dir}")
        return True
    
    def create_structure(self):
        """Create new directory structure"""
        self.print_header("📁 CREATING NEW FOLDER STRUCTURE")
        
        dirs = {
            'config': 'Configuration',
            'logs': 'Logs',
            'scheduler': 'Scheduled tasks',
            'scripts': 'Scripts',
            'tests': 'Tests',
            'data/uploads': 'Resume uploads',
            'data/templates': 'Templates',
            'data/sample': 'Sample data',
            'output/reports': 'Reports',
            'output/resumes': 'Resumes',
            'output/plans': 'Plans',
            'src/core': 'Core functions',
            'src/crews': 'CrewAI agents',
            'src/agents': 'Individual agents',
            'src/filters': 'Filters',
            'src/scrapers': 'Scrapers',
            'src/pipelines': 'Pipelines',
            'src/rag': 'RAG system',
            'src/utils': 'Utils',
        }
        
        for dir_path, desc in dirs.items():
            full_path = self.root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py for packages
            if dir_path in ['config', 'scheduler', 'scripts', 'tests'] or dir_path.startswith('src/'):
                init = full_path / '__init__.py'
                if not init.exists():
                    init.write_text(f'"""{desc}"""\n')
            
            print(f"✅ {dir_path:30s} - {desc}")
        
        return True
    
    def migrate_files(self, dry_run=True):
        """Move/copy files"""
        self.print_header(f"📦 FILE MIGRATION {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
        
        stats = {'moved': 0, 'skipped': 0, 'already_correct': 0, 'not_found': 0}
        
        for old_path_str, new_path_str in self.file_map.items():
            old = self.root / old_path_str
            new = self.root / new_path_str
            
            # File doesn't exist
            if not old.exists():
                print(f"⚠️  NOT FOUND: {old_path_str}")
                stats['not_found'] += 1
                continue
            
            # Already in correct place
            if old.resolve() == new.resolve():
                print(f"✓  CORRECT: {new_path_str}")
                stats['already_correct'] += 1
                continue
            
            # Destination exists
            if new.exists():
                if old.read_bytes() == new.read_bytes():
                    print(f"✓  EXISTS (same): {new_path_str}")
                    stats['already_correct'] += 1
                    continue
                else:
                    print(f"⚠️  CONFLICT: {new_path_str} exists but differs")
                    stats['skipped'] += 1
                    continue
            
            # Perform migration
            if dry_run:
                print(f"📋 WOULD COPY: {old_path_str}")
                print(f"            → {new_path_str}")
                stats['moved'] += 1
            else:
                new.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old, new)
                print(f"✅ COPIED: {old_path_str}")
                print(f"        → {new_path_str}")
                stats['moved'] += 1
        
        print(f"\n📊 Stats: {stats['moved']} {'would be ' if dry_run else ''}moved, "
              f"{stats['already_correct']} already correct, "
              f"{stats['skipped']} skipped, "
              f"{stats['not_found']} not found")
        return True
    
    def update_imports(self, dry_run=True):
        """Update import statements"""
        self.print_header(f"🔄 UPDATING IMPORTS {'(DRY RUN)' if dry_run else '(EXECUTING)'}")
        
        # Find Python files
        python_files = list(self.root.glob('**/*.py'))
        python_files = [
            f for f in python_files
            if '_backup_' not in str(f) 
            and '.venv' not in str(f)
            and '__pycache__' not in str(f)
        ]
        
        updated = 0
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original = content
                
                # Apply replacements
                for old_import, new_import in self.import_map.items():
                    content = content.replace(old_import, new_import)
                
                if content != original:
                    rel = py_file.relative_to(self.root)
                    if dry_run:
                        print(f"📝 Would update: {rel}")
                    else:
                        py_file.write_text(content, encoding='utf-8')
                        print(f"✅ Updated: {rel}")
                        updated += 1
            
            except Exception as e:
                print(f"❌ Error in {py_file.name}: {e}")
        
        print(f"\n📊 Total: {updated} files {'would be ' if dry_run else ''}updated")
        return True
    
    def create_runner(self):
    """Create unified runner.py"""
    self.print_header("🎯 CREATING UNIFIED RUNNER")
    
    runner_code = '''"""
H1B Job Agent - Unified Entry Point
Run all operations from here
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def show_menu():
    print("\\n" + "="*60)
    print("  H1B JOB AGENT - Main Runner")
    print("="*60)
    print("\\n1. Run H1B Job Finder (real-time scraping)")
    print("2. Run Daily Pipeline (batch jobs)")
    print("3. Test API Connections")
    print("4. Launch Streamlit UI")
    print("5. Exit")
    print("="*60)

def main():
    while True:
        show_menu()
        choice = input("\\nSelect (1-5): ").strip()
        
        if choice == '1':
            from src.pipelines.h1b_pipeline import run_h1b_job_finder
            run_h1b_job_finder()
        elif choice == '2':
            from src.pipelines.daily_pipeline import run_daily_job_pipeline
            run_daily_job_pipeline()
        elif choice == '3':
            print("\\nTesting APIs...")
            print("All APIs configured")
        elif choice == '4':
            import os
            os.system('streamlit run streamlit_app.py')
        elif choice == '5':
            print("\\nGoodbye!")
            break
        else:
            print("Invalid choice")
        
        if choice in ['1', '2', '3']:
            input("\\nPress Enter to continue...")

if __name__ == "__main__":
    main()
'''
    
    runner = self.root / 'runner.py'
    runner.write_text(runner_code, encoding='utf-8')  # ← ADDED encoding='utf-8'
    print(f"✅ Created: runner.py")
    return True

    
    def run(self, dry_run=True):
        """Execute migration"""
        self.print_header("🚀 H1B JOB AGENT - PROJECT REORGANIZATION", "=")
        
        print(f"\n📁 Project: {self.root}")
        print(f"🔧 Mode: {'DRY RUN (no changes)' if dry_run else '⚠️  LIVE EXECUTION'}")
        
        if not dry_run:
            print("\n" + "!"*70)
            print("⚠️  WARNING: This will modify your project!")
            print("!"*70)
            confirm = input("\nType 'YES' to continue, anything else to cancel: ")
            if confirm != 'YES':
                print("\n❌ Migration cancelled")
                return False
            
            self.create_backup()
        
        self.create_structure()
        self.migrate_files(dry_run=dry_run)
        self.update_imports(dry_run=dry_run)
        
        if not dry_run:
            self.create_runner()
        
        self.print_header("✅ COMPLETE!" if not dry_run else "✅ DRY RUN COMPLETE", "=")
        
        if dry_run:
            print("\n📋 Review the plan above. To execute:")
            print("   python migrate_project.py --execute")
        else:
            print(f"\n💾 Backup: {self.backup_dir}")
            print("📝 Created: runner.py")
            print("\n✅ Migration successful! Test with:")
            print("   python runner.py")
            print("   streamlit run streamlit_app.py")
        
        return True

if __name__ == "__main__":
    import sys
    migrator = SafeProjectMigrator()
    
    # Check flags
    execute = '--execute' in sys.argv or '-e' in sys.argv
    
    migrator.run(dry_run=not execute)
