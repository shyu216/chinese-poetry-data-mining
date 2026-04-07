#!/usr/bin/env python3
"""
script: 02_generate-authors-meta-v2.py
stage: P4-检索索引构建
artifact: authors meta v2
purpose: 配对 author(v1 JSON) 与 author_v2(FBS) 生成 chunks 元数据。
inputs:
- results/author
- results/author_v2
outputs:
- results/author_v2
depends_on:
- author_sim_v2.py
develop_date: 2026-03-15
last_modified_date: 2026-03-16
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 设置控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def generate_authors_meta_v2():
    """Generate metadata for author chunks (v2 FBS format)."""
    # Find the project root (where this script is located)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    # Path to author chunks v1 (JSON format) - used to determine author counts
    json_dir = project_root / "results" / "author"
    # Path to author chunks v2 (FBS format) - for actual filenames
    fbs_dir = project_root / "results" / "author_v2"
    output_dir = fbs_dir
    if not json_dir.exists():
        print(f"❌ Author v1 directory not found: {json_dir}")
        return False
    if not fbs_dir.exists():
        print(f"❌ Author v2 directory not found: {fbs_dir}")
        return False
    # Get all v1 JSON and v2 FBS chunk files, sorted by filename
    # They correspond 1-to-1 in sorted order
    json_files = sorted(json_dir.glob("author_chunk_*.json"))
    fbs_files = sorted(fbs_dir.glob("author_chunk_*.fbs"))
    if not json_files:
        print(f"⚠️ No author chunks found in {json_dir}")
        return False
    if len(json_files) != len(fbs_files):
        print(f"⚠️ Mismatch: {len(json_files)} JSON files vs {len(fbs_files)} FBS files")
        return False
    print(f"📁 Found {len(json_files)} chunk files in both directories")
    # Build chunks metadata by pairing v1 and v2 files in sorted order
    chunks = []
    total_authors = 0
    for i, (json_file, fbs_file) in enumerate(zip(json_files, fbs_files)):
        try:
            # Get the chunk index from v2 FBS filename (sequential: 0000, 0001, ...)
            chunk_idx = int(fbs_file.stem.split("_")[-1])
            # Get author count from v1 JSON file
            author_count = 1  # Default
            try:
                with open(json_file, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    if isinstance(data, list):
                        author_count = len(data)
                    elif isinstance(data, dict):
                        # Single author object
                        author_count = 1
            except Exception as e:
                print(f"   Warning: Could not read {json_file}: {e}")
            chunks.append({
                "index": chunk_idx,
                "filename": fbs_file.name,
                "authorCount": author_count
            })
            total_authors += author_count
        except ValueError as e:
            print(f"   Error parsing filenames: {e}")
            continue
    # Sort by chunk index
    chunks.sort(key=lambda x: x["index"])
    # Build metadata
    meta = {
        "total": len(chunks),
        "totalAuthors": total_authors,
        "chunks": chunks,
        "format": "flatbuffers",
        "version": "v2",
        "generatedAt": datetime.now().isoformat()
    }
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    # Write metadata file
    output_file = output_dir / "authors-meta.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"✅ Generated authors metadata v2: {output_file}")
    print(f"   Total chunks: {meta['total']}")
    print(f"   Total authors: {meta['totalAuthors']}")
    print(f"   Format: {meta['format']}")
    print(f"   First: {chunks[0]['filename']} ({chunks[0]['authorCount']} authors)")
    print(f"   Last: {chunks[-1]['filename']} ({chunks[-1]['authorCount']} authors)")
    return True
if __name__ == "__main__":
    success = generate_authors_meta_v2()
    exit(0 if success else 1)
