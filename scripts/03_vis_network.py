#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交网络可视化脚本
读取02_analysis_network.py的结果，生成社交网络可视化图表
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import pandas as pd

from src.visualization.poetry_visualizer import PoetryVisualizer


def load_network_data(project_root: Path) -> dict:
    """加载社交网络分析结果"""
    result_path = project_root / "reports" / "social_network" / "network_analysis.json"
    
    if not result_path.exists():
        print(f"警告: 未找到分析结果文件 {result_path}")
        print("请先运行: python scripts/02_analysis_network.py")
        return None
    
    with open(result_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def visualize_network_graph(data: dict, output_dir: Path):
    """社交网络图可视化"""
    print("生成社交网络图...")
    
    if not data or 'authors' not in data:
        print("  ✗ 无数据可可视化")
        return
    
    authors = data['authors']
    similarity_matrix = data.get('similarity_matrix', [])
    top_pairs = data.get('top_similar_pairs', [])
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    # 准备节点和边
    nodes = [{'id': author, 'label': author, 'size': 10} for author in authors]
    
    edges = []
    for pair in top_pairs[:50]:  # 只取前50条边
        edges.append({
            'source': pair['author1'],
            'target': pair['author2'],
            'weight': pair['similarity']
        })
    
    # 创建网络图
    fig = visualizer.create_network_graph(nodes, edges, title="诗人社交网络")
    
    if fig:
        visualizer.save_visualization(fig, str(output_dir / '03_vis_network_graph.html'))
        print(f"  ✓ 已保存: network_graph.html")


def visualize_centrality(data: dict, output_dir: Path):
    """中心性分析可视化"""
    print("生成中心性分析可视化...")
    
    if not data or 'centrality' not in data:
        print("  ✗ 无中心性数据")
        return
    
    centrality = data['centrality']
    degree_cent = centrality.get('degree', {})
    
    # 准备数据
    plot_data = []
    for author, score in sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:20]:
        plot_data.append({
            'author': author,
            'centrality': score
        })
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        fig = px.bar(plot_data, x='author', y='centrality',
                    title='诗人网络中心性TOP20',
                    labels={'author': '诗人', 'centrality': '中心性得分'})
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_network_centrality.html'))
        print(f"  ✓ 已保存: network_centrality.html")


def visualize_similarity_heatmap(data: dict, output_dir: Path):
    """相似度热力图"""
    print("生成相似度热力图...")
    
    if not data or 'similarity_matrix' not in data:
        print("  ✗ 无相似度数据")
        return
    
    authors = data['authors'][:20]  # 只取前20个作者
    similarity_matrix = data['similarity_matrix'][:20][:20]
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    fig = visualizer.create_heatmap(similarity_matrix, authors, 
                                   title="诗人相似度热力图")
    
    if fig:
        visualizer.save_visualization(fig, str(output_dir / '03_vis_network_heatmap.html'))
        print(f"  ✓ 已保存: network_heatmap.html")


def main():
    """主函数"""
    print("=" * 60)
    print("社交网络可视化")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "reports" / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载分析结果
    print("\n加载分析结果...")
    data = load_network_data(project_root)
    
    if data:
        print(f"共 {len(data.get('authors', []))} 位诗人")
        print(f"网络密度: {data.get('network_properties', {}).get('density', 0):.3f}\n")
        
        # 生成可视化
        visualize_network_graph(data, output_dir)
        visualize_centrality(data, output_dir)
        visualize_similarity_heatmap(data, output_dir)
        
        print(f"\n可视化已保存到: {output_dir}")
    else:
        print("\n无法生成可视化，请先运行分析脚本")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
