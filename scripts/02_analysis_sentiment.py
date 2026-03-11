#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪指纹分析脚本
使用sample data进行情感分析
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from tqdm import tqdm

from src.features.sentiment_features import SentimentFeatureExtractor


def analyze_sentiment_distribution(df: pd.DataFrame) -> dict:
    """
    分析情感分布
    
    Args:
        df: 诗词数据DataFrame
        
    Returns:
        情感分析统计结果
    """
    analyzer = SentimentFeatureExtractor()
    
    print("进行情感分析...")
    results = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="情感分析"):
        content = row.get('content', '')
        if not content:
            continue
        
        result = analyzer.extract_sentiment_features(content)
        results.append({
            'title': row.get('title', ''),
            'author': row.get('author', ''),
            'dynasty': row.get('dynasty', ''),
            'sentiment_score': result['sentiment_score'],
            'sentiment': result['sentiment']
        })
    
    # 统计
    sentiment_counts = Counter(r['sentiment'] for r in results)
    avg_score = np.mean([r['sentiment_score'] for r in results])
    
    # 找出最积极和最消极的诗
    sorted_by_sentiment = sorted(results, key=lambda x: x['sentiment_score'])
    most_negative = sorted_by_sentiment[:5]
    most_positive = sorted_by_sentiment[-5:]
    
    return {
        'total_poems': len(results),
        'sentiment_distribution': dict(sentiment_counts),
        'average_score': float(avg_score),
        'most_positive': most_positive,
        'most_negative': most_negative,
        'all_results': results
    }


def analyze_author_sentiment(df: pd.DataFrame) -> dict:
    """
    分析诗人的情感倾向
    
    Args:
        df: 诗词数据DataFrame
        
    Returns:
        诗人情感分析结果
    """
    analyzer = SentimentFeatureExtractor()
    
    print("分析诗人情感倾向...")
    author_sentiments = {}
    
    # 按作者分组
    for author in df['author'].unique():
        author_df = df[df['author'] == author]
        if len(author_df) < 2:  # 至少2首诗才分析
            continue
        
        scores = []
        for _, row in author_df.iterrows():
            content = row.get('content', '')
            if content:
                result = analyzer.extract_sentiment_features(content)
                scores.append(result['sentiment_score'])
        
        if scores:
            author_sentiments[author] = {
                'poem_count': len(scores),
                'avg_sentiment': float(np.mean(scores)),
                'sentiment_std': float(np.std(scores)),
                'tendency': '积极' if np.mean(scores) > 0.1 else ('消极' if np.mean(scores) < -0.1 else '中性')
            }
    
    # 排序
    sorted_authors = sorted(author_sentiments.items(), 
                           key=lambda x: x[1]['avg_sentiment'], 
                           reverse=True)
    
    return {
        'author_count': len(author_sentiments),
        'most_positive_authors': sorted_authors[:10],
        'most_negative_authors': sorted_authors[-10:],
        'all_authors': author_sentiments
    }


def main():
    """主函数"""
    print("=" * 60)
    print("诗词情感分析")
    print("=" * 60)
    
    # 加载数据
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "sample_data" / "all_poetry.pkl"
    
    print(f"\n加载数据: {data_path}")
    df = pd.read_pickle(data_path)
    print(f"共 {len(df)} 首诗")
    
    # 情感分布分析
    print("\n" + "-" * 60)
    sentiment_result = analyze_sentiment_distribution(df)
    
    print(f"\n情感分布:")
    for sentiment, count in sentiment_result['sentiment_distribution'].items():
        print(f"  {sentiment}: {count}首")
    print(f"平均情感得分: {sentiment_result['average_score']:.3f}")
    
    print(f"\n最积极的5首诗:")
    for poem in sentiment_result['most_positive']:
        print(f"  《{poem['title']}》- {poem['author']}: {poem['sentiment_score']:.3f}")
    
    print(f"\n最消极的5首诗:")
    for poem in sentiment_result['most_negative']:
        print(f"  《{poem['title']}》- {poem['author']}: {poem['sentiment_score']:.3f}")
    
    # 诗人情感倾向分析
    print("\n" + "-" * 60)
    author_result = analyze_author_sentiment(df)
    
    print(f"\n分析了 {author_result['author_count']} 位诗人")
    
    print(f"\n最积极的10位诗人:")
    for author, info in author_result['most_positive_authors']:
        print(f"  {author}: {info['avg_sentiment']:.3f} ({info['poem_count']}首)")
    
    print(f"\n最消极的10位诗人:")
    for author, info in author_result['most_negative_authors']:
        print(f"  {author}: {info['avg_sentiment']:.3f} ({info['poem_count']}首)")
    
    # 保存结果
    import json
    output_dir = project_root / "reports" / "sentiment_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "sentiment_distribution.json", 'w', encoding='utf-8') as f:
        json.dump(sentiment_result, f, ensure_ascii=False, indent=2, default=str)
    
    with open(output_dir / "author_sentiment.json", 'w', encoding='utf-8') as f:
        json.dump(author_result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n结果已保存到: {output_dir}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
