#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
朝代可视化脚本
读取sample或full data，生成朝代相关的可视化图表
"""

import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd

from src.visualization.poetry_visualizer import PoetryVisualizer


def load_dynasty_data(project_root: Path, data_type: str = 'sample') -> pd.DataFrame:
    """加载朝代数据"""
    if data_type == 'sample':
        data_path = project_root / "data" / "sample_data" / "all_poetry.pkl"
    else:
        data_path = project_root / "data" / "processed_data" / "all_poetry.pkl"
    
    if not data_path.exists():
        print(f"警告: 未找到数据文件 {data_path}")
        return None
    
    return pd.read_pickle(data_path)


def visualize_dynasty_distribution(df: pd.DataFrame, output_dir: Path):
    """朝代分布可视化"""
    print("生成朝代分布可视化...")
    
    # 统计
    dynasty_counts = df['dynasty'].value_counts()
    plot_data = [{'dynasty': d, 'count': c} for d, c in dynasty_counts.items()]
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        # 饼图
        fig = px.pie(plot_data, values='count', names='dynasty',
                    title='诗词朝代分布',
                    color='dynasty')
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_dynasty_pie.html'))
        print(f"  ✓ 已保存: dynasty_pie.html")
        
        # 柱状图
        fig2 = px.bar(plot_data, x='dynasty', y='count',
                     title='诗词朝代分布',
                     labels={'dynasty': '朝代', 'count': '数量'},
                     color='dynasty')
        
        visualizer.save_visualization(fig2, str(output_dir / '03_vis_dynasty_bar.html'))
        print(f"  ✓ 已保存: dynasty_bar.html")


def visualize_genre_by_dynasty(df: pd.DataFrame, output_dir: Path):
    """各朝代的体裁分布"""
    print("生成体裁分布可视化...")
    
    # 交叉统计
    cross_tab = pd.crosstab(df['dynasty'], df['genre'])
    
    # 转换为长格式
    plot_data = []
    for dynasty in cross_tab.index:
        for genre in cross_tab.columns:
            plot_data.append({
                'dynasty': dynasty,
                'genre': genre,
                'count': cross_tab.loc[dynasty, genre]
            })
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        # 分组柱状图
        fig = px.bar(plot_data, x='dynasty', y='count', color='genre',
                    title='各朝代体裁分布',
                    labels={'dynasty': '朝代', 'count': '数量', 'genre': '体裁'},
                    barmode='group')
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_dynasty_genre.html'))
        print(f"  ✓ 已保存: dynasty_genre.html")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='朝代可视化')
    parser.add_argument('--data', choices=['sample', 'full'], default='sample',
                       help='使用 sample 或 full 数据 (默认: sample)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("朝代可视化")
    print(f"数据类型: {args.data}")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "gh-pages" / args.data / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    print("\n加载数据...")
    df = load_dynasty_data(project_root, args.data)
    
    if df is not None:
        print(f"共 {len(df)} 首诗")
        print(f"朝代: {df['dynasty'].unique().tolist()}\n")
        
        # 生成可视化
        visualize_dynasty_distribution(df, output_dir)
        visualize_genre_by_dynasty(df, output_dir)
        
        print(f"\n可视化已保存到: {output_dir}")
    else:
        print("\n无法生成可视化，数据文件不存在")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
