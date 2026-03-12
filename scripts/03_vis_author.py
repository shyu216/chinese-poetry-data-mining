#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗人可视化脚本
读取02_analysis_sentiment.py的结果，生成诗人相关的可视化图表
"""

import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import pandas as pd

from src.visualization.poetry_visualizer import PoetryVisualizer


def load_author_sentiment_data(project_root: Path, data_type: str = 'sample') -> dict:
    """加载诗人情感分析结果"""
    result_path = project_root / "reports" / data_type / "sentiment_analysis" / "author_sentiment.json"
    
    if not result_path.exists():
        print(f"警告: 未找到分析结果文件 {result_path}")
        print(f"请先运行: python scripts/02_analysis_sentiment.py --data {data_type}")
        return None
    
    with open(result_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def visualize_author_sentiment(data: dict, output_dir: Path):
    """诗人情感倾向可视化"""
    print("生成诗人情感倾向可视化...")
    
    if not data or 'all_authors' not in data:
        print("  ✗ 无数据可可视化")
        return
    
    authors = data['all_authors']
    
    # 准备数据
    plot_data = []
    for author, info in authors.items():
        plot_data.append({
            'author': author,
            'avg_sentiment': info['avg_sentiment'],
            'poem_count': info['poem_count'],
            'tendency': info['tendency']
        })
    
    # 按情感得分排序
    plot_data.sort(key=lambda x: x['avg_sentiment'], reverse=True)
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        # 情感得分柱状图
        fig = px.bar(plot_data[:20], x='author', y='avg_sentiment', 
                    color='tendency',
                    title='诗人情感倾向TOP20',
                    labels={'author': '诗人', 'avg_sentiment': '平均情感得分', 'tendency': '倾向'})
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_author_sentiment.html'))
        print(f"  ✓ 已保存: author_sentiment.html")
        
        # 散点图：作品数量 vs 情感得分
        fig2 = px.scatter(plot_data, x='poem_count', y='avg_sentiment',
                         color='tendency', hover_data=['author'],
                         title='诗人作品数量与情感倾向关系',
                         labels={'poem_count': '作品数量', 'avg_sentiment': '平均情感得分'})
        
        visualizer.save_visualization(fig2, str(output_dir / '03_vis_author_scatter.html'))
        print(f"  ✓ 已保存: author_scatter.html")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='诗人可视化')
    parser.add_argument('--data', choices=['sample', 'full'], default='sample',
                       help='使用 sample 或 full 数据 (默认: sample)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("诗人可视化")
    print(f"数据类型: {args.data}")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "gh-pages" / args.data / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载分析结果
    print("\n加载分析结果...")
    data = load_author_sentiment_data(project_root, args.data)
    
    if data:
        print(f"共 {data.get('author_count', 0)} 位诗人\n")
        
        # 生成可视化
        visualize_author_sentiment(data, output_dir)
        
        print(f"\n可视化已保存到: {output_dir}")
    else:
        print("\n无法生成可视化，请先运行分析脚本")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
