#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词知识库后端API服务
功能：
1. 提供诗词查询API
2. 按句式/格律索引
3. 支持搜索、筛选、分页
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

DATA_CACHE = {}


def load_data():
    """加载数据到内存"""
    global DATA_CACHE
    if DATA_CACHE:
        return DATA_CACHE

    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"

    print(f"加载数据: {data_path}")
    df = pd.read_csv(data_path, low_memory=False)
    
    # 转换lines字段从字符串到列表
    if 'lines' in df.columns:
        df['lines'] = df['lines'].apply(lambda x: x.split('|') if isinstance(x, str) else [])
    
    print(f"加载完成: {len(df)} 首诗")

    DATA_CACHE['df'] = df
    return DATA_CACHE


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    df = load_data()['df']

    return jsonify({
        'total': len(df),
        'by_dynasty': df['dynasty'].value_counts().to_dict(),
        'by_genre': df['genre'].value_counts().to_dict(),
        'by_type': df['poem_type'].value_counts().to_dict(),
        'regular_count': int(df['is_regular'].sum()),
    })


@app.route('/api/poems', methods=['GET'])
def get_poems():
    """获取诗词列表，支持分页和筛选"""
    df = load_data()['df']

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    dynasty = request.args.get('dynasty', '')
    genre = request.args.get('genre', '')
    poem_type = request.args.get('poem_type', '')
    meter_pattern = request.args.get('meter_pattern', '')
    search = request.args.get('search', '')
    is_regular = request.args.get('is_regular', '')

    filtered_df = df.copy()

    if dynasty:
        filtered_df = filtered_df[filtered_df['dynasty'] == dynasty]
    if genre:
        filtered_df = filtered_df[filtered_df['genre'] == genre]
    if poem_type:
        filtered_df = filtered_df[filtered_df['poem_type'] == poem_type]
    if meter_pattern:
        filtered_df = filtered_df[filtered_df['meter_pattern'] == meter_pattern]
    if is_regular:
        filtered_df = filtered_df[filtered_df['is_regular'] == (is_regular == 'true')]
    if search:
        mask = (
            filtered_df['title'].str.contains(search, na=False) |
            filtered_df['author'].str.contains(search, na=False) |
            filtered_df['lines'].apply(lambda x: search in '|'.join(x) if isinstance(x, list) else False)
        )
        filtered_df = filtered_df[mask]

    total = len(filtered_df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = filtered_df.iloc[start:end]

    results = []
    for _, row in page_df.iterrows():
        results.append({
            'id': str(row['id']),
            'title': row['title'],
            'author': row['author'],
            'dynasty': row['dynasty'],
            'genre': row['genre'],
            'poem_type': row['poem_type'],
            'meter_pattern': row['meter_pattern'],
            'total_lines': row['total_lines'],
            'total_chars': row['total_chars'],
            'is_regular': bool(row['is_regular']),
            'lines': row['lines'] if isinstance(row['lines'], list) else [],
        })

    return jsonify({
        'total': total,
        'page': page,
        'page_size': page_size,
        'data': results,
    })


@app.route('/api/poem/<poem_id>', methods=['GET'])
def get_poem(poem_id):
    """获取单首诗的详细信息"""
    df = load_data()['df']

    poem = df[df['id'] == poem_id]
    if poem.empty:
        poem = df.iloc[int(poem_id)] if poem_id.isdigit() else None
        if poem is None:
            return jsonify({'error': 'Not found'}), 404
    else:
        poem = poem.iloc[0]

    return jsonify({
        'id': str(poem['id']),
        'title': poem['title'],
        'author': poem['author'],
        'dynasty': poem['dynasty'],
        'genre': poem['genre'],
        'poem_type': poem['poem_type'],
        'meter_pattern': poem['meter_pattern'],
        'line_char_counts': poem['line_char_counts'],
        'total_lines': poem['total_lines'],
        'total_chars': poem['total_chars'],
        'is_regular': bool(poem['is_regular']),
        'regular_meter': poem['regular_meter'],
        'lines': poem['lines'] if isinstance(poem['lines'], list) else [],
    })


@app.route('/api/meter-patterns', methods=['GET'])
def get_meter_patterns():
    """获取所有格律模式"""
    df = load_data()['df']
    
    limit = request.args.get('limit', 100, type=int)
    patterns = df['meter_pattern'].value_counts().head(limit).to_dict()
    return jsonify(patterns)


@app.route('/api/meter-stats', methods=['GET'])
def get_meter_stats():
    """获取完整的格律统计数据"""
    df = load_data()['df']
    
    # 按诗歌类型统计 - 返回全部
    by_poem_type = {}
    for ptype in df['poem_type'].unique():
        ptype_df = df[df['poem_type'] == ptype]
        patterns = ptype_df['meter_pattern'].value_counts().to_dict()
        if patterns:
            by_poem_type[ptype] = patterns
    
    # 按体裁统计 - 返回全部
    by_genre = {}
    for genre in df['genre'].unique():
        genre_df = df[df['genre'] == genre]
        patterns = genre_df['meter_pattern'].value_counts().to_dict()
        if patterns:
            by_genre[genre] = patterns
    
    # 所有格律模式及其数量
    all_patterns = df['meter_pattern'].value_counts().to_dict()
    
    stats = {
        'total_poems': int(len(df)),
        'total_patterns': int(df['meter_pattern'].nunique()),
        'all_patterns': all_patterns,
        'by_poem_type': by_poem_type,
        'by_genre': by_genre,
    }
    return jsonify(stats)


@app.route('/api/meter-position/<meter>', methods=['GET'])
def get_meter_position(meter):
    """获取指定格律的位置统计"""
    import json
    from pathlib import Path
    
    stats_path = Path(__file__).parent.parent / "data" / "meter_position_stats.json"
    
    if not stats_path.exists():
        return jsonify({'error': '统计数据未生成'}), 404
    
    with open(stats_path, 'r', encoding='utf-8') as f:
        all_stats = json.load(f)
    
    if meter in all_stats:
        return jsonify(all_stats[meter])
    else:
        return jsonify({'error': '格律不在统计范围内'}), 404


@app.route('/api/search/by-sentence', methods=['GET'])
def search_by_sentence():
    """按句式搜索（精确匹配）"""
    df = load_data()['df']

    sentence = request.args.get('sentence', '').strip()
    if not sentence:
        return jsonify({'error': 'sentence parameter required'}), 400

    char_count = len([c for c in sentence if '\u4e00' <= c <= '\u9fff'])

    filtered_df = df[df['line_char_counts'].apply(
        lambda x: char_count in x if isinstance(x, list) else False
    )]

    results = []
    for _, row in filtered_df.iterrows():
        if isinstance(row['lines'], list):
            for i, line in enumerate(row['lines']):
                if char_count == len(line):
                    results.append({
                        'id': str(row['id']),
                        'title': row['title'],
                        'author': row['author'],
                        'dynasty': row['dynasty'],
                        'genre': row['genre'],
                        'matched_line': line,
                        'line_index': i,
                    })

    return jsonify({
        'query': sentence,
        'char_count': char_count,
        'total': len(results),
        'data': results[:50],
    })


@app.route('/api/search/by-meter', methods=['GET'])
def search_by_meter():
    """按格律模式搜索"""
    df = load_data()['df']

    meter = request.args.get('meter', '').strip()
    if not meter:
        return jsonify({'error': 'meter parameter required'}), 400

    filtered_df = df[df['meter_pattern'] == meter]

    results = []
    for _, row in filtered_df.iterrows():
        results.append({
            'id': str(row['id']),
            'title': row['title'],
            'author': row['author'],
            'dynasty': row['dynasty'],
            'genre': row['genre'],
            'poem_type': row['poem_type'],
            'lines': row['lines'] if isinstance(row['lines'], list) else [],
        })

    return jsonify({
        'query': meter,
        'total': len(results),
        'data': results[:50],
    })


@app.route('/api/random', methods=['GET'])
def get_random():
    """随机获取一首诗"""
    df = load_data()['df']

    count = request.args.get('count', 1, type=int)
    poem = df.sample(n=min(count, 10))

    results = []
    for _, row in poem.iterrows():
        results.append({
            'id': str(row['id']),
            'title': row['title'],
            'author': row['author'],
            'dynasty': row['dynasty'],
            'genre': row['genre'],
            'poem_type': row['poem_type'],
            'lines': row['lines'] if isinstance(row['lines'], list) else [],
        })

    return jsonify(results)


def main():
    parser = argparse.ArgumentParser(description='诗词知识库API服务')
    parser.add_argument('--port', type=int, default=5000, help='服务端口')
    parser.add_argument('--host', default='127.0.0.1', help='服务地址')
    args = parser.parse_args()

    load_data()

    print("="*60)
    print("诗词知识库 API 服务")
    print("="*60)
    print(f"访问地址: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/api/stats")
    print("="*60)

    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
