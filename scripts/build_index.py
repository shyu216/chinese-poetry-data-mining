#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建可视化索引页面
为GitHub Pages生成一个美观的导航页
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))


def build_index_html(visualizations_dir: Path) -> str:
    """
    构建索引HTML
    
    Args:
        visualizations_dir: 可视化文件目录
        
    Returns:
        HTML字符串
    """
    # 获取所有HTML文件
    html_files = sorted(visualizations_dir.glob("*.html"))
    
    # 按类别分组
    categories = {
        'sentiment': {'title': '情感分析', 'files': []},
        'meter': {'title': '格律分析', 'files': []},
        'network': {'title': '社交网络', 'files': []},
        'dynasty': {'title': '朝代分析', 'files': []},
        'author': {'title': '诗人分析', 'files': []}
    }
    
    for html_file in html_files:
        filename = html_file.name
        if 'sentiment' in filename:
            categories['sentiment']['files'].append(filename)
        elif 'meter' in filename:
            categories['meter']['files'].append(filename)
        elif 'network' in filename:
            categories['network']['files'].append(filename)
        elif 'dynasty' in filename:
            categories['dynasty']['files'].append(filename)
        elif 'author' in filename:
            categories['author']['files'].append(filename)
    
    # 构建HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中国古代文学时空图谱 - 可视化报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .update-time {{
            margin-top: 15px;
            font-size: 0.9em;
            opacity: 0.7;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
        }}
        
        .card {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }}
        
        .card h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .card ul {{
            list-style: none;
        }}
        
        .card li {{
            margin-bottom: 12px;
        }}
        
        .card a {{
            display: block;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 8px;
            text-decoration: none;
            color: #555;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
        }}
        
        .card a:hover {{
            background: #667eea;
            color: white;
            border-left-color: #764ba2;
            transform: translateX(5px);
        }}
        
        .card a::before {{
            content: "📊 ";
            margin-right: 8px;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 50px;
            opacity: 0.8;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 30px 0;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            text-align: center;
            color: white;
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        
        @media (max-width: 768px) {{
            h1 {{
                font-size: 1.8em;
            }}
            
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>中国古代文学时空图谱</h1>
            <p class="subtitle">数据挖掘与可视化分析报告</p>
            <p class="update-time">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-number">{len(html_files)}</span>
                    <span class="stat-label">可视化图表</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{len([c for c in categories.values() if c['files']])}</span>
                    <span class="stat-label">分析维度</span>
                </div>
            </div>
        </header>
        
        <div class="grid">
'''
    
    # 添加每个类别的卡片
    for key, category in categories.items():
        if category['files']:
            html += f'''
            <div class="card">
                <h2>{category['title']}</h2>
                <ul>
'''
            for filename in sorted(category['files']):
                # 生成友好的显示名称
                display_name = filename.replace('03_vis_', '').replace('.html', '').replace('_', ' ').title()
                html += f'''
                    <li><a href="{filename}">{display_name}</a></li>
'''
            html += '''
                </ul>
            </div>
'''
    
    html += '''
        </div>
        
        <footer class="footer">
            <p>基于 chinese-poetry 数据集 | 使用 Python + Plotly 构建</p>
        </footer>
    </div>
</body>
</html>
'''
    
    return html


def main():
    """主函数"""
    print("构建可视化索引页面...")
    
    # 设置路径
    project_root = Path(__file__).parent.parent
    visualizations_dir = project_root / "reports" / "visualizations"
    
    if not visualizations_dir.exists():
        print(f"警告: 可视化目录不存在 {visualizations_dir}")
        return
    
    # 构建HTML
    html_content = build_index_html(visualizations_dir)
    
    # 保存
    index_path = visualizations_dir / "index.html"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ 索引页面已生成: {index_path}")
    
    # 统计
    html_files = list(visualizations_dir.glob("*.html"))
    print(f"✓ 共 {len(html_files)} 个可视化文件")


if __name__ == "__main__":
    main()
