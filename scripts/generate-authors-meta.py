#!/usr/bin/env python3
"""
Generate authors metadata for the web app.
This script scans the results/author/ directory and creates a JSON file
with metadata about available author chunks.

Run this during build time to keep the web app in sync with data.
"""

import json
import os
from pathlib import Path


def generate_authors_meta():
    """Generate metadata for author chunks."""
    # Find the project root (where this script is located)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Path to author chunks
    author_dir = project_root / "results" / "author"
    output_dir = project_root / "web" / "public" / "data" / "author"
    
    if not author_dir.exists():
        print(f"❌ Author directory not found: {author_dir}")
        return False
    
    # Get all chunk files
    chunk_files = sorted(author_dir.glob("author_chunk_*.json"))
    
    if not chunk_files:
        print(f"⚠️ No author chunks found in {author_dir}")
        return False
    
    # Extract chunk indices
    chunks = []
    for f in chunk_files:
        # Extract number from filename like "author_chunk_0001.json"
        try:
            idx = int(f.stem.split("_")[-1])
            chunks.append({
                "index": idx,
                "filename": f.name
            })
        except ValueError:
            continue
    
    # Sort by index
    chunks.sort(key=lambda x: x["index"])
    
    # Build metadata
    meta = {
        "total": len(chunks),
        "chunks": chunks,
        "generated_at": None  # Could add timestamp if needed
    }
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write metadata file
    output_file = output_dir / "authors-meta.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Generated authors metadata: {output_file}")
    print(f"   Total chunks: {meta['total']}")
    print(f"   First: {chunks[0]['filename']}")
    print(f"   Last: {chunks[-1]['filename']}")
    
    return True


if __name__ == "__main__":
    success = generate_authors_meta()
    exit(0 if success else 1)
