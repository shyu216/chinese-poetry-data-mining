"""
Silver层结构化处理脚本

功能:
1. 解析诗句结构
2. 提取格律模式
3. 判断是否为格律诗
4. 分类诗体类型

输入:
- results/bronze/poems_chunk_*.csv (分块文件)

输出:
- results/silver/poems_chunk_*.csv (原始分块文件)
- results/silver/poems_chunk_processed_*.csv (处理后分块文件)
- results/silver/poems_chunk_metadata.json (元数据)
- results/silver/poems_chunk_state.json (状态文件)
- data/silver/v2_stats.json (统计信息)
- data/silver/v2_metadata.json (管线元数据)
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import Counter
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.schema import PoemProcessed, PipelineMetadata, PipelineStep
from src.config import get_settings
from src.chunk import AdvancedChunkManager, create_chunk_manager


def clean_text(text: str) -> str:
    """清理文本，去除标点"""
    cleaned = re.sub(r'[^\u4e00-\u9fa5\n]', '', text)
    return cleaned


def split_lines(content: str) -> List[str]:
    """将内容分割为诗句"""
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    return lines


def analyze_meter_pattern(lines: List[str]) -> Tuple[str, List[int], int, int]:
    """分析格律模式
    
    返回:
        pattern: 格律模式，如 "7,7,7,7"
        line_char_counts: 每句字数列表
        total_lines: 总行数
        total_chars: 总字数
    """
    line_char_counts = [len(line) for line in lines]
    total_lines = len(lines)
    total_chars = sum(line_char_counts)
    
    if line_char_counts:
        pattern = ','.join(map(str, line_char_counts))
    else:
        pattern = ""
    
    return pattern, line_char_counts, total_lines, total_chars


def classify_poem_type(pattern: str, genre: str) -> Tuple[bool, str, str]:
    """分类诗体类型
    
    返回:
        is_regular: 是否为格律诗
        poem_type: 诗体类型（如七言绝句）
        meter_category: 格律类别（五言/七言）
    """
    if genre != "诗":
        return False, "其他", None
    
    counts = [int(x) for x in pattern.split(',') if x.isdigit()]
    
    if not counts:
        return False, "其他", None
    
    unique_counts = set(counts)
    
    if len(unique_counts) == 1:
        char_count = list(unique_counts)[0]
        
        if char_count == 5:
            meter_category = "五言"
            if len(counts) == 4:
                return True, "五言绝句", meter_category
            elif len(counts) == 8:
                return True, "五言律诗", meter_category
            else:
                return False, "五言古体", meter_category
        
        elif char_count == 7:
            meter_category = "七言"
            if len(counts) == 4:
                return True, "七言绝句", meter_category
            elif len(counts) == 8:
                return True, "七言律诗", meter_category
            else:
                return False, "七言古体", meter_category
    
    return False, "杂言", None


def process_poem_row(row: pd.Series) -> Dict[str, Any]:
    """处理单首诗词"""
    content = row.get('content', '')
    genre = row.get('genre', '其他')
    
    if not isinstance(content, str):
        content = str(content) if content is not None else ''
    
    cleaned_content = clean_text(content)
    lines = split_lines(cleaned_content)
    pattern, line_char_counts, total_lines, total_chars = analyze_meter_pattern(lines)
    is_regular, poem_type, meter_category = classify_poem_type(pattern, genre)
    
    return {
        'id': row.get('id', ''),
        'title': row.get('title', ''),
        'author': row.get('author', ''),
        'dynasty': row.get('dynasty', ''),
        'genre': genre,
        'poem_type': poem_type,
        'content': content,
        'lines': lines,
        'line_char_counts': line_char_counts,
        'meter_pattern': pattern,
        'total_lines': total_lines,
        'total_chars': total_chars,
        'is_regular': is_regular,
        'meter_category': meter_category,
    }


def process_chunk(df: pd.DataFrame) -> pd.DataFrame:
    """处理一个chunk的数据"""
    print(f"  处理chunk: {len(df)} 条记录")
    processed = []
    for idx, row in df.iterrows():
        if (idx + 1) % 1000 == 0:
            print(f"    进度: {idx+1}/{len(df)}")
        processed.append(process_poem_row(row))
    result_df = pd.DataFrame(processed)
    print(f"  完成处理: {len(result_df)} 条记录")
    return result_df


def calculate_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """计算统计信息"""
    print(f"  计算统计信息...")
    print(f"    总诗词数: {len(df)}")
    print(f"    总作者数: {df['author'].nunique()}")
    print(f"    总朝代数: {df['dynasty'].nunique()}")
    
    stats = {
        'total_poems': len(df),
        'total_authors': df['author'].nunique(),
        'total_dynasties': df['dynasty'].nunique(),
        'genre_distribution': df['genre'].value_counts().to_dict(),
        'poem_type_distribution': df['poem_type'].value_counts().to_dict(),
        'regular_ratio': df['is_regular'].mean(),
        'avg_lines': df['total_lines'].mean(),
        'avg_chars': df['total_chars'].mean(),
    }
    
    print(f"    格律诗比例: {stats['regular_ratio']:.2%}")
    print(f"    平均行数: {stats['avg_lines']:.1f}")
    print(f"    平均字数: {stats['avg_chars']:.1f}")
    
    author_stats = df.groupby('author').agg({
        'id': 'count',
        'genre': lambda x: x.value_counts().to_dict(),
        'total_lines': 'mean',
        'total_chars': 'mean',
    }).reset_index()
    author_stats.columns = ['author', 'poem_count', 'genre_distribution', 'avg_lines', 'avg_chars']
    
    stats['top_authors'] = author_stats.nlargest(20, 'poem_count')[['author', 'poem_count']].to_dict('records')
    print(f"    Top 20作者: {[a['author'] for a in stats['top_authors'][:5]]}...")
    
    return stats


def save_stats(stats: Dict[str, Any], output_path: Path):
    """保存统计信息"""
    import json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"保存: {output_path}")


def save_metadata(
    metadata_path: Path,
    input_version: str,
    output_version: str,
    total_records: int,
    params: Dict[str, Any]
):
    """保存元数据"""
    metadata = PipelineMetadata(
        version=output_version,
        steps=[
            PipelineStep(
                name="structure",
                input_version=input_version,
                output_version=output_version,
                timestamp=datetime.now().isoformat(),
                params=params,
                record_count=total_records
            )
        ],
        total_records=total_records,
        source_files=[],
        params=params
    )
    
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        f.write(metadata.model_dump_json(indent=2))
    print(f"保存: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description="Silver层结构化处理")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("Silver层结构化处理脚本启动")
    print("=" * 60)
    print(f"参数: force={args.force}")
    
    settings = get_settings()
    
    # 路径
    bronze_dir = settings.data.bronze_dir
    silver_dir = settings.data.silver_dir
    
    print(f"\n>>> 配置信息:")
    print(f"  Bronze目录: {bronze_dir}")
    print(f"  Silver目录: {silver_dir}")
    
    output_stats = silver_dir / "v2_stats.json"
    output_metadata = silver_dir / "v2_metadata.json"
    
    # 创建chunk管理器
    print(f"\n>>> 创建Silver层chunk管理器...")
    chunk_manager = create_chunk_manager(
        data_type="silver",
        prefix="poems_chunk",
        step_name="structure"
    )
    print(f"  Silver Chunk基础目录: {chunk_manager.base_dir}")
    print(f"  Chunk前缀: {chunk_manager.prefix}")
    print(f"  Chunk大小: {chunk_manager.chunk_size}")
    
    # 检查是否已存在
    print(f"\n>>> 检查现有Silver层数据...")
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
        print(f"\n>>> 清理现有Silver层数据...")
        chunk_manager.clear_chunks()
        print(f"  清理完成")
    
    print("\n" + "=" * 60)
    print("Silver层结构化处理")
    print("=" * 60)
    
    # 1. 处理数据（使用chunk）
    print("\n[1/3] 处理数据...")
    print(f">>> 创建Bronze层chunk管理器...")
    bronze_chunk_manager = create_chunk_manager(
        data_type="bronze",
        prefix="poems_chunk",
        step_name="clean"
    )
    print(f"  Bronze Chunk基础目录: {bronze_chunk_manager.base_dir}")
    
    bronze_chunk_count = bronze_chunk_manager.get_chunk_count()
    print(f"  Bronze chunk数量: {bronze_chunk_count}")
    
    if bronze_chunk_count == 0:
        print(f"\n错误: 未找到bronze层数据")
        print(f"请先运行: python scripts/steps/01_clean.py")
        return
    
    print(f"\n>>> 开始处理所有chunk...")
    print(f"  总chunk数: {bronze_chunk_count}")
    
    # 使用process_chunks处理所有chunk
    chunk_manager.process_chunks(
        process_func=process_chunk,
        input_path=None,
        input_chunk_manager=bronze_chunk_manager,
        output_format="csv",
        resume=True,
        force=False
    )
    
    # 2. 计算统计
    print("\n[2/3] 计算统计...")
    print(f">>> 加载处理后的数据...")
    all_dfs = []
    chunk_count = chunk_manager.get_chunk_count()
    print(f"  Silver chunk数量: {chunk_count}")
    
    for idx, chunk_df in enumerate(chunk_manager.iter_chunks(processed=True), 1):
        print(f"  加载chunk {idx}/{chunk_count}: {len(chunk_df)} 条记录")
        all_dfs.append(chunk_df)
    
    print(f">>> 合并所有chunk...")
    df = pd.concat(all_dfs, ignore_index=True)
    print(f"  合并完成: {len(df)} 条记录")
    
    print(f"\n>>> 计算统计信息...")
    stats = calculate_stats(df)
    save_stats(stats, output_stats)
    
    # 3. 保存元数据
    print("\n[3/3] 保存元数据...")
    print(f">>> 保存元数据...")
    print(f"  元数据路径: {output_metadata}")
    save_metadata(
        output_metadata,
        input_version="v1",
        output_version="v2",
        total_records=len(df),
        params={"force": args.force}
    )
    
    print("\n" + "=" * 60)
    print("完成!")
    print(f"  总记录: {len(df)}")
    print(f"  格律诗比例: {stats['regular_ratio']:.2%}")
    print(f"  分块数量: {chunk_manager.get_chunk_count()}")
    print(f"  状态文件: {chunk_manager.state_file}")
    print(f"  统计文件: {output_stats}")
    print(f"  元数据文件: {output_metadata}")
    print("=" * 60)


if __name__ == "__main__":
    main()
