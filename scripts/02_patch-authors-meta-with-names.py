#!/usr/bin/env python3
"""
script: 02_patch-authors-meta-with-names.py
stage: P4-检索索引构建 (补丁)
artifact: authors meta v2 (带诗人名字列表)
purpose: 为 authors-meta.json 补充每个 chunk 的诗人名字列表，实现 O(1) 跳转到目标 chunk。
inputs:
- results/author_v2/author_chunk_*.fbs
- results/author_v2/authors-meta.json
outputs:
- results/author_v2/authors-meta.json (更新)
depends_on:
- 02_generate-authors-meta-v2.py
- 02_author_sim_v2.py
develop_date: 2026-04-07
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

# 添加 flatbuffers 生成目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "flatbuffers_generated"))

from AuthorChunk.AuthorChunkFile import AuthorChunkFile


def patch_authors_meta_with_names():
    """为 authors-meta.json 补充诗人名字列表"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 路径
    fbs_dir = project_root / "results" / "author_v2"
    meta_file = fbs_dir / "authors-meta.json"

    if not fbs_dir.exists():
        print(f"❌ Author v2 directory not found: {fbs_dir}")
        return False

    if not meta_file.exists():
        print(f"❌ Metadata file not found: {meta_file}")
        return False

    # 读取现有 metadata
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    print(f"📖 Loaded metadata: {meta['total']} chunks, {meta['totalAuthors']} authors")

    # 检查是否已有 names 字段
    has_names = any("names" in chunk for chunk in meta.get("chunks", []))
    if has_names:
        print("✅ Metadata already has 'names' field, skipping patch")
        return True

    # 获取所有 chunk 文件
    fbs_files = sorted(fbs_dir.glob("author_chunk_*.fbs"))
    print(f"📁 Found {len(fbs_files)} FBS chunk files")

    # 为每个 chunk 添加诗人名字列表
    patched_count = 0
    for fbs_file in fbs_files:
        try:
            chunk_idx = int(fbs_file.stem.split("_")[-1])

            # 读取并解析 FBS 文件
            with open(fbs_file, "rb") as f:
                buf = f.read()

            if not AuthorChunkFile.AuthorChunkFileBufferHasIdentifier(buf, 0):
                print(f"   ⚠️ {fbs_file.name}: Invalid identifier")
                continue

            chunk = AuthorChunkFile.GetRootAs(buf, 0)
            authors_len = chunk.AuthorsLength()

            # 提取诗人名字列表
            names = []
            for i in range(authors_len):
                author = chunk.Authors(i)
                if author:
                    name = author.Author()
                    if name:
                        # FBS 返回的是 bytes，需要解码
                        names.append(name.decode('utf-8') if isinstance(name, bytes) else name)

            # 找到对应的 chunk 元数据并更新
            for chunk_meta in meta["chunks"]:
                if chunk_meta["index"] == chunk_idx:
                    chunk_meta["names"] = names
                    patched_count += 1
                    break

        except Exception as e:
            print(f"   ❌ Error processing {fbs_file.name}: {e}")
            continue

    print(f"✅ Patched {patched_count} chunks with诗人名字列表")

    # 添加补丁元数据
    meta["patchedAt"] = datetime.now().isoformat()
    meta["patchVersion"] = 1

    # 写回 metadata 文件
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"✅ Updated metadata file: {meta_file}")
    return True


if __name__ == "__main__":
    success = patch_authors_meta_with_names()
    exit(0 if success else 1)
