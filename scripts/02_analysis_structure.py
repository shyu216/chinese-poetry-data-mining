#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词结构分析脚本
功能：
1. 清理标点符号
2. 解析诗句结构（如7言、5言等）
3. 提取格律模式（如7,7,7,7）
4. 双格式保存（Pickle + CSV）
5. 支持sample和full数据分阶段测试
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re
import json
import argparse
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter

import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
from src.core.text_utils import TextProcessor


def is_punctuation(char: str) -> bool:
    """使用Unicode类别判断是否为标点符号"""
    if not char:
        return False
    category = unicodedata.category(char)
    return category.startswith('P')


def clean_punctuation(text: str) -> str:
    """
    清理标点符号，只保留中文字符
    使用Unicode标点类别，更robust地处理各种语言标点
    """
    if not isinstance(text, str):
        return ""
    chinese_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
    return ''.join(chinese_chars)


def clean_punctuation_v2(text: str) -> str:
    """
    清理标点符号（备选方案2）
    使用正则表达式匹配Unicode标点范围
    覆盖：中文、英文、日文、韩文、拉丁文等所有标点
    """
    if not isinstance(text, str):
        return ""
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return ''.join(chinese_chars)


def load_data(data_type: str = 'sample') -> tuple:
    """加载数据"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    if data_type == 'sample':
        data_path = data_dir / "sample_data" / "all_poetry.pkl"
    else:
        data_path = data_dir / "processed_data" / "all_poetry.pkl"

    if not data_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {data_path}")

    print(f"加载数据: {data_path}")
    df = pd.read_pickle(data_path)
    print(f"共 {len(df)} 首诗")

    preprocessor = TextProcessor()
    return df, preprocessor


def analyze_line_char_count(line: str) -> int:
    """分析单行诗句的字数（只计算中文字符）"""
    return len(line)


def analyze_poem_structure(row: pd.Series, preprocessor: TextProcessor = None) -> Dict:
    """
    分析单首诗的结构
    使用paragraphs字段（每句是一个 couplet）
    返回：行数、每行字数、句数、押韵情况等
    """
    result = {
        'lines': [],
        'line_char_counts': [],
        'meter_pattern': '',
        'total_lines': 0,
        'total_chars': 0,
        'is_regular': False,
        'regular_meter': '',
    }

    paragraphs = row.get('paragraphs', [])
    if not isinstance(paragraphs, list) or not paragraphs:
        content = row.get('content', '')
        if content:
            if preprocessor:
                content = preprocessor.traditional_to_simplified(content)
            cleaned = clean_punctuation(content)
            if cleaned:
                result['lines'] = [cleaned]
                result['line_char_counts'] = [len(cleaned)]
                result['total_lines'] = 1
                result['total_chars'] = len(cleaned)
        return result

    all_lines = []
    char_counts = []

    for para in paragraphs:
        if preprocessor:
            para = preprocessor.traditional_to_simplified(str(para))
        cleaned_para = clean_punctuation(para)
        if not cleaned_para:
            continue

        half_len = len(cleaned_para) // 2
        line1 = cleaned_para[:half_len]
        line2 = cleaned_para[half_len:]

        if line1:
            all_lines.append(line1)
            char_counts.append(len(line1))
        if line2:
            all_lines.append(line2)
            char_counts.append(len(line2))

    result['lines'] = all_lines
    result['line_char_counts'] = char_counts
    result['total_lines'] = len(all_lines)
    result['total_chars'] = sum(char_counts)

    if char_counts:
        result['meter_pattern'] = ','.join(map(str, char_counts))

        if len(set(char_counts)) == 1 and len(char_counts) >= 2:
            result['is_regular'] = True
            result['regular_meter'] = f"{char_counts[0]}言{len(char_counts)}句"

    return result


def classify_poem_type(meter_pattern: str, genre: str) -> str:
    """根据格律模式和体裁分类诗歌类型"""
    if not meter_pattern:
        return "未知"

    try:
        counts = [int(x) for x in meter_pattern.split(',')]
    except:
        return "其他"

    if genre == "词":
        ci_patterns = {
            (2,): "词",
            (7,): "七言",
            (5,): "五言",
        }
        unique_counts = list(set(counts))
        if len(unique_counts) == 1 and unique_counts[0] in ci_patterns:
            return ci_patterns[tuple(unique_counts)]
        return "词"

    unique_counts = list(set(counts))

    if len(counts) == 4 and len(unique_counts) == 1:
        char_count = counts[0]
        if char_count == 5:
            return "五言绝句"
        elif char_count == 7:
            return "七言绝句"
    elif len(counts) == 8 and len(unique_counts) == 1:
        char_count = counts[0]
        if char_count == 5:
            return "五言律诗"
        elif char_count == 7:
            return "七言律诗"
    elif len(counts) == 6 and len(unique_counts) == 1:
        char_count = counts[0]
        if char_count == 5:
            return "五言六句"
        elif char_count == 7:
            return "七言六句"

    return "其他"


def analyze_poetry_structure(df: pd.DataFrame, preprocessor: TextProcessor = None) -> pd.DataFrame:
    """分析所有诗词的结构"""
    print("\n开始分析诗词结构...")

    results = []
    for idx, row in df.iterrows():
        genre = row.get('genre', '诗')

        structure = analyze_poem_structure(row, preprocessor)

        result = {
            'id': row.get('id', idx),
            'author': row.get('author', ''),
            'title': row.get('title', ''),
            'dynasty': row.get('dynasty', ''),
            'genre': genre,
            'lines': structure['lines'],
            'line_char_counts': structure['line_char_counts'],
            'meter_pattern': structure['meter_pattern'],
            'total_lines': structure['total_lines'],
            'total_chars': structure['total_chars'],
            'is_regular': structure['is_regular'],
            'regular_meter': structure['regular_meter'],
            'poem_type': classify_poem_type(structure['meter_pattern'], genre),
        }
        results.append(result)

    result_df = pd.DataFrame(results)
    print(f"结构分析完成，共处理 {len(result_df)} 首诗")

    return result_df


def generate_structure_statistics(df: pd.DataFrame, name: str = "数据集") -> Dict:
    """生成结构统计信息"""
    print(f"\n{'='*60}")
    print(f"{name}结构统计")
    print(f"{'='*60}")

    stats = {
        'total_poems': len(df),
        'regular_poems': 0,
        'irregular_poems': 0,
        'meter_distribution': {},
        'type_distribution': {},
        'genre_distribution': {},
    }

    if 'is_regular' in df.columns:
        regular_count = df['is_regular'].sum()
        stats['regular_poems'] = int(regular_count)
        stats['irregular_poems'] = len(df) - int(regular_count)
        print(f"\n格律分布:")
        print(f"  规范诗（格律诗）: {regular_count} 首 ({regular_count/len(df)*100:.1f}%)")
        print(f"  不规范诗: {len(df) - regular_count} 首 ({(len(df)-regular_count)/len(df)*100:.1f}%)")

    if 'meter_pattern' in df.columns:
        meter_counts = df['meter_pattern'].value_counts().head(20)
        stats['meter_distribution'] = meter_counts.to_dict()
        print(f"\n格律模式分布 (Top 20):")
        for pattern, count in meter_counts.items():
            print(f"  {pattern}: {count} 首")

    if 'poem_type' in df.columns:
        type_counts = df['poem_type'].value_counts()
        stats['type_distribution'] = type_counts.to_dict()
        print(f"\n诗歌类型分布:")
        for ptype, count in type_counts.items():
            print(f"  {ptype}: {count} 首")

    if 'genre' in df.columns:
        genre_counts = df['genre'].value_counts()
        stats['genre_distribution'] = genre_counts.to_dict()
        print(f"\n体裁分布:")
        for genre, count in genre_counts.items():
            print(f"  {genre}: {count} 首")

    if 'dynasty' in df.columns:
        dynasty_counts = df['dynasty'].value_counts()
        stats['dynasty_distribution'] = dynasty_counts.to_dict()
        print(f"\n朝代分布:")
        for dynasty, count in dynasty_counts.items():
            print(f"  {dynasty}: {count} 首")

    return stats


def save_dual_format(df: pd.DataFrame, output_dir: Path, filename_base: str):
    """双格式保存数据（Pickle + CSV）"""
    output_dir.mkdir(parents=True, exist_ok=True)

    pickle_path = output_dir / f"{filename_base}.pkl"
    df.to_pickle(pickle_path)
    print(f"  ✓ Pickle格式已保存: {pickle_path}")

    df_csv = df.copy()
    if "lines" in df_csv.columns:
        df_csv["lines"] = df_csv["lines"].apply(lambda x: '|'.join(x) if isinstance(x, list) else str(x))
    if "line_char_counts" in df_csv.columns:
        df_csv["line_char_counts"] = df_csv["line_char_counts"].apply(lambda x: ','.join(map(str, x)) if isinstance(x, list) else str(x))

    csv_path = output_dir / f"{filename_base}.csv"
    df_csv.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  ✓ CSV格式已保存: {csv_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='诗词结构分析脚本')
    parser.add_argument('--type', choices=['sample', 'full'], default='sample',
                        help='数据类型: sample(采样数据) 或 full(完整数据)')
    args = parser.parse_args()

    data_type = args.type

    print("="*60)
    print("诗词结构分析脚本")
    print("="*60)
    print(f"数据类型: {data_type}")

    project_root = Path(__file__).parent.parent
    output_dir = project_root / "data" / "structure_analysis"

    df, preprocessor = load_data(data_type)

    result_df = analyze_poetry_structure(df, preprocessor)

    output_name = f"poetry_structure_{data_type}"
    print(f"\n保存 {data_type} 数据...")
    save_dual_format(result_df, output_dir, output_name)

    stats = generate_structure_statistics(result_df, f"{data_type.upper()}数据集")

    stats_path = output_dir / f"statistics_{data_type}.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\n统计信息已保存: {stats_path}")

    print("\n" + "="*60)
    print(f"{data_type.upper()} 数据处理完成！")
    print("="*60)


if __name__ == "__main__":
    main()
