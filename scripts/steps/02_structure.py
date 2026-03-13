"""
Silver层结构化处理脚本

功能:
1. 解析诗句结构
2. 提取格律模式
3. 判断是否为格律诗
4. 分类诗体类型

输出:
- data/silver/v2_poems_structured.csv
- data/silver/v2_metadata.json
- data/silver/v2_stats.json
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import Counter

import pandas as pd

from src.schema import PoemProcessed, PipelineMetadata, PipelineStep
from src.config import get_settings


def clean_text(text: str) -> str:
    """清理文本，去除标点"""
    # 保留中文字符和换行
    cleaned = re.sub(r'[^\u4e00-\u9fa5\n]', '', text)
    return cleaned


def split_lines(content: str) -> List[str]:
    """将内容分割为诗句"""
    # 按换行分割
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
        # 词和曲不做格律判断
        return False, "其他", None
    
    # 解析模式
    counts = [int(x) for x in pattern.split(',') if x.isdigit()]
    
    if not counts:
        return False, "其他", None
    
    # 判断是否为格律诗
    # 绝句: 4句，每句5或7字
    # 律诗: 8句，每句5或7字
    
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
    
    # 混合字数，非格律诗
    return False, "杂言", None


def process_poem(row: pd.Series) -> Dict[str, Any]:
    """处理单首诗词"""
    content = row.get('content', '')
    genre = row.get('genre', '其他')
    
    # 清理文本
    cleaned_content = clean_text(content)
    
    # 分割诗句
    lines = split_lines(cleaned_content)
    
    # 分析格律
    pattern, line_char_counts, total_lines, total_chars = analyze_meter_pattern(lines)
    
    # 分类诗体
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


def calculate_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """计算统计信息"""
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
    
    # 作者统计
    author_stats = df.groupby('author').agg({
        'id': 'count',
        'genre': lambda x: x.value_counts().to_dict(),
        'total_lines': 'mean',
        'total_chars': 'mean',
    }).reset_index()
    author_stats.columns = ['author', 'poem_count', 'genre_distribution', 'avg_lines', 'avg_chars']
    
    stats['top_authors'] = author_stats.nlargest(20, 'poem_count')[['author', 'poem_count']].to_dict('records')
    
    return stats


def save_to_csv(df: pd.DataFrame, output_path: Path):
    """保存为CSV"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"保存: {output_path}")


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
    bronze_dir = settings.data.bronze_dir
    silver_dir = settings.data.silver_dir
    
    # 输入文件
    if args.data == "sample":
        input_csv = bronze_dir / "v1_sample_1000.csv"
    else:
        input_csv = bronze_dir / "v1_poems_merged.csv"
    
    output_csv = silver_dir / "v2_poems_structured.csv"
    output_stats = silver_dir / "v2_stats.json"
    output_metadata = silver_dir / "v2_metadata.json"
    
    # 检查输入是否存在
    if not input_csv.exists():
        print(f"错误: 输入文件不存在 {input_csv}")
        print("请先运行: python scripts/steps/01_clean.py")
        return
    
    # 检查是否已存在
    if not args.force and output_csv.exists():
        print(f"已存在: {output_csv}，使用 --force 重新生成")
        return
    
    print("=" * 50)
    print("Silver层结构化处理")
    print("=" * 50)
    
    # 1. 加载数据
    print(f"\n[1/3] 加载数据: {input_csv}")
    df = pd.read_csv(input_csv)
    print(f"加载: {len(df)} 首诗词")
    
    # 2. 结构化处理
    print("\n[2/3] 结构化处理...")
    processed = []
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  处理: {idx}/{len(df)}")
        processed.append(process_poem(row))
    
    df_processed = pd.DataFrame(processed)
    print(f"完成: {len(df_processed)} 首")
    
    # 3. 保存数据
    print("\n[3/3] 保存数据...")
    save_to_csv(df_processed, output_csv)
    
    # 4. 计算统计
    stats = calculate_stats(df_processed)
    save_stats(stats, output_stats)
    
    # 5. 保存元数据
    save_metadata(
        output_metadata,
        input_version="v1",
        output_version="v2",
        total_records=len(df_processed),
        params={"data": args.data, "force": args.force}
    )
    
    print("\n" + "=" * 50)
    print("完成!")
    print(f"总记录: {len(df_processed)}")
    print(f"格律诗比例: {stats['regular_ratio']:.2%}")
    print("=" * 50)


if __name__ == "__main__":
    main()
