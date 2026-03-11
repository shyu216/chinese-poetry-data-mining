#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪指纹分析脚本（优化版）
支持 sample/full 数据切换、结果缓存、使用 transformers 进行更准确的情感分析
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

# 尝试导入 transformers 进行更准确的情感分析
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("警告: transformers 未安装，使用基础情感分析。安装: pip install transformers")

from src.features.sentiment_features import SentimentFeatureExtractor


class SentimentAnalyzer:
    """情感分析器（支持多种后端）"""
    
    def __init__(self, use_transformers: bool = False):
        """
        初始化分析器
        
        Args:
            use_transformers: 是否使用 transformers 进行更准确的分析
        """
        self.use_transformers = use_transformers and TRANSFORMERS_AVAILABLE
        self.basic_analyzer = SentimentFeatureExtractor()
        
        if self.use_transformers:
            print("加载 transformers 情感分析模型...")
            # 使用中文情感分析模型
            self.transformer_classifier = pipeline(
                "sentiment-analysis",
                model="uer/roberta-base-finetuned-jd-binary-chinese",
                device=-1  # CPU
            )
    
    def analyze(self, text: str) -> Dict:
        """
        分析文本情感
        
        Args:
            text: 文本内容
            
        Returns:
            情感分析结果
        """
        if self.use_transformers and len(text) < 512:  # transformers 有长度限制
            try:
                result = self.transformer_classifier(text[:512])[0]
                # 转换为统一格式
                label = result['label']
                score = result['score']
                
                # 映射到我们的格式
                if label == 'positive':
                    return {
                        'sentiment_score': score,
                        'sentiment': '积极',
                        'confidence': score
                    }
                else:
                    return {
                        'sentiment_score': -score,
                        'sentiment': '消极',
                        'confidence': score
                    }
            except Exception as e:
                # 失败时回退到基础分析
                pass
        
        # 使用基础分析
        result = self.basic_analyzer.extract_sentiment_features(text)
        return {
            'sentiment_score': result['sentiment_score'],
            'sentiment': result['sentiment'],
            'confidence': abs(result['sentiment_score'])
        }


def get_cache_path(data_path: Path, suffix: str = "") -> Path:
    """生成缓存文件路径"""
    # 使用数据文件的哈希作为缓存标识
    data_hash = hashlib.md5(str(data_path).encode()).hexdigest()[:8]
    cache_dir = Path(__file__).parent.parent / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"sentiment_{data_hash}{suffix}.json"


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
    """
    加载数据
    
    Args:
        data_type: 'sample' 或 'full'
        
    Returns:
        DataFrame
    """
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


def analyze_sentiment_distribution(df: pd.DataFrame, analyzer: SentimentAnalyzer, 
                                   cache_path: Optional[Path] = None,
                                   override: bool = False) -> Dict:
    """
    分析情感分布（带缓存）
    
    Args:
        df: 诗词数据
        analyzer: 情感分析器
        cache_path: 缓存文件路径
        override: 是否覆盖缓存
        
    Returns:
        情感分析结果
    """
    # 尝试加载缓存
    if cache_path:
        cached = load_cached_analysis(cache_path, override)
        if cached:
            return cached
    
    print("进行情感分析...")
    results = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="情感分析"):
        content = row.get('content', '')
        if not content:
            continue
        
        result = analyzer.analyze(content)
        results.append({
            'id': row.get('id', idx),
            'title': row.get('title', ''),
            'author': row.get('author', ''),
            'dynasty': row.get('dynasty', ''),
            'sentiment_score': result['sentiment_score'],
            'sentiment': result['sentiment'],
            'confidence': result.get('confidence', 1.0)
        })
    
    # 统计
    sentiment_counts = Counter(r['sentiment'] for r in results)
    avg_score = np.mean([r['sentiment_score'] for r in results])
    
    # 找出最积极和最消极的诗
    sorted_by_sentiment = sorted(results, key=lambda x: x['sentiment_score'])
    most_negative = sorted_by_sentiment[:5]
    most_positive = sorted_by_sentiment[-5:]
    
    result = {
        'total_poems': len(results),
        'sentiment_distribution': dict(sentiment_counts),
        'average_score': float(avg_score),
        'most_positive': most_positive,
        'most_negative': most_negative,
        'all_results': results
    }
    
    # 保存缓存
    if cache_path:
        save_cached_analysis(cache_path, result)
    
    return result


def analyze_author_sentiment(df: pd.DataFrame, sentiment_results: List[Dict]) -> Dict:
    """
    分析诗人的情感倾向（基于已分析结果）
    
    Args:
        df: 原始数据
        sentiment_results: 情感分析结果列表
        
    Returns:
        诗人情感分析结果
    """
    print("分析诗人情感倾向...")
    author_sentiments = {}
    
    # 按作者分组
    for result in sentiment_results:
        author = result['author']
        if not author:
            continue
        
        if author not in author_sentiments:
            author_sentiments[author] = {
                'poem_count': 0,
                'scores': [],
                'sentiments': Counter()
            }
        
        author_sentiments[author]['poem_count'] += 1
        author_sentiments[author]['scores'].append(result['sentiment_score'])
        author_sentiments[author]['sentiments'][result['sentiment']] += 1
    
    # 过滤并计算统计
    final_authors = {}
    for author, data in author_sentiments.items():
        if data['poem_count'] < 2:  # 至少2首诗
            continue
        
        scores = data['scores']
        final_authors[author] = {
            'poem_count': data['poem_count'],
            'avg_sentiment': float(np.mean(scores)),
            'sentiment_std': float(np.std(scores)),
            'sentiment_distribution': dict(data['sentiments']),
            'tendency': '积极' if np.mean(scores) > 0.1 else ('消极' if np.mean(scores) < -0.1 else '中性')
        }
    
    # 排序
    sorted_authors = sorted(final_authors.items(), 
                           key=lambda x: x[1]['avg_sentiment'], 
                           reverse=True)
    
    return {
        'author_count': len(final_authors),
        'most_positive_authors': sorted_authors[:10],
        'most_negative_authors': sorted_authors[-10:],
        'all_authors': final_authors
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='诗词情感分析')
    parser.add_argument('--data', choices=['sample', 'full'], default='sample',
                       help='使用 sample 或 full 数据 (默认: sample)')
    parser.add_argument('--override', action='store_true',
                       help='覆盖已有缓存')
    parser.add_argument('--transformers', action='store_true',
                       help='使用 transformers 进行更准确的分析（需要 GPU/较长时间）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("诗词情感分析")
    print(f"数据类型: {args.data}")
    print(f"使用 transformers: {args.transformers}")
    print("=" * 60)
    
    # 加载数据
    df = load_data(args.data)
    
    # 初始化分析器
    analyzer = SentimentAnalyzer(use_transformers=args.transformers)
    
    # 生成缓存路径
    data_path = Path(__file__).parent.parent / "data" / f"{args.data}_data" / "all_poetry.pkl"
    cache_path = get_cache_path(data_path)
    
    # 情感分布分析
    print("\n" + "-" * 60)
    sentiment_result = analyze_sentiment_distribution(
        df, analyzer, cache_path=cache_path, override=args.override
    )
    
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
    
    # 诗人情感倾向分析（复用已有结果，避免重复计算）
    print("\n" + "-" * 60)
    author_result = analyze_author_sentiment(df, sentiment_result['all_results'])
    
    print(f"\n分析了 {author_result['author_count']} 位诗人")
    
    print(f"\n最积极的10位诗人:")
    for author, info in author_result['most_positive_authors']:
        print(f"  {author}: {info['avg_sentiment']:.3f} ({info['poem_count']}首)")
    
    print(f"\n最消极的10位诗人:")
    for author, info in author_result['most_negative_authors']:
        print(f"  {author}: {info['avg_sentiment']:.3f} ({info['poem_count']}首)")
    
    # 保存结果 - 根据数据类型保存到不同子目录
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "reports" / args.data / "sentiment_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "sentiment_distribution.json", 'w', encoding='utf-8') as f:
        json.dump(sentiment_result, f, ensure_ascii=False, indent=2, default=str)
    
    with open(output_dir / "author_sentiment.json", 'w', encoding='utf-8') as f:
        json.dump(author_result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n结果已保存到: {output_dir}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
