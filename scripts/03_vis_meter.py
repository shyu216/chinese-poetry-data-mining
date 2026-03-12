#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格律可视化脚本
读取02_analysis_meter.py的结果，生成格律分析可视化图表
"""

import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json
import pandas as pd

from src.visualization.poetry_visualizer import PoetryVisualizer


def load_meter_data(project_root: Path, data_type: str = 'sample') -> dict:
    """加载格律分析结果"""
    result_path = project_root / "reports" / data_type / "meter_analysis" / "meter_analysis.json"
    
    if not result_path.exists():
        print(f"警告: 未找到分析结果文件 {result_path}")
        print(f"请先运行: python scripts/02_analysis_meter.py --data {data_type}")
        return None
    
    with open(result_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def visualize_form_distribution(data: dict, output_dir: Path):
    """诗体分布可视化"""
    print("生成诗体分布可视化...")
    
    if not data or 'form_distribution' not in data:
        print("  ✗ 无数据可可视化")
        return
    
    form_dist = data['form_distribution']
    plot_data = [{'form': k, 'count': v} for k, v in form_dist.items()]
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        # 饼图
        fig = px.pie(plot_data, values='count', names='form',
                    title='诗体分布',
                    color='form')
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_meter_pie.html'))
        print(f"  ✓ 已保存: meter_pie.html")
        
        # 柱状图
        fig2 = px.bar(plot_data, x='form', y='count',
                     title='诗体分布',
                     labels={'form': '诗体', 'count': '数量'},
                     color='form')
        
        visualizer.save_visualization(fig2, str(output_dir / '03_vis_meter_bar.html'))
        print(f"  ✓ 已保存: meter_bar.html")


def visualize_tone_patterns(data: dict, output_dir: Path):
    """平仄模式可视化"""
    print("生成平仄模式可视化...")
    
    if not data or 'details' not in data:
        print("  ✗ 无详细数据")
        return
    
    details = data['details']
    
    # 统计平仄比例
    level_count = 0
    oblique_count = 0
    
    for poem in details:
        for pattern in poem.get('tone_patterns', []):
            level_count += pattern.count('平')
            oblique_count += pattern.count('仄')
    
    total = level_count + oblique_count
    if total == 0:
        print("  ✗ 无平仄数据")
        return
    
    plot_data = [
        {'type': '平声', 'count': level_count, 'percentage': level_count / total},
        {'type': '仄声', 'count': oblique_count, 'percentage': oblique_count / total}
    ]
    
    # 创建可视化
    visualizer = PoetryVisualizer()
    
    if visualizer.plotly_available:
        import plotly.express as px
        
        fig = px.pie(plot_data, values='count', names='type',
                    title='平仄比例分布',
                    color='type',
                    color_discrete_map={'平声': '#3498db', '仄声': '#e74c3c'})
        
        visualizer.save_visualization(fig, str(output_dir / '03_vis_meter_tone.html'))
        print(f"  ✓ 已保存: meter_tone.html")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='格律可视化')
    parser.add_argument('--data', choices=['sample', 'full'], default='sample',
                       help='使用 sample 或 full 数据 (默认: sample)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("格律可视化")
    print(f"数据类型: {args.data}")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "gh-pages" / args.data / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载分析结果
    print("\n加载分析结果...")
    data = load_meter_data(project_root, args.data)
    
    if data:
        print(f"共 {data.get('total', 0)} 首诗\n")
        
        # 生成可视化
        visualize_form_distribution(data, output_dir)
        visualize_tone_patterns(data, output_dir)
        
        print(f"\n可视化已保存到: {output_dir}")
    else:
        print("\n无法生成可视化，请先运行分析脚本")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
