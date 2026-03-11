#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格律鉴定工具脚本
使用新的src结构
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from tqdm import tqdm

from src.models.poetry_classifier import identify_form
from src.features.rhyme_features import get_tone_pattern


def identify_meter(content: str) -> str:
    """
    鉴定格律
    
    Args:
        content: 诗词内容
        
    Returns:
        诗体名称
    """
    return identify_form(content)


def analyze_meter_batch(df: pd.DataFrame) -> dict:
    """
    批量分析格律
    
    Args:
        df: 诗词DataFrame
        
    Returns:
        格律分析结果
    """
    print("分析诗词格律...")
    
    results = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="格律分析"):
        content = row.get('content', '')
        if not content:
            continue
        
        form = identify_form(content)
        tone_patterns = get_tone_pattern(content)
        
        results.append({
            'title': row.get('title', ''),
            'author': row.get('author', ''),
            'form': form,
            'tone_patterns': tone_patterns
        })
    
    # 统计诗体分布
    from collections import Counter
    form_counts = Counter(r['form'] for r in results)
    
    return {
        'total': len(results),
        'form_distribution': dict(form_counts),
        'details': results
    }


def main():
    """主函数"""
    print("=" * 60)
    print("诗词格律鉴定")
    print("=" * 60)
    
    # 加载数据
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "sample_data" / "all_poetry.pkl"
    
    print(f"\n加载数据: {data_path}")
    df = pd.read_pickle(data_path)
    print(f"共 {len(df)} 首诗")
    
    # 分析格律
    result = analyze_meter_batch(df)
    
    print(f"\n诗体分布:")
    for form, count in result['form_distribution'].items():
        print(f"  {form}: {count}首")
    
    # 保存结果
    import json
    output_dir = project_root / "reports" / "meter_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "meter_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n结果已保存到: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
