"""
Bronze层清洗脚本

功能:
1. 加载 chinese-poetry submodule 数据
2. 统一诗/词/曲字段名
3. 繁简转换
4. 去重

输入:
- data/chinese-poetry/ (原始数据)

输出:
- results/bronze/poems_chunk_*.csv (分块文件)
- results/bronze/poems_chunk_metadata.json (元数据)
- results/bronze/poems_chunk_state.json (状态文件)
- data/bronze/v1_metadata.json (管线元数据)
"""

import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.schema import PoemRaw, PipelineMetadata, PipelineStep
from src.config import get_settings
from src.chunk import AdvancedChunkManager, create_chunk_manager


def load_poem_files(raw_dir: Path) -> List[Dict[str, Any]]:
    """加载所有诗词JSON文件"""
    print(f"\n>>> 开始加载诗词文件...")
    print(f"原始数据目录: {raw_dir}")
    
    poems = []
    source_files = []
    
    # chinese-poetry 数据格式 (JSON数组)
    poetry_dir = raw_dir / "chinese-poetry"
    print(f"chinese-poetry目录: {poetry_dir}")
    print(f"目录存在: {poetry_dir.exists()}")
    
    if poetry_dir.exists():
        # 加载全唐诗
        print(f"\n>>> 检查全唐诗目录...")
        tangshi_dir = poetry_dir / "全唐诗"
        print(f"全唐诗目录: {tangshi_dir}")
        print(f"目录存在: {tangshi_dir.exists()}")
        
        if tangshi_dir.exists():
            tangshi_files = sorted(tangshi_dir.glob("*.json"))
            print(f"找到 {len(tangshi_files)} 个全唐诗文件")
            
            for idx, file in enumerate(tangshi_files, 1):
                print(f"\n  [{idx}/{len(tangshi_files)}] 处理文件: {file.name}")
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        print(f"    读取到 {len(items)} 条记录")
                        
                        for item in items:
                            item["_source_type"] = "tangshi"
                            item["_source_file"] = str(file)
                            poems.append(item)
                        
                        source_files.append(str(file))
                        print(f"    累计诗词: {len(poems)} 首")
                        print(f"    累计文件: {len(source_files)} 个")
                except Exception as e:
                    print(f"    错误: 无法读取 {file}: {e}")
        
        # 加载宋词
        print(f"\n>>> 检查宋词目录...")
        songci_dir = poetry_dir / "宋词"
        print(f"宋词目录: {songci_dir}")
        print(f"目录存在: {songci_dir.exists()}")
        
        if songci_dir.exists():
            songci_files = sorted(songci_dir.glob("*.json"))
            print(f"找到 {len(songci_files)} 个宋词文件")
            
            for idx, file in enumerate(songci_files, 1):
                print(f"\n  [{idx}/{len(songci_files)}] 处理文件: {file.name}")
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        items = json.load(f)
                        print(f"    读取到 {len(items)} 条记录")
                        
                        for item in items:
                            item["_source_type"] = "songci"
                            item["_source_file"] = str(file)
                            poems.append(item)
                        
                        source_files.append(str(file))
                        print(f"    累计诗词: {len(poems)} 首")
                        print(f"    累计文件: {len(source_files)} 个")
                except Exception as e:
                    print(f"    错误: 无法读取 {file}: {e}")
    
    print(f"\n>>> 加载完成!")
    print(f"  总诗词数: {len(poems)} 首")
    print(f"  来源文件: {len(source_files)} 个")
    
    return poems, source_files


def unify_schema(raw_poems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """统一诗/词/曲的数据结构"""
    print(f"\n>>> 开始统一数据结构...")
    print(f"输入诗词数: {len(raw_poems)} 首")
    
    unified = []
    
    for idx, item in enumerate(raw_poems, 1):
        if idx % 10000 == 0:
            print(f"  处理进度: {idx}/{len(raw_poems)} ({idx/len(raw_poems)*100:.1f}%)")
        
        # 提取基础字段
        unified_item = {
            "id": item.get("_id", {}).get("$oid", item.get("id", "")),
            "title": item.get("title", item.get("rhythmic", "")),
            "author": item.get("writer", item.get("author", "佚名")),
            "dynasty": item.get("dynasty", "其他"),
            "genre": _get_genre(item.get("_source_type", "")),
            "paragraphs": [],
            "content": item.get("content", ""),
            "content_simplified": "",
            "source_file": item.get("_source_file", ""),
            "source_type": item.get("_source_type", ""),
            "hash": "",
        }
        
        # 处理 chinese-poetry 格式
        if "paragraphs" in item and isinstance(item["paragraphs"], list):
            unified_item["paragraphs"] = [p.strip() for p in item["paragraphs"] if p.strip()]
            unified_item["content"] = "\n".join(unified_item["paragraphs"])
        elif unified_item["content"]:
            unified_item["paragraphs"] = [p.strip() for p in unified_item["content"].split("\n") if p.strip()]
        
        # 计算hash（用于去重）
        hash_content = f"{unified_item['title']}_{unified_item['author']}_{unified_item['content']}"
        unified_item["hash"] = hashlib.md5(hash_content.encode("utf-8")).hexdigest()
        
        unified.append(unified_item)
    
    print(f"统一完成: {len(unified)} 首诗词")
    
    return unified


def _get_genre(source_type: str) -> str:
    """根据来源类型判断体裁"""
    if "tangshi" in source_type:
        return "诗"
    elif "songci" in source_type:
        return "词"
    elif "yuanqu" in source_type:
        return "曲"
    elif "yuding" in source_type:
        return "诗"
    elif "poet" in source_type:
        return "诗"
    elif "ci" in source_type:
        return "词"
    elif "qu" in source_type:
        return "曲"
    return "其他"


def remove_duplicates(poems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """基于hash去重"""
    print(f"\n>>> 开始去重...")
    print(f"输入诗词数: {len(poems)} 首")
    
    seen_hashes = set()
    unique_poems = []
    
    for idx, poem in enumerate(poems, 1):
        if idx % 10000 == 0:
            print(f"  去重进度: {idx}/{len(poems)} ({idx/len(poems)*100:.1f}%)")
            print(f"  已去重: {len(unique_poems)} 首")
        
        if poem["hash"] not in seen_hashes:
            seen_hashes.add(poem["hash"])
            unique_poems.append(poem)
    
    print(f"\n>>> 去重完成!")
    print(f"  去重前: {len(poems)} 首")
    print(f"  去重后: {len(unique_poems)} 首")
    print(f"  重复数: {len(poems) - len(unique_poems)} 首")
    print(f"  去重率: {(len(poems) - len(unique_poems))/len(poems)*100:.2f}%")
    
    return unique_poems


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
        "--force",
        action="store_true",
        help="强制重新生成"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("Bronze层数据清洗脚本启动")
    print("=" * 60)
    print(f"参数: force={args.force}")
    
    settings = get_settings()
    
    # 路径
    raw_dir = settings.data.raw_dir
    bronze_dir = settings.data.bronze_dir
    
    print(f"\n>>> 配置信息:")
    print(f"  原始数据目录: {raw_dir}")
    print(f"  Bronze目录: {bronze_dir}")
    print(f"  项目根目录: {Path(__file__).parent.parent.parent}")
    
    output_metadata = bronze_dir / "v1_metadata.json"
    
    # 创建chunk管理器
    print(f"\n>>> 创建chunk管理器...")
    chunk_manager = create_chunk_manager(
        data_type="bronze",
        prefix="poems_chunk",
        step_name="clean"
    )
    print(f"  Chunk基础目录: {chunk_manager.base_dir}")
    print(f"  Chunk前缀: {chunk_manager.prefix}")
    print(f"  Chunk大小: {chunk_manager.chunk_size}")
    print(f"  状态文件: {chunk_manager.state_file}")
    
    # 检查是否已存在
    print(f"\n>>> 检查现有数据...")
    existing_chunks = chunk_manager.get_chunk_count()
    print(f"  现有chunk数: {existing_chunks}")
    
    if not args.force and existing_chunks > 0:
        progress = chunk_manager.get_progress()
        print(f"\n>>> 已存在处理进度:")
        print(f"  总chunk数: {progress['total_chunks']}")
        print(f"  已完成: {progress['completed_chunks']}")
        print(f"  进度: {progress['progress_percent']:.1f}%")
        print(f"  使用 --force 重新生成")
        return
    
    if args.force:
        print(f"\n>>> 清理现有数据...")
        chunk_manager.clear_chunks()
        print(f"  清理完成")
    
    print("\n" + "=" * 60)
    print("Bronze层数据清洗")
    print("=" * 60)
    
    # 1. 加载数据
    print("\n[1/4] 加载原始数据...")
    poems, source_files = load_poem_files(raw_dir)
    
    # 2. 统一Schema
    print("\n[2/4] 统一数据结构...")
    unified_poems = unify_schema(poems)
    
    # 3. 去重
    print("\n[3/4] 去重...")
    unique_poems = remove_duplicates(unified_poems)
    
    # 4. 保存数据（使用chunk）
    print("\n[4/4] 保存数据...")
    print(f"  创建DataFrame...")
    df = pd.DataFrame(unique_poems)
    print(f"  DataFrame形状: {df.shape}")
    print(f"  DataFrame列: {list(df.columns)}")
    
    print(f"  开始分块保存...")
    chunk_manager.split_to_chunks(df, output_format="csv")
    
    # 5. 保存元数据
    print(f"\n>>> 保存元数据...")
    print(f"  元数据路径: {output_metadata}")
    save_metadata(
        output_metadata,
        source_files,
        len(unique_poems),
        {"force": args.force}
    )
    
    print("\n" + "=" * 60)
    print("完成!")
    print(f"  总记录: {len(unique_poems)}")
    print(f"  分块数量: {chunk_manager.get_chunk_count()}")
    print(f"  状态文件: {chunk_manager.state_file}")
    print(f"  元数据文件: {output_metadata}")
    print("=" * 60)


if __name__ == "__main__":
    main()
