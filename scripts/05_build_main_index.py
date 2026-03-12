#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建 GitHub Pages 主入口页面
导航到 sample 和 full 版本
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))


def build_main_index_html() -> str:
    """构建主入口 HTML"""
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中国古代文学时空图谱 - 数据挖掘与可视化</title>
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
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 800px;
            width: 100%;
        }}
        
        header {{
            text-align: center;
            color: white;
            margin-bottom: 60px;
        }}
        
        h1 {{
            font-size: 3em;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .subtitle {{
            font-size: 1.3em;
            opacity: 0.9;
        }}
        
        .version-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }}
        
        .version-card {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        
        .version-card:hover {{
            transform: translateY(-10px);
            box-shadow: 0 30px 80px rgba(0,0,0,0.2);
        }}
        
        .version-card .icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        
        .version-card h2 {{
            color: #333;
            font-size: 1.8em;
            margin-bottom: 15px;
        }}
        
        .version-card p {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        
        .version-card .badge {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .version-card.sample .badge {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        
        .version-card.full .badge {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        footer {{
            text-align: center;
            color: white;
            margin-top: 60px;
            opacity: 0.8;
        }}
        
        .update-time {{
            margin-top: 10px;
            font-size: 0.9em;
            opacity: 0.7;
        }}
        
        @media (max-width: 600px) {{
            h1 {{
                font-size: 2em;
            }}
            
            .version-card {{
                padding: 30px 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>中国古代文学时空图谱</h1>
            <p class="subtitle">数据挖掘与可视化分析平台</p>
        </header>
        
        <div class="version-cards">
            <a href="sample/index.html" class="version-card sample">
                <div class="icon">📊</div>
                <h2>采样数据版</h2>
                <p>精选代表性诗词数据，加载快速，适合快速浏览和演示</p>
                <span class="badge">Sample Data</span>
            </a>
            
            <a href="full/index.html" class="version-card full">
                <div class="icon">📚</div>
                <h2>完整数据版</h2>
                <p>包含全部诗词数据，内容丰富，适合深度研究和分析</p>
                <span class="badge">Full Dataset</span>
            </a>
        </div>
        
        <footer>
            <p>基于 chinese-poetry 数据集 | 使用 Python + Plotly 构建</p>
            <p class="update-time">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
'''
    
    return html


def main():
    """主函数"""
    print("构建 GitHub Pages 主入口页面...")
    
    project_root = Path(__file__).parent.parent
    output_path = project_root / "gh-pages" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    html_content = build_main_index_html()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ 主入口页面已生成: {output_path}")


if __name__ == "__main__":
    main()
