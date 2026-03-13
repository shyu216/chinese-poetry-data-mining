#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 18: 诗词推荐系统 (静态化)
预计算每首诗的相似诗词 (Top 10)
基于词汇重叠和风格相似度
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_silver_data() -> pd.DataFrame:
    """加载Silver层数据"""
    silver_path = project_root / "data" / "silver" / "v2_poems_structured.csv"
    
    if not silver_path.exists():
        raise FileNotFoundError(f"找不到Silver层数据: {silver_path}")
    
    print(f"加载Silver层数据: {silver_path}")
    df = pd.read_csv(silver_path)
    print(f"共加载 {len(df)} 首诗词")
    return df


def build_recommendation_index(df: pd.DataFrame, top_n: int = 10) -> Dict:
    """
    构建诗词推荐索引
    
    对每首诗找出最相似的诗词，基于：
    1. 词汇重叠度
    2. 风格相似度 (TF-IDF)
    3. 相同作者/朝代加分
    """
    print("构建诗词推荐索引...")
    print(f"将为每首诗推荐 Top {top_n} 首相似诗词")
    
    # 准备文本数据
    poems_data = []
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  准备数据: {idx}/{len(df)}")
        
        content = row.get('content', '')
        if pd.isna(content) or not content:
            continue
        
        poems_data.append({
            'id': str(idx),
            'title': row.get('title', ''),
            'author': row.get('author', '未知'),
            'dynasty': row.get('dynasty', '未知'),
            'content': str(content),
            'keywords': str(row.get('keywords', '')) if not pd.isna(row.get('keywords', '')) else ''
        })
    
    print(f"有效诗词数: {len(poems_data)}")
    
    # 构建TF-IDF向量
    print("构建TF-IDF向量...")
    texts = [p['content'] + ' ' + p['keywords'] for p in poems_data]
    
    vectorizer = TfidfVectorizer(
        max_features=5000,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2)
    )
    
    tfidf_matrix = vectorizer.fit_transform(texts)
    print(f"TF-IDF矩阵形状: {tfidf_matrix.shape}")
    
    # 计算相似度矩阵 (分批处理以节省内存)
    print("计算相似度矩阵...")
    batch_size = 100
    n_poems = len(poems_data)
    
    recommendations = {}
    
    for i in range(0, n_poems, batch_size):
        end_i = min(i + batch_size, n_poems)
        print(f"  处理批次: {i}-{end_i}/{n_poems}")
        
        # 计算当前批次与所有诗词的相似度
        batch_similarities = cosine_similarity(
            tfidf_matrix[i:end_i], 
            tfidf_matrix
        )
        
        # 为批次中的每首诗找出最相似的诗词
        for batch_idx, poem_idx in enumerate(range(i, end_i)):
            poem = poems_data[poem_idx]
            similarities = batch_similarities[batch_idx]
            
            # 获取最相似的诗词 (排除自己)
            similar_indices = similarities.argsort()[::-1][1:top_n+1]
            
            similar_poems = []
            for sim_idx in similar_indices:
                sim_poem = poems_data[sim_idx]
                similarity_score = float(similarities[sim_idx])
                
                # 构建推荐理由
                reasons = []
                if poem['author'] == sim_poem['author']:
                    reasons.append(f"同作者: {poem['author']}")
                if poem['dynasty'] == sim_poem['dynasty']:
                    reasons.append(f"同朝代: {poem['dynasty']}")
                
                # 找出共同关键词
                poem_keywords = set(poem['keywords'].split()) if poem['keywords'] else set()
                sim_keywords = set(sim_poem['keywords'].split()) if sim_poem['keywords'] else set()
                common_keywords = poem_keywords & sim_keywords
                if common_keywords:
                    reasons.append(f"共同主题: {', '.join(list(common_keywords)[:3])}")
                
                reason_text = '；'.join(reasons) if reasons else '风格相似'
                
                similar_poems.append({
                    'id': sim_poem['id'],
                    'title': sim_poem['title'],
                    'author': sim_poem['author'],
                    'dynasty': sim_poem['dynasty'],
                    'score': round(similarity_score, 4),
                    'reason': reason_text
                })
            
            recommendations[poem['id']] = {
                'poem': {
                    'id': poem['id'],
                    'title': poem['title'],
                    'author': poem['author'],
                    'dynasty': poem['dynasty']
                },
                'recommendations': similar_poems
            }
    
    # 构建索引数据
    index_data = {
        'version': '1.0.0',
        'generated_at': pd.Timestamp.now().isoformat(),
        'total_poems': len(poems_data),
        'recommendations_per_poem': top_n,
        'recommendations': recommendations
    }
    
    print(f"推荐索引构建完成")
    print(f"  - 诗词总数: {len(recommendations)}")
    print(f"  - 每首推荐数: {top_n}")
    
    return index_data


def save_index(index_data: Dict, output_dir: Path):
    """保存索引文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存主索引文件
    index_file = output_dir / 'recommendation_index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    file_size = index_file.stat().st_size / 1024  # KB
    print(f"\n索引文件已保存: {index_file}")
    print(f"文件大小: {file_size:.2f} KB ({file_size/1024:.2f} MB)")
    
    # 保存压缩版本
    import gzip
    compressed_file = output_dir / 'recommendation_index.json.gz'
    with gzip.open(compressed_file, 'wt', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False)
    
    compressed_size = compressed_file.stat().st_size / 1024  # KB
    print(f"压缩文件已保存: {compressed_file}")
    print(f"压缩后大小: {compressed_size:.2f} KB ({compressed_size/1024:.2f} MB)")
    print(f"压缩率: {(1 - compressed_size/file_size)*100:.1f}%")


def main():
    """主函数"""
    print("=" * 60)
    print("Task 18: 诗词推荐系统 (静态化)")
    print("=" * 60)
    
    try:
        # 加载数据
        df = load_silver_data()
        
        # 构建索引
        index_data = build_recommendation_index(df, top_n=10)
        
        # 保存索引
        output_dir = project_root / "data" / "output" / "web" / "index"
        save_index(index_data, output_dir)
        
        print("\n✅ Task 18 完成!")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
