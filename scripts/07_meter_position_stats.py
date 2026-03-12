#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格律位置词性和高频词统计
统计count>100的格律模式，分析每个位置的词性和高频词
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from collections import Counter, defaultdict
from pathlib import Path
import jieba
import jieba.posseg as pseg


def load_data():
    """加载数据"""
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "structure_analysis" / "poetry_structure_full.csv"
    
    print(f"加载数据: {data_path}")
    df = pd.read_csv(data_path, low_memory=False)
    
    # 转换lines字段
    if 'lines' in df.columns:
        df['lines'] = df['lines'].apply(lambda x: x.split('|') if isinstance(x, str) else [])
    
    return df


def analyze_meter_position_stats(df: pd.DataFrame, min_count: int = 100):
    """统计格律位置的词性和高频词"""
    
    # 统计每种格律的数量
    meter_counts = df['meter_pattern'].value_counts()
    
    # 筛选高频格律
    high_freq_meters = meter_counts[meter_counts >= min_count]
    print(f"\n格律数量 >= {min_count}: {len(high_freq_meters)} 种")
    print(f"涵盖诗词: {high_freq_meters.sum()} 首 (占比: {high_freq_meters.sum()/len(df)*100:.1f}%)")
    
    # 统计每个格律的每个位置
    meter_position_chars = defaultdict(lambda: defaultdict(list))
    meter_position_words = defaultdict(lambda: defaultdict(list))
    
    for _, row in df.iterrows():
        meter = row['meter_pattern']
        if meter not in high_freq_meters.index:
            continue
        
        lines = row.get('lines', [])
        if not isinstance(lines, list):
            continue
        
        for line in lines:
            positions = meter.split(',')
            char_idx = 0
            
            for pos_idx in range(len(positions)):
                if char_idx >= len(line):
                    break
                    
                char = line[char_idx]
                if '\u4e00' <= char <= '\u9fff':  # 只统计汉字
                    meter_position_chars[meter][pos_idx].append(char)
                
                char_idx += 1
    
    # 分词和词性分析
    for meter in meter_position_chars:
        for pos in meter_position_chars[meter]:
            chars = meter_position_chars[meter][pos]
            
            # 词性分析
            word_pos = []
            for char in chars[:5000]:  # 限制数量
                words = pseg.cut(char)
                for w in words:
                    word_pos.append((w.word, w.flag))
            
            meter_position_words[meter][pos] = word_pos
    
    return meter_position_chars, meter_position_words, high_freq_meters


def generate_position_analysis(meter_position_chars, meter_position_words, high_freq_meters):
    """生成位置分析报告"""
    
    results = {}
    
    for meter in list(high_freq_meters.index)[:50]:  # 限制数量
        if meter not in meter_position_chars:
            continue
        
        meter_info = {
            'count': int(high_freq_meters[meter]),
            'positions': {}
        }
        
        # 解析格律模式
        positions = meter.split(',')
        
        for pos_idx in range(len(positions)):
            chars = meter_position_chars.get(meter, {}).get(pos_idx, [])
            
            if not chars:
                continue
            
            # 统计高频字
            char_counter = Counter(chars)
            top_chars = char_counter.most_common(20)
            
            # 统计词性
            pos_counter = Counter()
            word_counter = Counter()
            
            if meter in meter_position_words and pos_idx in meter_position_words[meter]:
                for word, pos in meter_position_words[meter][pos_idx]:
                    if len(word) == 1:
                        pos_counter[pos] += 1
                    word_counter[word] += 1
            
            meter_info['positions'][f'pos_{pos_idx}'] = {
                'position': pos_idx + 1,
                'total_chars': len(chars),
                'top_chars': dict(top_chars[:10]),
                'top_words': dict(Counter({w: c for w, c in word_counter.items() if len(w) >= 1}).most_common(10)),
                'pos_distribution': dict(pos_counter.most_common(5)),
            }
        
        results[meter] = meter_info
    
    return results


def print_sample_analysis(results, meter='7,7,7,7'):
    """打印示例分析"""
    
    if meter not in results:
        print(f"格律 {meter} 不在统计结果中")
        return
    
    info = results[meter]
    print(f"\n{'='*70}")
    print(f"格律模式: {meter}")
    print(f"诗词数量: {info['count']}")
    print(f"{'='*70}")
    
    for pos_key, pos_info in info['positions'].items():
        print(f"\n【位置 {pos_info['position']}】 (共 {pos_info['total_chars']} 字)")
        
        # 高频字
        print(f"  高频字: ", end="")
        for char, count in list(pos_info['top_chars'].items())[:5]:
            print(f"{char}({count}) ", end="")
        print()
        
        # 词性分布
        if pos_info['pos_distribution']:
            print(f"  词性分布: ", end="")
            for pos, count in list(pos_info['pos_distribution'].items())[:5]:
                print(f"{pos}({count}) ", end="")
            print()


def main():
    print("="*60)
    print("格律位置词性和高频词统计")
    print("="*60)
    
    df = load_data()
    print(f"总诗词数: {len(df)}")
    
    # 分析
    meter_chars, meter_words, high_freq = analyze_meter_position_stats(df, min_count=100)
    
    # 生成报告
    results = generate_position_analysis(meter_chars, meter_words, high_freq)
    
    # 打印几个典型例子
    print_sample_analysis(results, '7,7,7,7')    # 七言绝句
    print_sample_analysis(results, '5,5,5,5')    # 五言绝句
    print_sample_analysis(results, '7,7,7,7,7,7,7,7')  # 七言律诗
    
    # 保存结果
    import json
    output_path = Path(__file__).parent.parent / "data" / "meter_position_stats.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n\n统计结果已保存: {output_path}")
    
    # 打印统计摘要
    print(f"\n{'='*60}")
    print("统计摘要")
    print(f"{'='*60}")
    print(f"统计格律数: {len(results)}")
    print(f"格律模式: 5言/7言 绝句/律诗/排律")


if __name__ == "__main__":
    main()
