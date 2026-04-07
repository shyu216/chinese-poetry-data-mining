"""
script: 99_code_line_counter.py
stage: P0-运维辅助
artifact: 代码量统计结果
purpose: 统计项目 py, ts, vue 代码的行数。
inputs:
- scripts/
- web/src/
outputs:
- 控制台
depends_on:
- 无
develop_date: 2026-04-07
last_modified_date: 2026-04-07
- 运行
python .\scripts\99_code_line_counter.py  
"""
import os
from pathlib import Path
from typing import Dict, Tuple

def count_lines(file_path: Path) -> Tuple[int, int, int]:
    """统计文件的有效代码行数（排除空行和纯注释行）"""
    total_lines = 0
    code_lines = 0
    comment_lines = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                total_lines += 1
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith('#') or stripped.startswith('//'):
                    comment_lines += 1
                else:
                    code_lines += 1
    except (UnicodeDecodeError, OSError):
        return 0, 0, 0
    
    return total_lines, code_lines, comment_lines

def scan_directory(root_path: Path, extensions: list) -> Dict[str, Tuple[int, int, int]]:
    """扫描目录下所有指定扩展名的文件"""
    results = {}
    
    exclude_dirs = {'__pycache__', 'node_modules', '.git', 'dist', 'build', '.nuxt', '.output'}
    
    for ext in extensions:
        for file_path in root_path.rglob(f"*{ext}"):
            parts = file_path.parts
            if any(ex in parts for ex in exclude_dirs):
                continue
            total, code, comment = count_lines(file_path)
            if total > 0:
                results[str(file_path)] = (total, code, comment)
    
    return results

def main():
    project_root = Path(".")
    
    print(f"{'='*60}")
    print("代码量统计 (Python, TypeScript, Vue)")
    print(f"{'='*60}\n")
    
    stats = {}
    
    # 统计 Python 文件
    print("正在扫描 Python 文件...")
    py_files = scan_directory(project_root, ['.py'])
    py_stats = {
        'files': len(py_files),
        'total': sum(s[0] for s in py_files.values()),
        'code': sum(s[1] for s in py_files.values()),
        'comment': sum(s[2] for s in py_files.values()),
    }
    stats['Python (.py)'] = py_stats
    print(f"  找到 {py_stats['files']} 个 Python 文件\n")
    
    # 统计 TypeScript 文件
    print("正在扫描 TypeScript 文件...")
    ts_files = scan_directory(project_root, ['.ts'])
    ts_stats = {
        'files': len(ts_files),
        'total': sum(s[0] for s in ts_files.values()),
        'code': sum(s[1] for s in ts_files.values()),
        'comment': sum(s[2] for s in ts_files.values()),
    }
    stats['TypeScript (.ts)'] = ts_stats
    print(f"  找到 {ts_stats['files']} 个 TypeScript 文件\n")
    
    # 统计 Vue 文件
    print("正在扫描 Vue 文件...")
    vue_files = scan_directory(project_root, ['.vue'])
    vue_stats = {
        'files': len(vue_files),
        'total': sum(s[0] for s in vue_files.values()),
        'code': sum(s[1] for s in vue_files.values()),
        'comment': sum(s[2] for s in vue_files.values()),
    }
    stats['Vue (.vue)'] = vue_stats
    print(f"  找到 {vue_stats['files']} 个 Vue 文件\n")
    
    # 打印汇总结果
    print(f"{'='*60}")
    print("统计结果汇总")
    print(f"{'='*60}")
    print(f"{'类型':<20} {'文件数':>8} {'总行数':>10} {'代码行':>10} {'注释行':>10}")
    print(f"{'-'*60}")
    
    total_files = 0
    total_lines = 0
    total_code = 0
    total_comment = 0
    
    for name, s in stats.items():
        print(f"{name:<20} {s['files']:>8} {s['total']:>10} {s['code']:>10} {s['comment']:>10}")
        total_files += s['files']
        total_lines += s['total']
        total_code += s['code']
        total_comment += s['comment']
    
    print(f"{'-'*60}")
    print(f"{'总计':<20} {total_files:>8} {total_lines:>10} {total_code:>10} {total_comment:>10}")
    print(f"{'='*60}")
    
    # 显示 Top 10 文件
    print(f"\n{'='*60}")
    print("代码量 Top 10 文件")
    print(f"{'='*60}")
    
    all_files = []
    for ext, files in [('.py', py_files), ('.ts', ts_files), ('.vue', vue_files)]:
        for fp, (total, code, comment) in files.items():
            all_files.append((fp, code, ext))
    
    all_files.sort(key=lambda x: x[1], reverse=True)
    
    for i, (fp, code, ext) in enumerate(all_files[:10], 1):
        print(f"{i:>2}. {code:>6} 行 [{ext}] {fp}")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    main()
