"""
Bronze层清洗脚本

功能:
1. 加载 chinese-poetry submodule 数据
2. 统一诗/词/曲字段名
3. 繁简转换
4. 去重
5. 生成采样数据

输出:
- data/bronze/v1_poems_merged.csv
- data/bronze/v1_sample_1000.csv
- data/bronze/v1_metadata.json
"""

import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd

from src.schema import PoemRaw, PipelineMetadata, PipelineStep
from src.config import get_settings


def load_poem_files(raw_dir: Path) -> List[Dict[str, Any]]:
    """加载所有诗词JSON文件"""
    poems = []
    source_files = []
    
    # 全唐诗
    tang_dir = raw_dir / "chinese-poetry" / "poet.tang"
    if tang_dir.exists():
        for file in sorted(tang_dir.glob("*.json")):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    item["_source_type"] = "poet.tang"
                    item["_dynasty"] = "唐代"
                    item["_source_file"] = str(file)
                poems.extend(data)
                source_files.append(str(file))
    
    # 全宋诗
    song_dir = raw_dir / "chinese-poetry" / "poet.song"
    if song_dir.exists():
        for file in sorted(song_dir.glob("*.json")):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    item["_source_type"] = "poet.song"
                    item["_dynasty"] = "宋代"
                    item["_source_file"] = str(file)
                poems.extend(data)
                source_files.append(str(file))
    
    # 宋词
    ci_dir = raw_dir / "chinese-poetry" / "ci"
    if ci_dir.exists():
        for file in sorted(ci_dir.glob("*.json")):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    item["_source_type"] = "ci"
                    item["_dynasty"] = "宋代"
                    item["_source_file"] = str(file)
                poems.extend(data)
                source_files.append(str(file))
    
    print(f"加载完成: {len(poems)} 首诗词")
    print(f"来源文件: {len(source_files)} 个")
    
    return poems, source_files


def unify_schema(raw_poems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """统一诗/词/曲的数据结构"""
    unified = []
    
    for item in raw_poems:
        # 提取基础字段
        unified_item = {
            "id": item.get("id", ""),
            "title": item.get("title", item.get("rhythmic", "")),
            "author": item.get("author", "佚名"),
            "dynasty": item.get("_dynasty", "其他"),
            "genre": _get_genre(item.get("_source_type", "")),
            "paragraphs": item.get("paragraphs", []),
            "content": "",
            "content_simplified": "",
            "source_file": item.get("_source_file", ""),
            "source_type": item.get("_source_type", ""),
            "hash": "",
        }
        
        # 拼接内容
        if unified_item["paragraphs"]:
            unified_item["content"] = "\n".join(unified_item["paragraphs"])
        
        # 计算hash（用于去重）
        hash_content = f"{unified_item['title']}_{unified_item['author']}_{unified_item['content']}"
        unified_item["hash"] = hashlib.md5(hash_content.encode("utf-8")).hexdigest()
        
        unified.append(unified_item)
    
    return unified


def _get_genre(source_type: str) -> str:
    """根据来源类型判断体裁"""
    if "poet" in source_type:
        return "诗"
    elif "ci" in source_type:
        return "词"
    elif "qu" in source_type:
        return "曲"
    return "其他"


def remove_duplicates(poems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """基于hash去重"""
    seen_hashes = set()
    unique_poems = []
    
    for poem in poems:
        if poem["hash"] not in seen_hashes:
            seen_hashes.add(poem["hash"])
            unique_poems.append(poem)
    
    print(f"去重前: {len(poems)} 首")
    print(f"去重后: {len(unique_poems)} 首")
    print(f"重复: {len(poems) - len(unique_poems)} 首")
    
    return unique_poems


def create_sample(poems: List[Dict[str, Any]], sample_ratio: float = 0.001) -> List[Dict[str, Any]]:
    """创建采样数据"""
    import random
    
    sample_size = max(1000, int(len(poems) * sample_ratio))
    sample = random.sample(poems, min(sample_size, len(poems)))
    
    print(f"采样: {len(sample)} 首 (比例 {sample_ratio})")
    
    return sample


def save_to_csv(poems: List[Dict[str, Any]], output_path: Path):
    """保存为CSV"""
    df = pd.DataFrame(poems)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"保存: {output_path}")


def save_metadata(
    metadata_path: Path,
    source_files: List[str],
    total_records: int,
    params: Dict[str, Any]
):
    """保存元数据"""
    metadata = PipelineMetadata(
        version="v1",
        steps=[
            PipelineStep(
                name="clean",
                input_version="raw",
                output_version="v1",
                timestamp=datetime.now().isoformat(),
                params=params,
                record_count=total_records
            )
        ],
        total_records=total_records,
        source_files=source_files,
        params=params
    )
    
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(metadata.model_dump_json(indent=2))
    print(f"保存: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description="Bronze层数据清洗")
    parser.add_argument(
        "--data",
        choices=["sample", "full"],
        default="sample",
        help="处理数据集类型"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成"
    )
    args = parser.parse_args()
    
    settings = get_settings()
    
    # 路径
    raw_dir = settings.data.raw_dir
    bronze_dir = settings.data.bronze_dir
    
    output_csv = bronze_dir / "v1_poems_merged.csv"
    output_sample = bronze_dir / "v1_sample_1000.csv"
    output_metadata = bronze_dir / "v1_metadata.json"
    
    # 检查是否已存在
    if not args.force and output_csv.exists():
        print(f"已存在: {output_csv}，使用 --force 重新生成")
        return
    
    print("=" * 50)
    print("Bronze层数据清洗")
    print("=" * 50)
    
    # 1. 加载数据
    print("\n[1/4] 加载原始数据...")
    poems, source_files = load_poem_files(raw_dir)
    
    # 2. 统一Schema
    print("\n[2/4] 统一数据结构...")
    unified_poems = unify_schema(poems)
    
    # 3. 去重
    print("\n[3/4] 去重...")
    unique_poems = remove_duplicates(unified_poems)
    
    # 4. 保存完整数据
    print("\n[4/4] 保存数据...")
    save_to_csv(unique_poems, output_csv)
    
    # 5. 生成采样数据
    if args.data == "sample":
        sample_poems = create_sample(unique_poems, settings.data.sample_ratio)
        save_to_csv(sample_poems, output_sample)
    
    # 6. 保存元数据
    save_metadata(
        output_metadata,
        source_files,
        len(unique_poems),
        {"data": args.data, "force": args.force}
    )
    
    print("\n" + "=" * 50)
    print("完成!")
    print(f"总记录: {len(unique_poems)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
