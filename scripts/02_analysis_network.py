#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文学社交网络分析脚本（优化版）
支持 sample/full 数据切换、结果缓存、使用 node2vec 进行网络嵌入
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
from node2vec import Node2Vec
from sklearn.cluster import SpectralClustering, KMeans
from sklearn.metrics import silhouette_score

from src.models.social_network_model import SocialNetworkModel
from src.visualization.poetry_visualizer import PoetryVisualizer


def get_cache_path(data_path: Path, suffix: str = "") -> Path:
    """生成缓存文件路径"""
    data_hash = hashlib.md5(str(data_path).encode()).hexdigest()[:8]
    cache_dir = Path(__file__).parent.parent / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"network_{data_hash}{suffix}.json"


def load_cached_analysis(cache_path: Path, override: bool = False) -> Optional[Dict]:
    """加载缓存的分析结果"""
    if override or not cache_path.exists():
        return None
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        print(f"加载缓存: {cache_path}")
        return json.load(f)


def save_cached_analysis(cache_path: Path, data: Dict):
    """保存分析结果到缓存"""
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"缓存已保存: {cache_path}")


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
    print(f"共 {len(df)} 首诗，{df['author'].nunique()} 位诗人")
    
    return df


def build_author_network(df: pd.DataFrame, min_poems: int = 2, 
                        similarity_threshold: float = 0.1,
                        use_node2vec: bool = False) -> dict:
    """
    构建作者社交网络（支持 node2vec 嵌入）
    
    Args:
        df: 诗词数据
        min_poems: 最少诗数阈值
        similarity_threshold: 相似度阈值
        use_node2vec: 是否使用 node2vec 进行网络嵌入
        
    Returns:
        社交网络分析结果
    """
    model = SocialNetworkModel()
    
    print("构建作者文本库...")
    author_texts = model.build_author_texts(df, min_poems=min_poems)
    
    print(f"共 {len(author_texts)} 位作者满足条件")
    
    if len(author_texts) < 2:
        print("作者数量不足，无法构建网络")
        return None
    
    print("计算作者间相似度...")
    authors_list, texts_list, similarity_matrix = model.calculate_similarity(author_texts)
    
    print("构建社交网络...")
    G = model.build_network(authors_list, similarity_matrix, threshold=similarity_threshold)
    
    print("分析网络属性...")
    network_analysis = model.analyze_network(G)
    
    # 找出相似度最高的作者对
    similar_pairs = []
    for i in range(len(authors_list)):
        for j in range(i + 1, len(authors_list)):
            sim = similarity_matrix[i][j]
            if sim > similarity_threshold:
                similar_pairs.append({
                    'author1': authors_list[i],
                    'author2': authors_list[j],
                    'similarity': float(sim)
                })
    
    similar_pairs.sort(key=lambda x: x['similarity'], reverse=True)
    
    result = {
        'authors': authors_list,
        'similarity_matrix': similarity_matrix.tolist(),
        'network': {
            'nodes': network_analysis['network_properties']['nodes'],
            'edges': network_analysis['network_properties']['edges'],
            'density': network_analysis['network_properties']['density'],
            'average_clustering': network_analysis['network_properties']['average_clustering']
        },
        'centrality': {
            'degree': network_analysis['degree_centrality'],
            'betweenness': network_analysis['betweenness_centrality'],
            'closeness': network_analysis['closeness_centrality']
        },
        'top_similar_pairs': similar_pairs[:20],
        'network_analysis': network_analysis
    }
    
    # 使用 node2vec 进行网络嵌入（可选）
    if use_node2vec and len(authors_list) > 5:
        print("使用 node2vec 进行网络嵌入...")
        node2vec = Node2Vec(G, dimensions=64, walk_length=30, num_walks=200, workers=4)
        model_n2v = node2vec.fit(window=10, min_count=1, batch_words=4)
        
        # 提取每个作者的嵌入向量
        embeddings = {}
        for author in authors_list:
            if author in model_n2v.wv:
                embeddings[author] = model_n2v.wv[author].tolist()
        
        result['node2vec_embeddings'] = embeddings
        print(f"  生成了 {len(embeddings)} 个作者的嵌入向量")
    
    return result


def analyze_author_clusters(network_result: dict, n_clusters: int = 5) -> dict:
    """
    分析作者聚类（支持多种算法）
    
    Args:
        network_result: 社交网络分析结果
        n_clusters: 聚类数量
        
    Returns:
        聚类分析结果
    """
    similarity_matrix = np.array(network_result['similarity_matrix'])
    authors = network_result['authors']
    
    n_clusters = min(n_clusters, len(authors))
    if n_clusters < 2:
        return {'clusters': [], 'method': 'none'}
    
    # 尝试多种聚类算法
    methods = {}
    
    # 1. 谱聚类
    # 修复：清空对角线（自身相似度设为0）
    np.fill_diagonal(similarity_matrix, 0)
    
    clustering = SpectralClustering(n_clusters=n_clusters, affinity='precomputed', random_state=42)
    labels = clustering.fit_predict(similarity_matrix)
    score = silhouette_score(similarity_matrix, labels, metric='precomputed')
    methods['spectral'] = {'labels': labels, 'score': score}
    
    # 2. K-Means（基于 node2vec 嵌入）
    if 'node2vec_embeddings' in network_result and len(network_result['node2vec_embeddings']) > n_clusters:
        embeddings = np.array([network_result['node2vec_embeddings'][a] for a in authors 
                              if a in network_result['node2vec_embeddings']])
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels_km = kmeans.fit_predict(embeddings)
        score_km = silhouette_score(embeddings, labels_km)
        methods['kmeans_node2vec'] = {'labels': labels_km, 'score': score_km}
    
    # 选择最佳方法
    if methods:
        best_method = max(methods.items(), key=lambda x: x[1]['score'])
        best_labels = best_method[1]['labels']
        
        # 组织聚类结果
        clusters = {}
        for author, label in zip(authors, best_labels):
            label_key = int(label)
            if label_key not in clusters:
                clusters[label_key] = []
            clusters[label_key].append(author)
        
        return {
            'n_clusters': n_clusters,
            'clusters': clusters,
            'method': best_method[0],
            'silhouette_score': float(best_method[1]['score'])
        }
    
    return {'clusters': [], 'method': 'none'}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文学社交网络分析')
    parser.add_argument('--data', choices=['sample', 'full'], default='sample',
                       help='使用 sample 或 full 数据 (默认: sample)')
    parser.add_argument('--override', action='store_true',
                       help='覆盖已有缓存')
    parser.add_argument('--node2vec', action='store_true',
                       help='使用 node2vec 进行网络嵌入')
    parser.add_argument('--threshold', type=float, default=0.1,
                       help='相似度阈值 (默认: 0.1)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("文学社交网络分析")
    print(f"数据类型: {args.data}")
    print(f"使用 node2vec: {args.node2vec}")
    print("=" * 60)
    
    # 加载数据
    df = load_data(args.data)
    
    # 生成缓存路径
    data_path = Path(__file__).parent.parent / "data" / f"{args.data}_data" / "all_poetry.pkl"
    cache_path = get_cache_path(data_path)
    
    # 尝试加载缓存
    network_result = load_cached_analysis(cache_path, args.override)
    
    if not network_result:
        # 构建社交网络
        print("\n" + "-" * 60)
        network_result = build_author_network(
            df, min_poems=2, similarity_threshold=args.threshold,
            use_node2vec=args.node2vec
        )
        
        if network_result:
            save_cached_analysis(cache_path, network_result)
    
    if network_result:
        print(f"\n网络统计:")
        print(f"  节点数: {network_result['network']['nodes']}")
        print(f"  边数: {network_result['network']['edges']}")
        print(f"  网络密度: {network_result['network']['density']:.3f}")
        print(f"  平均聚类系数: {network_result['network']['average_clustering']:.3f}")
        
        # 中心性分析
        print(f"\n中心性最高的10位诗人:")
        degree_cent = network_result['centrality']['degree']
        top_authors = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]
        for author, cent in top_authors:
            print(f"  {author}: {cent:.3f}")
        
        # 最相似的作者对
        print(f"\n最相似的10对诗人:")
        for pair in network_result['top_similar_pairs'][:10]:
            print(f"  {pair['author1']} - {pair['author2']}: {pair['similarity']:.3f}")
        
        # 聚类分析
        print("\n" + "-" * 60)
        print("进行聚类分析...")
        cluster_result = analyze_author_clusters(network_result)
        
        if cluster_result['clusters']:
            print(f"\n使用 {cluster_result['method']} 分为 {cluster_result['n_clusters']} 个群体:")
            print(f"轮廓系数: {cluster_result.get('silhouette_score', 0):.3f}")
            for cluster_id, authors in cluster_result['clusters'].items():
                print(f"  群体 {cluster_id + 1}: {', '.join(authors)}")
        
        # 保存结果 - 根据数据类型保存到不同子目录
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "reports" / args.data / "social_network"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "network_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(network_result, f, ensure_ascii=False, indent=2, default=str)
        
        with open(output_dir / "cluster_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(cluster_result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n结果已保存到: {output_dir}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
