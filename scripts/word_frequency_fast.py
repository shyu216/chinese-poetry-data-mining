"""
快速词频统计脚本 - 直接读取已存在的 words 字段

功能:
1. 读取 results/preprocessed/poems_chunk_*.csv 文件中的 words 字段
2. 直接构建关键词到诗 id 的映射索引（跳过分词步骤）

重要说明:
- 使用诗词的 UUID (id 字段) 而非 hash 字段作为索引键
- 原因: author 数据和前端查询都使用 UUID，使用 hash 会导致无法关联
- 必须与 author_sim_v1.py 保持一致，使用 poem_id = row.get('id', '')

输入:
- results/preprocessed/poems_chunk_*.csv (必须包含 words 字段)

输出:
- results/keyword_index/keyword_*.json (关键词索引文件)
- results/keyword_index/metadata.json (元数据)

命令行:
============================================================
完成!
  总记录数: {total_poems}
  总chunk数: {total_chunks}
  关键词数量: {keyword_count}
  索引chunk数: {index_chunks}
  输出目录: results\keyword_index
============================================================
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set
from datetime import datetime


def load_chunk_words(chunk_path: Path) -> List[Dict[str, str]]:
    """加载单个chunk文件，只读取 id 和 words 字段
    
    注意: 使用 id (UUID) 而非 hash，以与 author 数据和前端查询保持一致
    """
    poems = []
    with open(chunk_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            poems.append({
                'id': row.get('id', ''),  # 使用 UUID，与 author_sim_v1.py 保持一致
                'words': row.get('words', '')
            })
    return poems


def build_keyword_index(all_poems: List[Dict[str, str]]) -> Dict[str, Set[str]]:
    """构建关键词到诗 id 的索引
    
    注意: 使用 id (UUID) 作为索引键，以与 author 数据和前端查询保持一致
    """
    keyword_index = defaultdict(set)
    
    for poem in all_poems:
        poem_id = poem.get('id', '')  # 使用 UUID，与 author_sim_v1.py 保持一致
        if not poem_id:
            continue
        
        words_str = poem.get('words', '')
        if words_str:
            words = words_str.split()
            for word in words:
                if word:  # 跳过空字符串
                    keyword_index[word].add(poem_id)
    
    return keyword_index


def save_keyword_index(keyword_index: Dict[str, Set[str]], output_dir: Path, chunk_size: int = 1000):
    """保存关键词索引"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 清理旧的索引文件，避免重复或冲突
    for old_file in output_dir.glob("keyword_*.json"):
        old_file.unlink()
    
    keywords = sorted(keyword_index.keys())
    total_chunks = (len(keywords) + chunk_size - 1) // chunk_size
    
    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min((chunk_idx + 1) * chunk_size, len(keywords))
        chunk_keywords = keywords[start_idx:end_idx]
        
        chunk_data = {}
        for keyword in chunk_keywords:
            chunk_data[keyword] = sorted(list(keyword_index[keyword]))
        
        chunk_file = output_dir / f"keyword_{chunk_idx:04d}.json"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        if (chunk_idx + 1) % 10 == 0 or chunk_idx == total_chunks - 1:
            print(f"  [{chunk_idx+1}/{total_chunks}] 保存关键词索引 chunk {chunk_idx}: {len(chunk_keywords)} 个关键词 -> {chunk_file}")
    
    return total_chunks


def save_metadata(output_dir: Path, total_poems: int, total_chunks: int, keyword_count: int, index_chunks: int):
    """保存元数据"""
    metadata = {
        "version": "v1",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_poems": total_poems,
            "total_chunks": total_chunks,
            "total_keywords": keyword_count,
            "index_chunks": index_chunks
        }
    }
    
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def main():
    input_dir = Path("results/preprocessed")
    output_dir = Path("results/keyword_index")
    
    print("=" * 60)
    print("快速词频统计脚本启动 (跳过 jieba 分词)")
    print("=" * 60)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    
    chunk_files = sorted(input_dir.glob("poems_chunk_*.csv"))
    print(f"找到 {len(chunk_files)} 个chunk文件")
    
    if not chunk_files:
        print("错误: 未找到chunk文件")
        return
    
    all_poems = []
    total_processed = 0
    empty_words_count = 0
    
    print("\n" + "=" * 60)
    print("读取 words 字段")
    print("=" * 60)
    
    for idx, chunk_file in enumerate(chunk_files, 1):
        poems = load_chunk_words(chunk_file)
        
        # 统计空 words 的记录
        for poem in poems:
            if not poem.get('words', '').strip():
                empty_words_count += 1
        
        all_poems.extend(poems)
        total_processed += len(poems)
        
        if idx % 10 == 0 or idx == len(chunk_files):
            print(f"  [{idx}/{len(chunk_files)}] 已读取: {total_processed} 条记录")
    
    print(f"\n>>> 读取完成!")
    print(f"  总记录数: {total_processed}")
    print(f"  空 words 记录: {empty_words_count}")
    
    print("\n" + "=" * 60)
    print("构建关键词索引")
    print("=" * 60)
    
    keyword_index = build_keyword_index(all_poems)
    print(f"  关键词数量: {len(keyword_index)}")
    
    print("\n保存关键词索引...")
    index_chunks = save_keyword_index(keyword_index, output_dir, chunk_size=1000)
    
    print("\n保存元数据...")
    save_metadata(output_dir, total_processed, len(chunk_files), len(keyword_index), index_chunks)
    
    print("\n" + "=" * 60)
    print("完成!")
    print(f"  总记录数: {total_processed}")
    print(f"  总chunk数: {len(chunk_files)}")
    print(f"  关键词数量: {len(keyword_index)}")
    print(f"  索引chunk数: {index_chunks}")
    print(f"  输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
