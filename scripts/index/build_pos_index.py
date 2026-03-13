#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 17: 词性标注分析器 (静态化)
使用 jieba.posseg 进行词性标注，预计算每位作者的词性使用偏好
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_silver_data() -> pd.DataFrame:
    """加载Silver层数据"""
    silver_path = project_root / "data" / "silver" / "v2_poems_structured.csv"
    
    if not silver_path.exists():
        raise FileNotFoundError(f"找不到Silver层数据: {silver_path}")
    
    print(f"加载Silver层数据: {silver_path}")
    df = pd.read_csv(silver_path)
    print(f"共加载 {len(df)} 首诗词")
    return df


def build_pos_index(df: pd.DataFrame) -> Dict:
    """
    构建词性标注索引
    
    对每位作者的诗词进行词性标注，统计词性分布和常用词汇
    """
    print("构建词性标注索引...")
    
    try:
        import jieba.posseg as pseg
    except ImportError:
        raise ImportError("需要安装 jieba: pip install jieba")
    
    # 词性标签映射
    pos_tag_mapping = {
        'n': '名词',
        'v': '动词',
        'a': '形容词',
        'd': '副词',
        'm': '数词',
        'q': '量词',
        'r': '代词',
        'p': '介词',
        'c': '连词',
        'u': '助词',
        'e': '叹词',
        'y': '语气词',
        'o': '拟声词',
        'i': '成语',
        'l': '习用语',
        'j': '简称略语',
        'h': '前接成分',
        'k': '后接成分',
        'g': '语素',
        'x': '非语素字',
        'w': '标点符号',
        'ns': '地名',
        'nt': '机构团体',
        'nr': '人名',
        'nz': '其他专名',
        't': '时间词',
        's': '处所词',
        'f': '方位词',
        'b': '区别词',
        'z': '状态词'
    }
    
    # 停用词
    stop_words = {'，', '。', '、', '；', '：', '？', '！', '"', '"', ''', ''', 
                  '(', ')', '[', ']', '{', '}', '《', '》', '「', '」', '『', '』',
                  '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', 
                  '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
                  '你', '会', '着', '没有', '看', '好', '自己', '这'}
    
    # 作者词性统计
    author_stats: Dict[str, Dict] = defaultdict(lambda: {
        'total_words': 0,
        'pos_counts': Counter(),
        'word_counts': defaultdict(Counter)  # pos -> word -> count
    })
    
    # 全局词性统计
    global_pos_counts = Counter()
    global_total_words = 0
    
    # 处理每首诗词
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"  处理进度: {idx}/{len(df)}")
        
        author = row.get('author', '未知')
        content = row.get('content', '')
        
        if pd.isna(content) or not content:
            continue
        
        # 词性标注
        words_pos = list(pseg.cut(str(content)))
        
        for word, pos in words_pos:
            # 跳过停用词和标点
            if word in stop_words or pos == 'w' or len(word.strip()) == 0:
                continue
            
            # 更新全局统计
            global_pos_counts[pos] += 1
            global_total_words += 1
            
            # 更新作者统计
            author_stats[author]['total_words'] += 1
            author_stats[author]['pos_counts'][pos] += 1
            author_stats[author]['word_counts'][pos][word] += 1
    
    # 构建索引数据
    index_data = {
        'version': '1.0.0',
        'generated_at': pd.Timestamp.now().isoformat(),
        'pos_tags': pos_tag_mapping,
        'global': {
            'total_words': global_total_words,
            'distribution': {
                pos: round(count / global_total_words, 4) 
                for pos, count in global_pos_counts.most_common(20)
            }
        },
        'authors': {}
    }
    
    # 处理每位作者的统计
    for author, stats in author_stats.items():
        total = stats['total_words']
        if total < 10:  # 跳过诗词太少的作者
            continue
        
        # 计算词性分布
        pos_distribution = {
            pos: round(count / total, 4)
            for pos, count in stats['pos_counts'].most_common(10)
        }
        
        # 获取每类词性中最常用的词汇
        top_words_by_pos = {}
        for pos, word_counter in stats['word_counts'].items():
            if pos in pos_tag_mapping:  # 只保留主要词性
                top_words = [word for word, _ in word_counter.most_common(10)]
                if top_words:
                    top_words_by_pos[pos] = top_words
        
        index_data['authors'][author] = {
            'total_words': total,
            'distribution': pos_distribution,
            'top_words': top_words_by_pos
        }
    
    print(f"词性标注索引构建完成")
    print(f"  - 总词汇数: {global_total_words}")
    print(f"  - 作者数: {len(index_data['authors'])}")
    print(f"  - 词性标签数: {len(pos_tag_mapping)}")
    
    return index_data


def save_index(index_data: Dict, output_dir: Path):
    """保存索引文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存主索引文件
    index_file = output_dir / 'pos_index.json'
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    file_size = index_file.stat().st_size / 1024  # KB
    print(f"\n索引文件已保存: {index_file}")
    print(f"文件大小: {file_size:.2f} KB")
    
    # 保存压缩版本
    import gzip
    compressed_file = output_dir / 'pos_index.json.gz'
    with gzip.open(compressed_file, 'wt', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False)
    
    compressed_size = compressed_file.stat().st_size / 1024  # KB
    print(f"压缩文件已保存: {compressed_file}")
    print(f"压缩后大小: {compressed_size:.2f} KB")
    print(f"压缩率: {(1 - compressed_size/file_size)*100:.1f}%")


def main():
    """主函数"""
    print("=" * 60)
    print("Task 17: 词性标注分析器 (静态化)")
    print("=" * 60)
    
    try:
        # 加载数据
        df = load_silver_data()
        
        # 构建索引
        index_data = build_pos_index(df)
        
        # 保存索引
        output_dir = project_root / "data" / "output" / "web" / "index"
        save_index(index_data, output_dir)
        
        print("\n✅ Task 17 完成!")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
