#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格律鉴定工具脚本（优化版）
支持 sample/full 数据切换、结果缓存、使用更精确的韵律分析
"""

import sys
import argparse
import json
import hashlib
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from tqdm import tqdm

from src.models.poetry_classifier import identify_form
from src.features.rhyme_features import get_tone_pattern, RhymeFeatureExtractor


def get_cache_path(data_path: Path, suffix: str = "") -> Path:
    """生成缓存文件路径"""
    data_hash = hashlib.md5(str(data_path).encode()).hexdigest()[:8]
    cache_dir = Path(__file__).parent.parent / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"meter_{data_hash}{suffix}.json"


def load_cached_analysis(cache_path: Path, override: bool = False) -> Optional[Dict]:
    """加载缓存的分析结果"""
    if override or not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            print(f"加载缓存: {cache_path}")
            return json.load(f)
    except Exception as e:
        print(f"缓存加载失败: {e}")
        return None


def save_cached_analysis(cache_path: Path, data: Dict):
    """保存分析结果到缓存"""
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"缓存已保存: {cache_path}")
    except Exception as e:
        print(f"缓存保存失败: {e}")


def load_data(data_type: str = 'sample') -> pd.DataFrame:
    """加载数据"""
    project_root = Path(__file__).parent.parent
    
    if data_type == 'sample':
        data_path = project_root / "data" / "sample_data" / "all_poetry.pkl"
    else:
        data_path = project_root / "data" / "processed_data" / "all_poetry.pkl"
    
    if not data_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {data_path}")
    
    print(f"加载数据: {data_path}")
    df = pd.read_pickle(data_path)
    print(f"共 {len(df)} 首诗")
    
    return df


def analyze_meter_batch(df: pd.DataFrame, use_advanced: bool = True) -> Dict:
    """
    批量分析格律（支持高级分析）
    
    Args:
        df: 诗词DataFrame
        use_advanced: 是否使用高级韵律分析
        
    Returns:
        格律分析结果
    """
    print("分析诗词格律...")
    
    extractor = RhymeFeatureExtractor() if use_advanced else None
    
    results = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="格律分析"):
        content = row.get('content', '')
        if not content:
            continue
        
        # 基础分析
        form = identify_form(content)
        tone_patterns = get_tone_pattern(content)
        
        result = {
            'title': row.get('title', ''),
            'author': row.get('author', ''),
            'dynasty': row.get('dynasty', ''),
            'form': form,
            'tone_patterns': tone_patterns
        }
        
        # 高级韵律分析
        if use_advanced and extractor:
            try:
                from src.core.text_utils import normalize_poem_lines
                lines = normalize_poem_lines(content)
                rhythm_features = extractor.extract_rhythm_features(lines)
                
                result['rhythm'] = {
                    'line_count': rhythm_features.get('line_count', 0),
                    'rhyme_scheme': rhythm_features.get('rhyme_scheme', ''),
                    'alliteration_count': rhythm_features.get('alliteration_count', 0),
                    'assonance_count': rhythm_features.get('assonance_count', 0)
                }
            except Exception as e:
                pass
        
        results.append(result)
    
    # 统计诗体分布
    form_counts = Counter(r['form'] for r in results)
    
    # 统计平仄比例
    level_count = 0
    oblique_count = 0
    for r in results:
        for pattern in r.get('tone_patterns', []):
            level_count += pattern.count('平')
            oblique_count += pattern.count('仄')
    
    total_tones = level_count + oblique_count
    tone_ratio = {
        'level': level_count / total_tones if total_tones > 0 else 0,
        'oblique': oblique_count / total_tones if total_tones > 0 else 0
    }
    
    # 按作者统计
    author_forms = {}
    for r in results:
        author = r['author']
        if author not in author_forms:
            author_forms[author] = Counter()
        author_forms[author][r['form']] += 1
    
    # 找出每位作者最擅长的诗体
    author_specialty = {}
    for author, forms in author_forms.items():
        if sum(forms.values()) >= 2:  # 至少2首诗
            specialty = forms.most_common(1)[0]
            author_specialty[author] = {
                'specialty': specialty[0],
                'count': specialty[1],
                'total': sum(forms.values())
            }
    
    return {
        'total': len(results),
        'form_distribution': dict(form_counts),
        'tone_ratio': tone_ratio,
        'author_specialty': author_specialty,
        'details': results
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='诗词格律鉴定')
    parser.add_argument('--data', choices=['sample', 'full'], default='sample',
                       help='使用 sample 或 full 数据 (默认: sample)')
    parser.add_argument('--override', action='store_true',
                       help='覆盖已有缓存')
    parser.add_argument('--advanced', action='store_true', default=True,
                       help='使用高级韵律分析 (默认: True)')
    parser.add_argument('--no-advanced', dest='advanced', action='store_false',
                       help='禁用高级韵律分析')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("诗词格律鉴定")
    print(f"数据类型: {args.data}")
    print(f"高级分析: {args.advanced}")
    print("=" * 60)
    
    # 加载数据
    df = load_data(args.data)
    
    # 生成缓存路径
    data_path = Path(__file__).parent.parent / "data" / f"{args.data}_data" / "all_poetry.pkl"
    cache_path = get_cache_path(data_path)
    
    # 尝试加载缓存
    result = load_cached_analysis(cache_path, args.override)
    
    if not result:
        # 分析格律
        print("\n" + "-" * 60)
        result = analyze_meter_batch(df, use_advanced=args.advanced)
        
        if result:
            save_cached_analysis(cache_path, result)
    
    if result:
        print(f"\n诗体分布:")
        for form, count in result['form_distribution'].items():
            print(f"  {form}: {count}首")
        
        print(f"\n平仄比例:")
        print(f"  平声: {result['tone_ratio']['level']:.1%}")
        print(f"  仄声: {result['tone_ratio']['oblique']:.1%}")
        
        print(f"\n诗人擅长诗体TOP10:")
        top_authors = sorted(
            result['author_specialty'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]
        for author, info in top_authors:
            print(f"  {author}: {info['specialty']} ({info['count']}/{info['total']}首)")
        
        # 保存结果 - 根据数据类型保存到不同子目录
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "reports" / args.data / "meter_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "meter_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n结果已保存到: {output_dir}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
