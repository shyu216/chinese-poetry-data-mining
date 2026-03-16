import os
import fnmatch
from pathlib import Path

def load_gitignore_patterns(gitignore_path):
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns

def should_ignore(path, patterns, results_root):
    rel_path = os.path.relpath(path, results_root)
    for pattern in patterns:
        if pattern.startswith('results/'):
            pattern = pattern[8:]
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(rel_path, pattern + '*'):
            return True
        if os.path.dirname(rel_path).startswith(pattern.rstrip('/')):
            return True
    return False

def get_largest_files(results_dir, gitignore_path, top_n=5):
    patterns = load_gitignore_patterns(gitignore_path)
    
    file_sizes = []
    results_path = Path(results_dir)
    
    for root, dirs, files in os.walk(results_path):
        for file in files:
            file_path = os.path.join(root, file)
            if should_ignore(file_path, patterns, results_dir):
                continue
            try:
                size = os.path.getsize(file_path)
                file_sizes.append((file_path, size))
            except OSError:
                continue
    
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    return file_sizes[:top_n]

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

if __name__ == '__main__':
    gitignore_path = '.gitignore'
    results_dir = 'results'
    
    largest_files = get_largest_files(results_dir, gitignore_path)
    
    print(f"Top 5 largest files in '{results_dir}' (excluding .gitignore patterns):\n")
    for i, (file_path, size) in enumerate(largest_files, 1):
        print(f"{i}. {file_path}")
        print(f"   Size: {format_size(size)}\n")
