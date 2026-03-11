#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感可视化脚本
读取02_analysis_sentiment.py的结果，生成情感分析相关的可视化图表
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import pandas as pd

from src.visualization.poetry_visualizer import PoetryVisualizer


def load_sentiment_data(project_root: Path) -> dict:
    """加载情感分析结果"""
    result_path = project_root / "reports" / "sentiment_analysis" / "sentiment_distribution.json"
    
    if not result_path.exists():
        print(f"警告: 未找到分析结果文件 {result_path}")
        print("请先运行: python scripts/02_analysis_sentiment.py")
        return None
    
    with open(result_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def visualize_sentiment_distribution(data: dict, output_dir: Path):
    """情感分布可视化"""
    print("生成情感分布可视化...")
    
    if not data:
        print("  ✗ 无数据可可视化")
        return
    
    # 准备数据
    sentiment_dist = data.get('sentiment_distribution', {})
    plot_data = [{'sentiment': k, 'count': v} for k, v in sentiment_dist.items()]
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        # 情感分布饼图
        fig = px.pie(plot_data, values='count', names='sentiment',
                    title='诗词情感分布',
                    color='sentiment',
                    color_discrete_map={'积极': '#2ecc71', '中性': '#95a5a6', '消极': '#e74c3c'})
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_sentiment_pie.html'))
        print(f"  ✓ 已保存: sentiment_pie.html")
        
        # 情感分布柱状图
        fig2 = px.bar(plot_data, x='sentiment', y='count',
                     title='诗词情感分布',
                     labels={'sentiment': '情感', 'count': '数量'},
                     color='sentiment',
                     color_discrete_map={'积极': '#2ecc71', '中性': '#95a5a6', '消极': '#e74c3c'})
        
        visualizer.save_visualization(fig2, str(output_dir / '03_vis_sentiment_bar.html'))
        print(f"  ✓ 已保存: sentiment_bar.html")


def visualize_extreme_poems(data: dict, output_dir: Path):
    """极端情感诗词可视化"""
    print("生成极端情感诗词可视化...")
    
    if not data or 'all_results' not in data:
        print("  ✗ 无数据可可视化")
        return
    
    results = data['all_results']
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        # 情感得分分布直方图
        fig = px.histogram(results, x='sentiment_score', nbins=20,
                          title='情感得分分布',
                          labels={'sentiment_score': '情感得分', 'count': '数量'})
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_sentiment_hist.html'))
        print(f"  ✓ 已保存: sentiment_hist.html")


def main():
    """主函数"""
    print("=" * 60)
    print("情感可视化")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "reports" / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载分析结果
    print("\n加载分析结果...")
    data = load_sentiment_data(project_root)
    
    if data:
        print(f"共 {data.get('total_poems', 0)} 首诗\n")
        
        # 生成可视化
        visualize_sentiment_distribution(data, output_dir)
        visualize_extreme_poems(data, output_dir)
        
        print(f"\n可视化已保存到: {output_dir}")
    else:
        print("\n无法生成可视化，请先运行分析脚本")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
