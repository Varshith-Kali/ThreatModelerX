"""
Code Cleanup Script for ThreatModelerX
Removes comment lines from Python and TypeScript files while preserving docstrings and essential comments.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

class CodeCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.stats = {
            'files_processed': 0,
            'comments_removed': 0,
            'lines_removed': 0,
            'files_skipped': 0
        }
        
    def should_skip_directory(self, path: Path) -> bool:
        skip_dirs = {'.venv', 'node_modules', '__pycache__', '.git', 'dist', 'build'}
        return any(skip_dir in path.parts for skip_dir in skip_dirs)
    
    def clean_python_file(self, file_path: Path) -> Tuple[str, int]:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        cleaned_lines = []
        comments_removed = 0
        in_docstring = False
        docstring_char = None
        
        for line in lines:
            stripped = line.strip()
            
            if '"""' in stripped or "'''" in stripped:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = '"""' if '"""' in stripped else "'''"
                    cleaned_lines.append(line)
                elif docstring_char in stripped:
                    in_docstring = False
                    cleaned_lines.append(line)
                else:
                    cleaned_lines.append(line)
                continue
            
            if in_docstring:
                cleaned_lines.append(line)
                continue
            
            if stripped.startswith('#'):
                if any(keyword in stripped.lower() for keyword in ['todo', 'fixme', 'hack', 'note', 'important']):
                    cleaned_lines.append(line)
                else:
                    comments_removed += 1
                continue
            
            if '#' in line and not ('"' in line or "'" in line):
                code_part = line.split('#')[0]
                if code_part.strip():
                    cleaned_lines.append(code_part.rstrip() + '\n')
                else:
                    comments_removed += 1
                continue
            
            cleaned_lines.append(line)
        
        return ''.join(cleaned_lines), comments_removed
    
    def clean_typescript_file(self, file_path: Path) -> Tuple[str, int]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        comments_removed = 0
        
        content = re.sub(r'/\*\*[\s\S]*?\*/', '', content)
        multiline_matches = re.findall(r'/\*[\s\S]*?\*/', content)
        comments_removed += len(multiline_matches)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if '//' in line:
                if any(keyword in line.lower() for keyword in ['todo', 'fixme', 'hack', 'note', 'important']):
                    cleaned_lines.append(line)
                else:
                    code_part = line.split('//')[0]
                    if code_part.strip():
                        cleaned_lines.append(code_part.rstrip())
                    else:
                        comments_removed += 1
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines), comments_removed
    
    def process_file(self, file_path: Path):
        if self.should_skip_directory(file_path):
            self.stats['files_skipped'] += 1
            return
        
        try:
            if file_path.suffix == '.py':
                cleaned_content, comments = self.clean_python_file(file_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                self.stats['files_processed'] += 1
                self.stats['comments_removed'] += comments
                print(f"✓ Cleaned {file_path.relative_to(self.project_root)} - Removed {comments} comments")
                
            elif file_path.suffix in ['.tsx', '.ts']:
                cleaned_content, comments = self.clean_typescript_file(file_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                self.stats['files_processed'] += 1
                self.stats['comments_removed'] += comments
                print(f"✓ Cleaned {file_path.relative_to(self.project_root)} - Removed {comments} comments")
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {str(e)}")
            self.stats['files_skipped'] += 1
    
    def clean_project(self):
        print("=" * 60)
        print("ThreatModelerX Code Cleanup")
        print("=" * 60)
        print()
        
        py_files = list(self.project_root.rglob('*.py'))
        tsx_files = list(self.project_root.rglob('*.tsx'))
        ts_files = list(self.project_root.rglob('*.ts'))
        
        all_files = py_files + tsx_files + ts_files
        
        print(f"Found {len(py_files)} Python files")
        print(f"Found {len(tsx_files)} TSX files")
        print(f"Found {len(ts_files)} TS files")
        print(f"Total: {len(all_files)} files to process")
        print()
        
        for file_path in all_files:
            self.process_file(file_path)
        
        print()
        print("=" * 60)
        print("Cleanup Summary")
        print("=" * 60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        print(f"Comments removed: {self.stats['comments_removed']}")
        print()
        print("✓ Code cleanup complete!")

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    cleaner = CodeCleaner(project_root)
    cleaner.clean_project()
