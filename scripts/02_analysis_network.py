#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文学社交网络分析脚本
使用sample data进行社交网络分析
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from tqdm import tqdm

from src.models.social_network_model import SocialNetworkModel, build_poet_network
from src.visualization.poetry_visualizer import PoetryVisualizer


def build_author_network(df: pd.DataFrame, min_poems: int = 2, similarity_threshold: float = 0.1) -> dict:
    """
    构建作者社交网络
    
    Args:
        df: 诗词数据DataFrame
        min_poems: 最少诗数阈值
        similarity_threshold: 相似度阈值
        
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
    
    return {
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


def analyze_author_clusters(network_result: dict) -> dict:
    """
    分析作者聚类
    
    Args:
        network_result: 社交网络分析结果
        
    Returns:
        聚类分析结果
    """
    import networkx as nx
    from sklearn.cluster import SpectralClustering
    
    similarity_matrix = np.array(network_result['similarity_matrix'])
    authors = network_result['authors']
    
    # 使用谱聚类
    n_clusters = min(5, len(authors))
    if n_clusters < 2:
        return {'clusters': []}
    
    clustering = SpectralClustering(n_clusters=n_clusters, affinity='precomputed')
    labels = clustering.fit_predict(similarity_matrix)
    
    # 组织聚类结果
    clusters = {}
    for author, label in zip(authors, labels):
        label_key = int(label)  # 转换为Python int
        if label_key not in clusters:
            clusters[label_key] = []
        clusters[label_key].append(author)
    
    return {
        'n_clusters': int(n_clusters),
        'clusters': clusters
    }


def main():
    """主函数"""
    print("=" * 60)
    print("文学社交网络分析")
    print("=" * 60)
    
    # 加载数据
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "sample_data" / "all_poetry.pkl"
    
    print(f"\n加载数据: {data_path}")
    df = pd.read_pickle(data_path)
    print(f"共 {len(df)} 首诗")
    print(f"共 {df['author'].nunique()} 位诗人")
    
    # 构建社交网络
    print("\n" + "-" * 60)
    network_result = build_author_network(df, min_poems=2, similarity_threshold=0.05)
    
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
        
        print(f"\n分为 {cluster_result['n_clusters']} 个群体:")
        for cluster_id, authors in cluster_result['clusters'].items():
            print(f"  群体 {cluster_id + 1}: {', '.join(authors)}")
        
        # 生成可视化
        print("\n" + "-" * 60)
        print("生成可视化...")
        
        visualizer = PoetryVisualizer()
        
        # 准备节点和边
        nodes = [{'id': author, 'label': author, 'size': 10 + degree_cent.get(author, 0) * 50} 
                for author in network_result['authors']]
        
        edges = []
        for pair in network_result['top_similar_pairs'][:50]:  # 只取前50条边
            edges.append({
                'source': pair['author1'],
                'target': pair['author2'],
                'weight': pair['similarity']
            })
        
        # 创建网络图
        fig = visualizer.create_network_graph(nodes, edges, title="诗人社交网络")
        
        # 保存结果
        import json
        output_dir = project_root / "reports" / "social_network"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "network_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(network_result, f, ensure_ascii=False, indent=2, default=str)
        
        with open(output_dir / "cluster_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(cluster_result, f, ensure_ascii=False, indent=2, default=str)
        
        if fig:
            visualizer.save_visualization(fig, str(output_dir / "author_network.html"))
        
        print(f"\n结果已保存到: {output_dir}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
