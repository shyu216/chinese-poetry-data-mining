#!/usr/bin/env python3
"""
Generate authors metadata for the web app (v2 - FlatBuffers format).
This script scans the results/author_v2/ directory and creates a JSON file
with metadata about available author chunks in FBS format.

Run this during build time to keep the web app in sync with data.
"""

import json
import os
from pathlib import Path
from datetime import datetime


def generate_authors_meta_v2():
    """Generate metadata for author chunks (v2 FBS format)."""
    # Find the project root (where this script is located)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Path to author chunks v2 (FBS format)
    author_dir = project_root / "results" / "author_v2"
    output_dir = project_root / "web" / "public" / "data" / "author_v2"
    
    if not author_dir.exists():
        print(f"❌ Author v2 directory not found: {author_dir}")
        return False
    
    # Get all chunk files (FBS format)
    chunk_files = sorted(author_dir.glob("author_chunk_*.fbs"))
    
    if not chunk_files:
        print(f"⚠️ No author chunks found in {author_dir}")
        return False
    
    # Extract chunk indices and count authors per chunk
    chunks = []
    total_authors = 0
    
    # Try to get author count from original JSON files
    json_dir = project_root / "results" / "author"
    
    for f in chunk_files:
        # Extract number from filename like "author_chunk_0001.fbs"
        try:
            idx = int(f.stem.split("_")[-1])
            
            # Try to get author count from corresponding JSON file
            author_count = 1  # Default: assume 1 author per chunk
            json_file = json_dir / f"author_chunk_{idx:04d}.json"
            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        if isinstance(data, list):
                            author_count = len(data)
                        elif isinstance(data, dict) and "authors" in data:
                            author_count = len(data["authors"])
                except Exception as e:
                    print(f"   Warning: Could not read {json_file}: {e}")
            
            chunks.append({
                "index": idx,
                "filename": f.name,
                "authorCount": author_count
            })
            total_authors += author_count
            
        except ValueError:
            continue
    
    # Sort by index
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
